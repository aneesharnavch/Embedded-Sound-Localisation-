// ESP32-S3, 3x analog mic capsules -> ADC continuous/DMA -> band-limited GCC-PHAT -> azimuth.
//
// HYPOTHETICAL / UNVERIFIED: written against arduino-esp32 core 3.x (ESP-IDF 5.x adc_continuous
// API) and the "esp-dsp" library. Neither has been compiled or run on real hardware in this
// session. Treat this as a starting point to bring up on the bench, not working firmware.
//
// Implements the corrected paper thesis, not the retracted one:
//   - PHAT weight is band-limited to 300-3400 Hz (the un-limited version put 80.9% of
//     unit-weight bins outside the source band and was the dominant source of error).
//   - Peak localization is native-length IFFT + parabolic sub-sample refinement (no
//     zero-padding/upsampling beyond the minimum needed for linear, non-circular
//     cross-correlation).
//   - The multi-frame accumulator is a plain circular mean. Confidence-weighting it was tested
//     and its sign flips with the room (0.0001-0.006 deg, not a real effect) -- deliberately
//     left out.
//   - PSR/consistency gating across the 3 TDOA pairs was tested and contributes ~1-3% of the
//     error budget (rank-deficient: 1 redundant measurement can flag a fault but not identify
//     which mic is bad). Left out for the same reason -- not because it's wrong, because it's
//     not worth the code.

#include <esp_adc/adc_continuous.h>
#include <dsps_fft2r.h>
#include <math.h>

// ---------------------------------------------------------------------------
// Hardware config -- EDIT to match the actual board.
// ---------------------------------------------------------------------------
static const adc_channel_t MIC_CH[3] = { ADC_CHANNEL_0, ADC_CHANNEL_1, ADC_CHANNEL_2 };
static const adc_unit_t    ADC_UNIT_USED = ADC_UNIT_1;

// Mic positions in metres, array frame, mic 0 as reference. Fill in from calipers, not the
// datasheet drawing -- memory flags "5 cm aperture" as ambiguous between 8.66 cm circumradius
// and ~14.6 cm edge spacing for this array. Get this wrong and every azimuth is wrong by a
// fixed, plausible-looking offset.
static const float MIC_X[3] = { 0.0f,  0.0866f, 0.0433f };
static const float MIC_Y[3] = { 0.0f,  0.0f,    0.0750f };

static const float SPEED_OF_SOUND = 343.0f;  // m/s, re-check against bench temperature

// ---------------------------------------------------------------------------
// Signal config
// ---------------------------------------------------------------------------
static const uint32_t FS_PER_CHANNEL = 16000;              // Hz, per-mic sample rate
static const uint32_t ADC_SAMPLE_RATE = FS_PER_CHANNEL * 3; // round-robin across 3 channels
static const int FRAME_LEN = 256;                           // samples/channel/frame (16 ms)
static const int FFT_LEN   = 512;                            // >= 2*FRAME_LEN-1, next pow2
static const float BAND_LO_HZ = 300.0f;
static const float BAND_HI_HZ = 3400.0f;
static const int   ACC_FRAMES = 8;                           // circular-mean window, ~128 ms

static const int DMA_FRAME_SAMPLES = FRAME_LEN * 3;          // interleaved raw samples/frame
static const int DMA_BUF_BYTES = DMA_FRAME_SAMPLES * SOC_ADC_DIGI_RESULT_BYTES;

static adc_continuous_handle_t adc_handle = NULL;
static volatile bool frame_ready = false;
static uint8_t dma_raw[DMA_BUF_BYTES];

static float chA[FRAME_LEN], chB[FRAME_LEN], chC[FRAME_LEN];

// complex scratch buffers, interleaved re/im, length 2*FFT_LEN
static float specA[FFT_LEN * 2];
static float specB[FFT_LEN * 2];
static float specC[FFT_LEN * 2];
static float xcorr01[FFT_LEN * 2];
static float xcorr02[FFT_LEN * 2];

