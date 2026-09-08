# Scientific audit of the current draft

7 September 2026. This is a planning audit, not a replacement results paper. No original manuscript, recording, firmware, or simulation file was changed. Existing numerical results remain historical results of their documented implementation until the checks below are completed.

## The most consequential finding

The claimed reverberation floor is presently confounded with discretization of propagation time. In `validation/reverb_robustness.py`, arrival times are rounded to whole samples before the room impulse responses are constructed. The free-field generator instead uses fractional delays. The two conditions therefore differ in numerical propagation accuracy as well as acoustics.

I evaluated the noiseless direct-path arrival times analytically, with the current microphone coordinates, 1.5 m source distance, existing seven accumulation-study azimuths, and the same least-squares direction solve. This control does not use reflections, a noise realization, GCC-PHAT peak estimation, or a fitted accumulation curve.

| Delay construction | Rate | Direction RMSE at the seven existing azimuths |
|---|---:|---:|
| Exact spherical arrival times, followed by the far-field solve | Any | 0.3601° |
| Spherical arrivals rounded to samples | 16 kHz | 6.6125° |
| Spherical arrivals rounded to samples | 48 kHz | **1.4438°** |
| Spherical arrivals rounded to samples | 96 kHz | 0.5088° |
| Spherical arrivals rounded to samples | 192 kHz | 0.4699° |

The draft's lowest reported reverberant floor is approximately **1.48°**. The comparison establishes a material confound; it does **not** establish that rounding explains every reverberant result. Exact spherical delays also leave a 0.36° error when interpreted with a far-field solve. Curvature must therefore be separated too. Across 720 evenly distributed azimuths with a 0.13° offset, rounded 48 kHz arrivals give 2.1431° RMSE, versus 0.3375° for exact spherical arrivals. Angle selection matters.

The diagnostic output is in `research/direct_path_rounding_diagnostic.json`. A separate standard-library calculation in `research/direct_path_rounding_diagnostic.py`, importing no benchmark code, reproduces the earlier NumPy-based calculation within 3 × 10⁻¹⁴ degrees. This verifies the geometric diagnostic, not the complete room or GCC pipeline. These are analytic audit results, not newly validated performance figures for the manuscript. Do not subtract these RMSE values from room RMSE: correlated bias components do not add in quadrature automatically.

Source: [room simulator, arrival rounding](/home/ani/Desktop/sound_local/validation/reverb_robustness.py:58).

## Priority findings and required actions

| Priority | Finding | Why it affects publication | Required action |
|---|---|---|---|
| First | Whole-sample RIR arrival placement | Can create deterministic direction error without reverberation | Use a verified fractional-delay propagation model; compare against exact direct paths and an independently implemented reference |
| First | Only the first 2048 samples of convolution are evaluated | At 48 kHz this is 42.7 ms from source onset; most of a nominal 0.8 s RIR never contributes | Generate long continuous sources; include sufficient prehistory; compare startup with steady-state windows |
| First | Spherical room propagation is compared with plane-wave free-field propagation | Near-field curvature can be mistaken for multipath bias | Add exact spherical direct-path controls and a distance sweep; report the residual of the far-field model |
| First | Nominal RT60 is obtained through a Sabine coefficient formula | Desired RT60 is not the realized decay of the discrete, truncated, specular RIR | Measure EDT/T20/T30 where their fitted ranges are supported, document extrapolation, examine decay curves and convergence |
| First | Manuscript equations and implemented estimator differ | A reader cannot reproduce the reported algorithm from the manuscript | Freeze a single specification and reconcile equations, source, tables, and figures before rerunning |
| First | Very broad claims from one centered shoebox configuration | Many random source/noise draws do not create independent rooms | Vary room dimensions, array placement, source distance, orientation, and absorption distribution |
| First | Existing data cannot validate the intended hardware DoA task | Unknown timing and synchronization, severe undersampling of nominal excitation bands, and tiny clips | Keep acquisition audit separate; remove measured hardware accuracy, runtime, and power claims from the chosen paper |
| First | Existing AI provenance versus journal AI policy | A generic language-editing declaration would not accurately describe research or drafting assistance | Human author audits provenance; obtain editorial clarification on substantive AI-assisted code/drafting before submission |
| Next | Pooled frame errors treated as if all samples supplied equal independent evidence | Narrow Monte Carlo error bars can hide variation between acoustic scenes | Report conditional Monte Carlo uncertainty and between-scene variability separately; use hierarchical resampling |
| Next | Same records underpin direct bias and fitted floor estimates | Agreement is an internal consistency check, not independent validation | Estimate bias on one record set and validate the accumulation prediction on a disjoint set |
| Next | Accumulation values for different T reuse records | Cross-T covariance is omitted in the simple fit covariance | Bootstrap whole records/scenes, or fit with an appropriate covariance model |
| Next | Grid-limited baselines | A 1° SRP/MUSIC search grid can dominate high-SNR comparison with sub-degree GCC | Add a finer-grid or locally refined SRP comparison and state grid cost |
| Next | “Speechlike” source is band-limited white noise | Does not support performance claims on real speech | Name it accurately; use synthetic spectral variants and nonstationarity tests without claiming speech validation |
| Next | Physical lag constraints are described but absent from plain GCC peak search | An unconstrained argmax and bounded estimator are different methods | Apply and document consistent physical search limits; rerun the affected comparisons |
| Next | Figure scripts manually embed table values | A fresh experiment does not automatically update the manuscript figures | Export structured per-trial results and generate all tables/figures from the same data |
| Later | Firmware differs from simulation and is unverified | Cannot serve as evidence of a working three-pair embedded implementation | Document as an unvalidated prototype outside the main results; hardware work is outside this plan |

