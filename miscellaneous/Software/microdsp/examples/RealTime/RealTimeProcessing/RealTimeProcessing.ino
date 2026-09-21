// Running several streaming filters over one input at the same time.
//
// All of these are O(1) or O(window) per sample and allocate nothing after
// construction, so they are safe to call at audio-ish rates.
#include <microdsp.h>

#if defined(ESP32)
  const float ADC_VREF = 3.3, ADC_MAX = 4095.0;
#elif defined(ESP8266)
  const float ADC_VREF = 3.3, ADC_MAX = 1023.0;
#else
  const float ADC_VREF = 5.0, ADC_MAX = 1023.0;
#endif

dspRealTime::RealTimeMovingAverage average(8);
dspRealTime::RealTimeMedianFilter median(5);
dspRealTime::RealTimeGaussianFilter smooth(9, 2.0);

void setup() {
  Serial.begin(9600);
  if (!average.ok() || !median.ok() || !smooth.ok()) {
    Serial.println(F("allocation failed"));
  }
  Serial.println(F("raw\taverage\tmedian\tgaussian"));
}

void loop() {
  float raw = analogRead(A0) * (ADC_VREF / ADC_MAX);

  // Each returns the filtered value for the sample just added. The Gaussian
  // filter holds unity gain from the very first sample, so these are directly
  // comparable against each other and against `raw`.
  Serial.print(raw, 4);                     Serial.print('\t');
  Serial.print(average.update(raw), 4);     Serial.print('\t');
  Serial.print(median.update(raw), 4);      Serial.print('\t');
  Serial.println(smooth.update(raw), 4);

  delay(50);
}
