# Acta Acustica draft audit — 9 September 2026

**Verdict: the retained simulation results withstand substantial fresh checks, but this rewritten draft needs major revision before submission.** I found two definite methods-to-code contradictions, an incorrect figure description, incomplete statistical definitions, and claims about practical efficiency that this study does not establish. The most important repairs are to the manuscript. The checks completed here do not indicate a need to discard or repeat the full corrected campaign.

This audit reviews the current [Acta source](/home/ani/Desktop/sound_local/paper/direction_a_preprint/acta_preview/main_acta.tex) and its 11-page PDF, the existing supplement, the retained results, and the relevant simulation, estimator, verification, and analysis code. The manuscript and original results were preserved. The author reports that external researchers have reviewed the work; their comments and the scope of their checks were not available in the material examined here, so this report does not evaluate or contradict an unspecified external-review conclusion.

The reviewed source has SHA-256 `b2cac6cb4120ddc22c560dff3d11f7275d4488847e4e749f3fb5d43b9f40172b`; the PDF has SHA-256 `46268c6c0db75d24f10fcd53b355d6adb6ff519db82423fcaef812825996d895`. Line references below refer to this version. P1 means a major scientific-reporting correction or a submission blocker; P2 means a material clarification or reviewer concern; P3 means an editorial correction. A submission-policy finding is separate from a finding that the numerical science is wrong.

**1. [P1] The averaging method described in Section 3.5 does not produce the reported shorter-duration results.**

[Source line 332](/home/ani/Desktop/sound_local/paper/direction_a_preprint/acta_preview/main_acta.tex:332) says: “the first N consecutive frame estimates from each realization.” The implementation instead partitions each 128-frame test recording into **all non-overlapping N-frame blocks**, through [analysis.py, line 85](/home/ani/Desktop/sound_local/validation/direction_a/analysis.py:85), and uses all those blocks at lines 146 and 154. The [supplement, line 73](/home/ani/Desktop/sound_local/paper/direction_a_preprint/manuscript/supplement.tex:73) correctly describes this.

I independently recomputed both interpretations from the saved per-frame estimates:

| Subset and averaging length | Reported/all-block RMSE | First-N-only RMSE | All-block estimates | First-N-only estimates |
|---|---:|---:|---:|---:|
| Low, N = 1 | 1.5973° | 1.7357° | 23,040 | 180 |
| High, N = 1 | 39.0438° | 35.3389° | 23,040 | 180 |
| High, N = 8 | 18.3801° | 14.1837° | 2,880 | 180 |
| Low, N = 128 | 0.8352° | 0.8352° | 180 | 180 |
| High, N = 128 | 10.1583° | 10.1583° | 180 | 180 |

This is a reproducibility error, not a stylistic preference. It changes the estimand and the number of block estimates. The 128-frame headline endpoints remain correct because both methods use the entire recording at that length. The existing bootstrap appropriately retains all blocks from a selected recording together; 23,040 blocks do not represent 23,040 independent recordings.

**Repair:** retain the verified analysis and replace the sentence with: “For each averaging length N, every held-out 128-frame recording is partitioned into 128/N non-overlapping blocks of N consecutive frames. Each block produces one circular mean. Performance is pooled across blocks and fixed scenes, while uncertainty resamples complete recordings.” State that each low/high subset contributes 180 independent test recordings, yielding 180 × 128/N block estimates. Use “first frame” only in the separate startup trajectory.

**2. [P1] Section 3.1 overstates the scope of independent and permutation verification.**

[Source line 216](/home/ani/Desktop/sound_local/paper/direction_a_preprint/acta_preview/main_acta.tex:216) says: “Both arrival models and all six channel permutations are evaluated within each condition.” This is not what the retained verification does.

The 34,560 rows are the spherical/rounded sweep over 720 angles, three radii, four distances and four sampling rates. In [verify_direct.py, lines 24–46](/home/ani/Desktop/sound_local/validation/direction_a/verify_direct.py:24), the plane-wave recovery sweep runs across 720 angles for each of three radii. The independent scalar spherical solution is checked at six selected angles for each radius/distance combination: 72 such comparisons. The channel-permutation test in [test_direct.py, line 25](/home/ani/Desktop/sound_local/validation/direction_a/test_direct.py:25) exercises all six permutations for one specified geometry and source direction, for both the analytical solve and a waveform estimate. Separate tests include cardinal directions. These are useful checks, but they are not the claimed Cartesian product of every test.

