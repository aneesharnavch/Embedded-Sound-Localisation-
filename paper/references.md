# References for the 3-Mic Embedded DoA Paper (Acta Acustica, Technical & Applied Article)

> **Purpose.** A realistic, honest citation list built from what the project *actually does* —
> the code in `validation/`, the simulation results in the run logs, the paper outline, and the
> new datasets (`Triple Mic Samples/`, `Quadrant Based Estimations/`, `idle mic data/`).
> Nothing here is padding: every entry maps to a method you implemented, a baseline you compared
> against, a phenomenon you measured, or a claim you make in the text.
>
> **⚠️ Verify-before-submit.** DOIs, volumes, and page numbers below are given to my best
> knowledge but MUST each be confirmed at the publisher (IEEE Xplore / AIP / Springer / Elsevier /
> HAL) before the bibliography is final. Do not paste a DOI you have not opened.
>
> **⚠️ Data-integrity note (read this).** `Triple Mic Samples/python.py` generates a *synthetic*
> accuracy heatmap (`np.random.uniform(...)` forced to a 77 % mean). That is fabricated data and
> cannot appear in the paper in any form. The real `sample_*.xlsx` clips must go through
> `validation/real_data.py` (same estimators as the sim) to produce Section 6 numbers. This file
> assumes the honest pipeline, not the heatmap.

---

## 0. How the new data changes the scope (so the citations make sense)

| New dataset | What it actually is | Scope it adds | New citations it pulls in |
|---|---|---|---|
| `Triple Mic Samples/sample_*.xlsx` | 25 real ESP32-S3 recordings, 3 channels (MIC1/2/3, 12-bit ADC ~1250 DC), each labeled with a source position header, e.g. `(0,15)` | **Real-hardware validation** (Sec. 6) — the make-or-break campaign | MEMS-mic + ESP32 hardware refs; the GCC-PHAT/SRP/MUSIC method refs applied to measured clips |
| `Quadrant Based Estimations/quadrant_{1..4}.csv` | `(x, y, t)` grids over a 3 m × 3 m plane, per quadrant; `t` = propagation/arrival time (≤ ~146 µs) | **Near-field 2-D (x, y) position** localization, not just far-field azimuth — a genuine scope extension | Near-field TDOA / hyperbolic multilateration refs (Chan–Ho, Smith–Abel, Huang, Brandstein) |
| `idle mic data/{data,filtered_data}.xlsx` | ~24.7 k-sample idle (no-source) recording + a filtered version | **Microphone self-noise / noise-floor characterization** — grounds your SNR axis in a *measured* floor | MEMS self-noise + coherence/TDOA-accuracy-vs-SNR refs |

