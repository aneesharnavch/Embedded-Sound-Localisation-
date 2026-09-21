# Measured-data results and forensics

**Owner:** data-analysis track. **Generated:** 2026-07-27.
**Sources:** `validation/analyze_real.py` (all numbers), `validation/realdata_common.py`
(loaders and figure style), `validation/realdata_run.log` (full transcript, 944 lines),
`validation/figs/fig_real_*.png` (nine figures, 300 dpi).

Every number in this file is reproducible by running

```
py -3.14 validation/analyze_real.py
```

which reads only files already in the repository, uses a fixed RNG seed (7), and writes its
entire output to `validation/realdata_run.log`. Nothing here is simulated except where a
section says so explicitly.

**Scope note.** This file covers the MEASURED data only. The simulation harness
(`doa_benchmark.py`, `reverb_robustness.py`, `ablation.py`, their logs and their `fig_*`
figures) is owned by the re-baseline track. The single place where this file depends on a
simulation number is Figure 9, which is flagged there.

---

## 1. Data forensics

### 1.1 Critical question 1 — what is the acquisition sample rate?

**Answer: fs = 999.988 Hz. Nyquist = 500.0 Hz. Every excitation in the calibration campaign
is aliased, by a factor of 2 to 40.**

Two independent methods agree to 9 parts per million.

**Method A — the logger's own time column.** Over all 105 excitation recordings:

| Quantity | Value |
|---|---|
| Samples per file | 29 999 – 30 002 (median 30 001) |
| Record duration | 29.999 – 30.002 s |
| Mean sample interval | 1.000003 ms (sd across files 0.017 µs) |
| Median sample interval | 0.997305 ms |
| Within-file sd of the interval | 279 µs (median over files) |
| Intervals exactly equal to zero | 2.41 % of samples |
| Intervals > 1.5 ms | 2.67 % of samples |
| Largest single gap | 77.1 ms |
| **Implied rate** | **999.9965 Hz** |

**Method B — the alias test (decisive).** A tone at `f0` sampled at `fs < 2·f0` folds to
`f_alias = |f0 − k·fs|`. Writing the true sample interval as `T = (1 + δ)/1000` s, and noting
that every excitation frequency is an exact integer multiple of 1 kHz, the model collapses to
a one-parameter prediction:

```
f_alias = δ · f0
```

The observed low-frequency line must be strictly *proportional* to the excitation frequency,
with the same δ for every waveform and every distance. Nothing except undersampling produces
that. Measured (sine excitations, per-recording, `realdata_run.log` §1):

| Excitation | n resolved | Median observed line (Hz) | Implied δ (ppm) | Range (ppm) |
|---|---|---|---|---|
| 1 kHz | – | 0.0122 predicted | – | alias below the 0.0333 Hz record-length resolution |
| 5 kHz | 7 | 0.0534 | 10.68 | 9.16 – 12.97 |
| 10 kHz | 7 | 0.1144 | 11.44 | 11.06 – 12.59 |
| 15 kHz | 5 | 0.1717 | 11.44 | 10.68 – 12.46 |
| 20 kHz | 2 | 0.2384 | 11.92 | 11.63 – 12.21 |

