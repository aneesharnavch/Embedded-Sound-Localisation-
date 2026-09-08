#ifndef DSP_COMPAT_H
#define DSP_COMPAT_H

#include <stddef.h>

// Portability layer.
//
// microdsp targets 8-bit AVR as well as 32-bit MCUs. avr-gcc ships no
// <vector>, <algorithm> or <numeric>, so nothing in this library may include
// them. Everything the library needs from the standard library lives here,
// implemented against plain arrays.
//
// M_PI is a POSIX extension, not standard C or C++: it is absent under
// -std=c++NN (strict ANSI). Use DSP_PI instead of M_PI everywhere.
#define DSP_PI 3.14159265358979323846f
#define DSP_TWO_PI 6.28318530717958647692f

namespace dspCompat {

    // Ascending in-place sort. Insertion sort for short runs (typical filter
    // windows), heapsort above that: O(n log n) worst case, no recursion and
    // no scratch memory, so it is safe on a 2 KB stack.
    void sortFloat(float* a, size_t n);

    // Linear-interpolated percentile of an already-sorted array, p in [0,1].
    // Matches the conventional (numpy-default) definition, so percentile(0.5)
    // is the true median including the mean-of-middle-two case for even n.
    float percentileSorted(const float* sorted, size_t n, float p);

    // Median of an already-sorted array.
    float medianSorted(const float* sorted, size_t n);

    inline void swapFloat(float& a, float& b) { float t = a; a = b; b = t; }

    inline void copyFloat(const float* src, float* dst, size_t n) {
        for (size_t i = 0; i < n; ++i) dst[i] = src[i];
    }

    inline size_t minSize(size_t a, size_t b) { return a < b ? a : b; }
    inline size_t maxSize(size_t a, size_t b) { return a > b ? a : b; }

    // True for 1, 2, 4, 8, ... Zero is not a power of two.
    inline bool isPowerOfTwo(size_t n) { return n != 0 && (n & (n - 1)) == 0; }

    // Zeroth-order modified Bessel function of the first kind, used by the
    // Kaiser window. Abramowitz & Stegun polynomial approximation.
    float bessi0(float x);

    // Formats `value` into `buf` as fixed-point text with `decimals` places,
    // NUL-terminated, returning the number of characters written (0 if the
    // buffer is too small). Needs decimals + 16 bytes to be safe.
    //
    // Hand-rolled on purpose: avr-libc's printf omits float support unless the
    // sketch links extra flags, and String(float, uint8_t) is ambiguous on the
    // ESP32 core, so neither is portable across the boards this library claims.
    size_t formatFloat(float value, unsigned char decimals, char* buf, size_t bufLen);

}

#endif
