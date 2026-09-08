/* EmbeddedSoundLocalisation_Full.ino
   Author: Aneesh Arnav Chikkala (adapted for MicroDSP)
   Board: ESP32-S3 (Arduino Core / ESP-IDF)
   Purpose: Full embedded pipeline for multi-microphone sound localization:
     - Acquisition (multi-channel)
     - Calibration (per-channel gains saved to EEPROM)
     - FIR filtering (Kaiser FIR coefficients assumed precomputed)
     - Real-time processing with FreeRTOS tasks
     - GCC-PHAT for TDOA estimation using MicroDSP FFT/IFFT
     - TDOA -> angle conversion for generalized geometry (linear/circular)
     - Telemetry JSON output over Serial and dsp.exportToSerial()
   NOTES:
   1) Replace captureFrameBlocking() with a synchronous sampling implementation.
      The current stub uses analogRead() in a multiplexed loop and is only useful
      for testing; it will NOT provide accurate TDOA results.
   2) Replace or confirm MICRODSP function names if your installed library uses different APIs.
   3) Adjust NUM_MICS, ADC mapping, MIC_POSITIONS, SAMPLE_RATE_HZ, FRAME_SIZE, FIR coeffs, etc.
*/

#include <Arduino.h>
#include <EEPROM.h>
#include "microdsp.h"                  // MICRODSP main header (per your doc)
#include "internal/dspResources/dspResources.h" // resource management hooks (per doc)
#include <math.h>

// ----------------------- USER-CONFIGURABLE HARDWARE PARAMETERS -----------------------
#define NUM_MICS            4               // number of microphone channels used
#define SAMPLE_RATE_HZ      16000           // sampling rate per channel (Hz)
#define FRAME_SIZE          256             // samples per frame (power of two preferred)
#define SERIAL_BAUD         115200
#define EEPROM_BASE_ADDR    0               // where calibration data saved in EEPROM
#define EEPROM_MAGIC        0xDEAFBEEF

// microphone ADC pins or channel ids (adjust to your wiring)
const int ADC_PINS[NUM_MICS] = {34, 35, 36, 37}; // example: ADC GPIO pins (change to match your board)

// Microphone physical coordinates (meters) — provide (x,y) for each mic in array order
// Example for a small square/circular layout; change to your exact geometry
const float MIC_POSITIONS[NUM_MICS][2] = {
  {  0.03f,  0.00f },  // Mic 0
  { -0.03f,  0.00f },  // Mic 1
  {  0.00f,  0.03f },  // Mic 2
  {  0.00f, -0.03f }   // Mic 3
};

// Speed of sound (m/s)
const float SPEED_OF_SOUND = 343.0f;

const float FIR_COEFFS[] = {
  -0.0013, -0.0021, 0.0000, 0.0042, 0.0101,
   0.0148, 0.0142, 0.0056, -0.0108, -0.0297,
  -0.0431, -0.0431, -0.0261, 0.0092, 0.0557,
   0.1016, 0.1344, 0.1443, 0.1266, 0.0821,
   0.0184, -0.0476, -0.0983, -0.1186, -0.1032,
  -0.0600, 0.0000, 0.0600, 0.1032, 0.1186,
   0.0983, 0.0476, -0.0184, -0.0821, -0.1266,
  -0.1443, -0.1344, -0.1016, -0.0557, -0.0092,
   0.0261, 0.0431, 0.0431, 0.0297, 0.0108,
  -0.0056, -0.0142, -0.0148, -0.0101, -0.0042,
   0.0000, 0.0021, 0.0013
};
const int FIR_LEN = sizeof(FIR_COEFFS) / sizeof(FIR_COEFFS[0]);

// ----------------------- INTERNAL BUFFERS & STATE -----------------------
static float micBuffer[NUM_MICS][FRAME_SIZE];       // floating buffer for raw input (post gain)
static float filtBuffer[NUM_MICS][FRAME_SIZE];      // floating buffer for filtered output
static float fftRe[NUM_MICS][FRAME_SIZE];           // real part for FFT per channel
static float fftIm[NUM_MICS][FRAME_SIZE];           // imag part for FFT per channel
static float crossRe[FRAME_SIZE];                   // cross-spectrum real (temp)
static float crossIm[FRAME_SIZE];                   // cross-spectrum imag (temp)

