// Scalar Wiener gain: data *= signalVar / (signalVar + noiseVar).
//
// A single attenuation factor from your estimate of signal and noise power.
// Cheap, and useful when you know roughly how noisy the channel is.
#include <microdsp.h>

MicroDSP dsp;

void setup() {
  Serial.begin(9600);

  float data[] = {1.0, 2.0, 3.0, 4.0, 5.0};
  size_t len = sizeof(data) / sizeof(data[0]);

  float signalVar = 4.0;
  float noiseVar  = 1.0;
  // Expected gain here is 4/(4+1) = 0.8.
  if (dsp.wienerFilter(data, len, signalVar, noiseVar)) {
    Serial.print(F("Filtered: "));
    for (size_t i = 0; i < len; i++) { Serial.print(data[i], 3); Serial.print(' '); }
    Serial.println();
  }

  // Both variances zero would divide by zero, so it is rejected instead.
  Serial.print(F("Zero variances accepted? "));
  Serial.println(dsp.wienerFilter(data, len, 0.0, 0.0) ? F("yes") : F("no"));
}

void loop() {}
