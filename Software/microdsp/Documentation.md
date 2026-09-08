# microdsp Documentation

Reference for the mathematics behind each function, the API, and the algorithm
choices made to keep everything running on an 8-bit microcontroller.

Every function is reachable two ways: through the `MicroDSP` facade
(`dsp.mean(...)`) or through the namespace it belongs to (`dspStats::mean(...)`).
The namespaces expose slightly more than the facade does.

# Conventions

**Return Values**

Functions that transform a buffer in place return `bool`. A `false` return means
the call was rejected and the data was left untouched. Causes are a null pointer,
a zero length, a zero window size, a sigma of zero or less, an FFT length that is
not a power of two, or a failed scratch allocation.

**Degenerate Input**

Functions returning a `float` return `0.0` for empty or null input rather than
NaN. Predicates return `false`.

**Lengths**

All lengths are `size_t`. On AVR that is 16 bits, so an array cannot exceed 65535
elements, and the buffer manager rejects any request whose byte count would
overflow.

**Precision**

Everything is single-precision `float`. On AVR `double` is also 32 bits, so there
is no wider type to fall back on. The algorithms are chosen to stay accurate
within `float` rather than to rely on `double`.

**Constants**

Use `DSP_PI` and `DSP_TWO_PI`. `M_PI` is a POSIX extension and does not exist
under a strict-ANSI compiler, so the library never relies on it.

# Resource Management and Export

**CPU/Memory Hooks**

Functions to measure real free memory, track CPU load, and skip work when the
board is over budget.

```c++
dsp.begin();                      // start load accounting
dsp.setComputeLimit(40);          // aim to stay under 40% duty cycle
dsp.setFreeMemoryThreshold(256);  // keep 256 bytes back for the stack

if (dsp.canProcess(128 * sizeof(float))) {
    // enough headroom to allocate 128 floats
}
```

Throttling is cooperative, so the work has to be bracketed for the library to
measure it.

```c++
if (dsp.shouldProcess()) {
    dsp.beginWork();
    dsp.fft(real, imag, 64);
    dsp.endWork();
}
Serial.println(dsp.getLoadPercent());
```

**Serial Export**

```c++
dsp.exportToSerial(data, len, "Label");
```

Prints CSV data, optionally with a label, to UART or USB for data logging. Can be
run through the custom decoder to obtain it in CSV form. (Done via python script
in main repository.)

`exportRowToSerial` prints a single comma-separated line, and
`exportJSONToSerial` prints a JSON object. The decoder reads all of them.

**Examples for Implementation**

For more detailed examples, check out the examples folder.

# Real-Time Windowed Operations

Statistics, the moving average, median and Gaussian filters, and the FFT are all
available in streaming (sliding window) mode for live sensor or microphone data.

Each class owns one ring buffer allocated in its constructor, so `update()`
allocates nothing and old samples are overwritten in place rather than shifted
down.

Three rules apply to all of them.

- Construct the object once, as a global, a static or a member, and call
  `update()` on that stored object. Building one inside `loop()` creates a fresh
  empty window every iteration and it never accumulates history.
- Check `ok()` after construction. It is `false` if the window size was zero, if
  sigma was zero or less, if `RealTimeFFT` was given a non-power-of-two size, or
  if the allocation failed. An object that is not `ok()` is inert: `update()`
  returns its input unchanged and the accessors return zero.
- Window size must be at least 1, and a power of two for `RealTimeFFT`.

All of them are copyable, with deep-copied buffers.

# Full Feature Reference

## 1. Arithmetic Mean

**Mathematical Definition**

$$
\mu = \frac{1}{n} \sum_{i=1}^{n} x_i
$$

**Microcontroller Implementation**

Iterates through the array, sums all values, then divides by the length. A length
of zero returns 0.0 instead of dividing by zero.

```c++
float mean = dsp.mean(data, len);
```

## 2. Standard Deviation and Variance

**Mathematical Definition**

Population form, with divisor $n$:

$$
\mu = \frac{1}{n} \sum_{i=1}^{n} x_i \qquad
\sigma = \sqrt{ \frac{1}{n} \sum_{i=1}^{n} (x_i - \mu)^2 }
$$

