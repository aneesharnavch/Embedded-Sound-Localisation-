// Standard deviation, population and sample forms.
#include <microdsp.h>

MicroDSP dsp;

void setup() {
  Serial.begin(9600);

  float data[] = {2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0};
  size_t len = sizeof(data) / sizeof(data[0]);

  Serial.print(F("Mean:              ")); Serial.println(dsp.mean(data, len));
  // Divisor n: use this when the array IS the whole population.
  Serial.print(F("StdDev (pop, /n):  ")); Serial.println(dsp.stdDev(data, len));
  // Divisor n-1: use this when the array is a sample of something larger.
  Serial.print(F("StdDev (samp,/n-1):")); Serial.println(dsp.sampleStdDev(data, len));
  Serial.print(F("Variance:          ")); Serial.println(dsp.variance(data, len));
  Serial.print(F("RMS:               ")); Serial.println(dsp.rms(data, len));
  Serial.print(F("Min / Max:         "));
  Serial.print(dsp.minimum(data, len)); Serial.print(F(" / "));
  Serial.println(dsp.maximum(data, len));
}

void loop() {}
