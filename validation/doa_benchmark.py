"""
doa_benchmark.py
================
A self-contained, dependency-light (numpy/scipy/matplotlib only) Direction-of-Arrival
(DoA) accuracy benchmark for a small microphone array.

WHY THIS EXISTS
---------------
Journal of Open Hardware wants *quality control / validation*: measured, reproducible
numbers showing how well the hardware works. This script produces exactly those
figures in simulation (free-field, plane-wave, additive-noise model), and benchmarks
two textbook DoA estimators so you have a credible baseline to compare your on-device
"hedge" algorithm against:

    * GCC-PHAT (pairwise TDOA + least squares)  -> the "cheap" method (closest to what
      a lightweight embedded estimator actually does; ~10 us-class compute)
    * SRP-PHAT (steered-response power grid search) -> the "strong" robust baseline

The same harness later accepts your *real recorded* multichannel clips, so the figures
in your paper come from the SAME code on simulated AND measured data. That is the
honest, reviewer-proof validation section your resubmission needs.

>>> EDIT THE ARRAY GEOMETRY + FS BELOW TO MATCH YOUR ACTUAL BOARD <<<

RE-BASELINE NOTE (2026-07-27)
----------------------------
A defect was found in the GCC-PHAT front end and corrected here. PHAT normalises every
frequency bin to unit magnitude. Applied over the full 0-fs/2 band against a source that
occupies only SRC_BAND (300-3400 Hz), it promotes the essentially random phase of
noise-only bins to full weight. Roughly (fs/2 - B) / (fs/2) = 87 % of the weighted bins
carry no delay information at all.  The weight is now restricted to PHAT_BAND
(see `gcc_phat`), which is an explicit, documented parameter.

All numbers in `validation/archive/*_FULLBAND_PHAT_*.log` were produced with the old
full-band weight. The replacement numbers, the before/after comparison and the
decomposition of how much of the gain is a genuine estimator improvement versus an
artefact of the simulation's full-band noise model, are in `paper/rebaseline_results.md`.
"""

import os
import time
import numpy as np
from numpy.fft import rfft, irfft
import matplotlib.pyplot as plt

# ----------------------------------------------------------------------------------
# 1. CONFIG  --  >>> CHANGE THESE TO MATCH YOUR HARDWARE <<<
# ----------------------------------------------------------------------------------
C = 343.0                 # speed of sound, m/s (20 C air)
FS = 48_000               # per-channel sample rate of your ESP32-S3 ADC, Hz
SIG_LEN = 2048            # samples per snapshot (~43 ms @ 48 kHz)

# --- Microphone geometry (metres). 3 mics, since the paper uses 3 ADC channels. ---
# Default = small equilateral triangle, ~5 cm circum-radius (full 360 deg azimuth).
# If your board is a LINEAR array, use the LINEAR block instead.
R = 0.05                                  # array radius / spacing scale (m)  <-- MEASURE THIS
MIC_XY = np.array([                       # triangular array (resolves full 360 deg)
    [R * np.cos(np.deg2rad(a)), R * np.sin(np.deg2rad(a))]
    for a in (90, 210, 330)
])
# LINEAR alternative (front half-plane only, has front/back ambiguity):
# MIC_XY = np.array([[-R, 0.0], [0.0, 0.0], [R, 0.0]])

OUTDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "figs")
os.makedirs(OUTDIR, exist_ok=True)

SEED = 7                                  # fixed seed => reproducible figures
RNG = np.random.default_rng(SEED)

def reseed(tag=0):
    """Reset the module RNG deterministically.

    The RNG is a module-level generator consumed in call order, so a result depends on
    everything drawn before it. Each experiment therefore calls reseed(<its own tag>)
    first, which makes every experiment reproducible on its own and independent of the
    order in which the experiments are run. Tags are listed in the __main__ block of each
    script so a single experiment can be re-run in isolation and reproduce its log line.
    """
    global RNG
    RNG = np.random.default_rng([SEED, int(tag)])
    return RNG


# ----------------------------------------------------------------------------------
# 1b. BAND DEFINITIONS  --  the subject of the 2026-07-27 re-baseline
# ----------------------------------------------------------------------------------
# SRC_BAND   the band the simulated source actually occupies (see source_signal).
# PHAT_BAND  the band over which the PHAT weight is applied (see gcc_phat). THE FIX:
#            defaults to the source band. Set to None to reproduce the pre-re-baseline
#            full-band behaviour that produced validation/archive/*_FULLBAND_PHAT_*.log.
# ACQ_BAND   the pass-band of the modelled acquisition chain (anti-alias filter +
#            transducer response), applied to signal+noise in simulate(). None means the
#            idealised "white noise over the whole Nyquist band" model of the original
#            harness, which is the appropriate model for a 48 kHz chain whose anti-alias
#            filter sits just below Nyquist. A narrower chain is modelled by setting this
#            to e.g. (20.0, 4000.0). Used for the artefact decomposition; NOT a default.
SRC_BAND = (300.0, 3400.0)
PHAT_BAND = SRC_BAND
ACQ_BAND = None


# ----------------------------------------------------------------------------------
# 2. SIGNAL MODEL  --  plane wave from azimuth theta, fractional delay via FFT phase
# ----------------------------------------------------------------------------------
def steering_delays(theta_deg, mic_xy=MIC_XY):
    """Arrival time (s) at each mic relative to array origin for a far-field source."""
    u = np.array([np.cos(np.deg2rad(theta_deg)), np.sin(np.deg2rad(theta_deg))])
    return -(mic_xy @ u) / C            # tau_m = -(p_m . u)/c

def frac_delay(sig, tau_s, fs=FS):
    """Delay a 1-D signal by tau_s seconds (can be fractional) via frequency-domain phase shift."""
    n = sig.shape[0]
    f = np.fft.rfftfreq(n, d=1.0 / fs)
    return irfft(rfft(sig) * np.exp(-1j * 2 * np.pi * f * tau_s), n=n)

def bandlimit(x, band, fs=FS):
    """Ideal (brick-wall) band-pass of the last axis of `x`. `band=None` is a no-op.

    Used for two distinct purposes, which must not be confused:
      * shaping the SOURCE into SRC_BAND (source_signal), and
      * modelling the ACQUISITION CHAIN's anti-alias filter and transducer roll-off,
        which band-limits signal AND noise together (simulate, simulate_reverb).
    """
    if band is None:
        return x
    n = x.shape[-1]
    X = rfft(x, axis=-1)
    f = np.fft.rfftfreq(n, 1.0 / fs)
    X[..., (f < band[0]) | (f > band[1])] = 0.0
    return irfft(X, n=n, axis=-1)

def source_signal(kind="speechlike", n=SIG_LEN, fs=FS, band=SRC_BAND):
    """Broadband test source. 'speechlike' = 300-3400 Hz band-limited noise."""
    if kind == "tone":
        t = np.arange(n) / fs
        return np.sin(2 * np.pi * 2000 * t)
    if kind == "chirp":
        t = np.arange(n) / fs
        return np.sin(2 * np.pi * (500 + (6000 - 500) * t / (n / fs)) * t)
    # default: band-limited white noise (speech-like)
    x = RNG.standard_normal(n)
    return bandlimit(x, band, fs)