Sample form, with divisor $n-1$ (Bessel's correction):

$$
s = \sqrt{ \frac{1}{n-1} \sum_{i=1}^{n} (x_i - \mu)^2 }
$$

**Microcontroller Implementation**

First pass: find the mean as above. Second pass: subtract the mean, square the
result, sum, divide, and take the square root.

```c++
float sd     = dsp.stdDev(data, len);        // divisor n
float sSd    = dsp.sampleStdDev(data, len);  // divisor n-1
float var    = dsp.variance(data, len);
```

Two passes are used deliberately. The one-pass identity

$$
\sigma^2 = E[x^2] - (E[x])^2
$$

is algebraically equivalent but numerically unusable in `float`. Both terms are
large and nearly equal, so their difference loses every significant digit, can go
negative, and then the square root returns NaN. For four samples near $10^8$
differing by 1.0 the one-pass form returns values in the thousands where the
answer is about 0.5.

The remaining limit is `float` itself. A spread finer than the spacing between
the values being averaged cannot be resolved by any single-precision algorithm;
near $10^8$ that spacing is about 8.

*Note: use the population form when the array is the whole population, and the
sample form when it is a sample drawn from something larger.*

## 3. Minimum, Maximum and RMS

**Mathematical Definition**

$$
x_{\min} = \min_i x_i \qquad
x_{\max} = \max_i x_i \qquad
x_{\mathrm{rms}} = \sqrt{ \frac{1}{n} \sum_{i=1}^{n} x_i^2 }
$$

**Microcontroller Implementation**

Single pass each, no allocation.

```c++
float lo = dsp.minimum(data, len);
float hi = dsp.maximum(data, len);
float r  = dsp.rms(data, len);
```

## 4. Median and Percentiles

**Mathematical Definition**

For a sorted array and $p \in [0,1]$:

$$
\text{pos} = p\,(n-1) \qquad
P = x_{\lfloor \text{pos} \rfloor} +
    (\text{pos} - \lfloor \text{pos} \rfloor)
    \left( x_{\lfloor \text{pos} \rfloor + 1} - x_{\lfloor \text{pos} \rfloor} \right)
$$

**Microcontroller Implementation**

- Copy the array, then sort it.
- Index it with linear interpolation as above.

This matches the conventional (numpy-default) definition, so `percentile(0.5)`
averages the middle two values for even $n$. Quartiles are `percentile(0.25)` and
`percentile(0.75)`.

```c++
float med = dsp.median(data, len);
float q1  = dsp.percentile(data, len, 0.25);
float q3  = dsp.percentile(data, len, 0.75);
```

Sorting is insertion sort up to 16 elements and heapsort above that. Heapsort is
$O(n \log n)$ in the worst case, iterative, and needs no scratch memory beyond
the copy, which matters when the stack is 2 KB.

*Note: these functions allocate `len` floats internally and return 0.0 if that
allocation fails.*

## 5. Median Absolute Deviation

**Mathematical Definition**

$$
\mathrm{MAD} = \mathrm{median}\left( |x_i - \tilde{x}| \right)
$$

where $\tilde{x}$ is the median of the array.

**Microcontroller Implementation**

- Sort a copy of the array to find the median.
- Overwrite that same buffer with the absolute deviations from the median.
- Re-sort and take the median again.

Reusing one buffer for both passes halves the memory needed.

```c++
float mad = dspStats::medianAbsoluteDeviation(data, len);
```

## 6. Z-score Outlier Detection

**Mathematical Definition**

$$
z = \frac{x - \mu}{\sigma}
$$

with $x$ flagged when $|z| > \text{threshold}$. The default threshold is 3.0.

**Microcontroller Implementation**

Compute mean and standard deviation using the algorithms above, then compare.

```c++
bool spike = dsp.isZScoreOutlier(value, data, len, 3.0);
```

Both $\mu$ and $\sigma$ are themselves pulled around by the outliers being
hunted, so prefer the median-based tests below when that matters.

*Note: constant data has $\sigma = 0$, which leaves $z$ undefined. The test
returns `false` rather than dividing by zero.*

## 7. Modified Z-score Outlier Detection

**Mathematical Definition**

$$
M_z = 0.6745 \frac{x_i - \text{median}}{\mathrm{MAD}}
$$

where MAD is *Median Absolute Deviation*. The default threshold is 3.5.

**Microcontroller Implementation**

- Sort the array to find the median.
- Compute MAD as the median of $|x_i - \text{median}|$.
- Scale and compare against the threshold.

```c++
bool spike = dsp.isModifiedZScoreOutlier(value, data, len, 3.5);
```

The constant 0.6745 is the 0.75 quantile of the standard normal, which makes MAD
a consistent estimator of $\sigma$ for normally distributed data.

## 8. MAD Outlier Detection

**Mathematical Definition**

$$
\frac{|x - \text{median}|}{\mathrm{MAD}} > \text{threshold}
$$

**Microcontroller Implementation**

The same robust scale estimate as section 7, without the 0.6745 constant. At an
equal threshold this test is therefore slightly more permissive. Pick one of the
two and stay with it.

```c++
bool spike = dsp.isMADOutlier(value, data, len, 3.5);
```

## 9. The Zero-Spread Cases

Two situations leave the median-based statistics undefined, and both are handled
explicitly rather than dividing by zero.

**Constant Data**

$\sigma$ or MAD is zero, so the statistic has no meaning and all four outlier
tests return `false`.

**Masking**

MAD is exactly zero whenever more than half the window holds one value, for
instance seven samples of 10 and one of 1000. That hides the very outlier being
looked for. Following Iglewicz and Hoaglin, the median-based tests fall back to
the mean absolute deviation:

$$
M_z = 0.7979 \frac{x_i - \text{median}}{\mathrm{MeanAD}} \qquad
\mathrm{MeanAD} = \frac{1}{n} \sum_{i=1}^{n} |x_i - \text{median}|
$$

where $0.7979 = \sqrt{2/\pi}$ is the matching consistency constant. Only when
both estimates are zero, meaning genuinely constant data, does the test give up.

## 10. IQR (Interquartile Range) Outlier Detection

**Mathematical Definition**

$$
\mathrm{IQR} = Q_3 - Q_1
$$

$$
x\ \text{is an outlier if}\ x < Q_1 - m\,\mathrm{IQR}\ \text{or}\ x > Q_3 + m\,\mathrm{IQR}
$$

where $m$ is a multiplier, typically 1.5.

**Microcontroller Implementation**

- Sort the array and calculate the quartiles with linear interpolation.
- Check $x$ against the criterion above.

```c++
bool spike = dsp.isIQROutlier(value, data, len, 1.5);
```

*Note: needs a length of at least 2.*

## 11. Numerical Derivatives (All Orders)

**Mathematical Definition**

First-order discrete approximation:

$$
f'(x) \approx \frac{f(x+h) - f(x)}{h}
$$

where $h = dt$, the sample interval. Higher orders apply the same difference
repeatedly:

$$
f^{(n)}(x) \approx \frac{f^{(n-1)}(x+h) - f^{(n-1)}(x)}{h}
$$

**Microcontroller Implementation**

Two forms are provided. The first allocates the result and hands ownership to the
caller:

```c++
size_t outLen;
float* d = dsp.derivative(data, len, dt, 1, outLen);
if (d) {
    // ... use d ...
    dsp.freeBuffer(d);        // required, or the memory leaks
}
```

The second writes into a buffer already owned by the caller and allocates
nothing, which is preferable on a small board:

```c++
float out[LEN - 1];
size_t n = dsp.derivativeInto(data, len, dt, 1, out);
```

*Note: array length decreases by one for each derivative order, so
`outLen = len - order`. A `dt` of zero is rejected, since it would fill the
result with infinities, as is an order greater than or equal to the length.*

## 12. Numerical Integration

**Mathematical Definition**

Rectangle (left Riemann) rule:

$$
\int_a^b f(x)\,dx \approx \Delta x \sum_{i=0}^{n-1} f(x_i)
$$

Trapezoidal rule:

$$
\int_a^b f(x)\,dx \approx \Delta x
\left( \frac{f_0}{2} + f_1 + \cdots + f_{n-2} + \frac{f_{n-1}}{2} \right)
$$

**Microcontroller Implementation**

```c++
float area  = dsp.integral(data, len, dx);            // rectangle
float area2 = dsp.integralTrapezoid(data, len, dx);   // trapezoid
```

The trapezoidal rule is second-order accurate and exact for a straight line, so
it is the better estimate from the same samples. The rectangle rule is kept
because it is what 1.x computed.

**Cumulative Integration**

For a running total, such as position from velocity, `cumulativeIntegral` fills
an array trapezoidally with `out[0] = 0`. The output may alias the input.

```c++
float position[LEN];
dsp.cumulativeIntegral(velocity, len, dt, position);
```

**Volume Integration**

$$
\iiint f\,dx\,dy\,dz \approx \Delta x \Delta y \Delta z \sum_{i}\sum_{j}\sum_{k} f_{ijk}
$$

`tripleIntegral` takes a flat, contiguous grid in x-major order, with element
$(i,j,k)$ at `((i * yLen) + j) * zLen + k`.

```c++
float v = dspCalculus::tripleIntegral(grid, xLen, yLen, zLen, dx, dy, dz);
```

## 13. Moving Average Filter

**Mathematical Definition**

Causal, looking only backwards:

$$
y_i = \frac{1}{N} \sum_{j=0}^{N-1} x_{i-j}
$$

Centred, looking both ways:

$$
y_i = \frac{1}{N} \sum_{j=-k}^{k} x_{i+j} \qquad k = \lfloor N/2 \rfloor
$$

where $N$ is the window size.

**Microcontroller Implementation**

For each output, sum the samples in the window and divide by the count.

```c++
dsp.movingAverageFilter(data, len, 5);          // causal
dsp.movingAverageFilterCentered(data, len, 5);  // zero phase
```

The causal version runs in $O(n)$ using a sliding sum with a window-sized ring
buffer. The centred version keeps a delay line of the last $2k+1$ original
samples and emits output $i$ while reading input $i+k$, so filtering in place
never destroys a sample a later output still needs. Both need only
$O(\text{windowSize})$ memory rather than a full copy of the array.

*Note: the two differ in timing. The causal version delays the signal by roughly
$(N-1)/2$ samples; feed it an impulse at index 3 with $N = 3$ and the energy
comes out at 3, 4 and 5. The median and Gaussian filters are centred, so mixing
`movingAverageFilter` with them misaligns the results against each other. Use the
centred version when filter outputs are to be compared.*

*Note: an even window size has no true centre tap and is rounded up to the next
odd length by the centred filters.*

## 14. Median Filter

**Mathematical Definition**

$$
y_i = \text{median}(x_{i-k}, \ldots, x_i, \ldots, x_{i+k})
$$

where the window size is $2k+1$.

**Microcontroller Implementation**

- Gather the window around each sample from the delay line described in section 13.
- Sort it and take the middle value.

```c++
dsp.medianFilter(data, len, 3);
```

Removes impulsive noise while leaving genuine step edges intact, which a mean
filter cannot do. Windows are truncated at the array edges.

## 15. Gaussian Filter

**Mathematical Definition**

$$
y_i = \sum_{j=-R}^{R} x_{i+j} \cdot G(j) \qquad
G(j) = \exp\left( -\frac{j^2}{2\sigma^2} \right) \qquad
R = \lceil 3\sigma \rceil
$$

**Microcontroller Implementation**

- Precompute the kernel $G(j)$ for $j$ in $[-R, R]$ and normalise it by its own
  sum, which subsumes the usual $1/\sqrt{2\pi\sigma^2}$ factor.
- For each output, multiply the window by the kernel and sum.
- Renormalise over only the taps that landed inside the array.

$$
y_i = \frac{\sum_{j \in \text{valid}} x_{i+j} G(j)}{\sum_{j \in \text{valid}} G(j)}
$$

```c++
dsp.gaussianFilter(data, len, 1.5);
```

The renormalisation is what keeps the first and last $R$ samples from being
pulled towards zero. A constant input comes back unchanged everywhere, edges
included.

*Note: sigma must be greater than zero. Anything else is rejected and the data is
left untouched.*

## 16. FIR Filter (Finite Impulse Response)

**Mathematical Definition**

$$
y_i = \sum_{j=0}^{M-1} x_{i-j} \cdot c_j
$$

**Microcontroller Implementation**

Multiply the current and previous $M-1$ samples by the coefficients and sum for
each output. Samples before the start of the array are treated as zero, so the
first $M-1$ outputs ramp up.

```c++
dsp.applyFIR(data, len, coeffs, coeffLen);
```

The loop walks backwards, from the last sample to the first. Output $i$ depends
only on inputs at indices up to $i$, and going backwards means those are all
still original values, so the convolution runs in place with no scratch memory at
all. This is the cheapest routine in the library.

## 17. Kaiser Window and Lowpass FIR Design

**Mathematical Definition**

Kaiser window:

$$
w[n] = \frac{I_0\left( \beta \sqrt{1 - \left( \frac{2n}{N-1} - 1 \right)^2} \right)}{I_0(\beta)}
$$

where $I_0$ is the zeroth-order modified Bessel function of the first kind.

Ideal lowpass impulse response:

$$
h[m] = \frac{\sin(2\pi f_c m)}{\pi m} \qquad h[0] = 2 f_c
$$

where $m = n - (N-1)/2$.

**Microcontroller Implementation**

- Build the Kaiser window.
- Multiply it by the ideal sinc above.
- Normalise so the taps sum to 1, giving unity gain at DC.

```c++
// 1 kHz sampling, 100 Hz cutoff -> 100/1000 = 0.1
float coeffs[21];
dsp.designKaiserFIR(coeffs, 21, 5.0, 0.1);
dsp.applyFIR(signal, len, coeffs, 21);
```

`cutoffNorm` is the cutoff as a fraction of the sample rate and must lie in
$(0, 0.5)$. A larger `beta` buys deeper stopband attenuation at the cost of a
wider transition band; around 5 is a reasonable default. $I_0$ is evaluated with
an Abramowitz and Stegun polynomial approximation.

A genuine lowpass has negative side lobes and its taps sum to 1. The window on
its own is all-positive and would merely scale the signal, so it is available
separately when that is what is wanted:

```c++
dsp.kaiserWindow(window, 21, 5.0);
```

## 18. Frequency Sampling FIR Design

**Mathematical Definition**

$$
h[n] = \frac{1}{N} \left( H_0 + \sum_{k=1}^{\lfloor N/2 \rfloor} a_k H_k
\cos\left( \frac{2\pi k \left( n - \frac{N-1}{2} \right)}{N} \right) \right)
$$

with $a_k = 2$ except at the Nyquist bin of an even-length filter, where
$a_k = 1$.

**Microcontroller Implementation**

Specify the magnitude wanted at each DFT bin, then take the inverse DFT.

```c++
const size_t TAPS = 17;
float desired[TAPS / 2 + 1];                 // bins 0 .. TAPS/2
for (size_t k = 0; k < TAPS / 2 + 1; k++) desired[k] = (k <= 2) ? 1.0 : 0.0;

float coeffs[TAPS];
dsp.frequencySamplingFIR(coeffs, TAPS, desired);
```

`desiredResponse` holds $\lfloor N/2 \rfloor + 1$ entries covering bins
$0 \ldots \lfloor N/2 \rfloor$, where bin $k$ sits at $k f_s / N$.

Evaluating about the centre tap rather than about $n = 0$ makes the result linear
phase and symmetric, which is what `applyFIR` expects. The Nyquist bin of an
even-length filter has no mirror partner, hence the separate weight.

## 19. Adaptive Filters (LMS and NLMS)

**Mathematical Definition**

Single-tap LMS:

$$
y_i = w\,r_i \qquad e_i = x_i - y_i \qquad w \leftarrow w + \mu\, e_i\, r_i
$$

Multi-tap NLMS:

$$
y_i = \sum_{j=0}^{M-1} w_j\, r_{i-j} \qquad e_i = x_i - y_i
$$

$$
w_j \leftarrow w_j + \frac{\mu\, e_i\, r_{i-j}}{\varepsilon + \sum_j r_{i-j}^2}
$$

**Microcontroller Implementation**

Both are noise cancellers. Supply a `reference` correlated with the interference
but not with the wanted signal. On return, `data` holds the error signal $e$,
which is the input with the correlated component removed, and therefore the
cleaned signal.

```c++
dsp.adaptiveFilter(data, reference, len, 0.05);
```

`w` starts at zero, so the first sample is unfiltered and the filter needs a short
run to converge. A larger `mu` converges faster but overshoots; too large and it
never settles.

A single tap can only scale the reference. When the interference arrives delayed
or filtered, several taps are needed:

```c++
float weights[6] = {0, 0, 0, 0, 0, 0};
dsp.adaptiveFilterFIR(data, reference, len, 0.5, weights, 6);
```

Normalising by reference power makes the usable range of `mu` independent of input
amplitude, so $0 < \mu < 2$ is stable at any scale, and $\varepsilon$ keeps a
silent reference from dividing by zero. `weights` belongs to the caller: it is
updated in place and can be reused across calls to keep adapting between buffers.
Start it zeroed.

*Note: the output is the cleaned signal, not the noise estimate.*

## 20. Wiener Filter

**Mathematical Definition**

$$
y_i = x_i \cdot \frac{\sigma_s^2}{\sigma_s^2 + \sigma_n^2}
$$

**Microcontroller Implementation**

A single attenuation factor from estimates of signal and noise power, applied to
every sample.

```c++
dsp.wienerFilter(data, len, signalVar, noiseVar);
```

*Note: both variances summing to zero would divide by zero, so it is rejected.*

## 21. FFT — Fast Fourier Transform

**Mathematical Definition**

$$
X_k = \sum_{n=0}^{N-1} x_n \cdot e^{-i2\pi kn/N}
$$

**Microcontroller Implementation**

- Reorder the input into bit-reversed index order.
- Run $\log_2 N$ stages of butterflies over it, in place.
- Advance the twiddle factor by complex multiplication rather than recomputing it
  with `cos` and `sin` per butterfly.

```c++
float real[32], imag[32];
for (size_t i = 0; i < 32; i++) { real[i] = signal[i]; imag[i] = 0.0; }

if (!dsp.fft(real, imag, 32)) {
    // length was not a power of two
}
```

The transform is iterative and allocation-free: it works entirely in the caller's
two arrays plus a handful of locals. A textbook recursive radix-2 FFT allocates
temporaries at every level of recursion, which is $O(N \log N)$ allocations for a
single transform and fragments a small heap until it fails. Advancing the twiddle
factor matters too, since four trig calls per butterfly is ruinous on a core with
no FPU.

*Note: the length MUST be a power of two. Any other length returns `false` and
leaves the arrays untouched, rather than silently producing wrong numbers.*

*Note: for real-valued input, set the imaginary array to all zeros. Only bins
$0$ to $N/2$ are then unique.*

## 22. IFFT — Inverse FFT

**Mathematical Definition**

$$
x_n = \frac{1}{N} \sum_{k=0}^{N-1} X_k \cdot e^{i2\pi kn/N}
$$

**Microcontroller Implementation**

Conjugate the input, run the forward FFT, conjugate the output, and scale by
$1/N$.

```c++
dsp.fft(real, imag, N);
dsp.ifft(real, imag, N);        // recovers the original samples
```

Same power-of-two requirement as the forward transform. A round trip recovers the
input to within float rounding error.

## 23. Magnitude and Dominant Frequency

**Mathematical Definition**

$$
|X_k| = \sqrt{ \mathrm{Re}(X_k)^2 + \mathrm{Im}(X_k)^2 }
$$

Parabolic interpolation across the peak and its neighbours:

$$
\delta = \frac{1}{2} \cdot
\frac{|X_{k-1}| - |X_{k+1}|}{|X_{k-1}| - 2|X_k| + |X_{k+1}|} \qquad
f = (k + \delta) \frac{f_s}{N}
$$

**Microcontroller Implementation**

```c++
float magnitude[N];
dsp.fftMagnitude(real, imag, magnitude, N);

float hz = dsp.dominantFrequency(real, imag, N, sampleRate);
```

`dominantBin` returns the largest-magnitude bin in the first half of the spectrum,
skipping DC, since bin 0 is only the mean. `dominantFrequency` then refines that
with the interpolation above. Bin spacing is $f_s/N$, often tens of Hz, so
recovering a fractional bin position is what makes the estimate useful.

## 24. Window Functions

**Mathematical Definition**

$$
w_{\text{Hann}}[n] = 0.5 - 0.5\cos\left( \frac{2\pi n}{N-1} \right)
$$

$$
w_{\text{Hamming}}[n] = 0.54 - 0.46\cos\left( \frac{2\pi n}{N-1} \right)
$$

$$
w_{\text{Blackman}}[n] = 0.42 - 0.5\cos\left( \frac{2\pi n}{N-1} \right)
+ 0.08\cos\left( \frac{4\pi n}{N-1} \right)
$$

**Microcontroller Implementation**

An FFT assumes its buffer repeats forever. If the buffer does not hold a whole
number of cycles, that discontinuity smears energy across every bin, which is
spectral leakage. Tapering the ends first largely removes it.

```c++
float window[N];
dsp.hannWindow(window, N);
dsp.applyWindow(real, window, N);
dsp.fft(real, imag, N);
```

Blackman leaks least but widens the main lobe most. Hann is a good default.

*Note: windowing reduces total energy, so absolute magnitudes shrink. Compare
bins against each other, not against an unwindowed run.*

## 25. Laplace Transform (Numerical)

**Mathematical Definition**

$$
F(s) = \int_{0}^{\infty} f(t)\, e^{-st} \,dt \qquad s = \sigma + i\omega
$$

**Microcontroller Implementation**

Numerically approximate the integral by summing discrete samples at one complex
point $s$:

$$
F(s) \approx \Delta t \sum_{i=0}^{n-1} f(t_i)\, e^{-\sigma t_i}
\left[ \cos(\omega t_i) - i \sin(\omega t_i) \right] \qquad t_i = i\,\Delta t
$$

```c++
// f(t) = e^-t, so F(s) = 1/(s+1); at s = 1 this comes out near 0.5
float outReal, outImag;
dsp.laplaceTransform(signal, len, dt, 1.0, 0.0, outReal, outImag);
```

The result is a single complex number, which is what evaluating a transform means.
Sweep the imaginary part of $s$ to trace a frequency response.

`laplaceIntegrand` writes the un-summed per-sample integrand into two arrays, for
callers that want to accumulate or inspect it themselves.

*Note: pass the sample interval so the integral is scaled correctly.*

## 26. Real-Time Statistics

**API**

```c++
dspRealTime::RealTimeStats stats(16);

stats.update(value);

stats.getMean();    stats.getVariance();   stats.getStdDev();
stats.getMin();     stats.getMax();        stats.getRMS();
stats.getMedian();  stats.latest();
stats.count();      stats.capacity();      stats.full();
stats.reset();      stats.ok();

stats.isZScoreOutlier(3.0);
stats.isModifiedZScoreOutlier(3.5);
stats.isMADOutlier(3.5);
stats.isIQROutlier(1.5);
```

**Microcontroller Implementation**

Statistics use the same two-pass algorithm as section 2, computed over the window
and cached until the next `update()`. Calling `getMean()` and `getStdDev()`
together therefore costs one traversal, not two. A running sum would drift
without bound in a sketch that runs for days; recomputing does not.

All four outlier tests judge `latest()`, the newest sample in the window.

*Note: `getMedian()` and the median-based tests allocate a scratch buffer of
`windowSize` on first use, and return 0.0 or `false` if that fails.*

## 27. Real-Time Filters

**API**

```c++
dspRealTime::RealTimeMovingAverage   average(8);
dspRealTime::RealTimeMedianFilter    median(5);
dspRealTime::RealTimeGaussianFilter  smooth(9, 2.0);

float out = average.update(sample);   // returns the filtered value
```

**Microcontroller Implementation**

Each returns the filtered value for the sample just added.

The Gaussian kernel holds exactly `windowSize` taps centred on $(N-1)/2$, which
is correct for even and odd window sizes alike. While the window is still filling,
the taps in use are renormalised, so a constant input reads back as that constant
from the very first sample and the output stays directly comparable with the other
filters at all times.

## 28. Real-Time FFT

**API**

```c++
dspRealTime::RealTimeFFT spectrum(32);      // power of two

spectrum.update(sample);              // buffer, then transform
spectrum.updateDeferred(sample);      // buffer only
spectrum.transform();                 // recompute from the window
spectrum.isReady();
spectrum.getReal();  spectrum.getImag();  spectrum.size();
spectrum.magnitude(bin);
spectrum.dominantFrequency(sampleRate);
spectrum.setUseHannWindow(true);
```

**Microcontroller Implementation**

`isReady()` becomes true as soon as `windowSize` samples have arrived.

`update()` recomputes the whole transform on every sample, which is
$O(N \log N)$ each time. At a slow sample rate that is fine; otherwise buffer with
`updateDeferred()` and transform once per batch.

```c++
spectrum.updateDeferred(sample);
if (++count >= WINDOW / 2 && spectrum.isReady()) {
    count = 0;
    spectrum.transform();
    Serial.println(spectrum.dominantFrequency(SAMPLE_RATE));
}
```

*Note: the window size MUST be a power of two, or `ok()` reports `false`.*

*Note: `setUseHannWindow(true)` applies a Hann taper before each transform, at the
cost of one extra buffer of `windowSize` floats.*

## 29. Resource Management

**API**

```c++
dspResources::init();                          // MicroDSP::begin()
dspResources::freeMemory();                    // also getAvailableMemory()
dspResources::setAvailableMemory(bytes);       // manual override
dspResources::setFreeMemoryThreshold(bytes);
dspResources::hasSufficientMemory(bytes);      // also canProcess()

dspResources::setComputeLimit(percent);
dspResources::getComputeLimit();
dspResources::beginWork();
dspResources::endWork();
dspResources::getLoadPercent();
dspResources::shouldProcess();
dspResources::checkLoad(fraction);
dspResources::setLoadWindow(microseconds);
```

**Microcontroller Implementation**

`freeMemory()` measures the real figure per architecture.

- AVR: the gap between `__brkval` / `__heap_start` and the stack pointer.
- ESP8266 and ESP32: `ESP.getFreeHeap()`.
- Everything else: the largest block `malloc` will return, found by a bounded
  binary search.

`setFreeMemoryThreshold()`, 256 bytes by default, is a reserve kept back for the
stack. `hasSufficientMemory()` will not approve a request that eats into it.
`setAvailableMemory()` only matters on platforms where none of the above works.

CPU throttling is cooperative, since the library cannot preempt the sketch. Load
is averaged over a trailing window, 1 second by default, and the accounting uses
unsigned `micros()` differences so it stays correct across the roughly 71 minute
rollover. `checkLoad(0.5)` tests against half the configured limit, and a limit of
100, the default, never throttles.

## 30. Data Export

**API**

```c++
dspDataIO::exportCSV(data, len, "label");            // one value per line
dspDataIO::exportCSVRow(data, len, "label", 4);      // one comma-separated line
dspDataIO::exportJSON(data, len, "label", 6);        // JSON object
dspDataIO::annotateAndExport(data, len, "note");
dspDataIO::exportObfuscatedXOR(data, len, 0x5A);
```

Each also takes an explicit `Stream&` as its first argument, so anything works,
not just Serial.

```c++
dspDataIO::exportCSVRow(Serial1, data, len, "sensor");
```

**Microcontroller Implementation**

None of these build an Arduino `String`. They stream a character at a time.
Appending to a `String` in a loop reallocates on nearly every sample and fragments
the heap, which on a 2 KB part eventually fails outright.

Floats are formatted by `dspCompat::formatFloat`, a small fixed-point formatter,
because neither alternative is portable. avr-libc's `printf` omits `%f` support
unless the sketch links extra flags, and `String(float, uint8_t)` is ambiguous on
the ESP32 core.

`dspExport::floatArrayToCompactString` still returns a `String` for callers that
need the text in RAM, but it reserves the whole buffer once up front.

**XOR Obfuscation**

`exportObfuscatedXOR` XORs each float's raw bytes with a one-byte key and emits
zero-padded uppercase hex pairs. The zero padding matters: a byte below `0x10`
printed without it cannot be parsed back unambiguously.

*Note: this is obfuscation, NOT encryption. A one-byte XOR key is recovered from a
handful of samples. Do not use it to protect anything that matters.*

Bytes go out in the MCU's native float order, little-endian on AVR, ESP and ARM,
which is what the decoder assumes. `exportEncrypted` is kept as a deprecated
alias.

**Decoding**

```
python export_decoder.py --port COM3 --out data.csv
python export_decoder.py --input capture.txt --out data.csv
python export_decoder.py --input capture.txt --xor-key 0x5A --out data.csv
```

Auto-detects JSON, single-row CSV, one-value-per-line CSV and XOR hex, and writes
one CSV column per series it finds.

## 31. Buffer Management

**API**

```c++
dspDataManager::allocateBuffer(len);
dspDataManager::allocateZeroedBuffer(len);
dspDataManager::releaseBuffer(buffer);
dspDataManager::clearBuffer(buffer, len);
dspDataManager::fillBufferWithValue(buffer, len, value);
dspDataManager::copyBuffer(src, dst, len);
dspDataManager::canAllocate(len);
dspDataManager::isSafeToAllocate(bytes);
```

**Microcontroller Implementation**

`allocateBuffer` consults `dspResources::hasSufficientMemory` first, so a request
that would leave the stack no headroom fails cleanly instead of returning a
pointer that works right up until the stack meets the heap. It also rejects
lengths whose byte count would overflow a 16-bit `size_t`.

```c++
float* buf = dspDataManager::allocateZeroedBuffer(64);
if (buf) {
    // ...
    dspDataManager::releaseBuffer(buf);
}
```

# Memory and Compute Cost

$n$ is the array length and $N$ the window or tap count.

**No Extra Memory**

- `applyFIR` — $O(n \cdot N)$
- `fft`, `ifft` — $O(n \log n)$
- `derivativeInto` — $O(n \cdot \text{order})$
- `mean`, `variance`, `stdDev`, `minimum`, `maximum`, `rms` — $O(n)$
- `adaptiveFilter` — $O(n)$
- `adaptiveFilterFIR` — $O(n \cdot N)$, weights belong to the caller
- `laplaceTransform`, `integralTrapezoid`, `cumulativeIntegral` — $O(n)$
- `designKaiserFIR`, `frequencySamplingFIR` — $O(N^2)$

**Window-Sized Scratch**

- `movingAverage` — $O(n)$ time, $N$ floats
- `movingAverageCentered` — $O(n \cdot N)$ time, $2N$ floats
- `medianFilter` — $O(n \cdot N \log N)$ time, $2N$ floats
- `gaussianFilter` — $O(n \cdot N)$ time, $2N$ floats

**Array-Sized Scratch**

- `median`, `percentile`, `medianAbsoluteDeviation`, all outlier tests —
  $O(n \log n)$ time, $n$ floats
- `nthDerivative` — $O(n \cdot \text{order})$ time, $n$ plus $n - \text{order}$ floats

**Streaming Classes**

Per `update()` call:

- `RealTimeStats` — $O(1)$; `getMean` and `getStdDev` are $O(N)$ and cached;
  `getMedian` and the outlier tests are $O(N \log N)$
- `RealTimeMovingAverage` — $O(N)$
- `RealTimeMedianFilter` — $O(N \log N)$
- `RealTimeGaussianFilter` — $O(N)$
- `RealTimeFFT` — $O(N \log N)$

Allocated once at construction:

- `RealTimeStats`, `RealTimeMovingAverage` — $N$ floats
- `RealTimeMedianFilter`, `RealTimeGaussianFilter` — $2N$ floats
- `RealTimeFFT` — $3N$ floats, or $4N$ with Hann windowing enabled
