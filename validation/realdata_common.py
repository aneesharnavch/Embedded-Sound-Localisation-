"""
realdata_common.py
==================
Shared loaders, constants and publication figure style for the REAL-DATA analysis
scripts (`analyze_real.py`, `verify_sims.py`).

Everything in here reads files that exist on disk. Nothing is synthesised. Where a
quantity is derived rather than measured (for example the geometric quadrant table),
the loader says so in its docstring and the caller labels the result accordingly.

Conventions established by the forensics in `analyze_real.py`:

  * The calibration/idle CSVs store `Mic Value` = 2 x (raw 12-bit ADC code). Every
    recorded value is even and the greatest common divisor of the value differences is
    exactly 2. This is the signature of the Arduino-ESP32 `analogReadResolution(13)`
    setting, which left-shifts the native 12-bit conversion by one bit. All loaders
    here return RAW 12-BIT CODES (value / 2) so that every dataset in the project is on
    one common scale, the same scale as the three-channel `Triple Mic Samples` clips,
    which are stored unscaled.

  * ADC full scale is 4095 codes. One code (1 LSB) is the quantisation step.
"""

from __future__ import annotations

import glob
import hashlib
import os
import re
import sys

import numpy as np

# ----------------------------------------------------------------------------------
# Paths
# ----------------------------------------------------------------------------------
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

CAL_DIR = os.path.join(ROOT, "Microphone calibration data", "Microphone calibration data")
CAL_DIST = os.path.join(CAL_DIR, "Distance based sample_s")
CAL_WAVE = os.path.join(CAL_DIR, "Waveform based Sample_s")
CAL_IDLE = os.path.join(CAL_DIR, "Idle sample_s", "readings")
FB_DIR = os.path.join(ROOT, "Microphone feedback with respect to Frequency and Distance",
                      "Microphone feedback with respect to Frequency and Distance")
TRIPLE_DIR = os.path.join(ROOT, "Triple Mic Samples")
QUAD_DIR = os.path.join(ROOT, "Quadrant Based Estimations")
IDLE_XLSX_DIR = os.path.join(ROOT, "idle mic data")
FILTER_DIR = os.path.join(ROOT, "Filter alogrithims test")

FIGDIR = os.path.join(HERE, "figs")
os.makedirs(FIGDIR, exist_ok=True)

# ----------------------------------------------------------------------------------
# Measured hardware constants (see analyze_real.py section 1/2 for the evidence)
# ----------------------------------------------------------------------------------
ADC_BITS = 12
ADC_FULLSCALE = 2 ** ADC_BITS - 1        # 4095 codes
CAL_SCALE = 2                            # stored value = 2 x raw 12-bit code
FS_NOMINAL = 1000.0                      # Hz, the logger's intended rate
C_SOUND = 343.0                          # m/s, the constant used by the quadrant table
SEED = 7                                 # fixed RNG seed, matches doa_benchmark

# Excitation grid actually present on disk
CAL_FREQS_KHZ = (1, 5, 10, 15, 20)
CAL_DISTS_CM = (15, 50, 100, 150, 200, 250, 300)
CAL_WAVEFORMS = ("sine", "square", "triangle")


# ----------------------------------------------------------------------------------
# Logging: everything printed also lands in the run log, verbatim.
# ----------------------------------------------------------------------------------
class Tee:
    """Duplicate stdout into a UTF-8 log file so every printed number is citable."""

    def __init__(self, path, mode="w"):
        self.file = open(path, mode, encoding="utf-8", newline="\n")
        self.stdout = sys.stdout

    def write(self, s):
        self.stdout.write(s)
        self.file.write(s)

    def flush(self):
        self.stdout.flush()
        self.file.flush()

    def close(self):
        self.file.close()


def rule(title, char="="):
    print("\n" + char * 88)
    print(title)
    print(char * 88)


def caption(figname, text):
    """Record a self-contained caption for a figure into the run log."""
    print(f"\n[FIGURE] {figname}")
    print(f"[CAPTION] {text}")


# ----------------------------------------------------------------------------------
# Figure style: colour-blind-safe (Okabe-Ito), greyscale-safe via marker/linestyle,
# readable at single-column width, no decorative chrome.
# ----------------------------------------------------------------------------------
OKABE_ITO = ["#000000", "#E69F00", "#56B4E9", "#009E73",
             "#F0E442", "#0072B2", "#D55E00", "#CC79A7"]
