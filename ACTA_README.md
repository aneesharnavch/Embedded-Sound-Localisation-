# Acta Acustica template preview

This preview responds to the author's request for the Acta template and a more direct writing style, using the original Journal of Open Hardware draft as a guide to the order and level of explanation.

Open `main_acta.pdf`. The editable source is `main_acta.tex`; the six vector figures and bibliography are included in this directory. Build with Tectonic from this directory:

```sh
tectonic main_acta.tex
```

Install Tectonic 0.17.0 as described in the reproduction guide at `miscellaneous/paper/direction_a_preprint/REPRODUCING.md`; the downloaded executable is not stored in the repository.

The supplied EDP Sciences class is used directly. Its source is `author/edpsci.cls`, version 1.1 dated 5 April 2024, in the project. The duplicate extracted template directory was removed during repository cleanup. The class file is unchanged. Small document-level compatibility fixes accommodate the header boxes, remove an unnecessary affiliation number for the single unaffiliated author, print bibliography DOIs correctly, and prevent excessive vertical stretching between paragraphs. Line numbers are enabled for review. Final-column balancing is omitted because it conflicts with the line-numbering output routine. The default two-column dimensions, fonts, title treatment, article band, headings and captions come from the template.

The opening label says “Template preview for Acta Acustica” rather than claiming a journal submission. The paper remains an unreviewed preprint. This is a local formatting and editorial preview; the previously delivered source/data release remains the scientific record for the verified v2 campaign.

The rewrite uses a practical introduction, a step-by-step description of the simulation, quality-control sections, and explanations of the equations and error measures. The original hardware draft guides tone and presentation; its unsupported timing, algorithm and hardware-performance claims are not used as evidence in this simulation paper.

On 22 September 2026, the manuscript prose was revised again using the author's RRAM, SyncPlate and long-form critical writing as voice references. The revision uses more direct first-person ownership, clearer mechanical explanations and less template-like phrasing while preserving the scientific results, equations, figures, tables, citations and stated limitations. The companion human-writing guide was applied only as an editorial reference; its workflow instructions were not treated as manuscript content.

Figures 2--6 remain byte-identical copies of the verified originals. Figure 1 was redrawn from the documented array geometry and matched-control design. The nine bibliography entries are unchanged. The 9 September corrections align averaging and verification descriptions with the implementation, specify interaction conditioning and numerical-check scope, correct captions and rounding, discuss shorter-duration prediction discrepancies, and narrow the efficiency claims. The abstract is below 200 words. The existing section structure is preserved. No simulation or analysis was changed for these manuscript corrections; the preceding audit's fresh checks remain documented in `miscellaneous/paper/direction_a_preprint/acta_preview/audit_2026-09-09/REPORT.md`. The existing supplement remains under `miscellaneous/paper/direction_a_preprint/manuscript/`.

The author is Aneesh Arnav Chikkala, with no institutional affiliation and self-funding. At the author's request, no new manuscript sections or disclosures were added during this correction pass; the author will complete that material separately. This preview does not claim completed submission readiness. Document checks for the rebuilt PDF are recorded in `PREVIEW_QA.json`. The draft as it stood before correction is preserved under `audit_2026-09-09/before_corrections/`.
