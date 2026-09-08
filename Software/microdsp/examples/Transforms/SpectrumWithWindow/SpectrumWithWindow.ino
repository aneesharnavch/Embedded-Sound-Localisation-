// Why you window before an FFT.
//
// The FFT assumes the buffer repeats forever. If it does not contain a whole
// number of cycles, that discontinuity smears energy across every bin
// ("spectral leakage"). Multiplying by a window tapers the ends and largely
// removes it.
#include <microdsp.h>

MicroDSP dsp;

const size_t N = 64;
const float SAMPLE_RATE = 640.0;
// Deliberately between bins (bin spacing is 10 Hz) to provoke leakage.
const float TONE = 105.0;

static float leakage(const float* magnitude, size_t n, size_t peakBin) {
  // Energy outside the peak and its immediate neighbours.
  float other = 0;
  for (size_t i = 1; i < n / 2; i++) {
    if (i + 1 < peakBin || i > peakBin + 1) other += magnitude[i];
  }
  return other;
}

void setup() {
  Serial.begin(9600);

  float real[N], imag[N], magnitude[N], window[N];

  // --- without a window ---------------------------------------------------
  for (size_t i = 0; i < N; i++) {
    real[i] = sin(2.0 * PI * TONE * i / SAMPLE_RATE);
    imag[i] = 0.0;
  }
  dsp.fft(real, imag, N);
  dsp.fftMagnitude(real, imag, magnitude, N);
  size_t peak = 10;   // 105 Hz sits between bins 10 and 11
  Serial.print(F("Leakage, rectangular (no window): "));
  Serial.println(leakage(magnitude, N, peak), 3);

  // --- with a Hann window -------------------------------------------------
  dsp.hannWindow(window, N);
  for (size_t i = 0; i < N; i++) {
    real[i] = sin(2.0 * PI * TONE * i / SAMPLE_RATE);
    imag[i] = 0.0;
  }
  dsp.applyWindow(real, window, N);
  dsp.fft(real, imag, N);
  dsp.fftMagnitude(real, imag, magnitude, N);
  Serial.print(F("Leakage, Hann window:            "));
  Serial.println(leakage(magnitude, N, peak), 3);

  Serial.println(F("hammingWindow and blackmanWindow are also available."));
  Serial.println(F("Blackman leaks least but widens the peak the most."));
}

void loop() {}
