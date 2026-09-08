// Modified z-score: 0.6745 * (x - median) / MAD.
//
// Built on the median rather than the mean, so a couple of extreme samples do
// not drag the threshold along with them the way a plain z-score does.
#include <microdsp.h>

MicroDSP dsp;

void setup() {
  Serial.begin(9600);

  float data[] = {10.0, 10.5, 9.8, 10.2, 10.1, 9.9, 10.3};
  size_t len = sizeof(data) / sizeof(data[0]);

  Serial.print(F("Median: ")); Serial.println(dsp.median(data, len));

  Serial.print(F("50.0 an outlier? "));
  Serial.println(dsp.isModifiedZScoreOutlier(50.0, data, len, 3.5) ? F("yes") : F("no"));

  // When most of the window holds one value the MAD collapses to zero. The
  // library falls back to the mean absolute deviation so the outlier is still
  // caught rather than masked.
  float masked[] = {10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 1000.0};
  Serial.print(F("1000 against a masked window? "));
  Serial.println(dsp.isModifiedZScoreOutlier(1000.0, masked, 8) ? F("yes") : F("no"));
}

void loop() {}
