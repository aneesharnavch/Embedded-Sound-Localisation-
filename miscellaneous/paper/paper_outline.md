
## Title (pick one / merge)
- **"Confidence-weighted temporal accumulation for accurate real-time direction-of-arrival estimation on a low-cost three-microphone array"**

**Section:** Audio Signal Processing and Transducers. 
**Topical issue:** Benchmarking Acoustics (check deadline dumbass).

---

## Abstract 

Real-time sound-source localization is increasingly wanted on tiny, low-power, low-cost edge devices—assistive hearing systems, wearable interfaces, robots, and distributed IoT sensors—where accurate direction-of-arrival (DoA) estimation must operate under severe constraints in computation, memory, and energy. While modern localization methods can achieve excellent accuracy, many rely on computationally expensive beamforming or subspace techniques that are impractical for battery-powered embedded platforms. We therefore ask how far a deliberately minimal system can go: three MEMS microphones (5 cm aperture) on a single ESP32-S3 microcontroller, running only lightweight generalized cross-correlation with phase transform (GCC-PHAT) time-delay estimation.

On such a small array, a single time frame yields modest azimuth accuracy (≈4° RMSE at 10 dB SNR, worse in reverberation), and we show that a per-frame confidence-gating layer—the intuitive fix—yields little significant improvement because three microphones provide virtually no spatial redundancy to exploit. Instead, the dominant lever is temporal: confidence-weighted accumulation of successive estimates reduces localization error approximately as 1/√T, reaching sub-degree RMSE in free field and ≈2° in a typical room (RT60 = 0.3 s) after ~0.9 s of accumulation, while requiring only constant memory and a few arithmetic operations per frame. We further characterize the accuracy–latency–compute–aperture trade-offs, expose the reverberation-induced bias floor that temporal accumulation cannot overcome, and validate the complete system on real hardware ([MEASURE] RMSE).

Compared with existing embedded DoA localization systems operating under similar computational and power budgets, the proposed platform achieves [BLANK] lower localization error / [BLANK]× lower computational cost / [BLANK]× higher energy efficiency while requiring only three microphones and a low-cost microcontroller. The result is a quantified design envelope for minimal real-time DoA sensors and demonstrates that, under severe resource constraints, exploiting time is substantially more valuable than increasing per-frame algorithmic complexity.

**Keywords:** sound source localization; direction of arrival; GCC-PHAT; microphone array;
embedded systems; real-time; edge computing; reverberation.

---

## 1. Introduction  
- The problem: real-time DoA/azimuth estimation is needed on cost-, power-, and size-constrained
  edge devices; motivate with concrete uses (assistive hearing, wake-word direction, robot/HRI, IoT).
- The tension: classic high-accuracy methods (SRP-PHAT grid search, MUSIC and other subspace methods)
  are compute-heavy and/or want many microphones; big arrays are expensive and bulky. [CITE]
- The gap this paper fills: nobody has cleanly quantified *how minimal you can go* — 3 mics, ~5 cm,
  a $-class MCU — and *where the accuracy actually comes from* once you're that minimal.
- State the honest thesis up front: on a minimal array the per-frame algorithm barely matters; the
  **temporal** dimension (accumulating cheap estimates over a short window) is what buys accuracy —
  and it has a hard reverberation floor.
- Contributions (bullet list, keep it modest and true):
  1. An open, ultra-low-cost 3-mic ESP32-S3 real-time DoA platform.
  2. A confidence-weighted temporal-accumulation estimator; the honest formalization of the device's
     "TDOA + decision + tracking" pipeline.
  3. A systematic characterization of the accuracy / latency / compute / aperture / reverberation
     trade-offs, including a **negative result** (per-frame confidence gating ≈ plain GCC-PHAT on 3 mics)
     and the reverberation-bias floor.
  4. Real-hardware validation against the same simulation harness.
- One paragraph: paper roadmap.

## 2. Background and related work  *(what to mention)*
- TDOA + GCC-PHAT: the standard cheap estimator; the PHAT weighting and its noise/reverb behavior. [CITE Knapp & Carter 1976]
- SRP-PHAT: steered-response power, robust but grid-search cost. [CITE DiBiase]
- Subspace methods (MUSIC): high accuracy, high cost, needs snapshots/calibration. [CITE Schmidt]
- Small/embedded arrays & edge DoA: prior low-cost / MCU localizers; what accuracy they report. [CITE]
- Temporal integration / tracking of DoA (recursive averaging, particle/Kalman trackers) — position
  our accumulation as the minimal, O(1)-memory member of this family. [CITE]