def simulate(theta_deg, snr_db, kind="speechlike", mic_xy=MIC_XY, acq_band=None):
    """Return (M, N) array of mic signals for a source at theta_deg with given SNR.

    `snr_db` is the ratio of total signal power to total noise power BEFORE the
    acquisition filter, i.e. it fixes the noise power spectral density. That convention
    is what makes the acq_band comparison fair: band-limiting the acquisition chain then
    removes out-of-band noise without changing the in-band SNR, which is exactly what an
    anti-alias filter does physically. (Fixing total noise power instead would raise the
    in-band noise density as the band narrows and confound the comparison.)

    acq_band=None reproduces the original harness: white noise over the full 0-fs/2 band.
    """
    s = source_signal(kind)
    s = s / np.sqrt(np.mean(s**2) + 1e-12)
    taus = steering_delays(theta_deg, mic_xy)
    clean = np.stack([frac_delay(s, t) for t in taus])          # (M, N)
    sig_pow = np.mean(clean**2)
    noise_pow = sig_pow / (10 ** (snr_db / 10))
    noise = RNG.standard_normal(clean.shape) * np.sqrt(noise_pow)
    return bandlimit(clean + noise, acq_band)


# ----------------------------------------------------------------------------------
# 3. ESTIMATORS
# ----------------------------------------------------------------------------------
def gcc_phat(x_i, x_j, fs=FS, interp=8, band=PHAT_BAND):
    """GCC-PHAT cross-correlation between two channels. Returns (lags_s, cc).

    `band` -- (f_lo, f_hi) in Hz, or None for the whole 0..fs/2 range.
    ------------------------------------------------------------------
    THE 2026-07-27 FIX. PHAT divides every bin by its own magnitude, so after weighting
    a bin that contains only sensor noise has exactly the same influence on the
    correlation as a bin that contains the source. Its phase, however, is uniformly
    random and carries no information about the delay. With a 300-3400 Hz source and a
    48 kHz sampler, 3100 Hz of the 24 000 Hz weighted band is informative and the other
    20 900 Hz is not; the useless bins dominate the sum and set the peak-location error.
    The scaling argument (math_model.md M23-M24) predicts the resulting loss to be
    sqrt(int_0^24k f^2 df / int_300^3400 f^2 df) = 18.8 in delay standard deviation.

    Restricting the weight to the band where the two channels are actually coherent is
    what the maximum-likelihood generalized correlator prescribes (M21). It is applied
    here by zeroing the weighted cross-spectrum outside `band` before the inverse
    transform, which costs nothing.

    The regularized-PHAT magnitude floor below is UNCHANGED and still needed: within the
    retained band, bins more than 60 dB down are left attenuated rather than whitened to
    unit magnitude. The two mechanisms are complementary -- the floor handles near-zero
    bins inside the band, `band` removes the bins that are outside the source entirely.
    """
    n = x_i.shape[0] + x_j.shape[0]
    X = rfft(x_i, n=n)
    Y = rfft(x_j, n=n)
    R = X * np.conj(Y)
    # Regularized PHAT: floor the magnitude RELATIVE to the strongest bin so that
    # near-zero (out-of-band / noise-only) bins are down-weighted instead of having
    # their numerical-garbage phase amplified to unit weight. Without this, accuracy
    # paradoxically collapses at HIGH SNR. (eps = 1e-3 * max|R|.)
    mag = np.abs(R)
    R /= np.maximum(mag, 1e-3 * mag.max() + 1e-12)
    if band is not None:                       # <-- band-limited PHAT weight (the fix)
        f = np.fft.rfftfreq(n, 1.0 / fs)
        R[(f < band[0]) | (f > band[1])] = 0.0
    cc = irfft(R, n=interp * n)
    max_shift = int(interp * n / 2)
    cc = np.concatenate((cc[-max_shift:], cc[:max_shift + 1]))
    lags = np.arange(-max_shift, max_shift + 1) / (interp * fs)
    return lags, cc

def tdoa_phat(x_i, x_j, fs=FS, band=PHAT_BAND):
    """Best-delay TDOA (s) for a pair via GCC-PHAT peak."""
    lags, cc = gcc_phat(x_i, x_j, fs, band=band)
    return lags[np.argmax(cc)]

def est_gccphat_ls(X, mic_xy=MIC_XY, fs=FS, band=PHAT_BAND):
    """Cheap estimator: pairwise GCC-PHAT TDOAs -> least-squares azimuth."""
    M = X.shape[0]
    A, b = [], []
    for i in range(M):
        for j in range(i + 1, M):
            t_ij = tdoa_phat(X[i], X[j], fs, band=band)   # = -((p_i-p_j).u)/c
            A.append(mic_xy[i] - mic_xy[j])
            b.append(-C * t_ij)
    u, *_ = np.linalg.lstsq(np.array(A), np.array(b), rcond=None)
    return np.rad2deg(np.arctan2(u[1], u[0]))

def pair_tdoas(X, mic_xy=MIC_XY, fs=FS, band=PHAT_BAND):
    """Per-pair GCC-PHAT delays and their true values. Returns (est, true_unavailable).

    Exposed so the GDOP law (M40) can be validated against a directly measured per-pair
    sigma_tau instead of being inferred from the azimuth error.
    """
    M = X.shape[0]
    out = []
    for i in range(M):
        for j in range(i + 1, M):
            out.append(tdoa_phat(X[i], X[j], fs, band=band))
    return np.array(out)

def true_pair_tdoas(theta_deg, mic_xy=MIC_XY):
    """Noise-free TDOA of every pair for a far-field source at theta_deg (M4)."""
    taus = steering_delays(theta_deg, mic_xy)
    M = len(taus)
    return np.array([taus[i] - taus[j] for i in range(M) for j in range(i + 1, M)])

