#ifndef DSP_REALTIME_STATS_H
#define DSP_REALTIME_STATS_H

#include <stddef.h>

namespace dspRealTime {

// Sliding-window statistics over a stream of samples.
//
// Backed by a fixed ring buffer allocated once in the constructor, so update()
// is O(1) and performs no allocation. Construct it globally or in setup(), then
// call update() from loop().
//
// windowSize must be >= 1. A zero window leaves the object in a failed state
// (ok() == false) where update() returns false and the accessors return 0
// rather than dividing by zero or indexing an empty buffer, which is what 1.x
// did.
class RealTimeStats {
public:
    explicit RealTimeStats(size_t windowSize);
    ~RealTimeStats();
    RealTimeStats(const RealTimeStats& other);
    RealTimeStats& operator=(const RealTimeStats& other);

    // False if windowSize was 0 or the buffer could not be allocated.
    // Worth checking once after construction on a small board.
    bool ok() const { return buffer != 0; }

    // Discards all samples; keeps the allocation.
    void reset();

    // Adds a sample, evicting the oldest once the window is full.
    bool update(float value);

    size_t count() const { return filled; }
    size_t capacity() const { return windowSize; }
    bool full() const { return windowSize != 0 && filled == windowSize; }

    // Most recently added sample, 0 if none. All the outlier tests below judge
    // this value. 1.x used buffer.back() in isIQROutlier, which is a stale
    // sample once the ring has wrapped.
    float latest() const;

    // Population mean / variance / standard deviation over the window.
    //
    // Computed by a two-pass algorithm over the ring and cached until the next
    // update(). 1.x kept running sum and sum-of-squares and evaluated
    // sqrt(sumSq/n - mean^2), which cancels catastrophically: for large values
    // with a small spread it returned wildly wrong numbers or NaN.
    float getMean();
    float getVariance();
    float getStdDev();

    float getMin();
    float getMax();
    float getRMS();

    // Median of the window. Needs a scratch buffer of windowSize floats,
    // allocated on first use; returns 0 if that allocation fails.
    float getMedian();

    // ==== Outlier tests on the newest sample ====
    //
    // Each returns false when the window holds too few samples, or when the
    // relevant measure of spread is zero (the statistic is undefined there
    // rather than infinite).
    bool isZScoreOutlier(float threshold = 3.0f);
    bool isModifiedZScoreOutlier(float threshold = 3.5f);
    bool isMADOutlier(float threshold = 3.5f);
    bool isIQROutlier(float multiplier = 1.5f);

private:
    float* buffer;
    float* scratch;          // lazily allocated, for order statistics
    size_t windowSize;
    size_t head;             // index the next sample will occupy
    size_t filled;
    float cachedMean;
    float cachedVariance;
    bool statsDirty;

    void recomputeStats();
    bool ensureScratch();
    // Returns the window sorted ascending into `scratch`, or null on failure.
    float* sortedWindow();
    bool madTest(float threshold, float madScale, float meanAdScale);

    void copyFrom(const RealTimeStats& other);
    void release();
};

}

#endif
