// Arithmetic mean of a fixed array.
#include <microdsp.h>

MicroDSP dsp;

void setup() {
  Serial.begin(9600);

  float data[] = {1.0, 2.0, 3.0, 4.0, 5.0};
  size_t len = sizeof(data) / sizeof(data[0]);

  Serial.print(F("Mean: "));
  Serial.println(dsp.mean(data, len));

  // An empty array returns 0 rather than NaN.
  Serial.print(F("Mean of nothing: "));
  Serial.println(dsp.mean(data, 0));
}

void loop() {}