def _pair_confidence(lags, cc):
    """Confidence score for one GCC-PHAT pair from its peak-to-sidelobe ratio (PSR).

    A clean, single-source, low-reverberation pair has a tall isolated peak (high PSR).
    A pair corrupted by noise or a reflection has competing peaks (PSR -> 1). Returns
    (psr, tdoa_s): PSR in [1, inf) used as the pair weight, and the peak-lag delay.
    """
    k = int(np.argmax(cc))
    peak = cc[k]
    # Exclude a small window around the main lobe, then measure the strongest sidelobe.
    w = max(1, cc.size // 100)
    mask = np.ones(cc.size, dtype=bool)
    mask[max(0, k - w): min(cc.size, k + w + 1)] = False
    sidelobe = np.max(cc[mask]) if mask.any() else 0.0
    psr = float(peak / (abs(sidelobe) + 1e-9))
    return psr, float(lags[k])

def est_proposed(X, mic_xy=MIC_XY, fs=FS, gate=True, weight=True, gate_floor=0.5,
                 return_conf=False, band=PHAT_BAND):
    """PROPOSED lightweight estimator: confidence-gated, physically-feasible weighted TDOA.

    This is the honest formalization of the on-device "TDOA + decision" method. It costs
    essentially the same as est_gccphat_ls (same GCC-PHAT front end) but adds a per-pair
    decision layer before the least-squares azimuth solve:

      1. GCC-PHAT TDOA + PSR (peak-to-sidelobe) confidence for every microphone pair.
      2. GATE (the "decision" step) -- a pair is REJECTED if either:
           (a) its delay exceeds the physical far-field maximum d_ij / c  (a reflection or
               spurious peak that cannot come from a real source), or
           (b) its confidence is below gate_floor x the best pair's confidence  (an
               ambiguous, untrustworthy peak).
         Rejection is hard, but never below the 2 pairs needed to solve -- the lowest-
         confidence pairs are kept back if too many would be dropped.
      3. WEIGHTED least squares: surviving pairs contribute in proportion to their PSR, so
         a confident pair dominates a marginal one instead of being averaged with it.

    gate/weight are independent toggles for the ablation. With both off this reduces exactly
    to est_gccphat_ls (uniform, ungated). The two mechanisms are distinct: weighting is a
    soft, continuous down-weight; the gate is a hard drop of outliers and infeasible peaks.

    `band` is passed straight through to gcc_phat, so the proposed estimator and plain
    GCC-PHAT share the identical (band-limited) front end and the ablation stays a clean
    comparison of the decision layer alone.
    """
    M = X.shape[0]
    rows, taus, psrs = [], [], []
    for i in range(M):
        for j in range(i + 1, M):
            lags, cc = gcc_phat(X[i], X[j], fs, band=band)
            psr, t_ij = _pair_confidence(lags, cc)
            d_ij = np.linalg.norm(mic_xy[i] - mic_xy[j])
            feasible = abs(t_ij) <= 1.05 * d_ij / C           # far-field delay bound
            rows.append(mic_xy[i] - mic_xy[j])
            taus.append(t_ij)
            psrs.append(psr if feasible else 0.0)             # infeasible -> zero conf
    rows = np.array(rows); taus = np.array(taus); psrs = np.array(psrs)

    keep = np.ones(len(taus), dtype=bool)
    if gate:
        thresh = gate_floor * psrs.max()                      # relative confidence floor
        keep = psrs >= thresh
        if keep.sum() < 2:                                    # never starve the solver
            keep = np.argsort(psrs)[::-1][:max(2, (psrs > 0).sum())]
            k = np.zeros(len(taus), dtype=bool); k[keep] = True; keep = k
    A = rows[keep]; b = -C * taus[keep]
    w = psrs[keep] if weight else np.ones(keep.sum())
    w = np.where(w > 0, w, 1e-3)                              # avoid all-zero weights
    sw = np.sqrt(w)
    u, *_ = np.linalg.lstsq(A * sw[:, None], b * sw, rcond=None)
    az = np.rad2deg(np.arctan2(u[1], u[0]))
    if return_conf:
        return az, float(np.mean(psrs[keep]))                # frame confidence for accumulation
    return az

def accumulate_doa(frames, mic_xy=MIC_XY, fs=FS, weighted=True, band=PHAT_BAND):
    """Confidence-weighted temporal accumulation of per-frame DoA -- the core of the method.

    `frames` is an iterable of (M, N) snapshots from a (quasi-)stationary source. Each frame
    gives a confidence-gated azimuth (est_proposed) and a confidence (mean surviving PSR); the
    window estimate is the PSR-weighted CIRCULAR mean of the per-frame azimuths.

    This is where the accuracy comes from: independent per-frame noise averages out ~1/sqrt(T)
    down to the room's reverberation-bias floor, for a few adds per frame and O(1) memory --
    the right trade for a cheap real-time device (a fraction of a second of latency buys an
    order-of-magnitude lower error). `weighted=False` (plain circular mean) is the ablation.
    """
    az, conf = frame_estimates(frames, mic_xy, fs, band=band)
    return combine_frames(az, conf, weighted=weighted)

def frame_estimates(frames, mic_xy=MIC_XY, fs=FS, band=PHAT_BAND):
    """Per-frame (azimuth_deg, confidence) arrays for a sequence of snapshots.

    Split out from accumulate_doa so that the confidence-weighted and plain-mean variants
    can be evaluated on the SAME per-frame estimates. That makes the weighted-vs-plain
    ablation a paired comparison, which removes the between-run Monte-Carlo variance that
    would otherwise swamp the small difference between them.
    """
    az, conf = [], []
    for X in frames:
        a, c = est_proposed(X, mic_xy, fs, return_conf=True, band=band)
        az.append(a); conf.append(c)
    return np.array(az), np.array(conf)

def combine_frames(az_deg, conf, weighted=True):
    """Weighted circular mean (M52) of per-frame azimuths."""
    w = np.asarray(conf, float) if weighted else np.ones(len(az_deg))
    r = np.deg2rad(np.asarray(az_deg, float))
    return np.rad2deg(np.arctan2(np.sum(w * np.sin(r)), np.sum(w * np.cos(r))))

def kish_teff(conf):
    """Kish effective sample size (M58) of a weight vector."""
    w = np.asarray(conf, float)
    return float(w.sum() ** 2 / (np.sum(w ** 2) + 1e-30))

def track_pid(azimuths, kp=0.6, ki=0.05, kd=0.1):
    """Recursive angular tracker over a frame SEQUENCE (the temporal "PID" refinement).

    Per-snapshot estimates jitter; a source moves slowly. This wrapped-angle PID locks the
    running azimuth to the stream of noisy per-frame estimates at negligible compute (a
    handful of adds per frame), which is what the device does live. Returns the smoothed
    azimuth track. All error arithmetic is wrapped to [-180, 180] so it works across +-180.
    """
    est = float(azimuths[0])
    integ = 0.0
    prev_err = 0.0
    out = []
    for z in azimuths:
        err = (z - est + 180) % 360 - 180
        integ = 0.9 * integ + err                             # leaky integrator
        deriv = err - prev_err
        est = (est + kp * err + ki * integ + kd * deriv + 180) % 360 - 180
        prev_err = err
        out.append(est)
    return np.array(out)

def est_music(X, mic_xy=MIC_XY, fs=FS, grid_deg=1.0, n_src=1, band=SRC_BAND):
    """Heavy subspace baseline: incoherent wideband MUSIC.

    Per frequency bin in the source band: estimate the M x M spatial covariance from
    short-time frames (snapshots), eigendecompose, project the array manifold onto the
    noise subspace, accumulate the pseudospectrum, then pick the azimuth of the peak.

    RE-BASELINE NOTE. MUSIC was ALREADY band-limited: it only ever accumulated bins
    inside `band`. It is therefore the one estimator here that never had the full-band
    weighting defect. That is the explanation for the pre-re-baseline logs showing MUSIC
    an order of magnitude more accurate than GCC-PHAT: the comparison was not measuring
    subspace processing against correlation processing, it was measuring a band-limited
    front end against a full-band one. With the defect fixed the comparison is finally
    like-for-like. Like SRP-PHAT, MUSIC is quantised to `grid_deg` (0.289 deg RMSE floor
    at the 1 deg default).
    """
    M, N = X.shape
    L = 512 if N >= 1024 else N // 4
    hop = L // 2
    starts = list(range(0, N - L + 1, hop))
    win = np.hanning(L)
    freqs = np.fft.rfftfreq(L, 1 / fs)
    Xf = np.stack([rfft(X[:, s:s + L] * win, axis=1) for s in starts])   # (K, M, F)
    grid = np.arange(-180, 180, grid_deg)
    taus = np.stack([steering_delays(th, mic_xy) for th in grid])        # (G, M)
    band_bins = np.where((freqs >= band[0]) & (freqs <= band[1]))[0]
    pseudo = np.zeros(len(grid))
    for fi in band_bins:
        snaps = Xf[:, :, fi]                                             # (K, M)
        R = (snaps.T @ snaps.conj()) / snaps.shape[0]                    # (M, M) spatial cov
        _, V = np.linalg.eigh(R)                                         # ascending eigvals
        En = V[:, :M - n_src]                                            # noise subspace
        Pn = En @ En.conj().T
        A = np.exp(-1j * 2 * np.pi * freqs[fi] * taus).T                 # (M, G) manifold
        denom = np.real(np.sum(np.conj(A) * (Pn @ A), axis=0))
        pseudo += 1.0 / (denom + 1e-12)
    return grid[np.argmax(pseudo)]

def est_srp_phat(X, mic_xy=MIC_XY, fs=FS, grid_deg=1.0, band=PHAT_BAND):
    """Strong baseline: SRP-PHAT grid search over azimuth.

    SRP-PHAT is built on exactly the same PHAT-weighted pairwise correlations as
    GCC-PHAT, so it suffered from the identical full-band-weighting defect and receives
    the identical fix via `band`. Not fixing it here would make the comparison unfair in
    the proposed method's favour.

    NOTE ON THE GRID FLOOR. The estimate is quantised to `grid_deg`, so this estimator
    cannot do better than a uniform error on +-grid_deg/2, i.e. an RMSE floor of
    grid_deg/sqrt(12) = 0.289 deg at the default 1 deg grid. Before the re-baseline that
    floor was far below the error and irrelevant; after it, it is the binding limit at
    high SNR and must be quoted alongside the numbers. Same applies to est_music.
    """
    M = X.shape[0]
    pair_cc = {}
    for i in range(M):
        for j in range(i + 1, M):
            pair_cc[(i, j)] = gcc_phat(X[i], X[j], fs, band=band)
    grid = np.arange(-180, 180, grid_deg)
    power = np.zeros_like(grid, dtype=float)
    for k, phi in enumerate(grid):
        taus = steering_delays(phi, mic_xy)
        p = 0.0
        for (i, j), (lags, cc) in pair_cc.items():
            p += np.interp(taus[i] - taus[j], lags, cc)
        power[k] = p
    return grid[np.argmax(power)], grid, power

def est_srp_phat_vec(X, mic_xy=MIC_XY, fs=FS, grid_deg=1.0, band=PHAT_BAND):
    """Vectorised SRP-PHAT. IDENTICAL OUTPUT to est_srp_phat; used only to show that the
    measured 4x cost of the reference implementation is Python dispatch overhead and not
    algorithmic complexity (math_model.md Section 7.4). Not used for any accuracy number.
    """
    M = X.shape[0]
    grid = np.arange(-180, 180, grid_deg)
    u = np.stack([np.cos(np.deg2rad(grid)), np.sin(np.deg2rad(grid))])       # (2, G)
    taus = -(mic_xy @ u) / C                                                 # (M, G)
    power = np.zeros(grid.size)
    for i in range(M):
        for j in range(i + 1, M):
            lags, cc = gcc_phat(X[i], X[j], fs, band=band)
            power += np.interp(taus[i] - taus[j], lags, cc)
    return grid[np.argmax(power)], grid, power


# ----------------------------------------------------------------------------------
# 4. HELPERS
# ----------------------------------------------------------------------------------
def ang_err(est, true):
    """Smallest signed angular error in degrees, wrapped to [-180, 180]."""
    return (est - true + 180) % 360 - 180


AZ_JITTER = 0.5              # deg, half-width of the truth offset (= half the SRP grid)

def tiled_offsets(n, half=AZ_JITTER):
    """n deterministic azimuth offsets that tile (-half, +half] uniformly.

    WHY THE TRUTH MUST NOT SIT ON THE SEARCH GRID. SRP-PHAT and MUSIC search azimuth on a
    1 deg grid. Every azimuth in the original sweeps was a whole number of degrees, so
    the true bearing lay exactly on that grid and those two estimators could return the
    exact answer. Before the re-baseline their errors were degrees-large and this cost
    nothing; afterwards it dominates, and the first re-baseline run duly produced an
    RMSE of exactly 0.000 deg for SRP-PHAT and MUSIC at 20 and 40 dB. That is a property
    of the test design, not of the estimators.

    Offsetting the truth off the grid restores the real quantisation penalty. The offsets
    are TILED rather than drawn at random so that the pooled quantisation error is
    uniform on +-0.5 deg, whose RMS is exactly 1/sqrt(12) = 0.289 deg -- a number the
    reader can check against the reported RMSE floor. It also randomises the phase of the
    true inter-microphone delays relative to the 2.604 us correlation interpolation grid,
    which the correlation estimators need for the same reason.
    """
    return (np.arange(n) + 0.5) / n * 2.0 * half - half


# --- uncertainty helpers: every reported point estimate gets a standard error ---------
def rmse_se(e):
    """RMSE and its standard error, from a sample of errors.

    Var(RMSE) ~= Var(e^2) / (4 n RMSE^2) by the delta method applied to sqrt(mean(e^2)).
    This is distribution-free and, unlike the Gaussian shortcut 1/sqrt(2n), stays valid
    for the heavy-tailed error distributions this array produces.
    """
    e = np.asarray(e, float).ravel()
    n = e.size
    m2 = np.mean(e ** 2)
    r = np.sqrt(m2)
    if n < 2 or r == 0:
        return r, 0.0
    se_m2 = np.std(e ** 2, ddof=1) / np.sqrt(n)
    return r, float(se_m2 / (2 * r))

def quantile_se(e, q=0.5, B=400, rng=None):
    """Sample quantile and a bootstrap standard error for it."""
    e = np.asarray(e, float).ravel()
    n = e.size
    pt = float(np.quantile(e, q))
    if n < 4:
        return pt, 0.0
    rng = rng or np.random.default_rng([SEED, 999])
    idx = rng.integers(0, n, size=(B, n))
    return pt, float(np.std(np.quantile(e[idx], q, axis=1), ddof=1))

def summarize(e, rng=None):
    """(median, se), (p90, se), (rmse, se), n  for one sample of absolute errors."""
    e = np.asarray(e, float).ravel()
    med = quantile_se(e, 0.5, rng=rng)
    p90 = quantile_se(e, 0.9, rng=rng)
    rms = rmse_se(e)
    return med, p90, rms, e.size

def fmt_summary(label, e, rng=None):
    (med, med_se), (p90, p90_se), (rms, rms_se), n = summarize(e, rng)
    return (f"{label} median {med:6.3f} +-{med_se:5.3f}  "
            f"p90 {p90:7.3f} +-{p90_se:6.3f}  "
            f"RMSE {rms:7.3f} +-{rms_se:6.3f}  (n={n})")


# ----------------------------------------------------------------------------------
# 5. EXPERIMENTS + FIGURES
# ----------------------------------------------------------------------------------
# Figure style: Okabe-Ito colour-blind-safe palette, distinct markers and dash patterns
# so the figures also survive greyscale printing; sized for single-column width; 300 dpi.
# No decorative titles -- the caption carries the description, axes carry the units.
CB = ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00", "#56B4E9", "#000000"]
MK = ["o", "s", "^", "D", "v", "P", "X"]
LS = ["-", "--", "-.", ":", (0, (3, 1, 1, 1)), (0, (5, 2)), (0, (1, 1))]
DPI = 300
plt.rcParams.update({
    "axes.prop_cycle": plt.cycler(color=CB),
    "font.size": 9, "axes.labelsize": 9, "legend.fontsize": 8,
    "xtick.labelsize": 8, "ytick.labelsize": 8,
    "axes.grid": True, "grid.alpha": 0.3, "savefig.dpi": DPI, "figure.dpi": DPI,
    "lines.linewidth": 1.6, "lines.markersize": 4.5,
})

def _style(k):
    return dict(color=CB[k % len(CB)], marker=MK[k % len(MK)], ls=LS[k % len(LS)])

def plain_ticks(ax, which, vals, fmt="{:g}"):
    """Replace matplotlib's 2x10^0 style log-axis labels with plain numbers.

    On a log axis spanning less than a decade -- which is most of these figures after
    the re-baseline -- the default minor-tick labels collide with each other and are
    unreadable at single-column width.
    """
    a = ax.xaxis if which == 'x' else ax.yaxis
    a.set_major_locator(plt.FixedLocator(vals))
    a.set_minor_locator(plt.NullLocator())
    a.set_major_formatter(plt.FixedFormatter([fmt.format(v) for v in vals]))

def fig_geometry():
    plt.figure(figsize=(3.4, 3.4))
    plt.scatter(MIC_XY[:, 0] * 100, MIC_XY[:, 1] * 100, s=70, marker='o',
                color=CB[0], zorder=3)
    for k, (x, y) in enumerate(MIC_XY * 100):
        plt.annotate(f"M{k}", (x, y), textcoords="offset points", xytext=(7, 5))
    plt.axhline(0, lw=.5, color='gray'); plt.axvline(0, lw=.5, color='gray')
    plt.gca().set_aspect('equal')
    plt.xlabel("x (cm)"); plt.ylabel("y (cm)")
    plt.tight_layout(); plt.savefig(f"{OUTDIR}/fig_geometry.png", dpi=DPI); plt.close()

def run_sweeps(angles, snrs, trials=30, kind="speechlike", acq_band=None,
               band=PHAT_BAND, collect_tdoa=True):
    """Monte-Carlo over angles x SNRs x trials for all four estimators.

    Also records the per-pair TDOA error of the shared GCC-PHAT front end, so that the
    GDOP law sigma_theta = c sigma_tau / (sqrt(4.5) R) (M40) can be checked against a
    directly measured sigma_tau rather than inferred from the azimuth error.
    """
    methods = {"Proposed (gated)": lambda X: est_proposed(X, band=band),
               "GCC-PHAT (cheap)": lambda X: est_gccphat_ls(X, band=band),
               "SRP-PHAT (strong)": lambda X: est_srp_phat(X, band=band)[0],
               "MUSIC (subspace)": est_music}
    errs = {m: np.zeros((len(snrs), len(angles), trials)) for m in methods}
    dtau = np.zeros((len(snrs), len(angles), trials, 3)) if collect_tdoa else None
    off = tiled_offsets(trials)            # truth is nudged off the 1 deg search grid
    for si, snr in enumerate(snrs):
        for ai, th in enumerate(angles):
            for t in range(trials):
                th_true = th + off[t]
                t_true = true_pair_tdoas(th_true)
                X = simulate(th_true, snr, kind, acq_band=acq_band)
                for m, fn in methods.items():
                    errs[m][si, ai, t] = abs(ang_err(fn(X), th_true))
                if collect_tdoa:
                    dtau[si, ai, t] = pair_tdoas(X, band=band) - t_true
        print(f"  SNR {snr:>3} dB done", flush=True)
    return methods, errs, dtau

def fig_cdf(methods, errs, snrs, snr_pick=10):
    si = snrs.index(snr_pick)
    plt.figure(figsize=(3.4, 2.8))
    for k, m in enumerate(methods):
        e = np.sort(errs[m][si].ravel())
        plt.plot(e, np.linspace(0, 1, e.size), label=m, marker='',
                 color=CB[k % len(CB)], ls=LS[k % len(LS)])
    plt.axhline(.5, ls='--', lw=.6, color='gray')
    plt.xlabel("Absolute azimuth error (deg)"); plt.ylabel("Empirical CDF")
    plt.xscale('log'); plt.xlim(1e-2, 60); plt.ylim(0, 1)
    plt.legend(loc='lower right')
    plt.tight_layout(); plt.savefig(f"{OUTDIR}/fig_error_cdf.png", dpi=DPI); plt.close()

def fig_rmse_vs_snr(methods, errs, snrs, crb=None):
    plt.figure(figsize=(3.4, 2.8))
    for k, m in enumerate(methods):
        rmse = np.array([rmse_se(errs[m][si])[0] for si in range(len(snrs))])
        se = np.array([rmse_se(errs[m][si])[1] for si in range(len(snrs))])
        plt.errorbar(snrs, rmse, yerr=se, capsize=2, label=m, **_style(k))
    if crb is not None:
        plt.plot(snrs, crb, color='k', ls=':', marker='', lw=1.2, label="CRB (M82)")
    plt.axhline(1.0 / np.sqrt(12), color='gray', ls=(0, (1, 1)), lw=1.0, marker='')
    plt.text(snrs[-1], 1.0 / np.sqrt(12) * 0.72,
             "1 deg search-grid floor, $1/\\sqrt{12}$ deg", fontsize=6.5,
             color='gray', ha='right')
    plt.xlabel("Nominal SNR (dB)"); plt.ylabel("Azimuth RMSE (deg)")
    plt.yscale('log'); plt.legend(fontsize=7)
    plt.tight_layout(); plt.savefig(f"{OUTDIR}/fig_rmse_vs_snr.png", dpi=DPI); plt.close()

def fig_heatmap(errs, snrs, angles, method="GCC-PHAT (cheap)"):
    med_err = np.median(errs[method], axis=2)          # (snr, angle); median = outlier-robust
    plt.figure(figsize=(3.4, 2.6))
    im = plt.pcolormesh(angles, snrs, med_err, shading='auto', cmap='cividis')
    plt.colorbar(im, label="Median |azimuth error| (deg)")
    plt.xlabel("True azimuth (deg)"); plt.ylabel("Nominal SNR (dB)")
    plt.grid(False)
    plt.tight_layout(); plt.savefig(f"{OUTDIR}/fig_accuracy_matrix.png", dpi=DPI); plt.close()

def time_suite(fns, X, reps=40, rounds=9, warmup=3):
    """Interleaved wall-clock timing of several callables, in ms per call.

    Two deliberate choices, because naive timing on this machine was giving 2x spread
    between nominally idle runs:

      * MINIMUM over rounds, not mean or median. Interference from other processes can
        only ever make a measurement slower, so the minimum is the least contaminated
        estimator of the intrinsic cost. The spread across rounds is returned as well so
        the reader can see how noisy the host was.
      * ROUND-ROBIN interleaving. All callables are timed inside each round, so a slow
        patch of wall-clock time hits every candidate rather than whichever one happened
        to be running, and the RATIOS -- which are the only thing the paper quotes -- stay
        valid even when the absolute numbers drift.

    Returns {name: (min_ms, spread_ms)} where spread is max-min over rounds.
    """
    names = list(fns)
    for nm in names:
        for _ in range(warmup):
            fns[nm](X)
    per = {nm: [] for nm in names}
    for _ in range(rounds):
        for nm in names:
            t0 = time.perf_counter()
            for _ in range(reps):
                fns[nm](X)
            per[nm].append((time.perf_counter() - t0) / reps * 1e3)
    return {nm: (float(np.min(v)), float(np.max(v) - np.min(v))) for nm, v in per.items()}

def _time_ms(fn, X, reps=40, warmup=3, rounds=9):
    """Single-callable wrapper around time_suite; returns the minimum, in ms."""
    return time_suite({"f": fn}, X, reps=reps, rounds=rounds, warmup=warmup)["f"][0]

def measure_compute(reps=80, snr=20):
    """Wall-clock time per estimate for each method, on the host, in ms.

    WHAT THIS IS AND IS NOT. These are properties of THIS reference NumPy implementation
    running on an x86 host. They are NOT algorithmic complexity ratios and they do NOT
    transfer to the microcontroller. The earlier claim that they do has been retracted:
    the FLOP model (math_model.md Section 7) predicts SRP-PHAT at 1.006x GCC-PHAT because
    SRP reuses the very same pairwise correlations, whereas the measured ratio is ~4x.
    The gap is Python interpreter dispatch in the un-vectorised 360-point grid loop, and
    `est_srp_phat_vec` is provided to demonstrate exactly that. For an algorithmic
    comparison a system designer must use the FLOP and memory model, not this table.
    """
    fns = {"Proposed (gated)": est_proposed,
           "GCC-PHAT (cheap)": est_gccphat_ls,
           "SRP-PHAT (strong)": lambda X: est_srp_phat(X)[0],
           "SRP-PHAT (vectorised)": lambda X: est_srp_phat_vec(X)[0],
           "MUSIC (subspace)": est_music}
    X = simulate(30, snr)
    return time_suite(fns, X, reps=reps)

SHORT = {"Proposed (gated)": "Proposed", "GCC-PHAT (cheap)": "GCC-PHAT",
         "SRP-PHAT (strong)": "SRP-PHAT", "MUSIC (subspace)": "MUSIC"}

def fig_pareto(methods, errs, snrs, times, flops=None, snr_pick=10):
    """Accuracy versus cost, on the two cost axes separately.

    They are shown side by side and NOT merged, because they disagree by a factor of four
    for SRP-PHAT and MUSIC and only one of them is a property of the algorithm. Panel (a)
    also carries the vectorised SRP-PHAT point, which produces bit-identical output to the
    reference implementation and costs 0.94x GCC-PHAT instead of 4.3x: the gap between the
    two SRP points is the Python interpreter, not the algorithm.
    """
    si = snrs.index(snr_pick)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(6.8, 2.9))
    rm = {m: rmse_se(errs[m][si])[0] for m in methods}

    # per-method label offsets, because Proposed and GCC-PHAT land almost on top of
    # each other and SRP-PHAT and MUSIC sit at the right-hand edge
    OFF = {"Proposed (gated)": ((7, -3), 'left'), "GCC-PHAT (cheap)": ((0, 9), 'center'),
           "SRP-PHAT (strong)": ((-7, 2), 'right'), "MUSIC (subspace)": ((-7, 2), 'right')}
    for k, m in enumerate(methods):
        t = times[m][0] if isinstance(times[m], tuple) else times[m]
        ax1.scatter(t, rm[m], s=48, zorder=3, color=CB[k % len(CB)],
                    marker=MK[k % len(MK)])
        ax1.annotate(SHORT[m], (t, rm[m]), textcoords="offset points",
                     xytext=OFF[m][0], ha=OFF[m][1], fontsize=7)
    key = "SRP-PHAT (vectorised)"
    if key in times:
        tv = times[key][0] if isinstance(times[key], tuple) else times[key]
        ax1.scatter(tv, rm["SRP-PHAT (strong)"], s=48, zorder=3,
                    facecolors='none', edgecolors=CB[2], marker=MK[2])
        ax1.annotate("SRP-PHAT\nvectorised", (tv, rm["SRP-PHAT (strong)"]),
                     textcoords="offset points", xytext=(-2, -22), fontsize=7)
        ax1.annotate("", xy=(tv * 1.06, rm["SRP-PHAT (strong)"]),
                     xytext=(times["SRP-PHAT (strong)"][0] * 0.94,
                             rm["SRP-PHAT (strong)"]),
                     arrowprops=dict(arrowstyle='->', color='gray', lw=0.9))
    ax1.set_xscale('log'); ax1.set_yscale('log')
    ax1.set_xlim(0.62, 6.5)
    plain_ticks(ax1, 'x', [0.8, 1, 2, 4])
    plain_ticks(ax1, 'y', [0.3, 0.4, 0.5, 0.7])
    ax1.set_xlabel("Measured host time per estimate (ms)")
    ax1.set_ylabel(f"Azimuth RMSE at {snr_pick} dB SNR (deg)")
    ax1.annotate("(a) reference NumPy implementation\n"
                 "     (a property of the code, not the algorithm)",
                 (0.03, 0.96), xycoords='axes fraction', fontsize=6.5, va='top')

    for k, m in enumerate(methods):
        ax2.scatter(flops[m], rm[m], s=48, zorder=3, color=CB[k % len(CB)],
                    marker=MK[k % len(MK)])
        ax2.annotate(SHORT[m], (flops[m], rm[m]), textcoords="offset points",
                     xytext=OFF[m][0], ha=OFF[m][1], fontsize=7)
    ax2.set_yscale('log'); ax2.set_xlim(2.8, 5.4)
    plain_ticks(ax2, 'y', [0.3, 0.4, 0.5, 0.7])
    ax2.set_xlabel("Model cost per estimate (MFLOP)")
    ax2.set_ylabel(f"Azimuth RMSE at {snr_pick} dB SNR (deg)")
    ax2.annotate("(b) analytical FLOP model\n     (the algorithmic comparison)",
                 (0.03, 0.96), xycoords='axes fraction', fontsize=6.5, va='top')
    fig.tight_layout(); fig.savefig(f"{OUTDIR}/fig_pareto.png", dpi=DPI); plt.close(fig)