**Repair:** describe these checks as distinct suites and give their actual counts. Suitable wording: “The analytical rounding sweep contains 34,560 angle/radius/distance/sampling-rate conditions. Separate tests check plane-wave recovery, cardinal directions, selected independent scalar spherical solutions, and invariance under all six channel permutations.” Do not imply that the 34,560-row file provides exhaustive permutation or independent-reference coverage. The extra random perturbation checks for the timing bound are another distinct suite.

**3. [P1] The abstract presents an efficiency/device contribution that the experiments do not demonstrate.**

[Source line 30](/home/ani/Desktop/sound_local/paper/direction_a_preprint/acta_preview/main_acta.tex:30) introduces battery-powered edge devices, computational/memory/energy limitations of beamforming, and a “computationally minimal DoA system.” [Line 547](/home/ani/Desktop/sound_local/paper/direction_a_preprint/acta_preview/main_acta.tex:547) says averaging reduces error “without increasing the processing applied to each frame.” The actual evidence concerns an ideal simulation and fixed algorithms. There are no device runtime, energy, memory, cost or comparative complexity measurements. Three microphones provide a minimal non-collinear planar geometry for this approach; that does not establish computational minimality.

The per-frame GCC estimator is unchanged, but temporal accumulation is additional processing, and obtaining a 128-frame block requires 5.461 seconds of observations. A stationary-source result at that duration does not demonstrate moving-source tracking or responsiveness for hearing devices. Low/high subsets also differ in placement as well as absorption, so their abstract labels should retain that distinction. The body handles these limitations more carefully than the abstract.

**Repair:** make the contribution the verified, controlled attribution study and the measured error-versus-observation-duration tradeoff. Say “with the same per-frame localization estimator” instead of implying zero added processing. Remove or support the claims about computational/memory/energy advantages. Report practical applications as motivation, not as an evaluated outcome. No hardware experiment is required to make a defensible simulation paper if those claims are narrowed.

**4. [P2] Figure 2(a)'s caption describes the wrong error reference.**

[Source line 412](/home/ani/Desktop/sound_local/paper/direction_a_preprint/acta_preview/main_acta.tex:412) calls this panel “Angular change caused by rounding analytical arrivals.” The plot actually shows **signed error relative to the true source azimuth**, including the exact-spherical curve. [figures.py, lines 59–63](/home/ani/Desktop/sound_local/validation/direction_a/figures.py:59) plots `rounded_signed_error_deg` and `exact_signed_error_deg`. It does not subtract the exact-spherical estimate. Figure 6(a) does use that subtraction.

For R = 0.05 m and distance 1.5 m, the exact-spherical/plane-wave-solver curvature RMSE is 0.337457°. At 48 kHz, rounded-arrival RMSE relative to truth is 2.143073°, whereas the rounded-minus-exact-spherical change has RMSE 2.113533°. Confusing these quantities undermines the paper's central separation of error sources.

**Repair:** use “Signed angular error relative to the true source azimuth for exact spherical arrivals and sample-rounded arrivals.” Explain that the exact-spherical curve retains finite-distance curvature and that Figure 6 isolates the additional rounding shift. Keep the verified plot.

**5. [P2] The interaction equations and Table 3 omit necessary conditioning.**

[Source lines 310–324](/home/ani/Desktop/sound_local/paper/direction_a_preprint/acta_preview/main_acta.tex:310) define a rounding-by-reflection difference of differences without specifying how source history is handled. The reported 30.762 deg² is averaged equally over steady and onset histories. It is not the difference of the two steady-state rounding contrasts quoted immediately before it:

| Rounding-by-reflection contrast | MSE change |
|---|---:|
| Steady only | 37.010645 deg² |
| Onset only | 24.514217 deg² |
| Equal average of both histories, as reported | 30.762431 deg² |

The sentence saying “complete factorial dataset” points in the right direction, but the equation should define the estimand explicitly. Similarly, the onset-by-reflection interaction is averaged over fractional and rounded arrivals. The [existing supplement, line 64](/home/ani/Desktop/sound_local/paper/direction_a_preprint/manuscript/supplement.tex:64) gives the correct convention. Table 3's first, second and fourth rows are steady-state contrasts; its onset row is fractional-arrival onset minus steady. Its short labels do not disclose these settings. The equations also use R for rounded arrivals while the figures use Q for rounding and R for reflected propagation.

