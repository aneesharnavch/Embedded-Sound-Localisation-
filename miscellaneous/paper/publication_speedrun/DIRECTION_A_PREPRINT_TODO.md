# Direction A preprint: execution checklist

**Updated 8 September 2026.** Current target: an openly shareable **preprint**, using Acta Acustica's scientific rigor, structure, references, and presentation as the standard. Later submission to Acta is optional and its eligibility remains a separate question.

**Final title:** *Separating arrival rounding, source startup, and reverberation in three-microphone azimuth estimation*.

**Owner:** the assistant carries out the implementation, numerical verification, experiments, analysis, figures, manuscript drafting, and packaging below. The author supplies identity/declaration facts, reviews the scientific claims, and decides the public release. The local author-review package is complete (A01–A35). Completion evidence is recorded in the [execution log](/home/ani/Desktop/sound_local/paper/direction_a_preprint/EXECUTION_LOG.md).

**Research design:** use the [Direction A plan](/home/ani/Desktop/sound_local/paper/publication_speedrun/ACTA_ACUSTICA_ROUTE_A_PLAN.md) for the detailed model, initial parameter matrix, and controls, and the [scientific audit](/home/ani/Desktop/sound_local/paper/publication_speedrun/SCIENTIFIC_AUDIT.md) for known defects. This checklist governs execution order and ownership. It supersedes the earlier journal-first schedule and editorial-policy prerequisites.

**Scope:** one stationary broadband synthetic source, three ideal microphones, horizontal direction estimation, and verified three-dimensional shoebox-room simulations. Use existing project material plus new computation. The main study requires no new hardware recordings. The result must explain numerical and acoustic effects with evidence; a universal reverberation floor is not an assumed conclusion.

**Execution rules.** Resume from the first ready unchecked task. Continue routine reversible workspace work through each stage when its scientific checks pass; record failures, repair them, and rerun affected checks before advancing. Mark a task complete only after its output exists and its stated checks pass. Keep task ID, output paths, software/configuration identifiers, checks, and limitations in an execution log. A later code or model change must invalidate affected downstream outputs. Independent reference implementations are numerical checks; they are not external peer review.

**Output locations:** implementation and numerical checks under `/home/ani/Desktop/sound_local/validation/direction_a/`; records, reports, manuscript, and final package under `/home/ani/Desktop/sound_local/paper/direction_a_preprint/`. The completed package and supporting evidence are in these locations. The original source material is preserved in the baseline archive.

**Timing:** measure pilot throughput, memory, storage, and verification workload before forecasting elapsed execution time. The previous 80–120 author-hour estimate described a human-led workflow; it is not an estimate of automated runtime.

1. **Preserve the baseline and establish a traceable workflow.** Owner: assistant. Start here.

    - [x] **A01 — Preserve the evidence.** Save a dated snapshot and hash manifest of the relevant code, drafts, logs, configurations, and diagnostic outputs. Keep original recordings intact. Verify that the snapshot can recover the pre-change research state; this workspace currently has no Git history.
    - [x] **A02 — Establish a working environment.** Inspect the available numerical and LaTeX tools, choose compatible versions, and record dependencies. Verify that a small numerical example runs and that the manuscript toolchain can compile a minimal document. Resolve an unavailable dependency using a documented alternative.
    - [x] **A03 — Set up result and provenance records.** Create the output directories, execution log, explicit scene/record seeds, configuration hashes, per-frame result schema, and assistance/provenance register. Record the roles of AI assistance and human checks accurately, including unknown historical details. Ensure separate experiments do not depend on the order of random-number calls.
    - [x] **A04 — Audit claims and establish the literature gap.** Review the nearest work on image-source interpolation, delay-estimation bias, finite-distance curvature, small-array geometry, and averaging. Create a claim/source table distinguishing established techniques, historical findings, and hypotheses to test. Log exclusions, including the forced 77% illustration and unsupported hardware claims. Verify citations used in the new paper against original sources.

    **Output:** recoverable baseline, environment record, execution log, provenance register, and novelty/claim table. Existing diagnostic numbers may motivate the study but cannot be relabeled as verified end-to-end performance.

