#include "microdsp.h"

MicroDSP::MicroDSP() {
    // Nothing to set up; call begin() if you intend to use the CPU-load
    // throttling helpers.
}

// ==== Stats ====
float MicroDSP::mean(const float* data, size_t len) {
    return dspStats::mean(data, len);
}

float MicroDSP::stdDev(const float* data, size_t len) {
    return dspStats::stdDev(data, len);
}

float MicroDSP::variance(const float* data, size_t len) {
    return dspStats::variance(data, len);
}

float MicroDSP::sampleStdDev(const float* data, size_t len) {
    return dspStats::sampleStdDev(data, len);
}

float MicroDSP::minimum(const float* data, size_t len) {
    return dspStats::minimum(data, len);
}

float MicroDSP::maximum(const float* data, size_t len) {
    return dspStats::maximum(data, len);
}

float MicroDSP::rms(const float* data, size_t len) {
    return dspStats::rms(data, len);
}

float MicroDSP::median(const float* data, size_t len) {
    return dspStats::median(data, len);
}

float MicroDSP::percentile(const float* data, size_t len, float p) {
    return dspStats::percentile(data, len, p);
}

// ==== Outliers ====
bool MicroDSP::isZScoreOutlier(float val, const float* data, size_t len, float threshold) {
    return dspStats::isZScoreOutlier(val, data, len, threshold);
}

bool MicroDSP::isModifiedZScoreOutlier(float val, const float* data, size_t len, float threshold) {
    return dspStats::isModifiedZScoreOutlier(val, data, len, threshold);
}

bool MicroDSP::isIQROutlier(float val, const float* data, size_t len, float multiplier) {
    return dspStats::isIQROutlier(val, data, len, multiplier);
}

bool MicroDSP::isMADOutlier(float val, const float* data, size_t len, float threshold) {
    return dspStats::isMADOutlier(val, data, len, threshold);
}

// ==== Calculus ====
float* MicroDSP::derivative(const float* data, size_t len, float deltaT, int order, size_t& outLen) {
    return dspCalculus::nthDerivative(data, len, deltaT, order, outLen);
}

void MicroDSP::freeBuffer(float* buffer) {
    dspCalculus::freeBuffer(buffer);
}

size_t MicroDSP::derivativeInto(const float* data, size_t len, float deltaT, int order, float* out) {
    return dspCalculus::derivativeInto(data, len, deltaT, order, out);
}

float MicroDSP::integral(const float* data, size_t len, float deltaT) {
    return dspCalculus::definiteIntegral(data, len, deltaT);
}

float MicroDSP::integralTrapezoid(const float* data, size_t len, float deltaT) {
    return dspCalculus::integralTrapezoid(data, len, deltaT);
}

bool MicroDSP::cumulativeIntegral(const float* data, size_t len, float deltaT, float* out) {
    return dspCalculus::cumulativeIntegral(data, len, deltaT, out);
}

// ==== Filters ====
bool MicroDSP::movingAverageFilter(float* data, size_t len, size_t windowSize) {
    return dspFilters::movingAverage(data, len, windowSize);
}

bool MicroDSP::movingAverageFilterCentered(float* data, size_t len, size_t windowSize) {
    return dspFilters::movingAverageCentered(data, len, windowSize);
}

bool MicroDSP::medianFilter(float* data, size_t len, size_t windowSize) {
    return dspFilters::medianFilter(data, len, windowSize);
}

bool MicroDSP::gaussianFilter(float* data, size_t len, float sigma) {
    return dspFilters::gaussianFilter(data, len, sigma);
}

bool MicroDSP::applyFIR(float* data, size_t len, const float* coeffs, size_t coeffLen) {
    return dspFilters::applyFIR(data, len, coeffs, coeffLen);
}

bool MicroDSP::designKaiserFIR(float* coeffs, size_t numTaps, float beta, float cutoffNorm) {
    return dspFilters::designKaiserFIR(coeffs, numTaps, beta, cutoffNorm);
}

bool MicroDSP::kaiserWindow(float* window, size_t numTaps, float beta) {
    return dspFilters::kaiserWindow(window, numTaps, beta);
}

bool MicroDSP::frequencySamplingFIR(float* coeffs, size_t numTaps, const float* desiredResponse) {
    return dspFilters::frequencySamplingFIR(coeffs, numTaps, desiredResponse);
}

bool MicroDSP::adaptiveFilter(float* data, const float* reference, size_t len, float mu) {
    return dspFilters::adaptiveFilter(data, reference, len, mu);
}

