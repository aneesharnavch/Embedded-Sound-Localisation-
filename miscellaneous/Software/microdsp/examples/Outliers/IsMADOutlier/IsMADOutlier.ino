// MAD outlier test: |x - median| / MAD > threshold.
//
// Same robust scale estimate as the modified z-score, but without the 0.6745
// normal-consistency constant, so at an equal threshold this test is slightly
// more permissive. Pick one and stay with it.
#include <microdsp.h>

MicroDSP dsp;

void setup() {
  Serial.begin(9600);

  float data[] = {5.0, 5.2, 4.9, 5.1, 5.3, 4.8, 5.0};
  size_t len = sizeof(data) / sizeof(data[0]);

  float probe = 12.0;
  Serial.print(F("MAD test:        "));
  Serial.println(dsp.isMADOutlier(probe, data, len, 3.5) ? F("outlier") : F("normal"));
  Serial.print(F("Modified z test: "));
  Serial.println(dsp.isModifiedZScoreOutlier(probe, data, len, 3.5) ? F("outlier") : F("normal"));
}

void loop() {}
