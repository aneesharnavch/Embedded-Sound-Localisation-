// Definite integration: rectangle rule vs trapezoidal rule.
#include <microdsp.h>

MicroDSP dsp;

void setup() {
  Serial.begin(9600);

  // A straight ramp, where the exact area is easy to check by hand.
  float data[] = {0.0, 1.0, 2.0, 3.0, 4.0};
  size_t len = sizeof(data) / sizeof(data[0]);
  float dt = 1.0;

  // Rectangle rule: dt * sum(f). Simple, but biased on a slope.
  Serial.print(F("Rectangle:   ")); Serial.println(dsp.integral(data, len, dt));
  // Trapezoidal rule: second-order accurate, exact for a straight line.
  Serial.print(F("Trapezoidal: ")); Serial.println(dsp.integralTrapezoid(data, len, dt));
  Serial.println(F("(exact area under 0..4 is 8.0)"));
}

void loop() {}