bool MicroDSP::adaptiveFilterFIR(float* data, const float* reference, size_t len,
                                 float mu, float* weights, size_t numTaps) {
    return dspFilters::adaptiveFilterFIR(data, reference, len, mu, weights, numTaps);
}

bool MicroDSP::wienerFilter(float* data, size_t len, float signalVar, float noiseVar) {
    return dspFilters::wienerFilter(data, len, signalVar, noiseVar);
}

// ==== Transforms ====
bool MicroDSP::fft(float* dataReal, float* dataImag, size_t len) {
    return dspTransforms::fft(dataReal, dataImag, len);
}

bool MicroDSP::ifft(float* dataReal, float* dataImag, size_t len) {
    return dspTransforms::ifft(dataReal, dataImag, len);
}

bool MicroDSP::fftMagnitude(const float* real, const float* imag, float* magnitude, size_t len) {
    return dspTransforms::fftMagnitude(real, imag, magnitude, len);
}

float MicroDSP::dominantFrequency(const float* real, const float* imag, size_t len, float sampleRate) {
    return dspTransforms::dominantFrequency(real, imag, len, sampleRate);
}

bool MicroDSP::hannWindow(float* window, size_t len) {
    return dspTransforms::hannWindow(window, len);
}

bool MicroDSP::hammingWindow(float* window, size_t len) {
    return dspTransforms::hammingWindow(window, len);
}

bool MicroDSP::blackmanWindow(float* window, size_t len) {
    return dspTransforms::blackmanWindow(window, len);
}

bool MicroDSP::applyWindow(float* data, const float* window, size_t len) {
    return dspTransforms::applyWindow(data, window, len);
}

bool MicroDSP::laplaceTransform(const float* input, size_t len, float dt,
                                float sReal, float sImag, float& outReal, float& outImag) {
    return dspTransforms::laplaceTransform(input, len, dt, sReal, sImag, outReal, outImag);
}

// ==== Resource Management ====
void MicroDSP::begin() {
    dspResources::init();
}

void MicroDSP::setComputeLimit(uint8_t percent) {
    dspResources::setComputeLimit(percent);
}

uint8_t MicroDSP::getComputeLimit() {
    return dspResources::getComputeLimit();
}

void MicroDSP::setAvailableMemory(size_t bytes) {
    dspResources::setAvailableMemory(bytes);
}

size_t MicroDSP::freeMemory() {
    return dspResources::freeMemory();
}

void MicroDSP::setFreeMemoryThreshold(size_t bytes) {
    dspResources::setFreeMemoryThreshold(bytes);
}

bool MicroDSP::canProcess(size_t bytes) {
    return dspResources::hasSufficientMemory(bytes);
}

void MicroDSP::beginWork() {
    dspResources::beginWork();
}

void MicroDSP::endWork() {
    dspResources::endWork();
}

float MicroDSP::getLoadPercent() {
    return dspResources::getLoadPercent();
}

bool MicroDSP::shouldProcess() {
    return dspResources::shouldProcess();
}

// ==== Export ====
void MicroDSP::exportToSerial(const float* data, size_t len, const char* label) {
    // An empty label would otherwise print a blank line; treat it as "none".
    const char* effective = (label && label[0]) ? label : nullptr;
    dspDataIO::exportCSV(data, len, effective);
}

void MicroDSP::exportRowToSerial(const float* data, size_t len, const char* label) {
    dspDataIO::exportCSVRow(data, len, label);
}

void MicroDSP::exportJSONToSerial(const float* data, size_t len, const char* label) {
    dspDataIO::exportJSON(data, len, label);
}

// ==== Real-Time Processing ====
dspRealTime::RealTimeStats MicroDSP::realTimeStats(size_t windowSize) {
    return dspRealTime::RealTimeStats(windowSize);
}

dspRealTime::RealTimeMovingAverage MicroDSP::realTimeMovingAverage(size_t windowSize) {
    return dspRealTime::RealTimeMovingAverage(windowSize);
}

dspRealTime::RealTimeMedianFilter MicroDSP::realTimeMedianFilter(size_t windowSize) {
    return dspRealTime::RealTimeMedianFilter(windowSize);
}

dspRealTime::RealTimeGaussianFilter MicroDSP::realTimeGaussianFilter(size_t windowSize, float sigma) {
    return dspRealTime::RealTimeGaussianFilter(windowSize, sigma);
}

dspRealTime::RealTimeFFT MicroDSP::realTimeFFT(size_t windowSize) {
    return dspRealTime::RealTimeFFT(windowSize);
}
