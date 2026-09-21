# Current Acta Acustica draft

The main folder contains the current manuscript and only the files required to compile or review it.

- `main_acta.tex` is the editable LaTeX manuscript.
- `main_acta.pdf` is the latest compiled paper.
- `main_acta_text.md` is the complete prose-only manuscript, including captions, tables and references.
- `main_acta_text.txt` is the same manuscript as unformatted plain text.
- `edpsci.cls` is the Acta Acustica document class.
- `references.bib` contains the bibliography.
- `figures/` contains the six figures used by the manuscript.
- `PREVIEW_QA.json` records the latest build and visual checks.
- `ACTA_README.md` contains manuscript-specific notes.

Build the paper from this folder with:

```sh
tectonic main_acta.tex
```

All supporting datasets, validation code, previous drafts, templates, logs and temporary material are preserved under `miscellaneous/`.
