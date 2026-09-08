"""
ablation.py
===========
The "does each part earn its keep, and how cheap can we go" study -- the part of the
paper that turns a platform demo into a research finding. Three experiments, all reusing
the exact estimators and room model from doa_benchmark / reverb_robustness so every number
is apples-to-apples with the rest of the paper:

  1. ABLATION: the proposed estimator with its two decision components toggled on/off
     (feasibility GATE, PSR WEIGHTing), swept over reverberation time. With both off it is
     identically GCC-PHAT, so this isolates exactly what the refinement layer buys. All
     four variants see the SAME snapshots, so the comparison is PAIRED and the difference
     between variants is reported with its own standard error.

  2. RESOURCE SCALING: how localization accuracy degrades as the physical array shrinks
     (aperture radius) and as the snapshot gets shorter -- i.e. how cheap/small a build can
     still hit a target accuracy.

  3. TEMPORAL ACCUMULATION: the core mechanism. RMSE versus number of accumulated frames
     T, in free field and in three reverberant rooms, with and without confidence
     weighting, out to T = 128.

RE-BASELINE CHANGES (2026-07-27)
--------------------------------
  * The GCC-PHAT front end is now band-limited (doa_benchmark.PHAT_BAND). Every number
    produced here supersedes validation/archive/ablation_run_FULLBAND_PHAT_*.log.
  * Trial counts raised: RT60 sweeps 12 -> 60, scaling 25 -> 60, accumulation 8/6 -> 30.
  * The accumulation sweep is extended from T <= 32 to T = 128, past the predicted
    futility knee at T ~ 65-108 (math_model.md M67), so the bias floor can be established
    from the accumulation curves themselves rather than only from a direct measurement.
  * The reverberant accumulation sweep is now run WITHOUT confidence weighting as well as
    with it. Previously only weighted=True had ever been run, so the claim that weighting
    beats a plain circular mean in reverberation was unsupported.
  * Weighted and plain accumulation are evaluated on the SAME per-frame estimates, so
    that comparison is paired and its standard error is the standard error of a
    difference, not of two independent means.
  * Every reported number carries a standard error.

Run:  py -3.14 ablation.py
"""

import numpy as np
import matplotlib.pyplot as plt
import doa_benchmark as d
import reverb_robustness as rr


# ----------------------------------------------------------------------------------
# Experiment 1: ablation of the two decision components vs reverberation
# ----------------------------------------------------------------------------------
VARIANTS = {
    "Proposed (gate+weight)": lambda X: d.est_proposed(X, gate=True,  weight=True),
    "Weight only (no gate)":  lambda X: d.est_proposed(X, gate=False, weight=True),
    "Gate only (no weight)":  lambda X: d.est_proposed(X, gate=True,  weight=False),
    "Neither (= GCC-PHAT)":   lambda X: d.est_proposed(X, gate=False, weight=False),
}
REF_VARIANT = "Neither (= GCC-PHAT)"

def ablation_vs_rt60(rt60s, angles, snr=10, trials=60, acq_band=None):
    """Returns raw[variant][i] = array of |error| over all (angle, trial) at rt60s[i].

    All variants are evaluated on the identical snapshot, so raw[v][i][k] and
    raw[v'][i][k] are a matched pair and their difference can be tested directly.
    """
    raw = {v: [] for v in VARIANTS}
    off = d.tiled_offsets(len(angles))     # keep the truth off the correlation lag grid
    for rt in rt60s:
        errs = {v: [] for v in VARIANTS}
        for ai, th0 in enumerate(angles):
            th = th0 + off[ai]
            rirs = rr.build_rirs(th, rt)                    # room depends on (angle, RT60)
            for _ in range(trials):
                X = rr.simulate_reverb(rirs, snr, acq_band=acq_band)
                for v, fn in VARIANTS.items():
                    errs[v].append(abs(d.ang_err(fn(X), th)))
        for v in VARIANTS:
            raw[v].append(np.array(errs[v]))
        print(f"  RT60 {rt:.2f}s done ({len(angles)*trials} frames per variant)",
              flush=True)
    return raw

def paired_delta(a, b):
    """Mean of (|e_a| - |e_b|) over matched frames, with its standard error.

    This is the statistic that answers "is the decision layer doing anything?". Because
    the two variants share the snapshot, the between-frame variance cancels and the test
    is far more sensitive than comparing two independently estimated medians.
    """
    dv = np.asarray(a, float) - np.asarray(b, float)
    n = dv.size
    return float(dv.mean()), float(dv.std(ddof=1) / np.sqrt(n)), n

