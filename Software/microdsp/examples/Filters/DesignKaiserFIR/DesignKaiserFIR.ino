// Designing a Kaiser-windowed lowpass FIR, then applying it.
//
// designKaiserFIR multiplies an ideal sinc by a Kaiser window and normalises to
// unity DC gain. cutoffNorm is a fraction of the sample rate: 0.1 means fs/10.
// A larger beta buys deeper stopband attenuation at the cost of a wider
// transition band.
#include <microdsp.h>

MicroDSP dsp;

void setup() {
  Serial.begin(9600);

  const size_t TAPS = 21;
  float coeffs[TAPS];

  // 1 kHz sampling, cutoff at 100 Hz -> 100/1000 = 0.1.
  if (!dsp.designKaiserFIR(coeffs, TAPS, 5.0, 0.1)) {
    Serial.println(F("design failed (check that 0 < cutoff < 0.5)"));
    return;
  }

  Serial.println(F("Coefficients:"));
  float sum = 0;
  for (size_t i = 0; i < TAPS; i++) {
    Serial.print(coeffs[i], 5); Serial.print(' ');
    sum += coeffs[i];
  }
  Serial.println();
  // A real lowpass has negative side lobes and sums to 1.
  Serial.print(F("Sum of taps (DC gain): ")); Serial.println(sum, 5);

  // Apply it to a mix of a slow and a fast component; the fast one should
  // largely disappear.
  const size_t LEN = 64;
  float signal[LEN];
  for (size_t i = 0; i < LEN; i++) {
    signal[i] = sin(2.0 * PI * 0.02 * i)     // 20 Hz, inside the passband
              + sin(2.0 * PI * 0.35 * i);    // 350 Hz, well into the stopband
  }
  dsp.applyFIR(signal, LEN, coeffs, TAPS);

  Serial.println(F("Filtered tail (fast component suppressed):"));
  for (size_t i = LEN - 8; i < LEN; i++) { Serial.print(signal[i], 3); Serial.print(' '); }
  Serial.println();

  // If you only want the window itself, ask for it directly.
  float window[TAPS];
  dsp.kaiserWindow(window, TAPS, 5.0);
  Serial.print(F("Kaiser window centre tap: ")); Serial.println(window[TAPS / 2], 4);
}

void loop() {}