def fig_srp_example(theta=37, snr=10):
    """One SRP-PHAT spatial spectrum, for the method description."""
    X = simulate(theta, snr)
    est, grid, power = est_srp_phat(X)
    plt.figure(figsize=(3.4, 2.6))
    plt.plot(grid, power / power.max(), color=CB[0], marker='')
    plt.axvline(theta, color=CB[2], ls='--', lw=1.2, label=f"true {theta} deg")
    plt.axvline(est, color=CB[1], ls=':', lw=1.2, label=f"estimate {est:.0f} deg")
    plt.xlabel("Candidate azimuth (deg)")
    plt.ylabel("Steered-response power (normalised)")
    plt.xlim(-180, 180); plt.legend()
    plt.tight_layout(); plt.savefig(f"{OUTDIR}/fig_srp_spectrum.png", dpi=DPI); plt.close()

def fig_phat_band_demo(theta=37, snr=10, tag=1001):
    """The defect, made visible: the PHAT-weighted correlation of one pair, full-band
    versus band-limited, on the SAME snapshot."""
    reseed(tag)
    X = simulate(theta, snr)
    t_true = true_pair_tdoas(theta)[0]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(6.8, 2.7))
    for k, (lab, bnd) in enumerate([("full-band weight (0-24 kHz)", None),
                                    (f"band-limited weight ({SRC_BAND[0]:.0f}-"
                                     f"{SRC_BAND[1]:.0f} Hz)", SRC_BAND)]):
        lags, cc = gcc_phat(X[0], X[1], band=bnd)
        sel = np.abs(lags) <= 400e-6
        ax1.plot(lags[sel] * 1e6, cc[sel] / np.max(np.abs(cc[sel])), marker='',
                 color=CB[k], ls=LS[k], label=lab)
    ax1.axvline(t_true * 1e6, color='gray', ls=(0, (1, 1)), lw=1.0)
    ax1.text(t_true * 1e6, 1.02, "true TDOA", fontsize=6.5, ha='center', color='gray')
    ax1.set_xlabel("Lag (us)"); ax1.set_ylabel("Normalised GCC-PHAT")
    ax1.legend(fontsize=6.5, loc='lower left')

    n = 2 * X.shape[1]
    f = np.fft.rfftfreq(n, 1.0 / FS)
    Rw = rfft(X[0], n=n) * np.conj(rfft(X[1], n=n))
    mag = np.abs(Rw)
    w_full = np.ones_like(mag)
    w_full[mag < 1e-3 * mag.max()] = mag[mag < 1e-3 * mag.max()] / (1e-3 * mag.max())
    w_bl = w_full.copy()
    w_bl[(f < SRC_BAND[0]) | (f > SRC_BAND[1])] = 0.0
    ax2.plot(f / 1e3, w_full, marker='', color=CB[0], ls=LS[0])
    ax2.plot(f / 1e3, w_bl, marker='', color=CB[1], ls=LS[1])
    ax2.set_xlabel("Frequency (kHz)"); ax2.set_ylabel("Effective PHAT bin weight")
    ax2.set_xlim(0, FS / 2e3); ax2.set_ylim(-0.05, 1.15)
    # Same definition as rebaseline_checks.weight_occupancy: of the bins the regularized
    # PHAT leaves at (near) unit weight, what fraction lies outside the source band?
    unit = w_full >= 0.5
    inband = (f >= SRC_BAND[0]) & (f <= SRC_BAND[1])
    frac = np.sum(unit & ~inband) / max(np.sum(unit), 1)
    ax2.annotate(f"{100*frac:.0f} % of the bins left at unit\n"
                 f"weight lie outside the source band",
                 (0.28, 0.62), xycoords='axes fraction', fontsize=6.5)
    fig.tight_layout(); fig.savefig(f"{OUTDIR}/fig_phat_band_defect.png", dpi=DPI)
    plt.close(fig)


