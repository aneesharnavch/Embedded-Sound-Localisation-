"""
rebaseline_checks.py
====================
The audit trail for the 2026-07-27 re-baseline. Four independent studies, none of which
takes any previously reported number on trust:

  A. DEFECT VERIFICATION. Reproduce, on a fixed seed and on matched snapshots, the claim
     that applying the PHAT weight over the full 0-24 kHz band rather than over the
     300-3400 Hz source band inflates the per-frame azimuth error. Measures the per-pair
     TDOA error directly as well as the azimuth error, and counts how many full-weight
     bins actually contain source.

  B. ARTEFACT DECOMPOSITION. Part of the improvement is an artefact of the simulation's
     noise model: the harness adds white Gaussian noise across the whole Nyquist band,
     whereas a real acquisition chain has an anti-alias filter and a transducer with
     finite bandwidth and therefore does not fill its out-of-band bins with noise. This
     study crosses {full-band weight, band-limited weight} with a sweep of acquisition
     bandwidths, on matched snapshots, so the paper can state how much of the gain is a
     genuine estimator improvement and how much was a simulation artefact.

  C. SNAPSHOT SCALING, full-band versus band-limited, paired. Tests the claim that the
     anomalous N^-0.208 scaling in the archived log is entirely a consequence of the
     full-band weight and that N^-1/2 is recovered by the fix.

  D. COMPUTE. Per-stage timing that separates arithmetic from Python dispatch, a
     vectorised SRP-PHAT that isolates the dispatch cost, an audit of the analytical FLOP
     model, and a measurement of the cost and the accuracy price of replacing the
     eightfold zero-padded inverse FFT with a native-length IFFT plus parabolic peak
     refinement.

Run:  py -3.14 rebaseline_checks.py
"""

import sys
import time
import os

import numpy as np
from numpy.fft import rfft, irfft

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import doa_benchmark as d                     # noqa: E402
import matplotlib.pyplot as plt               # noqa: E402

FULL = None                                   # PHAT weight over the whole 0..fs/2 band
BAND = d.SRC_BAND                             # PHAT weight over the source band (the fix)


# ==================================================================================
# A. DEFECT VERIFICATION
# ==================================================================================
def weight_occupancy(theta=37.0, snr_db=10.0, tag=101, trials=40):
    """What fraction of the bins that PHAT promotes to (near) unit weight is source?

    The regularized PHAT of gcc_phat leaves a bin at unit weight unless it is more than
    60 dB below the strongest bin. Count the unit-weight bins that lie outside the source
    band; those are the bins whose random phase is being given full authority.
    """
    d.reseed(tag)
    n = 2 * d.SIG_LEN
    f = np.fft.rfftfreq(n, 1.0 / d.FS)
    inband = (f >= BAND[0]) & (f <= BAND[1])
    fr_unit, fr_oob = [], []
    for _ in range(trials):
        X = d.simulate(theta, snr_db)
        R = rfft(X[0], n=n) * np.conj(rfft(X[1], n=n))
        mag = np.abs(R)
        unit = mag >= 1e-3 * mag.max()               # not attenuated by the 60 dB floor
        fr_unit.append(unit.mean())
        fr_oob.append(np.sum(unit & ~inband) / max(np.sum(unit), 1))
    return float(np.mean(fr_unit)), float(np.mean(fr_oob)), int(inband.sum()), int(f.size)


def paired_weight_comparison(angles, snrs, trials, tag, acq_band=None,
                             weight_bands=(FULL, BAND)):
    """Evaluate several PHAT weight bands on the SAME snapshots.

    Returns res[(weight_label, snr)] = dict(az_err=..., dtau=...).
    Pairing matters: the whole point is to attribute a difference to the weight and to
    nothing else, and matched snapshots remove the Monte-Carlo variance entirely.
    """
    labels = ["full-band" if b is None else f"{b[0]:.0f}-{b[1]:.0f} Hz"
              for b in weight_bands]
    res = {(lab, s): {"az": [], "dtau": []} for lab in labels for s in snrs}
    d.reseed(tag)
    off = d.tiled_offsets(trials)      # keep the truth off the correlation lag grid
    for snr in snrs:
        for th0 in angles:
            for t in range(trials):
                th = th0 + off[t]
                t_true = d.true_pair_tdoas(th)
                X = d.simulate(th, snr, acq_band=acq_band)
                for lab, b in zip(labels, weight_bands):
                    res[(lab, snr)]["az"].append(
                        d.ang_err(d.est_gccphat_ls(X, band=b), th))
                    res[(lab, snr)]["dtau"].append(d.pair_tdoas(X, band=b) - t_true)
        print(f"    SNR {snr:>3} dB done", flush=True)
    for k in res:
        res[k]["az"] = np.array(res[k]["az"])
        res[k]["dtau"] = np.array(res[k]["dtau"]).ravel()
    return labels, res