static float accCos = 0.0f, accSin = 0.0f;
static int   accCount = 0;

// ---------------------------------------------------------------------------
// ADC continuous DMA setup
// ---------------------------------------------------------------------------
static bool IRAM_ATTR adc_conv_done_cb(adc_continuous_handle_t handle,
                                        const adc_continuous_evt_data_t *edata,
                                        void *user_data) {
  frame_ready = true;
  return false; // no higher-priority task woken from ISR here
}

void adcInit() {
  adc_continuous_handle_cfg_t handle_cfg = {
    .max_store_buf_size = DMA_BUF_BYTES * 4,
    .conv_frame_size = DMA_BUF_BYTES,
  };
  ESP_ERROR_CHECK(adc_continuous_new_handle(&handle_cfg, &adc_handle));

  adc_digi_pattern_config_t pattern[3];
  for (int i = 0; i < 3; i++) {
    pattern[i].atten = ADC_ATTEN_DB_12;
    pattern[i].channel = MIC_CH[i];
    pattern[i].unit = ADC_UNIT_USED;
    pattern[i].bit_width = SOC_ADC_DIGI_MAX_BITWIDTH;
  }

  adc_continuous_config_t dig_cfg = {
    .sample_freq_hz = ADC_SAMPLE_RATE,
    .conv_mode = ADC_CONV_SINGLE_UNIT_1,
    .format = ADC_DIGI_OUTPUT_FORMAT_TYPE2,
    .pattern_num = 3,
    .adc_pattern = pattern,
  };
  ESP_ERROR_CHECK(adc_continuous_config(adc_handle, &dig_cfg));

  adc_continuous_evt_cbs_t cbs = { .on_conv_done = adc_conv_done_cb };
  ESP_ERROR_CHECK(adc_continuous_register_event_callbacks(adc_handle, &cbs, NULL));
  ESP_ERROR_CHECK(adc_continuous_start(adc_handle));
}

// Round-robin de-interleave: raw stream is ch0,ch1,ch2,ch0,ch1,ch2,... in pattern order.
void demux(const uint8_t *raw, int nBytes) {
  int nSamples = nBytes / SOC_ADC_DIGI_RESULT_BYTES;
  int idx = 0;
  for (int i = 0; i < nSamples; i++) {
    adc_digi_output_data_t *p = (adc_digi_output_data_t *)&raw[i * SOC_ADC_DIGI_RESULT_BYTES];
    uint16_t code = p->type2.data; // 12-bit code, 0-4095
    int chSlot = i % 3;
    int frameIdx = idx;
    if (chSlot == 0) { if (frameIdx < FRAME_LEN) chA[frameIdx] = (float)code; }
    else if (chSlot == 1) { if (frameIdx < FRAME_LEN) chB[frameIdx] = (float)code; }
    else { if (frameIdx < FRAME_LEN) chC[frameIdx] = (float)code; idx++; }
  }
}

// ---------------------------------------------------------------------------
// DSP helpers
// ---------------------------------------------------------------------------

// DC removal (per-frame mean subtract -- fine at 16 ms frames, replace with a running
// high-pass if capsule DC drifts faster than that) + Hann window, into a zero-padded
// complex buffer ready for dsps_fft2r_fc32.
void windowToComplex(const float *in, float *complexOut) {
  float mean = 0.0f;
  for (int i = 0; i < FRAME_LEN; i++) mean += in[i];
  mean /= FRAME_LEN;

  for (int i = 0; i < FFT_LEN; i++) {
    complexOut[2 * i] = 0.0f;
    complexOut[2 * i + 1] = 0.0f;
  }
  for (int i = 0; i < FRAME_LEN; i++) {
    float w = 0.5f - 0.5f * cosf(2.0f * (float)M_PI * i / (FRAME_LEN - 1));
    complexOut[2 * i] = (in[i] - mean) * w;
  }
}