Pooled over the sine set: **δ = 11.444 ppm, sd 0.890 ppm, n = 21 → fs = 999.98856 Hz.**
A global one-parameter matched scan over all 84 recordings at 5 kHz and above (summing each
recording's normalised spectral amplitude at its own predicted alias frequency) peaks at
**δ = 12.195 ppm → fs = 999.98781 Hz**, with a peak-to-median scan ratio of 16.3.

The square and triangle recordings at 15 and 20 kHz sit near 7 ppm rather than 11.4, because
those waveforms fold their odd harmonics onto separate lines while their fundamental is weak.
They are reported but excluded from the point estimate.

**What this destroys and what it leaves.** All *frequency* information in the calibration set
is destroyed: a 5 kHz excitation is recorded as a 0.061 Hz waveform, a 20 kHz excitation as a
0.244 Hz waveform. Folding preserves *amplitude*, so a level reading would in principle
survive — but §3.3 shows it does not survive in practice, for the separate reason that the
drive level was not held constant.

**Corollary — the time column is a host artefact, not the sample clock.** The within-file
scatter of the time column is 279 µs RMS. If the converter had really been clocked that
irregularly, a 5 kHz carrier (period 200 µs) would accumulate 8.8 rad of phase error between
consecutive samples and no coherent alias line could exist. The alias lines are in fact highly
coherent over the 30 s record (median peak-to-background 177). Combined with the 2.4 %
duplicate timestamps and the 77 ms gaps, the conclusion is that the conversion loop is
uniformly clocked and the `Time (ms)` column records when the *host* received a serial line.
**Use the sample index, not the time column.**

**Consequence for TDOA — stated precisely.** With the array as configured in
`doa_benchmark.py` (equilateral triangle, circum-radius R = 5 cm, so microphone spacing
R·√3 = 8.66 cm):

| Quantity | Value |
|---|---|
| Sampling period | 1000.0 µs |
| Largest inter-microphone delay, 8.66 cm spacing | 252.5 µs |
| Largest delay if the spacing is instead 5.00 cm | 145.8 µs |
| Whole 360° azimuth range, 8.66 cm | ±0.2525 samples |
| Whole 360° azimuth range, 5.00 cm | ±0.1458 samples |

Being sub-sample is *not by itself* fatal — interpolated cross-correlation routinely resolves
a fraction of a sample. The argument turns on the aliasing:

1. Sub-sample delay estimation is interpolation, which is only valid for a signal band-limited
   below Nyquist. These recordings are not: 5–20 kHz reaches the converter at full amplitude
   with no anti-alias filter.
2. **Aliasing corrupts delay worse than it corrupts spectrum.** A component at `f0` delayed by
   τ carries phase `−2π f0 τ`. Folding moves it to `f_a` but does *not* change its phase, so it
   enters the cross-spectrum at `f_a` carrying a phase belonging to `f0` — an apparent group
   delay inflated by `f0/f_a`. For 20 kHz at the array's maximum delay the true phase is
   31.7 rad (5.05 whole wraps), whereas an honest in-band component at 0.244 Hz would carry
   3.9 × 10⁻⁴ rad. Every folded component injects a several-cycle phase error, and GCC-PHAT —
   which fits a linear phase ramp and gives every bin unit weight — has its phase randomised.
3. **The fix is therefore an anti-alias filter and a hardware-timed conversion clock, not
   merely a faster converter.** With those in place, 1 kHz sampling of a genuinely band-limited
   source would give a Cramér–Rao delay bound of tens of microseconds — marginal but not
   absurd. Without them, no sample rate helps.

> **Section 6 of the paper must not claim hardware TDOA on any data in this repository.**

*Ambiguity flagged for the author:* "5 cm aperture" in `HANDOVER.md` is ambiguous between
circum-radius (giving 8.66 cm spacing, 252.5 µs) and microphone spacing (giving 145.8 µs).
Both are carried through above. This must be replaced with a measured board dimension.

### 1.2 Critical question 2 — are the 30-sample triple-mic clips usable?

**Answer: no. A direction-of-arrival estimate cannot be extracted from them.**

**Acquisition chain.** The 25 clips carry 30 samples × 3 channels, sit on the same
~1266-code DC pedestal as the rest of the hardware, and are stored as plain 12-bit codes
(78.4 % of values are odd, unlike the factor-two-scaled calibration words).

**Per-channel rate, inferred from the noise correlation time.** The clips carry no time
column. The front-end noise is band-limited, so its autocorrelation acts as a clock, and the
60 s idle recordings measure that autocorrelation directly at a known 1 kHz:

| Lag (samples at 1 kHz) | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|---|---|---|
| Idle ρ (mean of 3 mics) | 1.000 | 0.545 | 0.456 | 0.341 | 0.220 | 0.118 | 0.045 | −0.006 | −0.031 |

Lag-1 autocorrelation of the 8 quietest clips (24 channel series):

| Quantity | Value |
|---|---|
| Raw mean | −0.0358 |
| Small-sample bias −1/(N−1), N = 30 | −0.0345 |
| **Bias-corrected** | **−0.0013 ± 0.0320** |
| The 1 kHz idle value | +0.5448 |

The clips' noise is **white**, while the same front end at 1 kHz gives +0.545. Reading the
idle autocorrelation backwards, the clips' 95 % upper bound (+0.061) is first reached at lag 6
of the idle record: **the clips are sampled at roughly 167 Hz per channel or slower**, which is
consistent with a loop that converts three multiplexed channels and writes one spreadsheet row
per set. The inference assumes the two datasets share an analogue noise bandwidth — likely,
given the common DC and common 12-bit grid, but not proved — and it is conservative in the
right direction, since residual source content in the "quiet" clips would only raise their
autocorrelation.

**Resolvability:**

| Assumed fs | Sampling period | Clip duration | 360° range in lag bins | Usable bins |
|---|---|---|---|---|
| 167 Hz (inferred for these clips) | 6000 µs | 180 ms | ±0.0421 | 1 |
| 1000 Hz (calibration rig) | 1000 µs | 30 ms | ±0.2525 | 1 |
| 48 000 Hz (simulation harness) | 20.8 µs | 0.625 ms | ±12.12 | 25 |

Measured cross-correlation peaks over all 75 channel pairs: 73 % at lag 0, 27 % at |lag| ≥ 1,
largest |lag| 18 samples. Every non-zero peak is 4× to 24× larger than any delay the array can
physically produce, so every one of them is noise.

**Cramér–Rao floors** (σ_τ ≥ 1/(β√(2N·SNR)), flat spectrum to Nyquist, N = 30):

| fs | SNR | σ_τ | × the full array delay range | Azimuth sd |
|---|---|---|---|---|
| 167 Hz | 10 dB | 135.05 µs | 0.53 | 32° |
| 167 Hz | 30 dB | 13.50 µs | 0.05 | 3.1° |
| 1 000 Hz | 10 dB | 22.51 µs | 0.09 | 5.1° |
| 1 000 Hz | 30 dB | 2.25 µs | 0.01 | 0.5° |
| 48 000 Hz | 10 dB | 0.47 µs | 0.002 | 0.1° |
| 48 000 Hz | 30 dB | 0.05 µs | 0.000 | 0.0° |

Read these as optimism, not achievement: they assume a properly band-limited source and an
unbiased estimator. The 1 kHz row *looks* usable at ~5°; it is not achievable here, because
there is no anti-alias filter (§1.1).

**Four reasons, honestly weighted:**

1. **Aliasing (decisive).** No anti-alias filter anywhere in the chain. Folded components
   randomise the cross-spectrum phase. No sample rate or estimator repairs this.
2. **Rate.** ~167 Hz per channel; the whole azimuth range is 0.084 of one lag bin and the
   Cramér–Rao azimuth bound is ~32° at 10 dB.
3. **Length.** 30 samples is too few for the sub-sample interpolation the geometry demands,
   even at 48 kHz.
4. **Scorability.** No time base, no stated rate, no azimuth ground truth, no room, no repeats.

**What the clips do establish, and it is real:** the three channels are strongly correlated at
lag 0 (median r = 0.67), the front end shares a common 1266-code DC operating point, and the
per-channel gains match to about 1.2 dB (§3.4). They are a working three-channel capture, not
a localization dataset.

### 1.3 The 25 position labels

Header cell D1 of each workbook. The labels are exactly the 5 × 5 Cartesian product of
x ∈ {−30, −15, 0, 15, 30} cm and y ∈ {−30, −15, 0, 15, 30} cm — every node once, none repeated.
There is no azimuth label, no distance label, no room label and no repeat measurement.

| File | Label | File | Label | File | Label | File | Label | File | Label |
|---|---|---|---|---|---|---|---|---|---|
| sample_1 | (0,15) | sample_6 | (0,−30) | sample_11 | (30,−15) | sample_16 | (−30,15) | sample_21 | (15,−15) |
| sample_2 | (0,−15) | sample_7 | (30,0) | sample_12 | (30,−30) | sample_17 | (−15,−15) | sample_22 | (15,−30) |
| sample_3 | (−15,0) | sample_8 | (−30,0) | sample_13 | (−30,30) | sample_18 | (−15,30) | sample_23 | (15,30) |
| sample_4 | (15,0) | sample_9 | (15,15) | sample_14 | (−30,−15) | sample_19 | (−15,−30) | sample_24 | (30,15) |
| sample_5 | (0,30) | sample_10 | (−15,15) | sample_15 | (−30,−30) | sample_20 | (0,0) | sample_25 | (30,30) |

### 1.4 Dataset inventory, de-duplication and quarantine

**The excitation set is stored three times.** MD5 comparison of every CSV shows
`Distance based sample_s` (105 files), `Waveform based Sample_s` (105 files) and the entire
`Microphone feedback with respect to Frequency and Distance` folder (105 files) are
byte-identical re-organisations of **105 distinct recordings**, all three copies present for
every one. The apparent 239 + 126 = 365 files are 105 unique recordings plus 3 idle recordings
plus scripts and MP3s. Every analysis counts each recording once.

| Dataset | Apparent files | Distinct recordings | Channels | Usable? |
|---|---|---|---|---|
| `Microphone calibration data/Distance based sample_s` | 105 CSV | 105 | 1 | yes, with §1.1 and §3.3 caveats |
| `Microphone calibration data/Waveform based Sample_s` | 105 CSV | 0 new (duplicate) | – | duplicate |
| `Microphone feedback with respect to .../` | 105 CSV | 0 new (duplicate) | – | duplicate |
| `Microphone calibration data/Idle sample_s/readings` | 3 CSV | 3 (60 s each) | 1 each | **yes — the noise-floor source** |
| `Triple Mic Samples/sample_*.xlsx` | 25 | 25 (30 samples each) | 3 | partly (§1.2) |
| `Quadrant Based Estimations/quadrant_*.csv` | 4 | 0 measurements | – | **synthetic, §5** |
| `idle mic data/data.xlsx` | 1 | 0 | – | **corrupt, quarantined** |
| `idle mic data/filtered_data.xlsx` | 1 | 0 | – | **invalid derivative, quarantined** |
| `Filter alogrithims test/*.py` | 4 | 0 | – | design sketches, re-implemented in §4 |

**Word length and scaling.** Across all 105 excitation recordings the greatest common divisor
of the differences of the stored `Mic Value` is exactly **2**, there are **zero** odd stored
values, and the stored range is 82 – 5050. The logger therefore emits a 13-bit word whose
least significant bit is always zero — exactly what the Arduino-ESP32 core does for
`analogReadResolution(13)`, which left-shifts the native 12-bit conversion. Effective
resolution is 12 bits; the quantisation step in the stored files is 2 units = 1 raw LSB. All
values in this document are **raw 12-bit codes** (stored value ÷ 2).

**Quarantine 1 — `Triple Mic Samples/python.py` fabricates its heatmap.** Re-verified
programmatically: it contains `np.random.uniform(0.4, 0.76)`, rescales to `target_avg = 0.77`,
and never opens a `sample_*.xlsx`. Its output must not appear in the paper in any form.
`results.csv` is empty (2 bytes).

**Quarantine 2 — `idle mic data/data.xlsx` is corrupt.** 24 701 × 4 cells; 17 186 non-empty in
column A, of which 16 854 parse as a number, spanning 0 to 2.35 × 10¹². Column A interleaves at
least three streams (a monotonically increasing sample counter near 12 900–37 600, plausible
ADC codes near 1250, and small integers), plus literal `_x0000_` cells and run-together values
such as `6612938` and `112935`. Unrecoverable.

**Quarantine 3 — `idle mic data/filtered_data.xlsx` is invalid as a noise floor.** Produced by
`process_excel.py`, which keeps only values in [1100, 1500]. That is a value-range gate, not a
filter: it discards 51.5 % of column A, destroys the time base by non-uniform decimation, and
truncates exactly the tails a noise-floor estimate depends on. Its standard deviation (9.80
over 8171 rows, mean 1261.88) is biased by construction. The clean 60 s idle recordings are
used instead.

### 1.5 What acquisition chain is this? (INMP441 question)

**The data are not consistent with an INMP441 anywhere in this acquisition path.**

| Evidence | Observation | INMP441 would give |
|---|---|---|
| Word format | Unsigned integers on a 4096-code grid | Signed 24-bit two's complement |
| DC offset | 1266.5 codes (31 % of full scale) | None; digital output is DC-free |
| Clipping | Hard analogue rails at 42 and 2523 codes | Digital full scale at ±2²³ |
| Sample clock | ~1 kHz software-timed loop with host-side timestamps | I²S, hardware-clocked, typically 16–48 kHz |
| Quantisation | 1 raw LSB out of 4096 | 24-bit |

This is an analogue capsule and preamplifier feeding the ESP32-S3 internal 12-bit SAR
converter. Two readings are possible and the author must resolve which:

- the calibration and triple-microphone rigs used an analogue capsule while the DoA array uses
  an INMP441 — in which case **none** of the measurements in this document characterise the
  array's microphones; or
- the stated part is wrong.

Until this is settled the paper cannot cite an INMP441 datasheet noise figure alongside these
measurements. **A datasheet equivalent-input-noise comparison is deliberately not made here**,
because the measured floor is in ADC codes of an unknown analogue chain, with no measured
sensitivity in mV/Pa and no acoustic reference level. Converting 5.06 LSB into dB(A) SPL
requires a calibrator measurement that does not exist in this repository.

---

## 2. Measured noise floor

Source: three 60 s idle (no-source) recordings,
`Microphone calibration data/Microphone calibration data/Idle sample_s/readings/`.
Script: `analyze_real.py` §3. Figure: `fig_real_noise_floor.png`.

| Mic | N | Duration | DC (code) | RMS (LSB) | Robust 1.4826·MAD (LSB) | Outliers | Peak-to-peak (LSB) | Excess kurtosis |
|---|---|---|---|---|---|---|---|---|
| 1 | 64 051 | 60.0 s | 1264.37 | 5.56 | 5.93 | 56 | 116 | 7.86 |
| 2 | 62 042 | 60.0 s | 1267.06 | 4.03 | 4.45 | 15 | 86 | 6.34 |
| 3 | 62 045 | 60.0 s | 1268.21 | 5.59 | 4.45 | 31 | 86 | 3.58 |

Outliers are isolated single-sample dropouts (codes near 13 and 18, i.e. the converter reading
almost zero) plus a few transients, 0.02–0.09 % of samples. They are excluded from the RMS so
that the quoted figure is the stationary floor rather than a glitch rate; the glitch rate
itself is reported above and is a real hardware property.

**The noise is not Gaussian.** Excess kurtosis is 3.6–7.9 (0 for a Gaussian): a sharp core with
heavy tails, meaning occasional excursions well beyond what the RMS suggests. This matters for
any threshold or gate and should be stated rather than smoothed over. The two scale estimates
nevertheless agree to about 10 %, so the RMS is a sound figure for an SNR budget. (The robust
scale is granular because the MAD of integer data is an integer, in steps of 1.48 LSB.)

| Derived quantity | Value |
|---|---|
| Self-noise RMS, mean of three | **5.06 LSB** |
| Robust scale, mean of three | 4.94 LSB |
| 12-bit quantisation floor, 1/√12 | 0.289 LSB |
| Measured floor ÷ quantisation floor | **17.5× (24.9 dB)** |
| DC operating point, mean of three | 1266.5 of 4095 codes |
| Observed positive clipping rail | 2523 codes |
| Observed negative clipping rail | 42 codes |
| Largest undistorted peak swing | 1256 LSB |
| **Chain ceiling, peak SNR** | **47.9 dB** |
| Chain ceiling, RMS SNR of a full-swing sine | 44.9 dB |

**The converter is not the limiting noise source; the analogue front end is, by 25 dB. Adding
ADC bits would buy nothing.** The spectrum (panel c of the figure) is roughly flat above
100 Hz at ~2 × 10⁻² LSB²/Hz with a raised, structured region below 100 Hz that is interference
picked up by the analogue chain, not acoustic.

---

## 3. Microphone frequency, distance and waveform response

Source: the 105 de-duplicated excitation recordings. Script: `analyze_real.py` §4.
Figure: `fig_real_level_response.png`.

### 3.1 Clipping census

A sample counts as clipped if it lies within 2 % of the observed dynamic range of either
analogue rail (code ≥ 2475 or ≤ 92). Percentage of clipped samples, mean over the three
waveforms:

| Distance | 1 kHz | 5 kHz | 10 kHz | 15 kHz | 20 kHz |
|---|---|---|---|---|---|
| 15 cm | 40.64 | 48.00 | 20.65 | 0.21 | 8.78 |
| 50 cm | 0 | 0 | 0 | 0 | 0 |
| 100 cm | 0 | 0 | 0 | 0 | 0 |
| 150 cm | 0 | 0 | 0 | 0 | 0 |
| 200 cm | 0 | 0 | 0 | 0 | 0 |
| 250 cm | 0 | 0 | 0 | 0 | 0 |
| 300 cm | 0 | 0 | 0 | 0 | 0 |

11 of 105 recordings exceed 0.5 % clipped samples; all are at 15 cm. Those are excluded from
the level fits, because the front end rather than the microphone is setting their amplitude.

### 3.2 Level, dB re 1 LSB RMS, unclipped recordings only (94 of 105)

| Waveform | f (kHz) | 15 cm | 50 | 100 | 150 | 200 | 250 | 300 |
|---|---|---|---|---|---|---|---|---|
| sine | 1 | – | 29.24 | 47.94 | 39.36 | 40.21 | 43.61 | 42.70 |
| sine | 5 | – | 35.66 | 44.95 | 46.73 | 51.31 | 48.71 | 52.29 |
| sine | 10 | – | 34.34 | 43.93 | 39.22 | 32.37 | 37.38 | 35.27 |
| sine | 15 | 33.24 | 25.62 | 23.05 | 27.19 | 21.76 | 20.85 | 25.05 |
| sine | 20 | 24.41 | 25.28 | 21.29 | 26.51 | 26.61 | 18.68 | 24.11 |
| square | 1 | – | 35.16 | 33.21 | 48.13 | 41.29 | 46.27 | 45.82 |
| square | 5 | – | 41.61 | 31.02 | 46.52 | 53.58 | 45.41 | 51.95 |
| square | 10 | – | 40.14 | 33.40 | 36.26 | 34.21 | 33.07 | 37.75 |
| square | 15 | – | 31.80 | 28.66 | 39.82 | 38.87 | 33.62 | 34.38 |
| square | 20 | – | 37.03 | 28.68 | 44.67 | 38.24 | 45.58 | 41.44 |
| triangle | 1 | – | 27.92 | 41.69 | 43.33 | 40.04 | 42.08 | 44.66 |
| triangle | 5 | – | 35.38 | 40.83 | 41.61 | 46.57 | 40.71 | 45.45 |
| triangle | 10 | – | 33.24 | 44.76 | 37.39 | 33.25 | 33.31 | 35.03 |
| triangle | 15 | 44.46 | 26.39 | 29.74 | 31.45 | 28.55 | 23.96 | 25.20 |
| triangle | 20 | 44.76 | 25.88 | 26.65 | 28.79 | 25.40 | 28.76 | 28.48 |

Median level over all distances and waveforms: 42.70 dB at 1 kHz, 46.52 at 5 kHz,
36.26 at 10 kHz, 28.66 at 15 kHz, 28.48 at 20 kHz.

### 3.3 Inverse-square-law check — the result is negative

Fitted slope of level against log₁₀(distance), unclipped points only:

| Waveform | f (kHz) | n | Slope (dB/decade) | Residual sd (dB) | Deviation from −20 |
|---|---|---|---|---|---|
| sine | 1 | 6 | +12.99 | 5.06 | +32.99 |
| sine | 5 | 6 | +19.99 | 1.78 | +39.99 |
| sine | 10 | 6 | −2.33 | 4.06 | +17.67 |
| sine | 15 | 7 | −7.28 | 2.47 | +12.72 |
| sine | 20 | 7 | −1.20 | 2.84 | +18.80 |
| square | 1 | 6 | +16.47 | 4.05 | +36.47 |
| square | 5 | 6 | +17.71 | 6.35 | +37.71 |
| square | 10 | 6 | −4.50 | 2.46 | +15.50 |
| square | 15 | 6 | +6.35 | 3.82 | +26.35 |
| square | 20 | 6 | +11.73 | 5.19 | +31.73 |
| triangle | 1 | 6 | +17.72 | 3.35 | +37.72 |
| triangle | 5 | 6 | +11.31 | 2.30 | +31.31 |
| triangle | 10 | 6 | −3.52 | 4.40 | +16.48 |
| triangle | 15 | 7 | −12.37 | 3.92 | +7.63 |
| triangle | 20 | 7 | −10.79 | 4.56 | +9.21 |

| Quantity | Value |
|---|---|
| Pooled slope | **+4.82 dB/decade** (sd across conditions 11.30) |
| Free-field ideal | −20.00 dB/decade |
| Conditions with a positive fitted slope | 9 of 15 |
| Adjacent distance steps where level rises with distance | 43 of 79 (54 %) |

The level does not fall with distance at all; in 54 % of adjacent steps it rises, and the
pooled slope is positive. No acoustic mechanism produces that. The dominant explanation must be
that **the excitation level was not held constant between runs**: the sine 1 kHz condition
reads 29.2 dB at 50 cm and 47.9 dB at 100 cm, an **+18.7 dB change over one doubling of
distance** where the physics allows at most −6 dB. Contributing factors that cannot be
separated with the data available: the loudspeaker drive level and preamplifier gain are
recorded nowhere and there is no reference microphone; the room is untreated so the reverberant
field dominates beyond the critical distance; and the 15 cm points that would anchor the fit
are clipped.

> **An inverse-square-law verification cannot be claimed from this dataset, and neither can a
> distance response of any kind.**

**Frequency axis.** Because every excitation is aliased (§1.1), the horizontal axis of any
"frequency response" drawn from these files is the loudspeaker *command* frequency, not
anything present in the recording. With the drive level also uncontrolled, the only statement
the data will bear is qualitative: the transmit-plus-receive chain delivers noticeably more
level at 1–10 kHz than at 15–20 kHz.

---

## 4. Inter-microphone mismatch

Script: `analyze_real.py` §5. Figure: `fig_real_mic_mismatch.png`.

**What can and cannot be measured.** The 105 calibration recordings each contain one
microphone channel and do not record which microphone it was, so they yield no inter-microphone
comparison at all. Only two datasets carry comparable per-microphone information: the three
idle recordings (DC and noise-floor mismatch) and the 25 three-channel clips (relative
broadband gain). **Phase mismatch cannot be measured from anything in this repository**,
because that requires a common excitation captured simultaneously on all three channels with a
time base, which no file provides.

### 4.1 DC and noise-floor mismatch (idle recordings)

| Mic | DC (LSB) | Self-noise RMS (LSB) |
|---|---|---|
| 1 | 1264.37 | 5.56 |
| 2 | 1267.06 | 4.03 |
| 3 | 1268.21 | 5.59 |

DC spread 3.85 LSB (0.30 % of the operating point); noise-floor spread 1.39× (**2.84 dB**).

### 4.2 Relative broadband gain (three-channel clips)

Total least squares (consistent when both channels carry comparable noise); ordinary least
squares shown as a lower bracket, since OLS is biased towards zero by a noisy regressor.

| Pair | n clips (r > 0.8) | TLS gain | TLS (dB) | OLS (dB) | IQR of TLS (dB) |
|---|---|---|---|---|---|
| MIC1→MIC2 | 10 | 1.0763 | +0.64 | −0.19 | 0.93 |
| MIC1→MIC3 | 8 | 0.8779 | −1.13 | −1.70 | 1.27 |
| MIC2→MIC3 | 9 | 0.7797 | −2.16 | −2.91 | 2.09 |

Transitivity check: g₁₂ × g₂₃ = 0.8392 against g₁₃ = 0.8779, closure error **−0.39 dB**. A gain
ratio must be transitive around the three channels, so the closure error is a direct estimate
of the method's own uncertainty — and it is a third of the mismatch being measured. Treat these
as order-of-magnitude figures.

| Quantity | Value |
|---|---|
| Median absolute pairwise gain mismatch | **1.21 dB** |
| Interquartile spread of the estimate | 2.67 dB |

### 4.3 What mismatch costs a GCC-PHAT array

GCC-PHAT normalises each cross-spectrum to unit magnitude, so a *frequency-flat gain* mismatch
cancels exactly and contributes no delay bias. What does not cancel is a gain mismatch that
varies with frequency (which tilts the weighting) and any *phase* mismatch, which maps
one-for-one into a delay error. On this array (delay budget 252.5 µs):

| Phase mismatch | Delay error at 2 kHz | Worst-case azimuth error |
|---|---|---|
| 1° | 1.39 µs | 0.32° |
| 2° | 2.78 µs | 0.63° |
| 5° | 6.94 µs | 1.58° |
| 10° | 13.89 µs | 3.15° |

Five degrees of uncorrected phase mismatch at 2 kHz already consumes 2.8 % of the array's
entire delay budget. This is a real and citable limitation of a low-cost three-microphone
build — but **this repository contains no measurement of it**. Obtaining one requires a single
source captured simultaneously on all three channels, at a known sample rate, at one known
azimuth: roughly ten minutes of bench time, and it should be done.

---

## 5. Filter algorithm comparison

Script: `analyze_real.py` §6. Figure: `fig_real_filter_comparison.png`.

**What the four scripts actually do.** Each builds a low-pass FIR, applies it to
`np.random.randn(1000)` — synthetic noise — and plots the result. None opens a recording and
none measures anything. The comparison below re-implements the four designs exactly as written
and runs them on the real idle and calibration data.

Note that A1 and A2 do **not** share a cutoff despite both scripts writing `0.1`: A1 writes it
into `np.sinc(2·fc·n)`, where fc is in cycles per sample (0.1 fs = 0.2 Nyquist), whereas A2
passes it to `firwin`, which takes a fraction of Nyquist (0.05 fs). Every metric is therefore
measured relative to each filter's own −3 dB point.

### 5.1 Design-domain response, at the fitted fs = 1000.0 Hz

| Filter | Taps | −3 dB (Hz) | Passband ripple | Stopband att. | Linear phase | Group delay (samples) |
|---|---|---|---|---|---|---|
| A1 windowed sinc, Hamming | 21 | 79.6 | 1.51 dB | 51.1 dB | yes | 10.00 (±0.00) |
| **A2 Kaiser firwin** | 51 | 39.7 | 1.55 dB | **87.2 dB** | yes | 25.00 (±0.00) |
| A3 frequency sampling | 51 | 5.2 | 1.84 dB | **−2.3 dB** | **NO** | 19.76 (±1.23) |
| A4 Gaussian window | 21 | 44.2 | 1.92 dB | 70.5 dB | yes | 10.00 (±0.00) |

### 5.2 Noise suppression, measured on the three 60 s idle recordings (dB RMS reduction)

| Filter | MIC1 | MIC2 | MIC3 | Mean |
|---|---|---|---|---|
| A1 | 4.03 | 2.95 | 1.59 | 2.85 |
| **A2** | 7.10 | 5.52 | 3.05 | **5.22** |
| A3 | 3.42 | 3.75 | 3.45 | 3.54 |
| A4 | 6.32 | 4.90 | 2.78 | 4.67 |

### 5.3 Passband fidelity on a real recording (`sine_wave_15k_15.csv`)

| Filter | In-band amplitude change (dB) | Out-of-band residual (dB) |
|---|---|---|
| A1 | −0.000 | −18.32 |
| A2 | −0.000 | **−89.81** |
| A3 | −0.003 | −9.65 |
| A4 | −0.000 | −29.50 |

### 5.4 The metric that decides it: phase

A filter applied identically to all three channels contributes a *common* delay, which cancels
in every time-difference. What does not cancel is group delay that varies with frequency.

| Filter | GD variation, own passband | GD variation, 0–100 Hz | At fs = 48 kHz | Azimuth error @48 kHz |
|---|---|---|---|---|
| A1 | 0.000 smp | 0.000 smp | 0.000 µs | 0.00° |
| A2 | 0.000 smp | 0.000 smp | 0.000 µs | 0.00° |
| A3 | 2.465 smp | **285.2 smp** | **5943 µs** | **unbounded** |
| A4 | 0.000 smp | 0.000 smp | 0.000 µs | 0.00° |

### 5.5 Recommendation

**Use A2 — the 51-tap Kaiser (β = 8.6) `firwin` low-pass — applied identically to all three
channels.**

1. Exactly linear phase (coefficients symmetric to 1 × 10⁻¹²), so its 25-sample group delay is
   common to all channels and cancels exactly in every TDOA. Passband group-delay variation
   0.000 samples.
2. Deepest stopband by a wide margin: 87 dB, against 51 dB (A1), 70 dB (A4) and −2 dB (A3).
3. Removes the most measured noise from the real idle recordings: 5.22 dB.
4. Trivial cost: 51 MACs per sample per channel, 153 per three-channel frame — far under 1 % of
   one ESP32-S3 core at 48 kHz.

**Reject A3 outright.** Its coefficients are not symmetric, so it is not linear phase: it is the
un-shifted inverse DFT of a rectangular mask, a coding error rather than a design choice. It
has no usable stopband (−2.3 dB), a −3 dB point at only 5.2 Hz, and a 0–100 Hz group-delay
variation of 285 samples — 24× the array's entire delay budget at 48 kHz. A non-linear-phase
filter in front of a TDOA estimator is the one thing a delay-based system must not do.

**A1 and A4** are usable, cheaper (21 taps, 10-sample group delay) and both linear phase, so
neither corrupts the delay; they simply roll off too gently.

**Latency caveat.** A2's 25-sample group delay is 25 ms at 1 kHz but only 0.52 ms at the 48 kHz
design rate. At the low rate, prefer A1 or A4.

**Scope caveat.** This chooses among the author's four candidates. None is a band-pass, and a
TDOA front end for a 300–3400 Hz source wants a band-pass. More importantly, **no post-
conversion filter can undo the aliasing of §1.1**. The filter this hardware actually needs is an
anti-alias filter *ahead of* the converter — a hardware change, not a software one.

---

## 6. Near-field quadrant tables — appendix scope

Script: `analyze_real.py` §8. Figure: `fig_real_quadrant_gdop.png`.

| Quadrant | Rows | x range (m) | y range (m) | t range (µs) | Blank t |
|---|---|---|---|---|---|
| 1 | 3600 | 0.05 … 3.00 | 0.05 … 3.00 | 2.43 … 145.75 | 0 |
| 2 | 3660 | 0.05 … 3.00 | −3.00 … −0.00 | 2.43 … 145.77 | 0 |
| 3 | 3660 | −3.00 … −0.00 | 0.05 … 3.00 | 0.00 … 145.75 | 5 |
| 4 | 3721 | −3.00 … −0.00 | −3.00 … −0.00 | 0.00 … 145.77 | 5 |

**What `t` is.** The naive reading — straight-line propagation time from the origin — is wrong:
at (0.05, 0.05) m the table gives 99.82 µs, whereas r/c for r = 0.0707 m is 206.15 µs, and the
correlation of t with r/c over all 14 631 rows is +0.054, i.e. none. `t` is also bounded at
145.77 µs and saturates there rather than growing with r.

`t` is the **two-microphone TDOA** for a near-field source at (x, y), for a pair separated by d
on the x-axis and centred on the origin:

```
t(x, y) = | sqrt((x + d/2)^2 + y^2) − sqrt((x − d/2)^2 + y^2) | / c
```

| Test | Result |
|---|---|
| Fixed d = 0.05 m, c = 343 m/s: residual RMS | 2.886 × 10⁻¹¹ s (0.029 ns) |
| R² | 1.0000000000 |
| Max residual | 2.0 × 10⁻¹⁰ s |
| Free fit of (d, c) | d = 0.050000000 m, c = 343.000000 m/s |

The residual is exactly the rounding of the ten-decimal text format. This **independently
confirms the mathematics track's conclusion**, obtained here by a separate route (hypothesis
enumeration then Levenberg–Marquardt fit over all four files).