**Consequence for the paper:** you now have two localization regimes to cite for, not one —
(a) far-field **azimuth** (GCC-PHAT / SRP-PHAT / MUSIC, the current sim), and (b) near-field
**2-D position** from TDOA multilateration (the quadrant maps). Keep the azimuth story as the
headline (it's what the sim + temporal-accumulation result support); present the 2-D quadrant work
as either a modeling appendix or a clearly-scoped secondary result, and cite the multilateration
family (§4 below) for it.

---

## 1. Core methods you implemented — MUST cite (Tier A)

These are non-negotiable: the reader must be able to trace every estimator in `doa_benchmark.py`
to its origin.

### GCC-PHAT / TDOA — your `gcc_phat`, `tdoa_phat`, `est_gccphat_ls`
- **Knapp & Carter (1976)** — the paper that defines GCC and the PHAT weighting. This is *the*
  citation for your whole front end.
  ```bibtex
  @article{knapp1976gcc,
    author  = {Knapp, Charles and Carter, Glen},
    title   = {The generalized correlation method for estimation of time delay},
    journal = {IEEE Transactions on Acoustics, Speech, and Signal Processing},
    volume  = {24}, number = {4}, pages = {320--327}, year = {1976},
    doi     = {10.1109/TASSP.1976.1162830}
  }
  ```

### SRP-PHAT — your `est_srp_phat`
- **DiBiase (2000), PhD thesis, Brown University** — origin of SRP-PHAT (steered response power
  with phase transform). *Verified title:* "A High-Accuracy, Low-Latency Technique for Talker
  Localization in Reverberant Environments Using Microphone Arrays" (advisor H. F. Silverman).
  ```bibtex
  @phdthesis{dibiase2000srpphat,
    author = {DiBiase, Joseph H.},
    title  = {A High-Accuracy, Low-Latency Technique for Talker Localization in
              Reverberant Environments Using Microphone Arrays},
    school = {Brown University}, year = {2000}
  }
  ```
- **DiBiase, Silverman & Brandstein (2001)** — the accessible book-chapter version of SRP-PHAT, in
  Brandstein & Ward (see §5). Cite alongside the thesis; reviewers reach for the chapter.

### MUSIC (subspace) — your `est_music`
- **Schmidt (1986)** — the MUSIC algorithm. Your "accuracy ceiling / compute floor" baseline.
  ```bibtex
  @article{schmidt1986music,
    author  = {Schmidt, Ralph O.},
    title   = {Multiple emitter location and signal parameter estimation},
    journal = {IEEE Transactions on Antennas and Propagation},
    volume  = {34}, number = {3}, pages = {276--280}, year = {1986},
    doi     = {10.1109/TAP.1986.1143830}
  }
  ```

### Image-source room model — your `reverb_robustness.py`
- **Allen & Berkley (1979)** — the image method you implement for RT60→reflection reverberation.
  ```bibtex
  @article{allen1979image,
    author  = {Allen, Jont B. and Berkley, David A.},
    title   = {Image method for efficiently simulating small-room acoustics},
    journal = {The Journal of the Acoustical Society of America},
    volume  = {65}, number = {4}, pages = {943--950}, year = {1979},
    doi     = {10.1121/1.382599}
  }
  ```
- **Habets (2006, rev. 2010), "Room Impulse Response Generator," tech. report, TU Eindhoven** —
  the widely-cited reference implementation your code mirrors (uniform-wall β, Sabine RT60→β).
  Cite so reviewers know your ISM is the standard one, not ad hoc.

---

## 2. Reverberation, TDOA accuracy & the theory behind your results — MUST/strongly cite (Tier A/B)

These support the *findings*, not just the methods: the `1/√T` accumulation law, the reverb bias
floor, and the SNR axis.

- **Carter (1987), "Coherence and time delay estimation," Proc. IEEE 75(2):236–255** — the CRB /
  coherence framework that justifies why averaging independent frames drives error as `1/√T` and
  why coherence loss (reverberation) sets a floor accumulation can't cross. Directly underwrites
  your headline result and your honest "floor" caveat.
  DOI: `10.1109/PROC.1987.13723`.
- **Brandstein & Silverman (1997), "A robust method for speech signal time-delay estimation in
  reverberant rooms," ICASSP** — the canonical statement that reverberation, not noise, is what
  breaks TDOA, and motivates confidence/reliability weighting of GCC peaks. This is the honest
  home for your PSR gate/weight layer *and* the reverb-floor discussion.
  DOI: `10.1109/ICASSP.1997.599651`.
- **Litovsky, Colburn, Yost & Guzman (1999), "The precedence effect," JASA 106(4):1633–1654** —
  cite in the *future-work / floor* discussion: precedence-effect / early-reflection gating is the
  principled way to lower the reverb floor you report. DOI: `10.1121/1.427914`.

---

## 3. Related work / positioning — strongly recommended (Tier B)

This is the §2 "Background and related work" that keeps you honestly in "Technical & Applied"
scope: cheap + embedded localizers, and DoA tracking as the family your accumulator belongs to.

- **Grondin & Michaud (2019), "Lightweight and optimized sound source localization and tracking
  methods...," Robotics and Autonomous Systems 113:63–80** — *verified.* The ODAS/ManyEars line:
  the closest prior "make SSL cheap enough to embed" work. Your key contrast: they still use
  8 mics; you ask how far 3 mics go. DOI: `10.1016/j.robot.2018.11.009`.
  ```bibtex
  @article{grondin2019lightweight,
    author  = {Grondin, Fran\c{c}ois and Michaud, Fran\c{c}ois},
    title   = {Lightweight and optimized sound source localization and tracking methods
               for open and closed microphone array configurations},
    journal = {Robotics and Autonomous Systems},
    volume  = {113}, pages = {63--80}, year = {2019},
    doi     = {10.1016/j.robot.2018.11.009}
  }
  ```
- **Valin, Michaud & Rouat (2007), "Robust localization and tracking of simultaneous moving sound
  sources using beamforming and particle filtering," Robotics and Autonomous Systems 55(3):216–228**
  — *verified.* The particle-filter DoA-tracking anchor; position your O(1)-memory confidence-
  weighted accumulator as the *minimal* member of this tracking family. DOI: `10.1016/j.robot.2006.08.004`.
- **Argentieri, Danès & Souères (2015), "A survey on sound source localization in robotics: from
  binaural to array processing methods," Computer Speech & Language 34(1):87–112** — *verified.*
  The survey that names your exact constraints (embeddability, real-time, reverb, noise). One clean
  citation for "classic methods are compute-/mic-heavy" in the Introduction. DOI: `10.1016/j.csl.2015.03.003`.

---

## 4. Near-field 2-D position (the `Quadrant Based Estimations/` data) — cite if you keep it (Tier B/C)

Only needed because the quadrant `(x, y, t)` maps push you from far-field azimuth into near-field
2-D TDOA localization. If you keep that result, cite the multilateration family:

- **Chan & Ho (1994), "A simple and efficient estimator for hyperbolic location," IEEE Trans.
  Signal Processing 42(8):1905–1915** — *verified.* The standard closed-form TDOA→(x,y) estimator;
  the natural reference for turning your per-pair delays into a position. DOI: `10.1109/78.301830`.
  ```bibtex
  @article{chan1994hyperbolic,
    author  = {Chan, Y. T. and Ho, K. C.},
    title   = {A simple and efficient estimator for hyperbolic location},
    journal = {IEEE Transactions on Signal Processing},
    volume  = {42}, number = {8}, pages = {1905--1915}, year = {1994},
    doi     = {10.1109/78.301830}
  }
  ```
- **Smith & Abel (1987), "Closed-form least-squares source location estimation from range-
  difference measurements," IEEE Trans. ASSP 35(12):1661–1669** — spherical-interpolation
  closed-form; the older companion to Chan–Ho. DOI: `10.1109/TASSP.1987.1165089`.
- **Huang, Benesty, Elko & Mersereau (2001), "Real-time passive source localization: a practical
  linear-correction least-squares approach," IEEE Trans. Speech & Audio Processing 9(8):943–956** —
  near-field, real-time, few-mic 2-D/3-D localization — closest in spirit to your quadrant setup.
  DOI: `10.1109/89.966097`.
- **Brandstein, Adcock & Silverman (1997), "A closed-form location estimator for use with room
  environment microphone arrays," IEEE Trans. Speech & Audio Processing 5(1):45–50** — the
  linear-intersection estimator; optional third multilateration cite. DOI: `10.1109/89.554268`.

---

## 5. Textbooks / foundations — cite 1–2 (Tier B)

Anchor the array-processing background with one or two standard texts rather than many papers.

- **Brandstein & Ward (eds.) (2001), "Microphone Arrays: Signal Processing Techniques and
  Applications," Springer** — the standard edited volume; also the home of the SRP-PHAT chapter.
  ISBN 978-3-540-41953-2.
- **Benesty, Chen & Huang (2008), "Microphone Array Signal Processing," Springer** — modern
  reference for GCC/TDOA localization and array theory. DOI (book): `10.1007/978-3-540-78612-2`.
- **Van Trees (2002), "Optimum Array Processing (Detection, Estimation, and Modulation Theory,
  Part IV)," Wiley** — cite *only* if you invoke CRB / resolution-vs-aperture formally in §4.5/§5.6.
