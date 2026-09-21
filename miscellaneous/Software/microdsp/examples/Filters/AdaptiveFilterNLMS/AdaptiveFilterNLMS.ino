// Multi-tap normalised LMS.
//
// The single-tap version can only scale the reference. When the interference
// reaches your signal delayed or filtered, you need several taps to model it.
// Step size is normalised by reference power, so a mu in (0, 2) is stable no
// matter how large the input is.
#include <microdsp.h>

MicroDSP dsp;

// Weights persist across calls, so adaptation carries over between buffers.
const size_t NUM_TAPS = 6;
float weights[NUM_TAPS] = {0, 0, 0, 0, 0, 0};

void setup() {
  Serial.begin(9600);

  const size_t LEN = 128;
  float data[LEN], reference[LEN];

  // The interference arrives two samples late, which one tap cannot cancel.
  for (size_t i = 0; i < LEN; i++) {
    reference[i] = sin(0.2 * i);
    float delayed = (i >= 2) ? sin(0.2 * (i - 2)) : 0.0;
    data[i] = 3.0 + 1.5 * delayed;
  }

  if (!dsp.adaptiveFilterFIR(data, reference, LEN, 0.5, weights, NUM_TAPS)) {
    Serial.println(F("NLMS failed"));
    return;
  }

  Serial.println(F("Cleaned output (last 8, should approach 3.0):"));
  for (size_t i = LEN - 8; i < LEN; i++) { Serial.print(data[i], 3); Serial.print(' '); }
  Serial.println();

  Serial.println(F("Learned weights:"));
  for (size_t i = 0; i < NUM_TAPS; i++) { Serial.print(weights[i], 4); Serial.print(' '); }
  Serial.println();
}

void loop() {}
