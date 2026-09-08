// Sliding-window FFT on live data.
//
// windowSize must be a power of two. Note that update() recomputes the entire
// transform on every sample, which is O(n log n) each time; for anything but a
// slow sample rate use updateDeferred() and call transform() once per batch,
// as the second half of loop() shows.
#include <microdsp.h>

#if defined(ESP32)
  const float ADC_VREF = 3.3, ADC_MAX = 4095.0;
#else
  const float ADC_VREF = 5.0, ADC_MAX = 1023.0;
#endif

const size_t WINDOW = 32;              // power of two
const float SAMPLE_RATE = 100.0;       // matches the 10 ms delay below

dspRealTime::RealTimeFFT spectrum(WINDOW);

void setup() {
  Serial.begin(9600);
  if (!spectrum.ok()) {
    Serial.println(F("window size must be a power of two"));
    return;
  }
  // Tapering the window edges keeps a tone from smearing across every bin.
  spectrum.setUseHannWindow(true);
}

void loop() {
  float sample = analogRead(A0) * (ADC_VREF / ADC_MAX);

  // Buffer the sample without transforming yet.
  spectrum.updateDeferred(sample);

  // Transform once per window's worth of new samples instead of every sample.
  static size_t sinceTransform = 0;
  if (++sinceTransform >= WINDOW / 2 && spectrum.isReady()) {
    sinceTransform = 0;
    spectrum.transform();

    Serial.print(F("dominant: "));
    Serial.print(spectrum.dominantFrequency(SAMPLE_RATE), 2);
    Serial.print(F(" Hz  |  bins: "));
    for (size_t i = 1; i < WINDOW / 2; i++) {
      Serial.print(spectrum.magnitude(i), 2);
      Serial.print(' ');
    }
    Serial.println();
  }

  delay(10);
}
