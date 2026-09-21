// Capping how much CPU time DSP work is allowed to consume.
//
// The limit is cooperative: bracket the expensive work in beginWork()/endWork()
// and the library measures what fraction of wall-clock time you spend inside
// it. shouldProcess() then tells you whether you are inside your budget.
#include <microdsp.h>

MicroDSP dsp;

float buffer[64];
unsigned long skipped = 0, processed = 0;

void setup() {
  Serial.begin(9600);

  dsp.begin();              // starts load accounting
  dsp.setComputeLimit(40);  // spend at most 40% of the time doing DSP

  Serial.print(F("Compute limit: "));
  Serial.print(dsp.getComputeLimit());
  Serial.println(F("%"));
}

void loop() {
  // Ask before doing the work; skip this round if we are over budget.
  if (dsp.shouldProcess()) {
    dsp.beginWork();

    for (size_t i = 0; i < 64; i++) buffer[i] = sin(0.1 * (i + processed));
    float re[64], im[64];
    for (size_t i = 0; i < 64; i++) { re[i] = buffer[i]; im[i] = 0; }
    dsp.fft(re, im, 64);

    dsp.endWork();
    processed++;
  } else {
    skipped++;
  }

  static unsigned long lastReport = 0;
  if (millis() - lastReport > 1000) {
    lastReport = millis();
    Serial.print(F("load="));       Serial.print(dsp.getLoadPercent(), 1);
    Serial.print(F("%  done="));    Serial.print(processed);
    Serial.print(F("  skipped=")); Serial.println(skipped);
  }
}
