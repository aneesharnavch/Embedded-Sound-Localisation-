#include "dspResources.h"
#include <Arduino.h>
#include <stdlib.h>

#if defined(ARDUINO_ARCH_AVR)
extern "C" char* __brkval;
extern "C" char __heap_start;
#endif

namespace dspResources {

    size_t FREE_MEMORY_BYTES = 2048;

    static size_t freeMemoryThreshold = 256;
    static uint8_t computeLimitPercent = 100;

    static uint32_t loadWindowMicros = 1000000UL;   // 1 second
    static uint32_t windowStartMicros = 0;
    static uint32_t busyMicros = 0;
    static uint32_t workBeganMicros = 0;
    static bool workInProgress = false;

    // ---- memory -------------------------------------------------------------

    void setAvailableMemory(size_t bytes) {
        FREE_MEMORY_BYTES = bytes;
    }

    void setFreeMemoryThreshold(size_t bytes) {
        freeMemoryThreshold = bytes;
    }

    size_t getFreeMemoryThreshold() {
        return freeMemoryThreshold;
    }

#if !defined(ARDUINO_ARCH_AVR) && !defined(ESP8266) && !defined(ESP32)
    // Portable fallback: binary-search the largest block malloc will hand
    // back. This measures the largest *contiguous* free block, which is the
    // number that actually matters when allocating a DSP buffer.
    static size_t largestAllocatableBlock() {
        const size_t upperLimit = 512UL * 1024UL;
        size_t lo = 0, hi = upperLimit;

        // Establish an upper bound first so we never probe absurd sizes.
        size_t probe = 64;
        while (probe < upperLimit) {
            void* p = malloc(probe);
            if (!p) break;
            free(p);
            lo = probe;
            probe <<= 1;
        }
        hi = (probe < upperLimit) ? probe : upperLimit;

        // Narrow to within 32 bytes; bounded iteration count.
        while (hi - lo > 32) {
            size_t mid = lo + (hi - lo) / 2;
            void* p = malloc(mid);
            if (p) { free(p); lo = mid; } else { hi = mid; }
        }
        return lo;
    }
#endif

    size_t freeMemory() {
#if defined(ARDUINO_ARCH_AVR)
        // On AVR the heap grows up from __heap_start and the stack grows down
        // from RAMEND; the gap between them is what is left.
        char top;
        if (__brkval == 0) return (size_t)(&top - &__heap_start);
        return (size_t)(&top - __brkval);
#elif defined(ESP8266) || defined(ESP32)
        return (size_t)ESP.getFreeHeap();
#else
        size_t measured = largestAllocatableBlock();
        return measured > 0 ? measured : FREE_MEMORY_BYTES;
#endif
    }

    size_t getAvailableMemory() {
        return freeMemory();
    }

    bool hasSufficientMemory(size_t requiredBytes) {
        size_t available = freeMemory();
        // Guard against the reserve margin exceeding what is free, which would
        // wrap around if subtracted directly.
        if (available <= freeMemoryThreshold) return false;
        return requiredBytes <= (available - freeMemoryThreshold);
    }

    bool canProcess(size_t requiredBytes) {
        return hasSufficientMemory(requiredBytes);
    }

    // ---- CPU load -----------------------------------------------------------

    void init() {
        windowStartMicros = micros();
        busyMicros = 0;
        workInProgress = false;
    }

    void setComputeLimit(uint8_t percent) {
        if (percent > 100) percent = 100;
        computeLimitPercent = percent;
    }

    uint8_t getComputeLimit() {
        return computeLimitPercent;
    }

    void setLoadWindow(uint32_t microseconds) {
        if (microseconds == 0) return;
        loadWindowMicros = microseconds;
    }

    // Unsigned subtraction wraps correctly, so this stays valid across the
    // ~71 minute micros() rollover.
    static void rollWindow() {
        uint32_t now = micros();
        if ((uint32_t)(now - windowStartMicros) >= loadWindowMicros) {
            windowStartMicros = now;
            busyMicros = 0;
        }
    }

    void beginWork() {
        rollWindow();
        workBeganMicros = micros();
        workInProgress = true;
    }

    void endWork() {
        if (!workInProgress) return;
        busyMicros += (uint32_t)(micros() - workBeganMicros);
        workInProgress = false;
    }

    float getLoadPercent() {
        rollWindow();
        uint32_t elapsed = (uint32_t)(micros() - windowStartMicros);
        if (elapsed == 0) return 0.0f;
        float load = 100.0f * (float)busyMicros / (float)elapsed;
        return (load > 100.0f) ? 100.0f : load;
    }

    bool shouldProcess() {
        if (computeLimitPercent >= 100) return true;
        return getLoadPercent() < (float)computeLimitPercent;
    }

    bool checkLoad(float fraction) {
        if (fraction <= 0.0f) return false;
        if (fraction > 1.0f) fraction = 1.0f;
        return getLoadPercent() < fraction * (float)computeLimitPercent;
    }

}
