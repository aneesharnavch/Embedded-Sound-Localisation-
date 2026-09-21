"""
reverb_robustness.py
====================
Adds the ONE thing that turns a free-field DoA toy into a defensible research
contribution: realistic room reverberation, via the image-source method (ISM).

Free-field localization is considered trivial by acoustics reviewers. The hard,
publishable question is: how does a cheap embedded estimator hold up as a room
gets more reverberant? This script answers that quantitatively -- accuracy vs RT60
(reverberation time) -- for the same three estimators benchmarked in doa_benchmark.py.

Pure NumPy/SciPy (pyroomacoustics won't build on Python 3.14). Reuses the estimators
and source model from doa_benchmark so the comparison is apples-to-apples.
"""

import numpy as np
from scipy.signal import fftconvolve
import matplotlib.pyplot as plt
import doa_benchmark as d


# ----------------------------------------------------------------------------------
# Image-source room model (Allen-Berkley / Habets formulation, uniform wall absorption)
# ----------------------------------------------------------------------------------
def rt60_to_beta(rt60, room):
    """Sabine: convert a target reverberation time to a wall pressure-reflection coeff."""
    Lx, Ly, Lz = room
    V = Lx * Ly * Lz
    S = 2 * (Lx * Ly + Ly * Lz + Lx * Lz)
    alpha = min(0.161 * V / (S * rt60), 0.99)        # absorption coefficient
    return np.sqrt(1.0 - alpha)

def build_rirs(theta_deg, rt60, room=(6.0, 5.0, 3.0), dist=1.5,
               K=12, fs=d.FS, c=d.C, rir_dur=0.8):
    """Room impulse response for each mic, source at azimuth theta_deg, distance `dist`."""
    room = np.array(room, float)
    center = room / 2.0
    u = np.array([np.cos(np.deg2rad(theta_deg)), np.sin(np.deg2rad(theta_deg)), 0.0])
    src = center + dist * u                                       # source in horizontal plane
    mics = np.column_stack([d.MIC_XY, np.zeros(len(d.MIC_XY))]) + center  # (M,3)
    beta = rt60_to_beta(rt60, room)
    n = np.arange(-K, K + 1)
    MX, MY, MZ = np.meshgrid(n, n, n, indexing='ij')             # image-room indices
    rir_len = int(rir_dur * fs)
    rirs = np.zeros((len(mics), rir_len))
    for mi, r in enumerate(mics):
        acc = rirs[mi]
        for px in (0, 1):
            for py in (0, 1):
                for pz in (0, 1):
                    ix = (1 - 2 * px) * src[0] + 2 * MX * room[0]
                    iy = (1 - 2 * py) * src[1] + 2 * MY * room[1]
                    iz = (1 - 2 * pz) * src[2] + 2 * MZ * room[2]
                    dd = np.sqrt((ix - r[0])**2 + (iy - r[1])**2 + (iz - r[2])**2)
                    expo = (np.abs(MX - px) + np.abs(MX) + np.abs(MY - py)
                            + np.abs(MY) + np.abs(MZ - pz) + np.abs(MZ))
                    atten = (beta ** expo) / (4 * np.pi * dd + 1e-9)
                    taps = np.round(dd / c * fs).astype(int)
                    ok = taps < rir_len
                    np.add.at(acc, taps[ok], atten[ok])
    return rirs

def simulate_reverb(rirs, snr_db, kind="speechlike", n=d.SIG_LEN, acq_band=None):
    """Convolve a source through the room RIRs and add noise to the target SNR.

    `acq_band` models the acquisition chain (anti-alias filter + transducer roll-off) and
    is applied to signal+noise together, exactly as in doa_benchmark.simulate(). None
    reproduces the original white-noise-to-Nyquist model.
    """
    s = d.source_signal(kind, n=n)
    s = s / np.sqrt(np.mean(s**2) + 1e-12)
    mics = np.stack([fftconvolve(s, rirs[m])[:n] for m in range(rirs.shape[0])])
    sig_pow = np.mean(mics**2)
    noise = d.RNG.standard_normal(mics.shape) * np.sqrt(sig_pow / 10**(snr_db / 10))
    return d.bandlimit(mics + noise, acq_band)


