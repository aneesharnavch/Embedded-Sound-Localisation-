#ifndef DSP_CALCULUS_H
#define DSP_CALCULUS_H

#include <stddef.h>

namespace dspCalculus {

    // ==== Derivatives ====

    // Forward-difference nth derivative. Each order shortens the result by one
    // sample, so outLen = len - order.
    //
    // OWNERSHIP: returns a buffer allocated with new[]. The caller must
    // release it with freeBuffer() (or delete[]). Returns nullptr and sets
    // outLen = 0 on invalid arguments, dt == 0, or allocation failure.
    //
    // Prefer derivativeInto() on memory-constrained boards: it writes into a
    // buffer you already own and allocates nothing.
    float* nthDerivative(const float* data, size_t len, float dt, int order,
                         size_t& outLen);

    // Releases a buffer returned by nthDerivative(). Safe to call with null.
    void freeBuffer(float* buffer);

    // Allocation-free nth derivative. `out` must have room for len - order
    // floats; it doubles as the working buffer, so it must not alias `data`.
    // Returns the number of samples written, or 0 on invalid arguments.
    size_t derivativeInto(const float* data, size_t len, float dt, int order,
                          float* out);

    // ==== Integrals ====

    // Rectangle (left Riemann) rule: dx * sum(f). Kept for compatibility with
    // 1.x results.
    float definiteIntegral(const float* data, size_t len, float dx);

    // Trapezoidal rule: dx * (f0/2 + f1 + ... + f(n-1)/2). Second-order
    // accurate, so it is a strictly better estimate than the rectangle rule
    // for the same samples - prefer it unless you need 1.x's exact numbers.
    float integralTrapezoid(const float* data, size_t len, float dx);

    // Running (cumulative) integral, out[i] = integral of data[0..i], by the
    // trapezoidal rule. This is what you want for position-from-velocity type
    // problems. `out` needs len entries and may alias `data`.
    bool cumulativeIntegral(const float* data, size_t len, float dx, float* out);

    // Volume integral over a 3-D sample grid stored as a flat, contiguous
    // array in x-major order: element (i,j,k) lives at
    // ((i * yLen) + j) * zLen + k.
    //
    // 1.x took a float*** here, which is not a shape any embedded caller can
    // realistically build (it needs xLen + xLen*yLen separate allocations).
    float tripleIntegral(const float* data, size_t xLen, size_t yLen, size_t zLen,
                         float dx, float dy, float dz);

}

#endif
