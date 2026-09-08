# Claim and source audit

Verified 7–8 September 2026. This is a focused audit, not proof of an exhaustive novelty search. The earlier project review screened 398 Acta records and kept reading-level distinctions in `paper/publication_speedrun/research/reading_notes.json`; those notes remain archived. The new focused Crossref searches and complete returned metadata are retained here. Publisher pages were checked for the foundational papers named below. Full-text access and abstract-only access are distinguished.

| Topic / possible claim | Closest evidence and reading level | Decision for Direction A |
|---|---|---|
| Generalized correlation / PHAT | Knapp and Carter (1976), DOI 10.1109/TASSP.1976.1162830; original IEEE abstract and bibliographic page checked | Established method. Specify the present bounded, regularized implementation; do not claim its invention or universal maximum-likelihood optimality. |
| Three-microphone equilateral azimuth estimation | Catur and Saputra (2019), DOI 10.1109/ICRAMET47453.2019.8980432; original IEEE abstract checked | Existing experimental and simulation work already combines this geometry with GCC-PHAT. Array layout is not the contribution. No numerical comparison without matched inputs. |
| Subsample delay construction | Laakso, Välimäki, Karjalainen and Laine (1996), DOI 10.1109/79.482137; original IEEE abstract and metadata checked | Fractional-delay filters are established. Independently test the actual filter and distinguish propagation interpolation from estimator interpolation. |
| Subsample GCC | Qin, Zhang, Fu and Yan (2008), DOI 10.1109/ICOSP.2008.4697676; metadata verified; publisher reading incomplete after a timeout | Search lead only at this stage. No detailed claim about its algorithm or superiority; exclude from manuscript unless primary reading is completed. |
| Shoebox image simulation | Allen and Berkley (1979), DOI 10.1121/1.382599; original AIP abstract and bibliographic page checked | Established image method. Present pressure gains, wall counts, truncation and time interpolation explicitly. The new implementation is not a new propagation theory. |
| Physical versus numerical discrepancy | Ernoult et al. (2026), DOI 10.1051/aacus/2026048; earlier publisher full-text verification/conclusions reading retained | Adopt the distinction between implementation error, discretization and physical assumptions. Our independent software checks are not experimental validation or external peer review. |
| Room numerical convergence | Hölter, Weinzierl and Lemke (2024), DOI 10.1051/aacus/2024071; earlier publisher methods and verification reading retained | Established practice of refinement and analytical controls. Their wave-based solver is not the present specular model. |
| Requested versus realized decay | Bellows and Katz (2025), DOI 10.1051/aacus/2025011; original publisher abstract in prior review, Crossref abstract checked again | Absorption/RT equations require calibration. Use nominal Sabine settings as labels, measure the actual band-limited decay; do not assume an RT target is achieved. |
| Tolerance / mismatch criterion | Lee and Ma (2026), DOI 10.1051/aacus/2026061; original Acta abstract/introduction and earlier full-text mismatch/conclusion notes | A bounded engineering criterion is useful, but rotating-source formulas/empirical thresholds do not transfer. Derive the present elementary geometry sensitivity and test it separately. |
| Finite-distance curvature | Exact spherical distances and a far-field least-squares solve, independently implemented here | Established geometry, not a novel physical effect. Quantify it separately from rounding. Preserve radius, source distance and angle dependence. |
| Averaging / error floor | Standard covariance identity for an average; to be derived explicitly and tested with separate records | No universal floor assumed. Test per-scene stability and use empirical circular distributions for large or multimodal errors. |

## What this preprint can contribute

The intended contribution is a reproducible, controlled attribution study for a precisely specified minimal array and estimator. It connects independent numerical references, paired source-history/rounding/reflection controls, realized acoustic descriptors, record-level uncertainty and held-out averaging. This is a verification and replication contribution; no claim of being the first, of a new estimator, or of a universal reverberation law is justified by the search.

The pilot is exploratory. Its records are excluded from confirmatory estimates. An apparent large effect must survive the frozen main matrix and cannot be inferred from this audit alone.

## Excluded historical evidence

- The forced 77% spatial illustration in `Triple Mic Samples/python.py` is not an experimental result and is excluded from all new figures and claims.
- Historical integer-sample image arrivals and frame-by-frame source restarts are diagnostic baselines, not corrected propagation or continuous recordings.
- Old seven-angle analytical numbers are reproduced only to audit the previous calculation. They are not end-to-end, hardware or full-circle accuracy.
- Existing recordings do not establish the required microphone synchronization, geometry, direction ground truth and acoustic controls for this paper. No hardware localization, latency, energy, power or deployment claim is made.
- Historical manuscript claims and fabricated-looking acceptance/publishing metadata are not evidence. The new paper is explicitly an unreviewed preprint.

Bibliographic verification is not full-text review. Sources read only at abstract level will support only the broad established facts visible there. Additional sources for decay integration, SRP and bootstrap methods will be checked before their citation is finalized.
