#ifndef DSP_FILTERS_H
#define DSP_FILTERS_H

#include <stddef.h>

namespace dspFilters {

    // Every function returns false and leaves `data` untouched on invalid
    // arguments (null pointer, zero length, zero window) or if a required
    // scratch allocation fails, so a low-memory board degrades predictably
    // instead of writing NaNs over the caller's array.

    // Trailing (causal) mean of the last `windowSize` samples. Introduces a
    // group delay of (windowSize-1)/2 samples: the output lags the input.
    // Use movingAverageCentered when the output must stay time-aligned with
    // the input, e.g. when comparing against another filter's output.
    // Needs windowSize floats of scratch.
    bool movingAverage(float* data, size_t len, size_t windowSize);

    // Zero-phase (centred) mean. Time-aligned with the input; the window is
    // truncated and renormalised at both array edges.
    bool movingAverageCentered(float* data, size_t len, size_t windowSize);

    // Centred median. Removes impulsive noise without the edge smearing of a
    // mean filter. Needs 2*windowSize floats of scratch.
    bool medianFilter(float* data, size_t len, size_t windowSize);

    // Centred Gaussian smoothing, kernel radius 3*sigma. The kernel is
    // renormalised over the in-bounds taps at each position, so the array
    // edges are not attenuated towards zero. sigma must be > 0.
    bool gaussianFilter(float* data, size_t len, float sigma);

    // Direct-form FIR: y[i] = sum_j coeffs[j] * data[i-j], with zeros assumed
    // before the start of the array. Runs in place with no scratch memory.
    bool applyFIR(float* data, size_t len, const float* coeffs, size_t coeffLen);

    // ==== Filter design ====

    // Kaiser window of `numTaps` points (values in 0..1). This is a window,
    // not a filter: multiply it by an ideal impulse response, or use
    // designKaiserFIR below.
    bool kaiserWindow(float* window, size_t numTaps, float beta);

    // Windowed-sinc lowpass FIR: ideal sinc at `cutoffNorm` multiplied by a
    // Kaiser window, then normalised to unity DC gain.
    //
    // cutoffNorm is the cutoff as a fraction of the sample rate, in (0, 0.5)
    // - so 0.25 means fs/4. Larger `beta` trades a wider transition band for
    // deeper stopband attenuation (beta ~ 5 is a reasonable default).
    //
    // 1.x wrote only the window here and left the sinc term as a TODO, so the
    // result was an all-positive kernel that acted as a gain rather than a
    // lowpass.
    bool designKaiserFIR(float* coeffs, size_t numTaps, float beta,
                         float cutoffNorm = 0.25f);

    // Frequency-sampling design. desiredResponse holds the desired magnitude
    // at bins k = 0 .. numTaps/2 (that is, numTaps/2 + 1 entries), where bin k
    // corresponds to k*fs/numTaps. Produces a linear-phase type-I/II impulse
    // response centred in the coefficient array, which is what applyFIR
    // expects; the 1.x version produced a response centred at n=0 and so was
    // applied with the wrong phase.
    bool frequencySamplingFIR(float* coeffs, size_t numTaps,
                              const float* desiredResponse);

    // ==== Adaptive / statistical ====

    // Single-tap LMS adaptive noise canceller. `reference` carries a signal
    // correlated with the noise in `data`; on return `data` holds the error
    // signal, i.e. the input with the correlated component removed.
    //
    // 1.x wrote the filter output y (the noise estimate) back into data,
    // which is the opposite of what a canceller should return.
    bool adaptiveFilter(float* data, const float* reference, size_t len, float mu);

    // Multi-tap NLMS adaptive filter. Removes noise correlated with
    // `reference` over `numTaps` lags, so it can cancel filtered or delayed
    // interference that the single-tap version cannot. `weights` holds
    // numTaps coefficients; it is updated in place and may be reused across
    // calls to continue adapting across buffers. Pass zeroed weights to start.
    // Step size mu is normalised by reference power, so 0 < mu < 2 is stable
    // regardless of input scale.
    bool adaptiveFilterFIR(float* data, const float* reference, size_t len,
                           float mu, float* weights, size_t numTaps);

    // Scalar Wiener gain: data *= signalVar / (signalVar + noiseVar).
    bool wienerFilter(float* data, size_t len, float signalVar, float noiseVar);

}

#endif
