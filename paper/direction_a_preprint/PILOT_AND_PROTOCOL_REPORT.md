# Revised pilot and frozen protocol

V2 repeats the same 12 pilot scene/direction conditions, two records, 32 frames, 10 dB and noiseless variants using separate pilot_v2 inputs. It retains 13,824 pilot frame rows and 18,432 primary/refined evaluations.

Elapsed time 146.10676110399982 seconds; peak memory 557.0703125 MiB. Refinements: {"propagation64": {"max_difference_deg": 0.0019396243328344553, "frames_above_tolerance": 0}, "extent84": {"max_difference_deg": 0.0, "frames_above_tolerance": 0}, "correlation16": {"max_difference_deg": 0.016775179871615364, "frames_above_tolerance": 0}}. All pass.

The 276,480-evaluation main allocation, 38,400-row sensitivity/refinement allocation and statistical rules remain unchanged. The correction changes numerical response support and input histories, not selected scenes or endpoints. New namespaces keep revised results separate. Protocol hash 800c62aa3ee71fb962a186255d947775d968a348906a4e6a026c2e6902b1f969.

See NUMERICAL_NOTES.md for the failed original check and retained v1 materials. No v1 result is pooled into final estimates.
