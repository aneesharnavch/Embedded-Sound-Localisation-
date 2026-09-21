"""
verify_sims.py
==============
Re-runs the three existing simulation experiments with the SAME parameters, the SAME
estimators and the SAME fixed seed as the runs recorded in `benchmark_run.log` and
`ablation_run.log`, and reports any discrepancy against those logs.

It does not touch the existing logs or the existing figures. New figures go to
`validation/figs_verify/` and the transcript goes to `validation/sim_verify_run.log`.

Reproduction notes
------------------
`doa_benchmark.RNG` is a module-level generator seeded with 7 at import. The original
numbers came from three SEPARATE processes, each of which therefore started from a fresh
seed-7 stream. To reproduce them here the generator is re-seeded before each experiment
block and the calls inside each block are issued in the original `__main__` order, so the
random stream is consumed identically.

Run:  py -3.14 verify_sims.py
"""

from __future__ import annotations

import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import realdata_common as rc            # noqa: E402
import doa_benchmark as d               # noqa: E402
import reverb_robustness as rr          # noqa: E402
import ablation as ab                   # noqa: E402

VERIFY_FIGDIR = os.path.join(HERE, "figs_verify")
os.makedirs(VERIFY_FIGDIR, exist_ok=True)
d.OUTDIR = VERIFY_FIGDIR                # protect the existing published figures

LOG = os.path.join(HERE, "sim_verify_run.log")

# Reference values transcribed from the existing logs (see HANDOVER.md section 3).
REF_BENCH = {                            # method -> {snr: (median, p90, rmse)}
    "Proposed (gated)":  {0: (3.43, 8.08, 5.02), 5: (3.14, 7.66, 4.69), 10: (2.88, 7.02, 4.32),
                          20: (1.67, 4.61, 7.23), 40: (0.34, 2.28, 1.95)},
    "GCC-PHAT (cheap)":  {0: (3.45, 8.07, 4.93), 5: (3.09, 7.41, 4.60), 10: (2.82, 6.89, 4.23),
                          20: (1.67, 4.28, 7.14), 40: (0.35, 2.21, 1.74)},
    "SRP-PHAT (strong)": {0: (4.00, 11.00, 6.66), 5: (4.00, 10.00, 6.12), 10: (4.00, 9.00, 5.60),
                          20: (2.00, 5.00, 3.21), 40: (0.00, 3.00, 2.32)},
    "MUSIC (subspace)":  {0: (1.00, 3.00, 12.93), 5: (1.00, 2.00, 6.00), 10: (0.00, 1.00, 0.81),
                          20: (0.00, 0.00, 0.13), 40: (0.00, 0.00, 0.00)},
}
REF_COMPUTE_MS = {"Proposed (gated)": 1.353, "GCC-PHAT (cheap)": 1.289,
                  "SRP-PHAT (strong)": 5.494, "MUSIC (subspace)": 5.459}
REF_ABLATION = {                         # variant -> medians over rt60s
    "Proposed (gate+weight)": [2.3, 2.7, 4.4, 4.7, 5.3, 4.7],
    "Weight only (no gate)":  [2.3, 2.7, 4.4, 4.7, 5.3, 4.5],
    "Gate only (no weight)":  [2.2, 2.7, 4.3, 4.8, 5.9, 5.0],
    "Neither (= GCC-PHAT)":   [2.2, 2.7, 4.3, 4.8, 5.9, 5.0],
}
REF_TEMPORAL = {
    "free (w)":  [3.88, 2.90, 2.20, 1.33, 0.96, 0.68],
    "free (u)":  [4.10, 2.92, 2.07, 1.38, 0.99, 0.75],
    "RT60 0.15": [4.70, 4.28, 2.91, 2.77, 2.36, 2.14],
    "RT60 0.3":  [8.13, 4.29, 3.58, 3.11, 2.74, 2.00],
    "RT60 0.6":  [7.04, 6.66, 5.92, 4.23, 3.75, 2.60],
}
REF_APERTURE = [7.31, 4.63, 2.95, 1.65, 1.10]
REF_SNAPSHOT = [4.27, 3.40, 3.06, 2.72, 2.40]