// Forward FFT in place (esp-dsp radix-2, bit-reversed order handled by dsps_fft2r_fc32 +
// dsps_bit_rev_fc32 per the library's own convention -- confirm against the installed version).
void fftForward(float *complexBuf) {
  dsps_fft2r_fc32(complexBuf, FFT_LEN);
  dsps_bit_rev_fc32(complexBuf, FFT_LEN);
}

// Inverse via conjugate trick: ifft(X) = conj(fft(conj(X))) / N.
void fftInverse(float *complexBuf) {
  for (int i = 0; i < FFT_LEN; i++) complexBuf[2 * i + 1] = -complexBuf[2 * i + 1];
  dsps_fft2r_fc32(complexBuf, FFT_LEN);
  dsps_bit_rev_fc32(complexBuf, FFT_LEN);
  for (int i = 0; i < FFT_LEN; i++) {
    complexBuf[2 * i]     =  complexBuf[2 * i]     / FFT_LEN;
    complexBuf[2 * i + 1] = -complexBuf[2 * i + 1] / FFT_LEN;
  }
}

// Band-limited GCC-PHAT cross-spectrum: Gij[k] = Xi[k] * conj(Xj[k]) / |Xi[k]*conj(Xj[k])|,
// zeroed outside [BAND_LO_HZ, BAND_HI_HZ]. This band limit is the fix for the defect that
// invalidated the old "temporal accumulation" thesis -- without it, ~81% of unit-weight bins
// are out-of-band noise.
void crossSpectrumPHAT(const float *Xi, const float *Xj, float *outXcorr) {
  int loBin = (int)ceilf(BAND_LO_HZ * FFT_LEN / FS_PER_CHANNEL);
  int hiBin = (int)floorf(BAND_HI_HZ * FFT_LEN / FS_PER_CHANNEL);
  if (hiBin > FFT_LEN / 2) hiBin = FFT_LEN / 2;

  for (int k = 0; k < FFT_LEN; k++) {
    outXcorr[2 * k] = 0.0f;
    outXcorr[2 * k + 1] = 0.0f;
  }

  for (int k = loBin; k <= hiBin; k++) {
    float xir = Xi[2 * k],     xii = Xi[2 * k + 1];
    float xjr = Xj[2 * k],     xji = Xj[2 * k + 1];
    // Xi * conj(Xj)
    float gr = xir * xjr + xii * xji;
    float gi = xii * xjr - xir * xji;
    float mag = sqrtf(gr * gr + gi * gi) + 1e-12f;
    outXcorr[2 * k] = gr / mag;
    outXcorr[2 * k + 1] = gi / mag;

    if (k > 0 && k < FFT_LEN / 2) { // hermitian mirror so ifft comes out real
      int m = FFT_LEN - k;
      outXcorr[2 * m] = gr / mag;
      outXcorr[2 * m + 1] = -gi / mag;
    }
  }
}

// Peak search with parabolic sub-sample refinement, restricted to the physically possible
// lag range for this mic pair (|tdoa| <= dist(i,j)/c) so it can't lock onto a reverberant
// sidelobe outside the feasible set.
float peakLagSamples(const float *xcorrComplex, float maxLagSamples) {
  int maxLagInt = (int)ceilf(maxLagSamples);
  int bestLag = 0;
  float bestVal = -1e30f;

  for (int lag = -maxLagInt; lag <= maxLagInt; lag++) {
    int idx = (lag >= 0) ? lag : (FFT_LEN + lag);
    float v = xcorrComplex[2 * idx];
    if (v > bestVal) { bestVal = v; bestLag = lag; }
  }

  auto valAt = [&](int lag) -> float {
    int idx = (lag >= 0) ? lag : (FFT_LEN + lag);
    return xcorrComplex[2 * idx];
  };
  float yL = valAt(bestLag - 1), y0 = valAt(bestLag), yR = valAt(bestLag + 1);
  float denom = (yL - 2.0f * y0 + yR);
  float delta = (fabsf(denom) > 1e-9f) ? 0.5f * (yL - yR) / denom : 0.0f;
  delta = fmaxf(-1.0f, fminf(1.0f, delta)); // guard against a denom near zero

  return (float)bestLag + delta;
}