static float micGains[NUM_MICS];                    // calibration gains per channel (loaded from EEPROM)
static bool hasCalibration = false;

MicroDSP dsp; // instance of your microdsp class

// task handles
TaskHandle_t taskAcquireHandle = NULL;
TaskHandle_t taskProcessHandle = NULL;

// ring buffer to pass frames from acquisition to processing (simple circular buffer)
#define RBUF_SIZE 4
struct Frame {
  uint32_t timestamp_us;
  // raw int16 capture to save memory transfer cost; convert to float on processing side
  int16_t raw[NUM_MICS][FRAME_SIZE];
};
static Frame ringBuf[RBUF_SIZE];
static volatile int rhead = 0;
static volatile int rtail = 0;
portMUX_TYPE ringMux = portMUX_INITIALIZER_UNLOCKED;

// ----------------------- FORWARD DECLARATIONS -----------------------
void setupHardware();
void setupMicroDSP();
void loadCalibrationFromEEPROM();
void saveCalibrationToEEPROM();
void runCalibrationRoutine();
void captureFrameBlocking(Frame &f); // MUST replace with a synchronous ADC/I2S driver
void applyGainsAndConvertToFloat(const Frame &f);
void applyFIRallChannels();
void computeGCCPHAT_TDOAs(float tdoa_matrix[NUM_MICS][NUM_MICS]);
float estimateAngleFromTDOAs(float tdoa_matrix[NUM_MICS][NUM_MICS], float &out_confidence);
void exportTelemetryJSON(uint32_t timestamp_us, float angle_deg, float confidence);

// ----------------------- SETUP -----------------------
void setup() {
  Serial.begin(SERIAL_BAUD);
  while (!Serial) { delay(10); } // wait for Serial

  Serial.println("\n=== Embedded Sound Localisation (Full) Boot ===");

  setupHardware();

  // init DSP resource system
  dspResources::init();
  dspResources::setFreeMemoryThreshold(1200); // bytes
  dspResources::setComputeLimit(0.75);        // 75% CPU budget

  setupMicroDSP();

  loadCalibrationFromEEPROM();

  // create tasks
  xTaskCreatePinnedToCore(
    [](void*){
      // wrapper to match earlier signature
      for (;;) {
        // Acquire frames and push to ring buffer
        Frame f;
        captureFrameBlocking(f);
        portENTER_CRITICAL(&ringMux);
        int next = (rhead + 1) % RBUF_SIZE;
        if (next == rtail) {
          // buffer full, drop oldest
          rtail = (rtail + 1) % RBUF_SIZE;
        }
        ringBuf[rhead] = f;
        rhead = next;
        portEXIT_CRITICAL(&ringMux);
        // small yield for scheduler
        taskYIELD();
      }
    },
    "acqTask",
    8 * 1024,
    NULL,
    3,
    &taskAcquireHandle,
    0); // core 0

  xTaskCreatePinnedToCore(
    [](void*){
      // Processing loop
      for (;;) {
        // check resources
        if (!dspResources::checkLoad(0.6)) {
          // too busy - yield briefly
          vTaskDelay(pdMS_TO_TICKS(2));
          continue;
        }
        // pop frame if available
        if (rhead == rtail) {
          // no frames - sleep tiny
          vTaskDelay(pdMS_TO_TICKS(1));
          continue;
        }
        Frame f;
        portENTER_CRITICAL(&ringMux);
        int tail = rtail;
        f = ringBuf[tail];
        rtail = (rtail + 1) % RBUF_SIZE;
        portEXIT_CRITICAL(&ringMux);

        // process
        applyGainsAndConvertToFloat(f);
        applyFIRallChannels();

        // compute TDOAs via GCC-PHAT
        float tdoa_matrix[NUM_MICS][NUM_MICS];
        computeGCCPHAT_TDOAs(tdoa_matrix);

        // estimate angle from TDOAs
        float confidence;
        float angle_deg = estimateAngleFromTDOAs(tdoa_matrix, confidence);

        // export telemetry
        exportTelemetryJSON(f.timestamp_us, angle_deg, confidence);

        // optional: export raw filtered channel 0 via microdsp helper (CSV)
        dsp.exportToSerial(filtBuffer[0], FRAME_SIZE, "filtered_ch0");

        // yield/short sleep
        vTaskDelay(pdMS_TO_TICKS(1));
      }
    },
    "procTask",
    14 * 1024,
    NULL,
    2,
    &taskProcessHandle,
    1); // core 1

  Serial.println("Tasks created. System running.");
}

