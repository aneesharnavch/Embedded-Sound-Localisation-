#include "dspRealTimeStats.h"
#include "../dspCompat.h"
#include <math.h>
#include <new>

namespace dspRealTime {

static const float MAD_SCALE = 0.6745f;
static const float MEAN_AD_SCALE = 0.7979f;

RealTimeStats::RealTimeStats(size_t windowSize_)
    : buffer(0), scratch(0), windowSize(windowSize_), head(0), filled(0),
      cachedMean(0.0f), cachedVariance(0.0f), statsDirty(true) {
    if (windowSize == 0) return;            // stays in the ok() == false state
    buffer = new (std::nothrow) float[windowSize];
    if (!buffer) windowSize = 0;
}

RealTimeStats::~RealTimeStats() {
    release();
}

void RealTimeStats::release() {
    delete[] buffer;
    delete[] scratch;
    buffer = 0;
    scratch = 0;
}

// Deep copy. These objects hold raw buffers, and MicroDSP's factory methods
// return them by value, so without correct copy semantics a copy would share
// and then double-free the buffer.
void RealTimeStats::copyFrom(const RealTimeStats& other) {
    windowSize = other.windowSize;
    head = other.head;
    filled = other.filled;
    cachedMean = other.cachedMean;
    cachedVariance = other.cachedVariance;
    statsDirty = other.statsDirty;
    buffer = 0;
    scratch = 0;

    if (windowSize == 0) return;
    buffer = new (std::nothrow) float[windowSize];
    if (!buffer) { windowSize = 0; filled = 0; head = 0; return; }
    dspCompat::copyFloat(other.buffer, buffer, windowSize);
    // `scratch` is a cache; the copy re-allocates it on demand.
}

RealTimeStats::RealTimeStats(const RealTimeStats& other) {
    copyFrom(other);
}

RealTimeStats& RealTimeStats::operator=(const RealTimeStats& other) {
    if (this == &other) return *this;
    release();
    copyFrom(other);
    return *this;
}

void RealTimeStats::reset() {
    head = 0;
    filled = 0;
    statsDirty = true;
}

bool RealTimeStats::update(float value) {
    if (!ok()) return false;

    buffer[head] = value;
    head = (head + 1) % windowSize;
    if (filled < windowSize) ++filled;
    statsDirty = true;
    return true;
}

float RealTimeStats::latest() const {
    if (!ok() || filled == 0) return 0.0f;
    // head has already advanced past the newest sample.
    return buffer[(head + windowSize - 1) % windowSize];
}

// The ring is only ever read in full for statistics, so iterating raw slot
// order is equivalent and cheaper than mapping chronological positions.
void RealTimeStats::recomputeStats() {
    if (!statsDirty) return;
    statsDirty = false;

    if (!ok() || filled == 0) {
        cachedMean = 0.0f;
        cachedVariance = 0.0f;
        return;
    }

    float sum = 0.0f;
    for (size_t i = 0; i < filled; ++i) sum += buffer[i];
    cachedMean = sum / (float)filled;

    // Second pass over the deviations: stable regardless of magnitude.
    float sumSq = 0.0f;
    for (size_t i = 0; i < filled; ++i) {
        float diff = buffer[i] - cachedMean;
        sumSq += diff * diff;
    }
    cachedVariance = sumSq / (float)filled;
}

float RealTimeStats::getMean() {
    recomputeStats();
    return cachedMean;
}

float RealTimeStats::getVariance() {
    recomputeStats();
    return cachedVariance;
}

float RealTimeStats::getStdDev() {
    recomputeStats();
    return sqrtf(cachedVariance);
}

float RealTimeStats::getMin() {
    if (!ok() || filled == 0) return 0.0f;
    float m = buffer[0];
    for (size_t i = 1; i < filled; ++i) if (buffer[i] < m) m = buffer[i];
    return m;
}

float RealTimeStats::getMax() {
    if (!ok() || filled == 0) return 0.0f;
    float m = buffer[0];
    for (size_t i = 1; i < filled; ++i) if (buffer[i] > m) m = buffer[i];
    return m;
}

float RealTimeStats::getRMS() {
    if (!ok() || filled == 0) return 0.0f;
    float sum = 0.0f;
    for (size_t i = 0; i < filled; ++i) sum += buffer[i] * buffer[i];
    return sqrtf(sum / (float)filled);
}

bool RealTimeStats::ensureScratch() {
    if (!ok()) return false;
    if (scratch) return true;
    scratch = new (std::nothrow) float[windowSize];
    return scratch != 0;
}

float* RealTimeStats::sortedWindow() {
    if (!ensureScratch() || filled == 0) return 0;
    dspCompat::copyFloat(buffer, scratch, filled);
    dspCompat::sortFloat(scratch, filled);
    return scratch;
}

float RealTimeStats::getMedian() {
    float* sorted = sortedWindow();
    if (!sorted) return 0.0f;
    return dspCompat::medianSorted(sorted, filled);
}

bool RealTimeStats::isZScoreOutlier(float threshold) {
    if (!ok() || filled < 2) return false;
    float sd = getStdDev();
    if (sd <= 0.0f) return false;              // constant window: z undefined
    return fabsf((latest() - getMean()) / sd) > threshold;
}

// See the note in dspStats.cpp: MAD collapses to zero when a majority of the
// window shares one value, which masks the very outlier we are looking for, so
// we fall back to the mean absolute deviation before giving up.
bool RealTimeStats::madTest(float threshold, float madScale, float meanAdScale) {
    if (!ok() || filled < 2) return false;

    float* sorted = sortedWindow();
    if (!sorted) return false;
    float median = dspCompat::medianSorted(sorted, filled);

    // Reuse the same scratch: overwrite the sorted values with their absolute
    // deviations and re-sort, avoiding a second buffer.
    float deviationSum = 0.0f;
    for (size_t i = 0; i < filled; ++i) {
        sorted[i] = fabsf(sorted[i] - median);
        deviationSum += sorted[i];
    }
    dspCompat::sortFloat(sorted, filled);
    float mad = dspCompat::medianSorted(sorted, filled);

    float value = latest();
    if (mad > 0.0f) {
        return fabsf(madScale * (value - median) / mad) > threshold;
    }

    float meanAd = deviationSum / (float)filled;
    if (meanAd > 0.0f) {
        return fabsf(meanAdScale * (value - median) / meanAd) > threshold;
    }
    return false;                              // constant window
}

bool RealTimeStats::isModifiedZScoreOutlier(float threshold) {
    return madTest(threshold, MAD_SCALE, MEAN_AD_SCALE);
}

bool RealTimeStats::isMADOutlier(float threshold) {
    return madTest(threshold, 1.0f, 1.0f);
}

bool RealTimeStats::isIQROutlier(float multiplier) {
    if (!ok() || filled < 4) return false;

    float* sorted = sortedWindow();
    if (!sorted) return false;

    float q1 = dspCompat::percentileSorted(sorted, filled, 0.25f);
    float q3 = dspCompat::percentileSorted(sorted, filled, 0.75f);
    float iqr = q3 - q1;

    // Judges latest(), not the tail of the backing array.
    float value = latest();
    return value < (q1 - multiplier * iqr) || value > (q3 + multiplier * iqr);
}

}
