// Frequency-sampling FIR design.
//
// You specify the magnitude you want at each DFT bin and get back a
// linear-phase impulse response. desiredResponse needs numTaps/2 + 1 entries,
// covering bins 0 .. numTaps/2; bin k sits at k * fs / numTaps.
#include <microdsp.h>

MicroDSP dsp;

void setup() {
  Serial.begin(9600);

  const size_t TAPS = 17;
  const size_t BINS = TAPS / 2 + 1;      // 9 entries for 17 taps

  // Pass the lowest three bins, stop the rest.
  float desired[BINS];
  for (size_t k = 0; k < BINS; k++) desired[k] = (k <= 2) ? 1.0 : 0.0;

  float coeffs[TAPS];
  if (!dsp.frequencySamplingFIR(coeffs, TAPS, desired)) {
    Serial.println(F("design failed"));
    return;
  }

  Serial.println(F("Coefficients (symmetric about the centre = linear phase):"));
  for (size_t i = 0; i < TAPS; i++) { Serial.print(coeffs[i], 4); Serial.print(' '); }
  Serial.println();

  Serial.print(F("coeffs[0] vs coeffs[16]: "));
  Serial.print(coeffs[0], 4); Serial.print(F(" / ")); Serial.println(coeffs[TAPS - 1], 4);
}

void loop() {}