> **These four files are a computed geometric lookup table, not a measurement.** They contain no
> microphone, no room, no noise and no acquisition. Nothing derived from them may be described
> as experimental. Note also that the tabulated pair separation d = 5.00 cm is the array's
> *circum-radius*, whereas the actual microphone spacing on an equilateral triangle of that
> circum-radius is 8.66 cm — so the table does not even describe the built array's geometry.

**Near-field dilution of precision for the real 3-microphone array.** With two independent
delay observables τ₁ₘ = (|p − p₁| − |p − pₘ|)/c for m = 2, 3, the position covariance is
(JᵀJ)⁻¹σ_τ², and GDOP = √(trace((JᵀJ)⁻¹)) has units of m/s, so position error = GDOP × σ_τ:

| Range from array centre | Median GDOP (m/s) | Position error for σ_τ = 1 µs |
|---|---|---|
| 0.05 – 0.25 m | 16 747 | 0.017 m |
| 0.25 – 0.50 m | 84 441 | 0.084 m |
| 0.50 – 1.00 m | 341 508 | 0.342 m |
| 1.00 – 1.50 m | 874 626 | 0.875 m |

A 1 µs delay uncertainty — optimistic even at 48 kHz, and 1000× below one sampling interval at
the measured rate — already gives metre-scale position error beyond about 0.5 m. **Near-field
two-dimensional positioning on a 5 cm aperture is geometry-limited, not algorithm-limited.**
That is the one honest thing the quadrant files illustrate, and it belongs in an appendix.

