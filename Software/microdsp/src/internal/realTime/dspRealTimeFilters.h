#ifndef DSP_REALTIME_FILTERS_H
#define DSP_REALTIME_FILTERS_H

#include <stddef.h>

namespace dspRealTime {

// Streaming filters over a sliding window.
//
// All three own a fixed ring buffer allocated in the constructor. 1.x used
// std::vector plus erase(begin()), which memmoved the whole window on every
// sample and made these unusable on AVR (no <vector> in avr-gcc).
//
// windowSize must be >= 1; zero leaves the object in a failed state
// (ok() == false) whose update() returns the input unchanged instead of
// indexing an empty buffer and dividing by zero.

class RealTimeMovingAverage {
public:
    explicit RealTimeMovingAverage(size_t windowSize);
    ~RealTimeMovingAverage();
    RealTimeMovingAverage(const RealTimeMovingAverage& other);
    RealTimeMovingAverage& operator=(const RealTimeMovingAverage& other);

    bool ok() const { return buffer != 0; }
    void reset();

    // Returns the mean of the window including `value`. During warm-up this is
    // the mean of the samples seen so far.
    float update(float value);

    size_t count() const { return filled; }
    bool full() const { return windowSize != 0 && filled == windowSize; }

private:
    float* buffer;
    size_t windowSize;
    size_t head;
    size_t filled;

    void copyFrom(const RealTimeMovingAverage& other);
};

class RealTimeMedianFilter {
public:
    explicit RealTimeMedianFilter(size_t windowSize);
    ~RealTimeMedianFilter();
    RealTimeMedianFilter(const RealTimeMedianFilter& other);
    RealTimeMedianFilter& operator=(const RealTimeMedianFilter& other);

    bool ok() const { return buffer != 0; }
    void reset();

    // Returns the median of the window including `value`.
    float update(float value);

    size_t count() const { return filled; }
    bool full() const { return windowSize != 0 && filled == windowSize; }

private:
    float* buffer;
    float* scratch;
    size_t windowSize;
    size_t head;
    size_t filled;

    void copyFrom(const RealTimeMedianFilter& other);
    void release();
};

class RealTimeGaussianFilter {
public:
    // sigma must be > 0. The kernel holds exactly windowSize taps centred on
    // the window: 1.x derived a radius of windowSize/2 and then wrote
    // 2*radius+1 taps into a windowSize-long vector, overrunning the buffer by
    // one float for every even windowSize.
    RealTimeGaussianFilter(size_t windowSize, float sigma);
    ~RealTimeGaussianFilter();
    RealTimeGaussianFilter(const RealTimeGaussianFilter& other);
    RealTimeGaussianFilter& operator=(const RealTimeGaussianFilter& other);

    bool ok() const { return buffer != 0 && kernel != 0; }
    void reset();

    // Returns the Gaussian-weighted average of the window. While the window is
    // still filling, the taps in use are renormalised so the gain stays at
    // unity; 1.x returned a heavily attenuated value during warm-up (a
    // constant 1.0 input read 0.05, 0.30, 0.70, ... before settling).
    float update(float value);

    size_t count() const { return filled; }
    bool full() const { return windowSize != 0 && filled == windowSize; }

private:
    float* buffer;
    float* kernel;
    size_t windowSize;
    size_t head;
    size_t filled;

    void copyFrom(const RealTimeGaussianFilter& other);
    void release();
};

}

#endif