def crb_azimuth_deg(snr_db, N=SIG_LEN, R_=R, band=SRC_BAND):
    """Cramer-Rao bound on azimuth standard deviation, degrees (M82).

    WHICH SNR GOES IN HERE. (M82) is a time-domain bound: sigma_w^2 is the per-sample
    noise variance, so P_s / sigma_w^2 is the NOMINAL full-band SNR that simulate() takes
    as its argument, and the source's band limitation is already carried by the
    mean-square radian bandwidth beta^2. The in-band conversion (M84) belongs to the
    coherence-based Knapp-Carter delay bound (M83), NOT here; applying it in both places
    double-counts and moves the bound by 8.9 dB. [Reproduces math_model.md Section 8.3
    to four significant figures: 0.5492 / 0.1737 / 0.05492 / 0.005492 deg at 0/10/20/40
    dB, against the 0.549 / 0.174 / 0.055 / 0.0055 tabulated there.]
    """
    f1, f2 = band
    beta2 = 4 * np.pi ** 2 * (f2 ** 3 - f1 ** 3) / (3 * (f2 - f1))
    snr = 10 ** (snr_db / 10)
    return np.rad2deg(C / R_ * np.sqrt(2.0 / (3 * N * snr * beta2)))

def crb_tdoa_s(snr_db, N=SIG_LEN, band=SRC_BAND, fs=FS):
    """Knapp-Carter bound on the per-pair delay standard deviation, seconds (M83).

    This one DOES take the in-band SNR (M84), because it is written in terms of the
    magnitude-squared coherence, which is a per-frequency quantity.
    [Reproduces math_model.md Section 8.3: 2.497 / 0.768 / 0.242 / 0.024 us.]
    """
    f1, f2 = band
    gamma = 10 ** (snr_db / 10) * (fs / 2) / (f2 - f1)          # in-band SNR (M84)
    integral = 4 * np.pi ** 2 * (f2 ** 3 - f1 ** 3) / 3
    return float(1.0 / np.sqrt(2 * (N / fs) * integral * gamma ** 2 / (1 + 2 * gamma)))

