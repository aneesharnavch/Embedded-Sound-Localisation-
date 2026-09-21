#ifndef DSPEXPORT_H
#define DSPEXPORT_H

#include <Arduino.h>

namespace dspExport {

    // String-building helper, for callers that need the text in RAM rather
    // than streamed out (to put it in an MQTT payload, say).
    //
    // The buffer is reserved once up front from an estimate of the final
    // length. 1.x appended to an empty String in a loop, which reallocates on
    // nearly every sample and fragments the heap badly on small parts.
    //
    // Returns an empty String if the reservation fails. If you are only sending
    // the data to a port, prefer dspDataIO::exportCSVRow, which builds no
    // String at all.
    String floatArrayToCompactString(const float* data, size_t len,
                                     const char* label = nullptr,
                                     uint8_t decimals = 4);

    // Streams the same text straight to the port with no String involved.
    void sendExportStringToSerial(const float* data, size_t len,
                                  const char* label = nullptr,
                                  uint8_t decimals = 4);

}

#endif
