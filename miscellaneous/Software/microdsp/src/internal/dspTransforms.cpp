#include "dspTransforms.h"
#include "dspCompat.h"
#include <math.h>

namespace dspTransforms {

    bool fft(float* real, float* imag, size_t len) {
        if (!real || !imag) return false;
        if (!dspCompat::isPowerOfTwo(len)) return false;
        if (len == 1) return true;

        // Decimation in time: reorder into bit-reversed index order so the
        // butterflies below can run in place.
        for (size_t i = 1, j = 0; i < len; ++i) {
            size_t bit = len >> 1;
            for (; j & bit; bit >>= 1) j ^= bit;
            j ^= bit;
            if (i < j) {
                dspCompat::swapFloat(real[i], real[j]);
                dspCompat::swapFloat(imag[i], imag[j]);
            }
        }

        // Iterative Cooley-Tukey. Every stage doubles the sub-transform size,
        // and the twiddle factor is advanced by complex multiplication rather
        // than recomputed with cos/sin per butterfly - four trig calls per
        // butterfly is ruinous on a core without an FPU.
        for (size_t size = 2; size <= len; size <<= 1) {
            float angle = -DSP_TWO_PI / (float)size;
            float wStepReal = cosf(angle);
            float wStepImag = sinf(angle);
            size_t half = size >> 1;

            for (size_t start = 0; start < len; start += size) {
                float wReal = 1.0f, wImag = 0.0f;
                for (size_t j = 0; j < half; ++j) {
                    size_t a = start + j;
                    size_t b = a + half;

                    float uReal = real[a], uImag = imag[a];
                    float vReal = real[b] * wReal - imag[b] * wImag;
                    float vImag = real[b] * wImag + imag[b] * wReal;

                    real[a] = uReal + vReal;
                    imag[a] = uImag + vImag;
                    real[b] = uReal - vReal;
                    imag[b] = uImag - vImag;

                    float nextReal = wReal * wStepReal - wImag * wStepImag;
                    wImag = wReal * wStepImag + wImag * wStepReal;
                    wReal = nextReal;
                }
            }
        }
        return true;
    }

    bool ifft(float* real, float* imag, size_t len) {
        if (!real || !imag) return false;
        if (!dspCompat::isPowerOfTwo(len)) return false;

        // conj -> forward FFT -> conj, then scale by 1/len.
        for (size_t i = 0; i < len; ++i) imag[i] = -imag[i];
        if (!fft(real, imag, len)) return false;

        float scale = 1.0f / (float)len;
        for (size_t i = 0; i < len; ++i) {
            real[i] *= scale;
            imag[i] *= -scale;
        }
        return true;
    }

    bool fftMagnitude(const float* real, const float* imag, float* magnitude,
                      size_t len) {
        if (!real || !imag || !magnitude || len == 0) return false;
        for (size_t i = 0; i < len; ++i) {
            magnitude[i] = sqrtf(real[i] * real[i] + imag[i] * imag[i]);
        }
        return true;
    }

    static float binMagnitude(const float* real, const float* imag, size_t i) {
        return sqrtf(real[i] * real[i] + imag[i] * imag[i]);
    }

    size_t dominantBin(const float* real, const float* imag, size_t len) {
        if (!real || !imag || len < 4) return 0;

        // Only the first half is unique for real input; bin 0 is DC, which is
        // just the mean and almost never the answer the caller wants.
        size_t limit = len / 2;
        size_t best = 1;
        float bestMag = binMagnitude(real, imag, 1);
        for (size_t i = 2; i < limit; ++i) {
            float m = binMagnitude(real, imag, i);
            if (m > bestMag) { bestMag = m; best = i; }
        }
        return best;
    }

    float dominantFrequency(const float* real, const float* imag, size_t len,
                            float sampleRate) {
        if (!real || !imag || len < 4 || !(sampleRate > 0.0f)) return 0.0f;

        size_t peak = dominantBin(real, imag, len);
        float offset = 0.0f;

        // Parabolic interpolation through the peak and its two neighbours
        // recovers a frequency between bin centres, which matters because bin
        // spacing is sampleRate/len - often tens of Hz.
        if (peak >= 1 && peak + 1 < len / 2) {
            float lo = binMagnitude(real, imag, peak - 1);
            float mid = binMagnitude(real, imag, peak);
            float hi = binMagnitude(real, imag, peak + 1);
            float denom = lo - 2.0f * mid + hi;
            if (fabsf(denom) > 1e-12f) {
                offset = 0.5f * (lo - hi) / denom;
                if (offset > 0.5f) offset = 0.5f;
                if (offset < -0.5f) offset = -0.5f;
            }
        }

        return ((float)peak + offset) * sampleRate / (float)len;
    }

    // ---- windows ------------------------------------------------------------

    bool hannWindow(float* window, size_t len) {
        if (!window || len == 0) return false;
        if (len == 1) { window[0] = 1.0f; return true; }
        float n1 = (float)(len - 1);
        for (size_t n = 0; n < len; ++n) {
            window[n] = 0.5f - 0.5f * cosf(DSP_TWO_PI * (float)n / n1);
        }
        return true;
    }

    bool hammingWindow(float* window, size_t len) {
        if (!window || len == 0) return false;
        if (len == 1) { window[0] = 1.0f; return true; }
        float n1 = (float)(len - 1);
        for (size_t n = 0; n < len; ++n) {
            window[n] = 0.54f - 0.46f * cosf(DSP_TWO_PI * (float)n / n1);
        }
        return true;
    }

    bool blackmanWindow(float* window, size_t len) {
        if (!window || len == 0) return false;
        if (len == 1) { window[0] = 1.0f; return true; }
        float n1 = (float)(len - 1);
        for (size_t n = 0; n < len; ++n) {
            float x = DSP_TWO_PI * (float)n / n1;
            window[n] = 0.42f - 0.5f * cosf(x) + 0.08f * cosf(2.0f * x);
        }
        return true;
    }

    bool applyWindow(float* data, const float* window, size_t len) {
        if (!data || !window || len == 0) return false;
        for (size_t i = 0; i < len; ++i) data[i] *= window[i];
        return true;
    }

    // ---- Laplace ------------------------------------------------------------

    bool laplaceTransform(const float* input, size_t len, float dt,
                          float sReal, float sImag,
                          float& outReal, float& outImag) {
        outReal = 0.0f;
        outImag = 0.0f;
        if (!input || len == 0) return false;

        // F(s) = sum f(t) e^(-sigma t) [cos(omega t) - j sin(omega t)] dt
        for (size_t i = 0; i < len; ++i) {
            float t = (float)i * dt;
            float decay = expf(-sReal * t) * input[i];
            outReal += decay * cosf(sImag * t);
            outImag -= decay * sinf(sImag * t);
        }
        outReal *= dt;
        outImag *= dt;
        return true;
    }

    bool laplaceIntegrand(const float* input, float* outputReal,
                          float* outputImag, size_t len, float dt,
                          float sReal, float sImag) {
        if (!input || !outputReal || !outputImag || len == 0) return false;
        for (size_t i = 0; i < len; ++i) {
            float t = (float)i * dt;
            float decay = expf(-sReal * t) * input[i];
            outputReal[i] = decay * cosf(sImag * t);
            outputImag[i] = -decay * sinf(sImag * t);
        }
        return true;
    }

}