def report_paired(labels, res, snrs, indent="  "):
    for snr in snrs:
        print(f"{indent}--- nominal SNR {snr} dB ---")
        for lab in labels:
            e = np.abs(res[(lab, snr)]["az"])
            dt = res[(lab, snr)]["dtau"]
            s_tau = float(np.std(dt))
            s_tau_r = float(np.median(np.abs(dt - np.median(dt))) / 0.6745)
            r, r_se = d.rmse_se(e)
            med, med_se = d.quantile_se(e, 0.5)
            p90, p90_se = d.quantile_se(e, 0.9)
            pred = np.rad2deg(d.C * s_tau / (np.sqrt(4.5) * d.R))
            print(f"{indent}  {lab:<14} RMSE {r:8.3f} +-{r_se:6.3f}  "
                  f"median {med:7.3f} +-{med_se:5.3f}  p90 {p90:8.3f} +-{p90_se:6.3f}  "
                  f"sigma_tau {s_tau*1e6:9.3f} us (robust {s_tau_r*1e6:7.3f})  "
                  f"M40 -> {pred:8.3f} deg")
        if len(labels) == 2:
            a = np.abs(res[(labels[0], snr)]["az"])
            b = np.abs(res[(labels[1], snr)]["az"])
            dv = a - b
            print(f"{indent}  paired mean |error| reduction "
                  f"({labels[0]} -> {labels[1]}): "
                  f"{dv.mean():+8.3f} +-{dv.std(ddof=1)/np.sqrt(dv.size):6.3f} deg "
                  f"({dv.mean()/(dv.std(ddof=1)/np.sqrt(dv.size)):+7.1f} sigma)")
            ra = d.rmse_se(a)[0]; rb = d.rmse_se(b)[0]
            print(f"{indent}  RMSE ratio full-band / band-limited: {ra/rb:8.2f}x")


# ==================================================================================
# C. SNAPSHOT SCALING, PAIRED
# ==================================================================================
def snapshot_scaling_paired(snaplens, angles, snr=10, trials=60, tag=140):
    """Signed azimuth errors, both weight bands, matched snapshots, versus snapshot length."""
    d.reseed(tag)
    out = {("full-band", N): [] for N in snaplens}
    out.update({("band-limited", N): [] for N in snaplens})
    off = d.tiled_offsets(trials)
    for N in snaplens:
        for th0 in angles:
            for t in range(trials):
                th = th0 + off[t]
                s = d.source_signal("speechlike", n=N)
                s = s / np.sqrt(np.mean(s ** 2) + 1e-12)
                taus = d.steering_delays(th)
                clean = np.stack([d.frac_delay(s, t) for t in taus])
                npow = np.mean(clean ** 2) / 10 ** (snr / 10)
                X = clean + d.RNG.standard_normal(clean.shape) * np.sqrt(npow)
                out[("full-band", N)].append(
                    d.ang_err(d.est_gccphat_ls(X, band=FULL), th))
                out[("band-limited", N)].append(
                    d.ang_err(d.est_gccphat_ls(X, band=BAND), th))
        print(f"    N = {N} done", flush=True)
    return {k: np.array(v) for k, v in out.items()}


# ==================================================================================
# D. COMPUTE
# ==================================================================================
def tdoa_parabolic(x_i, x_j, fs=d.FS, band=BAND):
    """Native-length IFFT plus parabolic peak refinement (math_model.md M20).

    The candidate cheap replacement for the eightfold zero-padded inverse FFT that
    dominates the front-end cost. Carries a systematic interpolation bias, because a
    whitened correlation peak is a sinc and not a parabola; this function exists so that
    the bias can be measured rather than assumed.
    """
    n = x_i.shape[0] + x_j.shape[0]
    X = rfft(x_i, n=n)
    Y = rfft(x_j, n=n)
    R = X * np.conj(Y)
    mag = np.abs(R)
    R /= np.maximum(mag, 1e-3 * mag.max() + 1e-12)
    if band is not None:
        f = np.fft.rfftfreq(n, 1.0 / fs)
        R[(f < band[0]) | (f > band[1])] = 0.0
    cc = irfft(R, n=n)
    half = n // 2
    cc = np.concatenate((cc[-half:], cc[:half + 1]))
    k = int(np.argmax(cc))
    if 0 < k < cc.size - 1:
        den = cc[k - 1] - 2 * cc[k] + cc[k + 1]
        delta = 0.5 * (cc[k - 1] - cc[k + 1]) / den if den != 0 else 0.0
        delta = float(np.clip(delta, -0.5, 0.5))
    else:
        delta = 0.0
    return (k - half + delta) / fs

def est_gccphat_ls_parabolic(X, mic_xy=d.MIC_XY, fs=d.FS, band=BAND):
    M = X.shape[0]
    A, b = [], []
    for i in range(M):
        for j in range(i + 1, M):
            A.append(mic_xy[i] - mic_xy[j])
            b.append(-d.C * tdoa_parabolic(X[i], X[j], fs, band))
    u, *_ = np.linalg.lstsq(np.array(A), np.array(b), rcond=None)
    return np.rad2deg(np.arctan2(u[1], u[0]))


