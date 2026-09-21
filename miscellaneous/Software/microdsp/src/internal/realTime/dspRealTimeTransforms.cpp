#include "dspRealTimeTransforms.h"
#include "../dspCompat.h"
#include "../dspTransforms.h"
#include <math.h>
#include <new>

namespace dspRealTime {

RealTimeFFT::RealTimeFFT(size_t windowSize_)
    : buffer(0), real(0), imag(0), hann(0), windowSize(windowSize_),
      head(0), filled(0), ready(false) {
    // Radix-2 only. Rejecting this up front is what stops the butterfly loop
    // from running off the end of the arrays.
    if (!dspCompat::isPowerOfTwo(windowSize)) { windowSize = 0; return; }

    buffer = new (std::nothrow) float[windowSize];
    real = new (std::nothrow) float[windowSize];
    imag = new (std::nothrow) float[windowSize];
    if (!buffer || !real || !imag) {
        release();
        windowSize = 0;
        return;
    }
    for (size_t i = 0; i < windowSize; ++i) {
        real[i] = 0.0f;
        imag[i] = 0.0f;
    }
}

RealTimeFFT::~RealTimeFFT() {
    release();
}

void RealTimeFFT::release() {
    delete[] buffer;
    delete[] real;
    delete[] imag;
    delete[] hann;
    buffer = 0;
    real = 0;
    imag = 0;
    hann = 0;
}

void RealTimeFFT::copyFrom(const RealTimeFFT& other) {
    windowSize = other.windowSize;
    head = other.head;
    filled = other.filled;
    ready = other.ready;
    buffer = 0;
    real = 0;
    imag = 0;
    hann = 0;
    if (windowSize == 0) return;

    buffer = new (std::nothrow) float[windowSize];
    real = new (std::nothrow) float[windowSize];
    imag = new (std::nothrow) float[windowSize];
    if (!buffer || !real || !imag) {
        release();
        windowSize = 0;
        filled = 0;
        head = 0;
        ready = false;
        return;
    }
    dspCompat::copyFloat(other.buffer, buffer, windowSize);
    dspCompat::copyFloat(other.real, real, windowSize);
    dspCompat::copyFloat(other.imag, imag, windowSize);

    if (other.hann) {
        hann = new (std::nothrow) float[windowSize];
        if (hann) dspCompat::copyFloat(other.hann, hann, windowSize);
    }
}

RealTimeFFT::RealTimeFFT(const RealTimeFFT& other) {
    copyFrom(other);
}

RealTimeFFT& RealTimeFFT::operator=(const RealTimeFFT& other) {
    if (this == &other) return *this;
    release();
    copyFrom(other);
    return *this;
}

void RealTimeFFT::reset() {
    head = 0;
    filled = 0;
    ready = false;
    for (size_t i = 0; i < windowSize; ++i) {
        real[i] = 0.0f;
        imag[i] = 0.0f;
    }
}

bool RealTimeFFT::buildHann() {
    if (hann) return true;
    hann = new (std::nothrow) float[windowSize];
    if (!hann) return false;
    dspTransforms::hannWindow(hann, windowSize);
    return true;
}

void RealTimeFFT::setUseHannWindow(bool enable) {
    if (!ok()) return;
    if (enable) {
        buildHann();
    } else {
        delete[] hann;
        hann = 0;
    }
}

bool RealTimeFFT::updateDeferred(float value) {
    if (!ok()) return false;

    buffer[head] = value;
    head = (head + 1) % windowSize;
    if (filled < windowSize) ++filled;
    // Set as soon as the window is genuinely full, not one sample later.
    if (filled == windowSize) ready = true;
    return ready;
}

void RealTimeFFT::update(float value) {
    if (updateDeferred(value)) transform();
}

bool RealTimeFFT::transform() {
    if (!ok() || !ready) return false;

    // Unpack the ring oldest-to-newest into the work arrays.
    size_t oldest = (head + windowSize - filled) % windowSize;
    for (size_t i = 0; i < windowSize; ++i) {
        real[i] = buffer[(oldest + i) % windowSize];
        imag[i] = 0.0f;
    }
    if (hann) dspTransforms::applyWindow(real, hann, windowSize);

    return dspTransforms::fft(real, imag, windowSize);
}

float RealTimeFFT::magnitude(size_t bin) const {
    if (!ok() || bin >= windowSize) return 0.0f;
    return sqrtf(real[bin] * real[bin] + imag[bin] * imag[bin]);
}

float RealTimeFFT::dominantFrequency(float sampleRate) const {
    if (!ok() || !ready) return 0.0f;
    return dspTransforms::dominantFrequency(real, imag, windowSize, sampleRate);
}

}
