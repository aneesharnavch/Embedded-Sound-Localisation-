# Acta Acustica publication speedrun

**Prepared 7 September 2026 · Existing files only · No new hardware recordings required**

**Current direction on 7 September 2026:** the author chose **Direction A, preprint first**, prepared through assistant-led execution and using Acta Acustica's scientific and presentation standards. Follow the [preprint execution checklist](/home/ani/Desktop/sound_local/paper/publication_speedrun/DIRECTION_A_PREPRINT_TODO.md) and [Direction A research plan](/home/ani/Desktop/sound_local/paper/publication_speedrun/ACTA_ACUSTICA_ROUTE_A_PLAN.md). This broader journal review remains background; its journal-first schedule and editorial-policy prerequisites do not govern the current preprint preparation.

## 1. Recommendation

Aim for **one coherent computational acoustics paper**, supported by a reproducible research package and a short acquisition-quality appendix. Your most promising contribution is a **verified account of where direction-estimation error comes from in a minimal three-microphone system**. The current abstract's universal “reverberation bias floor” claim is premature.

Start by separating **propagation discretization, spherical-wave curvature, correlation interpolation, startup transients, noise, and room reflections**. Then quantify what temporal averaging and different computational budgets actually buy. This makes useful use of the simulator, mathematical work, ablations, implementation studies, and recorded-data audit without requiring unsupported hardware claims.

**Planning estimate:** approximately **80–120 focused author-hours**, plus unattended computation and any editorial clarification. At 20 hours/week, allow **4–6 weeks to a submission-ready package**. A concentrated **10–15 working-day** route is possible only if the first scientific checks succeed and the scope stays narrow. Submission readiness, peer review, acceptance, and publication are different milestones; the journal controls the latter three.

**Do not submit the current draft as it stands.** The principal reasons are identifiable and repairable: the room simulator's arrival rounding can create a floor without reflections; the manuscript does not exactly describe its code; some uncertainty and generality claims are too strong; the abstract is 605 words against a 200-word maximum; and the journal's current AI policy needs careful provenance handling.

The first diagnostic in this audit found **1.4438° noiseless direction RMSE from sample-rounded direct paths** at the same seven angles used in the accumulation study. The draft's lowest reported room floor is about **1.48°**. This is a substantial confound, not a completed explanation of the entire result. The full evidence and limitations are in [Scientific audit](/home/ani/Desktop/sound_local/paper/publication_speedrun/SCIENTIFIC_AUDIT.md).

### What “publish everything” should mean

Give each legitimate piece of work a useful destination. The article should answer one research question; the repository and supplement can preserve the broader project. Code, negative results, intermediate designs, and data exclusions can all be documented without each becoming a main-text contribution or a separate paper.

The proposed package is:

1. A journal article about verified minimal-array estimation limits and numerical/physical error separation.
2. A versioned, citable code-and-data release with the valid recordings, simulation configurations, per-trial outputs, and provenance.
3. Supplementary derivations, complete ablations, and the acquisition audit.
4. A separate development archive for superseded drafts, the unverified firmware, and excluded illustrations.

This plan prepares those destinations. It does not upload or submit anything.

## 2. What was reviewed

The journal review covers **7 September 2021 through 7 September 2026, inclusive**, using online publication dates. It reconciles Crossref metadata with the journal's official volume listings. Six annual volumes intersect this rolling five-year window.

| Online publication year | Published items in the window |
|---|---:|
| 2021, from 7 September | 21 |
| 2022 | 61 |
| 2023 | 68 |
| 2024 | 81 |
| 2025 | 83 |
| 2026, through 7 September | 84 |
| **Total** | **398** |

The six whole volume listings contain 438 entries. Forty are before the cutoff. Crossref also returns **13 additional records outside the published-volume census**. Publisher landing pages confirm 12 as forthcoming; the remaining DOI, `10.1051/aacus/2026090`, resolves to a publisher “Content not found” page and remains unresolved. All 13 are retained separately rather than added to the published count. Two items in the 2025 volume have 2026 online dates; that is why the online-year totals differ from volume totals.

There are **388 publisher-deposited abstracts** for the 398 published items. The ten without abstracts include editorials, corrections, and book-review material. The catalogue includes all 398, not just localization papers. **All 398 received full-text extraction and keyword screening: 380 through HTML, 18 through publisher PDFs.** The PDF route recovered every HTML extraction failure. Selected sections of 16 relevant items received closer examination, with substantive project notes on 26 records overall. Full-text screening is distinguished from close scientific reading in each entry. This is a comprehensive scoping review for publication planning, not an independent replication or a line-by-line peer review of every article. See the [coverage and methods record](/home/ani/Desktop/sound_local/paper/publication_speedrun/COVERAGE_AND_METHOD.md).

The publisher's article-type labels include 294 Scientific Articles, 62 Technical & Applied Articles, 12 Review Articles, 10 Short Communications, 9 Audio Articles, 4 editorials, 3 corrigenda, 2 book reviews, and 1 letter. One remaining entry is labelled by subject rather than a standard article type in the listing. These counts describe the corpus; they do not estimate your chance of acceptance.

Use the [searchable reading register](/home/ani/Desktop/sound_local/paper/publication_speedrun/READING_REGISTER.html) for every title, author list, DOI, date, abstract, screening level, and project note. The [complete text register](/home/ani/Desktop/sound_local/paper/publication_speedrun/LITERATURE_REGISTER.md) is also available.

The local audit covered the current compact draft and supplement, longer drafts and mathematical sections, post-rebaseline reports, acquisition analysis, main estimators, room and accumulation code, figures, firmware, library documentation, and recording inventory. It identified **702 CSV/XLSX copies representing 141 distinct file contents** and inspected all 25 short three-channel workbooks. The existing project has more reusable analysis than the original hardware framing suggests, but it is not yet a validated embedded system paper.

## 3. Journal fit and current submission rules

The best subject match is **Audio Signal Processing and Transducers**, with **Computational and Numerical Acoustics** or **Room Acoustics** relevant depending on the final emphasis. The journal explicitly covers original models as well as experiments. There is no stated rule that every paper needs a new hardware campaign.