def srp_stage_callables(X, grid_deg=1.0):
    """Split est_srp_phat into (shared GCC front end) and (Python grid loop).

    Returns callables so the two stages can be timed inside the same interleaved suite
    as the whole estimators, which keeps the comparison fair when the host is noisy.
    """
    M = X.shape[0]
    def front(_=None):
        return {(i, j): d.gcc_phat(X[i], X[j])
                for i in range(M) for j in range(i + 1, M)}
    pair_cc = front()
    grid = np.arange(-180, 180, grid_deg)
    def loop(_=None):
        power = np.zeros_like(grid, dtype=float)
        for k, phi in enumerate(grid):
            taus = d.steering_delays(phi)
            p = 0.0
            for (i, j), (lags, cc) in pair_cc.items():
                p += np.interp(taus[i] - taus[j], lags, cc)
            power[k] = p
        return grid[np.argmax(power)]
    n_calls = grid.size * (1 + M * (M - 1) // 2)          # steering + one interp per pair
    return ({"SRP shared GCC-PHAT front end": front,
             "SRP azimuth grid loop (Python)": loop}, n_calls)


def out_of_band_weight_budget(theta=37.3, snr_db=10.0, acq_bands=(None, (20.0, 20000.0),
                                                                 (20.0, 8000.0),
                                                                 (20.0, 4000.0),
                                                                 (300.0, 3400.0)),
                              tag=160, trials=20):
    """Where the surviving damage comes from, for each acquisition bandwidth.

    Two distinct mechanisms keep the full-band weight harmful even after an anti-alias
    filter, and they need separating:

      (i)  the acquisition band is WIDER than the source band, so the bins between the
           source cut-off (3400 Hz) and the acquisition cut-off contain noise and no
           source, yet still receive unit PHAT weight;
      (ii) gcc_phat zero-pads from N to n = 2N before the forward transform. A brick-wall
           filter applied on the length-N grid is not a brick wall on the length-n grid,
           so the odd bins of the padded transform carry sinc leakage from the retained
           band. This is why the full-band weight still costs something even when the
           acquisition band equals the source band exactly.

    The figure of merit is the f^2-weighted weight budget, because the peak-location
    error is set by the noise slope over the curvature and both carry a factor f^2
    (math_model.md M22-M23). A ratio near 1 means the out-of-band bins contribute as much
    leverage as the source does.

    Returns a list of (label, n_oob_bins_at_weight_above_half, f2_weighted_ratio).
    """
    d.reseed(tag)
    n = 2 * d.SIG_LEN
    f = np.fft.rfftfreq(n, 1.0 / d.FS)
    inb = (f >= d.SRC_BAND[0]) & (f <= d.SRC_BAND[1])
    w2 = (2 * np.pi * f) ** 2
    rows = []
    for ab in acq_bands:
        lab = "0-24 kHz (none)" if ab is None else f"{ab[0]:.0f}-{ab[1]:.0f} Hz"
        cnt, rat = [], []
        for _ in range(trials):
            X = d.simulate(theta, snr_db, acq_band=ab)
            R = rfft(X[0], n=n) * np.conj(rfft(X[1], n=n))
            mag = np.abs(R)
            w = np.minimum(1.0, mag / (1e-3 * mag.max()))      # effective PHAT weight
            cnt.append(np.sum(w[~inb] > 0.5))
            rat.append(np.sqrt(np.sum(w[~inb] ** 2 * w2[~inb])
                               / np.sum(w[inb] ** 2 * w2[inb])))
        rows.append((lab, float(np.mean(cnt)), float(np.mean(rat))))
    return rows


def parabolic_bias(snr_db=40.0, tag=161, n_off=25, trials=40):
    """Systematic delay bias of parabolic refinement versus fractional sample offset.

    math_model.md M20 warns of up to 0.119 samples of bias because a PHAT-whitened peak
    is a sinc rather than a parabola. That warning was derived for a FULL-BAND whitened
    peak, whose main lobe is one sample wide. With the weight restricted to 300-3400 Hz
    the main lobe is about fs/(2*3400) = 7 samples wide and a parabola is a much better
    local model, so the bias should be far smaller. Measured here rather than assumed.
    """
    d.reseed(tag)
    fs = d.FS
    offs = np.linspace(-0.5, 0.5, n_off)
    bias_par, bias_i8 = [], []
    for off in offs:
        tau = off / fs
        ep, e8 = [], []
        for _ in range(trials):
            s = d.source_signal("speechlike")
            s = s / np.sqrt(np.mean(s ** 2) + 1e-12)
            a = s
            b = d.frac_delay(s, tau)
            p = np.mean(a ** 2) / 10 ** (snr_db / 10)
            a = a + d.RNG.standard_normal(a.shape) * np.sqrt(p)
            b = b + d.RNG.standard_normal(b.shape) * np.sqrt(p)
            ep.append(tdoa_parabolic(a, b) * fs + off)      # est is -tau in lag convention
            e8.append(d.tdoa_phat(a, b) * fs + off)
        bias_par.append(np.mean(ep)); bias_i8.append(np.mean(e8))
    return offs, np.array(bias_par), np.array(bias_i8)


def flop_model():
    """Recompute the analytical FLOP table of math_model.md 7.2-7.5 from its own
    formulas, so the numbers quoted there are audited rather than copied."""
    N, M, P, I, G = d.SIG_LEN, 3, 3, 8, 360
    n = 2 * N
    K = n // 2 + 1
    cfft = lambda L: 2.5 * L * np.log2(L)
    tbl = {}
    for lab, Ii in (("I=8", 8), ("I=1 + parabolic", 1)):
        fwd = M * cfft(n)
        cpsd = P * (6 * K + 4 * K + 2 * K)
        inv = P * cfft(Ii * n)
        amax = P * (Ii * n + 1)
        tbl[lab] = dict(forward=fwd / 1e6, cpsd=cpsd / 1e6, inverse=inv / 1e6,
                        argmax=amax / 1e6,
                        total=(fwd + cpsd + inv + amax) / 1e6)
    gcc = tbl["I=8"]["total"]
    prop = gcc + 3 * P * I * n / 1e6
    srp = gcc + (G * (2 * M + M + P * (np.log2(I * n) + 4)) + G) / 1e6
    L, Ksn, Fb, cexp = 512, 7, 33, 50
    music = (Ksn * M * (L + cfft(L))
             + Fb * (8 * M ** 2 * Ksn + M ** 3 + cexp * G * M
                     + 8 * G * M ** 2 + 8 * G * M)) / 1e6
    return tbl, dict(gcc=gcc, proposed=prop, srp=srp, music=music)


# ==================================================================================
def fig_artefact(acq_khz, rmse_full, rmse_band, se_full, se_band, snr):
    """acq_khz: upper cut-off of the modelled acquisition chain, in kHz."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(6.8, 2.7))
    x = np.array(acq_khz, float)
    ax1.errorbar(x, rmse_full, yerr=se_full, capsize=2,
                 label="full-band PHAT weight (pre-re-baseline)", **d._style(0))
    ax1.errorbar(x, rmse_band, yerr=se_band, capsize=2,
                 label=f"PHAT weight {BAND[0]:.0f}-{BAND[1]:.0f} Hz (re-baselined)",
                 **d._style(1))
    ax1.axvline(BAND[1] / 1e3, color='gray', ls=(0, (1, 1)), lw=1.0, marker='')
    ax1.text(BAND[1] / 1e3 * 1.1, max(rmse_full) * 0.72, "source\nband edge",
             fontsize=6.5, color='gray')
    ax1.set_xlabel("Acquisition-chain upper cut-off (kHz)")
    ax1.set_ylabel(f"Azimuth RMSE at {snr} dB SNR (deg)")
    ax1.set_xscale('log'); ax1.set_yscale('log')
    d.plain_ticks(ax1, 'x', [3.4, 4, 8, 12, 20, 24])
    d.plain_ticks(ax1, 'y', [0.3, 0.5, 1, 2, 4])
    ax1.legend(fontsize=6.0, loc='center left')
    ax1.annotate("(a)", (0.03, 0.95), xycoords='axes fraction', fontsize=8, va='top')

    ratio = np.array(rmse_full) / np.array(rmse_band)
    ax2.plot(x, ratio, **d._style(2))
    ax2.axhline(1.0, color='k', lw=0.8, ls='-', marker='')
    ax2.set_xlabel("Acquisition-chain upper cut-off (kHz)")
    ax2.set_ylabel("RMSE ratio,\nfull-band / band-limited weight")
    ax2.set_xscale('log'); ax2.set_yscale('log')
    d.plain_ticks(ax2, 'x', [3.4, 4, 8, 12, 20, 24])
    d.plain_ticks(ax2, 'y', [1, 2, 3, 5, 10, 14])
    ax2.annotate("(b) how much of the improvement\nsurvives a realistic front end",
                 (0.03, 0.95), xycoords='axes fraction', fontsize=6.5, va='top')
    fig.tight_layout()
    fig.savefig(f"{d.OUTDIR}/fig_phat_artefact_decomposition.png", dpi=d.DPI)
    plt.close(fig)


# ==================================================================================
ANGLES = list(range(-150, 151, 30))            # 11 azimuths
SNRS = [0, 10, 20, 40]
TRIALS = 40                                    # 440 matched frames per cell


def study_A():
    print("\n\n================ A. DEFECT VERIFICATION ================")
    fr_unit, fr_oob, n_in, n_tot = weight_occupancy()
    print(f"  FFT bins per pair (n = 2N zero-padded)   : {n_tot}")
    print(f"  bins inside the source band              : {n_in} "
          f"({100*n_in/n_tot:.2f} %)")
    print(f"  bins left at unit PHAT weight (10 dB SNR): {100*fr_unit:.2f} % of all bins")
    print(f"  of those, fraction OUTSIDE the source band: {100*fr_oob:.2f} %")
    print("  (the mathematics track reported 81 %; the line above is what this harness")
    print("   independently gives, so the premise of the defect is confirmed)")

    print(f"\n  Paired comparison, {len(ANGLES)} azimuths x {TRIALS} trials "
          f"= {len(ANGLES)*TRIALS} matched frames per cell,")
    print("  identical snapshots for both weight bands, plain GCC-PHAT + LS estimator:")
    labels, resA = paired_weight_comparison(ANGLES, SNRS, TRIALS, tag=110)
    report_paired(labels, resA, SNRS)

    print("\n  Bound comparison. (M82) is the azimuth CRB and takes the NOMINAL SNR;")
    print("  (M83) is the Knapp-Carter delay bound and takes the in-band SNR (M84).")
    print("  'attainable' is the M83 bound and the 2.604 us interpolation grid floor")
    print("  (M25) added in quadrature, which is the best this front end can do.")
    for snr in SNRS:
        crb = d.crb_azimuth_deg(snr)
        rf = d.rmse_se(np.abs(resA[(labels[0], snr)]["az"]))[0]
        rb = d.rmse_se(np.abs(resA[(labels[1], snr)]["az"]))[0]
        stf = np.std(resA[(labels[0], snr)]["dtau"])
        stb = np.std(resA[(labels[1], snr)]["dtau"])
        crb_tau = d.crb_tdoa_s(snr)
        attain = float(np.hypot(crb_tau, d.tdoa_grid_floor_s()))
        print(f"    SNR {snr:>3} dB: CRB(M82) {crb:8.4f} deg | full-band RMSE {rf:8.3f}"
              f" ({rf/crb:9.1f}x CRB) | band-limited RMSE {rb:7.3f} ({rb/crb:7.2f}x CRB)")
        print(f"                CRB(M83) sigma_tau {crb_tau*1e6:6.3f} us | grid floor "
              f"{d.tdoa_grid_floor_s()*1e6:5.3f} us | attainable {attain*1e6:5.3f} us"
              f" -> achieved/attainable: full-band {stf/attain:9.1f}x, "
              f"band-limited {stb/attain:6.2f}x")
    return labels, resA


def study_B():
    print("\n\n================ B. ARTEFACT DECOMPOSITION ================")
    print("  The harness adds white noise over the whole 0-24 kHz Nyquist band. Real")
    print("  hardware has an anti-alias filter and a band-limited transducer, so its")
    print("  out-of-band bins are not filled with noise in the same way. The acquisition")
    print("  band below is applied to signal AND noise together at constant noise power")
    print("  spectral density, so the in-band SNR is identical in every row and the only")
    print("  thing that changes is how much out-of-band noise the front end sees.")
    ACQ = [(None, "0-24 kHz (as simulated)"),
           ((20.0, 20000.0), "20 Hz - 20 kHz"),
           ((20.0, 12000.0), "20 Hz - 12 kHz"),
           ((20.0, 8000.0), "20 Hz - 8 kHz"),
           ((20.0, 4000.0), "20 Hz - 4 kHz"),
           ((300.0, 3400.0), "300 Hz - 3.4 kHz")]
    SNR_B = 10
    art, labs = {}, None
    for tag, (ab, lab) in enumerate(ACQ):
        print(f"  acquisition band {lab} ...", flush=True)
        labs, r = paired_weight_comparison(ANGLES, [SNR_B], TRIALS, tag=120 + tag,
                                           acq_band=ab)
        art[lab] = r
    print(f"\n  --- all cells at {SNR_B} dB nominal SNR, "
          f"{len(ANGLES)*TRIALS} matched frames each ---")
    print(f"  {'acquisition band':<26} {'PHAT weight':<14} "
          f"{'RMSE (deg)':>18} {'median (deg)':>18} {'sigma_tau (us)':>16}")
    rmse_full, rmse_band, se_full, se_band, acq_labels, acq_khz = [], [], [], [], [], []
    for ab, lab in ACQ:
        acq_labels.append(lab)
        acq_khz.append((d.FS / 2 if ab is None else ab[1]) / 1e3)
        for wl in labs:
            e = np.abs(art[lab][(wl, SNR_B)]["az"])
            r, rse = d.rmse_se(e)
            m, mse = d.quantile_se(e, 0.5)
            st = np.std(art[lab][(wl, SNR_B)]["dtau"]) * 1e6
            print(f"  {lab:<26} {wl:<14} {r:10.3f} +-{rse:5.3f} "
                  f"{m:11.3f} +-{mse:5.3f} {st:16.3f}")
            if wl == "full-band":
                rmse_full.append(r); se_full.append(rse)
            else:
                rmse_band.append(r); se_band.append(rse)
        print()
    fig_artefact(acq_khz, rmse_full, rmse_band, se_full, se_band, SNR_B)

    print("  gain from the fix as a function of acquisition bandwidth:")
    for lab, rf, rb in zip(acq_labels, rmse_full, rmse_band):
        print(f"    {lab:<26} full-band {rf:7.3f} deg -> band-limited {rb:6.3f} deg"
              f"   = {rf/rb:6.2f}x")

    print("\n  --- THE HEADLINE CONFIGURATIONS ---")
    hl = [("1. full-band weight + full-band noise        (the old baseline)",
           art["0-24 kHz (as simulated)"][("full-band", SNR_B)]),
          ("2. band-limited weight + full-band noise     (the reported fix)",
           art["0-24 kHz (as simulated)"][(labs[1], SNR_B)]),
          ("3. band-limited weight + band-limited noise  (realistic, 20 Hz-8 kHz)",
           art["20 Hz - 8 kHz"][(labs[1], SNR_B)]),
          ("4. full-band weight + band-limited noise     (the defect's cost on"
           " realistic hardware, 20 Hz-8 kHz)",
           art["20 Hz - 8 kHz"][("full-band", SNR_B)])]
    base = d.rmse_se(np.abs(hl[0][1]["az"]))[0]
    for name, cell in hl:
        e = np.abs(cell["az"])
        r, rse = d.rmse_se(e)
        m, mse = d.quantile_se(e, 0.5)
        print(f"  {name}")
        print(f"      RMSE {r:8.3f} +-{rse:6.3f} deg   median {m:7.3f} +-{mse:5.3f} deg"
              f"   improvement over config 1: {base/r:7.2f}x")
    r2 = d.rmse_se(np.abs(hl[1][1]["az"]))[0]
    r3 = d.rmse_se(np.abs(hl[2][1]["az"]))[0]
    r4 = d.rmse_se(np.abs(hl[3][1]["az"]))[0]
    print(f"\n  The improvement that survives on realistic hardware is config 4 -> 3, "
          f"i.e. {r4/r3:.2f}x,")
    print(f"  against {base/r2:.2f}x measured under the simulation's full-band noise "
          "model.")

    print("\n  Why band-limiting the weight still helps when the noise is already")
    print("  band-limited. Out-of-band weight budget, per acquisition bandwidth:")
    print(f"    {'acquisition band':<20} {'bins outside 300-3400 Hz':>26} "
          f"{'f^2-weighted out-of-band':>26}")
    print(f"    {'':<20} {'still at weight > 0.5':>26} "
          f"{'/ in-band leverage ratio':>26}")
    for lab, cnt, rat in out_of_band_weight_budget():
        print(f"    {lab:<20} {cnt:26.1f} {rat:26.3f}")
    print("    Two mechanisms. (i) When the acquisition band is wider than the source")
    print("    band, the bins between 3400 Hz and the acquisition cut-off hold noise and")
    print("    no source but still receive unit weight. (ii) Even when the acquisition")
    print("    band equals the source band, gcc_phat zero-pads N -> 2N, and a brick wall")
    print("    on the length-N grid is not a brick wall on the length-2N grid: the odd")
    print("    bins carry sinc leakage. Those leaked bins sit at high frequency, where")
    print("    the f^2 leverage is large, which is why the residual penalty is not")
    print("    negligible. The 60 dB regularized-PHAT floor does not remove either.")


def study_C():
    print("\n\n================ C. SNAPSHOT SCALING, PAIRED ================")
    SNAPS = [256, 512, 1024, 2048, 4096]
    sc = snapshot_scaling_paired(SNAPS, ANGLES, snr=10, trials=60, tag=140)
    print("  WHICH STATISTIC CARRIES THE SLOPE. At N = 256 the delay range spans 5 % of")
    print("  the record and both variants throw wrap outliers, so the RMSE at that point")
    print("  is set by a handful of catastrophic frames and its log-log slope is not a")
    print("  measure of the noise scaling. The theory (CRB, GDOP) is a statement about")
    print("  the DISPERSION of the bulk, so the slope is quoted on the robust standard")
    print("  deviation MAD/0.6745 of the signed error. Median, RMSE and the robust")
    print("  s.d. are all tabulated; medians are included because the archived log")
    print("  reports medians.")
    print("  N:                            " + "".join(f"{N:>16d}" for N in SNAPS))

    def _slope(y, yse, seed):
        lx, ly = np.log(np.array(SNAPS, float)), np.log(y)
        s = float(np.polyfit(lx, ly, 1)[0])
        rng = np.random.default_rng([d.SEED, seed])
        dr = [np.polyfit(lx, ly + rng.standard_normal(len(ly)) * (yse / y), 1)[0]
              for _ in range(400)]
        return s, float(np.std(dr, ddof=1))

    for wl in ("full-band", "band-limited"):
        med = np.array([d.quantile_se(np.abs(sc[(wl, N)]), 0.5)[0] for N in SNAPS])
        mse = np.array([d.quantile_se(np.abs(sc[(wl, N)]), 0.5)[1] for N in SNAPS])
        rms = np.array([d.rmse_se(sc[(wl, N)])[0] for N in SNAPS])
        rse = np.array([d.rmse_se(sc[(wl, N)])[1] for N in SNAPS])
        rob = np.array([float(np.median(np.abs(sc[(wl, N)] - np.median(sc[(wl, N)])))
                              / 0.6745) for N in SNAPS])
        nn = len(sc[(wl, SNAPS[0])])
        robse = rob / np.sqrt(2 * (nn - 1)) * 1.2      # MAD is ~1.2x noisier than the s.d.
        out_frac = np.array([100 * np.mean(np.abs(sc[(wl, N)]) > 20) for N in SNAPS])
        print(f"  {wl:<14} median   (deg): " +
              "".join(f"{x:10.3f}+-{s:5.3f}" for x, s in zip(med, mse)))
        print(f"  {'':<14} RMSE     (deg): " +
              "".join(f"{x:10.3f}+-{s:5.3f}" for x, s in zip(rms, rse)))
        print(f"  {'':<14} robust sd (deg): " +
              "".join(f"{x:10.3f}+-{s:5.3f}" for x, s in zip(rob, robse)))
        print(f"  {'':<14} |err| > 20 deg (%): " +
              "".join(f"{x:16.2f}" for x in out_frac))
        for nm, y, ys, sd in (("robust sd", rob, robse, 77), ("median", med, mse, 78),
                              ("RMSE", rms, rse, 79)):
            s, sse = _slope(y, ys, sd)
            print(f"  {'':<14} log-log slope of {nm:<10} vs N : {s:+.3f} +-{sse:.3f}"
                  f"   (theory -0.5)")


def study_D():
    print("\n\n================ D. COMPUTE ================")
    print("  Wall-clock numbers; run this study on an otherwise idle machine.")
    d.reseed(150)
    X = d.simulate(30, 20)

    print("\n  D1. Per-stage timing (minimum over interleaved rounds; see")
    print("      doa_benchmark.time_suite for why min-of-interleaved-rounds)")
    stages, n_calls = srp_stage_callables(X)
    suite = dict(stages)
    suite.update({
        "est_srp_phat (reference)": lambda Z: d.est_srp_phat(Z)[0],
        "est_srp_phat_vec": lambda Z: d.est_srp_phat_vec(Z)[0],
        "est_gccphat_ls": d.est_gccphat_ls,
        "est_proposed": d.est_proposed,
        "est_music": d.est_music,
        "est_gccphat_ls (I=1+parabolic)": est_gccphat_ls_parabolic,
    })
    tm = d.time_suite(suite, X, reps=40, rounds=11)
    for nm, (t, sp) in tm.items():
        print(f"    {nm:<32} {t:8.3f} ms  (spread {sp:6.3f} ms)")
    t_gcc = tm["est_gccphat_ls"][0]
    t_loop = tm["SRP azimuth grid loop (Python)"][0]
    t_front = tm["SRP shared GCC-PHAT front end"][0]
    print(f"    grid loop cost per NumPy call    : "
          f"{t_loop*1e3/n_calls:6.3f} us over {n_calls} calls")
    print(f"    front end + grid loop            : {t_front + t_loop:8.3f} ms "
          f"vs whole est_srp_phat {tm['est_srp_phat (reference)'][0]:8.3f} ms")
    for nm in ("est_proposed", "est_srp_phat (reference)", "est_srp_phat_vec",
               "est_music", "est_gccphat_ls (I=1+parabolic)"):
        print(f"    {nm:<32} / GCC-PHAT = {tm[nm][0]/t_gcc:6.3f}x")
    a1 = d.est_srp_phat(X)[0]; a2 = d.est_srp_phat_vec(X)[0]
    print(f"    vectorised SRP output identical  : {a1 == a2} ({a1} vs {a2} deg)")

    print("\n  D2. Analytical FLOP model, recomputed from math_model.md 7.2-7.5")
    tbl, tot = flop_model()
    for lab, row in tbl.items():
        print(f"    {lab:<16} forward {row['forward']:7.3f} | CPSD+PHAT "
              f"{row['cpsd']:7.3f} | inverse {row['inverse']:7.3f} "
              f"({100*row['inverse']/row['total']:5.1f} %) | argmax {row['argmax']:6.3f}"
              f" | total {row['total']:7.3f} MFLOP")
    print(f"    I=8 -> I=1 + parabolic total speed-up : "
          f"{tbl['I=8']['total']/tbl['I=1 + parabolic']['total']:6.2f}x "
          f"(inverse-transform term alone "
          f"{tbl['I=8']['inverse']/tbl['I=1 + parabolic']['inverse']:6.2f}x)")
    print(f"    GCC-PHAT {tot['gcc']:7.3f} | Proposed {tot['proposed']:7.3f} "
          f"({tot['proposed']/tot['gcc']:5.3f}x) | SRP {tot['srp']:7.3f} "
          f"({tot['srp']/tot['gcc']:5.3f}x) | MUSIC {tot['music']:7.3f} "
          f"({tot['music']/tot['gcc']:5.3f}x)")

    print("\n  D3. Measured cost and accuracy price of I=1 + parabolic refinement")
    tp = d.time_suite({
        "gcc_phat interp=8, one pair": lambda Z: d.gcc_phat(Z[0], Z[1], interp=8),
        "gcc_phat interp=1, one pair": lambda Z: d.gcc_phat(Z[0], Z[1], interp=1),
        "tdoa_parabolic, one pair": lambda Z: tdoa_parabolic(Z[0], Z[1]),
    }, X, reps=120, rounds=11)
    for nm, (t, sp) in tp.items():
        print(f"    {nm:<32} {t:8.4f} ms  (spread {sp:7.4f} ms)")
    t_i8 = tp["gcc_phat interp=8, one pair"][0]
    print(f"    interp=8 -> interp=1                       "
          f"{t_i8/tp['gcc_phat interp=1, one pair'][0]:5.2f}x cheaper")
    print(f"    interp=8 -> interp=1 + parabolic refinement "
          f"{t_i8/tp['tdoa_parabolic, one pair'][0]:5.2f}x cheaper")
    t_par_ls = tm["est_gccphat_ls (I=1+parabolic)"][0]
    print(f"    whole estimator, I=8             : {t_gcc:8.4f} ms")
    print(f"    whole estimator, I=1 + parabolic : {t_par_ls:8.4f} ms  "
          f"({t_gcc/t_par_ls:5.2f}x cheaper; FLOP model predicts 5.13x)")
    print("    accuracy price (paired, same snapshots, band-limited weight):")
    d.reseed(151)
    for snr in (10, 20, 40):
        e8, ep = [], []
        for th in ANGLES:
            for _ in range(40):
                Z = d.simulate(th, snr)
                e8.append(abs(d.ang_err(d.est_gccphat_ls(Z, band=BAND), th)))
                ep.append(abs(d.ang_err(est_gccphat_ls_parabolic(Z, band=BAND), th)))
        e8 = np.array(e8); ep = np.array(ep)
        r8, s8 = d.rmse_se(e8); rp, sp = d.rmse_se(ep)
        dv = ep - e8
        print(f"      SNR {snr:>3} dB: I=8 RMSE {r8:7.3f} +-{s8:5.3f} deg | "
              f"I=1+parabolic RMSE {rp:7.3f} +-{sp:5.3f} deg | "
              f"paired mean penalty {dv.mean():+7.3f} "
              f"+-{dv.std(ddof=1)/np.sqrt(dv.size):5.3f} deg")

    print("\n    systematic parabolic interpolation bias vs fractional sample offset")
    print("    (M20 warns of up to 0.119 samples for a FULL-BAND whitened sinc peak;")
    print("     with the band-limited weight the main lobe is ~7 samples wide)")
    offs, bpar, bi8 = parabolic_bias()
    print("      offset (samples): " + " ".join(f"{o:+6.2f}" for o in offs[::4]))
    print("      bias, parabolic : " + " ".join(f"{b:+6.3f}" for b in bpar[::4]))
    print("      bias, I=8 argmax: " + " ".join(f"{b:+6.3f}" for b in bi8[::4]))
    mb = float(np.max(np.abs(bpar)))
    print(f"      max |bias| parabolic {mb:.4f} samples = {mb/d.FS*1e6:.3f} us "
          f"= {np.rad2deg(d.C*mb/d.FS/(np.sqrt(4.5)*d.R)):.3f} deg")
    print(f"      max |bias| I=8 argmax {np.max(np.abs(bi8)):.4f} samples")

    print("\n  D4. Memory, from math_model.md 7.6 (analytical, not measured)")
    for lab, I_ in (("I=8", 8), ("I=1", 1)):
        corr_kb = I_ * 2 * d.SIG_LEN * 4 / 1024
        print(f"    {lab:<5} input {3*d.SIG_LEN*4/1024:6.1f} kB | correlation buffer "
              f"{corr_kb:7.1f} kB (per pair, reusable) | accumulator 8 B")


if __name__ == "__main__":
    # Section selection. Study D is wall-clock timing and must be run with nothing else
    # on the machine, so it can be requested alone:  py -3.14 rebaseline_checks.py D
    WANT = set(a.upper() for a in sys.argv[1:]) or {"A", "B", "C", "D"}
    print("rebaseline_checks.py  --  audit of the 2026-07-27 PHAT band re-baseline")
    print(f"  fs {d.FS} Hz, N {d.SIG_LEN}, R {d.R*100:.1f} cm, seed {d.SEED}")
    print(f"  source band {d.SRC_BAND} Hz, interpolation factor I = 8")
    print(f"  studies run: {sorted(WANT)}")
    if "A" in WANT:
        study_A()
    if "B" in WANT:
        study_B()
    if "C" in WANT:
        study_C()
    if "D" in WANT:
        study_D()
    print(f"\nFigures written to: {d.OUTDIR}")

