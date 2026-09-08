#ifndef DSP_REALTIME_TRANSFORMS_H
#define DSP_REALTIME_TRANSFORMS_H

#include <stddef.h>

namespace dspRealTime {

// Sliding-window FFT over a stream of samples.
//
// windowSize MUST be a power of two (16, 32, 64, ...). Anything else leaves the
// object in a failed state (ok() == false). In 1.x a non-power-of-two window
// ran the butterfly loop past the end of the output vectors - a 12-sample
// window wrote 4 floats beyond the allocation - and returned nonsense.
class RealTimeFFT {
public:
    explicit RealTimeFFT(size_t windowSize);
    ~RealTimeFFT();
    RealTimeFFT(const RealTimeFFT& other);
    RealTimeFFT& operator=(const RealTimeFFT& other);

    bool ok() const { return buffer != 0; }
    void reset();

    // Adds a sample. Once the window is full every call recomputes the whole
    // transform, which is O(n log n) per sample: for a 64-point window on an
    // 8-bit core, prefer calling updateDeferred() and transform() so you can
    // transform once per batch of samples instead.
    void update(float value);

    // Adds a sample without transforming. Returns true once the window is
    // full, i.e. when a transform() would be meaningful.
    bool updateDeferred(float value);

    // Recomputes the spectrum from the current window. Returns false if the
    // window is not yet full.
    bool transform();

    // True once windowSize samples have been seen. 1.x only set this on the
    // sample *after* the window filled, so the first transform came one sample
    // late and getReal() read all zeros when the window was exactly full.
    bool isReady() const { return ready; }

    // Spectrum, windowSize entries each. Valid once isReady() is true.
    const float* getReal() const { return real; }
    const float* getImag() const { return imag; }
    size_t size() const { return windowSize; }

    // Magnitude of bin i, sqrt(re^2 + im^2).
    float magnitude(size_t bin) const;

    // Frequency of the strongest non-DC bin, with parabolic interpolation.
    float dominantFrequency(float sampleRate) const;

    // Applies a Hann window to each transform, which suppresses the spectral
    // leakage you otherwise get from a window that does not contain a whole
    // number of cycles. Off by default (1.x had no windowing at all).
    void setUseHannWindow(bool enable);
    bool usesHannWindow() const { return hann != 0; }

private:
    float* buffer;     // ring of raw samples
    float* real;
    float* imag;
    float* hann;       // null unless windowing is enabled
    size_t windowSize;
    size_t head;
    size_t filled;
    bool ready;

    void copyFrom(const RealTimeFFT& other);
    void release();
    bool buildHann();
};

}

#endif
