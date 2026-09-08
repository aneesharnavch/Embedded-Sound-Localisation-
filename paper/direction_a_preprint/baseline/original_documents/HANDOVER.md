# Session Handover — 3-Mic Embedded DoA Paper

> **Current direction — 7 September 2026:** the author selected **Direction A, preprint first**, with Acta Acustica's scientific and presentation standards. The assistant owns technical execution, analysis, figures, drafting, and packaging; the author reviews and decides the public release. Follow the [preprint execution checklist](/home/ani/Desktop/sound_local/paper/publication_speedrun/DIRECTION_A_PREPRINT_TODO.md), [research plan](/home/ani/Desktop/sound_local/paper/publication_speedrun/ACTA_ACUSTICA_ROUTE_A_PLAN.md), and [scientific audit](/home/ani/Desktop/sound_local/paper/publication_speedrun/SCIENTIFIC_AUDIT.md). Acta editorial-policy clarification is deferred to any later journal submission. The older thesis and blanket simulation-only rejection claim below are superseded. The research campaign is planned, not yet executed.

> **Read this first if you are the next session.** It captures the whole project state: goal,
> what exists, what the numbers are, what the new data means, what's fabricated (and must stay out),
> and what to do next. Written 2026-07-27.

---

## 1. What this project is

An ESP32-S3, custom-PCB, **3-microphone (triangular, ~5 cm aperture)** real-time
direction-of-arrival (DoA) / sound-localization platform. Aneesh Arnav Chikkala — independent /
high-school researcher, **no prior publications**, working solo.

**Target venue:** *Acta Acustica* (EAA / EDP Sciences), as a **Technical & Applied Article**
(lowest realistic novelty bar). Diamond Open Access = €0, ~55% acceptance, IF ~1.4, **LaTeX-only,
English-only**. Best-fit section: *Audio Signal Processing and Transducers*. Consider the open
**"Benchmarking Acoustics" topical issue** (check deadline). LaTeX class is in the repo
(`macro_latex_edpsci_EN (1).zip`, `readme.txt`, `history.txt`, `instruction.pdf`).

**History / do-not-repeat:** an earlier **Journal of Open Hardware metapaper draft FAILED**. Do
not resurrect its framing. The `.docx` in the repo root is scrap/source only. The old draft's
"Hedging / Embedded Decision-Validation Network / 10 µs" claims are **vapor — drop them entirely.**

**Governing principle:** Aneesh was burned by overclaiming and explicitly needs *real* novelty and
*traceable* numbers. Every number must come from the shared harness on sim AND real data. Honesty
over marketing, always.

---

## 2. The honest contribution (the paper's thesis)

**Confidence-weighted temporal accumulation** of per-frame GCC-PHAT DoA on a cheap 3-mic array:
trade <1 s latency (~20 frames) for an order-of-magnitude accuracy gain. Error falls as ≈`1/√T`
down to an **RT60-dependent reverberation bias floor** that accumulation *cannot* cross (state this
explicitly — accumulation removes stochastic noise error, not deterministic multipath bias).

**Two honest negative results to REPORT, not hide:**
1. The per-frame **spatial** refinement (PSR confidence gate + weighting, i.e. the reframed
   "PID/decision-tree") is **essentially tied with plain GCC-PHAT** — with only 3 mics there is no
   redundancy for hard gating to exploit. Keep it as an ablation, not a headline.
2. RMSE is *inflated at high SNR* by rare wrap/ambiguity outliers on the small array (median is
   monotone though) — this actually *motivates* temporal accumulation.

---

## 3. Current state of the code (`validation/`)

