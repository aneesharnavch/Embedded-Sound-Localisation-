# Journal review: coverage and method

Checked **7 September 2026**. Window: **7 September 2021–7 September 2026**, inclusive, using online publication dates.

## Coverage

| Review stage | Completed |
|---|---:|
| Official publisher entries in the six intersecting annual volumes | 438 |
| Entries before the rolling cutoff | 40 |
| Published items in the review window | **398** |
| Published items with a Crossref-deposited abstract | 388 |
| Full-text HTML extraction and keyword screening | 380 |
| Full-text PDF extraction and keyword screening | 18 |
| Pages extracted from those 18 PDFs | 336 |
| Published items without a full-text screen after recovery | **0** |
| Items with selected sections examined more closely | 16 |
| Records with substantive project notes | 26 |
| Additional publisher-confirmed forthcoming records | 12 |
| Additional unresolved publisher record | 1 |

The 398 include articles and the journal's editorial/correction/review material. Their online-year counts are 21, 61, 68, 81, 83 and 84 for 2021 through 2026 respectively. The first and last years are partial. Two entries assigned to the 2025 volume have 2026 online dates. The 2021 volume also includes 40 entries before the review window.

The unresolved extra record is [10.1051/aacus/2026090](https://doi.org/10.1051/aacus/2026090). Crossref supplies metadata, but both its primary publisher link and DOI redirect return the publisher's “Content not found” page. It is not counted as a published item or a reviewed full text. The other 12 additional records were individually checked on publisher landing pages identifying them as forthcoming. The generic forthcoming index showed older entries and was not used as the authority for these counts.

## Method

1. Read the [official archive](https://acta-acustica.edpsciences.org/component/issues/?task=all&Itemid=121) and all six annual tables of contents; collect their DOI sets and article labels.
2. Retrieve the journal's deposited records from [Crossref](https://api.crossref.org/journals/2681-4617/works). Reconcile records by DOI and apply exact online-date boundaries. A year-only query alone mixed forthcoming and volume-assigned records, so it was not used as the final census.
3. Screen titles and available abstracts across the full corpus. Apply transparent thematic keyword tags for direction estimation, rooms/reverberation, numerical verification, uncertainty, efficient computation, and spatial perception. Tags overlap and are search aids, not quality scores.
4. Retrieve the full HTML for each published item and scan the text for project-relevant concepts, including GCC, PHAT, TDOA, microphone arrays, benchmarks, fractional delays, bias, simulation, reverberation and uncertainty. Retain the distinction between full-text screening and closer scientific reading.
5. Recover 18 HTML extraction failures through the publisher's visible PDF links. Extract **every page**, verify the DOI within the extracted text, and run the same concept screen. The PDF manifest records pages, character counts, hashes, file paths and term matches.
6. Examine selected methods, results, limitations and/or conclusions in the closest papers, then write project-specific notes. The 16 closer-reading records are marked individually; the notes explain both useful precedents and reasons a result does not transfer to this project.
7. Read the journal's [author instructions](https://acta-acustica.edpsciences.org/author-information/instructions-for-authors), [data policy](https://acta-acustica.edpsciences.org/author-information/data-policy), current topical-issue listing and 2026 editorial. Treat acceptance timing, topical-issue eligibility and AI-policy interpretation separately from scientific readiness.

## What this review establishes

It provides a complete five-year **scoping census**, a full-text concept screen, relevant journal precedents, and a publication strategy tied to the current local evidence. The searchable register contains every title, author list, DOI, date, available abstract, thematic tags and screening level. It also contains the 13 additional records with their distinct status.

It does **not** claim line-by-line critical appraisal of all 398 items, reproduction of their experiments, inspection of every figure or equation image, review of every supplement, a formal systematic-review risk-of-bias assessment, or proof of novelty across all journals. A keyword hit can occur in a reference list; relevance notes rely on examined article content where stated. The external prior-art check was a targeted preliminary check, not a replacement for a focused global novelty search before submission.

Numerical claims in the publication plan come from the local code/draft audit or the explicitly described geometric diagnostic. A published paper is used as precedent only within its own scope. No field accuracy from another article is treated as directly comparable to this project's synthetic direction errors.

## Audit files

- [Searchable reading register](/home/ani/Desktop/sound_local/paper/publication_speedrun/READING_REGISTER.html)
- [Complete text register](/home/ani/Desktop/sound_local/paper/publication_speedrun/LITERATURE_REGISTER.md)
- [Structured literature register](/home/ani/Desktop/sound_local/paper/publication_speedrun/research/literature_register.json)
- [Coverage receipt](/home/ani/Desktop/sound_local/paper/publication_speedrun/research/screening_receipt.json)
- [PDF recovery manifest](/home/ani/Desktop/sound_local/paper/publication_speedrun/research/pdf_screening_receipt.json)
- [Publisher volume DOI census](/home/ani/Desktop/sound_local/paper/publication_speedrun/research/publisher_volume_dois.json)
- [Crossref source response](/home/ani/Desktop/sound_local/paper/publication_speedrun/research/crossref_all.json)

The 18 downloaded publisher PDFs and their extracted text were removed during the September 2026 repository cleanup. Their DOIs, original filenames, page counts, checksums, and screening receipts remain; see [recovery instructions](research/README.md). Their authorship and licenses remain those of the original publications; these are research sources, not assets to bundle into your own paper's code/data release. Other HTML full texts were inspected in the browser; a complete local HTML archive is not claimed.
