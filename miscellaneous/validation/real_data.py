"""
real_data.py
============
The bridge from simulation to the bench. It runs REAL recorded multichannel clips through
the SAME estimators used on simulated data (doa_benchmark), so the hardware-validation
numbers in the paper come from identical code -- the reviewer-proof link the resubmission
needs.

Nothing here is hardware-specific beyond file I/O: record N-channel clips on the device (or
capture the raw ADC stream to WAV/CSV), name each file with its ground-truth azimuth, drop
them in a folder, and this produces the per-method RMSE / median / p90 table + an error CDF
that overlays directly on the simulated fig_error_cdf.png.

FILENAME CONVENTION (ground truth is encoded in the name; everything after is free text):
    az<+/-DDD>_<anything>.wav      e.g.  az+030_room1_speech.wav   ->  true azimuth +30 deg
    az000_damped_noise.wav         ->  0 deg
CSV clips: same naming, shape (num_samples, num_channels), one column per mic, in MIC_XY order.

Run:  py -3.14 real_data.py <folder_of_clips>
      py -3.14 real_data.py --latency <esp32_timing_log.csv>
"""

import os
import re
import sys
import glob
import numpy as np
import matplotlib.pyplot as plt
import doa_benchmark as d

try:
    from scipy.io import wavfile
except Exception:                                    # scipy optional for CSV-only use
    wavfile = None

_AZ_RE = re.compile(r"az([+-]?\d{1,3})", re.IGNORECASE)

METHODS = {
    "Proposed (gated)":  d.est_proposed,
    "GCC-PHAT (cheap)":  d.est_gccphat_ls,
    "SRP-PHAT (strong)": lambda X: d.est_srp_phat(X)[0],
    "MUSIC (subspace)":  d.est_music,
}


def true_azimuth_from_name(path):
    """Parse the ground-truth azimuth (deg) encoded in the filename, or None."""
    m = _AZ_RE.search(os.path.basename(path))
    return float(m.group(1)) if m else None

def load_multichannel(path):
    """Load a clip as an (M, N) float array (M mics, N samples), whatever the container.

    Returns (X, fs). WAV is read as (N, M) and transposed; CSV/NPY as (N, M) or (M, N)
    (auto-oriented so the SHORTER axis is the mic axis, since M << N in any real clip).
    """
    ext = os.path.splitext(path)[1].lower()
    if ext == ".wav":
        if wavfile is None:
            raise RuntimeError("scipy needed to read WAV files")
        fs, data = wavfile.read(path)
        X = data.T.astype(float)
        if np.issubdtype(data.dtype, np.integer):    # normalize PCM to [-1, 1]
            X /= np.iinfo(data.dtype).max
    elif ext in (".csv", ".txt"):
        X = np.loadtxt(path, delimiter=",").astype(float); fs = d.FS
    elif ext == ".npy":
        X = np.load(path).astype(float); fs = d.FS
    else:
        raise ValueError(f"unsupported clip format: {ext}")
    if X.ndim == 1:
        raise ValueError(f"{path}: single channel; need >= 2 mics")
    if X.shape[0] > X.shape[1]:                       # orient so axis 0 is mics
        X = X.T
    return X, fs

def estimate_all(X, fs):
    """Run every estimator on one clip; return {method: azimuth_deg}."""
    out = {}
    for name, fn in METHODS.items():
        try:
            out[name] = float(fn_with_fs(fn, X, fs))
        except Exception as e:
            out[name] = np.nan
            print(f"    ! {name} failed: {e}")
    return out

def fn_with_fs(fn, X, fs):
    """Call an estimator, passing fs when it accepts one (lambdas don't)."""
    try:
        return fn(X, fs=fs)
    except TypeError:
        return fn(X)


def evaluate_dir(folder):
    """Evaluate every labelled clip in a folder; print a per-method accuracy table."""
    clips = sorted(sum([glob.glob(os.path.join(folder, f"*{e}"))
                        for e in (".wav", ".csv", ".txt", ".npy")], []))
    labelled = [(p, true_azimuth_from_name(p)) for p in clips]
    labelled = [(p, t) for p, t in labelled if t is not None]
    if not labelled:
        print(f"No labelled clips (az<deg> in filename) found in {folder}")
        return
    print(f"Found {len(labelled)} labelled clips in {folder}\n")

    errs = {m: [] for m in METHODS}
    for path, true_deg in labelled:
        X, fs = load_multichannel(path)
        est = estimate_all(X, fs)
        print(f"  {os.path.basename(path):<32} true={true_deg:+6.1f}  " +
              "  ".join(f"{m.split()[0]}={est[m]:+6.1f}" for m in METHODS))
        for m in METHODS:
            if np.isfinite(est[m]):
                errs[m].append(abs(d.ang_err(est[m], true_deg)))

    print("\n==== REAL-DATA ACCURACY (deg) ====")
    print(f"  {'method':<20} {'N':>4} {'median':>8} {'p90':>8} {'RMSE':>8}")
    for m in METHODS:
        e = np.array(errs[m])
        if e.size:
            print(f"  {m:<20} {e.size:>4} {np.median(e):>8.2f} "
                  f"{np.percentile(e,90):>8.2f} {np.sqrt(np.mean(e**2)):>8.2f}")

    plt.figure(figsize=(5.4, 4))
    for m in METHODS:
        e = np.sort(np.array(errs[m]))
        if e.size:
            plt.plot(e, np.linspace(0, 1, e.size), lw=2, label=m)
    plt.xlabel("Absolute angular error (deg)"); plt.ylabel("CDF")
    plt.title("Measured angular-error CDF (real hardware)")
    plt.legend(); plt.grid(alpha=.3)
    plt.tight_layout()
    out = os.path.join(d.OUTDIR, "fig_real_error_cdf.png")
    plt.savefig(out, dpi=200); plt.close()
    print(f"\nFigure written to: {out}")


def summarize_latency(csv_path):
    """Summarize a device timing log (one column of per-estimate microseconds).

    On the ESP32-S3, log esp_timer_get_time() deltas around the estimator to a CSV, pull it
    off the device, and run this. Replaces the draft's unsupported '10 us' with a measured
    distribution (mean / median / p95 / max) and a real-time headroom check vs the snapshot.
    """
    us = np.loadtxt(csv_path, delimiter=",").ravel().astype(float)
    snap_ms = 1e3 * d.SIG_LEN / d.FS
    print(f"On-device latency over {us.size} estimates (us):")
    print(f"  mean {us.mean():.1f}   median {np.median(us):.1f}   "
          f"p95 {np.percentile(us,95):.1f}   max {us.max():.1f}")
    print(f"  snapshot = {snap_ms:.1f} ms  ->  real-time budget used: "
          f"{100*us.mean()/1e3/snap_ms:.1f}% (mean)")


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "--latency":
        summarize_latency(sys.argv[2])
    elif len(sys.argv) >= 2:
        evaluate_dir(sys.argv[1])
    else:
        print(__doc__)
        print("\nNo folder given. Example:  py -3.14 real_data.py ./measurements/room1")
