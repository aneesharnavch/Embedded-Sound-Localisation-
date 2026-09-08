// Getting data off the board.
//
// None of these build an Arduino String, so they do not fragment the heap.
#include <microdsp.h>

MicroDSP dsp;

void setup() {
  Serial.begin(9600);

  float data[] = {1.5, 2.25, 3.125, 4.0, 5.5};
  size_t len = sizeof(data) / sizeof(data[0]);

  // One value per line, with a heading.
  Serial.println(F("--- one per line ---"));
  dsp.exportToSerial(data, len, "My Data");

  // Single comma-separated row: easy to paste into a spreadsheet.
  Serial.println(F("--- single row ---"));
  dsp.exportRowToSerial(data, len, "My Data");

  // Any Stream works, not just Serial.
  dspDataIO::exportCSVRow(Serial, data, len, "explicit stream");

  // Obfuscated output. Note the name: a one-byte XOR is NOT encryption and is
  // trivially recovered. export_decoder.py can undo it given the key.
  Serial.println(F("--- XOR obfuscated (not secure) ---"));
  dspDataIO::exportObfuscatedXOR(data, len, 0x5A);
}

void loop() {}