**Repair:** use Q/F consistently for arrival construction and specify that each two-factor interaction is averaged over the remaining factor. Add the fixed conditions to Table 3's caption or row labels. Preserve the numerical values, which reproduce correctly.

**6. [P2] Report the averaging model's shorter-duration discrepancies, and state its assumptions.**

[Source line 477](/home/ani/Desktop/sound_local/paper/direction_a_preprint/acta_preview/main_acta.tex:477) emphasizes the agreement at N = 128: measured 2.013°, covariance prediction 2.075°, independent-frame prediction 2.106°. The complete eligible-set curve contains appreciably worse agreement at shorter lengths:

| N | Held-out RMSE | Covariance-model prediction | Relative overprediction |
|---|---:|---:|---:|
| 4 | 3.647° | 4.541° | 24.5% |
| 8 | 2.844° | 3.434° | 20.7% |
| 16 | 2.408° | 2.749° | 14.2% |
| 128 | 2.013° | 2.075° | 3.1% |

The figure shows these discrepancies, but the rewritten prose no longer discusses them as directly as the underlying preprint. These percentages are descriptive discrepancies, not formal rejection tests: uncertainty in the model predictions was not propagated. The 0.031° difference between the two 128-frame predictions does not establish a practically useful superiority of covariance correction.

The covariance identity also requires an approximately stationary scalar-error process, with covariance depending on lag. A spatially stationary source alone does not prove that statistical assumption. The fitted bias is circular whereas the covariance calculation is based on wrapped scalar errors; equivalence is an approximation. The training eligibility rule is explicitly acknowledged as allowing rare large errors, and the data confirm that: the 49 eligible scenes contain 78 training-frame errors above 90° among 31,360 training frames. Thus the rule is not a guarantee that squared-error behavior is well represented by a small-angle approximation.

Finally, [analysis.py, lines 138–145](/home/ani/Desktop/sound_local/validation/direction_a/analysis.py:138) centers each 128-frame record separately. This removes variation among record means and can bias low-frequency covariance estimation. In the eligible scenes, the mean variance of the five record means is 0.328 deg²; this is a diagnostic of removed variation, not an automatically valid extra asymptotic variance term. The current method can be retained as a finite-record heuristic, but its centering should not be presented as establishing an unbiased estimate of the unconditional stationary covariance. A clipped negative variance estimate is not necessarily mere floating-point “numerical error”; covariance estimation/truncation can also cause it.

**Repair:** explicitly state approximate stationarity, finite-record centering/taper bias, and the prediction's descriptive status. Restore a sentence reporting the larger discrepancies at short durations and the lack of established benefit from covariance correction. If a stronger predictive-model contribution is desired, assess prediction uncertainty and robustness to record centering and lag cutoff in a separately labeled analysis. Those additions are optional if the claim remains modest.

**7. [P2] Specify the numerical reference's scope and the processing used for decay measurements.**

[Source line 384](/home/ani/Desktop/sound_local/paper/direction_a_preprint/acta_preview/main_acta.tex:384) reports 5.22 million paths per microphone, relative spectral error 1.13 × 10⁻⁵, and angular discrepancy 0.000807°. These values reproduce. However, “full room reference” means all retained paths for one selected final scene, evaluated at 12 probe frequencies; it does not mean an independent reference at every frequency for all 216 scenes. See [verify_revision.py, lines 32–37](/home/ani/Desktop/sound_local/validation/direction_a/verify_revision.py:32). The joint duration/extent check covers six high-setting scene/direction cases and 960 matched frames. The propagation/GCC/SRP refinement checks cover 24 scenes and 3,840 frames per refinement. These different scopes should be visible in Table 2 or its caption.

Section 2.5 describes reverse integration but does not explicitly say that the impulse responses are first passed through the same 300–3400 Hz acquisition filter. They are: [room.py, line 122](/home/ani/Desktop/sound_local/validation/direction_a/room.py:122). A reader applying the stated calculation directly to the unfiltered response would measure a different decay. The reported T20 is a pooled, band-limited simulated-response descriptor, not a measured broadband or octave-band room certification.

