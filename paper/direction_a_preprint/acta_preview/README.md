# Acta Acustica template preview

This preview responds to the author's request for the Acta template and a more direct writing style, using the original Journal of Open Hardware draft as a guide to the order and level of explanation.

Open `main_acta.pdf`. The editable source is `main_acta.tex`; the six vector figures and bibliography are included in this directory. Build with Tectonic from this directory:

```sh
tectonic main_acta.tex
```

Install Tectonic 0.17.0 as described in [the reproduction guide](../REPRODUCING.md); the downloaded executable is not stored in the repository.

The supplied EDP Sciences class is used directly. Its source is `author/edpsci.cls`, version 1.1 dated 5 April 2024, in the project. The duplicate extracted template directory was removed during repository cleanup. The class file is unchanged. Small document-level compatibility fixes accommodate the header boxes, remove an unnecessary affiliation number for the single unaffiliated author, print bibliography DOIs correctly, balance the final columns, and prevent excessive vertical stretching between paragraphs. The default two-column dimensions, fonts, title treatment, article band, headings and captions come from the template.

The opening label says “Template preview for Acta Acustica” rather than claiming a journal submission. The paper remains an unreviewed preprint. This is a local formatting and editorial preview; the previously delivered source/data release remains the scientific record for the verified v2 campaign.

The rewrite uses a practical introduction, a step-by-step description of the simulation, quality-control sections, and explanations of the equations and error measures. The original hardware draft guides tone and presentation; its unsupported timing, algorithm and hardware-performance claims are not used as evidence in this simulation paper.

All six figures are byte-identical copies of the verified originals. The nine bibliography entries are unchanged. The numerical study, estimates, uncertainty intervals, correction history and limits are retained. No experiment was rerun for this editorial change. The existing supplement supplies the extended methods and reproduction details.

The author is Aneesh Arnav Chikkala, with no institutional affiliation and self-funding. Conflict confirmation, scientific sign-off and any public release are still pending. The preview's document checks are recorded in `PREVIEW_QA.json`.
