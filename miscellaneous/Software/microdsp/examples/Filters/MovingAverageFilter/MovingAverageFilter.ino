// Moving average, in both causal and centred form.
//
// The two differ in timing: the causal version only ever looks backwards, so
// its output lags the input by about half a window. The centred version stays
// aligned with the input. That matters as soon as you compare the filtered
// signal against anything else.
#include <microdsp.h>

MicroDSP dsp;

static void show(const char* label, float* d, size_t n) {
  Serial.print(label);
  for (size_t i = 0; i < n; i++) { Serial.print(d[i], 2); Serial.print(' '); }
  Serial.println();
}

void setup() {
  Serial.begin(9600);

  const size_t LEN = 9;
  float original[LEN] = {0, 0, 0, 9, 0, 0, 0, 0, 0};

  float causal[LEN], centred[LEN];
  memcpy(causal, original, sizeof(original));
  memcpy(centred, original, sizeof(original));

  show("input:    ", original, LEN);

  // Returns false on bad arguments (window 0, null pointer, no memory).
  if (dsp.movingAverageFilter(causal, LEN, 3))          show("causal:   ", causal, LEN);
  if (dsp.movingAverageFilterCentered(centred, LEN, 3)) show("centred:  ", centred, LEN);

  Serial.println(F("The impulse sits at index 3; note where each result puts it."));
}

void loop() {}
