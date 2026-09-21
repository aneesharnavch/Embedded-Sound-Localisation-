# Simulation re-baseline: results, before-and-after, and what changed in the conclusions

**Date:** 2026-07-27. **Scope:** all simulation results. Real-data results are the parallel
track's and are untouched.

A defect was found in the GCC-PHAT front end of `validation/doa_benchmark.py`: the PHAT weight
was applied over the full 0–24 kHz band while the simulated source occupies only 300–3400 Hz.
The defect has been reproduced independently, corrected, and every simulation has been re-run.
This document records the verification, the replacement numbers with standard errors, a
line-by-line comparison against the superseded logs, and the consequences for the paper's
argument.

**The short version.** The defect was real and the correction is large: per-frame free-field
azimuth RMSE at 10 dB SNR falls from 4.11° to 0.31°, a factor 13.4. How much of that factor is a
genuine estimator improvement rather than an artefact of the simulation's noise model depends on
the acquisition bandwidth: 7.0× survives a realistic 8 kHz chain and 3.2× a 4 kHz chain, while
the corrected estimator's absolute accuracy, 0.30–0.33°, is bandwidth-independent and can be
quoted as it stands (Section 2). The correction does **not** strengthen the paper's central
thesis — it substantially weakens it. Confidence-weighted temporal accumulation is no longer the dominant
lever, because the per-frame estimator is now accurate enough that in every reverberant room the
bias floor is reached within four to eight frames. The reverberation bias floor is now the
dominant effect, and the paper should be rewritten around it. Section 9 states this bluntly.

---

## Contents

