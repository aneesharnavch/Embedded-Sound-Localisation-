// Numerical derivatives, both the allocating and the allocation-free form.
#include <microdsp.h>

MicroDSP dsp;

void setup() {
  Serial.begin(9600);

  float data[] = {1.0, 2.0, 4.0, 7.0, 11.0};
  size_t len = sizeof(data) / sizeof(data[0]);

  // --- Form 1: library allocates the result -------------------------------
  // derivative() hands back a buffer you own. Release it with freeBuffer().
  size_t outLen = 0;
  float* d1 = dsp.derivative(data, len, 1.0, 1, outLen);
  if (d1) {
    Serial.print(F("1st derivative: "));
    for (size_t i = 0; i < outLen; i++) { Serial.print(d1[i]); Serial.print(' '); }
    Serial.println();
    dsp.freeBuffer(d1);            // <-- required, or the memory leaks
  } else {
    Serial.println(F("derivative() failed (bad arguments or out of memory)"));
  }

  // --- Form 2: no allocation at all --------------------------------------
  // Preferred on small boards. `out` needs len - order entries.
  float out[4];
  size_t n = dsp.derivativeInto(data, len, 1.0, 2, out);
  Serial.print(F("2nd derivative: "));
  for (size_t i = 0; i < n; i++) { Serial.print(out[i]); Serial.print(' '); }
  Serial.println();

  // A zero sample interval is rejected rather than producing infinities.
  Serial.print(F("deltaT = 0 gives: "));
  Serial.println(dsp.derivativeInto(data, len, 0.0, 1, out));
}

void loop() {}
