#include "dspExport.h"
#include "dspDataIO.h"
#include "dspCompat.h"
#include <string.h>

namespace dspExport {

    String floatArrayToCompactString(const float* data, size_t len,
                                     const char* label, uint8_t decimals) {
        String result;
        if (!data || len == 0) return result;

        // Worst case per sample: sign, a few integer digits, the decimal point,
        // `decimals` fraction digits and the separator. Reserving once turns
        // O(len) reallocations into one.
        size_t perSample = (size_t)decimals + 8;
        size_t estimate = len * perSample + 4;
        if (label) estimate += strlen(label) + 4;

        if (!result.reserve(estimate)) return String();

        if (label) {
            result += '[';
            result += label;
            result += "] ";
        }
        char text[32];
        for (size_t i = 0; i < len; ++i) {
            if (i) result += ',';
            // String(float, uint8_t) is ambiguous on the ESP32 core, so the
            // number is formatted through dspCompat instead.
            if (dspCompat::formatFloat(data[i], decimals, text, sizeof(text))) {
                result += text;
            }
        }
        return result;
    }

    void sendExportStringToSerial(const float* data, size_t len,
                                  const char* label, uint8_t decimals) {
        // Streamed directly: no intermediate String, so this costs no heap.
        dspDataIO::exportCSVRow(Serial, data, len, label, decimals);
    }

}
