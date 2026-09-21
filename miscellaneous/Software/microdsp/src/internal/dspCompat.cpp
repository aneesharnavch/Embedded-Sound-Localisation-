#include "dspCompat.h"
#include <math.h>

namespace dspCompat {

    // Insertion sort wins below this length and avoids heapsort's overhead;
    // filter windows are almost always in this range.
    static const size_t INSERTION_THRESHOLD = 16;

    static void insertionSort(float* a, size_t n) {
        for (size_t i = 1; i < n; ++i) {
            float key = a[i];
            size_t j = i;
            while (j > 0 && a[j - 1] > key) {
                a[j] = a[j - 1];
                --j;
            }
            a[j] = key;
        }
    }

    // Iterative sift-down; `end` is the last valid index of the heap.
    static void siftDown(float* a, size_t start, size_t end) {
        size_t root = start;
        while (root * 2 + 1 <= end) {
            size_t child = root * 2 + 1;
            if (child + 1 <= end && a[child] < a[child + 1]) ++child;
            if (a[root] < a[child]) {
                swapFloat(a[root], a[child]);
                root = child;
            } else {
                return;
            }
        }
    }

    void sortFloat(float* a, size_t n) {
        if (!a || n < 2) return;

        if (n <= INSERTION_THRESHOLD) {
            insertionSort(a, n);
            return;
        }

        // Heapify, then repeatedly move the max to the back.
        size_t start = n / 2;
        while (start > 0) {
            --start;
            siftDown(a, start, n - 1);
        }
        size_t end = n - 1;
        while (end > 0) {
            swapFloat(a[0], a[end]);
            --end;
            siftDown(a, 0, end);
        }
    }

    float percentileSorted(const float* sorted, size_t n, float p) {
        if (!sorted || n == 0) return 0.0f;
        if (n == 1) return sorted[0];
        if (p <= 0.0f) return sorted[0];
        if (p >= 1.0f) return sorted[n - 1];

        float pos = p * (float)(n - 1);
        size_t lo = (size_t)pos;
        if (lo >= n - 1) return sorted[n - 1];
        float frac = pos - (float)lo;
        return sorted[lo] + frac * (sorted[lo + 1] - sorted[lo]);
    }

    float medianSorted(const float* sorted, size_t n) {
        return percentileSorted(sorted, n, 0.5f);
    }

    static size_t writeLiteral(const char* text, char* buf, size_t bufLen) {
        size_t n = 0;
        while (text[n]) ++n;
        if (bufLen < n + 1) { buf[0] = '\0'; return 0; }
        for (size_t i = 0; i < n; ++i) buf[i] = text[i];
        buf[n] = '\0';
        return n;
    }

    size_t formatFloat(float value, unsigned char decimals, char* buf, size_t bufLen) {
        if (!buf || bufLen == 0) return 0;

        if (isnan(value)) return writeLiteral("nan", buf, bufLen);
        if (isinf(value)) return writeLiteral(value < 0 ? "-inf" : "inf", buf, bufLen);

        bool negative = (value < 0.0f);
        if (negative) value = -value;
        if (decimals > 9) decimals = 9;

        // Beyond this the integer part no longer fits a uint32_t.
        if (value >= 4294967040.0f) return writeLiteral(negative ? "-ovf" : "ovf", buf, bufLen);

        float integerPart = floorf(value);
        float fractionPart = value - integerPart;

        unsigned long scale = 1;
        for (unsigned char i = 0; i < decimals; ++i) scale *= 10UL;

        unsigned long ip = (unsigned long)integerPart;
        unsigned long fp = (unsigned long)(fractionPart * (float)scale + 0.5f);
        if (fp >= scale) { fp -= scale; ip += 1UL; }   // rounding carried over

        // Render the integer part backwards into a temporary, then emit.
        char digits[11];
        size_t digitCount = 0;
        if (ip == 0) {
            digits[digitCount++] = '0';
        } else {
            while (ip > 0 && digitCount < sizeof(digits)) {
                digits[digitCount++] = (char)('0' + (ip % 10UL));
                ip /= 10UL;
            }
        }

        size_t needed = digitCount + (negative ? 1 : 0)
                      + (decimals > 0 ? (size_t)decimals + 1 : 0) + 1;
        if (bufLen < needed) { buf[0] = '\0'; return 0; }

        size_t pos = 0;
        if (negative) buf[pos++] = '-';
        while (digitCount > 0) buf[pos++] = digits[--digitCount];

        if (decimals > 0) {
            buf[pos++] = '.';
            // Emit the fraction most-significant digit first, zero-padded.
            for (unsigned char i = 0; i < decimals; ++i) {
                scale /= 10UL;
                buf[pos++] = (char)('0' + ((fp / scale) % 10UL));
            }
        }
        buf[pos] = '\0';
        return pos;
    }

    float bessi0(float x) {
        float ax = fabsf(x);
        float y;

        if (ax < 3.75f) {
            y = x / 3.75f;
            y *= y;
            return 1.0f + y * (3.5156229f + y * (3.0899424f + y * (1.2067492f
                 + y * (0.2659732f + y * (0.0360768f + y * 0.0045813f)))));
        }

        y = 3.75f / ax;
        return (expf(ax) / sqrtf(ax)) * (0.39894228f + y * (0.01328592f
             + y * (0.00225319f + y * (-0.00157565f + y * (0.00916281f
             + y * (-0.02057706f + y * (0.02635537f + y * (-0.01647633f
             + y * 0.00392377f))))))));
    }

}
