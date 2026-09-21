# Archived pre-re-baseline simulation outputs

These files are the outputs of the simulation harness **before** the 2026-07-27
re-baseline. They are kept so that every number that changed in the paper can be traced.
**Do not cite any number from these files.** Their replacements are listed below.

The defect: `doa_benchmark.gcc_phat` applied the PHAT weight over the full 0-24 kHz band
while the simulated source occupies only 300-3400 Hz. PHAT normalises every bin to unit
magnitude, so bins containing nothing but noise had their essentially random phase
promoted to full influence. See `paper/rebaseline_results.md` for the verification, the
decomposition of how much of the correction is a genuine estimator improvement and how
much was an artefact of the simulation's full-band noise model, and the full
before/after table.

| archived file | produced by | superseded by |
|---|---|---|
| `benchmark_run_FULLBAND_PHAT_pre_rebaseline.log` | `doa_benchmark.py` (full-band PHAT, 30 trials) | `../benchmark_run.log` |
| `ablation_run_FULLBAND_PHAT_pre_rebaseline.log` | `ablation.py` (full-band PHAT, 12/25/8/6 trials, T <= 32) | `../ablation_run.log` |
| (none existed) | `reverb_robustness.py` was never logged | `../reverb_run.log` |
| `../figs_archive_prerebaseline/*.png` | the same runs | `../figs/*.png` |

The archived logs are UTF-16 (they were captured by a PowerShell redirect). The
replacements are UTF-8.
