// Single-tap LMS adaptive noise cancellation.
//
// You supply a reference that correlates with the interference but not with the
// signal you want. The filter learns how much of the reference is present and
// subtracts it; `data` comes back holding what is LEFT, i.e. the cleaned signal.
#include <microdsp.h>

MicroDSP dsp;

void setup() {
  Serial.begin(9600);

  const size_t LEN = 64;
  float data[LEN], reference[LEN];

  // Wanted: a steady 5.0. Interference: a sine, also visible on `reference`.
  for (size_t i = 0; i < LEN; i++) {
    reference[i] = sin(0.3 * i);
    data[i] = 5.0 + 2.0 * reference[i];
  }

  if (!dsp.adaptiveFilter(data, reference, LEN, 0.05)) {
    Serial.println(F("adaptiveFilter failed"));
    return;
  }

  // After a short convergence period the output should sit near 5.0.
  Serial.println(F("Cleaned output (last 8 samples, should approach 5.0):"));
  for (size_t i = LEN - 8; i < LEN; i++) { Serial.print(data[i], 3); Serial.print(' '); }
  Serial.println();

  Serial.println(F("A larger mu converges faster but overshoots; too large and"));
  Serial.println(F("it never settles."));
}

void loop() {}