def fig_ablation(rt60s, raw, snr):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(6.8, 2.8))
    for k, v in enumerate(VARIANTS):
        med = np.array([d.quantile_se(e, 0.5)[0] for e in raw[v]])
        mse = np.array([d.quantile_se(e, 0.5)[1] for e in raw[v]])
        ax1.errorbar(rt60s, med, yerr=mse, capsize=2, label=v, **d._style(k))
    ax1.set_xlabel("Reverberation time RT60 (s)")
    ax1.set_ylabel("Median |azimuth error| (deg)")
    ax1.legend(fontsize=6.0, loc='lower right')
    ax1.annotate("(a) all four variants, same snapshots", (0.03, 0.96),
                 xycoords='axes fraction', fontsize=6.5, va='top')

    short = {"Proposed (gate+weight)": "gate + weight",
             "Weight only (no gate)": "weight only",
             "Gate only (no weight)": "gate only"}
    for k, v in enumerate(VARIANTS):
        if v == REF_VARIANT:
            continue
        dm = [paired_delta(raw[v][i], raw[REF_VARIANT][i]) for i in range(len(rt60s))]
        ax2.errorbar(rt60s, [x[0] for x in dm], yerr=[x[1] for x in dm], capsize=2,
                     label=short[v], **d._style(k))
    ax2.axhline(0, color='k', lw=0.8, marker='', ls='-')
    ax2.set_xlabel("Reverberation time RT60 (s)")
    ax2.set_ylabel("Paired mean $\\Delta$|azimuth error| (deg)")
    ax2.set_ylim(-0.135, 0.02)
    ax2.legend(fontsize=6.0, loc='lower right', title="minus plain GCC-PHAT",
               title_fontsize=6.0)
    ax2.annotate("(b) note the vertical scale: the decision layer is\n"
                 "     worth 0.02 to 0.09 deg against an error of\n"
                 "     2.5 to 3.2 deg",
                 (0.03, 0.20), xycoords='axes fraction', fontsize=6.5, va='top')
    fig.tight_layout()
    fig.savefig(f"{d.OUTDIR}/fig_ablation_rt60.png", dpi=d.DPI)
    plt.close(fig)


# ----------------------------------------------------------------------------------
# Experiment 1b: isotropy of the azimuth variance (math_model.md M39)
# ----------------------------------------------------------------------------------
def isotropy_check(angles, snr=10, trials=200):
    """Per-azimuth error dispersion under uniform weights, PSR weights, and pair-dropping.

    (M39) predicts the azimuth variance of an equilateral 3-mic array is direction
    independent under UNIFORM weights, and that direction dependence appears only when
    the isotropy of A^T A is broken by weighting or by dropping a pair. That is a second,
    independent argument against gating, so it is worth testing explicitly.

    Returns {config: (per-angle sigma, per-angle standard error of sigma)} in degrees.
    """
    cfgs = {
        "uniform weights (3 pairs)": lambda X: d.est_proposed(X, gate=False, weight=False),
        "PSR weights (3 pairs)":     lambda X: d.est_proposed(X, gate=False, weight=True),
        "drop pair 1-2 (2 pairs)":   lambda X: _est_drop(X, 0),
        "drop pair 1-3 (2 pairs)":   lambda X: _est_drop(X, 1),
    }
    out = {c: (np.zeros(len(angles)), np.zeros(len(angles))) for c in cfgs}
    off = d.tiled_offsets(trials)
    for ai, th0 in enumerate(angles):
        errs = {c: [] for c in cfgs}
        for t in range(trials):
            th = th0 + off[t]
            X = d.simulate(th, snr)
            for c, fn in cfgs.items():
                errs[c].append(d.ang_err(fn(X), th))
        for c in cfgs:
            e = np.array(errs[c])
            s = float(np.median(np.abs(e - np.median(e))) / 0.6745)   # robust sigma
            out[c][0][ai] = s
            # Standard error of a MAD-based scale estimate. The MAD has asymptotic
            # relative efficiency 0.37 against the sample s.d. under normality, so its
            # standard error is s / sqrt(2 * 0.37 * n) = 1.166 s / sqrt(n) -- about 1.65x
            # the normal-theory s / sqrt(2(n-1)). Using the wrong one here would inflate
            # every chi-square below by a factor 2.7 and manufacture direction dependence
            # that is not there.
            out[c][1][ai] = 1.166 * s / np.sqrt(trials)
    return out

def isotropy_prediction(angles, drop=None, mic_xy=d.MIC_XY):
    """Relative azimuth s.d. versus azimuth predicted by (M36), normalised to its mean.

    sigma_theta(theta)^2 = c^2 sigma_tau^2 * e_theta^T (A^T W A)^{-1} e_theta.
    With all three pairs and uniform weights, A^T A = 4.5 R^2 I (M34) and the curve is
    flat. Dropping a pair leaves a 2x2 A whose Gram matrix is not isotropic, and the
    predicted curve below is what the measurement should follow if (M36) is right.
    """
    rows = []
    M = len(mic_xy)
    for i in range(M):
        for j in range(i + 1, M):
            rows.append(mic_xy[i] - mic_xy[j])
    A = np.array(rows)
    if drop is not None:
        A = A[[k for k in range(3) if k != drop]]
    G = np.linalg.inv(A.T @ A)
    th = np.deg2rad(np.asarray(angles, float))
    e = np.stack([-np.sin(th), np.cos(th)])                    # (2, n) tangential
    var = np.einsum('in,ij,jn->n', e, G, e)
    s = np.sqrt(var)
    return s / s.mean()