MARKERS = ["o", "s", "^", "D", "v", "P", "X", "*"]
LINESTYLES = ["-", "--", "-.", ":", (0, (3, 1, 1, 1)), (0, (5, 1))]


def use_paper_style():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from cycler import cycler
    plt.rcParams.update({
        "figure.dpi": 110,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "font.size": 8.5,
        "axes.titlesize": 9,
        "axes.labelsize": 8.5,
        "legend.fontsize": 7.5,
        "xtick.labelsize": 7.5,
        "ytick.labelsize": 7.5,
        "axes.grid": True,
        "grid.alpha": 0.25,
        "grid.linewidth": 0.5,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "lines.linewidth": 1.4,
        "lines.markersize": 3.6,
        "legend.frameon": False,
        "axes.prop_cycle": cycler(color=OKABE_ITO[:7]),
        "image.cmap": "cividis",          # perceptually uniform, colour-blind safe
    })
    return plt


def savefig(fig, name, dpi=300):
    path = os.path.join(FIGDIR, name)
    fig.savefig(path, dpi=dpi)
    import matplotlib.pyplot as plt
    plt.close(fig)
    return path


# ----------------------------------------------------------------------------------
# Loaders
# ----------------------------------------------------------------------------------
_CAL_RE = re.compile(r"(sine|square|triangle)_wave_(\d+)k(?:_(\d+))?\.csv$", re.I)


def parse_cal_name(path):
    """Return (waveform, freq_khz, dist_cm) for a calibration CSV, or None."""
    m = _CAL_RE.search(os.path.basename(path))
    if not m:
        return None
    wf, khz, dist = m.group(1).lower(), int(m.group(2)), m.group(3)
    if dist is None:                       # the FB copy omits the distance in the name
        parent = os.path.basename(os.path.dirname(os.path.dirname(path)))
        dist = re.sub(r"[^0-9]", "", parent)
    return wf, khz, int(dist)


def load_cal_csv(path):
    """Load one calibration CSV.

    Returns (t_ms, code) where `t_ms` is the logger's time column in milliseconds and
    `code` is the RAW 12-bit ADC code (the stored `Mic Value` divided by CAL_SCALE).
    """
    a = np.loadtxt(path, delimiter=",", skiprows=1)
    t_ms = a[:, 0].astype(float)
    code = a[:, 1].astype(float) / CAL_SCALE
    return t_ms, code


def list_calibration(unique_only=True):
    """List the excitation recordings.

    `Distance based sample_s`, `Waveform based Sample_s` and the whole
    `Microphone feedback with respect to Frequency and Distance` folder are three
    re-organised copies of ONE set of 105 files (verified byte-identical by MD5 in
    `analyze_real.py`). With `unique_only=True` each physical recording is returned once,
    taken from the `Distance based sample_s` copy.
    """
    files = sorted(glob.glob(os.path.join(CAL_DIST, "**", "*.csv"), recursive=True))
    out = []
    for f in files:
        meta = parse_cal_name(f)
        if meta:
            out.append((meta[0], meta[1], meta[2], f))
    if unique_only:
        return out
    for base in (CAL_WAVE, FB_DIR):
        for f in sorted(glob.glob(os.path.join(base, "**", "*.csv"), recursive=True)):
            meta = parse_cal_name(f)
            if meta:
                out.append((meta[0], meta[1], meta[2], f))
    return out


IDLE_FILES = {
    1: os.path.join(CAL_IDLE, "mic#1_raw_dile_data.csv"),
    2: os.path.join(CAL_IDLE, "mic#2_raw_idle_data.csv"),
    3: os.path.join(CAL_IDLE, "mic#3_raw_idle_data.csv"),
}


def load_idle(mic):
    """Load one 60 s idle (no source) recording as (t_ms, raw 12-bit code)."""
    return load_cal_csv(IDLE_FILES[mic])


def load_triple(k):
    """Load `Triple Mic Samples/sample_<k>.xlsx`.

    Returns (X, label) with X of shape (3, 30) in RAW 12-bit ADC codes (these files are
    stored unscaled) and `label` the position string in header cell D1, e.g. '(0,15)'.
    """
    import openpyxl
    path = os.path.join(TRIPLE_DIR, f"sample_{k}.xlsx")
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    label = rows[0][3]
    X = np.array([[r[0], r[1], r[2]] for r in rows[1:]
                  if r[0] is not None], dtype=float).T
    wb.close()
    return X, str(label)


