#ifndef DSPDATAMANAGER_H
#define DSPDATAMANAGER_H

#include <stddef.h>

namespace dspDataManager {

    // Guarded buffer allocation: checks the real free-RAM figure from
    // dspResources before allocating, so a request that would leave the stack
    // no headroom fails cleanly instead of returning a pointer that works right
    // up until the stack collides with the heap.
    //
    // Returns null on failure. Release with releaseBuffer().
    //
    // This module existed in 1.x but was not reachable - microdsp.h never
    // included it and nothing called it.
    float* allocateBuffer(size_t len);

    // Zero-initialised variant.
    float* allocateZeroedBuffer(size_t len);

    // Frees a buffer from allocateBuffer()/allocateZeroedBuffer(). Null-safe.
    void releaseBuffer(float* buffer);

    void clearBuffer(float* buffer, size_t len);
    void fillBufferWithValue(float* buffer, size_t len, float value);
    void copyBuffer(const float* src, float* dst, size_t len);

    // True if `len` floats could be allocated right now.
    bool canAllocate(size_t len);

    // True if `bytes` could be allocated right now.
    bool isSafeToAllocate(size_t bytes);

}

#endif