def isotropy_level(drop=None, mic_xy=d.MIC_XY, n=1440):
    """Azimuth-averaged sqrt(e_th^T (A^T A)^-1 e_th), un-normalised.

    isotropy_prediction() gives the SHAPE; this gives the LEVEL, so the predicted variance
    inflation from dropping a pair can be compared with the measured one.
    """
    rows = []
    M = len(mic_xy)
    for i in range(M):
        for j in range(i + 1, M):
            rows.append(mic_xy[i] - mic_xy[j])
    A = np.array(rows)
    if drop is not None:
        A = A[[k for k in range(3) if k != drop]]
    G = np.linalg.inv(A.T @ A)
    th = np.linspace(0, 2 * np.pi, n, endpoint=False)
    e = np.stack([-np.sin(th), np.cos(th)])
    return float(np.sqrt(np.einsum('in,ij,jn->n', e, G, e)).mean())

def _est_drop(X, drop_idx, mic_xy=d.MIC_XY, fs=d.FS):
    """Least-squares azimuth from only two of the three pairs."""
    M = X.shape[0]
    rows, taus = [], []
    for i in range(M):
        for j in range(i + 1, M):
            rows.append(mic_xy[i] - mic_xy[j])
            taus.append(d.tdoa_phat(X[i], X[j], fs))
    keep = [k for k in range(3) if k != drop_idx]
    A = np.array(rows)[keep]
    b = -d.C * np.array(taus)[keep]
    u, *_ = np.linalg.lstsq(A, b, rcond=None)
    return np.rad2deg(np.arctan2(u[1], u[0]))

ISO_DROP = {"uniform weights (3 pairs)": None, "PSR weights (3 pairs)": None,
            "drop pair 1-2 (2 pairs)": 0, "drop pair 1-3 (2 pairs)": 1}

def fig_isotropy(angles, iso):
    groups = [("(a) all three pairs",
               ["uniform weights (3 pairs)", "PSR weights (3 pairs)"]),
              ("(b) one pair dropped",
               ["drop pair 1-2 (2 pairs)", "drop pair 1-3 (2 pairs)"])]
    fig, axes = plt.subplots(1, 2, figsize=(6.8, 2.8), sharey=True)
    for ax, (tag, keys) in zip(axes, groups):
        for k, c in enumerate(keys):
            s, se = iso[c]
            ax.errorbar(angles, s / s.mean(), yerr=se / s.mean(), capsize=2, label=c,
                        **d._style(k))
            if ISO_DROP[c] is not None:
                ax.plot(angles, isotropy_prediction(angles, ISO_DROP[c]),
                        color=d.CB[k % len(d.CB)], ls=(0, (1, 1)), marker='', lw=1.1,
                        alpha=0.9)
        ax.axhline(1.0, color='k', lw=0.8, ls='-', marker='')
        ax.set_xlabel("True azimuth (deg)")
        ax.set_xlim(-180, 180); ax.set_xticks([-180, -90, 0, 90, 180])
        ax.legend(fontsize=6.0, loc='lower center')
        ax.annotate(tag, (0.03, 0.96), xycoords='axes fraction', fontsize=7, va='top')
    axes[0].set_ylabel("Azimuth error s.d.\n(normalised to its own mean)")
    axes[1].annotate("dotted: (M36) with Cov$(\\tau)=\\sigma_\\tau^2 I$",
                     (0.03, 0.87), xycoords='axes fraction', fontsize=6.5, va='top')
    fig.tight_layout(); fig.savefig(f"{d.OUTDIR}/fig_isotropy.png", dpi=d.DPI)
    plt.close(fig)


# ----------------------------------------------------------------------------------
# Experiment 2: resource scaling -- aperture radius and snapshot length (free field)
# ----------------------------------------------------------------------------------
def triangle(radius):
    """Equilateral 3-mic triangle of the given circum-radius (m)."""
    return np.array([[radius * np.cos(np.deg2rad(a)), radius * np.sin(np.deg2rad(a))]
                     for a in (90, 210, 330)])

def scaling_vs_aperture(radii, angles, snr=10, trials=60):
    raw = []
    off = d.tiled_offsets(trials)
    for R in radii:
        mic_xy = triangle(R)
        errs = []
        for th0 in angles:
            for t in range(trials):
                th = th0 + off[t]
                X = d.simulate(th, snr, mic_xy=mic_xy)
                errs.append(abs(d.ang_err(d.est_proposed(X, mic_xy=mic_xy), th)))
        raw.append(np.array(errs))
        print(f"  aperture R={R*100:.0f} cm done", flush=True)
    return raw

def scaling_vs_snaplen(snaplens, angles, snr=10, trials=60):
    raw = []
    off = d.tiled_offsets(trials)
    for N in snaplens:
        errs = []
        for th0 in angles:
            for t in range(trials):
                th = th0 + off[t]
                s = d.source_signal("speechlike", n=N)
                s = s / np.sqrt(np.mean(s**2) + 1e-12)
                taus = d.steering_delays(th)
                clean = np.stack([d.frac_delay(s, t) for t in taus])
                npow = np.mean(clean**2) / 10 ** (snr / 10)
                X = clean + d.RNG.standard_normal(clean.shape) * np.sqrt(npow)
                errs.append(abs(d.ang_err(d.est_proposed(X), th)))
        raw.append(np.array(errs))
        print(f"  snapshot N={N} ({1e3*N/d.FS:.0f} ms) done", flush=True)
    return raw

