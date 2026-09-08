#ifndef DSP_DATA_IO_H
#define DSP_DATA_IO_H

#include <Arduino.h>

namespace dspDataIO {

	// Every function streams straight to the port a character at a time. None
	// of them build an Arduino String: concatenating into a String in a loop
	// reallocates on almost every append and fragments the heap, which on a
	// 2 KB part will eventually fail outright.
	//
	// `stream` defaults to Serial but any Stream works (Serial1, SoftwareSerial,
	// a file, a network client).

	// One value per line, optionally preceded by a label line.
	void exportCSV(const float* data, size_t len, const char* label = nullptr);
	void exportCSV(Stream& stream, const float* data, size_t len,
	               const char* label = nullptr);

	// Single comma-separated line, optionally prefixed with "[label] ".
	// Compact enough to paste into a spreadsheet or plot tool.
	void exportCSVRow(const float* data, size_t len, const char* label = nullptr,
	                  uint8_t decimals = 4);
	void exportCSVRow(Stream& stream, const float* data, size_t len,
	                  const char* label = nullptr, uint8_t decimals = 4);

	// JSON object: {"type":"microdsp","label":"...","data":[...]}
	// This is the format export_decoder.py reads.
	void exportJSON(const float* data, size_t len, const char* label = nullptr,
	                uint8_t decimals = 6);
	void exportJSON(Stream& stream, const float* data, size_t len,
	                const char* label = nullptr, uint8_t decimals = 6);

	// Prints a description line, then the data as CSV.
	void annotateAndExport(const float* data, size_t len, const char* description);

	// Byte-level XOR of the raw float bytes, emitted as zero-padded uppercase
	// hex pairs separated by spaces, one sample per line.
	//
	// This is OBFUSCATION, NOT ENCRYPTION. A single-byte XOR key is recovered
	// trivially from a few samples, so do not use it to protect anything that
	// matters. It is here to keep casual readers of a serial log out, and to
	// stay compatible with 1.x's exportEncrypted().
	//
	// Bytes are emitted in the MCU's native float byte order (little-endian on
	// AVR, ESP and ARM), which is what export_decoder.py assumes.
	void exportObfuscatedXOR(const float* data, size_t len, uint8_t key);
	void exportObfuscatedXOR(Stream& stream, const float* data, size_t len,
	                         uint8_t key);

	// Deprecated 1.x spelling of exportObfuscatedXOR. It never encrypted
	// anything; prefer the honest name.
	void exportEncrypted(const float* data, size_t len, uint8_t key);

}

#endif