---

## 7. Sim-versus-real

There is **no measured direction-of-arrival result in this repository**, so the simulated
error-versus-SNR, error-versus-RT60 and temporal-accumulation curves cannot be overlaid with a
measured counterpart. Saying so plainly is the correct position.

One quantitative bridge exists: the measured signal chain fixes where on the simulation's SNR
axis this hardware operates.

| Quantity | Value |
|---|---|
| Measured self-noise RMS | 5.06 LSB |
| Largest undistorted peak swing | 1256 LSB |
| Chain ceiling, peak SNR | 47.9 dB |
| Chain ceiling, sine RMS SNR | 44.9 dB |
| Measured per-recording SNR, unclipped set (n = 94) | median 21.4 dB, 10th pct 11.1 dB, 90th pct 32.4 dB |

**Dependency note.** `fig_real_snr_operating_point.png` plots the measured operating band
against a simulated curve **parsed at run time** from `benchmark_run.log`, so it always tracks
whatever the re-baseline track has most recently produced; nothing is hardcoded, and the source
file plus its modification time are printed in `realdata_run.log` beside the parsed values.
Every measured quantity in the table above is independent of the simulation.

As of the run recorded in `realdata_run.log` (benchmark log last modified 2026-07-27 20:22:39,
i.e. the post-re-baseline version), the measured 11–45 dB operating band spans the region where
the simulated per-frame median error falls from 0.20° to 0.11°. Re-run `analyze_real.py` after
any further simulation change to refresh that sentence and the figure.

