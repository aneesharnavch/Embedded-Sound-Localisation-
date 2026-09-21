#ifndef DSP_TRANSFORMS_H
#define DSP_TRANSFORMS_H

#include <stddef.h>

namespace dspTransforms {

    // In-place radix-2 FFT. `len` MUST be a power of two; the transform
    // returns false and leaves the arrays untouched otherwise. (1.x silently
    // produced garbage for other lengths.)
    //
    // Iterative and allocation-free: it uses only the caller's two arrays and
    // a handful of locals. 1.x was recursive and heap-allocated four arrays at
    // every level of recursion, which fragments a small heap badly.
    bool fft(float* real, float* imag, size_t len);

    // In-place inverse FFT, scaled by 1/len. Same power-of-two requirement.
    bool ifft(float* real, float* imag, size_t len);

    // Per-bin magnitude sqrt(re^2 + im^2) into `magnitude` (len entries).
    // May alias `real`.
    bool fftMagnitude(const float* real, const float* imag, float* magnitude,
                      size_t len);

    // Index of the largest magnitude bin in the first half of the spectrum
    // (the unique part for real input), ignoring DC. Returns 0 if there is no
    // usable spectrum.
    size_t dominantBin(const float* real, const float* imag, size_t len);

    // Frequency in Hz of the dominant bin, using parabolic interpolation
    // across its neighbours for sub-bin resolution.
    float dominantFrequency(const float* real, const float* imag, size_t len,
                            float sampleRate);

    // ==== Window functions ====
    //
    // Applying a window before an FFT suppresses the spectral leakage caused
    // by the transform assuming the buffer repeats exactly. Each fills `len`
    // coefficients in 0..1; multiply them into the signal (or use applyWindow).
    bool hannWindow(float* window, size_t len);
    bool hammingWindow(float* window, size_t len);
    bool blackmanWindow(float* window, size_t len);
    bool applyWindow(float* data, const float* window, size_t len);

    // ==== Laplace transform ====

    // Numerically evaluates F(s) = integral f(t) e^(-st) dt at the single
    // complex point s = sReal + j*sImag, by the rectangle rule over `len`
    // samples spaced dt apart. The result is one complex number.
    //
    // 1.x wrote the un-summed integrand to an array and ignored dt, so it did
    // not compute a transform at all. Use laplaceIntegrand for that behaviour.
    bool laplaceTransform(const float* input, size_t len, float dt,
                          float sReal, float sImag,
                          float& outReal, float& outImag);

    // Per-sample integrand f(t) e^(-st) without summation, for callers that
    // want to inspect or accumulate it themselves.
    bool laplaceIntegrand(const float* input, float* outputReal,
                          float* outputImag, size_t len, float dt,
                          float sReal, float sImag);

}

#endif