| Item | Verified rule or practical implication |
|---|---|
| Publication charge | Diamond Open Access; no author APC from 1 January 2025. Your institutional status is not a reason to budget an APC |
| Language and files | English; LaTeX source required. The existing EDP template is useful |
| Scientific Article | Original ideas, models, or experiments contributing substantially to acoustics; typically up to 12 typeset pages |
| Technical & Applied Article | Original application of an existing technique/concept/measurement method, with interest beyond one installation or application. It is not a category with a guaranteed lower acceptance bar |
| Short Communication | At most four typeset pages; still requires an original scientific contribution |
| Abstract | Up to 200 words for papers; up to 100 for Short Communications and letters; structured around introduction, methods, results, discussion |
| Literature | Relevant acoustics literature must be cited; the journal explicitly uses this in assessing scope. At most 80 references except reviews |
| References | Numbered by first appearance; all author names; include `.bib` and `.bbl` where BibTeX is used |
| Manuscript readability | Consecutive page numbers and line numbers; define symbols when introduced |
| Figures | Separate files; vector format required except photographs. Color figures should also work in grayscale. The page also lists raster-resolution requirements; check the final submission format against both statements |
| Declarations | Conflict-of-interest and Data Availability statements mandatory; funding and author contributions recommended |
| Reviewers | Suggest three; do not suggest all three from the same country; check expertise and conflicts rather than selecting by presumed friendliness |
| Author identifiers | Corresponding-author ORCID during submission; coauthor identifiers must be validated by acceptance under the stated workflow |
| Preprints | Accepted as prior dissemination, subject to the journal's stated originality conditions. Do not submit concurrently to another journal |
| Proofs | Corrected proofs requested within eight days; production is not the stage for adding new scientific material |