---

## 8. Figure inventory

All at 300 dpi in `validation/figs/`. Colour-blind-safe Okabe–Ito palette; series distinguished
by marker and line style as well as colour, so all panels survive greyscale conversion. Full
captions are recorded verbatim in `validation/realdata_run.log` next to each `[FIGURE]` tag.

| # | File | What it shows | Paper section | Draft caption (short form) |
|---|---|---|---|---|
| 1 | `fig_real_timebase.png` | (a) histogram of the logged inter-sample interval; (b) observed spectral line vs nominal excitation frequency for all waveforms and distances, with the one-parameter alias fit | 3 (system) or 6.1 (protocol); **the key forensic figure** | Acquisition time base of the calibration rig. The logged interval clusters at 1.000 ms but carries duplicate stamps and tens-of-millisecond gaps, so it timestamps host reception, not conversion. The single low-frequency line in each recording is proportional to the excitation frequency — the signature of undersampling and of nothing else — giving δ = 12.2 ppm and fs = 999.988 Hz. |
| 2 | `fig_real_alias_demo.png` | The "5 kHz, 15 cm" recording: full 30 s time series (clipped, ~0.06 Hz) and its spectrum with the predicted alias marked | 3 or 6.1, beside Fig. 1 | What a 5 kHz excitation looks like sampled at 1 kHz: a near-square 0.06 Hz oscillation pinned against the analogue rails. No acoustic process exists at 0.06 Hz; this is the folded image, and the flat tops are amplifier clipping. The marked alias frequency was predicted from a global fit across all recordings, not from this file. |
| 3 | `fig_real_triplemic.png` | (a) one clip, 3 channels; (b) cross-correlation with the physically possible delay window shaded; (c) the 5×5 position-label map; (d) integer peak-lag histogram vs the physical bound | 6.2, as the honest replacement for a measured-accuracy figure | The 25 three-channel clips and why they cannot yield a DoA estimate. The shaded bar in (b) is the complete range of delays the array can physically produce — ±0.25 of one sampling interval at 1 kHz, ±0.04 at the 167 Hz inferred for these clips — so the whole azimuth range collapses into the lag-zero bin. Every non-zero peak in (d) lies outside the physically possible range and is noise. |
| 4 | `fig_real_noise_floor.png` | (a) 2 s of each idle channel; (b) log-density amplitude histograms vs a Gaussian; (c) Welch PSDs vs the 12-bit quantisation floor | 3 (hardware) or 6.3 | Measured self-noise from three 60 s idle recordings. The distributions are not Gaussian (excess kurtosis 3.6–7.9). Per-channel RMS 4.0–5.6 LSB, sitting 25 dB above the 12-bit quantisation floor, so the analogue front end, not the converter, sets the noise floor. Axes are in ADC LSB because no acoustic calibration of this rig exists. |
| 5 | `fig_real_level_response.png` | (a) level vs distance per excitation frequency with the 1/r reference; (b) level vs excitation frequency per waveform against the measured noise floor; (c) clipping map | 6.1 or appendix; **a negative result** | Recorded level against distance, excitation frequency and waveform. The measured decay is not merely shallower than 1/r, it is often positive, which no acoustic mechanism produces: the drive level was not held constant between runs. The frequency axis is the loudspeaker command frequency, since every excitation is aliased. |
| 6 | `fig_real_mic_mismatch.png` | (a) per-channel DC offset; (b) per-channel idle noise RMS; (c) per-clip TLS gain ratio for each pair | 6.4 (sim-vs-real limitations) or 7 | Measured channel-to-channel mismatch. DC pedestals agree to 3.8 LSB but noise floors differ by 2.8 dB and broadband gains by a median 1.2 dB. No phase-mismatch measurement exists; GCC-PHAT is insensitive to flat gain mismatch but not to phase mismatch. |
| 7 | `fig_real_filter_comparison.png` | (a) magnitude responses; (b) group delay; (c) measured idle PSD before and after each filter | 3 (firmware pipeline) or appendix | The four candidate low-pass filters re-implemented as written and run on real data. A1, A2 and A4 are linear phase, so the delay they add is common to all channels and cancels in every time-difference; A3, the un-shifted inverse DFT of a rectangular mask, is not, and would smear the cross-correlation peak. A2 is recommended: linear phase, 87 dB stopband, largest measured noise reduction. |
| 8 | `fig_real_quadrant_gdop.png` | (a) the four quadrant tables assembled, with the implied 5 cm microphone pair marked; (b) near-field position error for σ_τ = 1 µs on the real 3-mic array | **Appendix only** | The quadrant tables are a two-microphone TDOA surface reproduced exactly (residual 0.029 ns, R² = 1.000000) by the analytic expression for a 5.0 cm pair at c = 343 m/s, so they are a computed lookup table, not a measurement. Panel (b) gives the corresponding position error for the real array: beyond about half a metre, even 1 µs of delay uncertainty gives metre-scale error. |
| 9 | `fig_real_snr_operating_point.png` | Measured electrical SNR band of the real chain against the simulated median-error-vs-SNR curve, the latter parsed live from `benchmark_run.log` | 6.4 | The only sim-to-real bridge the data support. The shaded band is the measured SNR of the hardware; the curve is simulated and is read from the current simulation log at run time. The figure locates the hardware on the simulation's x-axis and does **not** report a measured localization accuracy. |