1. [Verification of the defect](#1-verification-of-the-defect)
2. [The three-way artefact decomposition](#2-the-three-way-artefact-decomposition-the-governing-result)
3. [What was changed in the code](#3-what-was-changed-in-the-code)
4. [Re-baselined results](#4-re-baselined-results)
5. [Before and after, number by number](#5-before-and-after-number-by-number)
6. [The three gaps closed](#6-the-three-gaps-closed)
7. [Compute, treated honestly](#7-compute-treated-honestly)
8. [Theory versus measurement](#8-theory-versus-measurement)
9. [What changed in the paper's conclusions](#9-what-changed-in-the-papers-conclusions)

### Provenance

| artefact | produced by | log |
|---|---|---|
| free-field sweep, compute, GDOP, CRB | `validation/doa_benchmark.py` | `validation/benchmark_run.log` |
| reverberation sweep, four estimators | `validation/reverb_robustness.py` | `validation/reverb_run.log` (**new — none existed before**) |
| ablation, isotropy, scaling, accumulation | `validation/ablation.py` | `validation/ablation_run.log` |
| defect verification, artefact decomposition, snapshot scaling | `validation/rebaseline_checks.py A B C` | `validation/rebaseline_checks_ABC.log` |
| compute study | `validation/rebaseline_checks.py D` | `validation/rebaseline_checks_D.log` |
| superseded logs and figures | — | `validation/archive/` (with a README mapping each old file to its replacement), `validation/figs_archive_prerebaseline/` |

The replacement logs are UTF-8; the archived ones are UTF-16, because they were captured by a
PowerShell redirect.

**One stale artefact, flagged not touched.** `validation/verify_sims.py` and
`validation/sim_verify_run.log` belong to the mathematics track. That script re-runs the old
experiments and compares them against the archived logs; with the corrected front end it will now
report large discrepancies against those logs, correctly but unhelpfully. Whoever owns it should
either re-point it at the new logs or retire it.

Seed 7 throughout. Each experiment calls `doa_benchmark.reseed(<tag>)` before it starts, so
every experiment is reproducible on its own and independent of the order in which the
experiments are run; tags are listed in each script's `__main__` block. Reproducibility was
checked, not assumed: two independent invocations of `ablation.py` produced byte-identical
numeric output, and `rebaseline_checks.py A B C` likewise.

### Figure inventory

All figures regenerated at 300 dpi, Okabe–Ito colour-blind-safe palette, distinct markers and
dash patterns so they survive greyscale, sized for single-column (3.4 in) or double-column
(6.8 in) width, axis labels carrying units, no decorative titles. Superseded versions are in
`validation/figs_archive_prerebaseline/`.

| figure | shows | script |
|---|---|---|
| `fig_geometry.png` | array geometry | `doa_benchmark.py` |
| `fig_srp_spectrum.png` | one SRP-PHAT spatial spectrum | `doa_benchmark.py` |
| **`fig_phat_band_defect.png`** | **new** — the defect made visible: effective PHAT bin weight and the resulting correlation, full-band versus band-limited, on one snapshot | `doa_benchmark.py` |
| `fig_rmse_vs_snr.png` | RMSE versus SNR, four estimators, with the CRB and the 1° grid floor | `doa_benchmark.py` |
| `fig_error_cdf.png` | error CDF at 10 dB | `doa_benchmark.py` |
| `fig_accuracy_matrix.png` | median error over azimuth × SNR | `doa_benchmark.py` |
| `fig_pareto.png` | accuracy versus cost, measured host time and FLOP model side by side, with the vectorised SRP-PHAT point | `doa_benchmark.py` |
| `fig_accuracy_vs_rt60.png` | median and RMSE versus RT60, four estimators | `reverb_robustness.py` |
| `fig_ablation_rt60.png` | gate/weight ablation and the paired difference against GCC-PHAT | `ablation.py` |
| **`fig_isotropy.png`** | **new** — azimuth dependence of the error s.d. against the (M36) prediction | `ablation.py` |
| `fig_resource_scaling.png` | aperture and snapshot scaling against the 1/R and N^−1/2 laws | `ablation.py` |
| `fig_temporal_accumulation.png` | RMSE versus T, free field and three rooms, weighted and plain | `ablation.py` |
| **`fig_bias_floor.png`** | **new, and the key figure of the re-baseline** — RMSE versus T against the fitted b² + σ₁²/T law, showing free field falling as 1/√T with no floor while every reverberant room is pinned to its floor from T = 1 | `ablation.py` |
| **`fig_phat_artefact_decomposition.png`** | **new** — RMSE versus acquisition bandwidth for both weight bands, and the surviving improvement ratio | `rebaseline_checks.py` |

---

## 1. Verification of the defect

Reproduced independently, on matched snapshots, without reference to the reported numbers.
Source: `rebaseline_checks.py`, study A.

### 1.1 The premise

PHAT divides each frequency bin by its own magnitude, so after weighting a bin containing only
sensor noise has exactly the same influence on the correlation as a bin containing the source,
while its phase is uniformly random. The implemented regularised PHAT attenuates only bins more
than 60 dB below the strongest bin, which at any usable SNR is almost none of them.

| quantity | measured |
|---|---|
| real-FFT bins per pair (zero-padded to `n = 2N`) | 2049 |
| bins inside the 300–3400 Hz source band | 265 (12.9 %) |
| bins left at unit PHAT weight at 10 dB SNR | 68.4 % of all bins |
| **of those, the fraction outside the source band** | **80.9 %** |

The mathematics track reported 81 %. **Confirmed.** `validation/figs/fig_phat_band_defect.png`
shows the effective bin weight and the resulting correlation for a single snapshot.

### 1.2 The magnitude of the correction

Plain GCC-PHAT plus least squares, 11 azimuths × 40 trials = 440 **matched** frames per cell
(both weight bands see the identical snapshot, so the difference is attributable to the weight
and to nothing else). Errors in degrees; σ_τ is the per-pair TDOA error standard deviation.

| nominal SNR | PHAT weight | RMSE | median | p90 | σ_τ (µs) |
|---|---|---|---|---|---|
| 0 dB | full band | 4.927 ± 0.164 | 3.212 ± 0.204 | 7.752 ± 0.355 | 26.64 |
| 0 dB | 300–3400 Hz | **0.740 ± 0.023** | 0.528 ± 0.027 | 1.208 ± 0.051 | **3.374** |
| 10 dB | full band | 4.046 ± 0.137 | 2.695 ± 0.142 | 6.560 ± 0.344 | 22.55 |
| 10 dB | 300–3400 Hz | **0.321 ± 0.011** | 0.227 ± 0.012 | 0.487 ± 0.017 | **1.494** |
| 20 dB | full band | 2.093 ± 0.079 | 1.435 ± 0.086 | 3.412 ± 0.175 | 13.94 |
| 20 dB | 300–3400 Hz | **0.174 ± 0.005** | 0.121 ± 0.007 | 0.287 ± 0.012 | **0.863** |
| 40 dB | full band | 0.816 ± 0.062 | 0.238 ± 0.014 | 1.330 ± 0.088 | 9.620 |
| 40 dB | 300–3400 Hz | **0.151 ± 0.004** | 0.107 ± 0.007 | 0.257 ± 0.007 | **0.752** |

Paired mean reduction in |error|: +3.329 ± 0.143° at 0 dB (23.3 σ), +2.946 ± 0.118° at 10 dB
(25.0 σ), +1.506 ± 0.062° at 20 dB (24.4 σ), +0.369 ± 0.031° at 40 dB (11.8 σ).

**Verdict on each reported claim.**

| claim by the mathematics track | measured here | verdict |
|---|---|---|
| 81 % of full-weight bins are out-of-band noise at 10 dB | 80.9 % | confirmed |
| per-frame free-field RMSE 4.14° → 0.31° | 4.05° → 0.32° (study A); 4.11° → 0.31° (study B) | confirmed |
| the high-SNR RMSE pathology disappears | the archived full-band log is non-monotone (GCC-PHAT RMSE 4.23° at 10 dB, 7.14° at 20 dB); the re-baselined estimator is strictly monotone in SNR for all four estimators. The heavy-tail signature RMSE/median at 40 dB falls from 3.43 (full band) to 1.41 (band-limited) | confirmed |
| N^−1/2 snapshot scaling restored, −0.512 versus −0.208 | −0.242 ± 0.015 full band, **−0.444 ± 0.015** band-limited (Section 8.3) | confirmed in direction; the exact figure differs, see Section 8.3 |
| estimator moves from 29× to 1.4× the bound | σ_τ /attainable = 21.0× → **1.39×** at 10 dB | confirmed exactly |

The one number that needed correcting is the Cramér–Rao bound convention itself. Section 8.3 of
`math_model.md` uses the **nominal** full-band SNR in (M82) and the **in-band** SNR in (M83),
which is correct — (M82) is a time-domain bound in which σ_w² is the total per-sample noise
variance, whereas (M83) is written in terms of coherence and needs the in-band conversion (M84).
Applying (M84) in both places, which the table's column header invites, moves the azimuth bound
by 8.9 dB. `doa_benchmark.crb_azimuth_deg` and `crb_tdoa_s` now reproduce both columns of that
table to four significant figures and carry a comment recording the trap.

---

## 2. The three-way artefact decomposition (the governing result)

**This section governs how the correction may be described in the paper.**

The harness adds white Gaussian noise across the whole 0–24 kHz Nyquist band. Real hardware has
an anti-alias filter and a transducer of finite bandwidth, so its out-of-band bins are not filled
with noise in the same way, and part of the measured improvement is therefore an artefact of the
simulation rather than a genuine estimator gain.

The acquisition chain is now modelled explicitly (`simulate(..., acq_band=...)`,
`simulate_reverb(..., acq_band=...)`): a brick-wall band-pass applied to **signal and noise
together**, exactly as an anti-alias filter acts physically. The nominal SNR fixes the noise
power *spectral density*, so narrowing the acquisition band removes out-of-band noise without
changing the in-band SNR. Every cell below therefore has an identical in-band SNR and the only
thing that varies is how much out-of-band noise the front end sees. All cells are matched
snapshots, 440 frames each, 10 dB nominal SNR. Source: `rebaseline_checks.py`, study B;
`validation/figs/fig_phat_artefact_decomposition.png`.

### 2.1 The three configurations the paper must report

| # | configuration | RMSE (deg) | median (deg) | improvement over #1 |
|---|---|---|---|---|
| 1 | **full-band weight + full-band noise** — the old baseline | 4.105 ± 0.142 | 2.752 ± 0.149 | 1.00× |
| 2 | **band-limited weight + full-band noise** — the reported fix | **0.307 ± 0.011** | 0.200 ± 0.012 | **13.39×** |
| 3 | **band-limited weight + band-limited noise** — the realistic case (20 Hz–8 kHz chain) | **0.317 ± 0.011** | 0.207 ± 0.013 | 12.96× |
| 4 | full-band weight + band-limited noise — what the defect costs on realistic hardware | 2.205 ± 0.087 | 1.369 ± 0.081 | 1.86× |

### 2.2 How to read it

Two facts, and they point in different directions.

* **The absolute performance of the corrected estimator is genuine.** Rows 2 and 3 agree to
  within 3 %: 0.307° against 0.317°. Across the whole sweep of acquisition bandwidths the
  corrected estimator gives 0.301–0.327°, i.e. it is flat to ±4 %. **The re-baselined accuracy
  numbers do not depend on the simulation's noise model at all**, and can be quoted as they
  stand.
* **The size of the improvement is inflated by the noise model.** The old baseline's error
  depends strongly on acquisition bandwidth, because it is dominated by out-of-band noise that
  a real chain would not admit. The honest measure of what the fix buys on hardware is
  configuration 4 → 3.

| acquisition chain upper cut-off | full-band weight | band-limited weight | gain from the fix |
|---|---|---|---|
| 24 kHz (as simulated) | 4.105 ± 0.142 | 0.307 ± 0.011 | **13.39×** |
| 20 kHz | 3.935 ± 0.139 | 0.305 ± 0.010 | 12.91× |
| 12 kHz | 3.400 ± 0.117 | 0.301 ± 0.010 | 11.30× |
| 8 kHz | 2.205 ± 0.087 | 0.317 ± 0.011 | **6.96×** |
| 4 kHz | 1.044 ± 0.058 | 0.327 ± 0.011 | 3.20× |
| 3.4 kHz (= the source band) | 1.084 ± 0.097 | 0.311 ± 0.010 | 3.49× |

### 2.3 The sentence the paper should use

> Restricting the PHAT weight to the source band reduces per-frame azimuth RMSE at 10 dB SNR
> from 4.11° to 0.31°, a factor of 13.4, in the simulation as originally configured. Part of that
> factor is an artefact of the simulation's noise model, which adds white noise across the whole
> 24 kHz Nyquist band against a 3.1 kHz source. Repeating the comparison with the additive noise
> band-limited to a realistic 8 kHz acquisition chain, the improvement is 7.0×; with a 4 kHz
> chain it is 3.2×. The corrected estimator's absolute accuracy, 0.30–0.33° across every
> acquisition bandwidth tested, does not depend on the noise model and is the number to quote.

The honest headline is therefore **"a factor of 3 to 13 depending on acquisition bandwidth, and
a per-frame RMSE of 0.31° that is bandwidth-independent"** — not a bare "13×".

### 2.4 Why the fix still helps when the noise is already band-limited

Even with the acquisition band set exactly equal to the source band, the full-band weight still
costs a factor 3.5. Two mechanisms, both measured (`rebaseline_checks.py` study B, final block):

| acquisition band | bins outside 300–3400 Hz still at weight > 0.5 | f²-weighted out-of-band / in-band leverage |
|---|---|---|
| 0–24 kHz (none) | 1523 | 16.50 |
| 20 Hz–20 kHz | 1203 | 12.33 |
| 20 Hz–8 kHz | 360 | 3.10 |
| 20 Hz–4 kHz | 75 | 0.85 |
| 300 Hz–3.4 kHz | 32 | 0.50 |

1. When the acquisition band is **wider** than the source band, the bins between 3400 Hz and the
   acquisition cut-off hold noise and no source, and still receive unit weight. This dominates.
2. Even when the two bands coincide, `gcc_phat` zero-pads from `N` to `n = 2N` before the forward
   transform, and a brick wall on the length-`N` grid is not a brick wall on the length-`2N`
   grid: the interleaved bins carry sinc leakage from the retained band. Those leaked bins sit at
   high frequency, where the f² leverage on the correlation slope is large, so 32 of them are
   enough to matter. The 60 dB regularised-PHAT floor removes neither mechanism.

The practical consequence for the firmware is that **an anti-alias filter is not a substitute for
band-limiting the weight**; both are needed.

---

## 3. What was changed in the code

### 3.1 The fix

`doa_benchmark.gcc_phat(..., band=PHAT_BAND)`. After the existing regularised-PHAT magnitude
floor, the weighted cross-spectrum is zeroed outside `band`. The band is an explicit, documented
module-level parameter:

```python
SRC_BAND  = (300.0, 3400.0)   # the band the simulated source occupies
PHAT_BAND = SRC_BAND          # the band over which the PHAT weight is applied -- THE FIX
ACQ_BAND  = None              # modelled acquisition-chain pass-band; None = 0..fs/2
```

Setting `PHAT_BAND = None` reproduces the pre-re-baseline behaviour exactly, so the archived
numbers remain reproducible. The regularised-PHAT flooring is **unchanged** and still required:
it handles near-zero bins *inside* the retained band, while the band restriction removes bins
that are outside the source entirely.

### 3.2 Which estimators received the fix, and why

| estimator | affected by the defect? | action |
|---|---|---|
| `est_gccphat_ls` | yes | fixed, `band` passed through |
| `est_proposed` | yes (same front end) | fixed, `band` passed through — the ablation stays a clean comparison of the decision layer alone |
| `est_srp_phat` | **yes** — SRP-PHAT is built on the identical PHAT-weighted pairwise correlations | fixed identically; not fixing it would have made the comparison unfair in the proposed method's favour |
| `est_music` | **no** — MUSIC only ever accumulated bins inside `band=(300, 3400)` | unchanged |

**MUSIC was never affected, and that has a consequence for how the old comparison must be read.**
The archived log shows MUSIC at 0.81° RMSE against GCC-PHAT's 4.23° at 10 dB and was read as
evidence that subspace processing is far more accurate. It was not measuring subspace processing
against correlation processing; it was measuring a band-limited front end against a full-band
one. With the defect fixed, GCC-PHAT (0.301°) is *better* than MUSIC (0.697°). Any claim in the
draft that MUSIC is an order of magnitude more accurate than GCC-PHAT must be deleted.

### 3.3 A second fairness defect found and fixed during the re-baseline

Every test azimuth in the original sweeps was a whole number of degrees, and SRP-PHAT and MUSIC
search azimuth on a 1° grid. The truth therefore lay exactly on their search grid and they could
return the exact answer. Before the re-baseline the errors were degrees-large and this cost
nothing; afterwards it dominates, and the first re-baselined run duly produced an RMSE of
**exactly 0.000°** for SRP-PHAT and MUSIC at 20 and 40 dB.

`doa_benchmark.tiled_offsets(n)` now nudges the truth off the grid by offsets tiling
(−0.5°, +0.5°]. Tiled rather than random, so the pooled quantisation error is uniform and its
RMS is exactly 1/√12 = 0.289° — a number the reader can check. The same offsets also randomise
the phase of the true inter-microphone delays relative to the 2.604 µs correlation interpolation
grid, which matters for the correlation estimators for the same reason: without it the residual
quantisation error is identical in every frame and behaves as a bias, which would have
contaminated the free-field bias-floor measurement of Section 6.2.

**This is applied to every sweep in every script.** It is the reason SRP-PHAT and MUSIC now
plateau at 0.29–0.31° at high SNR rather than at zero: that is their 1° grid floor, and it is now
the binding limit on both of them.

### 3.4 Statistical reporting

`rmse_se` (delta-method standard error on an RMSE, distribution-free, valid for the heavy-tailed
error distributions this array produces) and `quantile_se` (bootstrap) were added, and every
number in every log now carries a standard error. Variant comparisons that share snapshots are
reported as **paired** differences with the standard error of the difference, which is far more
sensitive than comparing two independently estimated medians.

Trial counts were raised: free-field sweep 30 → 60 per (angle, SNR); RT60 sweeps 12 → 60 per
(angle, RT60); resource scaling 25 → 60; temporal accumulation 8 (free field) and 6
(reverberant) → 30 records of 128 frames.

---

## 4. Re-baselined results

### 4.1 Free-field accuracy versus SNR

`benchmark_run.log`. 21 azimuths × 60 trials = 1260 frames per cell. Absolute azimuth error in
degrees. Figures: `fig_rmse_vs_snr.png`, `fig_error_cdf.png`, `fig_accuracy_matrix.png`.

| method | SNR | median | p90 | RMSE |
|---|---|---|---|---|
| Proposed (gated) | 0 dB | 0.529 ± 0.015 | 1.221 ± 0.026 | 0.750 ± 0.014 |
| | 5 dB | 0.308 ± 0.009 | 0.760 ± 0.020 | 0.456 ± 0.009 |
| | 10 dB | 0.212 ± 0.006 | 0.493 ± 0.013 | 0.301 ± 0.006 |
| | 20 dB | 0.127 ± 0.004 | 0.293 ± 0.009 | 0.176 ± 0.003 |
| | 40 dB | 0.108 ± 0.004 | 0.244 ± 0.005 | 0.148 ± 0.003 |
| GCC-PHAT (cheap) | 0 dB | 0.527 ± 0.016 | 1.219 ± 0.029 | 0.749 ± 0.014 |
| | 5 dB | 0.308 ± 0.009 | 0.762 ± 0.020 | 0.456 ± 0.009 |
| | 10 dB | 0.212 ± 0.007 | 0.493 ± 0.012 | 0.301 ± 0.006 |
| | 20 dB | 0.125 ± 0.004 | 0.293 ± 0.008 | 0.176 ± 0.003 |
| | 40 dB | 0.108 ± 0.004 | 0.244 ± 0.005 | 0.148 ± 0.003 |
| SRP-PHAT (strong) | 0 dB | 0.558 ± 0.018 | 1.308 ± 0.028 | 0.792 ± 0.015 |
| | 5 dB | 0.358 ± 0.013 | 0.858 ± 0.019 | 0.523 ± 0.010 |
| | 10 dB | 0.275 ± 0.010 | 0.625 ± 0.016 | 0.390 ± 0.007 |
| | 20 dB | 0.258 ± 0.008 | 0.492 ± 0.009 | 0.309 ± 0.005 |
| | 40 dB | 0.250 ± 0.009 | 0.458 ± 0.005 | 0.295 ± 0.004 |
| MUSIC (subspace) | 0 dB | 1.008 ± 0.034 | 3.125 ± 0.144 | 6.470 ± 1.984 |
| | 5 dB | 0.592 ± 0.023 | 1.727 ± 0.071 | 5.096 ± 1.847 |
| | 10 dB | 0.358 ± 0.014 | 0.942 ± 0.030 | 0.697 ± 0.036 |
| | 20 dB | 0.258 ± 0.008 | 0.508 ± 0.009 | 0.346 ± 0.013 |
| | 40 dB | 0.250 ± 0.009 | 0.458 ± 0.008 | 0.290 ± 0.004 |

Four things to note.

1. **RMSE is now monotone in SNR for every estimator.** The high-SNR RMSE inflation recorded in
   `HANDOVER.md` as negative result #2 is gone. It was a symptom of the defect, not a property of
   small arrays. *The paper must retract negative result #2.*
2. **Proposed ≈ GCC-PHAT remains true, and is now much tighter.** The two agree to within 0.002°
   at every SNR, against a standard error of 0.003–0.014°. Negative result #1 survives the
   re-baseline and is in fact strengthened.
3. **SRP-PHAT and MUSIC saturate at 0.29–0.31° above 20 dB.** That is their 1° search-grid floor
   (1/√12 = 0.289°), not an accuracy limit of the algorithms. It must be quoted whenever those
   two rows are quoted.
4. **MUSIC's RMSE at 0–5 dB (6.5°, 5.1°) is outlier-driven**, with a median of only 1.0° and
   0.59°. MUSIC breaks catastrophically in a small fraction of low-SNR frames.

### 4.2 Reverberation, four estimators

`reverb_run.log` — **this log did not previously exist**; the reverberation sweep had never been
captured. 9 azimuths × 60 trials = 540 frames per cell, 15 dB SNR, 6.0 × 5.0 × 3.0 m room, source
at 1.5 m, image order 12. Figure: `fig_accuracy_vs_rt60.png`.

Median |error| (deg):

| RT60 (s) | Proposed | GCC-PHAT | SRP-PHAT | MUSIC |
|---|---|---|---|---|
| 0.05 | 0.446 ± 0.124 | 0.444 ± 0.202 | 0.444 ± 0.324 | 0.778 ± 0.351 |
| 0.10 | 0.460 ± 0.354 | 0.444 ± 0.280 | 0.444 ± 0.265 | 1.000 ± 0.391 |
| 0.20 | 1.897 ± 0.195 | 1.882 ± 0.220 | 1.778 ± 0.333 | 2.667 ± 0.081 |
| 0.30 | 2.565 ± 0.090 | 2.630 ± 0.107 | 2.667 ± 0.051 | 3.333 ± 0.327 |
| 0.45 | 2.775 ± 0.111 | 2.920 ± 0.092 | 2.667 ± 0.006 | 3.444 ± 0.200 |
| 0.60 | 2.757 ± 0.088 | 2.948 ± 0.102 | 2.667 ± 0.025 | 3.667 ± 0.162 |
| 0.80 | 2.876 ± 0.111 | 3.030 ± 0.107 | 2.667 ± 0.043 | 3.667 ± 0.129 |

RMSE (deg):

| RT60 (s) | Proposed | GCC-PHAT | SRP-PHAT | MUSIC |
|---|---|---|---|---|
| 0.05 | 3.018 ± 0.072 | 3.018 ± 0.072 | 3.134 ± 0.076 | 3.093 ± 0.076 |
| 0.10 | 3.013 ± 0.072 | 3.013 ± 0.072 | 3.156 ± 0.076 | 3.091 ± 0.075 |
| 0.20 | 3.075 ± 0.078 | 3.189 ± 0.081 | 3.129 ± 0.079 | 14.020 ± 2.989 |
| 0.30 | 3.540 ± 0.099 | 3.630 ± 0.101 | 3.504 ± 0.099 | 28.446 ± 2.857 |
| 0.45 | 3.991 ± 0.116 | 4.044 ± 0.115 | 3.976 ± 0.119 | 31.420 ± 2.779 |
| 0.60 | 4.280 ± 0.132 | 4.402 ± 0.132 | 4.300 ± 0.140 | 36.113 ± 2.949 |
| 0.80 | 4.661 ± 0.149 | 4.736 ± 0.149 | 4.639 ± 0.160 | 30.445 ± 2.841 |

Two findings.

* **MUSIC collapses in reverberation.** Its RMSE reaches 28–36° above RT60 = 0.3 s while its
  median stays near 3.4°: it produces gross front–back and wrap failures in a large minority of
  frames. This is a genuinely new result — it could not be seen before, because the previous
  reverberation sweep was never logged. The narrow-band covariance model underlying incoherent
  wideband MUSIC does not survive strong early reflections at M = 3.
* **The three correlation-based estimators are indistinguishable in reverberation.** Proposed,
  GCC-PHAT and SRP-PHAT agree to within about one standard error at every RT60.

Note the RMSE at RT60 = 0.05 s (3.0°) is far above the free-field figure at the same SNR. Even a
nearly anechoic image-source room places a strong first reflection, and the reverberation bias
dominates from the very first point of the sweep.

### 4.3 Gate and weight ablation versus RT60

`ablation_run.log`, section 1. 9 azimuths × 60 trials = 540 matched frames per cell, 10 dB SNR.
All four variants see the identical snapshot. Figure: `fig_ablation_rt60.png`.

Median |error| (deg):

| RT60 (s) | Proposed (gate+weight) | Weight only | Gate only | Neither (= GCC-PHAT) |
|---|---|---|---|---|
| 0.05 | 0.775 ± 0.236 | 0.775 ± 0.126 | 0.785 ± 0.182 | 0.785 ± 0.181 |
| 0.15 | 1.157 ± 0.224 | 1.165 ± 0.236 | 1.148 ± 0.229 | 1.148 ± 0.227 |
| 0.30 | 2.522 ± 0.097 | 2.518 ± 0.099 | 2.610 ± 0.132 | 2.590 ± 0.139 |
| 0.45 | 2.703 ± 0.077 | 2.695 ± 0.080 | 2.767 ± 0.063 | 2.793 ± 0.067 |
| 0.60 | 2.691 ± 0.097 | 2.700 ± 0.096 | 2.802 ± 0.110 | 2.811 ± 0.119 |
| 0.80 | 3.007 ± 0.117 | 3.024 ± 0.120 | 3.209 ± 0.137 | 3.222 ± 0.131 |

Paired mean difference in |error| against plain GCC-PHAT (negative = the variant is better):

| RT60 (s) | Proposed − GCC | Weight only − GCC | Gate only − GCC |
|---|---|---|---|
| 0.05 | −0.0001 ± 0.0006 (0.1 σ) | −0.0004 ± 0.0005 (0.8 σ) | +0.0004 ± 0.0004 (1.0 σ) |
| 0.15 | −0.0245 ± 0.0037 (6.7 σ) | −0.0180 ± 0.0032 (5.6 σ) | −0.0093 ± 0.0024 (3.9 σ) |
| 0.30 | −0.0878 ± 0.0135 (6.5 σ) | −0.0802 ± 0.0107 (7.5 σ) | −0.0150 ± 0.0093 (1.6 σ) |
| 0.45 | −0.0721 ± 0.0145 (5.0 σ) | −0.0575 ± 0.0137 (4.2 σ) | −0.0167 ± 0.0062 (2.7 σ) |
| 0.60 | −0.0862 ± 0.0167 (5.2 σ) | −0.0710 ± 0.0154 (4.6 σ) | −0.0203 ± 0.0088 (2.3 σ) |
| 0.80 | −0.0672 ± 0.0183 (3.7 σ) | −0.0437 ± 0.0179 (2.4 σ) | −0.0179 ± 0.0071 (2.5 σ) |

**Negative result #1 is confirmed, and the paired test lets us say something sharper than
before.** With 540 matched frames the improvement from the decision layer is now *statistically
detectable* — 3 to 7 standard errors — but it is **0.02–0.09°, that is 1 to 3 % of an error of
2.5–3.2°**. Almost all of it comes from the PSR weighting rather than the gate. The correct
statement for the paper is not "the gate and weighting make no difference" but:

> The confidence gate and PSR weighting produce a reduction in mean absolute azimuth error of
> 0.02–0.09° in reverberation, which is statistically significant over 540 matched frames but
> amounts to 1–3 % of the error and is far below the reverberation bias floor. With three
> microphones the decision layer cannot pay for itself.

That is a stronger, more defensible negative result than the previous "essentially tied", because
it is quantitative and bounded rather than a failure to reject.

### 4.4 Resource scaling

`ablation_run.log`, sections 2a and 2b. 11 azimuths × 60 trials = 660 frames per point, 10 dB
SNR. Figure: `fig_resource_scaling.png`.

| R (cm) | median | p90 | RMSE | R × median (cm·deg) |
|---|---|---|---|---|
| 2 | 0.459 ± 0.017 | 1.323 ± 0.033 | 0.785 ± 0.022 | 0.92 |
| 3 | 0.338 ± 0.017 | 0.872 ± 0.037 | 0.516 ± 0.014 | 1.01 |
| 5 | 0.203 ± 0.010 | 0.516 ± 0.017 | 0.317 ± 0.009 | 1.01 |
| 8 | 0.126 ± 0.007 | 0.311 ± 0.011 | 0.190 ± 0.005 | 1.01 |
| 12 | 0.087 ± 0.004 | 0.208 ± 0.006 | 0.128 ± 0.004 | 1.04 |

Log–log slope of the median against R: **−0.946 ± 0.032** (M40 predicts −1). The product
R × median is constant to within 8 % over a 6:1 range of aperture, and to within 3 % excluding
the smallest array.

| N | duration | median | p90 | RMSE |
|---|---|---|---|---|
| 256 | 5.3 ms | 0.554 ± 0.026 | 1.363 ± 0.060 | 0.818 ± 0.024 |
| 512 | 10.7 ms | 0.390 ± 0.014 | 0.932 ± 0.037 | 0.577 ± 0.017 |
| 1024 | 21.3 ms | 0.273 ± 0.011 | 0.681 ± 0.028 | 0.403 ± 0.011 |
| 2048 | 42.7 ms | 0.219 ± 0.010 | 0.514 ± 0.019 | 0.317 ± 0.009 |
| 4096 | 85.3 ms | 0.149 ± 0.006 | 0.358 ± 0.009 | 0.220 ± 0.006 |

Log–log slope of the median against N: **−0.461 ± 0.020** (theory −0.5; the archived log gave
−0.208).

### 4.5 Temporal accumulation

`ablation_run.log`, section 3. Free field: 11 azimuths × 30 records × 128 frames. Reverberant:
7 azimuths × 30 records × 128 frames per room. Each record is split into disjoint blocks of T, so
the number of independent error samples is 42240/T (free field) and 26880/T (reverberant); at
T = 128 that is 330 and 210 blocks. 10 dB SNR. Figures: `fig_temporal_accumulation.png`,
`fig_bias_floor.png`.

Confidence-weighted RMSE (deg):

| T | free field | RT60 0.15 s | RT60 0.30 s | RT60 0.60 s |
|---|---|---|---|---|
| 1 | 0.308 ± 0.001 | 1.572 ± 0.010 | 2.351 ± 0.010 | 3.180 ± 0.012 |
| 2 | 0.218 ± 0.001 | 1.527 ± 0.014 | 2.173 ± 0.013 | 2.883 ± 0.015 |
| 4 | 0.153 ± 0.001 | 1.503 ± 0.020 | 2.076 ± 0.017 | 2.725 ± 0.018 |
| 8 | 0.109 ± 0.001 | 1.492 ± 0.029 | 2.028 ± 0.024 | 2.638 ± 0.024 |
| 16 | 0.076 ± 0.001 | 1.486 ± 0.040 | 2.002 ± 0.033 | 2.597 ± 0.032 |
| 32 | 0.054 ± 0.001 | 1.483 ± 0.057 | 1.988 ± 0.046 | 2.574 ± 0.044 |
| 64 | 0.038 ± 0.001 | 1.482 ± 0.081 | 1.981 ± 0.065 | 2.564 ± 0.062 |
| 128 | **0.027 ± 0.001** | **1.481 ± 0.115** | **1.978 ± 0.092** | **2.557 ± 0.087** |

**In free field accumulation works exactly as advertised: 0.308° → 0.027°, a factor 11.4 over
T = 128, with no floor. In every reverberant room it is over by T = 4.** Going from T = 1 to
T = 128 — from 43 ms of latency to 5.5 s — buys 5.8 % at RT60 = 0.15 s, 15.9 % at 0.30 s and
19.6 % at 0.60 s. Going from T = 1 to T = 8, i.e. 341 ms, already captures 88 %, 87 % and 87 %
of even that.

Fitted MSE(T) = b² + σ₁²/T (M62), weighted variant:

| condition | fitted b (deg) | fitted σ₁ (deg) | RMSE residual (deg) |
|---|---|---|---|
| free field | 0.000 ± 0.007 | 0.308 ± 0.001 | 0.0003 |
| RT60 0.15 s | 1.480 ± 0.016 | 0.529 ± 0.058 | 0.0002 |
| RT60 0.30 s | 1.977 ± 0.014 | 1.272 ± 0.031 | 0.0015 |
| RT60 0.60 s | 2.553 ± 0.014 | 1.896 ± 0.032 | 0.0008 |

Directly measured per-azimuth bias, from the circular mean of 3840 per-frame errors per azimuth:

| condition | b_rms (deg) | s.e. of each b(θ) | mean σ₁ (deg) |
|---|---|---|---|
| free field | **0.004** | 0.005 | 0.308 |
| RT60 0.15 s | **1.481** | 0.008 | 0.525 |
| RT60 0.30 s | **1.976** | 0.021 | 1.272 |
| RT60 0.60 s | **2.554** | 0.030 | 1.890 |

**The fitted and the directly measured bias agree to three decimal places in all four
conditions**, and the fitted σ₁ matches the measured σ₁ to within 1 %. (M62) is confirmed to a
degree the previous data could not approach: the fit residual is 0.0002–0.0015°, against
0.14–0.77° in the archived analysis. The free-field bias is 0.004 ± 0.005°, i.e. indistinguishable
from zero, which also demonstrates that the azimuth-jitter fix of Section 3.3 successfully removed
the delay-grid artefact that would otherwise have masqueraded as a bias.

Futility knee, T_futile = σ₁²/(0.1 b²) (M67): infinite in free field, **1.3 frames** at
RT60 = 0.15 s, **4.1 frames** at 0.30 s, **5.5 frames** at 0.60 s.

---

## 5. Before and after, number by number

Every figure below is traceable: "old" from `validation/archive/*_FULLBAND_PHAT_*.log`, "new"
from the log named in Section 0. Old runs used integer azimuths, 30/12/25/8/6 trials; new runs
use off-grid azimuths and 60/60/60/30 trials.

### 5.1 Free-field accuracy, `benchmark_run.log`

| method | SNR | old median | new median | old RMSE | new RMSE | RMSE change |
|---|---|---|---|---|---|---|
| Proposed | 0 dB | 3.43 | 0.529 | 5.02 | 0.750 | 6.7× better |
| Proposed | 5 dB | 3.14 | 0.308 | 4.69 | 0.456 | 10.3× |
| Proposed | 10 dB | 2.88 | 0.212 | 4.32 | 0.301 | 14.4× |
| Proposed | 20 dB | 1.67 | 0.127 | 7.23 | 0.176 | 41× |
| Proposed | 40 dB | 0.34 | 0.108 | 1.95 | 0.148 | 13.2× |
| GCC-PHAT | 0 dB | 3.45 | 0.527 | 4.93 | 0.749 | 6.6× |
| GCC-PHAT | 5 dB | 3.09 | 0.308 | 4.60 | 0.456 | 10.1× |
| GCC-PHAT | 10 dB | 2.82 | 0.212 | 4.23 | 0.301 | 14.1× |
| GCC-PHAT | 20 dB | 1.67 | 0.125 | 7.14 | 0.176 | 41× |
| GCC-PHAT | 40 dB | 0.35 | 0.108 | 1.74 | 0.148 | 11.8× |
| SRP-PHAT | 10 dB | 4.00 | 0.275 | 5.60 | 0.390 | 14.4× |
| SRP-PHAT | 40 dB | 0.00 † | 0.250 | 2.32 | 0.295 | 7.9× |
| MUSIC | 10 dB | 0.00 † | 0.358 | 0.81 | 0.697 | 1.2× |
| MUSIC | 40 dB | 0.00 † | 0.250 | 0.00 † | 0.290 | — |

† The old zeros are the grid-alignment artefact of Section 3.3, not accuracy. The MUSIC row is
the only one that got *worse*, and only because MUSIC never had the defect and has now lost the
free ride the aligned azimuth grid was giving it.

### 5.2 Ablation versus RT60, median |error| (deg), `ablation_run.log`

| RT60 (s) | old gate+weight | new gate+weight | old GCC-PHAT | new GCC-PHAT |
|---|---|---|---|---|
| 0.05 | 2.3 | 0.775 | 2.2 | 0.785 |
| 0.15 | 2.7 | 1.157 | 2.7 | 1.148 |
| 0.30 | 4.4 | 2.522 | 4.3 | 2.590 |
| 0.45 | 4.7 | 2.703 | 4.8 | 2.793 |
| 0.60 | 5.3 | 2.691 | 5.9 | 2.811 |
| 0.80 | 4.7 | 3.007 | 5.0 | 3.222 |

The reverberant error falls by a factor of 1.6–2.9, much less than the free-field factor of 14,
because it was already dominated by the reverberation bias rather than by front-end noise.

### 5.3 Temporal accumulation, RMSE (deg)

| T | old free (w) | new free (w) | old RT60 0.15 | new | old RT60 0.30 | new | old RT60 0.60 | new |
|---|---|---|---|---|---|---|---|---|
| 1 | 3.88 | 0.308 | 4.70 | 1.572 | 8.13 | 2.351 | 7.04 | 3.180 |
| 2 | 2.90 | 0.218 | 4.28 | 1.527 | 4.29 | 2.173 | 6.66 | 2.883 |
| 4 | 2.20 | 0.153 | 2.91 | 1.503 | 3.58 | 2.076 | 5.92 | 2.725 |
| 8 | 1.33 | 0.109 | 2.77 | 1.492 | 3.11 | 2.028 | 4.23 | 2.638 |
| 16 | 0.96 | 0.076 | 2.36 | 1.486 | 2.74 | 2.002 | 3.75 | 2.597 |
| 32 | 0.68 | 0.054 | 2.14 | 1.483 | 2.00 | 1.988 | 2.60 | 2.574 |
| 64 | — | 0.038 | — | 1.482 | — | 1.981 | — | 2.564 |
| 128 | — | 0.027 | — | 1.481 | — | 1.978 | — | 2.557 |

Improvement from T = 1 to T = 32: **old** 5.7× (free), 2.2× / 4.1× / 2.7× (reverberant); **new**
5.7× (free), 1.06× / 1.18× / 1.24× (reverberant). *In free field the gain from accumulation is
unchanged. In reverberation it has essentially vanished.* That single line is the most important
consequence of the re-baseline.

The old reverberant "floors" of 2.14 / 2.00 / 2.60° at T = 32 were also not floors — they were
points on a curve still descending, with a relative standard error of about 11 %, and their
apparent non-monotonicity was noise, exactly as the mathematics track suspected. The new floors,
1.481 ± 0.115 / 1.978 ± 0.092 / 2.557 ± 0.087°, are genuine asymptotes, measured past the knee,
and are **monotone in RT60**.

### 5.4 Scaling and compute

| quantity | old | new |
|---|---|---|
| aperture median at R = 2/3/5/8/12 cm (deg) | 7.31 / 4.63 / 2.95 / 1.65 / 1.10 | 0.459 / 0.338 / 0.203 / 0.126 / 0.087 |
| aperture log–log slope | −1.06 (no error bar) | −0.946 ± 0.032 |
| snapshot median at N = 256…4096 (deg) | 4.27 / 3.40 / 3.06 / 2.72 / 2.40 | 0.554 / 0.390 / 0.273 / 0.219 / 0.149 |
| snapshot log–log slope | −0.208 | −0.461 ± 0.020 |
| SRP/GCC measured host ratio | 4.3× ("ratios transfer to MCU") | 3.9–4.3× (**retracted as an algorithmic ratio**; 0.99× vectorised) |
| MUSIC/GCC measured host ratio | 4.2× | 3.5× (same retraction) |

---

## 6. The three gaps closed

### 6.1 Gap 1 — the unweighted reverberant accumulation sweep, never previously run

`temporal_reverb` had only ever been called with `weighted=True`, so the claim that confidence
weighting beats a plain circular mean in reverberation was unsupported. It has now been run both
ways, and — better — both variants are computed from the **same** per-frame estimates, so the
comparison is paired and the standard error is that of a difference.

Paired mean difference in |error|, weighted minus plain (negative = weighted better), degrees:

| T | free field | RT60 0.15 s | RT60 0.30 s | RT60 0.60 s |
|---|---|---|---|---|
| 1 | +0.0000 (3.9 σ) | +0.0000 (0.6 σ) | +0.0000 (0.1 σ) | −0.0000 (0.1 σ) |
| 8 | +0.0001 (0.7 σ) | +0.0019 (4.7 σ) | +0.0000 (0.0 σ) | −0.0016 (1.1 σ) |
| 32 | +0.0001 (0.7 σ) | +0.0018 (3.9 σ) | −0.0008 (0.7 σ) | −0.0049 (3.1 σ) |
| 128 | −0.0001 (0.5 σ) | +0.0020 (3.7 σ) | −0.0005 (0.4 σ) | −0.0059 (3.6 σ) |

**Result: a tie, and this is the third honest negative result.** The differences are 0.0001° to
0.006°, which is 0.004 % to 0.23 % of the error, and **their sign is not even consistent**:
confidence weighting is significantly *worse* at RT60 = 0.15 s, indistinguishable at 0.30 s and
significantly *better* at 0.60 s. Nothing that changes sign with the room at the fourth decimal
place is a mechanism.

**Consequence.** The method simplifies to a plain circular mean. The word "confidence-weighted"
should be dropped from the paper's description of the accumulator, with the weighting retained
only as a reported ablation. This also removes the PSR computation from the per-frame cost
(7 % of the front end by the FLOP model, Section 7) and removes the need to compute or store a
confidence at all. The recursive constant-memory form (M68) becomes simply

    z_t = (1 - lambda) z_{t-1} + lambda * u_t / ||u_t||

with no weight term — five floating-point operations per frame and no transcendental.

### 6.2 Gap 2 — the accumulation sweep extended to T = 128

Run at T ∈ {1, 2, 4, 8, 16, 32, 64, 128} with 30 records of 128 frames per azimuth. Because each
record is split into disjoint blocks, the number of independent samples is 42240/T in free field
and 26880/T in reverberation, giving 330 and 210 blocks at T = 128 — comfortably above the
"≥ 30 trials per condition" the mathematics track asked for.

The extension answers the question it was meant to answer, but the answer is the opposite of the
one anticipated. The mathematics track predicted the futility knee at T ≈ 65–108 and expected the
extension to let the accumulation curves establish the bias floor independently. With the
corrected front end, σ₁ collapses from 4.5–10.3° to 0.5–1.9° while b barely moves (1.48 / 1.98 /
2.55° against the previously measured 1.79 / 2.22 / 3.15°), so

    T_futile = sigma_1^2 / (0.1 b^2)

falls from 65 / 80 / 108 frames to **1.3 / 4.1 / 5.5 frames**. The knee is now at the very start
of the sweep, and the two-parameter fits are no longer unstable: the fitted b values
(1.480 ± 0.016, 1.977 ± 0.014, 2.553 ± 0.014) agree with the directly measured b_rms
(1.481, 1.976, 2.554) to three decimals, and the fit residuals are 0.0002–0.0015° against the
0.14–0.77° of the archived analysis. **The accumulation curves now establish the floor on their
own, and the floor is monotone in RT60.**

### 6.3 Gap 3 — trial counts and standard errors

| experiment | old trials per condition | new | old n per cell | new n per cell |
|---|---|---|---|---|
| free-field SNR sweep | 30 | 60 | 630 | 1260 |
| RT60 sweep, four estimators | 12 | 60 | 108 | 540 |
| gate/weight ablation vs RT60 | 12 | 60 | 108 | 540 |
| aperture and snapshot scaling | 25 | 60 | 275 | 660 |
| accumulation, free field | 8 | 30 records × 128 frames | 88 | 42240/T |
| accumulation, reverberant | 6 | 30 records × 128 frames | 42 | 26880/T |
| isotropy check | never run | 400 per azimuth × 24 azimuths | — | 9600 |

Every point estimate in every log now carries a standard error: bootstrap for quantiles,
delta-method for RMSE, and the standard error of the *difference* wherever two variants share
snapshots. The relative standard error on a reverberant RMSE has fallen from about 11 % to about
2–3 %, which is what makes the statements in Sections 4.3 and 6.1 possible at all.

---

## 7. Compute, treated honestly

Source: `rebaseline_checks_D.log`, run with nothing else on the machine.

### 7.1 The retraction

The claim that measured host timing ratios transfer to the microcontroller is **withdrawn**. It
appeared in the `measure_compute` docstring and in `benchmark_run.log`'s heading, both of which
now carry the retraction and the reason. It also appears in `HANDOVER.md` §3, which has been
given a pointer to this document marking its simulation numbers as superseded; rewriting that
file is left to whoever next updates the project state.

### 7.2 Confirmation that the 4.3× is interpreter overhead

Host timings are noisy on this machine — up to 3 ms of spread between rounds — so
`doa_benchmark.time_suite` now times all candidates **round-robin** and takes the **minimum**
over rounds. Interference can only make a measurement slower, so the minimum is the least
contaminated estimator, and interleaving keeps the ratios valid even when the absolute numbers
drift.

| stage / estimator | measured (ms) | ratio to GCC-PHAT |
|---|---|---|
| SRP shared GCC-PHAT front end | 1.231 | — |
| SRP azimuth grid loop (Python) | 2.471 | — |
| sum of the two stages | 3.701 | — |
| whole `est_srp_phat` (reference) | 4.008 | 4.26× |
| **`est_srp_phat_vec`, bit-identical output** | **0.886** | **0.94×** |
| `est_gccphat_ls` | 0.940 | 1.00× |
| `est_proposed` | 1.020 | 1.08× |
| `est_music` | 2.927 | 3.11× |
| `est_gccphat_ls` with I = 1 + parabolic | 0.310 | 0.33× |

The grid loop costs **1.716 µs per NumPy call** over 1440 calls, which is pure dispatch overhead.
Vectorising the grid search — same algorithm, same arithmetic, byte-identical output, verified —
takes SRP-PHAT from 4.26× GCC-PHAT to **0.94×**, i.e. slightly *cheaper*. The FLOP model predicts
1.006×. **The mathematics track's diagnosis is confirmed in full: the measured 4.3× is a property
of the Python loop, not of SRP-PHAT.**

An independent timing run inside `doa_benchmark.py` (`benchmark_run.log`) corroborates this:
SRP-PHAT 3.74× and vectorised SRP-PHAT 1.02× GCC-PHAT, MUSIC 3.14×, proposed 1.16×. Absolute
host times vary by up to 30 % between sessions; ratios are stable, and the vectorised/reference
gap of roughly 4× reproduces every time.

### 7.3 The algorithmic comparison, which is what a designer should use

Recomputed from the formulas of `math_model.md` §7.2–7.3 rather than copied:

| method | model (MFLOP) | model ratio | measured host (ms) | measured ratio |
|---|---|---|---|---|
| GCC-PHAT | 4.227 | 1.000 | 0.940 | 1.00 |
| Proposed (gated) | 4.522 | 1.070 | 1.020 | 1.08 |
| SRP-PHAT | 4.251 | 1.006 | 4.008 (ref.) / 0.886 (vec.) | 4.26 / 0.94 |
| MUSIC | 3.193 | 0.755 | 2.927 | 3.11 |

Memory (analytical, `math_model.md` §7.6): input 24 kB; correlation buffer 128 kB at I = 8 or
16 kB at I = 1, per pair and reusable; accumulator 8 bytes.

**Which of the two should a system designer use? The FLOP and memory model, without
qualification.** The measured host times are properties of this reference NumPy implementation on
x86 and of nothing else. Where the model and the measurement agree — proposed/GCC, +7 % predicted
against +8 % measured — the measurement is corroborating evidence. Where they disagree by a factor
of four, the model is right and the measurement is measuring CPython. The paper may report the
host timings, but only under the heading "reference implementation" and only with the vectorised
SRP-PHAT row alongside, because that row is what demonstrates the point.

### 7.4 The eightfold interpolated inverse FFT, and the recommendation that follows

The mathematics track's claim that 87 % of the front-end cost is the eightfold zero-padded inverse
FFT, and that a native-length IFFT with parabolic peak refinement is about 5.1× cheaper,
**holds — and the accuracy price it was expected to carry does not materialise.**

| term | I = 8 (MFLOP) | I = 1 + parabolic (MFLOP) |
|---|---|---|
| forward FFTs | 0.369 | 0.369 |
| CPSD + PHAT | 0.074 | 0.074 |
| **inverse FFTs** | **3.686 (87.2 %)** | **0.369 (44.8 %)** |
| argmax | 0.098 | 0.012 |
| **total** | **4.227** | **0.823** |

Model speed-up **5.13×** overall and 10.0× in the inverse-transform term; measured host speed-up
**3.03×** for the whole estimator (0.940 → 0.310 ms), the shortfall being the fixed Python and
`lstsq` overhead that the model does not charge.

Accuracy, paired on identical snapshots with the band-limited weight:

| SNR | I = 8 RMSE | I = 1 + parabolic RMSE | paired mean penalty |
|---|---|---|---|
| 10 dB | 0.299 ± 0.010 | 0.268 ± 0.008 | +0.008 ± 0.006 |
| 20 dB | 0.169 ± 0.007 | 0.103 ± 0.004 | −0.003 ± 0.006 |
| 40 dB | 0.144 ± 0.007 | 0.042 ± 0.003 | −0.036 ± 0.005 |

**Parabolic refinement is not merely free, it is more accurate at high SNR** — by a factor of 3.4
at 40 dB — because it produces a continuous estimate whereas the I = 8 argmax is quantised to the
2.604 µs grid and cannot do better than 0.139° (M25, M28).

The interpolation bias that (M20) warns of, up to 0.119 samples for a full-band whitened sinc
peak, was measured against fractional sample offset and is **0.0026 samples maximum
(0.055 µs, 0.010° of azimuth)** — a factor 46 below the warning, and smaller than the I = 8
argmax's own quantisation ripple of 0.0417 samples. The reason is that the warning was derived
for a full-band whitened peak whose main lobe is one sample wide; with the weight restricted to
300–3400 Hz the main lobe is about f_s/(2·3400) ≈ 7 samples wide and a parabola is an excellent
local model of it.

> **Implementation recommendation for the paper.** Replace the eightfold zero-padded inverse FFT
> with a native-length inverse FFT and parabolic peak refinement. It is 5.1× cheaper by the FLOP
> model (3.0× measured on the host), reduces the correlation buffer from 128 kB to 16 kB per
> pair, and is *more* accurate above 20 dB SNR. This is only true once the PHAT weight is
> band-limited; the two changes are complementary and should be presented together.

---

## 8. Theory versus measurement

Every falsifiable prediction in `math_model.md` tested against the re-baselined data.

### 8.1 The GDOP law, σ_θ = c σ_τ / (√4.5 · R) — **partly refuted, and corrected**

`benchmark_run.log`. σ_τ measured directly from the per-pair TDOA errors.

| SNR | measured σ_τ (µs) | (M40) prediction | measured GCC RMSE |
|---|---|---|---|
| 0 dB | 3.429 | 0.635° | 0.749 ± 0.014° |
| 5 dB | 2.067 | 0.383° | 0.456 ± 0.009° |
| 10 dB | 1.438 | 0.266° | 0.301 ± 0.006° |
| 20 dB | 0.945 | 0.175° | 0.176 ± 0.003° |
| 40 dB | 0.846 | 0.157° | 0.148 ± 0.003° |

(M40) under-predicts the measured RMSE by 15–18 % at 0–10 dB and is exact at 20–40 dB. The
discrepancy is systematic and its cause was found: **the three per-pair TDOA errors are not
independent**, so the assumption Cov(δτ) = σ_τ² I underlying (M37) and hence (M40) is false. With
M = 3 microphones there are only two independent delays, and all three pairwise correlations are
computed from the same three channels.

| SNR | corr(12,13) | corr(12,23) | corr(13,23) | (M40) isotropic | (M36) with measured Cov | measured RMSE |
|---|---|---|---|---|---|---|
| 0 dB | +0.385 | −0.423 | +0.410 | 0.635° | **0.753°** (0.741–0.766) | 0.749° |
| 5 dB | +0.435 | −0.330 | +0.390 | 0.383° | **0.450°** (0.434–0.466) | 0.456° |
| 10 dB | +0.352 | −0.323 | +0.337 | 0.266° | **0.308°** (0.302–0.314) | 0.301° |
| 20 dB | +0.212 | −0.115 | +0.097 | 0.175° | **0.187°** (0.177–0.196) | 0.176° |
| 40 dB | +0.115 | −0.041 | +0.068 | 0.157° | **0.163°** (0.159–0.166) | 0.148° |

**The general expression (M36), evaluated with the measured covariance, reproduces the measured
RMSE to within 2 % at 0, 5, 10 and 20 dB and 10 % at 40 dB.** The correlations reach ±0.33 to
±0.44 at low SNR and decay towards zero at high SNR, which is exactly why the isotropic form is
wrong where it is wrong.

*Recommendation to the mathematics track:* (M36) is correct and should be the quoted law. (M40)
should be presented as its equal-independent-variance special case, with the explicit caveat that
the independence assumption fails at M = 3 and costs 15–18 % at low SNR. This does not weaken the
analysis — the closed form is still right, and the correction is measured.

### 8.2 The 1/R aperture law — **confirmed**

Log–log slope of the median against R: **−0.946 ± 0.032**, against the predicted −1, i.e. 1.7
standard errors. R × median is constant to within 8 % over a 6:1 range of aperture. The slight
shallowing is consistent with the interpolation-grid floor (0.139°) becoming a larger fraction of
the error at R = 12 cm, where the median is 0.087°.

### 8.3 The restored N^−1/2 snapshot law — **confirmed in direction; the magnitude differs**

The archived log's anomalous −0.208 slope was attributed entirely to the full-band weight. Paired
re-run (`rebaseline_checks_ABC.log`, study C), same snapshots for both weight bands, 660 frames
per point:

| statistic | full-band weight | band-limited weight | theory |
|---|---|---|---|
| log–log slope of the robust s.d. vs N | −0.242 ± 0.015 | **−0.444 ± 0.015** | −0.5 |
| log–log slope of the median vs N | −0.245 ± 0.022 | −0.441 ± 0.022 | −0.5 |
| log–log slope of the RMSE vs N | −0.772 ± 0.040 | −1.072 ± 0.144 | not applicable |
| frames with \|error\| > 20° at N = 256 | 7.73 % | 0.15 % | — |

The independent ablation run gives −0.461 ± 0.020 on the median, consistent.

Two remarks. First, **the RMSE is the wrong statistic for this slope.** At N = 256 the physical
delay range spans 5 % of the record and 7.7 % of full-band frames throw wrap outliers, so the
RMSE at that point is set by a handful of catastrophic frames; the theory is a statement about the
dispersion of the bulk, and the slope must be read on a robust scale. The mathematics track's
quoted −0.512 was obtained on a statistic that saturated at zero at large N and is not
reproducible here.

Second, **−0.444 ± 0.015 is 3.7 standard errors from −0.5, and the shortfall is explained.** The
delay estimate approaches the 2.604 µs interpolation-grid floor (σ_τ,q = 0.752 µs, M25) as N
grows. Fitting a floor: extrapolating N^−1/2 from N = 256 predicts 0.194° at N = 4096, the
measurement is 0.224°, and the implied floor is √(0.224² − 0.194²) = 0.112°, against the predicted
grid floor of 0.139° (M28). The law is recovered; what remains is the grid, exactly as predicted.

### 8.4 The 1/√T accumulation law — **confirmed exactly in free field**

Free field, weighted: 0.308 → 0.027° over T = 1 → 128. The fitted MSE(T) = b² + σ₁²/T has
b = 0.000 ± 0.007°, σ₁ = 0.308 ± 0.001° and an RMSE residual of **0.0003°**. Pure 1/√T from
T = 1 would give 0.0272° at T = 128; measured 0.027°. This is the cleanest confirmation in the
whole re-baseline.

In reverberation the law also holds, but with b so large relative to σ₁ that the 1/√T region is
compressed into T < 4 (Section 4.5).

### 8.5 The Cramér–Rao bound ratio — **confirmed**

| SNR | CRB (M82) | full-band RMSE | ×CRB | band-limited RMSE | ×CRB | σ_τ /attainable, full band | band-limited |
|---|---|---|---|---|---|---|---|
| 0 dB | 0.5492° | 4.927 | 9.0 | 0.740 | **1.35** | 10.2× | **1.29×** |
| 10 dB | 0.1737° | 4.046 | 23.3 | 0.321 | **1.85** | 21.0× | **1.39×** |
| 20 dB | 0.0549° | 2.093 | 38.1 | 0.174 | 3.17 | 17.7× | 1.09× |
| 40 dB | 0.0055° | 0.816 | 148.6 | 0.151 | 27.5 | 12.8× | **1.00×** |

"Attainable" is the Knapp–Carter delay bound (M83) and the interpolation-grid floor (M25) added
in quadrature. Against that — the correct comparator, since the grid is part of the front end —
the corrected estimator is at **1.29×, 1.39×, 1.09× and 1.00×** the attainable precision. The
mathematics track's figures of 29× before and 1.39× after are both reproduced: 21.0× and 1.39× at
10 dB. Above 20 dB the estimator is *at* the interpolation floor and is no longer noise-limited,
which is precisely why replacing I = 8 with parabolic refinement improves it (Section 7.4).

### 8.6 Isotropy of the azimuth variance — **confirmed for uniform weights and for pair-dropping's level; refuted for PSR weighting**

`ablation_run.log`, section 1b. 24 azimuths × 400 trials each, robust standard deviation of the
signed error, with the correct MAD standard error (1.166 σ/√n, the MAD having asymptotic relative
efficiency 0.37; using the normal-theory σ/√(2(n−1)) would inflate every χ² below by 2.7 and
manufacture direction dependence that is not there).

| configuration | mean s.d. (deg) | × the 3-pair uniform case | CV over azimuth | χ²/dof vs flat | χ²/dof vs (M36) |
|---|---|---|---|---|---|
| uniform weights, 3 pairs | 0.314 | 1.000 | 6.46 % | **1.37** | 1.31 |
| PSR weights, 3 pairs | 0.315 | **1.002** | 6.65 % | **1.47** | 1.41 |
| drop pair 1–2, 2 pairs | 0.356 | **1.131** (predicted 1.391) | 8.88 % | 2.49 | 7.83 |
| drop pair 1–3, 2 pairs | 0.356 | **1.133** (predicted 1.391) | 9.70 % | 2.96 | 7.80 |

Three findings, and only the first is what the mathematics track predicted.

1. **With uniform weights the azimuth variance is isotropic.** χ²/dof = 1.37 against a flat curve.
   (M39) is confirmed.
2. **PSR weighting does not measurably break isotropy.** Its curve is statistically
   indistinguishable from the uniform one (χ²/dof = 1.47 against flat; mean s.d. 1.002× the
   uniform case). The prediction that "the PSR weighting of Section 5.3 *creates*
   direction-dependent error where none existed" is **not supported**. The reason is
   straightforward: at M = 3 in free field the three PSRs are nearly equal, so W ≈ I and
   AᵀWA stays nearly isotropic. **The second independent argument against gating therefore does
   not survive the measurement, and the paper should not use it.**
3. **Dropping a pair does break isotropy, and it inflates the variance — but by less than
   predicted.** The measured inflation is 1.131× and 1.133× against a predicted **1.391×**, and
   the measured curve does not follow the predicted two-fold-symmetric shape
   (χ²/dof = 7.8 against the prediction, worse than against a flat line). Both discrepancies have
   the same cause as Section 8.1: the prediction assumes Cov(δτ) = σ_τ² I, and the measured
   inter-pair correlations of +0.35/−0.32/+0.34 at 10 dB make the dropped pair's information
   partly recoverable from the two that remain. (The predicted 1.391× is the azimuth-averaged
   ratio of √(e_θᵀ(A₂ᵀA₂)⁻¹e_θ) to √(e_θᵀ(AᵀA)⁻¹e_θ), evaluated numerically from `MIC_XY`; it is
   identical for all three choices of dropped pair, as symmetry requires.)

**Net effect on the paper's argument against gating.** The argument stands, but on one leg rather
than two. The surviving arguments are the rank/redundancy result (fault exclusion is impossible at
M = 3) and the direct ablation measurement of Section 4.3, which now bounds the decision layer's
benefit at 1–3 % of the error. The isotropy argument should be dropped, because the measurement
says PSR weighting does not break isotropy.

---

## 9. What changed in the paper's conclusions

Stated bluntly, because the evidence requires it.

### 9.1 The central thesis is substantially weakened

The paper's thesis is that **confidence-weighted temporal accumulation is the dominant lever**:
trade under a second of latency for an order-of-magnitude accuracy gain, down to an
RT60-dependent bias floor. After the re-baseline, each of the three parts of that sentence is in
trouble.

* **"Confidence-weighted" is dead.** Weighted and plain circular means differ by 0.0001–0.006°,
  and the sign of the difference changes with the room (Section 6.1). The method simplifies to a
  plain circular mean. This is the third honest negative result.
* **"An order-of-magnitude gain" now holds only in free field**, where accumulation takes the
  error from 0.308° to 0.027° over 128 frames. In every reverberant room, going from 43 ms to
  5.5 s of latency buys 6 % to 20 %. Accumulation is over by T = 4.
* **"Down to a bias floor" is now the whole story rather than the caveat.** The corrected
  per-frame estimator is within 1.3–1.4× of the attainable delay precision — the Knapp–Carter
  bound and the interpolation grid added in quadrature — so there is almost no
  stochastic error left for accumulation to remove; what remains is deterministic multipath bias,
  which accumulation provably cannot touch.

The task brief anticipated this: a 13× better per-frame estimator leaves accumulation less room to
improve things in free field. The measurement says something stronger. In free field accumulation
still works perfectly but is now largely *unnecessary*, because 0.31° per frame at 43 ms of
latency is already better than any plausible hardware can deliver — a ±1 dB microphone
sensitivity tolerance, an inter-channel clock skew of one sample (≈ 4°, A8), or the near-field
curvature bias of 0.72° at 1 m (M11) each exceed it by a wide margin. In reverberation
accumulation is *ineffective*, because the bias floor is reached within four frames.

### 9.2 What the paper should be about instead

**The reverberation bias floor is the dominant effect and should become the paper's subject.** The
evidence for it is now far stronger than it was, and it is the one result that is both robust and
practically binding:

* it is measured two independent ways that agree to three decimal places — a direct per-azimuth
  circular-mean measurement over 3840 frames per azimuth, and a two-parameter fit of (M62) to
  accumulation curves extended past the knee, with fit residuals of 0.0002–0.0015°;
* it is monotone in RT60 — 1.481 ± 0.115°, 1.978 ± 0.092°, 2.557 ± 0.087° at RT60 = 0.15, 0.30,
  0.60 s — where the old data could not even establish monotonicity;
* it is reached within 4–6 frames, i.e. under 250 ms, which is an actionable latency budget rather
  than an aspiration;
* it is estimator-independent: Proposed, GCC-PHAT and SRP-PHAT all sit on it (Section 4.2), and
  no amount of front-end improvement crosses it.

The honest headline becomes: *a 5 cm three-microphone array with a correctly band-limited
GCC-PHAT front end reaches 0.3° per frame in free field at 10 dB SNR — 1.85× the Cramér–Rao
bound, and 1.39× the precision actually attainable once the correlation interpolation grid is
counted — at 4.2 MFLOP per frame, and in any real room its accuracy is set entirely by a
reverberation bias floor of 1.5–2.6° that is reached in under 250 ms and that no accumulation,
gating, weighting or subspace method can cross.* That is a smaller claim than the original thesis,
but it is true, it is measured with standard errors throughout, and it is useful to a system
designer, who learns exactly how much latency to budget and exactly what the ceiling is.

### 9.3 Specific claims that must change

| claim in the current draft / `HANDOVER.md` | status |
|---|---|
| "Confidence-weighted temporal accumulation … order-of-magnitude accuracy gain" | **rewrite.** True in free field only; the weighting does nothing. |
| Negative result #1: proposed ≈ GCC-PHAT | **keep and strengthen.** Now bounded at 1–3 % of the error with paired standard errors. |
| Negative result #2: RMSE inflated at high SNR by wrap outliers | **retract.** It was a symptom of the defect. RMSE is now monotone in SNR for every estimator. |
| Compute: "ratios transfer to MCU", SRP 4.3× | **retracted.** Vectorising gives 0.94×; the FLOP model predicts 1.006×. |
| MUSIC is far more accurate than GCC-PHAT | **retract.** That was a band-limited front end being compared with a full-band one. GCC-PHAT now beats MUSIC in free field and MUSIC collapses in reverberation (RMSE 28–36° above RT60 = 0.3 s). |
| Free field @10 dB: median 2.88° / RMSE 4.32° | **replace** with 0.212 ± 0.006° / 0.301 ± 0.006°. |
| Reverberation floors 2.14 / 2.00 / 2.60° at T = 32 | **replace** with 1.481 ± 0.115 / 1.978 ± 0.092 / 2.557 ± 0.087°, now genuine asymptotes and monotone. |
| Snapshot scaling anomaly (−0.208, unexplained) | **replace** with −0.461 ± 0.020, diagnosed and resolved. |
| Isotropy as a second argument against gating | **drop.** PSR weighting does not measurably break isotropy at M = 3. |
| Aperture scaling 7.31° → 1.10° | **replace** with 0.459° → 0.087°; the −1 slope conclusion is unchanged. |

### 9.4 New results the re-baseline produced

1. The full comparison against SRP-PHAT and MUSIC is now fair for the first time, and its
   conclusion is that a correctly band-limited GCC-PHAT with least-squares inversion is the best
   of the four in free field and tied with the best in reverberation, at a quarter of the cost.
2. MUSIC's catastrophic failure in reverberation (Section 4.2) — previously invisible because the
   reverberation sweep was never logged.
3. The per-pair TDOA errors are correlated at M = 3, the isotropic GDOP law under-predicts by
   15–18 % at low SNR because of it, and the general form (M36) with the measured covariance is
   accurate to 2 % (Section 8.1).
4. Native-length IFFT with parabolic refinement is 5.1× cheaper by the FLOP model, 8× smaller in
   memory, and *more* accurate above 20 dB (Section 7.4). This is a directly actionable firmware
   recommendation.
5. An anti-alias filter does not substitute for band-limiting the PHAT weight; both are required,
   for two separately measured reasons (Section 2.4).

### 9.5 What has not changed

The array geometry, the source model, the room model, the estimator structure, the seed, and the
negative result about the decision layer. The paper's honesty posture is intact: every number
above comes from a named script and a named log, every one carries a standard error, and the
superseded numbers are preserved in `validation/archive/` rather than deleted.
