#include "dspCalculus.h"
#include "dspCompat.h"
#include <new>

namespace dspCalculus {

    // Shared core: differentiates `work` in place `order` times, returning the
    // surviving length. Each pass shortens the run by one sample.
    static size_t differentiateInPlace(float* work, size_t len, float dt, int order) {
        float invDt = 1.0f / dt;
        size_t currentLen = len;
        for (int k = 0; k < order; ++k) {
            for (size_t i = 0; i + 1 < currentLen; ++i) {
                work[i] = (work[i + 1] - work[i]) * invDt;
            }
            --currentLen;
        }
        return currentLen;
    }

    static bool derivativeArgsValid(const float* data, size_t len, float dt, int order) {
        if (!data || order < 1) return false;
        if (len <= (size_t)order) return false;
        // dt == 0 would divide by zero and fill the result with infinities.
        if (dt == 0.0f) return false;
        return true;
    }

    float* nthDerivative(const float* data, size_t len, float dt, int order,
                         size_t& outLen) {
        outLen = 0;
        if (!derivativeArgsValid(data, len, dt, order)) return nullptr;

        // One allocation, sized to the result. 1.x allocated three buffers of
        // `len` and ping-ponged between two of them.
        size_t resultLen = len - (size_t)order;
        float* work = new (std::nothrow) float[len];
        if (!work) return nullptr;
        dspCompat::copyFloat(data, work, len);

        differentiateInPlace(work, len, dt, order);

        float* result = new (std::nothrow) float[resultLen];
        if (!result) { delete[] work; return nullptr; }
        dspCompat::copyFloat(work, result, resultLen);

        delete[] work;
        outLen = resultLen;
        return result;
    }

    void freeBuffer(float* buffer) {
        delete[] buffer;
    }

    size_t derivativeInto(const float* data, size_t len, float dt, int order,
                          float* out) {
        if (!out) return 0;
        if (!derivativeArgsValid(data, len, dt, order)) return 0;

        // `out` holds len - order samples, but the intermediate passes need up
        // to len. Differentiate the first pass straight from `data` into `out`
        // (which shortens it to len-1), then continue in place.
        size_t currentLen = len - 1;
        float invDt = 1.0f / dt;
        for (size_t i = 0; i < currentLen; ++i) {
            out[i] = (data[i + 1] - data[i]) * invDt;
        }
        if (order > 1) {
            currentLen = differentiateInPlace(out, currentLen, dt, order - 1);
        }
        return currentLen;
    }

    float definiteIntegral(const float* data, size_t len, float dx) {
        if (!data || len == 0) return 0.0f;
        float sum = 0.0f;
        for (size_t i = 0; i < len; ++i) sum += data[i];
        return sum * dx;
    }

    float integralTrapezoid(const float* data, size_t len, float dx) {
        if (!data || len == 0) return 0.0f;
        if (len == 1) return 0.0f;          // a single sample spans no interval

        float sum = 0.5f * (data[0] + data[len - 1]);
        for (size_t i = 1; i + 1 < len; ++i) sum += data[i];
        return sum * dx;
    }

    bool cumulativeIntegral(const float* data, size_t len, float dx, float* out) {
        if (!data || !out || len == 0) return false;

        // Forward order, and each step only reads data[i] and data[i-1] before
        // writing out[i], so out may alias data.
        float running = 0.0f;
        float previous = data[0];
        out[0] = 0.0f;
        for (size_t i = 1; i < len; ++i) {
            float current = data[i];
            running += 0.5f * (previous + current) * dx;
            previous = current;
            out[i] = running;
        }
        return true;
    }

    float tripleIntegral(const float* data, size_t xLen, size_t yLen, size_t zLen,
                         float dx, float dy, float dz) {
        if (!data || xLen == 0 || yLen == 0 || zLen == 0) return 0.0f;

        float total = 0.0f;
        size_t count = xLen * yLen * zLen;
        for (size_t i = 0; i < count; ++i) total += data[i];
        return total * dx * dy * dz;
    }

}