- Explicitly state what we do NOT claim: no new estimator theory; the contribution is the applied
  characterization and the platform. (This framing is what keeps it in "Technical & Applied" scope.)

## 3. System and hardware platform  *(what to mention)*
- Block diagram: 3 MEMS mics → [MEASURE preamp/ADC path, e.g. I2S] → ESP32-S3 → DoA output.
- Array geometry: equilateral triangle, circum-radius R = [MEASURE] cm (resolves full 360° azimuth).
  Include the measured mic coordinates and a photo of the board.
- Sampling: fs = [MEASURE] kHz per channel; snapshot length N = [MEASURE] samples (≈[MEASURE] ms).
- Firmware pipeline (real-time): capture → windowed FIR band-limiting → per-pair GCC-PHAT →
  gated weighted-LS azimuth → temporal accumulator. Note dual-core split, SRAM/CPU usage [MEASURE].
- Cost & BOM summary (Table): total ≈ $[MEASURE]; contrast with commercial arrays.
- Reproducibility pointer: repo + Zenodo DOIs.

## 4. Method  *(the section the old draft never had — be formal)*
- **4.1 Signal model.** Far-field plane wave, azimuth θ; per-mic delay τ_m = −(p_m·u)/c; define
  the array manifold and the TDOA for a pair. (One or two equations.)
- **4.2 Per-frame estimate.** GCC-PHAT cross-correlation per pair; TDOA = peak lag; pairwise
  least-squares for azimuth. Give the LS equation A u = b with A = p_i − p_j, b = −c·τ_ij.
- **4.3 Confidence gate + weighting (the "decision" layer).** Define per-pair confidence = peak-to-
  sidelobe ratio (PSR); reject pairs that are (a) physically infeasible (|τ| > d_ij/c) or (b) below a
  fraction of the best PSR; weight survivors by PSR in the LS. **State plainly it is a marginal effect
  on 3 mics** — Section 6 quantifies this; keep it as an ablation, not a headline.
- **4.4 Confidence-weighted temporal accumulation (the core).** Over a window of T frames, take the
  PSR-weighted **circular mean** of per-frame azimuths. Give the equation
  θ̂ = atan2(Σ w_t sin θ_t, Σ w_t cos θ_t). Argue: noise is independent across frames → averages as
  1/√T; reverberation multipath is fixed → a residual bias floor remains. Note O(1) memory, a few
  adds/frame → real-time on the MCU. Mention the recursive/online PID variant for moving sources.
- **4.5 Complexity.** Per-frame FLOPs/memory vs SRP-PHAT and MUSIC; why the proposed method is in the
  cheap tier (our measured ratio: proposed ≈ GCC-PHAT ≈ ¼ the cost of SRP/MUSIC).

## 5. Simulation study  *(setup + our real numbers + figure callouts)*
- **5.1 Setup.** Plane-wave + fractional-delay model; band-limited speech-like source (300–3400 Hz);
  additive noise to target SNR; image-source room model for reverberation (Sabine RT60→reflection).
  Fixed RNG seed → reproducible. Baselines: GCC-PHAT, SRP-PHAT, MUSIC. (Fig: geometry, SRP spectrum.)
- **5.2 Free-field accuracy vs SNR.** Report median/p90/RMSE table. Note median is monotone
  (≈3.4°→0.3° over 0→40 dB); RMSE is inflated at high SNR by rare wrap/ambiguity outliers on the small
  array — motivates temporal accumulation. (Fig: `fig_rmse_vs_snr`, `fig_error_cdf`, `fig_accuracy_matrix`.)
- **5.3 Reverberation.** Median error vs RT60; ≈2–3° in typical rooms (0.2–0.5 s), degrading beyond.
  (Fig: `fig_accuracy_vs_rt60`.)
- **5.4 Ablation of the decision layer.** gate/weight on–off vs RT60: differences are within noise →
  **the negative result.** (Fig: `fig_ablation_rt60`.) Interpret: no redundancy at M = 3.
- **5.5 Temporal accumulation (headline).** RMSE vs T tracks 1/√T; free field 3.96°→0.89° (T:1→20 @10 dB);
  reverberant floors ≈0.9°/2.0°/3.1° at RT60 0.1/0.3/0.6 s; weighted ≈ plain mean in free field, small
  gain in reverb. (Fig: `fig_temporal_accumulation`.)
