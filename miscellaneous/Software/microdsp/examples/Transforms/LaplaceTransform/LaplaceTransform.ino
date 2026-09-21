// Numerical Laplace transform: F(s) = integral f(t) e^(-st) dt.
//
// This evaluates the transform at ONE complex point s and returns a single
// complex number, which is what a transform means. Pass the sample interval so
// the integral is scaled correctly.
#include <microdsp.h>

MicroDSP dsp;

void setup() {
  Serial.begin(9600);

  // f(t) = e^(-t), whose transform is known exactly: F(s) = 1/(s+1).
  //
  // A finer dt gives a closer answer, but the buffer has to fit in RAM: 500
  // floats is 2 KB, which is the entire data space of an Uno.
#if defined(ARDUINO_ARCH_AVR)
  const size_t N = 128;
  const float dt = 0.04;
#else
  const size_t N = 500;
  const float dt = 0.01;
#endif
  static float signal[N];
  for (size_t i = 0; i < N; i++) signal[i] = exp(-(float)i * dt);

  float sReal = 1.0, sImag = 0.0;
  float outReal = 0, outImag = 0;

  if (!dsp.laplaceTransform(signal, N, dt, sReal, sImag, outReal, outImag)) {
    Serial.println(F("laplaceTransform failed"));
    return;
  }

  Serial.print(F("F(1) numerically: "));
  Serial.print(outReal, 4); Serial.print(F(" + j")); Serial.println(outImag, 4);
  Serial.print(F("F(1) exactly:     "));
  Serial.println(1.0 / (sReal + 1.0), 4);
  // The gap is the rectangle rule's discretisation error, so it shrinks with dt
  // and is larger on AVR where the buffer has to be coarser.
  Serial.println(F("(the difference is the rectangle rule's step size)"));

  // Sweeping the imaginary part traces the frequency response.
  Serial.println(F("\nomega\t|F(j*omega)|"));
  for (float omega = 0.0; omega <= 5.0; omega += 1.0) {
    dsp.laplaceTransform(signal, N, dt, 0.0, omega, outReal, outImag);
    Serial.print(omega, 1); Serial.print('\t');
    Serial.println(sqrt(outReal * outReal + outImag * outImag), 4);
  }
}

void loop() {}
