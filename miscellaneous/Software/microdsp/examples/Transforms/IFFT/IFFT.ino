// Round trip: fft() then ifft() should return the original samples.
#include <microdsp.h>

MicroDSP dsp;

void setup() {
  Serial.begin(9600);

  const size_t N = 16;
  float original[N], real[N], imag[N];

  for (size_t i = 0; i < N; i++) {
    original[i] = sin(2.0 * PI * i / N) * 3.0;
    real[i] = original[i];
    imag[i] = 0.0;
  }

  if (!dsp.fft(real, imag, N) || !dsp.ifft(real, imag, N)) {
    Serial.println(F("transform failed"));
    return;
  }

  Serial.println(F("original\trecovered\terror"));
  float worst = 0;
  for (size_t i = 0; i < N; i++) {
    float err = fabs(original[i] - real[i]);
    if (err > worst) worst = err;
    Serial.print(original[i], 4); Serial.print('\t');
    Serial.print(real[i], 4); Serial.print('\t');
    Serial.println(err, 6);
  }
  Serial.print(F("Worst error: ")); Serial.println(worst, 6);
  Serial.println(F("Small residuals are normal: this is 32-bit float arithmetic."));
}

void loop() {}
