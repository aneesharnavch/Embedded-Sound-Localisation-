# microdsp

microdsp (micro digital signal processing) is a lightweight signal processing
library made for resource-constrained signal processing on microcontrollers. It
works on fixed-size buffers you already have, or on live sample streams through a
set of sliding-window classes. Refer to examples for detailed instructions on
implementation, and refer to the documentation for further information.

It uses no C++ standard library containers, so it runs on 8-bit AVR (Uno, Nano,
Mega) as well as on 32-bit targets (ESP32, ESP8266, SAMD, STM32, RP2040, Teensy).
The FFT and the FIR path allocate nothing at all.

```c++
#include <microdsp.h>

MicroDSP dsp;

void setup() {
  Serial.begin(9600);

  float data[] = {1.0, 2.0, 3.0, 4.0, 100.0, 6.0, 7.0, 8.0};
  size_t len = 8;

  Serial.println(dsp.mean(data, len));
  Serial.println(dsp.isIQROutlier(100.0, data, len) ? "spike!" : "clean");

  dsp.medianFilter(data, len, 3);      // the 100.0 is gone
}

void loop() {}
```

# Installation

**Library Manager**

In the Arduino IDE, open Tools > Manage Libraries, search for `microdsp`, and
click Install.

**Manual**

Download this repository and drop it into your `libraries` folder
(`Documents/Arduino/libraries/microdsp`), then restart the IDE.

**arduino-cli**

```
arduino-cli lib install microdsp
```

Then `#include <microdsp.h>`. Examples appear under File > Examples > microdsp.

# Features Overview

**Statistics**

- Arithmetic Mean
- Standard Deviation (population and sample)
- Variance
- Minimum, Maximum and RMS
- Median and Interpolated Percentiles
- Median Absolute Deviation
- Outlier Detection:
  - Z-score
  - Modified Z-score
  - Interquartile Range (IQR)
  - Median Absolute Deviation (MAD)

**Calculus**

- Numerical derivatives (allocating and allocation-free)
- Definite integrals (rectangle and trapezoidal)
- Cumulative integration
- Volume integration over a flat 3-D grid

**Filtering**

- Moving Average filter (causal and centred)
- Median filter
- Gaussian filter
- Finite Impulse Response (FIR) filter
- Kaiser-windowed FIR design
- Frequency-sampling FIR design
- Adaptive LMS and multi-tap NLMS filters
- Wiener filter

**Transforms**

- Fast Fourier Transform (FFT)
- Inverse FFT (IFFT)
- Magnitude and dominant-frequency estimation
- Hann, Hamming and Blackman windows
- Laplace Transform (numerical implementation)

**Resource Management**

- Real free-RAM measurement
- Guarded buffer allocation
- Cooperative CPU duty-cycle throttling

**Data Export**

- Serial output
- CSV output (per line or single row)
- JSON output
- XOR obfuscation

**Real-Time Support**

Statistics, the moving average, median and Gaussian filters, and the FFT can all
operate on sliding-window data for streaming applications.

## Resource Management and Export

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

Serial.println(dsp.freeMemory());
```

Throttling is cooperative, so the work has to be bracketed for the library to
measure it.

```c++
if (dsp.shouldProcess()) {
    dsp.beginWork();
    dsp.fft(real, imag, 64);
    dsp.endWork();
}
```

**Serial Export**

```c++
dsp.exportToSerial(data, len, "Label");
```

Prints CSV data, optionally with label, to UART or USB for data logging. Can be
run through the custom decoder to obtain it in CSV form. (Done via python script
in main repository.)

```
python export_decoder.py --port COM3 --out data.csv
python export_decoder.py --input capture.txt --out data.csv
python export_decoder.py --input capture.txt --xor-key 0x5A --out data.csv
```

The decoder auto-detects JSON, single-row CSV, one-value-per-line CSV and XOR hex
output, and writes one CSV column per series it finds.

*Note: `exportObfuscatedXOR` is obfuscation, NOT encryption. A one-byte XOR key is
recovered from a handful of samples. Do not use it to protect anything that
matters.*

## Real-Time Windowed Operations

The real-time classes hold a fixed ring buffer allocated once at construction and
compute outputs as new samples arrive, so `update()` allocates nothing and old
samples are overwritten in place rather than shifted down.

```c++
dspRealTime::RealTimeStats stats(16);      // construct ONCE, not in loop()

