# Direction A: author-review package

Prepared for **Aneesh Arnav Chikkala**, with **no affiliation** and **self-funding**. The package is **server-neutral** and uses Acta Acustica's scientific structure and presentation as a reference.

- [Nine-page preprint](manuscript/main.pdf)
- [Five-page supplement](manuscript/supplement.pdf)
- [Source and data bundle: rebuild instructions](release/README.md)
- [Reproduction guide](REPRODUCING.md)
- [Claim ledger](FINAL_CLAIM_LEDGER.md)

The paper is titled **“Separating arrival rounding, source startup, and reverberation in three-microphone azimuth estimation.”** It contains six main figures, three main tables, numbered verified references, line/page numbers and a structured abstract below 200 words. The supplement documents the model, derivation, statistics, correction history and reproduction.

The main finding is that simulation choices can change the acoustic condition being evaluated. At 10 dB, rounding arrivals raises direct-path RMSE from **0.923° to 2.300°**. In the high-reverberation subset, the first frame after startup gives **4.16°**, compared with **42.51°** for steady recordings. Longer averaging helps, but after 5.46 seconds the low and high subsets retain different errors: **0.835° and 10.158°**. These are results for the defined ideal simulation and estimator, with no hardware-performance or universal reverberation-floor claim.

The final campaign contains **276,480 primary estimates across 216 physical scenes**, plus the fixed sensitivity/baseline/refinement work. Every final frame, pairing, code/configuration hash and train/holdout allocation was audited. A fresh environment reproduced the numerical references and **8,640 representative primary estimates exactly**, and all six main PNG figures were byte-identical. This was a representative reproduction, not another full revised campaign.

One important correction is fully documented. A stronger numerical check found that the original response cutoff could change a few estimates by more than the 0.05° target. That entire run was preserved, the model was extended, and the full study was rerun with new inputs. The final paper uses only the corrected v2 results. The revised numerical checks pass; the initial run remains available for audit.

The remaining decisions are yours:

1. Confirm the **conflicts-of-interest declaration**; this remains explicitly pending in the draft.
2. Review and approve the **scientific claims and assistance disclosure**.
3. Choose **manuscript/data/code licenses** and approve any **public release**. No licenses have been assigned and nothing has been uploaded.

Your name, lack of affiliation and self-funding are already recorded. No preprint-server choice is needed to review this package; server-specific preparation is deferred as requested. Later Acta submission would require its own eligibility/policy check. The present work is labeled an unreviewed preprint and discloses substantive AI assistance accurately.
