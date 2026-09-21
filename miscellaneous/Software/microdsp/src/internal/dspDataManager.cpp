#include "dspDataManager.h"
#include "dspResources.h"
#include "dspCompat.h"
#include <new>

namespace dspDataManager {

    float* allocateBuffer(size_t len) {
        if (len == 0) return nullptr;

        // Reject requests that would overflow the byte count on a 16-bit
        // size_t (AVR), where len * 4 wraps for len > 16383.
        if (len > ((size_t)-1) / sizeof(float)) return nullptr;

        size_t requiredBytes = len * sizeof(float);
        if (!dspResources::hasSufficientMemory(requiredBytes)) return nullptr;

        return new (std::nothrow) float[len];
    }

    float* allocateZeroedBuffer(size_t len) {
        float* buffer = allocateBuffer(len);
        if (buffer) clearBuffer(buffer, len);
        return buffer;
    }

    void releaseBuffer(float* buffer) {
        delete[] buffer;
    }

    void clearBuffer(float* buffer, size_t len) {
        if (!buffer) return;
        for (size_t i = 0; i < len; ++i) buffer[i] = 0.0f;
    }

    void fillBufferWithValue(float* buffer, size_t len, float value) {
        if (!buffer) return;
        for (size_t i = 0; i < len; ++i) buffer[i] = value;
    }

    void copyBuffer(const float* src, float* dst, size_t len) {
        if (!src || !dst) return;
        dspCompat::copyFloat(src, dst, len);
    }

    bool canAllocate(size_t len) {
        if (len == 0) return false;
        if (len > ((size_t)-1) / sizeof(float)) return false;
        return dspResources::hasSufficientMemory(len * sizeof(float));
    }

    bool isSafeToAllocate(size_t bytes) {
        return dspResources::hasSufficientMemory(bytes);
    }

}