def load_all_triple():
    """Return a list of (k, label, X) for all 25 clips, in file-number order."""
    out = []
    for k in range(1, 26):
        X, label = load_triple(k)
        out.append((k, label, X))
    return out


def parse_position(label):
    """'(-15,30)' -> (-15.0, 30.0) in centimetres."""
    m = re.findall(r"-?\d+(?:\.\d+)?", label)
    return float(m[0]), float(m[1])


def load_quadrant(i):
    """Load `Quadrant Based Estimations/quadrant_<i>.csv` -> (x, y, t) arrays in m, m, s.

    NOTE: this file is a COMPUTED geometric lookup table, not a measurement. See
    `analyze_real.py` section 8 for the exact closed form it satisfies to 3e-11 s.
    Rows whose `t` field is blank (the x = -0.0 column, where the true value is exactly
    zero and the writer emitted an empty field) are dropped.
    """
    path = os.path.join(QUAD_DIR, f"quadrant_{i}.csv")
    xs, ys, ts = [], [], []
    with open(path, "r", encoding="utf-8") as fh:
        next(fh)
        for line in fh:
            p = line.strip().split(",")
            if len(p) != 3 or p[2] == "":
                continue
            xs.append(float(p[0])); ys.append(float(p[1])); ts.append(float(p[2]))
    return np.array(xs), np.array(ys), np.array(ts)


def md5(path, chunk=1 << 20):
    h = hashlib.md5()
    with open(path, "rb") as fh:
        while True:
            b = fh.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


# ----------------------------------------------------------------------------------
# The four candidate filters the author trialled, reconstructed from the scripts in
# `Filter alogrithims test/`. Each original script applies its filter to
# `np.random.randn(1000)`, i.e. to synthetic noise and never to the recorded data;
# these functions return the impulse responses so `analyze_real.py` can run them on the
# REAL recordings.
# ----------------------------------------------------------------------------------
def filter_bank():
    """Return {name: (h, description)} for the four candidate filters, as designed.

    Note that the four scripts do NOT use the same convention for `f_c = 0.1`:
      * A1 writes `np.sinc(2 * f_c * n)`, in which f_c is in cycles per sample, so its
        cutoff is 0.1 * fs = 100 Hz at the measured rate (0.2 x Nyquist);
      * A2 passes f_c to `scipy.signal.firwin`, which takes a fraction of NYQUIST, so
        its cutoff is 0.05 * fs = 50 Hz (0.1 x Nyquist).
    The two designs therefore differ by a factor of two in cutoff even though both
    scripts write 0.1. Every response metric in `analyze_real.py` is measured relative to
    each filter's own -3 dB point so that the comparison is fair.
    """
    from scipy.signal import firwin

    # A1: windowed-sinc, 21 taps, Hamming, fc = 0.1 x Nyquist, DC-normalised
    n = np.arange(21)
    h1 = np.sinc(2 * 0.1 * (n - (21 - 1) / 2)) * np.hamming(21)
    h1 = h1 / np.sum(h1)

    # A2: firwin Kaiser(beta = 8.6), 51 taps, fc = 0.1 x Nyquist
    h2 = firwin(51, cutoff=0.1, window=("kaiser", 8.6), pass_zero=True)

    # A3: frequency-sampling via inverse DFT of a 51-point rectangular mask
    N = 51
    fr = np.zeros(N, dtype=complex)
    passband_end = int(0.2 * (N // 2))            # = 5 bins
    fr[:passband_end] = 1
    fr[-passband_end:] = 1
    h3 = np.real(np.fft.ifft(fr))                 # NOT shifted -> non-causal wrap-around

    # A4: Gaussian window, 21 taps, sigma = 3 samples, area-normalised
    nn = np.arange(21) - (21 - 1) / 2
    h4 = np.exp(-0.5 * (nn / 3.0) ** 2)
    h4 = h4 / np.sum(h4)

    return {
        "A1 windowed-sinc (Hamming, 21 tap)":
            (h1, "sinc x Hamming, N=21, cutoff 0.1 fs, DC-normalised; linear phase"),
        "A2 Kaiser firwin (51 tap)":
            (h2, "firwin Kaiser beta=8.6, N=51, cutoff 0.05 fs; linear phase"),
        "A3 frequency-sampling (51 tap)":
            (h3, "inverse DFT of a rectangular mask, N=51, no fftshift; NOT linear phase"),
        "A4 Gaussian window (21 tap)":
            (h4, "Gaussian sigma=3 samples, N=21, area-normalised; linear phase"),
    }
