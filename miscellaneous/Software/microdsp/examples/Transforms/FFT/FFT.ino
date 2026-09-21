// Forward FFT of a known tone.
//
// The transform is in place and radix-2: len MUST be a power of two. fft()
// returns false for anything else rather than quietly producing nonsense.
#include <microdsp.h>

MicroDSP dsp;

void setup() {
  Serial.begin(9600);

  const size_t N = 32;                 // power of two
  const float SAMPLE_RATE = 320.0;     // Hz
  const float TONE = 40.0;             // Hz -> lands exactly on bin 4

  float real[N], imag[N];
  for (size_t i = 0; i < N; i++) {
    real[i] = sin(2.0 * PI * TONE * i / SAMPLE_RATE);
    imag[i] = 0.0;                     // real-valued input
  }

  if (!dsp.fft(real, imag, N)) {
    Serial.println(F("fft failed: length must be a power of two"));
    return;
  }

  // Only the first half is unique for real input.
  float magnitude[N];
  dsp.fftMagnitude(real, imag, magnitude, N);

  Serial.println(F("bin\tHz\tmagnitude"));
  for (size_t i = 0; i < N / 2; i++) {
    Serial.print(i); Serial.print('\t');
    Serial.print(i * SAMPLE_RATE / N, 1); Serial.print('\t');
    Serial.println(magnitude[i], 3);
  }

  Serial.print(F("Dominant frequency: "));
  Serial.print(dsp.dominantFrequency(real, imag, N, SAMPLE_RATE), 2);
  Serial.println(F(" Hz"));

  // Non-power-of-two lengths are refused.
  float a[6], b[6];
  Serial.print(F("Length 6 accepted? "));
  Serial.println(dsp.fft(a, b, 6) ? F("yes") : F("no"));
}

void loop() {}