---

## 9. What this data cannot support

Claims the paper must **not** make, and what it would take to earn each one.

| Must NOT claim | Why not | Minimum additional measurement |
|---|---|---|
| **Any measured DoA or localization accuracy** (RMSE, median error, error CDF, accuracy heatmap) | No clip in the repository permits a delay estimate: no anti-alias filter, ~167 Hz per-channel rate, 30 samples, no azimuth ground truth. The only accuracy figure in the repo is fabricated (`Triple Mic Samples/python.py`). | A labelled campaign: hardware-timed I²S or timer-driven ADC at ≥16 kHz with an anti-alias filter, ≥30 azimuths at known angles (protractor/turntable, ground-truth uncertainty stated), ≥2 rooms with estimated RT60, broadband and speech sources, ≥10 repeats per angle, clips named `az<±DDD>_...` for `real_data.py`. |
| **The 77 % accuracy heatmap, or any figure derived from it** | Fabricated by `np.random.uniform(0.4, 0.76)` rescaled to a preset mean; never reads a recording. | As above. |
| **A microphone frequency response over 1–20 kHz** | Every excitation is 2–40× above Nyquist and is recorded only as a sub-hertz folded image. The frequency axis is the loudspeaker command, not the microphone's input. | Repeat the sweep with an anti-alias filter and fs ≥ 48 kHz, or use a stepped-sine measurement at frequencies below the actual Nyquist. |
| **An inverse-square-law verification, or any distance response** | Level rises with distance in 54 % of adjacent steps and the pooled slope is +4.8 dB/decade; the drive level was not documented or held constant, and there is no reference microphone. | Repeat with a documented, fixed drive level and a calibrated reference microphone at a fixed position, in a room with a stated RT60. |
| **Any inter-microphone phase or delay mismatch figure** | No file contains a common excitation captured simultaneously on all three channels with a time base. | One clip: a single broadband source at one known azimuth, captured simultaneously on all three channels at a known sample rate. Ten minutes of bench time. |
| **A microphone self-noise figure in dB(A) SPL, or a comparison with an INMP441 datasheet** | The measured floor is in ADC codes of an unknown analogue chain; no sensitivity in mV/Pa, no acoustic reference level, and the data are inconsistent with an INMP441 in any case (§1.5). | A pistonphone or class-1 calibrator measurement to fix mV/Pa, plus written confirmation of the microphone part number on the board. |
| **Anything experimental derived from `Quadrant Based Estimations/`** | Reproduced exactly (R² = 1.000000, residual 0.029 ns) by a two-parameter analytic formula. It is a forward model, not data. | Actual near-field recordings at known (x, y) with a resolvable time base. |
| **On-device latency, SRAM or CPU load** (the old "10 µs" claim) | No timing log exists anywhere in the repository. | Log `esp_timer_get_time()` deltas around the estimator to CSV and run `real_data.py --latency`. |
| **Measured array geometry, sample rate or snapshot length for the DoA build** | `R = 5 cm`, `fs = 48 kHz`, `N = 2048` are placeholders in `doa_benchmark.py`; "5 cm aperture" is ambiguous between circum-radius and spacing; and the only rate measured anywhere in this repository is ~1 kHz. | Measure the three microphone coordinates with calipers; state the firmware's configured sample rate and frame length. |
| **A sim-versus-real agreement claim** | There is no real DoA result to agree with. | The labelled campaign above. |
| **That the ADC resolution limits performance** | Measured: the analogue floor is 25 dB above the 12-bit quantisation floor. This is a positive finding and can be claimed — the *opposite* claim cannot. | – |

### Things the data DO support, and can be claimed

- fs = 999.988 Hz for the calibration rig, established two independent ways (§1.1).
- Self-noise 4.0–5.6 LSB RMS, 25 dB above the 12-bit quantisation floor (§2).
- Chain ceiling of 47.9 dB peak SNR, set by front-end clipping at 42 and 2523 codes (§2).
- Inter-channel DC agreement to 3.8 LSB, noise-floor spread 2.84 dB, broadband gain mismatch
  ~1.2 dB (§4).
- The filter recommendation, with measured stopband, ripple, group delay and noise reduction
  on real recordings (§5).
- The near-field GDOP result for a 5 cm aperture, clearly labelled as geometry (§6).
- Every negative result above, stated as a negative result. These are the most defensible
  content in this document and the reason a reviewer will trust the rest.