def tdoa_grid_floor_s(interp=8, fs=FS):
    """Interpolation-grid quantisation floor on the delay estimate, seconds (M25)."""
    return 1.0 / (np.sqrt(12) * interp * fs)


if __name__ == "__main__":
    print("doa_benchmark.py  --  RE-BASELINED free-field benchmark")
    print(f"  PHAT weighting band : {PHAT_BAND} Hz   (None = pre-re-baseline full band)")
    print(f"  source band         : {SRC_BAND} Hz")
    print(f"  acquisition band    : {ACQ_BAND}  (None = white noise over 0-{FS/2:.0f} Hz)")
    print(f"  seed                : {SEED}")
    print("Array geometry (cm):\n", np.round(MIC_XY * 100, 2))
    angles = list(range(-150, 151, 15))          # azimuth grid, 21 points
    snrs = [0, 5, 10, 20, 40]                     # dB
    TRIALS = 60                                   # was 30 pre-re-baseline

    reseed(1); fig_geometry()
    reseed(2); fig_srp_example()
    reseed(3); fig_phat_band_demo()

    print("Measuring per-estimate host compute (reference implementation only)...")
    reseed(4)
    times = measure_compute()

    print(f"Running Monte-Carlo sweeps ({len(angles)} angles x {len(snrs)} SNR "
          f"x {TRIALS} trials)...")
    reseed(5)
    methods, errs, dtau = run_sweeps(angles, snrs, trials=TRIALS)

    crb = [crb_azimuth_deg(s) for s in snrs]
    flops = {"Proposed (gated)": 4.522, "GCC-PHAT (cheap)": 4.227,
             "SRP-PHAT (strong)": 4.253, "MUSIC (subspace)": 3.239}   # math_model 7.2-7.3
    fig_cdf(methods, errs, snrs, snr_pick=10)
    fig_rmse_vs_snr(methods, errs, snrs, crb=crb)
    fig_heatmap(errs, snrs, angles)
    fig_pareto(methods, errs, snrs, times, flops=flops, snr_pick=10)

    # ---- numeric summary for the paper text ----
    bs = np.random.default_rng([SEED, 4242])
    print("\n==== FREE-FIELD ACCURACY (abs azimuth error, deg; +- = standard error) ====")
    print(f"     n = {len(angles)*TRIALS} frames per (method, SNR) cell")
    for m in methods:
        for si, snr in enumerate(snrs):
            print("  " + fmt_summary(f"{m:<20} SNR {snr:>3} dB:",
                                     errs[m][si].ravel(), rng=bs))

    print("\n==== PER-PAIR TDOA ERROR of the shared GCC-PHAT front end ====")
    print("  (feeds the GDOP law M40: sigma_theta = c sigma_tau / (sqrt(4.5) R))")
    for si, snr in enumerate(snrs):
        d_ = dtau[si].ravel()
        s_tau = float(np.std(d_))
        s_tau_rob = float(np.median(np.abs(d_ - np.median(d_))) / 0.6745)
        pred = np.rad2deg(C * s_tau / (np.sqrt(4.5) * R))
        pred_rob = np.rad2deg(C * s_tau_rob / (np.sqrt(4.5) * R))
        gcc_rmse, gcc_se = rmse_se(errs["GCC-PHAT (cheap)"][si])
        print(f"  SNR {snr:>3} dB: sigma_tau {s_tau*1e6:8.3f} us "
              f"(robust {s_tau_rob*1e6:7.3f} us) -> M40 predicts "
              f"{pred:7.3f} deg (robust {pred_rob:6.3f} deg); "
              f"measured GCC RMSE {gcc_rmse:7.3f} +-{gcc_se:5.3f} deg; "
              f"CRB {crb[si]:6.4f} deg; ratio to CRB {gcc_rmse/crb[si]:7.2f}")

    print("\n==== ARE THE THREE PER-PAIR TDOA ERRORS INDEPENDENT? ====")
    print("  (M37) and hence the simple GDOP law (M40) assume Cov(dtau) = sigma_tau^2 I.")
    print("  With M = 3 microphones there are only TWO independent delays, and all three")
    print("  pairwise correlations are computed from the same three channels, so the")
    print("  assumption is suspect. Below: the empirical correlation matrix of the")
    print("  per-pair TDOA errors (pairs 1-2, 1-3, 2-3), and the azimuth s.d. predicted")
    print("  by the GENERAL expression (M36) with the measured covariance substituted,")
    print("  against the simple isotropic form (M40).")
    rows_A = np.array([MIC_XY[i] - MIC_XY[j]
                       for i in range(3) for j in range(i + 1, 3)])
    Ap = np.linalg.pinv(rows_A)
    th_g = np.deg2rad(np.arange(0, 360, 0.25))
    e_g = np.stack([-np.sin(th_g), np.cos(th_g)])
    for si, snr in enumerate(snrs):
        D = dtau[si].reshape(-1, 3)
        Cm = np.cov(D, rowvar=False)
        Rm = Cm / np.sqrt(np.outer(np.diag(Cm), np.diag(Cm)))
        var_g = C ** 2 * np.einsum('in,ij,jn->n', e_g, Ap @ Cm @ Ap.T, e_g)
        s_gen = np.rad2deg(np.sqrt(var_g))
        s_iso = np.rad2deg(C * np.sqrt(np.mean(np.diag(Cm))) / (np.sqrt(4.5) * R))
        gcc_rmse = rmse_se(errs["GCC-PHAT (cheap)"][si])[0]
        print(f"  SNR {snr:>3} dB  corr(12,13) {Rm[0,1]:+6.3f}  corr(12,23) {Rm[0,2]:+6.3f}"
              f"  corr(13,23) {Rm[1,2]:+6.3f}")
        print(f"            (M40) isotropic prediction {s_iso:7.3f} deg | "
              f"(M36) with measured Cov: mean {s_gen.mean():7.3f} deg, "
              f"range {s_gen.min():6.3f}-{s_gen.max():6.3f} deg | "
              f"measured RMSE {gcc_rmse:7.3f} deg")

    print("\n==== HOST COMPUTE (ms per estimate; minimum over 9 interleaved rounds) ====")
    print("  x86 host, reference NumPy implementation. NOT an algorithmic complexity")
    print("  ratio and NOT transferable to the MCU -- see measure_compute() docstring.")
    print("  'spread' is max-min across rounds, i.e. how much the host interfered.")
    base = times["GCC-PHAT (cheap)"][0]
    for m, (t, sp) in times.items():
        print(f"  {m:<24} {t:8.3f} ms  (spread {sp:6.3f} ms)  "
              f"({t/base:6.2f}x GCC-PHAT measured)")
    print("  analytical FLOP model (math_model.md 7.2-7.3), the algorithmic comparison:")
    for m, fl in flops.items():
        print(f"  {m:<24} {fl:8.3f} MFLOP ({fl/flops['GCC-PHAT (cheap)']:6.3f}x "
              f"GCC-PHAT predicted)")
    print(f"\nFigures written to: {OUTDIR}")