- **5.6 Resource scaling.** Accuracy vs aperture (7.3°@2 cm → 1.1°@12 cm) and vs snapshot length
  (4.3°@5 ms → 2.4°@85 ms). Gives the design envelope. (Fig: `fig_resource_scaling`.)
- **5.7 Accuracy vs compute.** Pareto placing proposed/GCC in the cheap-and-good corner vs SRP/MUSIC.
  (Fig: `fig_pareto`.) Note timings are x86; only ratios transfer — real MCU latency is in Section 6.

## 6. Hardware validation  *(protocol + [MEASURE] results — the make-or-break section)*
- **6.1 Protocol.** Array on tripod; single loudspeaker at [MEASURE] m; azimuths every [MEASURE]° via
  printed protractor/turntable; ≥2 rooms (damped vs live) with RT60 estimated by [MEASURE method];
  sources: broadband + speech [+ alarm]. Ground-truth uncertainty ≈ [MEASURE]°. Clips run through the
  *same* estimators as simulation (`real_data.py`).
- **6.2 Measured accuracy.** Per-method, per-room median/p90/RMSE table [MEASURE]; measured error CDF
  overlaid on the simulated CDF to show agreement. Report the real temporal-accumulation curve [MEASURE].
- **6.3 Measured on-device cost.** Real per-estimate latency on ESP32-S3 (mean/median/p95) [MEASURE];
  real-time budget used; SRAM/CPU load [MEASURE]. **This replaces the old unsupported "10 µs" claim.**
- **6.4 Sim-vs-real agreement.** State honestly where they match and where the real world is worse
  (mic gain/phase mismatch, clock skew, self-noise), and whether real error sits at the predicted floor.

## 7. Discussion and limitations  *(be candid — this earns trust)*
- Azimuth-only, single source, horizontal plane; no elevation, no multi-source separation.
- Three mics → no spatial redundancy → per-frame gating can't help (the negative result); accuracy is
  aperture- and time-limited, not algorithm-limited.
- Reverberation-bias floor: temporal accumulation removes noise, not fixed multipath; a real ceiling.
- Latency/accuracy trade is only free for (quasi-)stationary sources; fast-moving sources cap usable T.
- Applications enabled (short): assistive hearing direction cue; wake-word DoA; optionally the
  "direction-vector-in-the-recording-metadata" idea as a *possible* use, clearly labeled speculative.

## 8. Conclusion  *(what to mention)*
- Restate the design envelope: what accuracy a 3-mic $-class real-time sensor can/can't reach, and why
  the win is temporal, not algorithmic.
- One line of future work: more mics for redundancy; dereverberation/precedence-effect gating to lower
  the floor; elevation via a non-planar array.

## Back matter
- **Data & code availability:** GitHub + Zenodo DOIs (existing records); note figures regenerate from
  `validation/` on Python 3.14 (numpy/scipy/matplotlib only).
- **Acknowledgements.** **Conflicts of interest:** none. **Funding:** [state].
- **References:** GCC-PHAT (Knapp & Carter), SRP-PHAT (DiBiase/Brandstein), MUSIC (Schmidt), a small-array
  / embedded-DoA survey, a DoA-tracking reference, image-source method (Allen & Berkley). [fill real cites]

---

### Figure inventory (already generated in `validation/figs/`)
| Fig | File | Section |
|-----|------|---------|
| Array geometry | `fig_geometry.png` | 5.1 |
| SRP spatial spectrum (pedagogical) | `fig_srp_spectrum.png` | 5.1 |
| RMSE vs SNR | `fig_rmse_vs_snr.png` | 5.2 |
| Error CDF | `fig_error_cdf.png` | 5.2 |
| Accuracy matrix (angle×SNR) | `fig_accuracy_matrix.png` | 5.2 |
| Accuracy vs RT60 | `fig_accuracy_vs_rt60.png` | 5.3 |
| Ablation (gate/weight) vs RT60 | `fig_ablation_rt60.png` | 5.4 |
| **Temporal accumulation (headline)** | `fig_temporal_accumulation.png` | 5.5 |
| Resource scaling (aperture, snapshot) | `fig_resource_scaling.png` | 5.6 |
| Accuracy vs compute (Pareto) | `fig_pareto.png` | 5.7 |
| Measured error CDF (real) | `fig_real_error_cdf.png` | 6.2 |
