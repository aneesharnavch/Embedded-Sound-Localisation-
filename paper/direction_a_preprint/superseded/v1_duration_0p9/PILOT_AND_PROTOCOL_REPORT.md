# Pilot report and protocol freeze

The pilot is exploratory and excluded from main estimates. All confirmatory choices below were frozen before the main campaign.

12 scene/direction combinations, two independent source/noise records, 32 frames, 10 dB and noiseless conditions: 13,824 retained pilot rows. Runtime 135.9 s; peak process memory 459.5 MiB. Numerical refinement adds separate checks.

| Refinement | Largest paired angular change | Frames exceeding 0.05° |
|---|---:|---:|
| propagation32 | 0.010058° | 0 |
| extent56 | 0.004176° | 0 |
| correlation16 | 0.029282° | 0 |

The primary settings pass the stochastic pilot. The 0.05° threshold is a numerical discrepancy target; effects below roughly 0.5° will not receive strong interpretation. It does not bound error against acoustic ground truth.

At 10 dB, pooled exploratory RMSE was 0.886° for fractional direct paths, 2.831° after rounding direct arrivals, 34.130° for fractional continuous reflected signals and 4.018° for the separately labeled frame-reset diagnostic. These are pilot-specific results, not final claims. The marked frame-reset contrast motivates the source-history analysis. Some high-reflection scenes have very large or multimodal errors, so a universal small-error variance model would be inappropriate.

The legacy diagnostic uses identical within-frame source/noise samples and resets source and acquisition-filter history for every 2048-sample frame. Continuous onset resets once at record start; the steady condition retains all prehistory. Every three-way attribution comparison uses identical source/noise realizations.

The original 276,480-evaluation allocation is retained. Pilot throughput suggests a campaign on the order of several to fifteen minutes with two local worker processes, excluding sensitivity analyses and document preparation; this is a measured estimate, not a device speed claim. Raw result storage is small compared with optional impulse-response caches. Minimum scene wall clearance: 0.3124 m.

The machine-readable protocol specifies every main cell, independent long-record split, statistical rules and the fixed sensitivity/baseline subset. Bootstrap records are the repeated units; frames do not count as independent room samples. Requested RT settings and measured decay are retained separately.

Protocol hash: `367d41d15d4ac2f95cdce332f67ffea689cb4b2132367d7651a2704754fdb21a`.
