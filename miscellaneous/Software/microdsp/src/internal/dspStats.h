#ifndef DSP_STATS_H
#define DSP_STATS_H

#include <stddef.h>

namespace dspStats {

    // All functions below tolerate len == 0 and null pointers; degenerate
    // input yields 0.0f (or false for the predicates) rather than NaN.

    float mean(const float* data, size_t len);

    // Population variance / standard deviation (divisor n), matching the
    // definition in Documentation.md. Computed with a two-pass algorithm, so
    // it stays accurate for large-magnitude, small-spread data.
    float variance(const float* data, size_t len);
    float stdDev(const float* data, size_t len);

    // Sample variance / standard deviation (divisor n-1), for when the data
    // is a sample drawn from a larger population.
    float sampleVariance(const float* data, size_t len);
    float sampleStdDev(const float* data, size_t len);

    float minimum(const float* data, size_t len);
    float maximum(const float* data, size_t len);
    float rms(const float* data, size_t len);

    // Median and linear-interpolated percentile/quartile.
    // These need a scratch buffer of `len` floats; they allocate it
    // internally and return 0.0f if that allocation fails.
    float median(const float* data, size_t len);
    float percentile(const float* data, size_t len, float p);

    // Median absolute deviation. Robust scale estimate; 0 for constant data.
    float medianAbsoluteDeviation(const float* data, size_t len);

    // ==== Outlier detection ====
    //
    // Each test needs a non-zero measure of spread. When the data is constant
    // (sd or MAD == 0) the test statistic is undefined, so these return false
    // rather than dividing by zero.

    // Argument order matches the original 1.x API: (val, data, len, ...).

    // z = |val - mean| / sd
    bool isZScoreOutlier(float val, const float* data, size_t len, float threshold = 3.0f);

    // Iglewicz-Hoaglin modified z-score: 0.6745 * (val - median) / MAD.
    bool isModifiedZScoreOutlier(float val, const float* data, size_t len, float threshold = 3.5f);

    // Unscaled MAD test: |val - median| / MAD. Distinct from the modified
    // z-score above, which folds in the 0.6745 normal-consistency constant,
    // so for the same threshold this test is slightly more permissive.
    bool isMADOutlier(float val, const float* data, size_t len, float threshold = 3.5f);

    // Tukey's fences: val < Q1 - m*IQR or val > Q3 + m*IQR, with quartiles
    // taken by linear interpolation. Needs len >= 2.
    bool isIQROutlier(float val, const float* data, size_t len, float multiplier = 1.5f);

}

#endif
