# DoA Paper Drafts Implementation Plan

**Goal:** Create a complete simulation-centered main-paper Markdown draft and a matching supplementary-materials Markdown draft without modifying `paper.md` or its abstract.

**Architecture:** The main draft will be a readable manuscript with formal equations, explicit claims, inline conceptual figures, and hardware placeholders. The supplementary draft will hold derivations, protocols, estimator pseudocode, statistical reporting, provenance, and the hardware-data boundary.

**Tech Stack:** Markdown, LaTeX math, Mermaid diagrams, existing project Markdown results.

**Global constraints:**

- Copy the abstract from `paper.md` unchanged.
- Do not invent hardware measurements or measured localization accuracy.
- Distinguish simulation results, acquisition-chain measurements, and outstanding hardware validation.
- Use the post-rebaseline numerical results as the authoritative simulation values.
- Keep `paper.md` unchanged.

### Task 1: Create the main-paper draft

**Files:**
- Create: `main_paper_draft.md`

- [ ] Copy the original abstract verbatim.
- [ ] Complete the introduction, related work, system model, method, simulation, discussion, and conclusion around the existing evidence.
- [ ] Include formal confidence-score, gating, weighted least-squares, circular-accumulation, bias-floor, GDOP, and complexity mathematics.
- [ ] Add inline conceptual diagrams and figure-ready empirical figure specifications.
- [ ] Mark hardware-dependent values as `[HARDWARE DATA REQUIRED]`.

### Task 2: Create the supplementary-materials draft

**Files:**
- Create: `supplementary_materials_draft.md`

- [ ] Provide full notation and derivations.
- [ ] Document simulation parameters, estimators, confidence statistics, ablations, uncertainty, and provenance.
- [ ] Add reproducibility, figure, and hardware-campaign checklists.
- [ ] Preserve the negative findings and prohibit unsupported claims.

### Task 3: Verify the deliverables

- [ ] Confirm `paper.md` has no diff.
- [ ] Confirm the abstract block in the main draft matches `paper.md` exactly.
- [ ] Scan both drafts for unresolved accidental placeholders, fabricated hardware values, and required section headings.
- [ ] Report remaining intentional hardware placeholders explicitly.
