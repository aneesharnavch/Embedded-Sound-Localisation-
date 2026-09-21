// Sliding-window statistics on live ADC data.
//
// Construct the window ONCE (here as a global) and call update() on that same
// object. Building it inside loop() would create an empty window every
// iteration and it would never accumulate any history.
#include <microdsp.h>

// ADC scaling differs per board.
#if defined(ESP32)
  const float ADC_VREF = 3.3, ADC_MAX = 4095.0;
#elif defined(ESP8266)
  const float ADC_VREF = 3.3, ADC_MAX = 1023.0;
#else
  const float ADC_VREF = 5.0, ADC_MAX = 1023.0;   // classic 5 V AVR
#endif

dspRealTime::RealTimeStats stats(16);

void setup() {
  Serial.begin(9600);
  // On a small board it is worth checking the buffer was actually allocated.
  if (!stats.ok()) Serial.println(F("could not allocate the window!"));
}

void loop() {
  float voltage = analogRead(A0) * (ADC_VREF / ADC_MAX);
  stats.update(voltage);

  Serial.print(F("n=")); Serial.print(stats.count());
  Serial.print(F(" mean=")); Serial.print(stats.getMean(), 4);
  Serial.print(F(" sd=")); Serial.print(stats.getStdDev(), 4);
  Serial.print(F(" min=")); Serial.print(stats.getMin(), 3);
  Serial.print(F(" max=")); Serial.print(stats.getMax(), 3);
  Serial.print(F(" median=")); Serial.print(stats.getMedian(), 4);

  // Every outlier test judges the newest sample.
  if (stats.isZScoreOutlier(3.0)) Serial.print(F("  <-- spike"));
  Serial.println();

  delay(100);
}