## Exact manuscript–implementation mismatches

1. **PHAT regularization.** The manuscript writes division by `|G| + epsilon`. The harness uses `max(|G|, 0.001 max|G| + 1e-12)`. This changes the spectral weight of weak bins. Use the exact implemented expression or change the implementation and rerun.
2. **Confidence score.** Equation (4) in the compact draft is a standardized peak relative to sidelobe mean and standard deviation. `_pair_confidence` uses peak divided by the magnitude of the largest sidelobe. These are different scores. The manuscript's thresholded power weighting also needs reconciliation with the weights actually used.
3. **Peak search.** `tdoa_phat` takes the global argmax. It does not search only within the pair's feasible lag interval, contrary to the compact draft's description. The gated method tests feasibility after selecting a peak, which is not equivalent to constraining the search.
4. **Preprocessing.** The supplement describes mean removal and a common analysis window. Plain GCC in the supplied harness directly transforms the input samples; MUSIC windows its short-time segments, and the firmware applies a Hann window. Specify the actual preprocessing of each result.
5. **Sign convention.** The compact draft and supplementary material use different signs for pair delay relative to baseline vectors. A consistent choice is sufficient, but it must match channel order and the code. Test known sources at 0°, 90°, and a non-cardinal direction.
6. **Geometry.** “5 cm aperture” is ambiguous. The simulation uses a **5 cm circumradius**, which gives **8.66 cm pair spacing** and a **10 cm diameter**. The quadrant lookup tables use a 5 cm pair. The physical dimensions of the device are unverified. Label each geometry explicitly.
7. **Hardware implementation.** The newer firmware computes pairs 0–1 and 0–2, while the simulation uses all three pairs. It specifies 16 kHz and 256 samples, versus 48 kHz and 2048 samples in the manuscript. Its round-robin ADC acquisition is not simultaneous sampling; channel offsets require accounting. No compilation or hardware execution was established in this audit.

Sources: [compact method](/home/ani/Desktop/sound_local/paper/main_paper_draft.md:97), [GCC implementation](/home/ani/Desktop/sound_local/validation/doa_benchmark.py:193), [confidence implementation](/home/ani/Desktop/sound_local/validation/doa_benchmark.py:248), [firmware](/home/ani/Desktop/sound_local/firmware/doa_gccphat/doa_gccphat.ino:245).

## Claims to revise before using them again

| Current claim or implication | Defensible replacement |
|---|---|
| A minimal array has a deterministic floor set by RT60 | A fixed acoustic configuration can produce persistent estimator bias; the current numbers also contain unresolved numerical and model errors |
| The floor is the same for every correlation estimator | The tested implementations behaved similarly in the tested configuration; do not extend to all correlation estimators |
| The floor is universally monotone in RT60 | The existing sweep was monotone; RT60 alone does not determine reflection direction, early-reflection strength, direct-to-reverberant ratio, or estimator bias |
| Two independent floor measurements agree to three decimals | Two related estimates use the same source/noise records and show close internal agreement; their uncertainties and small numerical differences need consistent reporting |
| An integer lag interval containing only zero makes all azimuths unobservable | Integer-lag peak picking is inadequate; fractional delay can still be informative for properly sampled band-limited signals |
| A fixed requirement of 5–10 native lag samples is a sampling theorem | It is an implementation/design heuristic that needs justification; Nyquist bandwidth and estimation error requirements are separate |
| Three microphones can never identify a bad pair | The unconstrained two-component linear solve has one residual degree of freedom; guaranteed identification requires additional assumptions or information. Scores, unit-norm constraints, and temporal structure must be considered |
| Confidence logic cannot pay for itself | The tested scores have small practical benefit in these trials; use an application-relevant equivalence margin and include difficult mismatch/outlier conditions |
| MSE(T) = b² + sigma²/T holds exactly | It is a small-error, stationary, independent-error approximation. Correlated records need a covariance-aware variance term |
| Five operations per temporal update | There are a few accumulations plus sine/cosine and an output atan2, or an explicitly stated approximation; transcendental evaluations are not equivalent to five ordinary arithmetic operations |
| Corrected GCC is universally near optimal | A stated information bound applies only under its signal/noise assumptions. Interpolation grid error is not the general Cramér–Rao bound |
| MUSIC collapses in reverberation | This particular incoherent MUSIC baseline under its specified covariance length and coherent-reflection conditions performed poorly |
| A 5.1× modeled compute reduction means a 5.1× device speedup | It is a reduction in a defined operation-count model; device time, memory allocation, and energy are separate measurements |
| The room floor is reached within 250 ms | The current simulated averaging protocol showed early saturation; continuous steady-state data, numerical controls, and actual observation delay remain to be checked |
| Band limiting is the new method | Band selection/weighting is established practice. The contribution would be quantified consequences, fair controls, and verified design guidance |
| “Exhaustive characterization” | A bounded sensitivity study over listed factors and ranges |