**Repair:** state the probe-frequency/scene/frame counts and say “band-limited impulse response after the acquisition filter” in the decay method. Preserve the existing acknowledgment that convergence checks are not universal bounds or physical validation. No new worst-case claim is supported by the reruns.

**8. [P1 for submission; P2 for scientific accessibility] The rewrite dropped declarations and access to the supporting work.**

The paper goes directly from its conclusion to the bibliography at [source line 562](/home/ani/Desktop/sound_local/paper/direction_a_preprint/acta_preview/main_acta.tex:562). It contains no Data Availability Statement, conflict declaration, funding/contribution information, assistance disclosure or announcement of supplementary material. The [underlying preprint, line 244](/home/ani/Desktop/sound_local/paper/direction_a_preprint/manuscript/main.tex:244) includes these items. Their omission also makes assertions such as “documented in the verification record” difficult for a reader to follow.

This matters scientifically because the current main text relies on exact protocol/configuration details absent from its description, including the unequal triangle construction, unequal wall multipliers, nuisance-factor averaging conventions, and exact precision-box bound shown in Figure 6. Those details are retained in the supplement and/or code/configuration files but are no longer signposted. The current preview README claims the existing supplement supplies extended details, yet the actual paper never announces it.

The journal's author instructions require a Conflict of Interest statement and a section titled **Data Availability Statement**, and specify announcement of Supplementary Material. The separate data policy allows several availability routes, including reviewer-restricted repository access during review and data available on request; absence of a public DOI alone is not a blanket submission prohibition.

**Repair:** restore accurate declarations and a visible supplementary-material section; identify how reviewers and readers can obtain the source, results and configuration. Update the provenance text to reflect the author's reported external research review, recording its actual scope. A colleague's review of reasoning/code and a physical measured-room validation are different activities. Do not invent a no-conflict declaration, public DOI, license, named reviewer endorsement or completed physical validation.

**9. [P2] Journal formatting compliance and the saved QA status are stale.**

The abstract is approximately 252–254 words, depending on whether it is counted from the source or extracted PDF. It is clearly over the **200-word** limit for a Scientific Article. It also lacks explicit IMRAD structure. The 11-page PDF has consecutive page numbers but no line numbers. Current Acta instructions require numbered lines on each page. Eleven pages is within the journal's typical up-to-12-page Scientific Article length, so page count itself is not a finding.

[PREVIEW_QA.json](/home/ani/Desktop/sound_local/paper/direction_a_preprint/acta_preview/PREVIEW_QA.json) describes a different, 10-page PDF with a 183-word abstract and another SHA-256 hash. It cannot certify this revised draft. The README also describes a previously checked editorial preview, so its completed-review language should not be assumed to cover the rewrite.

**Repair:** shorten and structure the abstract, enable line numbering for the submission version, and regenerate document checks against the actual final PDF. All six current scientific figures are byte-identical to their verified originals. Visual inspection of all 11 current pages found no clipping, overlapping equations/tables, missing glyphs or unreadable figures. The small final-page vertical-box warning has no observed visible collision. Formatting compliance and mathematical content are separate from that visual pass.

**10. [P2] The literature supports the methods, but the contribution needs a sharper comparison with prior work.**

The introduction's [“has received less attention” claim, line 39](/home/ani/Desktop/sound_local/paper/direction_a_preprint/acta_preview/main_acta.tex:39) is unsupported by a specific comparison. The nine references appropriately establish GCC, equilateral arrays, fractional delays, image sources, numerical verification, decay measurement, SRP and bootstrap. They do not, by themselves, establish that simulation startup effects or temporal averaging in compact arrays are underexplored. The new abstract compounds this by foregrounding ordinary temporal averaging as the main innovation.

The strongest defensible contribution is the combination of independent numerical checks, paired factorial controls, realized acoustic descriptors, retained difficult cases, and averaging evaluated on separate recordings for one precisely specified estimator. Say what this controlled comparison reveals beyond the nearest work, rather than implying that the layout, GCC-PHAT, the image method, the covariance identity or averaging is new. More references are useful only when they establish that distinction.

I checked all nine bibliography entries against the stored primary-source metadata/reading notes and found no fabricated reference. Their DOI, title, author and publication information are consistent with those records, subject to the recorded reading-level limits. This audit is not a fresh exhaustive international novelty search or a new full-text review of every citation. A positive statement that “nothing like this has been published” would require more evidence.

