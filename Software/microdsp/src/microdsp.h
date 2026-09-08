#ifndef MICRODSP_H
#define MICRODSP_H

#include "internal/dspCompat.h"
#include "internal/dspStats.h"
#include "internal/dspCalculus.h"
#include "internal/dspFilters.h"
#include "internal/dspTransforms.h"
#include "internal/dspResources.h"
#include "internal/dspDataIO.h"
#include "internal/dspDataManager.h"
#include "internal/dspExport.h"
#include "internal/realTime/dspRealTimeStats.h"
#include "internal/realTime/dspRealTimeFilters.h"
#include "internal/realTime/dspRealTimeTransforms.h"

// MicroDSP is a thin facade over the dsp* namespaces. Every method forwards to
// the namespace of the same name, so you can use either style; the namespaces
// expose a little more (windowing, extra statistics) than the facade does.
//
// The in-place filter and transform methods return bool: false means the
// arguments were rejected (null pointer, zero length, non-power-of-two FFT
// length) or a scratch allocation failed, and your array was left untouched.
class MicroDSP {
public:
    MicroDSP();

    // ==== Stats ====
    float mean(const float* data, size_t len);
    float stdDev(const float* data, size_t len);
    float variance(const float* data, size_t len);
    float sampleStdDev(const float* data, size_t len);
    float minimum(const float* data, size_t len);
    float maximum(const float* data, size_t len);
    float rms(const float* data, size_t len);
    float median(const float* data, size_t len);
    float percentile(const float* data, size_t len, float p);

    // ==== Outliers ====
    bool isZScoreOutlier(float val, const float* data, size_t len, float threshold = 3.0f);
    bool isModifiedZScoreOutlier(float val, const float* data, size_t len, float threshold = 3.5f);
    bool isIQROutlier(float val, const float* data, size_t len, float multiplier = 1.5f);
    bool isMADOutlier(float val, const float* data, size_t len, float threshold = 3.5f);

    // ==== Calculus ====
    // Returns a new[]-allocated buffer; release it with freeBuffer().
    float* derivative(const float* data, size_t len, float deltaT, int order, size_t& outLen);
    void freeBuffer(float* buffer);
    // Allocation-free alternative: writes len-order samples into `out`.
    size_t derivativeInto(const float* data, size_t len, float deltaT, int order, float* out);

    float integral(const float* data, size_t len, float deltaT);
    float integralTrapezoid(const float* data, size_t len, float deltaT);
    bool cumulativeIntegral(const float* data, size_t len, float deltaT, float* out);

    // ==== Filters ====
    bool movingAverageFilter(float* data, size_t len, size_t windowSize);
    bool movingAverageFilterCentered(float* data, size_t len, size_t windowSize);
    bool medianFilter(float* data, size_t len, size_t windowSize);
    bool gaussianFilter(float* data, size_t len, float sigma);
    bool applyFIR(float* data, size_t len, const float* coeffs, size_t coeffLen);
    bool designKaiserFIR(float* coeffs, size_t numTaps, float beta, float cutoffNorm = 0.25f);
    bool kaiserWindow(float* window, size_t numTaps, float beta);
    bool frequencySamplingFIR(float* coeffs, size_t numTaps, const float* desiredResponse);
    bool adaptiveFilter(float* data, const float* reference, size_t len, float mu);
    bool adaptiveFilterFIR(float* data, const float* reference, size_t len,
                           float mu, float* weights, size_t numTaps);
    bool wienerFilter(float* data, size_t len, float signalVar, float noiseVar);

    // ==== Transforms ====
    // len must be a power of two.
    bool fft(float* dataReal, float* dataImag, size_t len);
    bool ifft(float* dataReal, float* dataImag, size_t len);
    bool fftMagnitude(const float* real, const float* imag, float* magnitude, size_t len);
    float dominantFrequency(const float* real, const float* imag, size_t len, float sampleRate);

    bool hannWindow(float* window, size_t len);
    bool hammingWindow(float* window, size_t len);
    bool blackmanWindow(float* window, size_t len);
    bool applyWindow(float* data, const float* window, size_t len);

    // Evaluates F(s) at one point s = sReal + j*sImag.
    bool laplaceTransform(const float* input, size_t len, float dt,
                          float sReal, float sImag, float& outReal, float& outImag);

    // ==== Resource Management ====
    void begin();                       // starts CPU-load accounting
    void setComputeLimit(uint8_t percent);
    uint8_t getComputeLimit();
    void setAvailableMemory(size_t bytes);
    size_t freeMemory();
    void setFreeMemoryThreshold(size_t bytes);
    bool canProcess(size_t bytes);
    void beginWork();
    void endWork();
    float getLoadPercent();
    bool shouldProcess();

    // ==== Exporting ====
    void exportToSerial(const float* data, size_t len, const char* label = "");
    void exportRowToSerial(const float* data, size_t len, const char* label = nullptr);
    void exportJSONToSerial(const float* data, size_t len, const char* label = nullptr);

    // ==== Real-Time Processing ====
    //
    // These return a fresh object by value. Store it once - as a global, a
    // static, or a member - and call update() on that stored object. Calling
    // these inside loop() builds a brand new empty window every iteration and
    // the filter never accumulates any history.
    dspRealTime::RealTimeStats realTimeStats(size_t windowSize);
    dspRealTime::RealTimeMovingAverage realTimeMovingAverage(size_t windowSize);
    dspRealTime::RealTimeMedianFilter realTimeMedianFilter(size_t windowSize);
    dspRealTime::RealTimeGaussianFilter realTimeGaussianFilter(size_t windowSize, float sigma);
    // windowSize must be a power of two.
    dspRealTime::RealTimeFFT realTimeFFT(size_t windowSize);
};

#endif
