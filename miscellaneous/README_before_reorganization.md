# Three-microphone sound localization

ESP32-S3 firmware, microphone recordings, Python validation tools, and the source and results for the Direction A sound-localization paper.

## Start here

- [Current Acta Acustica preview](paper/direction_a_preprint/acta_preview/main_acta.pdf)
- [Preprint](paper/direction_a_preprint/manuscript/main.pdf) and [supplement](paper/direction_a_preprint/manuscript/supplement.pdf)
- [Reproduction instructions](paper/direction_a_preprint/REPRODUCING.md)
- [Author review and claim summary](paper/direction_a_preprint/AUTHOR_REVIEW.md)
- [Project history and data limitations](HANDOVER.md)

The paper uses simulated data. The historical microphone recordings are included separately and do not establish the paper's simulation results.

## Contents

| Folder | Contents |
| --- | --- |
| `Software/`, `firmware/` | Arduino/ESP32 code, DSP library, and calibration scripts |
| `validation/` | Simulation, real-recording analysis, and tests |
| `paper/direction_a_preprint/` | Current paper, figures, configurations, verified results, and correction history |
| `paper/publication_speedrun/` | Literature register and research notes |
| `Microphone calibration data/` | Original calibration and idle recordings |
| `Microphone feedback with respect to Frequency and Distance/` | Frequency/distance measurements |
| `Triple Mic Samples/` | Original three-channel recordings |
| `idle mic data/` | Historical idle data and processing scripts |
| `Quadrant Based Estimations/` | Geometric reference tables |
| `Filter alogrithims test/` | Historical filter experiments |
| `author/` | EDP Sciences template and editable historical sources |

Directory spellings are retained for compatibility with existing loaders. See `HANDOVER.md` for known limitations of the historical data and scripts.

## Setup and checks

From the project root, create a Python 3.12 environment:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r paper/direction_a_preprint/environment/requirements-lock.txt
OPENBLAS_NUM_THREADS=1 PYTHONPATH=paper .venv/bin/python -m pytest -q validation/direction_a/test_direct.py validation/direction_a/test_room.py validation/direction_a/test_srp.py paper/tests/test_generate_paper_figures.py
```

These pinned dependencies cover the Direction A simulation and figure tests. Historical recording scripts may require additional packages such as pandas and openpyxl. See the [reproduction guide](paper/direction_a_preprint/REPRODUCING.md) for analysis and document builds.

## Keeping the repository small

The September 2026 cleanup retained the recordings, source code, current documents, scientific results, and the superseded experiment needed to audit the numerical correction. The duplicate `callibration data/` import was checked file by file before removal; its 419 files matched the retained originals.

Local Python installations, simulation caches, duplicate release/extraction folders, downloaded literature, full-page document renders, and build intermediates are excluded by `.gitignore`. Recording formats, final PDFs, and scientific run logs are deliberately included.

The old full-project snapshot was replaced with its [three unique older documents and original manifest](paper/direction_a_preprint/baseline/README.md). A [source/data ZIP can be rebuilt](paper/direction_a_preprint/release/README.md) when needed. Downloaded literature can be recovered using the retained [DOIs and screening records](paper/publication_speedrun/research/README.md).
