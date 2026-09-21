# Direction A research plan: preprint first, Acta Acustica style

**Updated by author decision on 7 September 2026.** Target: a **preprint prepared through assistant-led execution**, using Acta Acustica's scientific and presentation standards. A later Scientific Article in *Acta Acustica* remains an option, primarily within **Audio Signal Processing and Transducers**, with **Computational and Numerical Acoustics** as a related field. Follow the [preprint execution checklist](/home/ani/Desktop/sound_local/paper/publication_speedrun/DIRECTION_A_PREPRINT_TODO.md) for task status, ownership, and current prerequisites.

**Working title:** *Separating numerical and acoustic error in three-microphone direction-of-arrival estimation*.

The paper will investigate how numerical propagation, wavefront curvature, estimator resolution, source startup, noise, and room reflections affect estimated sound direction. Its intended contribution is a verified explanation of those effects and a practical procedure for deciding whether an apparent accuracy limit is numerically credible. That contribution remains to be established by the work below.

**Execution timing:** estimate elapsed work from measured pilot throughput and the remaining verification tasks. The earlier 80–120 author-hour estimate applied to a human-led journal-preparation workflow and is not an automated-runtime forecast. The assistant now owns implementation, experiments, analysis, figures, drafting, and packaging; author review and public-release decisions remain with the author.

**Current status — 8 September 2026:** A01–A35 are complete. The [author-review package](/home/ani/Desktop/sound_local/paper/direction_a_preprint/AUTHOR_REVIEW.md) contains the final nine-page preprint, five-page supplement and verified source/data archive. A stronger joint-refinement check required preserving and superseding the initial run; the entire corrected 1.2-second/extent76/P32 campaign was completed and audited. The final paper uses 276,480 revised primary estimates. Clean reproduction matched 8,640 representative estimates exactly and all six main figures byte for byte. Follow `progress.json`, `FINAL_CLAIM_LEDGER.md` and `NUMERICAL_NOTES.md` for evidence. The design below records the original plan; final claims and allocation are documented in the package. Server-specific tasks remain deferred. Conflicts, final scientific review, licenses and public release await author decisions.

1. **The scientific question and the contribution we need to establish.** The central question is: *When a minimal microphone array appears to reach a direction-estimation error floor, how much of that behavior survives independent verification of the numerical model?*

    Three research questions determine the experiments and the paper:

    | Question | Evidence needed | Intended reader benefit |
    |---|---|---|
    | RQ1. How do propagation rounding, wavefront curvature, and estimator resolution affect apparent direction error? | Exact delay controls, independent waveform references, numerical refinement, and geometry/rate/distance sensitivity | A way to establish adequate numerical precision for a specified angular effect |
    | RQ2. How do reflections and source startup change the result after propagation is verified? | Matched reflection-on/off and startup/steady-state comparisons across room configurations | A physically interpretable account of persistent error within the tested model |
    | RQ3. When does averaging reduce error, and when does the remaining bias limit improvement? | Continuous records, uncertainty that respects temporal dependence, and prediction on independent records | A bounded statement about useful observation duration and remaining bias |

    The candidate original contributions are a reproducible verification protocol, a controlled study of interacting numerical and acoustic effects, and a geometry-aware precision criterion. GCC-PHAT, triangular arrays, fractional-delay methods, and circular averaging are established techniques. The paper needs a result or decision rule that other acoustics researchers can use beyond this implementation.

