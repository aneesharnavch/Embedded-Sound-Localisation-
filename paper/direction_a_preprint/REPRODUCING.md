# Reproducing Direction A

The final paper uses the revised v2 campaign only. The original v1 campaign failed a stronger joint duration/image refinement and is retained under `superseded/v1_duration_0p9`; its estimates are not pooled into the final paper. See `NUMERICAL_NOTES.md` and the protocol amendment.

The repository and source-and-data archive preserve the project-relative layout. Run the commands below from the directory containing `validation/` and `paper/`. The code locates its output directory relative to that root. Python 3.12.14 and the pinned scientific packages are the recorded environment; version details and hashes are in `environment/`. This is a local, server-neutral review package and has no assigned public DOI. The generated ZIP and extracted reproduction workspace were removed during repository cleanup; see [release/README.md](release/README.md) to rebuild the ZIP. A fresh clone can also be used for reproduction.

## Environment

Create a fresh Python 3.12 environment and install the pinned requirements:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r paper/direction_a_preprint/environment/requirements-lock.txt
```

Use `OPENBLAS_NUM_THREADS=1` for reproducible resource use and to avoid oversubscribing numerical worker processes. The identity-derived NumPy streams do not depend on worker order or Python's hash randomization.

## Inspect retained results

`results/main/r*p*t*a*.csv.gz` holds all 276,480 final primary frame estimates. Each matching JSON file holds scene coordinates, direct/early-reflection descriptors, realized decay, configuration hashes, source/noise identities and SHA-256 hashes. `configs/main_protocol.json` is the amended protocol frozen before v2 generation. Analysis outputs retain every fixed scene and the conditional bootstrap summaries. No raw microphone recording is needed.

```sh
OPENBLAS_NUM_THREADS=1 .venv/bin/python -m validation.direction_a.analysis
OPENBLAS_NUM_THREADS=1 .venv/bin/python -m validation.direction_a.figures
```

These commands recompute the statistics and figures from retained frame results. They do not rerun propagation or create new experimental observations.

## Representative reproduction

```sh
OPENBLAS_NUM_THREADS=1 .venv/bin/python -m validation.direction_a.reproduce --references
```

This runs nine meaningful direct/room/SRP tests, the full direct-path reference sweep, the joint final response-duration refinement, the independent final room reference, three complete main scenes totaling 8,640 primary estimates, the complete result audit/statistics, and all main figures. The three scenes include all short-record SNRs, all attribution variants, and both training/held-out long recordings. Main numerical outputs must agree within 1e-9 degrees, with identical nonnumeric identities; the six main PNG figures must match exactly. The report explicitly labels this a representative rerun, not a second complete revised campaign. PDF creation timestamps are not used for equality.

Run this in a fresh extracted copy if you want to preserve the packaged reference logs and generated figures unchanged. The command writes its report in `reproduction/clean_environment_report.json`. It uses temporary destinations for newly simulated main scenes. Optional response caches are not distributed; they are regenerated as needed. The archived v1 response builder supports the pruning regression check when the older cache is absent.

## Repeat the full revised campaign

The campaign safely reuses existing scene files only when their protocol and content hashes match. To force a full rerun, use another extracted copy and move its `results/main`, `results/sensitivity`, `results/analysis`, and optional `cache` directories aside. Preserve the protocol and source files.

```sh
OPENBLAS_NUM_THREADS=1 .venv/bin/python -m validation.direction_a.campaign --workers 3
OPENBLAS_NUM_THREADS=1 .venv/bin/python -m validation.direction_a.sensitivity
OPENBLAS_NUM_THREADS=1 .venv/bin/python -m validation.direction_a.analysis
OPENBLAS_NUM_THREADS=1 .venv/bin/python -m validation.direction_a.precision
OPENBLAS_NUM_THREADS=1 .venv/bin/python -m validation.direction_a.figures
```

The primary total is 276,480 estimates; the sensitivity output has 38,400 rows including numerical refinements and the matched SRP baseline. Pilot records and reference controls are separate. The code refuses a campaign whose frozen dependency hashes differ. An intentional numerical change therefore requires a documented new protocol revision and fresh affected outputs, not silent reuse.

The original broad room-refinement controls can be repeated with `python -m validation.direction_a.verify_room`. They retain their historical 0.9-second verification configurations; the final v2 support is additionally verified by `joint_refinement` and `verify_revision`. The pilot can be regenerated with `python -m validation.direction_a.pilot` using the disjoint `pilot_v2` namespace.

## Build the documents

The neutral LaTeX manuscripts use standard packages and numbered bibliography citations. Install Tectonic 0.17.0 from its official release, or use a compatible LaTeX/BibTeX toolchain. The exact official source URL and download hash are recorded in `environment/tectonic_source.json`; the executable and third-party package binaries are not redistributed in the research archive.

From `paper/direction_a_preprint/manuscript/`, run:

```sh
tectonic main.tex
tectonic supplement.tex
```

The source includes the checked data tables and vector figures. Raster copies of the scientific figures are retained; temporary full-page document renders are omitted. Scientific figures come from deterministic plotting code; no generated decorative images or historical forced-accuracy illustration are included in the source/data review archive.

## Interpretation and rights

Bootstrap uncertainty conditions on the chosen scenes and resamples whole records. Frame counts do not establish generality over real rooms. The model excludes microphone mismatch, moving/multiple sources, diffuse scattering, realistic wall frequency responses and hardware limitations. The timing criterion applies to ideal arrival times and a planar solve, not general GCC performance.

No distribution license is assigned yet. Code/data/manuscript licenses and public release remain author decisions. Dependencies are obtained from their upstream sources under their own licenses and are not redistributed. Bibliographic records and reading notes identify literature sources; publisher full texts and private historical recordings are excluded from the release archive.