// ----------------------- LOOP (unused) -----------------------
void loop() {
  delay(1000);
}
// ----------------------- HARDWARE SETUP -----------------------
void setupHardware() {
  for (int i = 0; i < NUM_MICS; ++i) {
    pinMode(ADC_PINS[i], INPUT);
  }
  // EEPROM init
  if (!EEPROM.begin(512)) {
    Serial.println("[EEPROM] init failed");
  }
  Serial.println("[HW] pins configured");
}

// ----------------------- MIC DSP SETUP -----------------------
void setupMicroDSP() {
  if (dsp.begin) {
  }
  Serial.println("[MicroDSP] ready");
}

// ----------------------- EEPROM CALIBRATION -----------------------
void loadCalibrationFromEEPROM() {
  uint32_t magic;
  EEPROM.get(EEPROM_BASE_ADDR, magic);
  if (magic != EEPROM_MAGIC) {
    Serial.println("[CAL] No EEPROM calibration found. Using unity gains.");
    for (int i = 0; i < NUM_MICS; ++i) micGains[i] = 1.0f;
    hasCalibration = false;
    // Save default so next boot sees magic
    saveCalibrationToEEPROM();
    return;
  }
  int addr = EEPROM_BASE_ADDR + sizeof(uint32_t);
  for (int i = 0; i < NUM_MICS; ++i) {
    float g;
    EEPROM.get(addr + i * sizeof(float), g);
    micGains[i] = g;
  }
  hasCalibration = true;
  Serial.print("[CAL] loaded gains: ");
  for (int i = 0; i < NUM_MICS; ++i) {
    Serial.printf("%.3f ", micGains[i]);
  }
  Serial.println();
}

void saveCalibrationToEEPROM() {
  EEPROM.put(EEPROM_BASE_ADDR, EEPROM_MAGIC);
  int addr = EEPROM_BASE_ADDR + sizeof(uint32_t);
  for (int i = 0; i < NUM_MICS; ++i) {
    EEPROM.put(addr + i * sizeof(float), micGains[i]);
  }
  EEPROM.commit();
  Serial.println("[CAL] Calibration saved to EEPROM");
}

// Interactive calibration routine (call manually via Serial command or embed a trigger)
void runCalibrationRoutine() {
  Serial.println("[CAL] Run calibration: place speaker at reference location and play steady tone.");
  const int NFRAMES = 4;
  float rms[NUM_MICS] = {0.0f};
  for (int f = 0; f < NFRAMES; ++f) {
    // blocking capture (reuse captureFrameBlocking)
    Frame fr;
    captureFrameBlocking(fr);
    // compute RMS per channel
    for (int ch = 0; ch < NUM_MICS; ++ch) {
      double sumsq = 0.0;
      for (int n = 0; n < FRAME_SIZE; ++n) {
        int16_t s = fr.raw[ch][n];
        sumsq += ((double)s * (double)s);
      }
      double r = sqrt(sumsq / FRAME_SIZE);
      rms[ch] += (float)r;
    }
  }
  for (int ch = 0; ch < NUM_MICS; ++ch) rms[ch] /= (float)NFRAMES;

  // set gains relative to channel 0
  float ref = rms[0] > 1e-6f ? rms[0] : 1.0f;
  for (int ch = 0; ch < NUM_MICS; ++ch) {
    if (rms[ch] < 1e-6f) micGains[ch] = 1.0f;
    else micGains[ch] = ref / rms[ch];
  }
  saveCalibrationToEEPROM();
  hasCalibration = true;
  Serial.println("[CAL] Completed. New gains:");
  for (int i = 0; i < NUM_MICS; ++i) Serial.printf("g[%d]=%.3f ", i, micGains[i]);
  Serial.println();
}

