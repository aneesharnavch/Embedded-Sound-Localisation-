# Literature source records

`crossref_all.json` retains the complete original Crossref response. `publisher_volume_dois.json`, the screening receipts, and `reading_notes.json` retain the source identifiers, review coverage, and project notes. `candidate_scores.json` preserves the order and screening scores from the former ranked-candidate export without repeating the full source records.

The date-filtered Crossref response was an exact subset of `crossref_all.json`. `window_items.json` and `ranked_candidates.json` repeated those same records with derived screening dates, cleaned text, or scores. These large duplicate exports were removed during the September 2026 cleanup.

Rebuild the reading registers with:

```sh
python3 paper/publication_speedrun/research/build_catalogue.py
```

Downloaded publisher PDFs, their extracted text, and cached publisher HTML were also removed. The retained `pdf_screening_receipt.json` records each PDF's DOI, original filename, page count, and SHA-256 digest. Follow `https://doi.org/<doi>` to the publisher and download the matching PDF to `publisher_pdfs/<filename>` if it is needed again. With those PDFs present and `pypdf` installed, `screen_pdf_alternatives.py` regenerates the text extracts and screening receipt. The download and extract directories are ignored by Git.
