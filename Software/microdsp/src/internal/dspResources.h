#ifndef DSP_RESOURCES_H
#define DSP_RESOURCES_H

#include <stddef.h>
#include <stdint.h>

namespace dspResources {

    // ==== Memory ====

    // Manual override for the amount of free RAM to assume, used only on
    // platforms where freeMemory() cannot measure it. Prefer the accessors.
    extern size_t FREE_MEMORY_BYTES;

    // Call once from setup() before using the throttling helpers. Safe to
    // call more than once; it restarts load accounting.
    void init();

    // Actual free RAM in bytes, measured per architecture: the heap/stack gap
    // on AVR, ESP.getFreeHeap() on ESP8266/ESP32, and the largest allocatable
    // block elsewhere. Returns the FREE_MEMORY_BYTES override if the platform
    // offers no way to measure.
    //
    // In 1.x this figure was whatever the user had passed to
    // setAvailableMemory(), so it never reflected reality.
    size_t freeMemory();
    size_t getAvailableMemory();          // alias for freeMemory()

    // Override the assumed free RAM (fallback platforms only).
    void setAvailableMemory(size_t bytes);

    // Bytes to keep in reserve for the stack and other allocations.
    // hasSufficientMemory() will not report success if honouring a request
    // would eat into this margin. Defaults to 256 bytes.
    void setFreeMemoryThreshold(size_t bytes);
    size_t getFreeMemoryThreshold();

    // True if `requiredBytes` can be allocated while leaving the reserve
    // margin intact.
    bool hasSufficientMemory(size_t requiredBytes);
    bool canProcess(size_t requiredBytes);   // alias for hasSufficientMemory()

    // ==== CPU load ====
    //
    // Cooperative duty-cycle throttling. Bracket expensive DSP work in
    // beginWork()/endWork() and the library tracks what fraction of wall-clock
    // time you are spending inside it; shouldProcess() then tells you whether
    // you are within the budget set by setComputeLimit().
    //
    // In 1.x the compute limit was stored and never read by anything, so it
    // had no effect at all.

    // Budget as a percentage of wall-clock time, 0..100. Values above 100 are
    // clamped. 100 (the default) never throttles.
    void setComputeLimit(uint8_t percent);
    uint8_t getComputeLimit();

    void beginWork();
    void endWork();

    // Measured busy fraction over the trailing accounting window, 0..100.
    float getLoadPercent();

    // True while the measured load is under the configured limit.
    bool shouldProcess();

    // True while the measured load is under `fraction` of the configured
    // limit, e.g. checkLoad(0.5) to stay under half the budget.
    bool checkLoad(float fraction);

    // Length of the trailing window load is averaged over. Default 1 s.
    void setLoadWindow(uint32_t microseconds);

}

#endif