// ----------------------- CAPTURE (MUST ADAPT TO YOUR ADC) -----------------------
void captureFrameBlocking(Frame &f) {
  uint32_t t0 = micros();
  for (int n = 0; n < FRAME_SIZE; ++n) {
    for (int ch = 0; ch < NUM_MICS; ++ch) {
      int raw = analogRead(ADC_PINS[ch]); // slow; placeholder
      // map 12-bit ADC (0..4095) to signed int16 centered around 0
      int16_t s = (int16_t)(raw - 2048);
      f.raw[ch][n] = s;
    }
    // spacing to approximate SAMPLE_RATE_HZ; not precise
    uint32_t dt = 1000000UL / SAMPLE_RATE_HZ;
    delayMicroseconds(dt);
  }
  f.timestamp_us = t0;
}

// ----------------------- APPLY GAINS & CONVERT -----------------------
void applyGainsAndConvertToFloat(const Frame &f) {
  for (int ch = 0; ch < NUM_MICS; ++ch) {
    float g = micGains[ch];
    for (int n = 0; n < FRAME_SIZE; ++n) {
      micBuffer[ch][n] = (float)f.raw[ch][n] * g;
    }
  }
}

// ----------------------- APPLY FIR (MICRODSP FIR) -----------------------
void applyFIRallChannels() {
  for (int ch = 0; ch < NUM_MICS; ++ch) {
    dsp.FIRFilter(micBuffer[ch], FRAME_SIZE, (float*)FIR_COEFFS, FIR_LEN, filtBuffer[ch]);
  }
}


void computeGCCPHAT_TDOAs(float tdoa_matrix[NUM_MICS][NUM_MICS]) {
  for (int ch = 0; ch < NUM_MICS; ++ch) {
    // copy real input into fftRe, zero imag
    for (int k = 0; k < FRAME_SIZE; ++k) {
      fftRe[ch][k] = filtBuffer[ch][k];
      fftIm[ch][k] = 0.0f;
    }
    dsp.FFT(fftRe[ch], fftIm[ch], FRAME_SIZE); // MICRODSP CALL - adapt if needed
  }

  for (int i = 0; i < NUM_MICS; ++i) {
    for (int j = 0; j < NUM_MICS; ++j) {
      if (i == j) {
        tdoa_matrix[i][j] = 0.0f;
        continue;
      }
      // compute cross-spectrum (complex multiply: Xi * conj(Xj))
      for (int k = 0; k < FRAME_SIZE; ++k) {
        float xi_re = fftRe[i][k];
        float xi_im = fftIm[i][k];
        float xj_re = fftRe[j][k];
        float xj_im = fftIm[j][k];
        // conj(Xj) => (xj_re, -xj_im)
        float re = xi_re * xj_re + xi_im * xj_im; // a*c + b*d
        float im = xi_im * xj_re - xi_re * xj_im; // b*c - a*d
        // magnitude
        float mag = sqrtf(re * re + im * im) + 1e-12f;
        // PHAT normalization
        crossRe[k] = re / mag;
        crossIm[k] = im / mag;
      }
      dsp.IFFT(crossRe, crossIm, FRAME_SIZE); // MICRODSP CALL - adapt signature if necessary
      int maxIdx = 0;
      float maxVal = -1e12f;
      for (int n = 0; n < FRAME_SIZE; ++n) {
        float v = crossRe[n];
        if (v > maxVal) {
          maxVal = v;
          maxIdx = n;
        }
      }
      // convert circular index to signed lag (samples)
      int lag = maxIdx;
      if (lag > FRAME_SIZE / 2) lag -= FRAME_SIZE;
      // convert lag to seconds: lag / fs
      float tdoa_s = (float)lag / (float)SAMPLE_RATE_HZ;
      tdoa_matrix[i][j] = tdoa_s;
      // (optionally) zero crossRe/crossIm for next iteration
    }
  }
}

