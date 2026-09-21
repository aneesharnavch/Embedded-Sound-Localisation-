#include "dspRealTimeFilters.h"
#include "../dspCompat.h"
#include <math.h>
#include <new>

namespace dspRealTime {

// ---- RealTimeMovingAverage --------------------------------------------------

RealTimeMovingAverage::RealTimeMovingAverage(size_t windowSize_)
    : buffer(0), windowSize(windowSize_), head(0), filled(0) {
    if (windowSize == 0) return;
    buffer = new (std::nothrow) float[windowSize];
    if (!buffer) windowSize = 0;
}

RealTimeMovingAverage::~RealTimeMovingAverage() {
    delete[] buffer;
}

void RealTimeMovingAverage::copyFrom(const RealTimeMovingAverage& other) {
    windowSize = other.windowSize;
    head = other.head;
    filled = other.filled;
    buffer = 0;
    if (windowSize == 0) return;
    buffer = new (std::nothrow) float[windowSize];
    if (!buffer) { windowSize = 0; filled = 0; head = 0; return; }
    dspCompat::copyFloat(other.buffer, buffer, windowSize);
}

RealTimeMovingAverage::RealTimeMovingAverage(const RealTimeMovingAverage& other) {
    copyFrom(other);
}

RealTimeMovingAverage& RealTimeMovingAverage::operator=(const RealTimeMovingAverage& other) {
    if (this == &other) return *this;
    delete[] buffer;
    copyFrom(other);
    return *this;
}

void RealTimeMovingAverage::reset() {
    head = 0;
    filled = 0;
}

float RealTimeMovingAverage::update(float value) {
    if (!ok()) return value;

    buffer[head] = value;
    head = (head + 1) % windowSize;
    if (filled < windowSize) ++filled;

    // Summed fresh from the ring rather than carried as a running total: a
    // running sum accumulates rounding error indefinitely in a sketch that
    // runs for days, and the window is small enough that this is cheap.
    float sum = 0.0f;
    for (size_t i = 0; i < filled; ++i) sum += buffer[i];
    return sum / (float)filled;
}

// ---- RealTimeMedianFilter ---------------------------------------------------

RealTimeMedianFilter::RealTimeMedianFilter(size_t windowSize_)
    : buffer(0), scratch(0), windowSize(windowSize_), head(0), filled(0) {
    if (windowSize == 0) return;
    buffer = new (std::nothrow) float[windowSize];
    if (!buffer) { windowSize = 0; return; }
    scratch = new (std::nothrow) float[windowSize];
    if (!scratch) { delete[] buffer; buffer = 0; windowSize = 0; }
}

RealTimeMedianFilter::~RealTimeMedianFilter() {
    release();
}

void RealTimeMedianFilter::release() {
    delete[] buffer;
    delete[] scratch;
    buffer = 0;
    scratch = 0;
}

void RealTimeMedianFilter::copyFrom(const RealTimeMedianFilter& other) {
    windowSize = other.windowSize;
    head = other.head;
    filled = other.filled;
    buffer = 0;
    scratch = 0;
    if (windowSize == 0) return;

    buffer = new (std::nothrow) float[windowSize];
    scratch = new (std::nothrow) float[windowSize];
    if (!buffer || !scratch) {
        release();
        windowSize = 0;
        filled = 0;
        head = 0;
        return;
    }
    dspCompat::copyFloat(other.buffer, buffer, windowSize);
}

RealTimeMedianFilter::RealTimeMedianFilter(const RealTimeMedianFilter& other) {
    copyFrom(other);
}

RealTimeMedianFilter& RealTimeMedianFilter::operator=(const RealTimeMedianFilter& other) {
    if (this == &other) return *this;
    release();
    copyFrom(other);
    return *this;
}

void RealTimeMedianFilter::reset() {
    head = 0;
    filled = 0;
}

float RealTimeMedianFilter::update(float value) {
    if (!ok()) return value;

    buffer[head] = value;
    head = (head + 1) % windowSize;
    if (filled < windowSize) ++filled;

    dspCompat::copyFloat(buffer, scratch, filled);
    dspCompat::sortFloat(scratch, filled);
    return dspCompat::medianSorted(scratch, filled);
}

// ---- RealTimeGaussianFilter -------------------------------------------------

RealTimeGaussianFilter::RealTimeGaussianFilter(size_t windowSize_, float sigma)
    : buffer(0), kernel(0), windowSize(windowSize_), head(0), filled(0) {
    if (windowSize == 0 || !(sigma > 0.0f)) { windowSize = 0; return; }

    buffer = new (std::nothrow) float[windowSize];
    if (!buffer) { windowSize = 0; return; }
    kernel = new (std::nothrow) float[windowSize];
    if (!kernel) { delete[] buffer; buffer = 0; windowSize = 0; return; }

    // Exactly windowSize taps, centred on (windowSize-1)/2. Using a fractional
    // centre handles even and odd window sizes uniformly and cannot overrun.
    float center = (float)(windowSize - 1) * 0.5f;
    float twoSigmaSq = 2.0f * sigma * sigma;
    float sum = 0.0f;
    for (size_t i = 0; i < windowSize; ++i) {
        float d = (float)i - center;
        kernel[i] = expf(-(d * d) / twoSigmaSq);
        sum += kernel[i];
    }
    if (sum > 0.0f) {
        for (size_t i = 0; i < windowSize; ++i) kernel[i] /= sum;
    }
}

RealTimeGaussianFilter::~RealTimeGaussianFilter() {
    release();
}

void RealTimeGaussianFilter::release() {
    delete[] buffer;
    delete[] kernel;
    buffer = 0;
    kernel = 0;
}

void RealTimeGaussianFilter::copyFrom(const RealTimeGaussianFilter& other) {
    windowSize = other.windowSize;
    head = other.head;
    filled = other.filled;
    buffer = 0;
    kernel = 0;
    if (windowSize == 0) return;

    buffer = new (std::nothrow) float[windowSize];
    kernel = new (std::nothrow) float[windowSize];
    if (!buffer || !kernel) {
        release();
        windowSize = 0;
        filled = 0;
        head = 0;
        return;
    }
    dspCompat::copyFloat(other.buffer, buffer, windowSize);
    dspCompat::copyFloat(other.kernel, kernel, windowSize);
}

RealTimeGaussianFilter::RealTimeGaussianFilter(const RealTimeGaussianFilter& other) {
    copyFrom(other);
}

RealTimeGaussianFilter& RealTimeGaussianFilter::operator=(const RealTimeGaussianFilter& other) {
    if (this == &other) return *this;
    release();
    copyFrom(other);
    return *this;
}

void RealTimeGaussianFilter::reset() {
    head = 0;
    filled = 0;
}

float RealTimeGaussianFilter::update(float value) {
    if (!ok()) return value;

    buffer[head] = value;
    head = (head + 1) % windowSize;
    if (filled < windowSize) ++filled;

    // Walk the window oldest-to-newest so sample i lines up with kernel tap i.
    size_t oldest = (head + windowSize - filled) % windowSize;
    float acc = 0.0f, weight = 0.0f;
    for (size_t i = 0; i < filled; ++i) {
        float k = kernel[i];
        acc += buffer[(oldest + i) % windowSize] * k;
        weight += k;
    }
    // Renormalise over the taps actually used: without this the output is
    // scaled down by the missing taps until the window fills.
    return (weight > 0.0f) ? (acc / weight) : value;
}

}