2. **Verify the direct-path problem before interpreting room errors.** Owner: assistant. Depends on A01–A03; the literature work may progress alongside these checks.

    - [x] **A05 — Freeze the exact estimator specification.** Reconcile microphone coordinates, channel order, delay sign, sound speed, preprocessing, analysis band, PHAT regularization, physical lag bounds, interpolation, and the direction solve. State 5 cm circumradius and 8.66 cm pair spacing as simulation dimensions. Match the equations to the implemented method.
    - [x] **A06 — Implement independent analytical controls.** Check exact plane-wave delays and direction recovery, then exact spherical delays interpreted by the same far-field estimator. Include cardinal directions, channel permutations, and near/far distances. The reference calculation must not import the solve being tested.
    - [x] **A07 — Quantify arrival-rounding effects.** Reproduce the existing diagnostic, then expand to the 720-angle grid and the planned sampling-rate, radius, and distance values. Keep physical bandwidth and observation duration controlled. Save signed errors and geometry metadata, not only pooled RMSE.
    - [x] **A08 — Verify fractional propagation and estimator resolution separately.** Generate independently constructed fractional-delay waveforms, compare them through the same estimator, and refine propagation and correlation interpolation separately. Distinguish propagation discrepancy from finite-window, curvature, and estimator errors. Add meaningful numerical tests for these properties.
    - [x] **A09 — Produce the direct-path verification report.** Record reference agreement and convergence. Use 0.05° as the initial numerical-discrepancy target for an interpreted effect of about 0.5° or larger; tighten it before the main run if smaller effects matter. Document the reason for the final tolerance.

    **Checkpoint G1:** the exact solve, fractional propagation, geometry/sign checks, and declared numerical tolerance pass. The report clearly separates numerical discrepancy from physical-model mismatch. If they fail, repair the relevant implementation before interpreting room results.

3. **Verify the room model and continuous recording protocol.** Owner: assistant. Depends on G1.

    - [x] **A10 — Make the room model explicit.** Parameterize microphone/source coordinates, room dimensions, wall properties, reflection inclusion, response length, and image coverage. Validate all coordinates and direct-path amplitudes/times. Give reflections an explicit on/off switch and retain fractional arrival times.
    - [x] **A11 — Correct source-history handling.** Generate continuous records with adequate prehistory. Compare identical analysis-interval source samples with zero versus populated prehistory. Reproduce the legacy procedure that restarts the source every short frame as a separately labeled diagnostic.
    - [x] **A12 — Cross-check an independent room reference.** Use an analytical frequency-domain image sum or a separately implemented reference for selected scenes. Verify reflection enumeration as well as delay interpolation; agreement between implementations that share the same mistaken path list is insufficient.
    - [x] **A13 — Measure the realized room behavior.** Check response-length, image-coverage, and interpolation convergence. Estimate supported decay metrics and record direct-to-reverberant energy plus important early reflections. Distinguish requested decay settings from decay computed from the simulated response.
    - [x] **A14 — Produce the room-verification report.** Show reference comparisons, supported decay fits, convergence, and onset/steady-state differences. Record model assumptions and meaningful numerical tests.

    **Checkpoint G2:** direct-path and room references agree within declared tolerances, relevant room metrics stabilize, and the recording protocol represents the stated experiment. These checks verify the computational model; they do not certify a real device or all real rooms.

4. **Pilot the study and freeze the confirmatory protocol.** Owner: assistant. Depends on G2 and A04.

    - [x] **A15 — Run and profile a small pilot.** Exercise matched rounded/fractional arrivals, onset/steady-state windows, and reflections off/on, including noiseless cases. Measure runtime, peak memory, storage, numerical discrepancies, effect sizes, and uncertainty. Identify whether the central question yields a useful finding beyond fixing a private script.
    - [x] **A16 — Freeze the main protocol.** Finalize the scene matrix, source/noise definition, common inputs, tolerances, failure threshold, seed allocation, separate pilot/analysis/validation records, and secondary-method subset. Use direct-path band power to set noise consistently across matched reflection conditions. Validate source-to-wall clearance. Record any reduction of redundant work and its reason before examining confirmatory results.

    **Checkpoint G3:** the study has a precise question, adequate numerical resolution, a feasible measured workload, and an uncertainty strategy. The initial workload is 276,480 primary-estimator frame evaluations plus verification/sensitivity work; the pilot determines the final allocation. Large frame counts do not replace variation across acoustic scenes.