All pure numpy/scipy/matplotlib, Python 3.14 (pyroomacoustics won't build on 3.14). Fixed RNG seed
(7) → reproducible figures. Figures land in `validation/figs/`.

| File | What it does | Key functions |
|---|---|---|
| `doa_benchmark.py` | Free-field plane-wave sim + all 4 estimators + core figs | `est_gccphat_ls`, `est_proposed`, `est_srp_phat`, `est_music`, `accumulate_doa`, `track_pid`, `simulate` |
| `reverb_robustness.py` | Image-source room model; accuracy vs RT60 | `build_rirs`, `simulate_reverb`, `run_rt60_sweep` |
| `ablation.py` | Gate/weight ablation, resource scaling (aperture, snapshot), **temporal accumulation** | `ablation_vs_rt60`, `scaling_vs_aperture`, `scaling_vs_snaplen`, `temporal_freefield`, `temporal_reverb` |
| `real_data.py` | Bridge: runs REAL clips through the SAME estimators. Filename convention `az<+/-DDD>_...`. Also `--latency` for ESP32 timing logs | `evaluate_dir`, `load_multichannel`, `summarize_latency` |

**Array geometry as configured:** equilateral triangle, R = 5 cm, mics at 90/210/330° →
`[[0,5],[-4.33,-2.5],[4.33,-2.5]]` cm. fs = 48 kHz, snapshot 2048 samples (~43 ms).
**These are placeholders — must be replaced with MEASURED board values.**

> ### SUPERSEDED — read `paper/rebaseline_results.md` before using any number below
> A defect was found in the GCC-PHAT front end on 2026-07-27: the PHAT weight was applied over
> the full 0–24 kHz band while the source occupies 300–3400 Hz. **Every simulation number in
> this section was produced with the defective front end and must not be used.** The harness has
> been fixed and every simulation re-run; the replacements, with standard errors, are in
> `paper/rebaseline_results.md` and in `validation/{benchmark,reverb,ablation}_run.log`. The old
> logs are preserved under `validation/archive/`.
> Headlines of the re-baseline: free-field per-frame RMSE at 10 dB falls from 4.32° to
> 0.301 ± 0.006°; **negative result #2 (high-SNR RMSE inflation) is retracted** — it was a
> symptom of the defect; the compute claim that "ratios transfer to MCU" is **retracted**; and
> temporal accumulation is **no longer the dominant lever**, because the reverberation bias
> floor is now reached within four to eight frames. Section 9 of `rebaseline_results.md` lists
> every claim that changes.

### Real simulation numbers already in the logs (traceable, use in text)
From `benchmark_run.log` (free field, median / p90 / RMSE deg):
- Proposed (gated) @10 dB: median 2.88, p90 7.02, RMSE 4.32
- GCC-PHAT @10 dB: median 2.82, p90 6.89, RMSE 4.23  → **proposed ≈ GCC-PHAT (negative result #1)**
- @40 dB median drops to ~0.34° (proposed) / 0.35° (GCC); RMSE inflated by outliers = negative result #2
- Compute (x86, ratios transfer): Proposed 1.35 ms ≈ GCC 1.29 ms; SRP 5.49 ms (4.3×); MUSIC 5.46 ms (4.2×)

From `ablation_run.log`:
- **Temporal accumulation, free field (weighted), T=1→32:** 3.88 → 2.90 → 2.20 → 1.33 → 0.96 → 0.68° (tracks 1/√T)
- Weighted ≈ plain mean in free field (small gain in reverb only)
- **Reverb floors (RMSE at T=32):** RT60 0.15 s → 2.14°; 0.3 s → 2.00°; 0.6 s → 2.60°
- **Ablation vs RT60:** gate+weight ≈ neither(=GCC-PHAT) at every RT60 (2.2–5.9°) → confirms negative result #1
- **Aperture scaling:** 7.31°@2 cm → 4.63@3 → 2.95@5 → 1.65@8 → 1.10°@12 cm
- **Snapshot scaling:** 4.27°@5 ms → 3.40@11 → 3.06@21 → 2.72@43 → 2.40°@85 ms

Figures already generated (see `paper/paper_outline.md` figure inventory): geometry, SRP spectrum,
RMSE vs SNR, error CDF, accuracy matrix, accuracy vs RT60, ablation, **temporal accumulation
(headline)**, resource scaling, Pareto.

---

## 4. The NEW data (added this session) and how it changes scope

| Folder | What it actually is | Scope impact |
|---|---|---|
| `Triple Mic Samples/sample_*.xlsx` | 25 **real** ESP32-S3 recordings, 3 ch (MIC1/2/3, 12-bit ADC ~1250 DC), each 30 samples, header-labeled with a source position e.g. `(0,15)` | Start of the real hardware campaign → Section 6. Feed to `real_data.py`. `results.csv` is empty. |
| `Quadrant Based Estimations/quadrant_{1..4}.csv` | `(x,y,t)` grids over a 3 m × 3 m plane, `t` = propagation time ≤ ~146 µs | **Near-field 2-D (x,y) position** via TDOA — a scope extension beyond far-field azimuth |
| `idle mic data/{data,filtered_data}.xlsx` | ~24.7 k-sample idle (no-source) recording + filtered | Microphone **self-noise / noise-floor** characterization; grounds the SNR axis in a measured floor |

**Decision needed from Aneesh:** keep near-field 2-D quadrant result as a scoped secondary
section/appendix, or cut it to keep the azimuth story tight? (Recommendation: keep as appendix.)

---

## 5. 🚨 DATA-INTEGRITY WARNINGS (critical — do not let these slip)

1. **`Triple Mic Samples/python.py` FABRICATES data.** It builds an accuracy heatmap with
   `np.random.uniform(0.4, 0.76)` forced to a preset **77% average** — it never reads the real
   clips. This figure MUST NOT appear in the paper in any form. Real accuracy comes only from
   `real_data.py` on the labeled clips. This is the exact overclaiming that sank the JoH draft.
2. The 30-sample length of each `sample_*.xlsx` is very short for GCC-PHAT (needs verification that
   these are usable snapshots, or whether they're single-frame captures to be concatenated).
3. Old `.docx` "10 µs / Hedging / Decision-Validation Network" — vapor. Never cite or repeat.

---

## 6. Deliverables produced this session

- **`paper/references.md`** — full, honest, scope-grounded citation list. Every entry maps to code
  run, a baseline compared, or a claim made. Organized in tiers (A must-cite → C optional), with
  BibTeX for the core refs, a priority list, and a map to the outline's `[CITE]` tags. Verified the
  non-canonical refs (Grondin & Michaud '19, Valin '07, Argentieri '15, Chan & Ho '94, DiBiase '00)
  via web search. **Every DOI/volume still needs a final publisher check before submission** —
  flagged at top of that file.
- Memory updated: `new-datasets-and-scope.md` (+ MEMORY.md index entry).

---

## 7. What's DONE vs PENDING

**Done:** simulation harness (all 4 estimators + reverb + ablation + temporal + resource scaling);
all sim figures; paper outline/skeleton; honest thesis + negative results identified; citation list.

**Pending (in rough priority):**
1. **THE MAKE-OR-BREAK:** real measurement campaign — labeled angles, ≥2 rooms (damped vs live),
   RT60 estimated, broadband + speech sources, ground-truth uncertainty stated. Acta Acustica will
   **reject a simulation-only submission.** The `Triple Mic Samples/` clips are the seed of this but
   likely insufficient (need labeled azimuths via `az<±DDD>` filenames, multiple rooms).
2. Replace ALL `[MEASURE]` placeholders in `paper_outline.md` §3/§6 with real board values
   (geometry, fs, snapshot, BOM/cost, on-device latency via `real_data.py --latency`).
3. Run `real_data.py` on the real clips → Section 6 tables + measured-vs-sim CDF overlay.
4. Verify every DOI/volume/page in `paper/references.md` at the publisher.
5. Decide near-field quadrant scope (§4 above).
6. Confirm the actual MEMS mic part on the board (INMP441? ICS-43434?) → finalizes the
   self-noise citation and §3 datasheet reference.
7. Draft the LaTeX in the edpsci class.

---

## 8. Open questions for Aneesh
- Which MEMS mic part is on the board? (needed for datasheet + self-noise citation)
- Keep or cut the near-field 2-D quadrant result?
- Status of the real measurement campaign — how many rooms, what angles, is a turntable/protractor
  setup available?

---

## 9. File map (repo root: `C:\Users\anees\OneDrive\Desktop\embedded_sound_local`)
```
paper/paper_outline.md        ← draft skeleton, abstract drafted, [MEASURE]/[CITE] tags, fig inventory
paper/references.md           ← THIS SESSION: citation list (verify DOIs before use)
HANDOVER.md                   ← this file
validation/*.py               ← simulation harness (see §3)
validation/*_run.log          ← real sim numbers (see §3)
validation/figs/              ← generated figures
Triple Mic Samples/           ← REAL recordings (+ FABRICATED python.py — do not use its output)
Quadrant Based Estimations/   ← near-field (x,y,t) grids
idle mic data/                ← mic self-noise floor
*.docx                        ← old failed JoH draft — scrap/source ONLY
macro_latex_edpsci_EN.zip, readme.txt, history.txt, instruction.pdf  ← EDP Sciences LaTeX class
```

Memory dir (persists across sessions):
`C:\Users\anees\.claude\projects\C--Users-anees-OneDrive-Desktop-embedded-sound-local\memory\`
→ `acta-acustica-target.md`, `researcher-profile.md`, `temporal-accumulation-contribution.md`,
`new-datasets-and-scope.md`, indexed in `MEMORY.md`.