def cmp_row(label, new, ref, tol_abs=0.05, tol_rel=0.02):
    """Print a comparison line; return True if within tolerance."""
    if ref is None:
        print(f"  {label:<44} new={new:8.3f}   (no logged reference)")
        return True
    delta = new - ref
    ok = abs(delta) <= max(tol_abs, tol_rel * abs(ref))
    flag = "OK " if ok else "DIFF"
    print(f"  {label:<44} logged={ref:8.3f}  new={new:8.3f}  delta={delta:+8.3f}  [{flag}]")
    return ok


def main():
    tee = rc.Tee(LOG)
    sys.stdout = tee
    t_start = time.time()
    discrepancies = []

    print("verify_sims.py -- re-run of the logged simulation experiments")
    print(f"numpy {np.__version__}   seed {d.RNG.__class__.__name__}(7)")
    print(f"array geometry (cm):\n{np.round(d.MIC_XY * 100, 2)}")
    print(f"fs = {d.FS} Hz, snapshot = {d.SIG_LEN} samples "
          f"({1e3 * d.SIG_LEN / d.FS:.1f} ms)")
    print(f"figures -> {VERIFY_FIGDIR}  (the published figs/ directory is untouched)")

    # ------------------------------------------------------------------ benchmark
    rc.rule("1. doa_benchmark.py  (reference: benchmark_run.log)")
    d.RNG = np.random.default_rng(rc.SEED)
    angles = list(range(-150, 151, 15))
    snrs = [0, 5, 10, 20, 40]
    d.fig_geometry()
    d.fig_srp_example()
    times = d.measure_compute()
    methods, errs = d.run_sweeps(angles, snrs, trials=30)
    d.fig_cdf(methods, errs, snrs, snr_pick=10)
    d.fig_rmse_vs_snr(methods, errs, snrs)
    d.fig_heatmap(errs, snrs, angles)
    d.fig_pareto(methods, errs, snrs, times, snr_pick=10)

    print("\n  accuracy (median / p90 / RMSE in degrees)")
    for m in methods:
        for si, snr in enumerate(snrs):
            e = errs[m][si].ravel()
            got = (float(np.median(e)), float(np.percentile(e, 90)),
                   float(np.sqrt(np.mean(e ** 2))))
            ref = REF_BENCH[m][snr]
            for k, tag in enumerate(("median", "p90", "RMSE")):
                if not cmp_row(f"{m} @{snr:>2} dB {tag}", got[k], ref[k]):
                    discrepancies.append(f"benchmark {m} @{snr} dB {tag}")
    print("\n  compute per estimate (ms, x86; only the ratios transfer to the MCU)")
    for m, t in times.items():
        cmp_row(f"{m} compute", t, REF_COMPUTE_MS[m], tol_abs=1e9)   # report, never fail
    base = min(times.values())
    for m, t in times.items():
        print(f"    ratio {m:<24} {t / base:6.2f}x cheapest")

    # ------------------------------------------------------------------ reverberation
    rc.rule("2. reverb_robustness.py  (no numeric log exists; recording fresh values)")
    d.RNG = np.random.default_rng(rc.SEED)
    rt60s = [0.05, 0.1, 0.2, 0.3, 0.45, 0.6, 0.8]
    rmethods, rmed, rp90 = rr.run_rt60_sweep(rt60s, list(range(-120, 121, 30)),
                                             snr=15, trials=12)
    rr.fig_accuracy_vs_rt60(rt60s, rmethods, rmed, 15)
    print("\n  median |error| (deg) vs RT60 @ 15 dB SNR")
    print("    RT60(s)  " + "  ".join(f"{r:>5.2f}" for r in rt60s))
    for m in rmethods:
        print(f"    {m:<20} " + "  ".join(f"{v:>5.2f}" for v in rmed[m]))
    print("  p90 |error| (deg) vs RT60")
    for m in rmethods:
        print(f"    {m:<20} " + "  ".join(f"{v:>5.2f}" for v in rp90[m]))

    # ------------------------------------------------------------------ ablation
    rc.rule("3. ablation.py  (reference: ablation_run.log)")
    d.RNG = np.random.default_rng(rc.SEED)
    SNR = 10
    art60s = [0.05, 0.15, 0.3, 0.45, 0.6, 0.8]
    med = ab.ablation_vs_rt60(art60s, list(range(-120, 121, 30)), snr=SNR)
    ab.fig_ablation(art60s, med, SNR)

    Ts = np.array([1, 2, 4, 8, 16, 32])
    tang = list(range(-150, 151, 30))
    ff_w = ab.temporal_freefield(Ts, tang, SNR, weighted=True)
    ff_u = ab.temporal_freefield(Ts, tang, SNR, weighted=False)
    rev = {rt: ab.temporal_reverb(Ts, list(range(-120, 121, 40)), rt, SNR)
           for rt in (0.15, 0.3, 0.6)}
    ab.fig_temporal(Ts, ff_w, ff_u, rev, SNR)

    radii = [0.02, 0.03, 0.05, 0.08, 0.12]
    med_ap, p90_ap = ab.scaling_vs_aperture(radii, list(range(-150, 151, 30)), snr=SNR)
    snaplens = [256, 512, 1024, 2048, 4096]
    med_sl = ab.scaling_vs_snaplen(snaplens, list(range(-150, 151, 30)), snr=SNR)
    ab.fig_scaling(radii, med_ap, p90_ap, snaplens, med_sl, SNR)

    print("\n  ablation: median |error| (deg) vs RT60")
    for v, refs in REF_ABLATION.items():
        for i, rt in enumerate(art60s):
            if not cmp_row(f"{v} @RT60 {rt}", med[v][i], refs[i], tol_abs=0.15):
                discrepancies.append(f"ablation {v} @RT60 {rt}")
    print("\n  temporal accumulation: RMSE (deg) vs T")
    curves = {"free (w)": ff_w, "free (u)": ff_u,
              "RT60 0.15": rev[0.15], "RT60 0.3": rev[0.3], "RT60 0.6": rev[0.6]}
    for key, cur in curves.items():
        for i, T in enumerate(Ts):
            if not cmp_row(f"{key} T={T}", float(cur[i]), REF_TEMPORAL[key][i],
                           tol_abs=0.10, tol_rel=0.03):
                discrepancies.append(f"temporal {key} T={T}")
    print("\n  aperture scaling: median |error| (deg)")
    for i, R in enumerate(radii):
        if not cmp_row(f"aperture R={R * 100:.0f} cm", float(med_ap[i]), REF_APERTURE[i]):
            discrepancies.append(f"aperture R={R * 100:.0f} cm")
    print("\n  snapshot scaling: median |error| (deg)")
    for i, N in enumerate(snaplens):
        if not cmp_row(f"snapshot N={N} ({1e3 * N / d.FS:.0f} ms)",
                       float(med_sl[i]), REF_SNAPSHOT[i]):
            discrepancies.append(f"snapshot N={N}")

    # ------------------------------------------------------------------ verdict
    rc.rule("VERDICT")
    if discrepancies:
        print(f"{len(discrepancies)} value(s) outside tolerance:")
        for x in discrepancies:
            print(f"  - {x}")
        print("\nThe logged numbers were NOT reproduced exactly. Investigate before citing.")
    else:
        print("All logged simulation numbers reproduced within tolerance.")
        print("benchmark_run.log and ablation_run.log remain citable as printed.")
    print(f"\nelapsed {time.time() - t_start:.1f} s")
    print(f"verification figures written to {VERIFY_FIGDIR}")

    sys.stdout = tee.stdout
    tee.close()
    print(f"log -> {LOG}")


if __name__ == "__main__":
    main()