5. **Run the frozen Direction A experiments.** Owner: assistant. Depends on G3. Save intermediate results so runs can resume without losing completed work.

    - [x] **A17 — Run the core corrected-room study.** Start from the planned three rooms, two array placements, three decay settings, 12 directions, three SNRs, five records, and 32 continuous frames per record. Record any pilot-approved change. The initial core count is 103,680 primary-estimator evaluations.
    - [x] **A18 — Run the paired attribution study.** On the six predeclared states, evaluate the eight arrival/startup/reflection combinations at 10 dB with identical underlying random realizations. Reuse the corresponding corrected core cell only when its configuration and inputs match exactly. The initial additional count is 80,640 evaluations.
    - [x] **A19 — Run the independent long-record study.** Use new 128-frame records on the six-state subset. Separate the five records used to estimate bias/correlation from the five used to test predictions within each scene. The initial count is 92,160 additional evaluations.
    - [x] **A20 — Run focused generalization and baseline checks.** Evaluate the predeclared orientation, non-equilateral geometry, wall-distribution, and source-spectrum variations. Compare with refined SRP-PHAT on a fixed subset with matched inputs and adequate angular resolution. Include other estimators only when they answer a remaining research question.
    - [x] **A21 — Audit run completeness and provenance.** Verify expected scene/record coverage, true/estimated angles, code/configuration hashes, pairing, disjoint validation seeds, and explicit failures. Re-run incomplete or invalid cells while retaining the original failure log.

    **Checkpoint G4:** the frozen matrix is accounted for and every retained result has known inputs and provenance. Difficult scenes and failed estimates remain visible.

6. **Establish what the experiments actually support.** Owner: assistant. Depends on G4.

    - [x] **A22 — Compute errors and appropriate uncertainty.** Report signed wrapped error, RMSE, median absolute error, 90th percentile, failures, and per-scene bias. Resample whole records while preserving pairing. Show variation across the chosen rooms separately from uncertainty within a scene; three room geometries do not support universal population claims.
    - [x] **A23 — Quantify effects and their interactions.** Compare matched propagation, startup, and reflection conditions. Use signed-error and squared-error differences with uncertainty. Do not subtract RMSE values or force correlated components into an additive error budget.
    - [x] **A24 — Test averaging on independent records.** Plot errors against actual observation duration. Compare the held-out behavior with predictions that account for temporal correlation where needed. Use empirical distributions when the small-error bias/variance approximation is inappropriate.
    - [x] **A25 — Derive and test a useful precision criterion.** Relate arrival-time precision to array geometry, direction, and angular error. Account for shared-microphone dependence in pair-delay errors. Verify any approximation against independent cases; label its domain and any failure cases. Retain it only if the evidence supports it.
    - [x] **A26 — Finalize the scientific claim ledger.** Map each intended conclusion to its results, uncertainty, configuration, and limitations. Resolve competing numerical/physical explanations. If novelty or generality is weaker than hoped, state the narrower finding honestly and revise the paper around it.

    **Checkpoint G5:** the central claims are traceable, supported by verified computations, and appropriately bounded. No universal RT60 law, guaranteed estimator superiority, or hardware performance is inferred from unsupported evidence.

7. **Write and render the preprint in Acta's style.** Owner: assistant. Depends on G5 for final results; a neutral manuscript skeleton can be prepared earlier.

    - [x] **A27 — Generate the figures and tables from verified outputs.** Build the geometry/verification diagram, direct-path and convergence plots, paired room-effect plots, held-out averaging plots, and precision-criterion plot if justified. Include configuration, verification, and principal-effect tables. Use deterministic scientific plotting, explicit uncertainty, readable units/captions, vector originals, and grayscale-safe distinctions. Record the actual assistance used.
    - [x] **A28 — Draft the complete manuscript.** Write the introduction, exact physical/estimator model, verification protocol, evaluation methods, results, discussion, and conclusion. Target approximately 8–10 typeset pages while preserving essential evidence. Explain why the finding matters to acoustics and identify established prior methods accurately.
    - [x] **A29 — Finalize the title, abstract, and references.** Write a structured abstract of at most 200 words with verified numerical findings. Use numbered citations in order of appearance, complete author lists, verified bibliographic details, and consistent symbols. Remove obsolete numbers and unsupported novelty language.
    - [x] **A30 — Add truthful preprint metadata and declarations.** Clearly identify the document as a preprint that has not been peer reviewed. Draft Data Availability, contributions, funding/conflict fields, and an accurate assistance statement. Keep missing author facts explicitly pending. Do not label substantive assistance as language editing alone or invent an archive DOI.
    - [x] **A31 — Compile and inspect the complete PDF.** Use neutral preprint formatting compatible with Acta's structure, readable two-column presentation where suitable, and page/line numbers. The existing EDP template may be reused if it can be adapted without implying journal publication. Inspect every page, equation, caption, reference, and figure at final size; repair overflow, broken links, unreadable labels, and misleading journal metadata.

    **Checkpoint G6:** the PDF and source agree with the verified results, are readable, and accurately describe publication status and provenance. Acta-inspired style does not imply Acta acceptance or compliance with every journal policy.