Source: [Instructions for authors](https://acta-acustica.edpsciences.org/author-information/instructions-for-authors), checked 7 September 2026.

### AI provenance is an early submission issue

The current author instructions say AI tools may be used **“only for language improvement”**, prohibit AI creation/modification of submitted images/figures/visual data, and require disclosure of the tool, version, and role in both the manuscript and cover letter. Human authors retain responsibility.

The existing project notes describe substantive AI-assisted analysis and drafting. Therefore, do not use a generic statement claiming that assistance was limited to grammar. Inventory the actual contributions. The human author must understand and independently verify the science. Obtain clarification from the editorial office about the applicability of the policy to the existing drafting, numerical code, and deterministic plotting workflow before committing to submission. Do not assume that rerunning a script alone resolves provenance or that all conventional programmatic plots are necessarily prohibited; those are different questions, and the wording needs an authoritative interpretation.

This document is private publication planning, not a manuscript ready to submit. No message has been sent to the journal. A later inquiry should state the real roles, the intended human verification process, and the exact uncertainty about policy. It should not seek permission to conceal assistance.

### Topical issue and timing

**Benchmarking Problems and Datasets in Acoustics** is listed as in progress and includes the 2026 FLOW-01 dataset article. The 2026 editorial described it as open at that time. The collection page does not establish a current submission deadline, so do not build the schedule around an assumed deadline or special fast track. The normal journal route remains the default unless the current call or editorial office confirms eligibility.

Sources: [topical issues](https://acta-acustica.edpsciences.org/topical-issues), [benchmarking collection](https://acta-acustica.edpsciences.org/component/toc/?task=topic&id=2448), [2026 editorial](https://doi.org/10.1051/aacus/2026076).

The editorial reports roughly ten days on average from submission to reviewer invitation, including initial checks. This is **not** ten days to acceptance or even necessarily to first decision. It also notes an increased rejection rate in 2025. The old project note's approximately 55% acceptance figure should not be used as a personal forecast. Plan for peer review to take weeks to months, with revision time additional; that is a scheduling allowance, not a journal guarantee.

## 4. What recent Acta papers imply for your strategy

The catalogue was screened across all subject areas. For this project, the useful patterns are a strong role for physical interpretation, explicit numerical verification, measured or analytical reference cases, bounded claims, and shareable methods/data. Hearing-localization studies are often about human perception rather than microphone-array estimation; their degree errors are not directly comparable to your simulator's degree errors.

| Paper | Relevance to your work | Consequence for your manuscript |
|---|---|---|
| Ghouli, 2026, *Passive acoustic detection and localization of drones using MEMS microphones and machine learning*, [DOI](https://doi.org/10.1051/aacus/2026008) | Direct application neighbor using microphone arrays, TDOA, an ESP32-S3 acquisition component, and a separate processing system | “Low-cost embedded localization” alone is not a distinct contribution. Discuss the different scope; do not compare your simulated RMSE to its field errors as if conditions matched |
| *A dimensionless rotational mismatch index for quantifying rotational speed bias effects in rotating beamforming*, 2026, [DOI](https://doi.org/10.1051/aacus/2026061) | Closely related paper structure: derive a bias mechanism, sweep coupled parameters, propose practical tolerances, and check them against a public fan dataset | A useful template for converting an error analysis into an engineering decision rule. Its rotating-source index is not a bound for your stationary array |
| *Experimental investigation of grazing-incidence sound propagation over free-standing absorbers*, 2026, [DOI](https://doi.org/10.1051/aacus/2026022) | TDOA/phase interpretation changes when direct and secondary arrivals are distinguished; includes fractional-delay alignment | Strong motivation for controlled attribution of apparent acoustic effects. Its recovered direct field is algebraically tied to the reference response, so do not copy that comparison as an independent validation test |
| *Joint short-time speaker recognition and tracking using sparsity-based source detection*, 2023, [DOI](https://doi.org/10.1051/aacus/2023004) | Image-method room simulations, TDOA, reliable microphone-pair selection, and temporal tracking with speaker identity | Pair confidence and temporal information already have related uses in this journal. Distinguish your minimal-array question; do not claim universal failure identifiability from a linear redundancy count |
| Mao et al., 2026, *Active control of low-frequency sound transmission using force radiation modes: A numerical study*, [DOI](https://doi.org/10.1051/aacus/2026043) | A Technical & Applied numerical paper checks convergence and compares with an analytical reference; experiments remain future work | Strong evidence against a blanket “new measurements are mandatory” rule. Your corresponding obligation is independent verification and a meaningful acoustic result |
| Friot et al., 2026, *Sparse estimation and global control of low-frequency wall-scattered pressure…*, [DOI](https://doi.org/10.1051/aacus/2026049) | Computational sensor-efficiency design study using analytical/modal and FE models, with measurement-calibrated model parameters | Copy the validation discipline and explicit deployment limits. Do not call it completely measurement-free precedent |
| *Benchmark study of pipe input impedance simulations and measurements for verification and validation in musical acoustics context*, 2026, [DOI](https://doi.org/10.1051/aacus/2026048) | Separates implementation errors, convergence, modeling assumptions, and measurement variability | A particularly useful model for separating numerical verification from physical validation in your error budget |
| Geyer et al., 2026, *FLOW-01: A benchmark dataset…*, [DOI](https://doi.org/10.1051/aacus/2026068) | Technical & Applied benchmark contribution with reuse as the purpose | A benchmark package needs well-defined cases, metadata, reference values and limitations, not merely code in a folder |
| *Constrained least-squares and maximum-likelihood calibration of absorption coefficients in reverberation time equations*, 2025, [DOI](https://doi.org/10.1051/aacus/2025011) | Room-model calibration and stochastic simulation | Desired RT60 and realized room behavior must be distinguished; report uncertainty and assumptions |
| Polack, 2025, *Revisiting reverberation*, [DOI](https://doi.org/10.1051/aacus/2025010) | Examines the assumptions behind reverberation formulas, free-path statistics and enclosure geometry | Reinforces that a Sabine-derived input does not certify the decay of your discrete RIR or determine a universal direction-error floor |
| *Computationally-efficient rendering of diffuse reflections for geometrical acoustics based room simulation*, 2025, [DOI](https://doi.org/10.1051/aacus/2024062) | Efficiency-versus-acoustic-fidelity questions | Your operation-count comparison should be connected to accuracy and simulation fidelity, not a universal MCU speedup |
| *Finite difference time domain discretization for room acoustic simulation based on the non-linear Euler equations*, 2024, [DOI](https://doi.org/10.1051/aacus/2024071) | Numerical dispersion, stability, efficiency, and reference room cases | Numerical effects can be a legitimate acoustics contribution when characterized systematically |
| *Capabilities of inverse scheme for acoustic source localization at low frequencies*, 2021, [DOI](https://doi.org/10.1051/aacus/2021034) | Source-identification limits and inverse-problem framing | Explain identifiability, geometry, and noise/model assumptions before interpreting an error curve |
| *Spatial speech detection for binaural hearing aids using deep phoneme classifiers*, 2022, [DOI](https://doi.org/10.1051/aacus/2022013) | Spatial estimation evaluated across anechoic/reverberant scenes and different SNRs | Useful scenario-design precedent; it is not a like-for-like baseline for a three-microphone noise-source experiment |
| *Auditory-visual scenes for hearing research*, 2022, [DOI](https://doi.org/10.1051/aacus/2022032) | Reusable scene definitions and measured/simulated comparison | Use explicit scene manifests and reference cases. Its data are an optional later extension, not required by this existing-files plan |
| *Towards modelling active sound localisation based on Bayesian inference in a static environment*, 2021, [DOI](https://doi.org/10.1051/aacus/2021039), and *A Bayesian model for human directional localization…*, 2023, [DOI](https://doi.org/10.1051/aacus/2023006) | Different localization problem: human/binaural inference and priors | Useful scope boundary; do not confuse human localization limits with an array's estimator bound |

These are purposeful reading anchors, not a request to cite all of them. Cite a paper only where it supports a statement or distinguishes the contribution.

### What is already established

GCC-PHAT, SRP-PHAT, MUSIC, fractional-delay estimation, circular averaging, aperture scaling, and the existence of reverberation-induced bias are established ideas. A separate Crossref prior-art check also found work explicitly on an **equilateral triangular GCC-PHAT array** in 2019 and **subsample GCC-PHAT estimation** in 2008. Three microphones and interpolation are therefore not defensible novelty claims by themselves.

Relevant outside-window records include [equilateral-triangle array, 2019](https://doi.org/10.1109/ICRAMET47453.2019.8980432), [subsample delay estimation, 2008](https://doi.org/10.1109/ICOSP.2008.4697676), and Acta's [two-microphone vehicle-source direction estimation, 2021](https://doi.org/10.1051/aacus/2021011), which precedes the rolling cutoff. These were identified as additional prior-art anchors, not given the same full-corpus review coverage. Read them before asserting a gap.

### Candidate contribution that could survive review

> A reproducible verification protocol and controlled study showing how numerical propagation, model mismatch, spectral weighting, and temporal statistics determine the apparent performance of minimal microphone-array estimators, together with a bounded accuracy–computation design envelope after those effects are separated.

That remains a **candidate**, not an established novelty finding. It becomes convincing only if it generalizes beyond one bug in one private script, survives an independent reference implementation, and produces a useful decision rule for other acoustics researchers.

## 5. Choose the paper after the first verification gate

| Route | Working title | Evidence required | Choose it when |
|---|---|---|---|
| **A — recommended** | **Separating numerical and acoustic error in three-microphone direction-of-arrival estimation** | Controlled rounding/curvature/startup studies, independent propagation reference, multiple room configurations, fair baselines, uncertainty | Numerical confounds materially alter the conclusions and the explanation generalizes across settings |
| B — broader design paper | **Accuracy and computational trade-offs in a minimal three-microphone direction-of-arrival estimator** | Verified simulator, room ensemble, aperture/frame/rate trade-offs, accurate operation/memory accounting | Corrected results yield useful, stable design recommendations beyond the verification finding |
| C — compact fallback | **Propagation-delay discretization in small-array direction-of-arrival benchmarks** | Clean analytical mechanism, independent reproduction, several geometries/rates, concise practical criterion | One strong result survives but the broader design study would add time without insight; consider a four-page Short Communication |

Use a Scientific Article for an original verification/methodological contribution. Consider Technical & Applied only if the final paper is best described as a broadly useful application/benchmark study. Choose the category because it fits the contribution, not because of an assumed easier review process.

If the numerical issue disappears after correction and the remaining results merely reproduce textbook behavior, the honest decision is to improve the study before submitting. A negative result is publishable when it resolves a meaningful question with sound evidence; a collection of unsurprising ablations is not automatically a contribution.

## 6. What to do with everything already in the project

| Asset | Destination | Work needed |
|---|---|---|
| Compact manuscript | Base for a rewritten main article | Rewrite around final verified question; reconcile all methods and quantities |
| Supplementary draft | Supplement | Remove stale claims; keep derivations, extended statistics and protocols |
| Long drafts and mathematical notes | Author research archive | Extract useful reasoning; do not merge all prose into the article |
| Corrected free-field PHAT benchmark | Main methods/control result | Verify sign, bounds, windows, regularization, bandwidth convention, and reference output |
| Room simulator and room sweeps | Main evidence after repair | Fractional propagation, steady state, realized decay, scene ensemble, independent check |
| Confidence and temporal ablations | Main result or supplement | Exact score definition, paired analysis, uncertainty, practical effect sizes |
| Aperture and frame-length sweeps | Design-envelope section | Separate sampling rate from observation time and bandwidth; include ambiguity regions |
| Analytical FLOP and memory model | Design section or supplement | Explicit operations, precision, FFT conventions and peak live memory; label as modeled |
| 105 distinct excitation recordings | Acquisition appendix and data release | Deduplicate; preserve raw words; document scale and uncertain metadata |
| Three valid idle CSVs | Acquisition appendix; optional noise-sensitivity input | Report raw ADC units, preprocessing and exclusions; do not claim calibrated microphone self-noise |
| 25 tiny three-channel clips | Metadata/exclusion case study | Preserve labels; state missing timing; no measured localization score |
| Quadrant tables | Optional geometric appendix | Label computed absolute pair-TDOA surfaces; do not call them experimental positions |
| Filter sketches | Supplement or development archive | Check actual response and shared-filter phase cancellation; keep only what informs the chosen question |
| MicroDSP library | Separate reusable software release | API documentation, meaningful reference checks, licenses, bounded performance claims; optional later software paper |
| Newer firmware | Development archive | Explicitly uncompiled/unvalidated in this evidence set; no device-performance table |
| Old four-microphone firmware stub | Development archive | Separate from the three-microphone paper implementation |
| Old root `.docx` | Historical source archive | Do not carry over unsupported “10 µs”, hedging-network or hardware-accuracy claims |
| Randomly forced 77% heatmap | Excluded historical illustration | Never include as experimental or simulated benchmark evidence |
| Corrupt/value-gated idle workbooks | Exclusion log | Keep originals; document why derivatives cannot supply noise statistics |
| Duplicate data directories | One canonical release manifest | Keep source files intact; deduplicate the release logically using hashes |

“Existing files only” does not require keeping every old result. It allows new computation using the existing code, mathematical models and recorded files. It does not supply missing sample-clock measurements, microphone dimensions, power logs, or new acoustic ground truth.

## 7. Experiment plan: first verify, then expand

### Gate 1 — establish a trustworthy direct path

**Budget: 8–12 author-hours. Run this before any large Monte Carlo campaign.**

Compare, on the same source directions and geometry:

1. Exact plane-wave delays with an independent least-squares direction calculation.
2. Exact spherical delays at finite distance, evaluated with the far-field estimator.
3. Rounded spherical delays at 16, 48, 96 and 192 kHz, with no reflections.
4. Fractional-delay synthetic waveforms and end-to-end GCC-PHAT, with no reflections.
5. The room generator with an explicit zero-reflection setting, using the same fractional-delay representation.

Use both the existing seven angles and a full-circle grid offset from the estimator's search grid. Sweep distance, including 1.5 m and a sufficiently distant reference, so the curvature contribution is visible. Add sources at known cardinal and non-cardinal directions to verify signs and channel order.

**Output:** a compact error table and a figure showing geometric versus numerical contributions. Establish a numerical error tolerance smaller than the smallest physical effect the article intends to interpret. An initial engineering target is below 0.05° or below one tenth of that effect, whichever is more appropriate; justify and freeze the final tolerance before evaluating the main study. This is a study-design choice, not a journal rule.

**Pass condition:** exact plane-wave inversion agrees to floating-point precision; end-to-end fractional propagation agrees with the reference within the declared tolerance; numerical refinement is convergent; spherical curvature is separately reported. If this fails, stop the main campaign and repair the implementation.

### Gate 2 — verify that the simulated room is the room being described

**Budget: 8–12 author-hours.**

- Preserve sub-sample arrival times with a validated interpolation kernel or another defensible band-limited propagation scheme. Check kernel length/oversampling convergence.
- Generate continuous source records with prehistory long enough for the modeled RIR. Crop steady-state analysis windows after convolution, while retaining startup as an explicitly separate condition.
- Compute decay curves and estimate supported EDT/T20/T30 quantities from the generated RIRs. State requested and realized decay values separately, including the fitted frequency band and extrapolation assumptions.
- Increase RIR duration and image-domain truncation until the chosen acoustic metrics and direction results stabilize. The current `K` is an image-index extent, not automatically a maximum reflection order.
- Cross-check a small set against an independently implemented image-source reference or analytical frequency-domain image sum. Reusing the same rounded tap placement in two scripts is not independent verification.
- Record direct-to-reverberant ratio, source distance, early-reflection arrival/direction, and relevant clarity metrics. RT60 alone cannot describe the directional error mechanism.

**Output:** a room-validation table, decay plots, direct-path comparison, and a numerical convergence plot.

**Pass condition:** the declared propagation band and geometry agree with the reference; decay estimates and localization outputs stabilize under refinement. If the independent reference disagrees, diagnose the difference before interpreting floors.

### Gate 3 — run a bounded, reproducible room ensemble

**Budget: 12–18 author-hours plus computation.**

Use a pilot first, then freeze the final matrix. An affordable starting design is:

| Factor | Proposed starting values | Purpose |
|---|---|---|
| Room geometry | Three different shoebox aspect ratios/sizes | Test dependence on geometry |
| Nominal decay setting | Three values spanning low/moderate/high reverberation | Compare with realized decay, rather than assuming equality |
| Array placement | Two positions, including an off-center position | Break the symmetry of the current centered model |
| Source direction | 12 off-grid azimuths spanning the full circle | Avoid cherry-picking seven favorable directions |
| Source distance | A controlled reference distance; additional near/far distances in a separate sensitivity block | Separate curvature from reflections without multiplying every cell |
| SNR | 0, 10 and 20 dB under one explicit convention | Show noise-limited and bias-dominated regimes |
| Independent records | Five seeds per scene/direction/SNR as an initial pilot allocation | Assess Monte Carlo precision; expand where uncertainty changes the conclusion |
| Frames per record | 32 continuous, non-overlapping analysis frames initially | Estimate short/medium averaging behavior |
| Long averaging subset | Six representative acoustic states, through 128 frames | Check long-T behavior without an unnecessarily large factorial study |

The core design is **18 acoustic states × 12 directions × 3 SNRs × 5 records × 32 frames = 103,680 frames**. The extended subset adds approximately **46,080 frames** if evaluated at one SNR with 12 directions and five 128-frame records per state. These are proposed workloads, not a claim that this many observations already exist or that this allocation is statistically sufficient. Time a small pilot and adjust before the full run.

Use identical waveforms/noise realizations for matched algorithm comparisons. Cache RIRs and common transforms. Evaluate costly baselines on a predeclared representative subset if necessary; document that subset instead of silently dropping difficult scenes.

**Primary metrics:** wrapped signed error, RMSE, median absolute error, 90th percentile, failure rate at a predefined angular tolerance, and per-scene bias. Show a full-circle error map and distributions across acoustic states. Do not average away systematic failures with one pooled RMSE.

**Pass condition:** the main conclusion survives different rooms/positions and independent records, or the paper explicitly narrows its claim to the configurations where it holds.

### Gate 4 — make the estimator comparison fair

**Budget: 6–10 author-hours.**

Keep the comparison focused:

- Band-limited GCC-PHAT + uniform least squares, with explicit physical lag bounds.
- Exactly specified gate/weight variants, sharing the same front end.
- SRP-PHAT with a declared angular grid, plus one refined-grid or locally refined reference.
- Native correlation plus parabolic peak refinement versus interpolated correlation, with identical input conditions and operation/memory accounting.
- MUSIC as a documented secondary baseline only if its covariance estimate, steering convention, bandwidth and numerical behavior can be verified. It need not dominate the paper.

Report whether source-band knowledge is fixed a priori or estimated. The current 300–3400 Hz mask knows the synthetic source band; that is an oracle assumption unless the operating band is part of the task definition. Test a small band-mismatch case so the main result does not depend on perfect hidden knowledge.

At each sample rate, keep bandwidth and physical observation duration controlled when asking about sampling itself. At each frame length, distinguish sample count from duration. At each aperture, inspect narrowband spatial ambiguities rather than extrapolating `1/R` indefinitely.

**Pass condition:** observed accuracy differences cannot be explained merely by different spectral information, search grids, source windows, or invalid peak ranges.

### Gate 5 — separate uncertainty from repeatability

**Budget: 6–10 author-hours.**

- Use independent records to validate any bias/floor estimate fitted on another set.
- Report Monte Carlo uncertainty conditional on a scene separately from the variation between rooms, placements and directions.
- Use a hierarchical/bootstrap resampling scheme that keeps complete records together and respects scene grouping.
- Treat curves at different averaging lengths as correlated when they reuse data.
- Test the independent-noise approximation with continuous steady-state records; account for error autocorrelation where it matters.
- Define “negligible benefit” using a practical equivalence margin. A small p-value is not a large design benefit; failure to detect significance is not equivalence.
- Use empirical bias/variance and quantiles where angular errors are multimodal. Do not force every condition into `b² + sigma²/T`.

**Output:** an error-budget table with clear uncertainty definitions, paired effect sizes, a held-out prediction check, and an explicit domain of applicability for the averaging law.

### Gate 6 — resource and acquisition evidence

**Budget: 5–8 author-hours.**

State the precision, FFT conventions, reused buffers, transform sharing, transcendental evaluations, and peak live memory in the analytical cost model. Host timings can be measured with warmups and distributions, but stay labelled as host timings. Do not convert them into ESP32 latency or power.

Keep the acquisition appendix short: unique-record inventory; approximate sample-rate/aliasing evidence with assumptions; clipping/noise in ADC units; and why the clips do not validate the intended DoA task. Do not turn the appendix into an independent microphone-calibration paper without the calibration evidence it requires.

**Pass condition:** every claimed hardware-related quantity is either supported by the existing recording files under stated assumptions or explicitly excluded. The main computational contribution stands without the appendix.

## 8. Execution schedule

The schedule assumes the author can work independently with the existing Python/C++ and mathematical material. Hours below are planning estimates, not measured completion times. Computation, learning an unfamiliar method, finding an independent verifier, and editorial correspondence can extend elapsed time.

### Concentrated route: 15 working days, approximately 84 author-hours

| Day | Hours | Work | Concrete deliverable / decision |
|---|---:|---|---|
| 1 | 5 | Freeze the evidence set, inspect exclusions, choose one method specification, prepare an accurate AI-provenance inventory | File manifest, claim ledger, agreed scope; policy question ready for the author to resolve |
| 2 | 6 | Reproduce direct-path rounding and curvature controls; verify sign and geometry | First control table; identify what the reported floor currently contains |
| 3 | 6 | Implement/verify fractional propagation against an independent reference | No-reflection agreement and refinement test |
| 4 | 6 | Correct source prehistory/steady-state handling; inspect RIR decay and truncation | Room-validation report; no nominal/realized RT60 confusion |
| 5 | 5 | Run a small room pilot; check baseline grids and spectral assumptions | **Choose Route A, B or C. Freeze the main question and experiment matrix** |
| 6 | 5 | Launch and monitor the core matched experiment matrix | Structured per-trial output and failed-run log |
| 7 | 5 | Finish fair estimator comparisons and the selected long-T subset | Comparison table with the same inputs and clearly stated baseline settings |
| 8 | 5 | Fit/check the bias–variance model using separated records; hierarchical uncertainty | Held-out prediction figure and uncertainty table |
| 9 | 5 | Check room/position/distance sensitivity and practical equivalence margins | Robustness figure; narrowed claims where necessary |
| 10 | 5 | Finalize computational costs and the short acquisition appendix | Modeled resource table; measured-data limitations table |
| 11 | 6 | Generate publication figures and tables from structured output | Stable figure/table set; no manual numeric drift |
| 12 | 7 | Human author writes methods, results and discussion around those figures | One complete, internally consistent manuscript |
| 13 | 7 | Verify references and novelty comparison; independent human technical read if available | Corrected citations, resolved major scientific comments |
| 14 | 6 | Format in LaTeX, shorten abstract, complete declarations and supplement | Compiling submission files with page/line numbering |
| 15 | 5 | Test clean reproduction, inspect submission package, prepare cover-letter points and reviewer suggestions | **Submission-ready package only if every gate passes** |

A ten-working-day version requires longer daily hours and substantial reuse of work already understood by the author. Compressing the verification steps is the wrong place to save time. Save time by reducing the number of research questions, not by skipping controls.

### Sustainable route: 20 author-hours per week

| Week, if starting 7 September | Main work | Exit condition |
|---|---|---|
| 7–11 September | Evidence/specification freeze and direct-path verification | Main source of the current apparent floor understood |
| 14–18 September | Fractional/steady-state room verification and pilot | Simulator and final question defensible |
| 21–25 September | Main matched comparisons and statistical analysis | Stable results and uncertainty |
| 28 September–2 October | Figures, manuscript, references, supplement | Earliest plausible submission package if results/policy are settled |
| 5–9 October, if needed | Independent technical review and corrections | All important objections answered with evidence |
| 12–16 October, if needed | Reproduction/release package and final checks | Submission package complete |

### Stop, narrow, or continue rules

| Trigger | Action |
|---|---|
| Fractional direct-path/reference implementations disagree beyond tolerance | Stop the main experiments; resolve the implementation discrepancy |
| The room floor mostly disappears after correcting propagation/startup | Move to Route A or C; report the corrected physical result without preserving the old headline |
| Bias varies strongly with position/early reflections at similar RT60 | Replace an RT60-only law with a conditional error budget and geometry-sensitive explanation |
| Confidence weighting helps only in a narrow subset | Report that subset and practical effect size; do not force a universal negative conclusion |
| Refined SRP changes the algorithm ranking | Retain the fair ranking and distinguish speed/accuracy operating points |
| No useful result generalizes beyond the custom implementation | Pause journal submission; release a documented benchmark correction or strengthen the research question |
| Only one strong finding survives | Use the four-page route if it is independently verified and scientifically substantial |
| The journal's AI-policy interpretation conflicts with the actual workflow | Resolve it honestly before submission; human rewriting/verification and disclosure must reflect what happened |
| Proposed work starts requiring new recordings | Remove it from this plan or make it a clearly separate future project |

## 9. Main-paper structure

Aim initially for **8–10 typeset pages**, within the journal's typical Scientific Article range, and approximately **4,500–5,500 words of main text** before final layout adjustments. This is a practical target, not an additional journal limit. Let the evidence determine the final length.

| Section | Question it must answer | What belongs there |
|---|---|---|
| Title and abstract | What was studied, by what verified method, and what was actually learned? | Specific problem and scope; no “novel”, “first”, universal best-performance or deployed-hardware claim |
| Introduction | Why does this error separation matter to acoustics researchers? | Minimal arrays, misleading benchmark conclusions, exact gap relative to published work |
| Signal model and estimator | What mathematical object and implementation were evaluated? | Geometry, source band, acquisition model, sign convention, regularization, lag search, LS/circular statistics |
| Numerical verification | How do we know the simulator and estimator implement the intended problem? | Exact direct path, spherical curvature, fractional delay, steady state, decay/refinement, independent reference |
| Evaluation protocol | What cases and uncertainty structure define the study? | Room matrix, seeds, source construction, SNR, held-out records, metrics, fairness settings |
| Results | What changes after numerical and physical effects are separated? | Main controlled comparison, conditional bias, temporal behavior, practical algorithm differences, resource trade-offs |
| Discussion | Which design choices follow, and when do they stop applying? | Useful decisions, limits of model/geometry/source class, differences between modeled and measured evidence |
| Conclusion | What can a reader do differently as a result? | Two or three supported consequences with the scope intact |
| Back matter | How can the work be inspected and reused? | Funding, conflicts, AI-use disclosure as applicable, Data Availability, contribution statement, supplement |

### Abstract repair

The current abstract is **605 whitespace-delimited words**, approximately three times the maximum. It also tries to announce a full paper's worth of secondary results. Write the abstract last, after the verification and analysis are fixed.

Use the following **195-word allocation** as a writing brief, not prewritten submission language:

- **Introduction, about 30 words:** identify the practical problem of interpreting error and computation in a minimal three-microphone direction estimator.
- **Methods, about 55 words:** describe controlled propagation/numerical comparisons, independently verified room simulation, scene variation, matched baselines and uncertainty.
- **Results, about 75 words:** include no more than two or three numerical findings from the final verified outputs, with their conditions. Explain whether rounding, curvature, startup, reflections, or noise dominated.
- **Discussion, about 35 words:** state the actionable implication and the boundary: single-source planar simulation, with acquisition audit where relevant and no measured embedded-performance claim.

For Route C, compress to the journal's **100-word** abstract limit. Remove the long catalogue of four negative results, “in any reverberant room”, “the answer is not the estimator”, the universal impossibility wording, and the precise unverified hardware implications.

## 10. Figure and table plan

Every final scientific figure should be generated from versioned numerical output using a workflow consistent with the clarified journal policy. The author must review the values, axes, uncertainty, and provenance. The existing generated figures are useful design references; their current values are not automatically final.

| Main figure | Content | Reviewer question answered |
|---|---|---|
| 1. Geometry and verification chain | Clearly distinguish radius, pair spacing, source distance and the signal-processing stages | What physical problem is actually being solved? |
| 2. Direct-path numerical controls | Exact versus rounded versus fractional propagation; distance/rate/refinement behavior | Could the claimed acoustic effect be numerical error? |
| 3. Verified room behavior | Realized decay and conditional bias across room/placement settings | Is the room model credible, and does one RT60 value predict a unique error? |
| 4. Temporal accuracy | RMSE/quantiles versus physical observation duration; held-out bias prediction and appropriate intervals | When does averaging help, and what limits it? |
| 5. Fair algorithm comparison | Matched error distributions; grid refinement; gate/weight practical effect | Does the ranking survive comparable information and numerical resolution? |
| 6. Design trade-off | Accuracy versus explicitly modeled computation/memory, with aperture/frame sensitivities where interpretable | What should another researcher choose under a stated budget? |

Main tables: (1) exact model/configuration and scope, (2) numerical verification tolerances/reference comparisons, (3) principal effect sizes and uncertainty, (4) modeled resource costs if not shown effectively in Figure 6.

Supplementary material can carry full parameter grids, all scene-level results, RIR-convergence details, extended averaging analysis, unretained baselines, and the acquisition case study. A main figure should earn its space by answering one of the core research questions. A collection of plots generated by the harness is not itself a narrative.

### Figure quality checks

- Use units on every axis and identify whether errors are signed, absolute, median, percentile, or RMSE.
- Define every error bar; distinguish uncertainty of a mean from variability between acoustic scenes.
- Show source conditions and record counts in captions or an adjacent protocol table.
- Use readable lettering at final column width, distinct line styles/markers, and accessible colors.
- Retain vector originals; inspect the actual LaTeX-generated PDF at 100% zoom.
- Never label a simulation panel “measured” unless the caption makes clear that the quantity was computed from simulated data.
- Do not include the forced 77% heatmap, unsupported hardware screenshots as evidence, or a plotted curve silently transcribed from an obsolete results table.

## 11. Reproducibility and release package

The critical improvement is a **single numerical source of truth**. Every claim in the paper should map to a recorded output, configuration, software version, and analysis procedure.

Suggested release structure:

```text
README
LICENSES/
environment/
configs/
data/raw_manifest/
data/acquisition/
data/exclusions/
results/per_trial/
results/summary/
src/simulation/
src/estimators/
src/analysis/
figures/
manuscript/
supplement/
```

This is a proposed structure; the current workspace has not been reorganized.

### Required contents

1. **Manifest:** original relative path, canonical record ID, SHA-256, origin, raw/derived/synthetic status, channels, units/scaling, date if known, sample rate and whether measured or inferred, source/room metadata, and explicit unknowns.
2. **Exclusions:** reason for excluding corrupt data, range-gated derivatives, synthetic illustrations and duplicate files. Exclude an item from analysis without deleting the original.
3. **Configurations:** microphone coordinates, physical constants, bands, frame/hop lengths, numerical refinements, room properties, source placement, SNR definition, random seeds and estimator settings.
4. **Per-trial outputs:** scene ID, record ID, seed, true azimuth, estimate, wrapped error, quality score if applicable, failure flag, and evaluation subset. Summary tables alone are not enough to reproduce uncertainty calculations.
5. **Environment:** a pinned, supported runtime and package versions. The present workspace has no complete environment manifest, and its old logs refer to a different operating system/runtime.
6. **Run instructions:** one small verification example, one representative experiment, and the full reproduction command. State expected duration/resource needs after a pilot measures them.
7. **Claim ledger:** each final numerical sentence and figure/table linked to an output file and analysis step. Archive obsolete values separately.
8. **Licensing:** use licenses appropriate to material you own; preserve existing library licenses and third-party notices. Do not assume all downloaded literature, dependencies or recordings can be relicensed together.
9. **Versioned archive:** when ready, use a repository plus a permanent release DOI for the cited version. The DOI and public deposit belong to the submission/release stage; none has been created in this planning task.

### Meaningful verification

Spend testing time on physical and statistical correctness: channel/sign permutations, exact delay recovery, fractional propagation convergence, no-reflection agreement, room steady state, sample-rate propagation through all estimators, wrapped angles, scene/record independence, and equality of declared paired inputs. A test that a figure function returns six filenames is useful plumbing but does not validate a research conclusion.

A clean reproduction should regenerate the final tables and representative figures from the archived configuration. Make numerical tolerances explicit; byte-identical plots across operating systems are not necessary if the underlying results agree within those tolerances.

## 12. Submission package and reviewer preparation

### Final package

- Main LaTeX source, bibliography source and compiled bibliography, class/style files required to compile, and a checked PDF.
- Separate figure files in accepted formats; table sources; a concise supplement.
- A final ≤200-word abstract, or ≤100 words for a Short Communication.
- Accurate funding, conflicts, contribution, Data Availability and AI-use statements. A funding or acknowledgement field is not “hardware data”; resolve it as an authorship/declaration fact.
- Repository/release DOI and complete access instructions, once authorized and created.
- Three suitable reviewer suggestions from more than one country, with expertise and conflicts checked from current institutional sources.
- A short cover letter explaining the research question, the actual new contribution, why Acta's audience benefits, and the evidence/limitations. If the manuscript was previously submitted elsewhere, answer the journal's originality/submission questions accurately.
- Final inspection of the PDF assembled by Editorial Manager before the author approves it.

### Cover-letter content brief

Lead with the acoustic problem and resulting insight. Identify the paper as a verified computational study. State the controlled numerical checks and reproducible package. Explain the relation to relevant Acta work without implying an endorsement. Describe the contribution using the final results; do not claim measured hardware validation, universal optimality, guaranteed novelty, or a journal acceptance probability. Include an accurate AI-use statement under the applicable policy.

### Likely reviewer objections and the evidence that answers them

| Objection | Prepare this answer before submission |
|---|---|
| “This is textbook GCC-PHAT.” | State the verified error-separation contribution and the new quantified, generalizable result; show how it changes a design or benchmarking decision |
| “Your floor is generated by the simulator.” | Exact/fractional direct-path controls, numerical refinement, curvature separation and independent reference |
| “You simulated only one room.” | Predeclared room/placement ensemble and scene-level results; explicit generalization limits |
| “RT60 does not specify early reflections.” | Realized decay, direct-to-reverberant ratio and geometry-conditioned analysis |
| “Your averaging uses independent artificial frames.” | Continuous steady-state records, error autocorrelation, and separated fitting/validation records |
| “The comparisons are unfair.” | Matched signals/bands, physical lag bounds, specified windows/regularization, grid sensitivity and verified baseline implementations |
| “The confidence result is statistically weak or practically trivial.” | Paired effect size, uncertainty, declared practical margin, and conditions where it helps or fails |
| “Your speech and hardware claims are unsupported.” | Accurate synthetic-source terminology, explicit acquisition appendix, and no measured deployment claim |
| “I cannot reproduce the numbers.” | Per-trial outputs, environments, configs, traceable figures and a tested reproduction entry point |
| “The work is too broad.” | One main question; move peripheral filters, near-field lookup tables and library development to the supplement or archive |

During revision, maintain a response table with each comment, action, changed location, and supporting result. Correct the paper when a reviewer identifies a valid issue. A repeatable workflow makes revisions much faster than rebuilding disconnected figures and prose.

## 13. Everything else you could do with these assets

These are research options, not an instruction to execute all of them. Estimated effort is incremental author effort after the basic pipeline is trustworthy; new-data requirements override any short estimate.

| Direction | Existing files sufficient to begin? | Approximate extra effort | Publication value and decision |
|---|---|---:|---|
| Numerical propagation/curvature error separation | Yes | Core plan | Strongest immediate candidate if independently verified and generalizable |
| Continuous-time/steady-state averaging and correlated errors | Yes, through simulation | Core plan | Strong complement to the main error-budget question |
| Bandwidth/oracle-band mismatch study | Yes | 4–8 h | Include a small controlled test; the underlying technique is established |
| Native IFFT/parabolic versus interpolated correlation trade-off | Yes | 6–10 h | Useful practical result when error and operation/memory assumptions are aligned |
| Geometry, aperture and source-distance sensitivity | Yes | 6–12 h | Include enough to bound the claim; a larger optimization project is optional |
| Clock offset, channel delay, position error and temperature sensitivity | Yes as simulations | 8–16 h | Valuable robustness extension; simulated perturbations are not measured tolerances |
| Empirical heavy-tail/noise-distribution sensitivity | Partly | 6–12 h | Use low-rate noise evidence cautiously; do not invent high-rate spectra or cross-channel coherence |
| Confidence-score calibration | Yes for a simulated calibration study | 12–24 h | Requires disjoint training/validation scenes and calibration metrics; not calibrated real-world reliability |
| Bias-aware stopping or adaptive averaging | Yes as a simulation study | 16–30 h | Interesting later method only if stopping does not secretly use ground-truth bias unavailable at inference |
| Three versus four microphones / redundancy trade-off | Yes as simulations | 10–20 h | Potential follow-up: define what an extra channel buys under an equal aperture/compute budget |
| Near-field observability and range conditioning | Yes analytically/synthetically | 8–16 h | Useful appendix or later methods question; current lookup tables alone are not a new localization result |
| Filter-phase and channel-mismatch audit | Yes | 4–8 h | Supplementary quality improvement; avoid a standalone “new filter” claim from standard designs |
| Acquisition-audit tutorial or reproducible case study | Yes, with unknowns retained | 10–20 h | Companion resource; journal-paper novelty is less certain than the computational route |
| Standalone data paper for the current recordings | Partly | 15–30 h | Limited by missing metadata and invalid intended sampling; package with the main study before seeking a separate article |
| MicroDSP numerical-correctness and portability release | Yes for software/host checks | 20–40 h | Worth developing separately; a software venue may fit better after utility/adoption evidence exists |
| MicroDSP performance paper | Only partly | 30–60 h plus benchmarks | Requires meaningful comparisons; supported hardware timing would need access beyond this plan |
| ESP32 real-time, latency, RAM and power paper | No for measured device claims | New hardware work | Defer under the user's existing-files constraint |
| Real-room generalization using an external public multichannel dataset | Requires additional external data | 15–30 h after access/setup | Optional later strengthening, not a hidden prerequisite; match geometry/timing/ground truth first |
| Learned/ML direction estimator | No sufficient task-specific training/validation evidence currently | Substantial new study | Do not add to the speedrun merely to increase perceived novelty |
| Speech recognition, sound-event classification or drone detection | No suitable labelled corpus currently | New data and validation | Application ideas only; no basis for classification-performance claims |
| Human hearing, assistive benefit or usability study | No | New participants/protocol/data | Future project, outside the present computational evidence |
| Calibrated microphone frequency response or acoustic self-noise | No | New calibrated measurements | Cannot reconstruct from aliased/uncalibrated captures |
| Measured 2-D/3-D multi-source localization | No | New acquisition/ground truth | Separate research program |
| Formal review of all Acta acoustics topics | Literature exists, but scope is too broad | Substantial editorial work | The current survey is planning support. A journal Review Article needs a defined topic and advance editor contact |

**Portfolio recommendation:** prepare the single computational article and its companion release first. Develop MicroDSP as a separate software asset. Revisit a hardware paper only when measured hardware evidence becomes available. Avoid splitting one small result into several overlapping submissions.

## 14. The first five actions

1. **Freeze one specification and one claim ledger.** Use the compact draft as the prose base, but let verified code/results determine the final method description.
2. **Run and independently verify the direct-path controls.** Establish how much error already exists before reflections; separate curvature and discretization.
3. **Verify fractional, continuous steady-state room simulation.** Measure realized decay and numerical convergence before producing a new headline floor.
4. **Choose one paper route from the pilot.** Freeze the scope, matrix and practical success/equivalence criteria. Resolve the AI-provenance policy question early enough to avoid wasted submission preparation.
5. **Build every figure, table and numerical sentence from the same versioned outputs.** Then write, format, review and submit the paper that the evidence supports.

The speed advantage comes from a narrower, verified argument and a reproducible package. The extensive existing work supplies a useful starting point; the current draft's strongest claims still need the controls above.

## Sources and accompanying files

- [Scientific audit](/home/ani/Desktop/sound_local/paper/publication_speedrun/SCIENTIFIC_AUDIT.md)
- [Searchable journal register](/home/ani/Desktop/sound_local/paper/publication_speedrun/READING_REGISTER.html)
- [Complete text register](/home/ani/Desktop/sound_local/paper/publication_speedrun/LITERATURE_REGISTER.md)
- [Journal instructions](https://acta-acustica.edpsciences.org/author-information/instructions-for-authors)
- [Journal archive](https://acta-acustica.edpsciences.org/component/issues/?task=all&Itemid=121)
- [Data policy](https://acta-acustica.edpsciences.org/author-information/data-policy)
- [Benchmarking collection](https://acta-acustica.edpsciences.org/component/toc/?task=topic&id=2448)
- [2026 journal editorial](https://doi.org/10.1051/aacus/2026076)

The research folder retains the Crossref responses, publisher DOI census, literature register JSON, data-file hash manifest, direct-path diagnostic, and final screening receipt. Those are audit records rather than additional manuscript results.
