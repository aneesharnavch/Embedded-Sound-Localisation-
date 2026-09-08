#include "dspStats.h"
#include "dspCompat.h"
#include <math.h>
#include <new>

namespace dspStats {

    // 0.6745 is the ~0.75 quantile of the standard normal, which makes
    // MAD a consistent estimator of sigma for normally distributed data.
    static const float MAD_SCALE = 0.6745f;

    // sqrt(2/pi): the equivalent consistency constant for the mean absolute
    // deviation, used when MAD degenerates to zero.
    static const float MEAN_AD_SCALE = 0.7979f;

    float mean(const float* data, size_t len) {
        if (!data || len == 0) return 0.0f;
        float sum = 0.0f;
        for (size_t i = 0; i < len; ++i) sum += data[i];
        return sum / (float)len;
    }

    // Two-pass: subtract the mean before squaring. The one-pass
    // E[x^2] - E[x]^2 form loses all precision when the spread is small
    // relative to the magnitude, and can even go negative and produce NaN.
    static float sumSquaredDeviations(const float* data, size_t len) {
        float m = mean(data, len);
        float sumSq = 0.0f;
        for (size_t i = 0; i < len; ++i) {
            float diff = data[i] - m;
            sumSq += diff * diff;
        }
        return sumSq;
    }

    float variance(const float* data, size_t len) {
        if (!data || len == 0) return 0.0f;
        return sumSquaredDeviations(data, len) / (float)len;
    }

    float stdDev(const float* data, size_t len) {
        return sqrtf(variance(data, len));
    }

    float sampleVariance(const float* data, size_t len) {
        if (!data || len < 2) return 0.0f;
        return sumSquaredDeviations(data, len) / (float)(len - 1);
    }

    float sampleStdDev(const float* data, size_t len) {
        return sqrtf(sampleVariance(data, len));
    }

    float minimum(const float* data, size_t len) {
        if (!data || len == 0) return 0.0f;
        float m = data[0];
        for (size_t i = 1; i < len; ++i) if (data[i] < m) m = data[i];
        return m;
    }

    float maximum(const float* data, size_t len) {
        if (!data || len == 0) return 0.0f;
        float m = data[0];
        for (size_t i = 1; i < len; ++i) if (data[i] > m) m = data[i];
        return m;
    }

    float rms(const float* data, size_t len) {
        if (!data || len == 0) return 0.0f;
        float sum = 0.0f;
        for (size_t i = 0; i < len; ++i) sum += data[i] * data[i];
        return sqrtf(sum / (float)len);
    }

    // Sorted copy of the input. Caller owns the result and must delete[] it.
    static float* sortedCopy(const float* data, size_t len) {
        if (!data || len == 0) return nullptr;
        float* buf = new (std::nothrow) float[len];
        if (!buf) return nullptr;
        dspCompat::copyFloat(data, buf, len);
        dspCompat::sortFloat(buf, len);
        return buf;
    }

    float percentile(const float* data, size_t len, float p) {
        float* sorted = sortedCopy(data, len);
        if (!sorted) return 0.0f;
        float result = dspCompat::percentileSorted(sorted, len, p);
        delete[] sorted;
        return result;
    }

    float median(const float* data, size_t len) {
        return percentile(data, len, 0.5f);
    }

    float medianAbsoluteDeviation(const float* data, size_t len) {
        // One buffer, used twice: first for the sorted values (to get the
        // median), then overwritten with the absolute deviations. The 1.x
        // code allocated two buffers of `len` for this.
        float* buf = sortedCopy(data, len);
        if (!buf) return 0.0f;

        float med = dspCompat::medianSorted(buf, len);
        for (size_t i = 0; i < len; ++i) buf[i] = fabsf(data[i] - med);
        dspCompat::sortFloat(buf, len);
        float mad = dspCompat::medianSorted(buf, len);

        delete[] buf;
        return mad;
    }

    bool isZScoreOutlier(float val, const float* data, size_t len, float threshold) {
        if (!data || len == 0) return false;
        float sd = stdDev(data, len);
        // Constant data: z is undefined (0/0), so report "not an outlier"
        // instead of returning a NaN comparison.
        if (sd <= 0.0f) return false;
        return fabsf((val - mean(data, len)) / sd) > threshold;
    }

    // Shared core for the two median/MAD-based tests.
    //
    // MAD is zero whenever more than half the window holds the same value -
    // seven 10s and one 1000, say - which "masks" the outlier and makes the
    // statistic undefined. Iglewicz and Hoaglin's remedy is to fall back to the
    // mean absolute deviation, which is what the meanAdScale path does. Only
    // genuinely constant data (both estimates zero) reports "not an outlier".
    static bool madTest(float val, const float* data, size_t len,
                        float threshold, float madScale, float meanAdScale) {
        if (!data || len == 0) return false;

        float* buf = sortedCopy(data, len);
        if (!buf) return false;

        float med = dspCompat::medianSorted(buf, len);

        float deviationSum = 0.0f;
        for (size_t i = 0; i < len; ++i) {
            buf[i] = fabsf(data[i] - med);
            deviationSum += buf[i];
        }
        dspCompat::sortFloat(buf, len);
        float mad = dspCompat::medianSorted(buf, len);
        delete[] buf;

        if (mad > 0.0f) {
            return fabsf(madScale * (val - med) / mad) > threshold;
        }

        float meanAd = deviationSum / (float)len;
        if (meanAd > 0.0f) {
            return fabsf(meanAdScale * (val - med) / meanAd) > threshold;
        }
        return false;                    // constant data: nothing to compare to
    }

    bool isModifiedZScoreOutlier(float val, const float* data, size_t len, float threshold) {
        return madTest(val, data, len, threshold, MAD_SCALE, MEAN_AD_SCALE);
    }

    bool isMADOutlier(float val, const float* data, size_t len, float threshold) {
        return madTest(val, data, len, threshold, 1.0f, 1.0f);
    }

    bool isIQROutlier(float val, const float* data, size_t len, float multiplier) {
        if (!data || len < 2) return false;

        float* sorted = sortedCopy(data, len);
        if (!sorted) return false;

        // Linear interpolation, as documented; the 1.x code indexed
        // sorted[len/4] directly, which is badly biased for small len.
        float q1 = dspCompat::percentileSorted(sorted, len, 0.25f);
        float q3 = dspCompat::percentileSorted(sorted, len, 0.75f);
        delete[] sorted;

        float iqr = q3 - q1;
        float lower = q1 - multiplier * iqr;
        float upper = q3 + multiplier * iqr;
        return val < lower || val > upper;
    }

}
