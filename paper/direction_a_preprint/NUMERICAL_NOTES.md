# Numerical investigation notes

The first room verification driver applied the production spectral tolerance to
all refinement settings, including the intentionally coarser oversampling-8
control. That control had relative spectral discrepancy 0.000107385 in scene 1,
slightly exceeding 0.0001. The originally selected production setting was 16,
which gave 0.00002795 and 0.003588 degrees angular discrepancy in that case.
The driver now retains all refinement outputs and requires settings 16 and 32
to pass the unchanged production tolerances. The original run log and isolated
coarse-grid diagnostic are retained. This changes the application of the gate,
not its numerical threshold or the selected production setting.

The 5 x 4 x 2.8 m high-decay scene had only one passing refinement step
by image extent 40. Its K=32 spectrum change was 0.001984, above the
0.001 criterion. The refinement sequence was extended to 48 and 56,
retaining the two-consecutive-pass rule and all thresholds. This is
numerical convergence work before the stochastic campaign is frozen.

## Joint duration/coverage correction

The original 0.9-second response/extent48 passed the separate controls but failed a stronger joint extension to 1.2 seconds/extent76: 10 of 960 paired stochastic frames exceeded 0.05 degrees; maximum 0.165514 degrees. Results, sources and draft were preserved under superseded/v1_duration_0p9 and affected statuses invalidated. The threshold was not relaxed.

The revised 1.2-second/extent76/P32 model passes joint extension to 1.5 seconds/extent96 with maximum 0.012727 degrees over 960 frames. A new full-extent independent reference and revised pilot pass. A safe axial tile bound accelerates construction; six old responses and path counts remain bitwise identical after this optimization. The protocol amendment precedes v2 main results; all scientific allocations and statistical rules remain unchanged.
