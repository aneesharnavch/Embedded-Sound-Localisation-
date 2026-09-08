// Tukey's fences: outside [Q1 - m*IQR, Q3 + m*IQR].
//
// Quartiles are taken by linear interpolation, so they stay sensible on short
// arrays where picking a nearest index would be badly biased.
#include <microdsp.h>

MicroDSP dsp;

void setup() {
  Serial.begin(9600);

  float data[] = {1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0};
  size_t len = sizeof(data) / sizeof(data[0]);

  Serial.print(F("Q1: ")); Serial.println(dsp.percentile(data, len, 0.25));
  Serial.print(F("Q3: ")); Serial.println(dsp.percentile(data, len, 0.75));

  Serial.print(F("100.0 an outlier? "));
  Serial.println(dsp.isIQROutlier(100.0, data, len, 1.5) ? F("yes") : F("no"));
  Serial.print(F("4.5 an outlier?   "));
  Serial.println(dsp.isIQROutlier(4.5, data, len, 1.5) ? F("yes") : F("no"));
}

void loop() {}
