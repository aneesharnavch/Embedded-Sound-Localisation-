#include "dspFilters.h"
#include "dspCompat.h"
#include <math.h>
#include <new>

namespace dspFilters {

    // ---- shared centred-window machinery ------------------------------------
    //
    // A centred filter at output index o needs input samples o-k .. o+k, but
    // filtering in place destroys inputs that later outputs still need. Rather
    // than copy the whole array (the 1.x approach, O(len) extra RAM), we keep a
    // delay line of the last 2k+1 originals and emit output o = p-k while
    // reading input p. Writes always trail reads by k samples, so the delay
    // line always holds exactly the window each output needs: O(windowSize).

    typedef float (*ReduceFn)(float* window, size_t n);

    static float reduceMean(float* window, size_t n) {
        if (n == 0) return 0.0f;
        float sum = 0.0f;
        for (size_t i = 0; i < n; ++i) sum += window[i];
        return sum / (float)n;
    }

    static float reduceMedian(float* window, size_t n) {
        if (n == 0) return 0.0f;
        dspCompat::sortFloat(window, n);
        return dspCompat::medianSorted(window, n);
    }

    static bool centeredWindowFilter(float* data, size_t len, size_t windowSize,
                                     ReduceFn reduce) {
        if (!data || len == 0 || windowSize == 0) return false;

        // An even windowSize has no true centre tap, so it is rounded up to
        // the next odd length to keep the filter zero-phase.
        size_t k = windowSize / 2;
        if (k == 0) return true;                 // window of 1 is the identity
        size_t eff = 2 * k + 1;

        float* ring = new (std::nothrow) float[eff];
        if (!ring) return false;
        float* work = new (std::nothrow) float[eff];
        if (!work) { delete[] ring; return false; }

        for (size_t p = 0; p < len + k; ++p) {
            if (p < len) ring[p % eff] = data[p];
            if (p < k) continue;

            size_t o = p - k;                    // output index, trails by k
            size_t hi = (p < len) ? p : len - 1; // newest original in the ring
            size_t lo = (hi + 1 >= eff) ? (hi + 1 - eff) : 0;

            size_t a = (o >= k) ? (o - k) : 0;
            if (a < lo) a = lo;
            size_t b = o + k;
            if (b > hi) b = hi;

            size_t n = 0;
            for (size_t j = a; j <= b; ++j) work[n++] = ring[j % eff];
            data[o] = reduce(work, n);
        }

        delete[] work;
        delete[] ring;
        return true;
    }

    // ---- moving average -----------------------------------------------------

    bool movingAverage(float* data, size_t len, size_t windowSize) {
        if (!data || len == 0 || windowSize == 0) return false;
        if (windowSize > len) windowSize = len;

        float* hist = new (std::nothrow) float[windowSize];
        if (!hist) return false;

        // Sliding sum: O(len) regardless of window size. Only `hist` is read
        // for old samples, so writing data[i] in place is safe.
        float sum = 0.0f;
        size_t count = 0, head = 0;
        for (size_t i = 0; i < len; ++i) {
            float x = data[i];
            if (count < windowSize) {
                hist[head] = x;
                sum += x;
                ++count;
            } else {
                sum -= hist[head];
                hist[head] = x;
                sum += x;
            }
            head = (head + 1) % windowSize;
            data[i] = sum / (float)count;
        }

        delete[] hist;
        return true;
    }

    bool movingAverageCentered(float* data, size_t len, size_t windowSize) {
        return centeredWindowFilter(data, len, windowSize, reduceMean);
    }

    bool medianFilter(float* data, size_t len, size_t windowSize) {
        return centeredWindowFilter(data, len, windowSize, reduceMedian);
    }

    // ---- gaussian -----------------------------------------------------------

    bool gaussianFilter(float* data, size_t len, float sigma) {
        if (!data || len == 0) return false;
        if (!(sigma > 0.0f)) return false;       // also rejects NaN

        long r = (long)ceilf(3.0f * sigma);
        if (r < 1) r = 1;
        if ((size_t)r > len) r = (long)len;
        size_t radius = (size_t)r;
        size_t eff = 2 * radius + 1;

        float* kernel = new (std::nothrow) float[eff];
        if (!kernel) return false;
        // The 1/sqrt(2*pi*sigma^2) scale factor is omitted: we normalise by
        // the tap sum below, which subsumes it.
        float twoSigmaSq = 2.0f * sigma * sigma;
        for (long j = -r; j <= r; ++j) {
            float fj = (float)j;
            kernel[(size_t)(j + r)] = expf(-(fj * fj) / twoSigmaSq);
        }

        float* ring = new (std::nothrow) float[eff];
        if (!ring) { delete[] kernel; return false; }

        for (size_t p = 0; p < len + radius; ++p) {
            if (p < len) ring[p % eff] = data[p];
            if (p < radius) continue;

            size_t o = p - radius;
            size_t hi = (p < len) ? p : len - 1;
            size_t lo = (hi + 1 >= eff) ? (hi + 1 - eff) : 0;

            size_t a = (o >= radius) ? (o - radius) : 0;
            if (a < lo) a = lo;
            size_t b = o + radius;
            if (b > hi) b = hi;

            // Renormalise over the taps that actually landed in bounds,
            // otherwise the first and last `radius` samples decay towards zero.
            float acc = 0.0f, wsum = 0.0f;
            for (size_t j = a; j <= b; ++j) {
                size_t tap = (size_t)((long)j - (long)o + r);
                float w = kernel[tap];
                acc += ring[j % eff] * w;
                wsum += w;
            }
            data[o] = (wsum > 0.0f) ? (acc / wsum) : ring[o % eff];
        }

        delete[] ring;
        delete[] kernel;
        return true;
    }

