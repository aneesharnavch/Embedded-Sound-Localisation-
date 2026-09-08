// Z-score outlier test: |x - mean| / stdDev > threshold.
#include <microdsp.h>

MicroDSP dsp;

void setup() {
  Serial.begin(9600);

  float data[] = {10.0, 10.5, 9.8, 10.2, 10.1, 9.9, 10.3};
  size_t len = sizeof(data) / sizeof(data[0]);

  Serial.print(F("50.0 an outlier? "));
  Serial.println(dsp.isZScoreOutlier(50.0, data, len, 3.0) ? F("yes") : F("no"));

  Serial.print(F("10.1 an outlier? "));
  Serial.println(dsp.isZScoreOutlier(10.1, data, len, 3.0) ? F("yes") : F("no"));

  // Constant data has no spread, so the z-score is undefined. The test reports
  // "no" instead of dividing by zero.
  float flat[] = {7.0, 7.0, 7.0, 7.0};
  Serial.print(F("Against constant data: "));
  Serial.println(dsp.isZScoreOutlier(99.0, flat, 4) ? F("yes") : F("no"));
}

void loop() {}