- **Kuttruff, "Room Acoustics" (Spon/CRC, latest ed.)** — one clean citation for Sabine's equation
  and RT60, backing `rt60_to_beta` in `reverb_robustness.py`, instead of Sabine's 1922 original.

---

## 6. Hardware & applications — supporting (Tier C, several are grey literature)

For §3 (platform) and §1/§7 (motivation). These are datasheets / standards / application anchors;
keep them minimal and label grey literature honestly.

- **ESP32-S3 technical reference manual, Espressif Systems** — the MCU; cite the datasheet/TRM in §3.
- **MEMS microphone datasheet for your actual part** (e.g. InvenSense **ICS-43434** or **INMP441**
  I²S MEMS mic — *confirm which part is on your board*) — needed for §3 (sensitivity, AOP, and the
  **self-noise floor** you characterize with `idle mic data/`). The datasheet's equivalent-input-
  noise spec is what your idle recording should be compared against.
- **Farmani, Pedersen, Tan & Jensen (2017/2019), "Informed sound source localization using relative
  transfer functions for hearing aid applications," IEEE/ACM TASLP** — *verify details* — a concrete
  hearing-aid DoA anchor for the §7 application paragraph. Use only if you keep the hearing-aid motivation.
- **A TinyML / edge-audio anchor** (e.g. Warden & Situnayake, "TinyML," O'Reilly 2019, or a keyword-
  spotting-on-MCU paper) — optional, one citation to justify "DoA on a $-class MCU is a real design point."