8. **Make the research reproducible and ready for author review.** Owner: assistant. Depends on G5–G6.

    - [x] **A32 — Prepare the supplement and research release.** Include extended derivations, room/reference checks, complete scene summaries, protocol files, per-record/per-frame outputs, environment instructions, and software/data notices. Include an acquisition appendix only if it contributes to the paper. Package relevant material with appropriate license choices pending owner approval; preserve third-party licenses.
    - [x] **A33 — Reproduce the package in a clean environment.** Regenerate the numerical reference checks and representative main results/figures from the packaged files. Check that the full-run instructions and archived-output paths are complete. Record exactly what was rerun, the versions used, and numerical tolerances; do not describe a representative rerun as a second full campaign.
    - [x] **A34 — Perform a critical review and repair findings.** Challenge the strongest scientific claim, independence of references, numerical tolerances, paired comparisons, uncertainty, source naming, figure provenance, and literature gap. Check equation/code/result consistency. Fix material issues and re-run affected checks. Describe this as an internal review, not independent peer review.
    - [x] **A35 — Deliver the author-review package.** Provide the PDF, LaTeX/bibliography, figures, supplement, reproducibility bundle, verification summary, and a short explanation of what was learned and what remains uncertain. List only the author facts, release decisions, and unresolved scientific issues requiring attention.

    **Checkpoint G7:** a complete local preprint package exists, with passed scientific and document checks, an honest reproduction record, and a concise author-review brief.

9. **Prepare the chosen server's submission package.** Technical preparation remains assistant-owned. The server is not selected yet; its choice does not prevent the research and draft from proceeding.

    - [ ] **A36 — Verify the chosen server's current requirements.** After the author chooses a destination, inspect its scope, source-file requirements, metadata, AI/disclosure policy, license options, and any account/endorsement requirements. If a requirement affects the paper or eligibility, resolve it using the complete package and accurate provenance.
    - [ ] **A37 — Produce the final upload bundle and metadata.** Adapt the checked files to that server, verify the final PDF again if formatting changes, and prepare the title, abstract, subjects/keywords, author details, version/date, assistance disclosure, and links to actual release locations. Keep publication/upload as the final author-controlled step.

    **Author decisions, collected when needed:**

    - [ ] **U01 — Confirm author facts and review.** Name (Aneesh Arnav Chikkala), sole authorship, no affiliation and self-funding are recorded. Conflicts and final scientific review remain pending; the completed author-review brief identifies these fields.
    - [ ] **U02 — Choose the destination and licenses.** Select the preprint server and approve the licenses/public contents after reviewing the applicable options. The assistant researches and prepares the choices.
    - [ ] **U03 — Approve the finished release.** Review the final claims and files, then publish the package or explicitly authorize its upload. Any required account or endorsement action stays with the author.

    **Current completion target:** A01–A35 produce the verified local, server-neutral author-review package. A36–A37 are deferred until a destination is selected, per the author’s instruction. U01–U03 cover remaining declarations, licensing, review and public release. Preparing the package and publishing it are separate statuses.

**What changes from the journal-first plan.** Acta's editorial clarification, reviewer suggestions, cover letter, and journal submission administration are deferred unless a later Acta submission is chosen. Its current language-only AI policy is not a prerequisite for producing this preprint. Preserve accurate assistance records and follow the chosen server's rules; producing a preprint does not erase prior assistance or establish future Acta eligibility. Scientific verification, uncertainty, citation accuracy, and reproducibility remain essential.

**Current execution:** A01–A35 are complete. The final nine-page preprint, five-page supplement, source/data archive and [author-review brief](/home/ani/Desktop/sound_local/paper/direction_a_preprint/AUTHOR_REVIEW.md) are ready locally. All 276,480 revised primary estimates were audited; a clean environment reproduced 8,640 representative estimates exactly and all six main figures byte for byte. The original failed joint-refinement run is preserved and superseded. A36–A37 are deferred because the author requested a server-neutral package. Conflicts, final scientific review, licenses and public release remain author decisions.
