# Room verification: final v2 settings

The original separate refinement tests were insufficient for the target in a joint duration/image extension. The failed check and superseded results remain archived and are described in NUMERICAL_NOTES.md.

Final settings: 1.2-second cutoff, image extent76, propagation grid32, sinc half-width32. A joint 1.5-second/extent96 check passes with largest angular change 0.012727 degrees over 960 paired frames. Final exact-phase independent reference: {"path_counts": [5215621, 5215553, 5215518], "relative_spectrum_error": 1.1298071908235994e-05, "angular_difference_deg": 0.0008073544532862797}.

Nine direct/room/SRP tests pass. Axial tile pruning matches six original responses and path counts exactly. Final pilot propagation64/image84/GCC16 refinements all pass the 0.05-degree target.

Realized band decay, component DRR including coherent cross terms and six early-wall arrivals are saved for each final scene. These are numerical checks of a simplified specular model, not experimental validation.