def loglog_slope(x, y, yerr=None, B=400, seed=11):
    """Log-log slope with a bootstrap standard error (resampling the points)."""
    lx, ly = np.log(np.asarray(x, float)), np.log(np.asarray(y, float))
    slope = float(np.polyfit(lx, ly, 1)[0])
    if yerr is None:
        return slope, float('nan')
    rng = np.random.default_rng([d.SEED, seed])
    rel = np.asarray(yerr, float) / np.asarray(y, float)
    draws = [np.polyfit(lx, ly + rng.standard_normal(len(ly)) * rel, 1)[0]
             for _ in range(B)]
    return slope, float(np.std(draws, ddof=1))

def fig_scaling(radii, ap_raw, snaplens, sl_raw, snr):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(6.8, 2.8))
    med = np.array([d.quantile_se(e, 0.5)[0] for e in ap_raw])
    mse = np.array([d.quantile_se(e, 0.5)[1] for e in ap_raw])
    p90 = np.array([d.quantile_se(e, 0.9)[0] for e in ap_raw])
    p9e = np.array([d.quantile_se(e, 0.9)[1] for e in ap_raw])
    rcm = np.array(radii) * 100
    ax1.errorbar(rcm, med, yerr=mse, capsize=2, label="median", **d._style(0))
    ax1.errorbar(rcm, p90, yerr=p9e, capsize=2, label="90th percentile", **d._style(1))
    ax1.plot(rcm, med[2] * (rcm[2] / rcm), color='k', ls=':', marker='', lw=1.1,
             label=r"$\propto 1/R$ (M40)")
    ax1.set_xlabel("Array circum-radius R (cm)")
    ax1.set_ylabel("|azimuth error| (deg)")
    ax1.set_xscale('log'); ax1.set_yscale('log'); ax1.legend(fontsize=6.5)
    d.plain_ticks(ax1, 'x', list(rcm))
    d.plain_ticks(ax1, 'y', [0.1, 0.2, 0.5, 1.0])
    ax1.annotate("(a)", (0.02, 0.95), xycoords='axes fraction', fontsize=8, va='top')

    smed = np.array([d.quantile_se(e, 0.5)[0] for e in sl_raw])
    smse = np.array([d.quantile_se(e, 0.5)[1] for e in sl_raw])
    ms = 1e3 * np.array(snaplens) / d.FS
    ax2.errorbar(ms, smed, yerr=smse, capsize=2, label="median", **d._style(0))
    ax2.plot(ms, smed[0] * np.sqrt(ms[0] / ms), color='k', ls=':', marker='', lw=1.1,
             label=r"$\propto N^{-1/2}$ (CRB)")
    ax2.set_xlabel("Snapshot length (ms)")
    ax2.set_ylabel("Median |azimuth error| (deg)")
    ax2.set_xscale('log'); ax2.set_yscale('log'); ax2.legend(fontsize=6.5)
    d.plain_ticks(ax2, 'x', [round(v) for v in ms])
    d.plain_ticks(ax2, 'y', [0.15, 0.2, 0.3, 0.4, 0.6])
    ax2.annotate("(b)", (0.02, 0.95), xycoords='axes fraction', fontsize=8, va='top')
    fig.tight_layout()
    fig.savefig(f"{d.OUTDIR}/fig_resource_scaling.png", dpi=d.DPI)
    plt.close(fig)


# ----------------------------------------------------------------------------------
# Experiment 3: temporal accumulation -- the core accuracy mechanism of the method
# ----------------------------------------------------------------------------------
def _blocks(az, conf, T, weighted):
    """Disjoint length-T blocks of one Tmax-frame record, each accumulated.

    Splitting the record into floor(Tmax/T) independent blocks rather than using only its
    first T frames costs nothing and gives Tmax/T times more error samples at small T.
    Blocks are disjoint, so within a record they are independent draws.
    """
    nb = len(az) // T
    return [d.combine_frames(az[k * T:(k + 1) * T], conf[k * T:(k + 1) * T], weighted)
            for k in range(nb)]

def temporal_sweep(make_frame, angles, Ts, trials=30, tmax=128):
    """Accumulation sweep. `make_frame(theta)` returns one (M, N) snapshot.

    Returns
      blocks[(mode, T)] : array of signed azimuth errors, mode in {'w','u'}
      per_angle_bias    : array of circular-mean per-frame error per angle  = b(theta)
      per_angle_sigma   : array of circular s.d. of per-frame error per angle = sigma_1
      n_frames_angle    : frames contributing to each per-angle statistic
    """
    modes = ('w', 'u')
    blocks = {(mo, T): [] for mo in modes for T in Ts}
    bias, sig = [], []
    for th in angles:
        az_all = []
        for _ in range(trials):
            frames = [make_frame(th) for _ in range(tmax)]
            az, conf = d.frame_estimates(frames)
            az_all.append(d.ang_err(az, th))
            for T in Ts:
                blocks[('w', T)].extend(
                    d.ang_err(np.array(_blocks(az, conf, T, True)), th))
                blocks[('u', T)].extend(
                    d.ang_err(np.array(_blocks(az, conf, T, False)), th))
        e = np.deg2rad(np.concatenate(az_all))
        Cb, Sb = np.mean(np.cos(e)), np.mean(np.sin(e))
        Rbar = np.hypot(Cb, Sb)
        bias.append(np.rad2deg(np.arctan2(Sb, Cb)))                 # b(theta)
        sig.append(np.rad2deg(np.sqrt(max(-2.0 * np.log(max(Rbar, 1e-12)), 0.0))))
        print(f"    theta {th:>7.2f} deg: b = {bias[-1]:+6.3f} deg, "
              f"sigma_1 = {sig[-1]:6.3f} deg", flush=True)
    return ({k: np.array(v) for k, v in blocks.items()},
            np.array(bias), np.array(sig), trials * tmax)