    // ---- FIR ----------------------------------------------------------------

    bool applyFIR(float* data, size_t len, const float* coeffs, size_t coeffLen) {
        if (!data || !coeffs || len == 0 || coeffLen == 0) return false;

        // Walking backwards means every sample we read (index <= i) is still
        // the original, so the convolution runs in place with zero scratch.
        for (size_t i = len; i-- > 0; ) {
            float sum = 0.0f;
            size_t taps = (i + 1 < coeffLen) ? (i + 1) : coeffLen;
            for (size_t j = 0; j < taps; ++j) sum += coeffs[j] * data[i - j];
            data[i] = sum;
        }
        return true;
    }

    // ---- design -------------------------------------------------------------

    bool kaiserWindow(float* window, size_t numTaps, float beta) {
        if (!window || numTaps == 0) return false;
        if (numTaps == 1) { window[0] = 1.0f; return true; }

        float denom = dspCompat::bessi0(beta);
        if (denom == 0.0f) return false;

        float n1 = (float)(numTaps - 1);
        for (size_t n = 0; n < numTaps; ++n) {
            float ratio = 2.0f * (float)n / n1 - 1.0f;
            float arg = 1.0f - ratio * ratio;
            if (arg < 0.0f) arg = 0.0f;          // rounding at the endpoints
            window[n] = dspCompat::bessi0(beta * sqrtf(arg)) / denom;
        }
        return true;
    }

    bool designKaiserFIR(float* coeffs, size_t numTaps, float beta,
                         float cutoffNorm) {
        if (!coeffs || numTaps == 0) return false;
        if (!(cutoffNorm > 0.0f) || cutoffNorm >= 0.5f) return false;
        if (!kaiserWindow(coeffs, numTaps, beta)) return false;

        // Multiply the Kaiser window by the ideal lowpass impulse response
        // h[m] = sin(2*pi*fc*m) / (pi*m), which is 2*fc at m = 0.
        float center = (float)(numTaps - 1) * 0.5f;
        float sum = 0.0f;
        for (size_t n = 0; n < numTaps; ++n) {
            float m = (float)n - center;
            float ideal;
            if (fabsf(m) < 1e-6f) {
                ideal = 2.0f * cutoffNorm;
            } else {
                ideal = sinf(DSP_TWO_PI * cutoffNorm * m) / (DSP_PI * m);
            }
            coeffs[n] *= ideal;
            sum += coeffs[n];
        }

        // Normalise to unity gain at DC.
        if (sum != 0.0f) {
            for (size_t n = 0; n < numTaps; ++n) coeffs[n] /= sum;
        }
        return true;
    }

    bool frequencySamplingFIR(float* coeffs, size_t numTaps,
                              const float* desiredResponse) {
        if (!coeffs || !desiredResponse || numTaps == 0) return false;

        size_t half = numTaps / 2;
        float center = (float)(numTaps - 1) * 0.5f;
        bool even = (numTaps % 2 == 0);

        for (size_t n = 0; n < numTaps; ++n) {
            // Inverse DFT of a real, symmetric magnitude response, evaluated
            // about the centre tap so the result is linear phase and can be
            // fed straight to applyFIR.
            float acc = desiredResponse[0];
            for (size_t k = 1; k <= half; ++k) {
                // For even numTaps the Nyquist bin has no mirror partner.
                float weight = (even && k == half) ? 1.0f : 2.0f;
                float phase = DSP_TWO_PI * (float)k * ((float)n - center)
                              / (float)numTaps;
                acc += weight * desiredResponse[k] * cosf(phase);
            }
            coeffs[n] = acc / (float)numTaps;
        }
        return true;
    }

    // ---- adaptive -----------------------------------------------------------

    bool adaptiveFilter(float* data, const float* reference, size_t len, float mu) {
        if (!data || !reference || len == 0) return false;

        float w = 0.0f;
        for (size_t i = 0; i < len; ++i) {
            float y = w * reference[i];      // estimate of the correlated noise
            float e = data[i] - y;           // what is left once it is removed
            w += mu * e * reference[i];
            data[i] = e;
        }
        return true;
    }

    bool adaptiveFilterFIR(float* data, const float* reference, size_t len,
                           float mu, float* weights, size_t numTaps) {
        if (!data || !reference || !weights || len == 0 || numTaps == 0) return false;

        for (size_t i = 0; i < len; ++i) {
            size_t taps = (i + 1 < numTaps) ? (i + 1) : numTaps;

            float y = 0.0f, power = 0.0f;
            for (size_t j = 0; j < taps; ++j) {
                float x = reference[i - j];
                y += weights[j] * x;
                power += x * x;
            }

            float e = data[i] - y;
            // Normalised LMS: dividing by reference power makes the usable
            // range of mu independent of input amplitude. The epsilon keeps
            // a silent reference from producing a divide-by-zero.
            float step = mu * e / (power + 1e-6f);
            for (size_t j = 0; j < taps; ++j) weights[j] += step * reference[i - j];

            data[i] = e;
        }
        return true;
    }

    bool wienerFilter(float* data, size_t len, float signalVar, float noiseVar) {
        if (!data || len == 0) return false;
        float denom = signalVar + noiseVar;
        if (!(denom > 0.0f)) return false;

        float gain = signalVar / denom;
        for (size_t i = 0; i < len; ++i) data[i] *= gain;
        return true;
    }

}