// Direction unit vector from two TDOAs (far-field plane wave assumption):
//   (mic_i - mic_0) . u = c * tdoa_0i
// Two baselines -> 2x2 linear solve for u = (ux, uy).
bool solveAzimuth(float tdoa01, float tdoa02, float *azimuthOut) {
  float a11 = MIC_X[1] - MIC_X[0], a12 = MIC_Y[1] - MIC_Y[0];
  float a21 = MIC_X[2] - MIC_X[0], a22 = MIC_Y[2] - MIC_Y[0];
  float b1 = SPEED_OF_SOUND * tdoa01;
  float b2 = SPEED_OF_SOUND * tdoa02;

  float det = a11 * a22 - a12 * a21;
  if (fabsf(det) < 1e-9f) return false;

  float ux = (b1 * a22 - b2 * a12) / det;
  float uy = (a11 * b2 - a21 * b1) / det;
  float norm = sqrtf(ux * ux + uy * uy);
  if (norm < 1e-6f) return false;

  *azimuthOut = atan2f(uy / norm, ux / norm);
  return true;
}

// ---------------------------------------------------------------------------
// Frame pipeline
// ---------------------------------------------------------------------------
void processFrame() {
  windowToComplex(chA, specA);
  windowToComplex(chB, specB);
  windowToComplex(chC, specC);
  fftForward(specA);
  fftForward(specB);
  fftForward(specC);

  crossSpectrumPHAT(specA, specB, xcorr01);
  crossSpectrumPHAT(specA, specC, xcorr02);
  fftInverse(xcorr01);
  fftInverse(xcorr02);

  float dist01 = hypotf(MIC_X[1] - MIC_X[0], MIC_Y[1] - MIC_Y[0]);
  float dist02 = hypotf(MIC_X[2] - MIC_X[0], MIC_Y[2] - MIC_Y[0]);
  float maxLag01 = dist01 / SPEED_OF_SOUND * FS_PER_CHANNEL;
  float maxLag02 = dist02 / SPEED_OF_SOUND * FS_PER_CHANNEL;

  float lag01 = peakLagSamples(xcorr01, maxLag01);
  float lag02 = peakLagSamples(xcorr02, maxLag02);
  float tdoa01 = lag01 / FS_PER_CHANNEL;
  float tdoa02 = lag02 / FS_PER_CHANNEL;

  float azimuth;
  if (!solveAzimuth(tdoa01, tdoa02, &azimuth)) return;

  // Plain circular mean accumulator -- confidence weighting this was tested and its sign
  // flips with room reverberation time, i.e. it isn't measuring anything real.
  accCos += cosf(azimuth);
  accSin += sinf(azimuth);
  accCount++;

  if (accCount >= ACC_FRAMES) {
    float meanAz = atan2f(accSin, accCos) * 180.0f / (float)M_PI;
    Serial.printf("azimuth_deg=%.2f  (over %d frames)\n", meanAz, accCount);
    accCos = 0.0f; accSin = 0.0f; accCount = 0;
  }
}

// ---------------------------------------------------------------------------
void setup() {
  Serial.begin(921600);
  dsps_fft2r_init_fc32(NULL, FFT_LEN);
  adcInit();
}

void loop() {
  if (!frame_ready) return;
  frame_ready = false;

  uint32_t bytesRead = 0;
  esp_err_t err = adc_continuous_read(adc_handle, dma_raw, DMA_BUF_BYTES, &bytesRead, 0);
  if (err != ESP_OK || bytesRead < (uint32_t)DMA_BUF_BYTES) return;

  demux(dma_raw, bytesRead);
  processFrame();
}
