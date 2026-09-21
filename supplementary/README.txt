SUPPLEMENTARY FILES

Supplementary_Material.pdf
Four-page explanation of the methods, numerical checks, results and limitations.

validation/direction_a
Python code used for simulation, verification, analysis and figure generation.

paper/direction_a_preprint/configs
Frozen estimator and final v2 simulation settings.

paper/direction_a_preprint/results
Final v2 frame-level results, summaries and numerical checks.

paper/direction_a_preprint/environment/requirements-lock.txt
Exact Python package versions used by the project.

To recalculate the analysis and figures from the retained results, run these commands from this supplementary folder after installing the requirements:

python3.12 -m venv .venv
.venv/bin/python -m pip install -r paper/direction_a_preprint/environment/requirements-lock.txt
OPENBLAS_NUM_THREADS=1 .venv/bin/python -m validation.direction_a.analysis
OPENBLAS_NUM_THREADS=1 .venv/bin/python -m validation.direction_a.figures

No raw microphone recordings are required because the reported study is synthetic.
