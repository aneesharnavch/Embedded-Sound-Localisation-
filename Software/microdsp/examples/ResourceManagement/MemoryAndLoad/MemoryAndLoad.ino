// Adapting the workload to whatever RAM and CPU headroom is left.
//
// A practical pattern: pick the FFT size you can afford, and back off when the
// duty cycle gets too high.
#include <microdsp.h>

MicroDSP dsp;

size_t chooseFFTSize() {
  // Each size needs two float arrays (real + imaginary).
  const size_t candidates[] = {256, 128, 64, 32, 16};
  for (size_t i = 0; i < 5; i++) {
    size_t bytes = candidates[i] * sizeof(float) * 2;
    if (dsp.canProcess(bytes)) return candidates[i];
  }
  return 0;
}

void setup() {
  Serial.begin(9600);
  dsp.begin();
  dsp.setComputeLimit(60);
  dsp.setFreeMemoryThreshold(300);

  Serial.print(F("Free RAM: "));
  Serial.println(dsp.freeMemory());

  size_t n = chooseFFTSize();
  Serial.print(F("Largest affordable FFT: "));
  Serial.println(n);

  if (n == 0) {
    Serial.println(F("Not enough RAM for any FFT size."));
    return;
  }

  float* real = dspDataManager::allocateZeroedBuffer(n);
  float* imag = dspDataManager::allocateZeroedBuffer(n);
  if (!real || !imag) {
    Serial.println(F("allocation failed after all"));
  } else {
    for (size_t i = 0; i < n; i++) real[i] = sin(2.0 * PI * 4 * i / n);

    dsp.beginWork();
    bool okFFT = dsp.fft(real, imag, n);
    dsp.endWork();

    Serial.print(F("FFT ok? ")); Serial.println(okFFT ? F("yes") : F("no"));
    Serial.print(F("Time spent in DSP: ")); Serial.print(dsp.getLoadPercent(), 2);
    Serial.println(F("%"));
    Serial.print(F("Free RAM while held: ")); Serial.println(dsp.freeMemory());
  }

  dspDataManager::releaseBuffer(real);
  dspDataManager::releaseBuffer(imag);
  Serial.print(F("Free RAM after release: ")); Serial.println(dsp.freeMemory());
}

void loop() {}
