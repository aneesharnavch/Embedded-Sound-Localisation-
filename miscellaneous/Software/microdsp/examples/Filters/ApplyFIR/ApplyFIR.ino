// Applying a set of FIR coefficients you already have.
//
// applyFIR runs in place and allocates nothing: it walks the array backwards so
// every sample it reads is still an original.
#include <microdsp.h>

MicroDSP dsp;

void setup() {
  Serial.begin(9600);

  float data[] = {1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0};
  size_t len = sizeof(data) / sizeof(data[0]);

  // A simple 3-tap smoother summing to 1.0, so DC gain is unity.
  float coeffs[] = {0.25, 0.5, 0.25};
  size_t coeffLen = sizeof(coeffs) / sizeof(coeffs[0]);

  if (!dsp.applyFIR(data, len, coeffs, coeffLen)) {
    Serial.println(F("applyFIR failed"));
    return;
  }

  Serial.print(F("Filtered: "));
  for (size_t i = 0; i < len; i++) { Serial.print(data[i], 3); Serial.print(' '); }
  Serial.println();
  Serial.println(F("The first samples ramp up: taps hanging off the start are"));
  Serial.println(F("treated as zeros."));
}

void loop() {}
