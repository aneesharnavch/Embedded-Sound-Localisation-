// Median filter: removes impulsive spikes without smearing edges.
#include <microdsp.h>

MicroDSP dsp;

void setup() {
  Serial.begin(9600);

  // A clean ramp with one bad sample dropped into the middle.
  float data[] = {1.0, 2.0, 3.0, 4.0, 100.0, 6.0, 7.0, 8.0, 9.0};
  size_t len = sizeof(data) / sizeof(data[0]);

  Serial.print(F("Before: "));
  for (size_t i = 0; i < len; i++) { Serial.print(data[i]); Serial.print(' '); }
  Serial.println();

  if (!dsp.medianFilter(data, len, 3)) {
    Serial.println(F("medianFilter failed"));
    return;
  }

  Serial.print(F("After:  "));
  for (size_t i = 0; i < len; i++) { Serial.print(data[i]); Serial.print(' '); }
  Serial.println();
  Serial.println(F("The 100.0 spike is gone; the ramp is otherwise intact."));
}

void loop() {}