void loop() {
    stats.update(analogRead(A0) * (5.0 / 1023.0));
    Serial.println(stats.getMean());
    if (stats.isZScoreOutlier(3.0)) Serial.println("spike");
}
```

## Data Types and Constraints

**Data Arrays**

Input and output arrays must be floating point unless specified otherwise.

**FFT Lengths**

`fft`, `ifft` and `RealTimeFFT` require a power-of-two length (16, 32, 64, and so
on). Any other length returns `false`, or reports `ok() == false`, rather than
producing wrong numbers.

**Return Values**

In-place filters and transforms return `bool`. A `false` return means the
arguments were rejected — a null pointer, a zero length, a sigma of zero or less,
or a failed scratch allocation — and the array was left untouched. Worth checking
on a 2 KB part.

**Buffer Ownership**

`derivative()` returns memory you own; release it with `dsp.freeBuffer()`. Or use
`derivativeInto()`, which writes into a buffer you supply and allocates nothing.

**Streaming Objects**

Construct them once, as globals, statics or members, and call `update()` on the
stored object. Building one inside `loop()` creates a fresh empty window every
iteration, so it never accumulates any history. Check `ok()` after construction.

**Filter Timing**

`movingAverageFilter` is causal and lags the input by about half a window.
`medianFilter`, `gaussianFilter` and `movingAverageFilterCentered` are centred and
stay time-aligned. Mixing the two kinds misaligns signals against each other.

**Memory**

The streaming classes allocate `windowSize` floats once, with the median filter
and `RealTimeFFT` needing a little more for scratch and spectrum arrays.
`medianFilter` and `gaussianFilter` allocate window-sized scratch for the duration
of the call. `fft`, `ifft` and `applyFIR` allocate nothing.

## Examples

Grouped under File > Examples > microdsp.

**Stats**

- Mean
- StdDev

**Outliers**

- IsZScoreOutlier
- IsModifiedZScoreOutlier
- IsMADOutlier
- IsIQROutlier

**Calculus**

- Derivative
- Integral
- CumulativeIntegral

**Filters**

- MovingAverageFilter
- MedianFilter
- GaussianFilter
- ApplyFIR
- DesignKaiserFIR
- FrequencySamplingFIR
- AdaptiveFilter
- AdaptiveFilterNLMS
- WienerFilter

**Transforms**

- FFT
- IFFT
- SpectrumWithWindow
- LaplaceTransform

**RealTime**

- RealTimeStats
- RealTimeProcessing
- RealTimeFFT

**ResourceManagement**

- SetComputeLimit
- SetAvailableMemory
- MemoryAndLoad

**Exporting**

- ExportToSerial
- ExportJSON

## Tests

The numerical core has no Arduino dependency and is tested on the host.

```
./test/run_tests.sh          # or test\run_tests.bat on Windows
```

CI compiles every example for Uno, Mega, ESP32 and Nano 33 IoT, runs this suite,
and checks the library metadata with arduino-lint.

## Documentation

[Documentation.md](Documentation.md) covers the mathematics behind each function,
the full API reference, and the algorithm choices.

Upgrading from 1.x? See [CHANGELOG.md](CHANGELOG.md). Version 2.0.0 changes
several signatures.

## Example Applications

- Smoothing and denoising sensor data for robotics
- Real-time frequency analysis of sampled audio or vibration
- Feature extraction for machine learning on embedded platforms
- Outlier and anomaly detection in physical systems
- Basic calculus operations (velocity/acceleration from position, etc.)

## License

microdsp is released under the MIT License.