def fit_bias_floor(Ts, mse, mse_se):
    """Weighted non-negative least squares of MSE(T) = b^2 + sigma_1^2 / T  (M62).

    Returns (b, se_b, sigma_1, se_sigma_1, rms_residual_in_RMSE_units).
    """
    Ts = np.asarray(Ts, float)
    y = np.asarray(mse, float)
    w = 1.0 / np.maximum(np.asarray(mse_se, float), 1e-12) ** 2
    A = np.column_stack([np.ones_like(Ts), 1.0 / Ts])
    Aw = A * np.sqrt(w)[:, None]
    p, *_ = np.linalg.lstsq(Aw, y * np.sqrt(w), rcond=None)
    cov = np.linalg.inv(Aw.T @ Aw)
    p0 = max(p[0], 0.0)
    b = np.sqrt(p0)
    s1 = np.sqrt(max(p[1], 0.0))
    se_b = np.sqrt(cov[0, 0]) / (2 * b) if b > 1e-9 else np.sqrt(np.sqrt(cov[0, 0]))
    se_s1 = np.sqrt(cov[1, 1]) / (2 * s1) if s1 > 1e-9 else float('nan')
    resid = float(np.sqrt(np.mean((np.sqrt(np.maximum(A @ p, 0)) - np.sqrt(y)) ** 2)))
    return b, se_b, s1, se_s1, resid