For temporally correlated small errors, the variance of a T-frame average is approximately

\[
\operatorname{Var}(\bar e_T)=\frac{\sigma^2}{T}\left[1+2\sum_{k=1}^{T-1}\left(1-\frac{k}{T}\right)\rho(k)\right].
\]

Use this to distinguish an actual persistent bias from slow variance reduction. It does not make the circular approximation exact for multimodal or large angular errors.

## Measured-data audit and scope

The current workspace contains **702 CSV/XLSX files but only 141 distinct file contents**, verified using SHA-256 hashes. Of the distinct contents, 105 excitation records each occur six times. The other 36 contents each occur twice. These are duplicated files, not independent observations.

I checked all **25 original triple-microphone workbooks**: each has one header row and **30 data rows**, with three microphone columns and a position label in a fourth header cell. They do not become long synchronized recordings by concatenating different source positions.

| Material | What remains useful | What it does not establish |
|---|---|---|
| 105 single-channel excitation records | Timing/aliasing evidence conditional on nominal drive frequencies; clipping census; raw code distributions | 1–20 kHz microphone transfer function, synchronized inter-channel phase, or localization performance |
| Three clean idle CSV recordings | Acquisition-chain idle variation in raw ADC units; robust/ordinary spread; glitch counts; low-rate temporal structure | Calibrated microphone self-noise in dB(A) SPL, or isolation of noise to the microphone versus ADC/environment |
| 25 three-channel short clips | File format, channel offsets, approximate distributional comparisons, missing-metadata example | Valid azimuth RMSE for the intended broadband task |
| Four quadrant lookup tables | A geometric illustration of two-microphone absolute TDOA and range ambiguity | Measured 2-D localization or an independent ground-truth data set |
| Four filter sketches | Deterministic filter-response comparison; useful source for a supplementary implementation audit | Acoustic restoration of aliased frequency information |
| Corrupt idle workbook and value-gated derivative | A documented exclusion reason | An unbiased noise-floor estimate |
| Random 77% accuracy heatmap script | Historical evidence of a synthetic illustration requiring exclusion | Any experimental accuracy figure |

The existing data report infers approximately 999.988 Hz by fitting alias frequencies under assumptions about the source frequencies. Describe this as a **conditional clock estimate**, not a calibrated absolute clock measurement. Nominal loudspeaker drive frequency and sampling-clock error can be confounded. The logger supports approximately 1 kHz operation; it does not prove per-channel synchronization. The proposed ≤167 Hz rate for the short clips is an inference from a noise-correlation model with unverified shared bandwidth, not a measured sample rate.

The existing acquisition report also contains overstrong causal statements. A non-monotone distance-level curve does not by itself prove the source level changed; reflections, directivity, placement, or logging differences are possible. Idle noise exceeding ideal quantization noise does not uniquely identify its physical source. Retain observations and state the competing explanations.

**Filter caution:** applying the same LTI filter to both channels multiplies the cross-spectrum by `|H(f)|²`; its common phase cancels. A nonlinear-phase common filter is not automatically a relative-delay error. Finite windows, unequal filters, nonlinear processing, and changing signal-to-noise weighting can still matter. The old report's blanket rejection of one filter based only on common nonlinear phase needs correction.

Sources: [existing acquisition report](/home/ani/Desktop/sound_local/paper/data_results.md:25), [synthetic heatmap script](</home/ani/Desktop/sound_local/Triple Mic Samples/python.py:20>), `research/data_inventory.json`.

## What the audit did and did not do

- Read the compact manuscript, its supplement, the project handover, result reports, relevant mathematical sections, estimator code, room generator, accumulation code, figure generator, firmware, library documentation, and data-processing sketches.
- Independently counted and hashed CSV/XLSX contents, inspected all 25 short multichannel workbooks, counted the abstract, and performed the direct-path geometric diagnostic above.
- Confirmed several exact source/manuscript discrepancies. Did not rerun the complete simulation campaign, certify the older acquisition report, compile firmware, or establish any new hardware result.
- Created a private plan and research register. All proposed experiments, schedules, and future paper titles remain proposals.

The publication plan treats the first group of findings as prerequisites to choosing the paper's final headline.