**11. [P1 for Acta eligibility] The journal's current AI policy still needs an editorial determination for the documented workflow.**

I inspected the live official [author instructions](https://acta-acustica.edpsciences.org/author-information/instructions-for-authors) on 9 September 2026. Section 1.8 says authors “may use AI tools only for language improvement,” that AI tools “cannot be used to create or modify images, figures, visual data, or graphical abstracts” in submitted manuscripts, and that use must be disclosed in the cover letter and manuscript, with tool/version/role. The retained project provenance records substantive assistance with planning, derivations, implementation, numerical reference checks, analysis and deterministic plotting as well as drafting.

That documented scope extends beyond language improvement. The exact treatment of deterministic plots made by assisted code should be determined by the journal, rather than assumed from the wording. Human rewriting or external technical review can improve and validate the work; they do not change its assistance history. This is an Acta submission-eligibility issue and does not establish a numerical flaw. No editorial inquiry or external message was sent during this audit.

**Repair:** keep an accurate workflow disclosure and obtain an explicit editorial interpretation before treating the manuscript as eligible for Acta submission. This does not require stopping local revision or the scientific audit, and it should not be “fixed” by deleting provenance. This recommendation comes from the journal's current instructions, not an invented approval rule.

**Small corrections worth making in the same pass [P3].**

- [Introduction line 37](/home/ani/Desktop/sound_local/paper/direction_a_preprint/acta_preview/main_acta.tex:37) prints `20.83,\mu s` with an actual comma. Use a thin space and a correctly typeset microsecond unit. “At this instance the microphone spacing is…” should read “For the present 86.6 mm microphone spacing…”.
- The introduction's separate source lines have no blank lines, so they render as one dense paragraph. Separate the geometry/sampling argument, startup problem, prior work and contribution into actual paragraphs.
- Define GCC-PHAT in full at its first occurrence. Use “azimuth” where the result is specifically horizontal, and reserve broader direction-of-arrival language for the motivation.
- The energy cross-term equation should either show the sum over microphone index as well as time or define the impulse-response products as channel inner products, consistent with the pooled-energy implementation.
- The SRP refinement maximum is 0.0023103038°: Table 2's 0.002310 is consistent with six decimal places; the prose's 0.002311 is not conventional nearest rounding. The reflected-rounding MSE interval's lower endpoint is 11.9734995, which rounds to 11.973 at three decimals, rather than the printed 11.974. Neither discrepancy changes an inference.
- Section 5's “five independent short recordings” should distinguish the short-record experiments from the five independent long test recordings used for averaging.
- Figure 6 includes an “Exact box bound” as well as the disk bound. The main text derives only the disk bound. Add a short explanation or a direct supplement reference for the exact vertex-angle calculation.
- Define symbols before or adjacent to the first equation using them. The circular-average definition and wrapped-error definition are each repeated; consolidate them to recover space for the missing result interpretation.
- Keep the template-preview/preprint designation for this local draft. The supplied class and its layout are not scientific deficiencies. Submission metadata can be adjusted when preparing an actual submission.

**What the fresh checks establish.**

| Check performed in this audit | Result |
|---|---|
| All primary frame files, hashes, settings, frame indices, pair identities and error/exceedance consistency | 276,480 estimates across 216 scenes pass |
| Saved analysis rerun into a separate directory | All 14 original analysis outputs match exactly (CSV bytes or JSON content) |
| Separate raw-frame calculation of core RMSE, direct/reflected rounding, startup and both averaging interpretations | Confirms reported values under the implemented definitions; exposes Finding 1 |
| Training/test input separation | No source or noise hash overlap between training and held-out sets |
| Existing direct-path, room and SRP tests | 9 passed |
| Fresh simulation of three complete scenes | 8,640 estimates, all saved fields exactly reproduced |
| Fresh final independent room reference, including six pruning regressions | Passed; spectral discrepancy 1.129807 × 10⁻⁵ and angular discrepancy 0.000807354° |
| Fresh joint duration/extent refinement, six high-setting cases | 960 matched frames pass; maximum angular change 0.012726248° |
| Fresh geometry precision sweep | 34,560 rounded-arrival cases and 12,000 independent perturbations pass |
| All main PDF pages | 11 pages visually inspected; six original scientific figures retained |

The independently checked headline values include direct-path RMSE 0.923° versus 2.300°, high-subset first-frame RMSE 4.157° versus 42.508°, final high-subset startup/steady RMSE 41.526° in both conditions, 128-frame low/high RMSE 0.835°/10.158°, 49 eligible scenes, and the stated GCC/SRP comparison. The main T20 ranges, scene-level ranges, direct-to-reverberant range and paired contrasts also agree with the retained outputs. There is no evidence here of a sign-convention failure, accidental training/test overlap, incorrect pooled-RMSE calculation, or pooling of the superseded campaign into the reported results.

The underlying mathematics also survives inspection within its stated domain: the lag sign and least-squares direction relation are consistent; image coordinates, wall counts and pressure gains are consistent with the independent enumeration; circular averaging is implemented as stated apart from block selection; and the geometry-only timing bound correctly retains shared-microphone dependence. The 0.954 microsecond sufficient bound is correctly scoped to ideal arrivals. None of these checks establishes real-room accuracy or a universal acoustic error floor.

The fresh-scene rerun covers three selected scenes, not another full 276,480-estimate campaign. The existing direct waveform sweep and sensitivity outcomes were inspected/recomputed from retained results; the nine tests, final independent room reference, joint duration/extent refinement and full precision checks described above were actually rerun. No new hardware data were obtained. Bibliographic metadata checks are not equivalent to reading every full paper. These distinctions are part of the audit result.

**A concrete revision order.**

First fix the two methods contradictions and Figure 2's reference quantity. Then make the interaction conditioning explicit and report the covariance model's shorter-duration discrepancies. Rewrite the abstract around the supported simulation contribution and restore declarations, data access and the supplement. Update the closest-prior-work comparison, apply the small copy corrections, and rerun document QA against the resulting PDF. Resolve the journal-specific policy question before an Acta submission. These are targeted repairs; the matched-control design, retained results and conservative limitations deserve to be preserved.

**Suggested replacement abstract, for author revision rather than automatically applied text.**

**Introduction:** Small microphone arrays are sensitive to acoustic conditions and numerical choices in simulation. We quantify arrival-time rounding, source startup and reflected propagation for three-microphone azimuth estimation. **Methods:** Matched simulations used an equilateral array of 5 cm radius, a stationary synthetic source and three rectangular rooms. The estimator combined generalized cross-correlation with phase transform (GCC-PHAT) and a planar least-squares direction fit. Analytical references and independent room calculations verified numerical implementation. Eight paired conditions separated arrival construction, source history and reflections. Temporal averaging was evaluated on independent recordings using non-overlapping blocks. **Results:** At a direct-sound-referenced SNR of 10 dB, rounding increased steady direct-path root-mean-square error (RMSE) from 0.923° to 2.300°. In the high-reverberation, offset-array subset, first-frame RMSE was 4.157° at onset versus 42.508° in steady operation. Averaging 128 frames (5.46 s) gave 0.835° and 10.158° RMSE in the low-reverberation/centred and high-reverberation/offset subsets. **Discussion:** Arrival discretization and source history materially change reported localization performance. Averaging reduces error for stationary simulated scenes but leaves condition-dependent residuals. These results concern the specified numerical model and estimator; hardware efficiency and measured-room accuracy remain untested.

Supporting audit outputs are retained in the [evidence directory](/home/ani/Desktop/sound_local/paper/direction_a_preprint/acta_preview/audit_2026-09-09/evidence/independent_audit.json), including the [first-N/all-block comparison](/home/ani/Desktop/sound_local/paper/direction_a_preprint/acta_preview/audit_2026-09-09/evidence/recomputed/first_N_versus_all_blocks.csv), [fresh scene reproduction](/home/ani/Desktop/sound_local/paper/direction_a_preprint/acta_preview/audit_2026-09-09/evidence/fresh_reproduction.json), and [document checks](/home/ani/Desktop/sound_local/paper/direction_a_preprint/acta_preview/audit_2026-09-09/evidence/document_checks.json). The current official requirements were read directly at the [author-instructions page](https://acta-acustica.edpsciences.org/author-information/instructions-for-authors) and [data-policy page](https://acta-acustica.edpsciences.org/author-information/data-policy).
