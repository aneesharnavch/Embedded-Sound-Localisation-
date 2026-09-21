// Running integral: position from velocity, for example.
#include <microdsp.h>

MicroDSP dsp;

void setup() {
  Serial.begin(9600);

  // Constant velocity of 2 units/s sampled every 0.5 s.
  float velocity[] = {2.0, 2.0, 2.0, 2.0, 2.0, 2.0};
  size_t len = sizeof(velocity) / sizeof(velocity[0]);
  float dt = 0.5;

  float position[6];
  if (dsp.cumulativeIntegral(velocity, len, dt, position)) {
    Serial.println(F("t\tv\tposition"));
    for (size_t i = 0; i < len; i++) {
      Serial.print(i * dt, 2); Serial.print('\t');
      Serial.print(velocity[i], 2); Serial.print('\t');
      Serial.println(position[i], 3);
    }
  }
}

void loop() {}