# ----------------------------------------------------------------------------------
# Experiment: accuracy vs reverberation time
# ----------------------------------------------------------------------------------
def run_rt60_sweep(rt60s, angles, snr=15, trials=60, acq_band=None, band=d.PHAT_BAND):
    """Median / p90 / RMSE with standard errors, for all four estimators, versus RT60.

    Trials were raised from 12 to 60 per (RT60, angle) at the 2026-07-27 re-baseline:
    12 trials x 9 angles gave a relative RMSE standard error near 11 %, which cannot
    separate adjacent RT60 points. All returned quantities carry a standard error.
    """
    methods = {"Proposed (gated)": lambda X: d.est_proposed(X, band=band),
               "GCC-PHAT (cheap)": lambda X: d.est_gccphat_ls(X, band=band),
               "SRP-PHAT (strong)": lambda X: d.est_srp_phat(X, band=band)[0],
               "MUSIC (subspace)": d.est_music}
    raw = {m: [] for m in methods}                    # per-RT60 arrays of |error|
    # Offset the truth off the 1 deg SRP/MUSIC search grid (doa_benchmark.tiled_offsets).
    # Tiled per AZIMUTH, not per trial, because the RIR must stay fixed within an azimuth
    # for the reverberation bias to be a fixed bias rather than averaged away.
    off = d.tiled_offsets(len(angles))
    for rt in rt60s:
        errs = {m: [] for m in methods}
        for ai, th0 in enumerate(angles):
            th = th0 + off[ai]
            rirs = build_rirs(th, rt)                 # RIR depends on (angle, RT60), not trial
            for _ in range(trials):
                X = simulate_reverb(rirs, snr, acq_band=acq_band)
                for m, fn in methods.items():
                    errs[m].append(abs(d.ang_err(fn(X), th)))
        for m in methods:
            raw[m].append(np.array(errs[m]))
        print(f"  RT60 {rt:.2f}s done ({len(angles)*trials} frames per method)",
              flush=True)
    return methods, raw

def _stat(raw, fn):
    return np.array([fn(e) for e in raw])

def fig_accuracy_vs_rt60(rt60s, methods, raw, snr):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(6.8, 2.8), sharex=True)
    for k, m in enumerate(methods):
        med = _stat(raw[m], lambda e: d.quantile_se(e, 0.5)[0])
        mse = _stat(raw[m], lambda e: d.quantile_se(e, 0.5)[1])
        rms = _stat(raw[m], lambda e: d.rmse_se(e)[0])
        rse = _stat(raw[m], lambda e: d.rmse_se(e)[1])
        ax1.errorbar(rt60s, med, yerr=mse, capsize=2, label=m, **d._style(k))
        ax2.errorbar(rt60s, rms, yerr=rse, capsize=2, label=m, **d._style(k))
    for ax, lab, tag, yt in ((ax1, "Median |azimuth error| (deg)", "(a)",
                              [0.1, 0.2, 0.5, 1, 2, 4]),
                             (ax2, "Azimuth RMSE (deg)", "(b)",
                              [3, 4, 5, 10, 20, 40])):
        ax.axvspan(0.2, 0.5, alpha=0.10, color='0.6', lw=0)
        ax.set_xlabel("Reverberation time RT60 (s)")
        ax.set_ylabel(lab); ax.set_yscale('log')
        d.plain_ticks(ax, 'y', yt)
        ax.annotate(tag, (0.02, 0.95), xycoords='axes fraction', fontsize=8, va='top')
    ax1.legend(fontsize=6.5, loc='lower right')
    fig.tight_layout()
    fig.savefig(f"{d.OUTDIR}/fig_accuracy_vs_rt60.png", dpi=d.DPI)
    plt.close(fig)


if __name__ == "__main__":
    rt60s = [0.05, 0.1, 0.2, 0.3, 0.45, 0.6, 0.8]
    angles = list(range(-120, 121, 30))               # 9 angles
    SNR = 15
    TRIALS = 60
    print("reverb_robustness.py  --  RE-BASELINED reverberation sweep")
    print(f"  PHAT weighting band : {d.PHAT_BAND} Hz")
    print(f"  room 6.0 x 5.0 x 3.0 m, source at 1.5 m, image order K=12")
    print(f"  SNR {SNR} dB, {len(angles)} angles, {TRIALS} trials per (RT60, angle), "
          f"seed {d.SEED}")
    print("Sweeping reverberation time (image-source room sim)...")
    d.reseed(20)
    methods, raw = run_rt60_sweep(rt60s, angles, snr=SNR, trials=TRIALS)
    fig_accuracy_vs_rt60(rt60s, methods, raw, SNR)

    bs = np.random.default_rng([d.SEED, 4243])
    print(f"\n==== ACCURACY vs RT60 @ {SNR} dB SNR "
          f"(abs azimuth error, deg; +- = standard error) ====")
    print(f"     n = {len(angles)*TRIALS} frames per (method, RT60) cell")
    for m in methods:
        for rt, e in zip(rt60s, raw[m]):
            print("  " + d.fmt_summary(f"{m:<20} RT60 {rt:4.2f} s:", e, rng=bs))
    print(f"\nFigure written to: {d.OUTDIR}/fig_accuracy_vs_rt60.png")
