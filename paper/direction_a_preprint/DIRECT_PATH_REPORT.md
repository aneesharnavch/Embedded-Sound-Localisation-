# Direct-path verification report

**G1 numerical checks: PASS.**

This report concerns analytical delays and noiseless deterministic harmonic verification signals. It is not a room-performance or hardware result.

- Analytical conditions saved: 34,560.
- Waveform/kernel conditions saved: 288.
- Maximum plane-wave inversion error: 5.68e-14 degrees.
- Maximum difference from the independent scalar solve: 7.25e-12 degrees.
- Maximum discrepancy reproducing the old geometric diagnostic: 2.84e-14 degrees.
- Maximum interpolation-factor 8 versus 64 difference: 0.000494578 degrees.

| Kernel half-width | Maximum relative waveform error | Maximum angular discrepancy |
|---|---:|---:|
| 16 | 4.69591e-06 | 5.15136e-05 degrees |
| 32 | 3.76633e-06 | 3.64081e-05 degrees |
| 64 | 3.40207e-06 | 1.63282e-05 degrees |

The 0.05-degree tolerance bounds numerical discrepancies in these reference comparisons. It is not an absolute estimator-accuracy promise. Finite-window effects and spherical-to-plane model mismatch can remain in both waveform implementations.

A fixed analysis interval is used across FIR refinements; sampling-rate comparisons retain approximately 42.667 ms with nearest-integer sample counts. The source band remains 300-3400 Hz.

The legacy seven-direction 48 kHz rounding diagnostic reproduces about 1.44385 degrees RMSE. The full-circle value is about 2.14307 degrees. Exact spherical delays leave curvature error under the far-field solve; neither number measures a universal reverberant floor.

Per-condition outputs and the verification summary are in the results/direct directory. Source hashes and environment versions accompany the run. The core scientific correctness tests must also pass before G1 is recorded complete.