---

## 7. Priority / what to actually put in the bibliography

**Definitely (8–10 refs, the honest minimum for this scope):**
Knapp & Carter 1976 · DiBiase 2000 (+ Brandstein–Ward chapter) · Schmidt 1986 · Allen & Berkley 1979 ·
Carter 1987 · Brandstein & Silverman 1997 · Grondin & Michaud 2019 · Argentieri et al. 2015 ·
Benesty/Chen/Huang 2008 (or Brandstein & Ward 2001).

**Add if you keep the near-field quadrant result:** Chan & Ho 1994 (+ one of Smith–Abel / Huang et al.).

**Add for depth / discussion:** Valin et al. 2007 (tracking family) · Litovsky et al. 1999 (precedence,
future work) · Habets 2006 (ISM implementation) · Kuttruff (RT60) · ESP32-S3 TRM + MEMS-mic datasheet.

**Do NOT cite / do NOT use:** the fabricated heatmap from `Triple Mic Samples/python.py`, and any
"10 µs / Embedded Decision-Validation Network / Hedging" framing from the old JoH `.docx` — those are
vapor and were flagged as such.

---

### Mapping to the outline's `[CITE]` tags
- §2 "SRP-PHAT [CITE DiBiase]" → DiBiase 2000 + Brandstein–Ward chapter.
- §2 "GCC-PHAT [CITE Knapp & Carter 1976]" → Knapp & Carter 1976. ✓
- §2 "MUSIC [CITE Schmidt]" → Schmidt 1986. ✓
- §2 "small/embedded arrays [CITE]" → Grondin & Michaud 2019 + Argentieri et al. 2015.
- §2 "temporal integration / tracking [CITE]" → Valin et al. 2007 + Carter 1987.
- §5.1 image-source [Allen & Berkley] → Allen & Berkley 1979 + Habets 2006. ✓
- Back-matter reference list → all of §7 "Definitely" above.