2. **Why Acta Acustica remains the style and scientific reference.** Frame the introduction around the credibility of acoustic inference from computational experiments. The journal explicitly accepts original models as well as experiments; a new hardware campaign is not a general requirement. Use a Scientific Article's methodological and explanatory structure for the preprint. Journal eligibility is a separate later decision.

    Use the following reading anchors selectively, together with a focused search across other journals:

    | Published work | Role in our argument | Boundary on the comparison |
    |---|---|---|
    | [Rotational mismatch index, 2026](https://doi.org/10.1051/aacus/2026061) | Example of deriving a bias mechanism and turning it into a practical tolerance | Its rotating-array formulas and empirical thresholds do not transfer to our stationary array |
    | [Pipe-impedance verification and validation benchmark, 2026](https://doi.org/10.1051/aacus/2026048) | Example of separating implementation, numerical, model, and measurement uncertainty | Our computational verification does not establish agreement with a physical device |
    | [Room-acoustic discretization study, 2024](https://doi.org/10.1051/aacus/2024071) | Example of connecting numerical resolution with acoustic consequences | We must establish the specific significance of delay placement for our estimation task |
    | [Force-radiation-mode numerical study, 2026](https://doi.org/10.1051/aacus/2026043) | Precedent for an independently checked numerical contribution | Numerical work still needs substantial scientific value |
    | [Reverberation-time calibration, 2025](https://doi.org/10.1051/aacus/2025011) | Supports distinguishing a requested decay setting from the simulated decay actually obtained | A single decay value does not determine directional bias |

    Before the main campaign, complete a novelty table covering image-source fractional-delay methods, TDOA interpolation bias, finite-distance model mismatch, small-array conditioning, and reverberant averaging. Include foundational GCC-PHAT/image-source literature and the existing [triangular-array](https://doi.org/10.1109/ICRAMET47453.2019.8980432) and [subsample GCC-PHAT](https://doi.org/10.1109/ICOSP.2008.4697676) prior-art leads. Record what each source already establishes and what our study would add. The existing five-year Acta review is a scoping review, not proof of novelty across the literature.

3. **Scope and starting evidence.** The primary study uses one stationary broadband synthetic source, three ideal matched omnidirectional microphones, horizontal azimuth estimation, and three-dimensional specular shoebox rooms. The estimator uses a plane-wave direction model; finite-distance curvature is an explicit experimental factor. Findings apply within these assumptions.

    Use the existing mathematical and software material to begin. New computation is required. Existing recordings can support a short supplementary acquisition audit if useful, but cannot establish the intended hardware localization performance. Broader compute/energy optimization, firmware deployment, moving sources, speech validation, learned estimators, multiple-source separation, and a new recording campaign are separate projects. Limit resource discussion to the cost of achieving the numerical precision used in this paper.

    The existing analytical audit provides motivation:

    | Diagnostic at the original seven azimuths | Recorded result |
    |---|---:|
    | Exact spherical delays interpreted by the far-field direction solve | 0.3601° RMSE |
    | Spherical arrivals rounded to samples at 48 kHz, with no reflections | 1.4438° RMSE |
    | Lowest room-related floor reported by the current draft | About 1.48° |

    The first two rows are noiseless delay-level diagnostics, not end-to-end waveform-estimator results. They show that numerical and geometric effects could confound the old interpretation. They do not establish that rounding explains the complete room result. The corresponding full-circle diagnostic gives different values, reinforcing the need for broad angle coverage. Do not subtract these RMSE values to assign independent physical contributions. Source: [diagnostic output](/home/ani/Desktop/sound_local/paper/publication_speedrun/research/direct_path_rounding_diagnostic.json).

4. **Stage 1: freeze the specification and verify a direct path.** Preserve the current code, logs, and results with a dated manifest and file hashes before changing implementations. This workspace currently has no Git repository; a reproducible snapshot is required whether version control is introduced later or not. Record runtime and dependency versions and use explicit random seeds per scene and record.

    Freeze microphone coordinates, channel order, delay sign, speed of sound, source/acquisition bands, windows, regularization, physical lag bounds, correlation interpolation, and the direction solve. Reconcile code and equations. The nominal geometry is a **5 cm circumradius**, **8.66 cm pair spacing**, and **10 cm circumscribed-circle diameter**; these are simulation dimensions, not measured board dimensions.

    Compare the following in sequence:

    | Control | What it establishes |
    |---|---|
    | Exact plane-wave delays and an independently coded solve | Geometry, sign, channel order, and inversion correctness |
    | Exact spherical delays at several source distances | Error from applying the far-field estimator to curved wavefronts |
    | Rounded spherical arrivals without reflections | Direction error introduced by discrete arrival placement |
    | Independently generated fractional-delay waveforms | Propagation accuracy separate from the estimator's finite-window and interpolation behavior |
    | The room generator with reflections explicitly disabled | Agreement between room and direct-path implementations for the same physical problem |

    Use the original seven angles for reproduction, then a dense 720-angle grid at 0.5° spacing with a 0.13° offset. Include separate cardinal-direction and channel-permutation checks. Start with 16, 48, 96, and 192 kHz; equilateral circumradii of 2.5, 5, and 10 cm; and direct-path distances of 0.5, 1.5, 5, and 20 m. Keep bandwidth and physical observation duration fixed when comparing sampling rates. The larger distances belong to free-field controls, not automatically to the room matrix.

    Independently refine propagation interpolation and correlation peak estimation. For example, examine correlation interpolation factors 8, 16, 32, and 64, extending only if needed. Agreement between two waveform generators must be tested using the same estimator; agreement with an exact delay solve is a different test. A persistent finite-window or estimator error must be characterized rather than silently attributed to propagation.

    **Checkpoint:** exact plane-wave inversion agrees within numerical precision; independently generated direct paths agree within a declared angular tolerance; refinement is convergent; curvature and estimator effects are separately documented. Use **0.05° as an initial numerical-discrepancy target**, appropriate to interpreting an effect of about 0.5° or larger. If the intended effect is smaller, tighten the tolerance before freezing the main campaign. This is a study-design target, not a journal standard or a promised accuracy result.

    Deliver a signed-error map, a reference-comparison table, and the final estimator specification. A failed checkpoint leads to implementation repair before room results are interpreted.

5. **Stage 2: verify the room and run an attribution pilot.** Preserve fractional arrival times, supply continuous source prehistory, and analyze steady-state windows after the full simulated response can contribute. Treat source onset as a separate condition. Reflections must have an explicit on/off control; setting nominal RT60 to zero is not a substitute.

    Check direct-path time and amplitude, reflection coordinates and amplitudes, interpolation support, response length, and image-domain truncation. The existing parameter K controls image-index extent and should be described that way. Extend response duration and image coverage until the relevant decay and direction quantities stabilize. Estimate EDT/T20/T30 only where the simulated decay supports the fitting interval, with the frequency band and extrapolation clearly stated. Record direct-to-reverberant energy and the timing, strength, and direction of important early reflections.

    Use an independent frequency-domain image sum or a separately implemented validated room reference for a small set of cases. Check image enumeration as well as fractional propagation; sharing the same image list and rounded tap placement would leave common errors unchecked. This verifies a specified room model, not physical validity for every real room.

    Pilot matched combinations of **rounded/fractional arrivals × source-onset/steady-state windows × reflections off/on**. Keep source distance, underlying source realization, estimator, and noise paired. Add noiseless cases to distinguish systematic effects from finite-record noise. Inspect interactions: the effect of rounding can change in the presence of reflections.

    For onset versus steady state, use identical source samples during the analysis interval, with zero versus populated prehistory. Also reproduce the legacy procedure that restarts the source for each short frame in a separate diagnostic. One continuous recording beginning at source onset and repeated startup-only frames are different protocols; their averaging curves must be labeled separately.

    **Checkpoint:** reference agreement and numerical refinement meet the declared tolerance; supported decay metrics stabilize; the pilot shows a meaningful question beyond repairing one script. Freeze the main matrix, effect-size target, uncertainty procedure, estimator settings, and workload only after this checkpoint. Retain the pilot separately from confirmatory records.

6. **Stage 3: execute a bounded experiment set for A.** The following is the proposed starting matrix, subject to the pilot and a recorded freeze. No matrix entries are completed results.

    | Factor | Default starting choice |
    |---|---|
    | Room dimensions | 6 × 5 × 3 m; 5 × 4 × 2.8 m; 8 × 6 × 3.2 m |
    | Array center | Room-relative coordinates (0.50, 0.50, 0.50) and (0.60, 0.45, 0.50) |
    | Nominal decay settings | 0.15, 0.30, 0.60 s; report the realized simulated decay separately |
    | Core geometry | Equilateral triangle, 5 cm circumradius, original orientation |
    | Source | Same height as array center, 1.5 m distance, 12 angles at 7.37° + 30°k, k = 0,…,11 |
    | Sampling and frames | 48 kHz; 2048 samples per frame; non-overlapping frames; 32 continuous analysis frames per record |
    | Signal and estimator band | Fixed task band of 300–3400 Hz; label the source band-limited noise |
    | SNR | 0, 10, 20 dB under one explicit convention |
    | Independent records | Five per scene/direction/SNR initially; increase if pilot precision is inadequate |
    | Primary estimator | Fully specified, physically bounded GCC-PHAT with uniform least squares |

    Validate that every microphone and source lies inside the room, with at least 0.20 m source-to-wall clearance for the core matrix. Every azimuth produces its own room response. A room/placement/decay setting is an acoustic state; a direction-specific source placement is a scene. Random records within one scene do not constitute additional rooms.

    Define SNR using clean **direct-path band power** averaged over microphones in the reference analysis interval, relative to noise power in the same band. Use that reference to set the noise for every paired propagation/reflection condition. Report the resulting total-field SNR separately where relevant. The primary noise is independent between microphones and passed through a declared common acquisition filter. This prevents a stronger reflected field from silently changing the noise level in an attribution comparison.

    | Experiment block | Starting workload and purpose |
    |---|---|
    | Core corrected rooms | 3 rooms × 2 placements × 3 decay settings × 12 directions × 3 SNRs × 5 records × 32 frames = **103,680 primary-estimator frame evaluations** |
    | Attribution block | Six predeclared states: every room at both placements, using 0.15 s for the centered position and 0.60 s for the off-center position. At 10 dB, run all eight propagation/startup/reflection combinations: 92,160 evaluations; **80,640 additional** after reusing the corrected steady-state reflection-on cell from the core |
    | Independent long-record block | The same six states × 12 directions × 10 new records × 128 frames, at 10 dB = **92,160 additional evaluations**. Within each scene, use five records to estimate bias/correlation and five to test the prediction |

    The default total is **276,480 primary-estimator frame evaluations**, before verification, sensitivity checks, or secondary estimators. Paired configurations share underlying random realizations and are not independent observations. Each short record spans about 1.37 s of analyzed audio; each long record spans about 5.46 s, in addition to prehistory. Time and profile a pilot before accepting this workload. Cache responses and share transforms where the implementation permits.

    Keep sensitivity work targeted. Use the direct-path radius/rate/distance controls from Stage 1 and predeclare small room subsets for a changed array orientation, one non-equilateral geometry, one altered wall-absorption distribution, and one source spectrum that does not perfectly fill the analysis band. Freeze valid coordinates and settings before evaluation. These checks bound the claim; they are not a full design-optimization campaign.

    Use refined SRP-PHAT on a fixed subset to test whether the central attribution depends on GCC-PHAT alone. Specify identical inputs, bands, and windows; refine the SRP angular search until grid error is below the chosen tolerance. Confidence variants and MUSIC belong in the supplement only if they answer a remaining research question and their implementations can be verified. A narrow comparison is sufficient for A.

7. **Stage 4: analyze effects without turning numerical artifacts into physical laws.** Retain signed wrapped error, RMSE, median absolute error, 90th percentile, and per-scene circular bias. Define a failure as absolute angular error exceeding **5°** for the initial protocol, while also reporting the full distribution; label 5° as a study convention. Keep failed and ambiguous estimates visible.

    Report paired changes in errors and squared errors, including propagation/startup/reflection interactions. Avoid an additive stacked error budget unless an applicable decomposition is established. RMSE contributions cannot generally be subtracted or combined as if they were independent variances.

    Estimate uncertainty by resampling complete records within scenes, retaining pairing between variants. Report variation across the finite room/placement/direction matrix separately. With only three chosen room geometries, do not present a narrow confidence interval as a population estimate for all rooms. Curves at different averaging durations reuse records and are correlated.

    Evaluate averaging at 1, 2, 4, 8, 16, and 32 frames, with 64 and 128 in the long-record block; show physical durations. Compare observed behavior with a small-error bias/variance approximation only where the angular distribution supports it. Include temporal covariance when needed. Fit or estimate on one record set, then test on the disjoint set. Report empirical distributions for multimodal cases.

    Derive a candidate geometry-aware relation between arrival-time precision and angular error. Whole-sample rounding gives each arrival an error of at most half a sample, but pair-delay errors share microphones and are correlated. Incorporate array conditioning and direction dependence. Verify the criterion against independent reference cases and declare its approximation range. A ratio involving sound speed, sampling rate, and microphone spacing is a possible scaling variable; it is not a Nyquist theorem or proof that fractional delays become unobservable.

    **Checkpoint:** each central claim has a traceable effect estimate, uncertainty appropriate to its sampling unit, an independent check, and explicit limits. If effects vary by scene, report that variation and narrow the claim. Similar decay times need not imply similar direction error.

8. **Stage 5: build the article around the verified findings.** Target 8–10 typeset pages, within the journal's typical Scientific Article length of up to 12 pages. Write the abstract after the results are fixed. Its maximum is 200 words and its structure must cover introduction, methods, results, and discussion.

    | Article component | Purpose and approximate space |
    |---|---|
    | Introduction | Acoustic problem, closest literature, precise gap, three research questions; about 1 page |
    | Physical model and estimator | Geometry, source/room assumptions, delay sign, bandwidth, exact method; about 1–1.5 pages |
    | Verification and evaluation protocol | Independent references, tolerances, controls, scene matrix, uncertainty; about 1.5–2 pages |
    | Results | Numerical/geometric attribution, room effects, averaging, precision criterion; about 2.5–3 pages |
    | Discussion and conclusion | What researchers can do differently and where the findings apply; about 1 page |
    | References and declarations | Allow remaining space; shorten secondary material before expanding the main question |

    Five main figures should carry the argument: (1) geometry and verification chain; (2) direct-path error and convergence across angle/rate/distance; (3) paired room/startup/reflection effects and interactions; (4) averaging with predictions tested on independent records; (5) the precision criterion and its verified applicability range. Use a configuration table, a reference/tolerance table, and a principal-effect table. Move full scene tables, detailed room convergence, secondary baselines, and any acquisition audit to the supplement.

    If the proposed precision criterion does not survive verification, Figure 5 must present the actual bounded finding or be removed. No figure, title, or abstract result is predetermined. Generate preprint figures deterministically from verified numerical output, preserve assistance provenance, and check the chosen preprint server's policy before public release. The Acta-specific policy below applies if a later journal submission is pursued.

9. **Execution ownership and concrete outputs.** The assistant performs the technical research and prepares the preprint. The author retains responsibility for understanding and approving the final claims, authorship, disclosures, and public release. An independent technical reader, if available, can challenge the reference checks and strongest claim; mathematical independence between implementations remains necessary regardless. Use the execution checklist to resume and record progress.

    | Milestone | Main work | Exit output |
    |---|---|---|
    | 1 | Evidence snapshot; novelty comparison; provenance inventory; direct-path specification and controls | Frozen baseline and initial verification table |
    | 2 | Fractional room propagation; continuous sources; decay/convergence checks; independent room reference; attribution pilot | Verified room report and frozen experiment matrix |
    | 3 | Core and attribution runs; focused baseline/sensitivity checks; long-record evaluation | Structured results with failures, provenance, and run-cost records |
    | 4 | Paired analysis; uncertainty; independent-record predictions; precision criterion; figures | Claim ledger and evidence-supported paper outline |
    | 5 | Assistant manuscript preparation; references; compiled PDF; clean reproduction; author review brief | Complete local preprint package if all checkpoints pass |
    | 6 | Server-specific checks; confirmed author facts and license choices; final author approval | Server-ready package and author-controlled public release |

    These milestones are dependency steps rather than calendar weeks. Failed numerical checks require repair; the preprint workflow does not wait for an Acta editorial-policy ruling.

10. **Acta style reference and optional later journal requirements.** The [author instructions](https://acta-acustica.edpsciences.org/author-information/instructions-for-authors) and [data policy](https://acta-acustica.edpsciences.org/author-information/data-policy) were inspected directly on 7 September 2026 while preparing this plan. Use the manuscript, abstract, figure, reference, and reproducibility standards as the preprint target. The journal-specific administrative items in this table are deferred; the chosen preprint server will have its own requirements.

    | Requirement | Plan for this article |
    |---|---|
    | Article type and field | Scientific Article; Audio Signal Processing and Transducers, with computational-acoustics relevance |
    | Files and language | English; LaTeX sources and a checked compiled PDF; use the existing EDP template after confirming current compatibility |
    | Abstract and manuscript | At most 200 abstract words; IMRAD structure; consecutive page numbers and line numbers |
    | Figures | Separate files, vector graphics except photographs, readable in grayscale and at final size; also check the publisher's format/resolution specifications |
    | References | Relevant acoustic literature; numbered by first appearance; all author names; at most 80 references; include .bib and .bbl where used |
    | Declarations | Mandatory conflicts and Data Availability statements; accurate funding and contributions; AI-use disclosure as required |
    | Reviewer suggestions | Three relevant, independent researchers, not all from the same country; verify conflicts before suggesting names |
    | Author details | Accurate affiliation; corresponding-author account and authenticated ORCID workflow; all authors approve submission |
    | Publication charge | Diamond Open Access with no author APC under the current policy |
    | Data and code | Document and cite the exact reusable release; the journal encourages open repositories and permits restricted reviewer access during review, with public availability at acceptance for that route |

    **If a later Acta submission is pursued, resolve policy applicability first.** Section 1.8 currently says authors “may use AI tools only for language improvement” and that AI tools “cannot be used to create or modify images, figures, visual data, or graphical abstracts” in submitted manuscripts. It requires disclosure in both manuscript and cover letter, including tool, version, and role. Existing project records describe substantive AI-assisted analysis and drafting; this research plan is also AI-assisted planning. Adopting Acta's style does not establish eligibility under this policy.

    Maintain an accurate inventory of planning, analytical suggestions, code, text, and plotting assistance, identifying human verification actually completed and any unknown provenance. For a future Acta submission, ask the editorial office how its policy applies to the actual history and workflow. Human verification, rewriting, and preprint publication do not erase the history of assistance.

    Any later inquiry should present that factual inventory; a language-only disclosure would be inaccurate. An Acta ruling is not a prerequisite for the current preprint's code, analysis, drafting, or deterministic figures. Apply the selected server's current policy at the preprint-release stage. No editorial inquiry, manuscript, or data release has been sent or submitted through this planning task.

11. **Reproducibility and integration with the existing workspace.** Every numerical statement should link to a configuration, result file, analysis procedure, and software snapshot. Retain scene ID, source direction, record ID, seed, frame index/time, estimator settings, propagation/startup/reflection condition, estimated angle, signed error, and failure status. Archive selected reference waveforms/responses and sufficient information to regenerate the remainder.

    Use one structured numerical output source for final tables and figures. The existing figure script manually transcribes older tables; those values cannot become the source for the new results. A clean reproduction must regenerate reference checks and representative findings within declared tolerances. Pin a supported environment after checking compatibility; an independent reference should not depend on an unavailable package/runtime combination.

    | Existing material | Role during execution |
    |---|---|
    | [Direct-path diagnostic](/home/ani/Desktop/sound_local/paper/publication_speedrun/research/direct_path_rounding_diagnostic.py) | Starting independent geometric control; extend without importing the estimator under test |
    | [Main estimator code](/home/ani/Desktop/sound_local/validation/doa_benchmark.py) | Reconcile and freeze front-end, sign, bounds, geometry, and interpolation |
    | [Room simulator](/home/ani/Desktop/sound_local/validation/reverb_robustness.py) | Correct and verify propagation, room configuration, response duration, and continuous-source handling |
    | [Averaging and ablations](/home/ani/Desktop/sound_local/validation/ablation.py) | Replace independent-frame assumptions where inappropriate; retain whole-record pairing and separate prediction records |
    | [Previous verification script](/home/ani/Desktop/sound_local/validation/verify_sims.py) | Historical regression context; reproducing old numbers does not verify their physical interpretation |
    | [Existing main draft](/home/ani/Desktop/sound_local/paper/main_paper_draft.md) | Historical source material; the selected title, research question, and verified results require a newly framed manuscript |
    | [Existing figure generator](/home/ani/Desktop/sound_local/paper/figures/generate_paper_figures.py) | Layout reference; final numerical input must come from the new structured outputs |

    Preserve recordings and old results; document exclusions and duplicated files. The main research release should contain the code, configurations, reference cases, per-record/per-frame results, environment, claim ledger, and supplement needed for this article. Include appropriate software/data licenses and third-party notices. The downloaded literature is research material and should not be bundled into the project release by default. Prepare a versioned deposit and persistent identifier at the later release stage.

12. **Decision rules and the first execution milestone.** Direction A remains the selected objective unless evidence justifies narrowing it.

    | Finding at a checkpoint | Decision |
    |---|---|
    | Numerical controls materially change acoustic interpretation, with a repeatable explanation across configurations | Continue A and center the paper on that verified mechanism and consequence |
    | Room bias remains after verification but varies with placement, reflections, and estimator settings | Continue A with conditional findings and the observed interactions |
    | Only the propagation-rounding result is substantial and independently verified | Document the narrower contribution and discuss a focused preprint; a later journal Short Communication remains an option |
    | Corrected results reproduce established behavior without a useful new criterion or explanation | Strengthen the research question or publish a documented software correction; do not call the current work submission-ready |
    | Reference disagreement or inadequate uncertainty could change the conclusion | Repair or expand the relevant check before interpreting the result |
    | Acta's policy cannot accommodate the actual workflow | Retain accurate provenance and treat future Acta eligibility separately; continue the preprint path subject to the selected server's rules |

    **The first execution milestone is a verified direct-path control report.** Its contents are the preserved baseline, one exact estimator specification, independently checked plane/spherical/rounded/fractional comparisons, and a declared numerical tolerance. This is the next unit of research work after the plan, before a large room campaign or manuscript rewrite.

    Preprint readiness requires a defensible novelty comparison and honest framing; passed direct-path and room checks; a useful, bounded contribution; uncertainty and independent-record validation; traceable figures and statements; a reproducible release package; a checked manuscript identifying its preprint status; accurate disclosure; and the chosen server's required files. Author approval is needed for the public release. A calendar date alone does not satisfy these conditions.
