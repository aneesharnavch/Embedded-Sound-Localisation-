// JSON export, which is what tools/export_decoder.py reads.
//
// Pipe the serial output through the decoder to get a CSV file:
//   python export_decoder.py --port COM3 --out data.csv
#include <microdsp.h>

MicroDSP dsp;

void setup() {
  Serial.begin(9600);

  float data[8];
  for (size_t i = 0; i < 8; i++) data[i] = sin(2.0 * PI * i / 8.0);

  // {"type":"microdsp","label":"sine","data":[...]}
  dsp.exportJSONToSerial(data, 8, "sine");

  // Statistics alongside it, so the log records what was measured.
  float summary[3] = { dsp.mean(data, 8), dsp.stdDev(data, 8), dsp.rms(data, 8) };
  dsp.exportJSONToSerial(summary, 3, "mean_sd_rms");
}

void loop() {}
