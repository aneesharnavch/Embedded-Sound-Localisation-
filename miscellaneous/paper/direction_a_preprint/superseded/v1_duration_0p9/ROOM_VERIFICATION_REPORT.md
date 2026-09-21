# Room-model verification report

**G2 numerical checks: PASS.**

The model is a frequency-independent, specular shoebox image-source model. This is computational verification, not validation against a real room.

| Scene | Requested RT60 (s) | Realized band T20 (s) | Selected image extent |
|---|---:|---:|---:|
| 0 | 0.15 | 0.0933 | 14 |
| 1 | 0.60 | 0.6211 | 40 |
| 2 | 0.15 | 0.1007 | 14 |
| 3 | 0.60 | 0.6056 | 48 |
| 4 | 0.15 | 0.0884 | 14 |
| 5 | 0.60 | 0.6363 | 40 |

Convergence requires two successive image refinements with angular change below 0.05 degrees, relative T20 change below 1%, and relative probe-spectrum change below 0.1%. Extending path duration from 0.9 to 1.2 s is checked separately at fixed image extent.

Fractional room responses deposit each image between two samples of a finer time grid, then apply a Kaiser-windowed sinc decimation filter. Grid oversampling 8, 16, and 32 is compared against an independent exact-phase image sum. This differs from the direct-path FIR implementation and has its own verification.

The full-extent independent reference has relative spectral discrepancy 3.1949e-05 and angular discrepancy 0.0018093 degrees. Path counts also agree.

Room decay is estimated after a common fourth-order 300-3400 Hz Butterworth acquisition filter using the Schroeder energy decay. T20 is extrapolated from -5 to -25 dB, and fit R-squared values are stored. Requested and realized decay are distinct.

The recording tests separately verify identical paired source/noise realizations, exact direct-band SNR calibration, and onset transients that disappear with sufficient history. The common acquisition filter is causal. The source onset condition includes the spectral broadening of switching on the source.

Detailed configurations, path counts, refinement results, reference errors, fit quality and source hashes are stored in results/room.

## Continuous-history and acoustic descriptors

The pilot saves band-limited direct/reflection component-energy ratios (including the coherent cross term), direct arrival times/gains, all six first-order wall arrival times/gains, decay fits and wall clearance for 12 additional scene/direction combinations. This component DRR is not an isolated temporal-window DRR: overlapping arrivals remain coherent. See `results/pilot/summary.json`.

The paired pilot compares continuous steady state, one-time onset, and legacy frame resets with exactly the same within-frame source/noise samples. At 10 dB their pooled reflected RMSEs are 34.130°, 32.560° and 4.018°, respectively; these exploratory values are not main-campaign results. All three stochastic numerical refinements remain below 0.05°. See `PILOT_AND_PROTOCOL_REPORT.md`.