// ----------------------- ANGLE ESTIMATION FROM TDOAs -----------------------
float estimateAngleFromTDOAs(float tdoa_matrix[NUM_MICS][NUM_MICS], float &out_confidence) {
  float ATA[2][2] = {{0, 0}, {0, 0}};
  float ATb[2] = {0, 0};
  int eqCount = 0;

  for (int i = 0; i < NUM_MICS; ++i) {
    for (int j = i+1; j < NUM_MICS; ++j) {
      float dx = MIC_POSITIONS[j][0] - MIC_POSITIONS[i][0];
      float dy = MIC_POSITIONS[j][1] - MIC_POSITIONS[i][1];
      // predicted: (dx,dy)·u = c * tdoa_ij. Use tdoa_ij = t_j - t_i
      float tij = tdoa_matrix[i][j];
      // if measurement absurd (NaN/infinite), skip
      if (!isfinite(tij)) continue;
      float rhs = SPEED_OF_SOUND * tij;
      // accumulate
      ATA[0][0] += dx * dx;
      ATA[0][1] += dx * dy;
      ATA[1][0] += dx * dy;
      ATA[1][1] += dy * dy;
      ATb[0] += dx * rhs;
      ATb[1] += dy * rhs;
      eqCount++;
    }
  }

  if (eqCount < 1) {
    out_confidence = 0.0f;
    return 0.0f;
  }

  // Solve 2x2 linear system ATA * u = ATb
  float det = ATA[0][0]*ATA[1][1] - ATA[0][1]*ATA[1][0];
  if (fabs(det) < 1e-9f) {
    // poorly conditioned - fallback
    out_confidence = 0.0f;
    return 0.0f;
  }
  // inverse ATA
  float inv00 = ATA[1][1] / det;
  float inv01 = -ATA[0][1] / det;
  float inv10 = -ATA[1][0] / det;
  float inv11 = ATA[0][0] / det;
  float ux = inv00 * ATb[0] + inv01 * ATb[1];
  float uy = inv10 * ATb[0] + inv11 * ATb[1];

  // Normalize u to unit vector (direction only)
  float norm = sqrtf(ux*ux + uy*uy) + 1e-12f;
  float nx = ux / norm;
  float ny = uy / norm;

  // Angle (degrees)
  float angle_rad = atan2f(ny, nx);
  float angle_deg = angle_rad * 180.0f / M_PI;

  // Compute residuals and produce confidence: lower residual => higher confidence
  float sumsq = 0.0f;
  float sumrhs = 0.0f;
  for (int i = 0; i < NUM_MICS; ++i) {
    for (int j = i+1; j < NUM_MICS; ++j) {
      float dx = MIC_POSITIONS[j][0] - MIC_POSITIONS[i][0];
      float dy = MIC_POSITIONS[j][1] - MIC_POSITIONS[i][1];
      float pred = (dx * nx + dy * ny) / SPEED_OF_SOUND; // predicted tdoa (s)
      float meas = tdoa_matrix[i][j];
      float err = meas - pred;
      sumsq += err * err;
      sumrhs += fabs(meas);
    }
  }
  float mse = sumsq / max(1, (NUM_MICS*(NUM_MICS-1)/2));
  // Confidence metric: clamp between 0..1, higher when mse small compared to typical tdoa magnitudes
  // heuristics: use inverse relation
  float conf = 1.0f / (1.0f + 1000.0f * mse); // scale factor chosen heuristically
  if (conf < 0.0f) conf = 0.0f;
  if (conf > 1.0f) conf = 1.0f;
  out_confidence = conf;

  return angle_deg;
}

// ----------------------- TELEMETRY OUTPUT -----------------------
void exportTelemetryJSON(uint32_t timestamp_us, float angle_deg, float confidence) {
  // compute unit vector coords (r=1)
  float theta = angle_deg * (M_PI / 180.0f);
  float x = cosf(theta);
  float y = sinf(theta);
  // print JSON line
  Serial.printf("{\"timestamp\":%u,\"angle_deg\":%.2f,\"confidence\":%.3f,\"x\":%.3f,\"y\":%.3f}\n",
                (unsigned int)timestamp_us, angle_deg, confidence, x, y);
}

// ----------------------- SERIAL COMMAND HOOKS (optional) -----------------------
#ifdef ENABLE_SERIAL_COMMANDS
// A simple serial handler to run calibration on demand or print status. If you want this, #define ENABLE_SERIAL_COMMANDS
void serialCommandHandler() {
  if (!Serial.available()) return;
  String cmd = Serial.readStringUntil('\n');
  cmd.trim();
  if (cmd == "cal") {
    runCalibrationRoutine();
  } else if (cmd == "save") {
    saveCalibrationToEEPROM();
  } else if (cmd == "show") {
    Serial.print("Gains: ");
    for (int i = 0; i < NUM_MICS; ++i) Serial.printf("%.3f ", micGains[i]);
    Serial.println();
  } else {
    Serial.println("Commands: cal, save, show");
  }
}
#endif
