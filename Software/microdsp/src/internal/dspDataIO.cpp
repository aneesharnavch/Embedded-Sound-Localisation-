#include "dspDataIO.h"

namespace dspDataIO {

	void exportCSV(Stream& stream, const float* data, size_t len,
	               const char* label) {
		if (!data) return;
		if (label) stream.println(label);
		for (size_t i = 0; i < len; ++i) stream.println(data[i], 6);
	}

	void exportCSV(const float* data, size_t len, const char* label) {
		exportCSV(Serial, data, len, label);
	}

	void exportCSVRow(Stream& stream, const float* data, size_t len,
	                  const char* label, uint8_t decimals) {
		if (!data) return;
		if (label) {
			stream.print('[');
			stream.print(label);
			stream.print(F("] "));
		}
		for (size_t i = 0; i < len; ++i) {
			if (i) stream.print(',');
			stream.print(data[i], decimals);
		}
		stream.println();
	}

	void exportCSVRow(const float* data, size_t len, const char* label,
	                  uint8_t decimals) {
		exportCSVRow(Serial, data, len, label, decimals);
	}

	void exportJSON(Stream& stream, const float* data, size_t len,
	                const char* label, uint8_t decimals) {
		if (!data) return;
		stream.print(F("{\"type\":\"microdsp\",\"label\":\""));
		if (label) stream.print(label);
		stream.print(F("\",\"data\":["));
		for (size_t i = 0; i < len; ++i) {
			if (i) stream.print(',');
			stream.print(data[i], decimals);
		}
		stream.println(F("]}"));
	}

	void exportJSON(const float* data, size_t len, const char* label,
	                uint8_t decimals) {
		exportJSON(Serial, data, len, label, decimals);
	}

	void annotateAndExport(const float* data, size_t len, const char* description) {
		Serial.println(F("ANNOTATION:"));
		if (description) Serial.println(description);
		exportCSV(data, len);
	}

	void exportObfuscatedXOR(Stream& stream, const float* data, size_t len,
	                         uint8_t key) {
		if (!data) return;
		for (size_t i = 0; i < len; ++i) {
			const uint8_t* bytePtr = (const uint8_t*)&data[i];
			for (size_t j = 0; j < sizeof(float); ++j) {
				uint8_t b = (uint8_t)(bytePtr[j] ^ key);
				// Zero-pad to two digits. print(b, HEX) emits a single digit
				// for values below 0x10, so 1.x's output could not be parsed
				// back into bytes unambiguously.
				if (b < 0x10) stream.print('0');
				stream.print(b, HEX);
				if (j + 1 < sizeof(float)) stream.print(' ');
			}
			stream.println();
		}
	}

	void exportObfuscatedXOR(const float* data, size_t len, uint8_t key) {
		exportObfuscatedXOR(Serial, data, len, key);
	}

	void exportEncrypted(const float* data, size_t len, uint8_t key) {
		exportObfuscatedXOR(Serial, data, len, key);
	}

}
