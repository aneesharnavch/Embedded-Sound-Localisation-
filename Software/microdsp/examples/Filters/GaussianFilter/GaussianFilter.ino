// Gaussian smoothing.
//
// The kernel is renormalised over whatever taps land inside the array, so the
// first and last few samples are smoothed without being pulled towards zero.
#include <microdsp.h>

MicroDSP dsp;

void setup() {
  Serial.begin(9600);

  // Constant input: a correctly normalised filter returns it unchanged,
  // edges included.
  float flat[12];
  for (size_t i = 0; i < 12; i++) flat[i] = 5.0;
  dsp.gaussianFilter(flat, 12, 1.5);
  Serial.print(F("Constant 5.0 in, out: "));
  for (size_t i = 0; i < 12; i++) { Serial.print(flat[i], 2); Serial.print(' '); }
  Serial.println();

  // Noisy data actually being smoothed.
  float data[] = {1.0, 5.0, 2.0, 8.0, 3.0, 6.0, 2.0, 7.0};
  size_t len = sizeof(data) / sizeof(data[0]);
  if (dsp.gaussianFilter(data, len, 1.0)) {
    Serial.print(F("Smoothed: "));
    for (size_t i = 0; i < len; i++) { Serial.print(data[i], 3); Serial.print(' '); }
    Serial.println();
  }

  // sigma must be positive; anything else is rejected and the data is left be.
  Serial.print(F("sigma = 0 accepted? "));
  Serial.println(dsp.gaussianFilter(data, len, 0.0) ? F("yes") : F("no"));
}

void loop() {}