def fig_temporal(Ts, ff, rev, snr):
    """ff  = {mode: (rmse, se)}; rev = {rt60: {mode: (rmse, se)}}"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(6.8, 2.9))
    for k, (mo, lab) in enumerate((('w', "confidence-weighted"),
                                   ('u', "plain circular mean"))):
        r, se = ff[mo]
        ax1.errorbar(Ts, r, yerr=se, capsize=2, label=lab, **d._style(k))
    ax1.plot(Ts, ff['w'][0][0] / np.sqrt(np.array(Ts, float)), color='k', ls=':',
             marker='', lw=1.1, label=r"$1/\sqrt{T}$ reference")
    ax1.set_xlabel("Accumulated frames T")
    ax1.set_ylabel("Azimuth RMSE (deg)")
    ax1.set_xscale('log', base=2); ax1.set_yscale('log')
    ax1.legend(fontsize=6.5)
    ax1.annotate("(a) free field", (0.02, 0.06), xycoords='axes fraction', fontsize=7)

    for k, (rt, curves) in enumerate(rev.items()):
        r, se = curves['w']
        ax2.errorbar(Ts, r, yerr=se, capsize=2, label=f"RT60 = {rt:.2f} s",
                     **d._style(k))
        ru, seu = curves['u']
        ax2.plot(Ts, ru, ls=(0, (1, 1)), marker='', lw=1.0,
                 color=d.CB[k % len(d.CB)], alpha=0.9,
                 label="plain circular mean" if k == 0 else None)
    ax2.set_xlabel("Accumulated frames T")
    ax2.set_ylabel("Azimuth RMSE (deg)")
    ax2.set_xscale('log', base=2); ax2.set_yscale('log')
    ax2.set_ylim(1.15, 3.7)
    d.plain_ticks(ax2, 'y', [1.5, 2.0, 2.5, 3.0, 3.5])
    ax2.legend(fontsize=6.5, loc='lower right')
    ax2.annotate("(b) reverberant rooms\n     solid = confidence-weighted",
                 (0.03, 0.14), xycoords='axes fraction', fontsize=6.5, va='top')
    fig.tight_layout()
    fig.savefig(f"{d.OUTDIR}/fig_temporal_accumulation.png", dpi=d.DPI)
    plt.close(fig)

def fig_bias_floor(Ts, ff, rev, floors):
    """RMSE(T) against the fitted b^2 + sigma^2/T law, showing where the floor bites."""
    plt.figure(figsize=(3.4, 2.9))
    curves = [("free field", ff['w'])] + \
             [(f"RT60 {rt:.2f} s", c['w']) for rt, c in rev.items()]
    Tf = np.logspace(0, np.log2(max(Ts)) * np.log10(2), 100, base=10)
    for k, (lab, (r, se)) in enumerate(curves):
        st = d._style(k); st["ls"] = 'none'
        plt.errorbar(Ts, r, yerr=se, capsize=2, label=lab, **st)
        b, _, s1, _, _ = floors[lab]
        plt.plot(Tf, np.sqrt(b ** 2 + s1 ** 2 / Tf), color=d.CB[k % len(d.CB)],
                 ls='-', marker='', lw=1.1)
        if b > 0.05:
            plt.axhline(b, color=d.CB[k % len(d.CB)], ls=(0, (1, 2)), lw=0.8, marker='')
    plt.xlabel("Accumulated frames T"); plt.ylabel("Azimuth RMSE (deg)")
    plt.xscale('log', base=2); plt.yscale('log')
    d.plain_ticks(plt.gca(), 'y', [0.03, 0.1, 0.3, 1.0, 3.0])
    plt.legend(fontsize=6.5, loc='lower left')
    plt.annotate("solid: fitted $\\sqrt{b^2+\\sigma_1^2/T}$ (M62)\n"
                 "dotted: fitted bias floor $b$",
                 (0.52, 0.58), xycoords='axes fraction', fontsize=6.5, va='top')
    plt.tight_layout()
    plt.savefig(f"{d.OUTDIR}/fig_bias_floor.png", dpi=d.DPI)
    plt.close()


def safe_fig(fn, *a, **kw):
    """Never let a plotting error destroy a multi-minute Monte-Carlo run."""
    try:
        fn(*a, **kw)
    except Exception as exc:                                        # noqa: BLE001
        print(f"  WARNING: figure {fn.__name__} failed: {exc!r}", flush=True)

def _curve(blocks, Ts, mode):
    r = np.array([d.rmse_se(blocks[(mode, T)])[0] for T in Ts])
    s = np.array([d.rmse_se(blocks[(mode, T)])[1] for T in Ts])
    return r, s


if __name__ == "__main__":
    SNR = 10
    print("ablation.py  --  RE-BASELINED ablation, scaling and accumulation study")
    print(f"  PHAT weighting band : {d.PHAT_BAND} Hz")
    print(f"  seed {d.SEED}; reseed tags: 30 ablation, 31 isotropy, 32 aperture,")
    print("  33 snapshot, 34 free-field accumulation, 35/36/37 reverberant accumulation")
    bs = np.random.default_rng([d.SEED, 4244])

    # ---------------- Experiment 1: ablation vs RT60 --------------------------------
    print("\nAblation vs reverberation (image-source room model)...")
    rt60s = [0.05, 0.15, 0.3, 0.45, 0.6, 0.8]
    ab_angles = list(range(-120, 121, 30))
    AB_TRIALS = 60
    d.reseed(30)
    ab_raw = ablation_vs_rt60(rt60s, ab_angles, snr=SNR, trials=AB_TRIALS)
    safe_fig(fig_ablation, rt60s, ab_raw, SNR)

    # ---------------- Experiment 1b: isotropy ---------------------------------------
    print("\nIsotropy of the azimuth variance (M39)...")
    iso_angles = list(range(-180, 180, 15))
    d.reseed(31)
    iso = isotropy_check(iso_angles, snr=SNR, trials=400)
    safe_fig(fig_isotropy, iso_angles, iso)

    # ---------------- Experiment 2: resource scaling --------------------------------
    print("\nResource scaling: aperture...")
    radii = [0.02, 0.03, 0.05, 0.08, 0.12]
    sc_angles = list(range(-150, 151, 30))
    d.reseed(32)
    ap_raw = scaling_vs_aperture(radii, sc_angles, snr=SNR, trials=60)
    print("Resource scaling: snapshot length...")
    snaplens = [256, 512, 1024, 2048, 4096]
    d.reseed(33)
    sl_raw = scaling_vs_snaplen(snaplens, sc_angles, snr=SNR, trials=60)
    safe_fig(fig_scaling, radii, ap_raw, snaplens, sl_raw, SNR)

    # ---------------- Experiment 3: temporal accumulation ---------------------------
    Ts = [1, 2, 4, 8, 16, 32, 64, 128]
    TMAX, T_TRIALS = 128, 30
    print(f"\nTemporal accumulation, free field (T up to {TMAX}, "
          f"{T_TRIALS} records per azimuth)...")
    # Azimuths are nudged off whole degrees (d.tiled_offsets) so that the true
    # inter-microphone delays do not sit at a fixed phase relative to the 2.604 us
    # correlation interpolation grid. Without this the residual quantisation error is
    # the same in every frame, i.e. it behaves as a bias, and it would contaminate the
    # free-field bias-floor measurement that this experiment exists to make.
    tang = [a + o for a, o in zip(range(-150, 151, 30), d.tiled_offsets(11))]
    d.reseed(34)
    ff_blocks, ff_b, ff_s1, ff_n = temporal_sweep(
        lambda th: d.simulate(th, SNR), tang, Ts, trials=T_TRIALS, tmax=TMAX)
    ff = {mo: _curve(ff_blocks, Ts, mo) for mo in ('w', 'u')}

    rev, rev_bias, rev_sigma = {}, {}, {}
    rev_blocks = {}
    rang = [a + o for a, o in zip(range(-120, 121, 40), d.tiled_offsets(7))]
    for tag, rt in zip((35, 36, 37), (0.15, 0.3, 0.6)):
        print(f"\nTemporal accumulation, RT60 = {rt} s...")
        d.reseed(tag)
        rirs_cache = {th: rr.build_rirs(th, rt) for th in rang}
        blocks, b_, s_, _ = temporal_sweep(
            lambda th: rr.simulate_reverb(rirs_cache[th], SNR),
            rang, Ts, trials=T_TRIALS, tmax=TMAX)
        rev_blocks[rt] = blocks
        rev[rt] = {mo: _curve(blocks, Ts, mo) for mo in ('w', 'u')}
        rev_bias[rt], rev_sigma[rt] = b_, s_

    safe_fig(fig_temporal, Ts, ff, rev, SNR)

    floors = {}
    for lab, (r, se) in [("free field", ff['w'])] + \
                        [(f"RT60 {rt:.2f} s", c['w']) for rt, c in rev.items()]:
        floors[lab] = fit_bias_floor(Ts, r ** 2, 2 * r * se)
    safe_fig(fig_bias_floor, Ts, ff, rev, floors)

    # ================================ REPORT ========================================
    print("\n\n==== 1. ABLATION: gate and weighting vs RT60 "
          f"@ {SNR} dB SNR ====")
    print(f"     n = {len(ab_angles)*AB_TRIALS} frames per (variant, RT60) cell; "
          "variants share every snapshot (paired)")
    for v in VARIANTS:
        for rt, e in zip(rt60s, ab_raw[v]):
            print("  " + d.fmt_summary(f"{v:<24} RT60 {rt:4.2f} s:", e, rng=bs))
    print("\n  -- PAIRED difference vs 'Neither (= GCC-PHAT)', mean d|error| in deg --")
    print("     a difference is real only if |mean| exceeds ~2 standard errors")
    for v in VARIANTS:
        if v == REF_VARIANT:
            continue
        for i, rt in enumerate(rt60s):
            m, s, n = paired_delta(ab_raw[v][i], ab_raw[REF_VARIANT][i])
            flag = "   <-- significant" if abs(m) > 2 * s else ""
            print(f"  {v:<24} RT60 {rt:4.2f} s: {m:+7.4f} +-{s:6.4f} deg "
                  f"({m/s if s > 0 else 0:+5.2f} sigma, n={n}){flag}")

    print("\n\n==== 1b. ISOTROPY of the azimuth error (M39) ====")
    print("     robust s.d. of the signed azimuth error, per azimuth, 400 trials each")
    print("     azimuth (deg): " + " ".join(f"{a:>6d}" for a in iso_angles))
    print("     dotted 'predicted' rows are (M36): sqrt(e_th^T (A^T A)^-1 e_th),")
    print("     normalised to its own mean, i.e. the SHAPE the theory demands.")
    ref = iso["uniform weights (3 pairs)"][0].mean()
    for c, (s, se) in iso.items():
        pred = isotropy_prediction(iso_angles, ISO_DROP[c])
        print(f"  {c:<26} " + " ".join(f"{x:6.3f}" for x in s))
        print(f"  {'  (standard error)':<26} " + " ".join(f"{x:6.3f}" for x in se))
        print(f"  {'  normalised measured':<26} " + " ".join(f"{x:6.3f}"
                                                            for x in s / s.mean()))
        print(f"  {'  normalised predicted':<26} " + " ".join(f"{x:6.3f}" for x in pred))
        cv = 100 * np.std(s, ddof=1) / np.mean(s)
        chi2_flat = np.sum((s - np.mean(s)) ** 2 / se ** 2) / (len(s) - 1)
        chi2_pred = np.sum((s - s.mean() * pred) ** 2 / se ** 2) / len(s)
        lvl = isotropy_level(ISO_DROP[c]) / isotropy_level(None)
        print(f"  {'  -> mean s.d.':<26} {s.mean():6.3f} deg "
              f"(measured {s.mean()/ref:5.3f}x the 3-pair uniform case; "
              f"(M36) with Cov = sigma_tau^2 I predicts {lvl:5.3f}x)")
        print(f"  {'  -> CV over azimuth':<26} {cv:5.2f} %   "
              f"chi2/dof against FLAT {chi2_flat:6.2f}   "
              f"chi2/dof against (M36) {chi2_pred:6.2f}")

    print("\n\n==== 2a. APERTURE SCALING (free field, "
          f"{SNR} dB SNR, {len(sc_angles)*60} frames per point) ====")
    for R_, e in zip(radii, ap_raw):
        print("  " + d.fmt_summary(f"R = {R_*100:>5.1f} cm:", e, rng=bs))
    apm = np.array([d.quantile_se(e, 0.5)[0] for e in ap_raw])
    apse = np.array([d.quantile_se(e, 0.5)[1] for e in ap_raw])
    sl_, sl_se = loglog_slope(np.array(radii), apm, apse, seed=12)
    print(f"  log-log slope of median vs R : {sl_:+.3f} +-{sl_se:.3f}  "
          f"(M40 predicts -1)")
    print("  R x median (cm deg): " +
          "  ".join(f"{R_*100*m:.2f}" for R_, m in zip(radii, apm)))

    print("\n==== 2b. SNAPSHOT SCALING (free field, "
          f"{SNR} dB SNR, {len(sc_angles)*60} frames per point) ====")
    for N_, e in zip(snaplens, sl_raw):
        print("  " + d.fmt_summary(f"N = {N_:>5d} ({1e3*N_/d.FS:>5.1f} ms):", e, rng=bs))
    slm = np.array([d.quantile_se(e, 0.5)[0] for e in sl_raw])
    slse = np.array([d.quantile_se(e, 0.5)[1] for e in sl_raw])
    ss, ss_se = loglog_slope(np.array(snaplens, float), slm, slse, seed=13)
    print(f"  log-log slope of median vs N : {ss:+.3f} +-{ss_se:.3f}  "
          f"(CRB predicts -0.5; pre-re-baseline log gave -0.208)")

    print("\n\n==== 3. TEMPORAL ACCUMULATION ====")
    print(f"     free field: {len(tang)} azimuths x {T_TRIALS} records x {TMAX} frames")
    print(f"     reverberant: {len(rang)} azimuths x {T_TRIALS} records x {TMAX} frames")
    print("     blocks at T are disjoint sub-sequences of each record, so n falls as 1/T")
    header = "     T:      " + "".join(f"{t:>9d}" for t in Ts)
    for name, curves in [("free field", ff)] + \
                        [(f"RT60 {rt:.2f} s", c) for rt, c in rev.items()]:
        print(f"\n  {name}")
        print(header)
        for mo, lab in (('w', "weighted"), ('u', "plain   ")):
            r, se = curves[mo]
            print(f"     {lab} RMSE:" + "".join(f"{x:>9.3f}" for x in r))
            print(f"       +- s.e.  :" + "".join(f"{x:>9.3f}" for x in se))
        n_at = [len(curves['w'][0])] * 0
        print("     n blocks :" + "".join(
            f"{len((ff_blocks if name=='free field' else rev_blocks[float(name.split()[1])])[('w', t)]):>9d}"
            for t in Ts))
        # paired weighted-vs-plain difference at each T
        src = ff_blocks if name == "free field" else rev_blocks[float(name.split()[1])]
        print("     weighted - plain, paired mean |error| difference (deg):")
        for t in Ts:
            a = np.abs(src[('w', t)]); b_ = np.abs(src[('u', t)])
            m, s, n = paired_delta(a, b_)
            flag = " <-- significant" if abs(m) > 2 * s else ""
            print(f"       T={t:>4d}: {m:+8.4f} +-{s:7.4f} deg "
                  f"({m/s if s > 0 else 0:+6.2f} sigma, n={n}){flag}")

    print("\n  -- fitted MSE(T) = b^2 + sigma_1^2 / T  (M62), weighted variant --")
    for lab, (b, se_b, s1, se_s1, res) in floors.items():
        print(f"  {lab:<14} b = {b:6.3f} +-{se_b:5.3f} deg,  "
              f"sigma_1 = {s1:6.3f} +-{se_s1:5.3f} deg,  "
              f"RMSE-residual {res:.4f} deg")

    print("\n  -- DIRECTLY MEASURED per-azimuth bias b(theta) and dispersion sigma_1 --")
    print(f"     free field ({ff_n} frames per azimuth)")
    print("     azimuth (deg): " + " ".join(f"{a:>7.2f}" for a in tang))
    print("     b(theta)     : " + " ".join(f"{x:>7.3f}" for x in ff_b))
    print("     sigma_1      : " + " ".join(f"{x:>7.3f}" for x in ff_s1))
    print(f"     b_rms = {np.sqrt(np.mean(ff_b**2)):.3f} deg   "
          f"(s.e. of each b(theta) ~ {np.mean(ff_s1)/np.sqrt(ff_n):.3f} deg), "
          f"mean sigma_1 = {np.mean(ff_s1):.3f} deg")
    for rt in rev:
        b_, s_ = rev_bias[rt], rev_sigma[rt]
        print(f"     RT60 {rt:.2f} s ({ff_n} frames per azimuth)")
        print("     azimuth (deg): " + " ".join(f"{a:>7.2f}" for a in rang))
        print("     b(theta)     : " + " ".join(f"{x:>7.3f}" for x in b_))
        print("     sigma_1      : " + " ".join(f"{x:>7.3f}" for x in s_))
        print(f"     b_rms = {np.sqrt(np.mean(b_**2)):.3f} deg   "
              f"(s.e. of each b(theta) ~ {np.mean(s_)/np.sqrt(ff_n):.3f} deg), "
              f"mean sigma_1 = {np.mean(s_):.3f} deg")

    print("\n  -- futility knee T_futile = sigma_1^2 / (alpha b^2), alpha = 0.1 (M67) --")
    for lab, (b, se_b, s1, se_s1, res) in floors.items():
        if b > 1e-3:
            tf = s1 ** 2 / (0.1 * b ** 2)
            print(f"  {lab:<14} T_futile = {tf:8.1f} frames = "
                  f"{tf*d.SIG_LEN/d.FS:7.2f} s")
        else:
            print(f"  {lab:<14} T_futile = infinite (no measurable bias floor)")

    print(f"\nFigures written to: {d.OUTDIR}")
