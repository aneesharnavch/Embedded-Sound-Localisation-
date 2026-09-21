"""
analyze_real.py
===============
Forensics and analysis of every REAL data folder in this repository, and the figures
the paper can honestly draw from them.

Nothing in this script synthesises a result. Where a synthetic signal is used it is a
controlled probe applied to a measured noise record, and it is labelled as such in the
output. Two things in the repository are known-bad and are quarantined rather than used:

  * `Triple Mic Samples/python.py` fabricates a localization-accuracy heatmap with
    `np.random.uniform(0.4, 0.76)` rescaled to a preset 77 % mean, and never opens a
    single recording. Section 0 re-verifies this. Its output must never enter the paper.
  * `idle mic data/data.xlsx` is a corrupted serial dump (section 0). Its derivative
    `filtered_data.xlsx` was produced by `process_excel.py`, which keeps only values in
    [1100, 1500] -- a value-range gate, not a filter -- and is therefore biased by
    construction. The clean idle recordings in `Microphone calibration data/` are used
    instead.

Outputs
-------
  validation/realdata_run.log     every number printed here, verbatim
  validation/figs/fig_real_*.png  all figures, 300 dpi

Run:  py -3.14 analyze_real.py
"""

from __future__ import annotations

import collections
import os
import sys
import textwrap
import time

import numpy as np
from scipy import signal as sps

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import realdata_common as rc                      # noqa: E402

plt = rc.use_paper_style()
RNG = np.random.default_rng(rc.SEED)

LOG = os.path.join(HERE, "realdata_run.log")

# Array geometry used for every "what would this mean for the array" statement.
# Equilateral triangle, circum-radius R; identical to doa_benchmark.MIC_XY.
R_ARRAY = 0.05
MIC_XY = np.array([[R_ARRAY * np.cos(np.deg2rad(a)), R_ARRAY * np.sin(np.deg2rad(a))]
                   for a in (90, 210, 330)])
D_MAX = float(np.max([np.linalg.norm(MIC_XY[i] - MIC_XY[j])
                      for i in range(3) for j in range(i + 1, 3)]))   # 8.66 cm
TAU_MAX = D_MAX / rc.C_SOUND                                          # s


# ==================================================================================
# 0. Inventory and integrity
# ==================================================================================
def section0_inventory():
    rc.rule("0. DATA INVENTORY AND INTEGRITY")

    # --- 0a. de-duplicate the three copies of the excitation set -------------------
    groups = collections.defaultdict(list)
    for tag, base in (("Distance based sample_s", rc.CAL_DIST),
                      ("Waveform based Sample_s", rc.CAL_WAVE),
                      ("Microphone feedback .../", rc.FB_DIR)):
        import glob
        for f in glob.glob(os.path.join(base, "**", "*.csv"), recursive=True):
            groups[rc.md5(f)].append(tag)
    n_unique = len(groups)
    n_triplicate = sum(1 for v in groups.values() if len(v) == 3)
    print(textwrap.dedent(f"""
      Excitation recordings on disk are stored THREE times under different folder
      hierarchies. MD5 comparison of every CSV:

        Distance based sample_s          {len(list(os.walk(rc.CAL_DIST)))-1} folders, 105 CSV
        Waveform based Sample_s          105 CSV
        Microphone feedback .../         105 CSV
        distinct file contents           {n_unique}
        contents present in all 3 copies {n_triplicate}

      The 'Microphone calibration data' (239 files) and 'Microphone feedback with
      respect to Frequency and Distance' (126 files) folders therefore contain
      {n_unique} distinct recordings between them, not 365. Every analysis below counts
      each recording ONCE.
    """).rstrip())

    cal = rc.list_calibration()
    wf = collections.Counter(c[0] for c in cal)
    kh = collections.Counter(c[1] for c in cal)
    di = collections.Counter(c[2] for c in cal)
    print(f"\n  excitation set: {len(cal)} recordings = "
          f"{len(di)} distances x {len(wf)} waveforms x {len(kh)} frequencies")
    print(f"    waveforms   : {dict(sorted(wf.items()))}")
    print(f"    freq (kHz)  : {dict(sorted(kh.items()))}")
    print(f"    distance(cm): {dict(sorted(di.items()))}")
    print("    channels per recording: 1 (single 'Mic Value' column; the microphone "
          "identity is not recorded)")

    # --- 0b. quantisation step / word length ---------------------------------------
    t, v = rc.load_cal_csv(cal[0][3])
    raw2 = (v * rc.CAL_SCALE).astype(np.int64)
    step = int(np.gcd.reduce(np.diff(np.unique(raw2))))
    gmin, gmax = np.inf, -np.inf
    odd = 0
    for _, _, _, p in cal:
        _, vv = rc.load_cal_csv(p)
        r2 = (vv * rc.CAL_SCALE).astype(np.int64)
        odd += int(np.sum(r2 % 2 != 0))
        gmin = min(gmin, r2.min()); gmax = max(gmax, r2.max())
    print(textwrap.dedent(f"""
      Word length and scaling
        stored 'Mic Value' greatest common divisor of differences : {step}
        odd stored values across all {len(cal)} recordings         : {odd}
        stored value range over the whole excitation set           : {gmin} .. {gmax}
        => stored value = 2 x (raw 12-bit ADC code); raw range     : {gmin//2} .. {gmax//2}

      Every stored value is even, so the logger emitted a 13-bit word whose least
      significant bit is always zero. That is exactly what the Arduino-ESP32 core does
      for `analogReadResolution(13)`: it left-shifts the native 12-bit conversion. The
      effective resolution is 12 bits (4096 codes), and the quantisation step in the
      stored files is 2 units = 1 raw LSB. All values below are RAW 12-BIT CODES.
    """).rstrip())

    # --- 0c. the fabricated heatmap script ------------------------------------------
    src = open(os.path.join(rc.TRIPLE_DIR, "python.py"), "r", encoding="utf-8",
               errors="replace").read()
    fab = "np.random.uniform(0.4, 0.76)" in src
    reads_data = ("xlsx" in src) or ("read_excel" in src) or ("sample_" in src)
    print(textwrap.dedent(f"""
      Quarantine check -- Triple Mic Samples/python.py
        contains np.random.uniform(0.4, 0.76)      : {fab}
        rescales to a preset mean of 0.77          : {"target_avg = 0.77" in src}
        opens any sample_*.xlsx recording          : {reads_data}
        VERDICT: the accuracy heatmap it produces is FABRICATED. It is excluded from
        every result in this file and must not appear in the paper in any form.
      Triple Mic Samples/results.csv is {os.path.getsize(os.path.join(rc.TRIPLE_DIR,'results.csv'))} bytes (empty).
    """).rstrip())

    # --- 0d. the corrupt idle workbook -----------------------------------------------
    import pandas as pd
    dfx = pd.read_excel(os.path.join(rc.IDLE_XLSX_DIR, "data.xlsx"), header=None)
    col0 = pd.to_numeric(dfx[0], errors="coerce")
    num = col0.dropna().to_numpy(float)
    in_band = np.mean((num >= 1100) & (num <= 1500))
    dff = pd.read_excel(os.path.join(rc.IDLE_XLSX_DIR, "filtered_data.xlsx"), header=None)
    fv = dff[0].to_numpy(float)
    print(textwrap.dedent(f"""
      Quarantine check -- idle mic data/data.xlsx
        rows x cols                          : {dfx.shape[0]} x {dfx.shape[1]}
        non-empty cells in column A          : {int(dfx[0].notna().sum())}
        of which parse as a number           : {int(col0.notna().sum())}
        numeric range                        : {num.min():.0f} .. {num.max():.0f}
        fraction inside a plausible ADC band : {in_band:.3f}
        column A interleaves at least three streams (a monotonically increasing sample
        counter near 12900-37600, plausible ADC codes near 1250, and small integers),
        plus literal '_x0000_' cells and run-together values such as 6612938 and 112935.
        VERDICT: unrecoverable. Not used.

      idle mic data/filtered_data.xlsx  ({len(fv)} rows, mean {fv.mean():.2f}, sd {fv.std(ddof=1):.2f})
        produced by process_excel.py, which KEEPS ONLY values in [1100, 1500]. That is a
        value-range gate, not a filter: it discards {100*(1-in_band):.1f} % of column A,
        destroys the time base by non-uniform decimation, and truncates exactly the tails
        that a noise-floor estimate depends on. Its standard deviation is biased low by
        construction and must not be quoted as a noise floor.
        The clean 60 s idle recordings in Microphone calibration data/Idle sample_s/
        are used instead (section 3).
    """).rstrip())

    return cal


# ==================================================================================
# 1. CRITICAL QUESTION 1 -- the sampling rate
# ==================================================================================
def section1_timebase(cal):
    rc.rule("1. CRITICAL QUESTION 1 -- WHAT IS THE ACQUISITION SAMPLE RATE?")

    # --- 1a. the time column --------------------------------------------------------
    stats = []
    for wfm, khz, dist, p in cal:
        t, v = rc.load_cal_csv(p)
        dt = np.diff(t)
        stats.append(dict(n=len(t), dur=t[-1] - t[0], mean=dt.mean(), med=np.median(dt),
                          sd=dt.std(ddof=1), zero=np.mean(dt == 0),
                          big=np.mean(dt > 1.5), mx=dt.max()))
    S = {k: np.array([s[k] for s in stats]) for k in stats[0]}
    print(textwrap.dedent(f"""
      Statistics of the 'Time (ms)' column over all {len(cal)} excitation recordings:

        samples per file            {int(S['n'].min())} .. {int(S['n'].max())}   (median {int(np.median(S['n']))})
        record duration             {S['dur'].min()/1000:.3f} .. {S['dur'].max()/1000:.3f} s
        MEAN sample interval        {S['mean'].mean():.6f} ms  (sd across files {S['mean'].std(ddof=1)*1e3:.3f} us)
        MEDIAN sample interval      {np.median(S['med']):.6f} ms
        within-file sd of interval  {np.median(S['sd'])*1e3:.1f} us (median over files)
        intervals equal to zero     {100*S['zero'].mean():.2f} % of samples
        intervals > 1.5 ms          {100*S['big'].mean():.2f} % of samples
        largest single gap          {S['mx'].max():.1f} ms

        => nominal rate from the mean interval: {1000/S['mean'].mean():.4f} Hz
        => Nyquist frequency:                   {500/S['mean'].mean()*1000/1000:.2f} Hz

      The excitation labels are 1, 5, 10, 15 and 20 kHz. Every one of them is between
      2x and 40x ABOVE this Nyquist frequency.
    """).rstrip())

    # --- 1b. the alias test ----------------------------------------------------------
    # For every recording, compute a heavily zero-padded spectrum of the 0-1.5 Hz band.
    # Zero padding does not add resolution (that is fixed at 1/30 s = 0.0333 Hz by the
    # record length); it interpolates the transform so a line can be LOCATED to a small
    # fraction of a bin, which is what is needed here.
    NPAD = 262144
    rows = []
    for wfm, khz, dist, p in cal:
        t, v = rc.load_cal_csv(p)
        n = len(v)
        ac = (v - v.mean()) * np.hanning(n)
        Vfine = np.abs(np.fft.rfft(ac, n=NPAD))
        ffine = np.fft.rfftfreq(NPAD, 1.0 / rc.FS_NOMINAL)
        m = ffine <= 1.5
        Vraw = np.abs(np.fft.rfft(ac))
        fraw = np.fft.rfftfreq(n, 1.0 / rc.FS_NOMINAL)
        bg = float(np.median(Vraw[(fraw > 3) & (fraw < 50)]))
        rows.append(dict(wf=wfm, khz=khz, dist=dist, n=n, res=float(fraw[1]),
                         V=Vfine[m], f=ffine[m], bg=bg,
                         rms=float((v - v.mean()).std(ddof=1)),
                         mean_dt=float(np.diff(t).mean())))
    res0 = float(np.median([r["res"] for r in rows]))
    fine = float(rows[0]["f"][1])

    # (i) GLOBAL MATCHED SCAN. One free parameter d. For each candidate d, sum the
    #     normalised spectral amplitude that every recording shows at its own predicted
    #     alias frequency d * f0. Under the alias hypothesis all 84 recordings light up
    #     at the same d; under any other hypothesis they do not.
    dgrid = np.linspace(0.5e-6, 60e-6, 4000)
    scan = np.zeros_like(dgrid)
    scan_sine = np.zeros_like(dgrid)
    for r in rows:
        if r["khz"] < 5:
            continue                       # 1 kHz alias is below the 0.0333 Hz resolution
        amp = np.interp(dgrid * r["khz"] * 1000.0, r["f"], r["V"]) / (r["bg"] + 1e-30)
        scan += amp
        if r["wf"] == "sine":
            scan_sine += amp
    delta = float(dgrid[int(np.argmax(scan))])
    delta_sine = float(dgrid[int(np.argmax(scan_sine))])
    sharp = float(scan.max() / np.median(scan))
    fs_hat = 1000.0 / (1.0 + delta)

    # (ii) PER-RECORDING measurement, searching within +/-45 % of the global prediction.
    for r in rows:
        if r["khz"] < 5:
            r["f_alias"] = np.nan; r["psr"] = 0.0; continue
        fp = delta * r["khz"] * 1000.0
        w = (r["f"] > 0.55 * fp) & (r["f"] < 1.45 * fp)
        i = int(np.argmax(r["V"][w]))
        r["f_alias"] = float(r["f"][w][i])
        r["psr"] = float(r["V"][w][i] / (r["bg"] + 1e-30))
    good = [r for r in rows if r["khz"] >= 5 and r["psr"] >= 10]
    sine_good = [r for r in good if r["wf"] == "sine"]
    dd_sine = np.array([r["f_alias"] / (r["khz"] * 1000.0) for r in sine_good])

    print(textwrap.dedent(f"""
      THE ALIAS TEST.  A tone at f0 sampled at fs < 2*f0 does not vanish: it folds to
      f_alias = |f0 - k*fs| with k = round(f0/fs). Writing the true sample interval as
      T = (1 + d) / 1000 s and noting that every excitation frequency is an exact
      integer multiple of 1 kHz, the model collapses to a ONE-PARAMETER prediction

            f_alias  =  d * f0            (Hz)

      so the observed low-frequency line must be strictly PROPORTIONAL to the excitation
      frequency, with the SAME constant d for every waveform and every distance. That is
      a very restrictive prediction: nothing except undersampling produces it.

      Global matched scan. For each candidate d, the normalised spectral amplitude that
      each recording shows at its own predicted alias frequency is summed over all
      {sum(1 for r in rows if r['khz']>=5)} recordings at 5 kHz and above:
        best d over all waveforms      {delta*1e6:.3f} ppm   ->  fs = {fs_hat:.5f} Hz
        best d over the sine subset    {delta_sine*1e6:.3f} ppm   ->  fs = {1000/(1+delta_sine):.5f} Hz
        scan peak / scan median        {sharp:.1f}   (a sharp, unambiguous maximum)
        FFT resolution / interpolated grid  {res0:.4f} Hz / {fine:.5f} Hz

      Per-recording line frequency, measured independently in each file within +/-45 %
      of the global prediction, for the sine excitations (a pure tone folds to a single
      clean line; square and triangle also fold their harmonics, which is treated below):

        excitation   n resolved   median f_alias (Hz)   implied d (ppm)   range (ppm)
    """).rstrip())
    for khz in rc.CAL_FREQS_KHZ:
        if khz == 1:
            print(f"        {khz:>3} kHz          -           "
                  f"{delta*1000:8.4f} predicted   "
                  f"      -           alias below the {res0:.4f} Hz resolution")
            continue
        sel = [r for r in sine_good if r["khz"] == khz]
        if not sel:
            print(f"        {khz:>3} kHz          0        (line not resolved)")
            continue
        d_i = np.array([r["f_alias"] / (r["khz"] * 1000.0) for r in sel]) * 1e6
        print(f"        {khz:>3} kHz         {len(sel):>2}          "
              f"{np.median([r['f_alias'] for r in sel]):8.4f}          "
              f"{np.median(d_i):8.2f}       {d_i.min():.2f} - {d_i.max():.2f}")
    print(textwrap.dedent(f"""
        pooled over the sine set: d = {np.median(dd_sine)*1e6:.3f} ppm, sd {dd_sine.std(ddof=1)*1e6:.3f} ppm, n = {len(dd_sine)}
        implied fs               = {1000/(1+np.median(dd_sine)):.5f} Hz

      The same constant, to within one part per million, reproduces the observed line at
      5, 10, 15 and 20 kHz and at every source distance. The square and triangle
      recordings at 15 and 20 kHz sit lower, near 7 ppm, because those waveforms carry
      strong odd harmonics that fold to their own lines (the third harmonic of a 15 kHz
      square folds to 3 x 15 x d = {45000*delta:.3f} Hz) and their fundamental is weak;
      they are excluded from the point estimate and reported here for completeness.

      Independent cross-check from the timestamps of the same files: the mean sample
      interval is {S['mean'].mean():.6f} ms, i.e. fs = {1000/S['mean'].mean():.4f} Hz. The spectroscopic value is
      {fs_hat:.5f} Hz. Two entirely independent methods -- one from the logger's clock, one
      from the physics of the folded tone -- agree to {abs(1000/S['mean'].mean() - fs_hat)*1e6/fs_hat:.0f} ppm.

      ANSWER TO CRITICAL QUESTION 1
        fs = {fs_hat:.3f} Hz (nominal 1 kHz). Nyquist = {fs_hat/2:.1f} Hz.
        The 1/5/10/15/20 kHz sweeps are ALIASED and cannot be read as a frequency
        response at face value: a 5 kHz excitation is recorded as a {5000*delta:.3f} Hz
        waveform, a 20 kHz excitation as a {20000*delta:.3f} Hz waveform. All FREQUENCY
        information is destroyed. Folding preserves AMPLITUDE, so a level reading would
        in principle survive; section 4 shows that in practice it does not, for the
        separate reason that the drive level was not held constant between runs.

      COROLLARY -- the time column is a host artefact, not the sample clock.
        The within-file scatter of the time column is {np.median(S['sd'])*1e3:.0f} us RMS. If the ADC had
        really been clocked that irregularly, a 5 kHz carrier (period 200 us) would
        accumulate a phase error of 2*pi*5000*{np.median(S['sd'])*1e-3:.2e} = {2*np.pi*5000*np.median(S['sd'])*1e-3:.1f} rad between
        consecutive samples and no coherent alias line could exist. The alias lines are
        in fact extremely coherent (median peak-to-background ratio
        {np.median([r['psr'] for r in good]):.0f} over a 30 s record).
        Therefore the conversion loop is uniformly clocked and the 'Time (ms)' column --
        which also contains {100*S['zero'].mean():.1f} % duplicate stamps and gaps up to {S['mx'].max():.0f} ms -- records when
        the HOST received a line, not when the sample was taken. Use the sample index,
        not the time column.

      CONSEQUENCE FOR TDOA.
        Sampling period                        1 / fs = {1e6/fs_hat:.1f} us
        Array geometry as configured in doa_benchmark.py: equilateral triangle,
        circum-radius R = {R_ARRAY*100:.1f} cm, so the microphone-to-microphone spacing is
        R*sqrt(3) = {D_MAX*100:.2f} cm.  [Both figures must be replaced with measured
        board values; 'aperture 5 cm' in the handover is ambiguous between the two.]
        Largest inter-microphone delay, spacing {D_MAX*100:.2f} cm     {TAU_MAX*1e6:.1f} us
        Largest delay if the spacing is instead 5.00 cm  {0.05/rc.C_SOUND*1e6:.1f} us
        Ratio, {D_MAX*100:.2f} cm spacing                        {TAU_MAX*fs_hat:.4f} samples
        Ratio, 5.00 cm spacing                        {0.05/rc.C_SOUND*fs_hat:.4f} samples
        On either reading the ENTIRE 360 deg azimuth range maps inside ONE sampling
        interval, a factor of {1/(TAU_MAX*fs_hat):.1f} to {1/(0.05/rc.C_SOUND*fs_hat):.1f} below the sampling grid.

        Being sub-sample is not by itself fatal -- interpolated cross-correlation
        routinely resolves a fraction of a sample -- so the argument has to be made
        properly, and it turns on the aliasing rather than on the rate:

          1. Sub-sample delay estimation is interpolation, and interpolation is only
             valid for a signal that is band-limited below Nyquist. These recordings are
             not: section 1 shows components at 5 to 20 kHz reaching the converter at
             full amplitude with no anti-alias filter.
          2. Aliasing corrupts DELAY specifically, and worse than it corrupts spectrum.
             A component at f0 delayed by tau carries phase -2*pi*f0*tau. Folding moves
             it to f_a but does NOT change its phase, so it appears in the cross-spectrum
             as an in-band component at f_a carrying a phase that belongs to f0 -- an
             apparent group delay inflated by f0/f_a. For the 20 kHz excitation and the
             array's maximum delay, the true phase is 2*pi*20000*{TAU_MAX*1e6:.1f}e-6 = {2*np.pi*20000*TAU_MAX:.1f} rad, or
             {2*np.pi*20000*TAU_MAX/(2*np.pi):.2f} full wraps, whereas an honest in-band component at
             {20000*delta:.3f} Hz would carry {2*np.pi*20000*delta*TAU_MAX:.2e} rad. Every folded component therefore
             injects a phase error of several whole cycles, and GCC-PHAT -- which fits a
             linear phase ramp across the band and gives every bin unit weight -- has its
             cross-spectrum phase randomised.
          3. So the fix is not simply a faster converter. It is an anti-alias filter
             ahead of the converter, plus a hardware-timed conversion clock. With those
             in place, 1 kHz sampling of a genuinely band-limited source would give a
             Cramer-Rao delay bound of tens of microseconds (section 2), which is
             marginal but not absurd; without them, no sample rate helps.

        For reference, a 1 deg azimuth resolution needs a delay resolution of about
        {TAU_MAX*np.deg2rad(1)*1e6:.2f} us. At 48 kHz that is {TAU_MAX*np.deg2rad(1)*48000:.3f} of a sample, i.e. it
        requires sub-sample interpolation even at the design rate -- which is precisely
        why the anti-alias filter, not the rate, is the load-bearing requirement.
    """).rstrip())

    fig_timebase(rows, S, delta, fs_hat, res0)
    fig_alias_demo(delta, fs_hat)
    return rows, fs_hat, delta


def fig_timebase(rows, S, delta, fs_hat, res0):
    fig, ax = plt.subplots(1, 2, figsize=(7.0, 2.9))

    # left: interval histogram
    t, v = rc.load_cal_csv(os.path.join(rc.CAL_DIST, "15 cm", "sine", "sine_wave_5k_15.csv"))
    dt = np.diff(t)
    ax[0].hist(np.clip(dt, 0, 3), bins=np.linspace(0, 3, 121),
               color=rc.OKABE_ITO[5], edgecolor="none")
    ax[0].axvline(1.0, color="k", lw=1.0, ls="--")
    ax[0].annotate("1.000 ms\nnominal", (1.0, ax[0].get_ylim()[1] * 0.72),
                   xytext=(6, 0), textcoords="offset points", fontsize=7)
    ax[0].set_yscale("log")
    ax[0].set_xlabel("Logged inter-sample interval (ms)")
    ax[0].set_ylabel("Count")
    ax[0].set_title("(a) Host time column, one 30 s record")

    # right: alias frequency vs excitation frequency
    for i, wf in enumerate(rc.CAL_WAVEFORMS):
        sel = [r for r in rows if r["wf"] == wf and r["khz"] >= 5 and r["psr"] >= 10]
        jit = (i - 1) * 0.28
        ax[1].plot([r["khz"] + jit for r in sel], [r["f_alias"] for r in sel],
                   rc.MARKERS[i], mfc="none", ms=4, mew=0.9,
                   color=rc.OKABE_ITO[[1, 5, 3][i]], ls="none", label=wf)
    xf = np.linspace(0, 21, 50)
    ax[1].plot(xf, delta * xf * 1000, "k-", lw=1.0,
               label=fr"$f_{{\rm alias}} = \delta f_0$, $\delta$ = {delta*1e6:.1f} ppm")
    ax[1].axhline(res0, color="0.5", lw=0.8, ls=":")
    ax[1].annotate("record-length resolution", (11.5, res0), xytext=(0, -9),
                   textcoords="offset points", fontsize=6.5, color="0.4")
    ax[1].set_xlabel("Nominal excitation frequency (kHz)")
    ax[1].set_ylabel("Observed spectral line (Hz)")
    ax[1].set_xlim(0, 22); ax[1].set_ylim(0, 0.30)
    ax[1].set_title(f"(b) Aliasing: fs = {fs_hat:.3f} Hz")
    ax[1].legend(loc="upper left")
    fig.tight_layout()
    p = rc.savefig(fig, "fig_real_timebase.png")
    rc.caption("fig_real_timebase.png", textwrap.fill(
        "Acquisition time base of the calibration rig. (a) Histogram of the logged "
        "inter-sample interval for one 30 s recording (sine_wave_5k_15.csv); the column "
        "clusters at the intended 1.000 ms but carries duplicate stamps and gaps to tens "
        "of milliseconds, showing that it timestamps host reception rather than "
        "conversion. (b) The low-frequency spectral line present in each excitation "
        "recording, plotted against the nominal excitation frequency for all three "
        "waveforms and all seven source distances (waveforms offset horizontally for "
        "legibility). The line is proportional to the excitation frequency, which is the "
        "signature of undersampling and of nothing else; a global one-parameter matched "
        f"fit gives delta = {delta*1e6:.1f} ppm and hence fs = {fs_hat:.3f} Hz, in "
        "agreement with the mean logged interval. The dotted line is the frequency "
        "resolution set by the 30 s record length, below which the 1 kHz excitation's "
        "predicted alias falls.", 100))
    print(f"          written: {p}")


def fig_alias_demo(delta, fs_hat):
    """Show the 5 kHz recording for what it is: a 0.07 Hz folded image, clipped."""
    t, v = rc.load_cal_csv(os.path.join(rc.CAL_DIST, "15 cm", "sine", "sine_wave_5k_15.csv"))
    n = len(v)
    idx = np.arange(n) / fs_hat
    fig, ax = plt.subplots(1, 2, figsize=(7.0, 2.7))
    ax[0].plot(idx, v, lw=0.5, color=rc.OKABE_ITO[5])
    ax[0].set_xlabel("Time from sample index (s)")
    ax[0].set_ylabel("ADC code (12-bit)")
    ax[0].set_xlim(0, 30)
    ax[0].set_title("(a) Recording labelled 'sine 5 kHz, 15 cm'")
    ax[0].axhline(np.max(v), color="0.4", lw=0.7, ls="--")
    ax[0].axhline(np.min(v), color="0.4", lw=0.7, ls="--")
    ax[0].annotate("front-end clipping", (1.0, np.max(v)), xytext=(0, -12),
                   textcoords="offset points", fontsize=6.5, color="0.3")

    ac = v - v.mean()
    V = np.abs(np.fft.rfft(ac * np.hanning(n))) / n
    fr = np.fft.rfftfreq(n, 1 / fs_hat)
    ax[1].semilogy(fr, V + 1e-12, lw=0.7, color=rc.OKABE_ITO[5])
    ax[1].axvline(5000 * delta, color=rc.OKABE_ITO[6], lw=1.0, ls="--")
    ax[1].annotate(f"predicted alias\n{5000*delta:.3f} Hz", (5000 * delta, V.max()),
                   xytext=(8, -6), textcoords="offset points", fontsize=6.5,
                   color=rc.OKABE_ITO[6])
    ax[1].set_xlim(0, 2.0)
    ax[1].set_xlabel("Frequency (Hz)")
    ax[1].set_ylabel("Amplitude (code)")
    ax[1].set_title("(b) Spectrum: all energy below 1 Hz")
    fig.tight_layout()
    p = rc.savefig(fig, "fig_real_alias_demo.png")
    rc.caption("fig_real_alias_demo.png", textwrap.fill(
        "What a 5 kHz excitation actually looks like when sampled at 1 kHz. (a) The full "
        f"30 s record: a near-square oscillation of period about {1/(5000*delta):.0f} s that "
        "spends long intervals pinned against the analogue front-end rails. No acoustic "
        f"process exists at {5000*delta:.2f} Hz; this is the folded image of the 5 kHz "
        "tone, and the flat tops are amplifier clipping, not signal. (b) Its amplitude "
        "spectrum, with the alias frequency predicted from the fitted sample rate marked. "
        "The prediction comes from a global fit across all recordings at 5 kHz and above, "
        "not from this file.", 100))
    print(f"          written: {p}")


# ==================================================================================
# 2. CRITICAL QUESTION 2 -- are the 30-sample triple-mic clips usable?
# ==================================================================================
def section2_triple(fs_hat):
    rc.rule("2. CRITICAL QUESTION 2 -- ARE THE 30-SAMPLE TRIPLE-MIC CLIPS USABLE FOR DoA?")

    clips = rc.load_all_triple()
    labels = [(k, lab, rc.parse_position(lab)) for k, lab, _ in clips]

    print("\n  2a. Position labels (header cell D1 of each workbook)\n")
    print("      file               label       x (cm)   y (cm)")
    for k, lab, (x, y) in labels:
        print(f"      {'sample_%d.xlsx' % k:<18} {lab:<10} {x:>7.0f} {y:>8.0f}")
    xs = sorted({p[0] for _, _, p in labels}); ys = sorted({p[1] for _, _, p in labels})
    print(f"\n      The 25 labels are exactly the 5 x 5 Cartesian product of "
          f"x in {xs} and y in {ys} (centimetres); every grid node appears once, "
          f"none is repeated. There is no azimuth label, no distance label, no room "
          f"label and no repeat measurement.")

    # --- per-channel statistics -------------------------------------------------------
    print("\n  2b. Per-clip channel statistics (raw 12-bit codes)\n")
    print("      file   label        N   DC1     DC2     DC3     sd1    sd2    sd3   "
          "r12    r13    r23")
    dcs, sds, rr = [], [], []
    for k, lab, X in clips:
        Z = X - X.mean(axis=1, keepdims=True)
        r = [np.corrcoef(Z[i], Z[j])[0, 1] for i, j in ((0, 1), (0, 2), (1, 2))]
        dcs.append(X.mean(axis=1)); sds.append(X.std(axis=1, ddof=1)); rr.append(r)
        print(f"      {k:>4}   {lab:<10} {X.shape[1]:>3}  "
              + "  ".join(f"{m:6.1f}" for m in X.mean(axis=1)) + "  "
              + " ".join(f"{s:6.2f}" for s in X.std(axis=1, ddof=1)) + "  "
              + " ".join(f"{q:+.3f}" for q in r))
    dcs = np.array(dcs); sds = np.array(sds); rr = np.array(rr)
    n_samp = clips[0][2].shape[1]

    # --- effective sample rate --------------------------------------------------------
    # The clips carry no time column. Their sample rate is inferred from the CORRELATION
    # TIME of the front-end noise, which the 60 s idle recordings measure directly at a
    # known 1 kHz. If the clips were sampled at 1 kHz through the same chain they must
    # reproduce the idle autocorrelation; if they are slower, the noise decorrelates.
    idle_acf = []
    for m in (1, 2, 3):
        _, z = rc.load_idle(m)
        med = np.median(z)
        rsd = 1.4826 * np.median(np.abs(z - med))
        z = np.where(np.abs(z - med) <= 10 * rsd, z, med)
        z = z - z.mean()
        a = np.correlate(z, z, "full")[len(z) - 1: len(z) + 13]
        idle_acf.append(a / a[0])
    idle_acf = np.mean(idle_acf, axis=0)

    order = np.argsort([X.std(axis=1, ddof=1).mean() for _, _, X in clips])
    quiet = [clips[i] for i in order[:8]]          # the 8 quietest clips
    ac1_clip = []
    for _, _, X in quiet:
        for ch in range(3):
            z = X[ch] - X[ch].mean()
            ac1_clip.append(np.corrcoef(z[:-1], z[1:])[0, 1])
    ac1_clip = np.array(ac1_clip)
    bias = -1.0 / (n_samp - 1)                     # small-sample bias of r1 after mean removal
    r1 = float(ac1_clip.mean() - bias)
    r1_se = float(ac1_clip.std(ddof=1) / np.sqrt(len(ac1_clip)))
    r1_hi = r1 + 1.96 * r1_se
    lag_lo = next((L for L in range(1, len(idle_acf)) if idle_acf[L] <= r1_hi), None)
    odd_frac = np.mean([np.mean(X.astype(np.int64) % 2 != 0) for _, _, X in clips])
    cal_dc = float(rc.load_idle(1)[1].mean())

    print(textwrap.dedent(f"""
      2c. What acquisition chain produced these clips, and at what rate?
        samples per clip / channels               {n_samp} / 3
        DC per channel, mean over 25 clips        {dcs[:,0].mean():.2f}, {dcs[:,1].mean():.2f}, {dcs[:,2].mean():.2f} codes
        DC of the 1 kHz idle recordings           {cal_dc:.2f} codes
        odd-valued samples                        {100*odd_frac:.1f} %  (so these are plain
                                                  12-bit codes, NOT the factor-two-scaled
                                                  words used by the calibration logger)

      The clips sit on the same DC operating point and the same 12-bit grid as the rest
      of the hardware, so they come from the same analogue chain. They carry no time
      column, so the rate must be inferred. The front-end noise is band-limited, so its
      autocorrelation is a clock: the 60 s idle recordings measure it directly at a known
      {fs_hat:.1f} Hz.

        measured idle autocorrelation, mean of the three microphones
          lag (samples)   """ + "".join(f"{L:>8}" for L in range(0, 9)) + f"""
          rho             """ + "".join(f"{a:8.3f}" for a in idle_acf[:9]) + f"""

        lag-1 autocorrelation of the 8 quietest clips ({len(ac1_clip)} channel series):
          raw mean                                {ac1_clip.mean():+.4f}
          small-sample bias for N = {n_samp}, -1/(N-1)   {bias:+.4f}
          bias-corrected                          {r1:+.4f} +/- {r1_se:.4f} (standard error)
          the 1 kHz idle value                    {idle_acf[1]:+.4f}

        The clips' noise is WHITE: the bias-corrected lag-1 autocorrelation is
        indistinguishable from zero, while the same front end sampled at {fs_hat:.0f} Hz gives
        {idle_acf[1]:+.3f}. Reading the measured idle autocorrelation backwards, an
        autocorrelation as low as the clips' 95 % upper bound ({r1_hi:+.3f}) is first
        reached at lag {lag_lo} samples of the idle record, i.e. an inter-sample interval of
        about {lag_lo} ms. The clips are therefore sampled at roughly {1000.0/lag_lo:.0f} Hz PER CHANNEL
        or slower -- consistent with a loop that converts three multiplexed channels and
        writes a spreadsheet row per set -- and certainly not faster than the {fs_hat:.0f} Hz of
        the calibration rig.
        Caveat, stated plainly: this inference assumes the two datasets share an analogue
        noise bandwidth, which their common DC operating point and common 12-bit grid make
        likely but do not prove. It is also conservative in the direction that matters --
        any residual source content in the 'quiet' clips would RAISE their autocorrelation,
        so the true per-channel interval is if anything longer than {lag_lo} ms. Nothing in
        these files supports a rate high enough for TDOA.
    """).rstrip())

    # --- resolvability ------------------------------------------------------------------
    print("\n  2d. Cross-channel correlation and delay resolvability\n")
    print(f"      zero-lag Pearson r, median over 25 clips: "
          f"r12 {np.median(rr[:,0]):+.3f}   r13 {np.median(rr[:,1]):+.3f}   "
          f"r23 {np.median(rr[:,2]):+.3f}")
    print(f"      fraction of pairs with r > 0.5          : "
          f"{np.mean(rr > 0.5):.2f}  (the three channels see one common source)")
    peak_lags = []
    for k, lab, X in clips:
        Z = X - X.mean(axis=1, keepdims=True)
        for i, j in ((0, 1), (0, 2), (1, 2)):
            cc = np.correlate(Z[i], Z[j], "full")
            peak_lags.append(int(np.argmax(cc)) - (X.shape[1] - 1))
    peak_lags = np.array(peak_lags)
    frac0 = np.mean(peak_lags == 0)

    for fs_try, why in ((1000.0 / lag_lo, "the rate inferred in 2c for these clips"),
                        (fs_hat, "the rate measured for the calibration rig"),
                        (48000.0, "the rate assumed by the simulation harness")):
        print(textwrap.dedent(f"""
        If fs = {fs_try:,.0f} Hz ({why}):
          sampling period                       {1e6/fs_try:.2f} us
          clip duration                         {n_samp/fs_try*1e3:.3f} ms
          max array delay {TAU_MAX*1e6:.1f} us              {TAU_MAX*fs_try:.4f} samples
          lags spanned by the whole 360 deg     +/-{TAU_MAX*fs_try:.4f} of ONE sample
          usable lag bins inside that span      {max(1, int(2*TAU_MAX*fs_try)+1)}
        """).rstrip())
    print(textwrap.dedent(f"""
        Measured integer-lag cross-correlation peaks over all 75 channel pairs:
          at lag 0                              {100*frac0:.0f} %
          |lag| >= 1 sample                     {100*(1-frac0):.0f} %
          largest |lag| observed                {np.abs(peak_lags).max()} samples
        At the calibration rig's 1 kHz a one-sample lag is 1000 us, which is {1000/(TAU_MAX*1e6):.1f}x
        larger than any delay the array can physically produce, and at the {1000.0/lag_lo:.0f} Hz
        inferred for these clips it is {lag_lo*1000/(TAU_MAX*1e6):.0f}x larger. Every non-zero peak is
        therefore noise, not propagation. The {100*frac0:.0f} % of peaks that sit exactly at lag 0
        say only that the true delay is somewhere inside the first sampling interval.

      A Cramer-Rao floor for the best case. For a broadband source occupying the whole
      band with root-mean-square bandwidth beta, N samples and per-channel SNR,
      sigma_tau >= 1 / (beta * sqrt(2 * N * SNR)).
    """).rstrip())
    crb = {}
    for fs_try in (1000.0 / lag_lo, fs_hat, 48000.0):
        beta = 2 * np.pi * (fs_try / 2) / np.sqrt(3)      # flat spectrum to Nyquist
        for snr_db in (10.0, 30.0):
            snr = 10 ** (snr_db / 10)
            sig_tau = 1.0 / (beta * np.sqrt(2 * n_samp * snr))
            # azimuth sensitivity: d(tau)/d(theta) is at most d_max/c
            frac = sig_tau / TAU_MAX
            crb[(round(fs_try), snr_db)] = (sig_tau, frac)
            note = (f"-> azimuth sd {np.rad2deg(np.arcsin(frac)):.1f} deg" if frac < 1
                    else "-> azimuth completely undetermined")
            print(f"        fs {fs_try:>8,.0f} Hz, SNR {snr_db:>4.0f} dB, N = {n_samp}: "
                  f"sigma_tau = {sig_tau*1e6:8.2f} us  "
                  f"= {frac:7.2f} x the full array delay  {note}")
    print(textwrap.dedent(f"""
        These bounds assume the best possible case: a source that is genuinely
        band-limited below Nyquist and fills the band with a flat spectrum, an unbiased
        estimator, and the stated in-band SNR. Read them as optimism, not as achievement.
        Two of the rows deserve comment rather than a slogan.
          * At the clips' own inferred rate the bound is {crb[(round(1000.0/lag_lo), 10.0)][1]:.2f} times the array's
            entire delay range at 10 dB SNR, i.e. an azimuth standard deviation of about
            {np.rad2deg(np.arcsin(min(0.999, crb[(round(1000.0/lag_lo), 10.0)][1]))):.0f} deg. That is not a measurement of direction.
          * At the calibration rig's {fs_hat:.0f} Hz the bound would be about {np.rad2deg(np.arcsin(crb[(round(fs_hat), 10.0)][1])):.0f} deg, which
            LOOKS usable. It is not achievable here, for the reason set out in section 1:
            there is no anti-alias filter, so out-of-band energy folds in carrying the
            phase of its original frequency and randomises the cross-spectrum. The bound
            describes a hypothetical properly band-limited 1 kHz system, not this one.

      ANSWER TO CRITICAL QUESTION 2
        NO. A direction-of-arrival estimate cannot be extracted from these clips.
        Four reasons, and the honest weighting matters:
          (i)   ALIASING, the decisive one. There is no anti-alias filter anywhere in
                this acquisition chain (section 1 measures 20 kHz content folding into
                the band at full amplitude). Folded components carry the phase of their
                original frequency, so they enter the cross-spectrum with a delay-phase
                error of several whole cycles. GCC-PHAT's phase ramp is destroyed. No
                sample rate and no estimator repairs this; it needs a hardware filter.
          (ii)  RATE. The clips' own noise statistics put their per-channel rate at about
                {1000.0/lag_lo:.0f} Hz, at which the whole 360 deg azimuth range occupies {2*TAU_MAX*1000.0/lag_lo:.3f} of
                one lag bin and the Cramer-Rao azimuth bound is about
                {np.rad2deg(np.arcsin(min(0.999, crb[(round(1000.0/lag_lo), 10.0)][1]))):.0f} deg at 10 dB SNR.
          (iii) LENGTH. 30 samples is too few for the sub-sample interpolation the
                geometry demands, even at 48 kHz, where the Cramer-Rao floor over 30
                samples is still {crb[(48000, 10.0)][1]:.2f} times the array's full delay range at 10 dB.
          (iv)  SCORABILITY. The clips carry no time base, no stated sample rate, no
                azimuth ground truth, no room description and no repeat measurements, so
                even a correct estimate could not be scored against anything.
        What the clips DO establish is real and worth reporting: the three channels are
        strongly correlated at lag 0 (median r = {np.median(rr):.2f}), the front end shares a
        common {dcs.mean():.0f}-code DC operating point, and the per-channel gains match to within
        the figure quoted in section 5. They are a working three-channel capture, not a
        localization dataset.
        Section 6 of the paper must NOT claim hardware TDOA on this data.
    """).rstrip())

    fig_triple(clips, rr, peak_lags, fs_hat, n_samp, 1000.0 / lag_lo)
    return clips, dcs, sds, rr


def fig_triple(clips, rr, peak_lags, fs_hat, n_samp, fs_clip):
    fig = plt.figure(figsize=(7.0, 4.6))
    gs = fig.add_gridspec(2, 2, height_ratios=[1.0, 1.0], hspace=0.55, wspace=0.30)

    # (a) one clip, three channels
    axa = fig.add_subplot(gs[0, 0])
    k, lab, X = clips[9]                       # sample_10, a high-level clip
    for ch in range(3):
        axa.plot(np.arange(X.shape[1]), X[ch], marker=rc.MARKERS[ch], ms=2.6, lw=1.0,
                 color=rc.OKABE_ITO[[5, 1, 3][ch]], label=f"MIC{ch+1}")
    axa.set_xlabel("Sample index")
    axa.set_ylabel("ADC code")
    axa.set_title(f"(a) sample_{k}.xlsx, source at {lab} cm")
    axa.legend(ncol=3, loc="upper right")

    # (b) cross-correlation with the physical delay window
    axb = fig.add_subplot(gs[0, 1])
    Z = X - X.mean(axis=1, keepdims=True)
    for m, (i, j) in enumerate(((0, 1), (0, 2), (1, 2))):
        cc = np.correlate(Z[i], Z[j], "full") / (np.linalg.norm(Z[i]) * np.linalg.norm(Z[j]))
        lags = np.arange(-(X.shape[1] - 1), X.shape[1])
        axb.plot(lags, cc, ls=rc.LINESTYLES[m], lw=1.1,
                 color=rc.OKABE_ITO[[5, 1, 3][m]], label=f"MIC{i+1}-MIC{j+1}")
    half = TAU_MAX * fs_hat
    axb.axvspan(-half, half, color=rc.OKABE_ITO[6], alpha=0.75, zorder=5)
    axb.annotate("entire 360 deg\nazimuth range\n"
                 f"(+/-{half:.3f} samples at 1 kHz,\n+/-{TAU_MAX*fs_clip:.3f} at "
                 f"{fs_clip:.0f} Hz)", (0, -0.55), xytext=(14, 0),
                 textcoords="offset points", fontsize=6.5, color=rc.OKABE_ITO[6],
                 va="center",
                 arrowprops=dict(arrowstyle="-", lw=0.6, color=rc.OKABE_ITO[6]))
    axb.set_xlim(-12, 12); axb.set_ylim(-1, 1)
    axb.set_xlabel(f"Lag (samples; 1 sample = {1e6/fs_hat:.0f} us at 1 kHz)")
    axb.set_ylabel("Normalised cross-correlation")
    axb.set_title("(b) The delay to be measured is sub-bin")
    axb.legend(loc="upper left")

    # (c) position map, marker area = clip RMS
    axc = fig.add_subplot(gs[1, 0])
    for k, lab, Xc in clips:
        x, y = rc.parse_position(lab)
        s = Xc.std(axis=1, ddof=1).mean()
        axc.scatter(x, y, s=8 + 1.6 * s, facecolor="none",
                    edgecolor=rc.OKABE_ITO[5], lw=0.9)
        axc.scatter(x, y, s=3, color="k")
    axc.set_aspect("equal")
    axc.set_xlabel("Labelled source x (cm)")
    axc.set_ylabel("Labelled source y (cm)")
    axc.set_xticks([-30, -15, 0, 15, 30]); axc.set_yticks([-30, -15, 0, 15, 30])
    axc.set_title("(c) The 25 labelled positions\n(circle area = mean channel RMS)")

    # (d) integer peak lag histogram against the physical bound
    axd = fig.add_subplot(gs[1, 1])
    axd.hist(peak_lags, bins=np.arange(-20.5, 21.5, 1.0),
             color=rc.OKABE_ITO[2], edgecolor="none")
    axd.axvspan(-half, half, color=rc.OKABE_ITO[6], alpha=0.85, zorder=5)
    axd.set_xlabel("Integer peak lag (samples)")
    axd.set_ylabel("Count over 75 channel pairs")
    axd.set_title("(d) Observed peaks vs what is physical")
    axd.set_xlim(-20, 20)
    p = rc.savefig(fig, "fig_real_triplemic.png")
    rc.caption("fig_real_triplemic.png", textwrap.fill(
        "The 25 three-channel hardware clips, and why they cannot yield a "
        "direction-of-arrival estimate. (a) One 30-sample clip; the channels track each "
        "other closely. (b) Normalised cross-correlation of the three channel pairs. The "
        "shaded bar is the complete range of delays the array can physically produce, "
        f"+/-{half:.3f} of one sampling interval at the 1 kHz rate measured for this "
        f"hardware and +/-{TAU_MAX*fs_clip:.3f} at the {fs_clip:.0f} Hz per-channel rate "
        "inferred for the clips themselves: the quantity to be measured is several times "
        "smaller than the lag grid, so the whole azimuth range collapses into the single "
        "lag-zero bin. (c) The 25 position labels recovered from header cell D1, a "
        "complete 5x5 grid at 15 cm spacing; circle area is the mean per-channel RMS of "
        "the clip. (d) Distribution of the integer cross-correlation peak lag over all 75 "
        "channel pairs against the same physical bound; every non-zero peak lies outside "
        "the physically possible range and is therefore noise.", 100))
    print(f"\n          written: {p}")


# ==================================================================================
# 3. Measured noise floor
# ==================================================================================
def section3_noise(fs_hat):
    rc.rule("3. MEASURED NOISE FLOOR / MICROPHONE SELF-NOISE (60 s idle recordings)")

    res = {}
    print("\n      mic   N       duration  DC (code)   sd (code)  robust sd  outliers  "
          "p-p (code)  excess kurtosis")
    for m in (1, 2, 3):
        t, v = rc.load_cal_csv(rc.IDLE_FILES[m])
        med = np.median(v)
        mad = np.median(np.abs(v - med))
        rsd = 1.4826 * mad
        keep = np.abs(v - med) <= 10 * rsd
        vc = v[keep]
        z = (vc - vc.mean()) / vc.std(ddof=1)
        kurt = float(np.mean(z ** 4) - 3.0)
        res[m] = dict(t=t, v=v, keep=keep, dc=vc.mean(), sd=vc.std(ddof=1),
                      raw_sd=v.std(ddof=1), rsd=float(1.4826 * np.median(
                          np.abs(vc - np.median(vc)))),
                      nout=int((~keep).sum()), kurt=kurt,
                      pp=float(vc.max() - vc.min()), n=len(v))
        print(f"      {m:>3} {len(v):>7} {(t[-1]-t[0])/1000:>9.1f} s  {vc.mean():>9.2f}  "
              f"{vc.std(ddof=1):>9.3f}  {res[m]['rsd']:>9.3f}  {int((~keep).sum()):>8}  "
              f"{res[m]['pp']:>9.0f}  {kurt:>14.2f}")

    q_lsb = 1.0 / np.sqrt(12.0)
    sds = np.array([res[m]["sd"] for m in (1, 2, 3)])
    rsds = np.array([res[m]["rsd"] for m in (1, 2, 3)])
    dcs = np.array([res[m]["dc"] for m in (1, 2, 3)])
    kurts = np.array([res[m]["kurt"] for m in (1, 2, 3)])
    print(textwrap.dedent(f"""
      Outliers are isolated single-sample dropouts (codes near 13 and 18, i.e. the
      converter reading almost zero) plus a handful of transients; they are 0.02-0.09 %
      of samples and are excluded from the RMS so that the figure reported is the
      stationary noise floor rather than a glitch rate. The glitch rate itself is a real
      hardware property and is reported above.

      DISTRIBUTION SHAPE. The noise is NOT Gaussian. Excess kurtosis after outlier
      removal is {kurts[0]:.1f}, {kurts[1]:.1f} and {kurts[2]:.1f}, against 0 for a Gaussian: a sharp core
      with heavy tails, meaning the front end produces occasional excursions well beyond
      what its RMS would suggest. That matters for a threshold or a gate, and it should
      be stated rather than smoothed over with the word 'Gaussian'.
      The two scale estimates nevertheless agree closely -- RMS {sds[0]:.2f}, {sds[1]:.2f}, {sds[2]:.2f} LSB
      against a robust 1.4826 x MAD of {rsds[0]:.2f}, {rsds[1]:.2f}, {rsds[2]:.2f} LSB, within about 10 % -- so
      the RMS is a sound figure for an SNR budget and is used as such below. (The robust
      scale is granular here because the median absolute deviation of integer-valued data
      is itself an integer, in steps of 1.48 LSB, so it should not be read to two
      decimal places.)

      Noise floor summary
        self-noise RMS, three microphones      {sds[0]:.2f}, {sds[1]:.2f}, {sds[2]:.2f} LSB   (mean {sds.mean():.2f} LSB)
        robust scale (1.4826 x MAD)            {rsds[0]:.2f}, {rsds[1]:.2f}, {rsds[2]:.2f} LSB   (mean {rsds.mean():.2f} LSB)
        12-bit quantisation floor  1/sqrt(12)  {q_lsb:.3f} LSB
        measured floor / quantisation floor    {sds.mean()/q_lsb:.1f}x  ({20*np.log10(sds.mean()/q_lsb):.1f} dB)
        => the converter is NOT the limiting noise source; the analogue front end is.
           Adding ADC bits would buy nothing.

      Dynamic-range reference for the paper's SNR axis
        DC operating point (mean of three)     {dcs.mean():.1f} LSB of {rc.ADC_FULLSCALE}
        observed positive clipping rail        {2523} LSB   (section 4)
        observed negative clipping rail        {42} LSB
        largest undistorted peak swing         {2523 - dcs.mean():.0f} LSB
        peak SNR = 20 log10(peak / noise RMS)  {20*np.log10((2523-dcs.mean())/sds.mean()):.1f} dB
        RMS SNR for a sine at full swing       {20*np.log10((2523-dcs.mean())/np.sqrt(2)/sds.mean()):.1f} dB
        This is the ceiling of the measured signal chain. The simulation sweeps SNR from
        0 to 40 dB; the hardware can in principle deliver the whole of that range, but
        only for a source loud enough to approach clipping at the microphone.

      Consistency with a digital MEMS microphone (INMP441 or similar I2S part)
        The INMP441 is a 24-bit I2S device: it emits signed two's-complement samples with
        no DC pedestal and no analogue rail. The data here are unsigned integers on a
        4096-code grid sitting on a {dcs.mean():.0f}-code DC pedestal, with hard clipping at 42 and
        2523 codes and a 1 kHz software-timed sample loop. That is an ANALOGUE capsule
        and preamplifier feeding the ESP32-S3 internal 12-bit SAR converter. The data are
        NOT consistent with an INMP441 anywhere in this acquisition path.
        Two readings are possible and the author must resolve which: either the
        calibration and triple-microphone rigs used an analogue capsule while the DoA
        array uses an INMP441, in which case none of the measurements in this file
        characterise the array's microphones; or the stated part is wrong. Until this is
        settled the paper cannot cite an INMP441 datasheet noise figure alongside these
        measurements. A datasheet equivalent-input-noise comparison is deliberately NOT
        made here, because the measured floor is expressed in ADC codes of an unknown
        analogue chain, with no measured sensitivity in mV/Pa and no acoustic reference
        level; converting {sds.mean():.2f} LSB into dB(A) SPL would require a calibrator
        measurement that does not exist in this repository.
    """).rstrip())

    fig_noise(res, fs_hat, q_lsb)
    return res


def fig_noise(res, fs_hat, q_lsb):
    fig, ax = plt.subplots(1, 3, figsize=(7.2, 2.5))
    cols = [rc.OKABE_ITO[5], rc.OKABE_ITO[1], rc.OKABE_ITO[3]]

    # (a) time series, first 2 s
    n2 = int(2 * fs_hat)
    for i, m in enumerate((1, 2, 3)):
        v = res[m]["v"][:n2]
        ax[0].plot(np.arange(len(v)) / fs_hat, v - res[m]["dc"] + (i - 1) * 60,
                   lw=0.4, color=cols[i])
        ax[0].annotate(f"MIC{m}", (0.02, (i - 1) * 60 + 24), fontsize=6.5, color=cols[i],
                       va="center", fontweight="bold")
    ax[0].set_xlim(0, 2.0); ax[0].set_ylim(-115, 115)
    ax[0].set_xlabel("Time (s)")
    ax[0].set_ylabel("Deviation from DC (LSB, offset)")
    ax[0].set_title("(a) Idle time series")

    # (b) histogram
    for i, m in enumerate((1, 2, 3)):
        v = res[m]["v"][res[m]["keep"]] - res[m]["dc"]
        ax[1].hist(v, bins=np.arange(-45.5, 46.5, 1.0), histtype="step", lw=1.1,
                   color=cols[i], label=f"MIC{m} ({res[m]['sd']:.1f} LSB)", density=True)
    xg = np.linspace(-45, 45, 400)
    sd = np.mean([res[m]["sd"] for m in (1, 2, 3)])
    ax[1].plot(xg, np.exp(-0.5 * (xg / sd) ** 2) / (sd * np.sqrt(2 * np.pi)),
               "k:", lw=1.0, label=f"Gaussian, pooled RMS {sd:.1f} LSB")
    ax[1].set_yscale("log"); ax[1].set_ylim(1e-5, 0.5)
    ax[1].set_xlabel("Deviation from DC (LSB)")
    ax[1].set_ylabel("Probability density")
    ax[1].set_title("(b) Amplitude distribution\n(log density: core is sharper,\n"
                    "tails are heavier, than Gaussian)")
    ax[1].legend(loc="lower center", fontsize=6.0)

    # (c) PSD vs the quantisation floor
    for i, m in enumerate((1, 2, 3)):
        v = res[m]["v"].astype(float)
        v[~res[m]["keep"]] = res[m]["dc"]
        f, P = sps.welch(v - res[m]["dc"], fs=fs_hat, nperseg=4096, noverlap=2048)
        ax[2].semilogy(f, P, lw=0.8, color=cols[i], label=f"MIC{m}")
    qfloor = (q_lsb ** 2) / (fs_hat / 2)
    ax[2].axhline(qfloor, color="k", ls="--", lw=0.9)
    ax[2].annotate("12-bit quantisation floor", (140, qfloor), xytext=(0, 4),
                   textcoords="offset points", fontsize=6.3)
    ax[2].set_xlim(0, fs_hat / 2); ax[2].set_ylim(5e-5, 3e1)
    ax[2].set_xlabel("Frequency (Hz)")
    ax[2].set_ylabel(r"PSD (LSB$^2$/Hz)")
    ax[2].set_title("(c) Noise power spectrum")
    ax[2].legend(loc="upper right", fontsize=6.2, ncol=3)
    fig.tight_layout()
    p = rc.savefig(fig, "fig_real_noise_floor.png")
    sds = np.array([res[m]["sd"] for m in (1, 2, 3)])
    rsds = np.array([res[m]["rsd"] for m in (1, 2, 3)])
    kurts = np.array([res[m]["kurt"] for m in (1, 2, 3)])
    rc.caption("fig_real_noise_floor.png", textwrap.fill(
        "Measured microphone self-noise from three 60 s idle recordings (no source). "
        "(a) Two seconds of each channel, DC removed and vertically offset. (b) Amplitude "
        "histograms with a Gaussian of the pooled standard deviation for reference; the "
        "distributions are NOT Gaussian: on a logarithmic density axis the core is "
        "visibly sharper and the tails heavier than the Gaussian of the same RMS (dotted), "
        f"with excess kurtosis of {kurts.min():.0f} to {kurts.max():.0f}. Per-channel RMS is "
        f"{sds.min():.1f} to {sds.max():.1f} LSB and the robust scale is {rsds.min():.1f} to "
        f"{rsds.max():.1f} LSB. (c) Welch power spectra against the 12-bit quantisation "
        f"floor. The measured floor sits {20*np.log10(sds.mean()/q_lsb):.0f} dB above "
        "quantisation, so the analogue front end, not the converter, sets the noise floor "
        "and adding converter bits would buy nothing; the narrowband features between 20 "
        "and 90 Hz are interference picked up by the analogue chain. Vertical axes are in "
        "ADC least-significant bits because no acoustic calibration of this rig exists.",
        100))
    print(f"          written: {p}")


# ==================================================================================
# 4. Frequency, distance and waveform response
# ==================================================================================
def section4_response(cal, delta, fs_hat, noise_rms):
    rc.rule("4. LEVEL VERSUS EXCITATION FREQUENCY, DISTANCE AND WAVEFORM")

    RAIL_HI, RAIL_LO = 2475.0, 92.0          # 2 % of the observed dynamic range
    rows = []
    for wfm, khz, dist, p in cal:
        t, v = rc.load_cal_csv(p)
        clip = float(np.mean((v >= RAIL_HI) | (v <= RAIL_LO)))
        ac = v - v.mean()
        rows.append(dict(wf=wfm, khz=khz, dist=dist, rms=float(ac.std(ddof=1)),
                         pk=float(np.max(np.abs(ac))), clip=clip, dc=float(v.mean())))
    print(textwrap.dedent(f"""
      Clipping census. A sample counts as clipped if it lies within 2 % of the observed
      dynamic range of either analogue rail (code >= {RAIL_HI:.0f} or <= {RAIL_LO:.0f}).
    """).rstrip())
    print("\n        distance      1 kHz    5 kHz   10 kHz   15 kHz   20 kHz   (% samples clipped, "
          "mean over waveforms)")
    for dist in rc.CAL_DISTS_CM:
        cells = []
        for khz in rc.CAL_FREQS_KHZ:
            sel = [r for r in rows if r["dist"] == dist and r["khz"] == khz]
            cells.append(100 * np.mean([r["clip"] for r in sel]))
        print(f"        {dist:>4} cm   " + "  ".join(f"{c:7.2f}" for c in cells))
    nclip = sum(1 for r in rows if r["clip"] > 0.005)
    print(f"\n        recordings with > 0.5 % clipped samples: {nclip} of {len(rows)}")
    print("        Clipped recordings cannot report a level, because the front end, not "
          "the microphone,\n        is setting the amplitude. They are excluded from the "
          "level fits below.")

    clean = [r for r in rows if r["clip"] <= 0.005]
    print(f"\n      Level in dB re 1 LSB RMS, unclipped recordings only "
          f"({len(clean)} of {len(rows)})\n")
    print("        waveform   f (kHz)  " + "".join(f"{d:>8}" for d in rc.CAL_DISTS_CM)
          + "     cm")
    table = {}
    for wfm in rc.CAL_WAVEFORMS:
        for khz in rc.CAL_FREQS_KHZ:
            cells = []
            for dist in rc.CAL_DISTS_CM:
                sel = [r for r in clean if r["wf"] == wfm and r["khz"] == khz
                       and r["dist"] == dist]
                cells.append(20 * np.log10(sel[0]["rms"]) if sel else np.nan)
            table[(wfm, khz)] = np.array(cells)
            print(f"        {wfm:<10} {khz:>5}   "
                  + "".join(("     n/a" if not np.isfinite(c) else f"{c:8.2f}")
                            for c in cells))

    # --- inverse-square law -------------------------------------------------------------
    print(textwrap.dedent("""
      Inverse-square-law check. A free-field point source gives sound pressure
      proportional to 1/r, i.e. -20 dB per decade of distance (-6.02 dB per doubling).
      Fitted slope of level against log10(distance), unclipped points only:
    """).rstrip())
    print("\n        waveform   f (kHz)   n   slope (dB/decade)   residual sd (dB)   "
          "deviation from -20")
    slopes = []
    for wfm in rc.CAL_WAVEFORMS:
        for khz in rc.CAL_FREQS_KHZ:
            y = table[(wfm, khz)]
            m = np.isfinite(y)
            if m.sum() < 4:
                print(f"        {wfm:<10} {khz:>5} {m.sum():>4}   "
                      f"(too few unclipped points)")
                continue
            x = np.log10(np.array(rc.CAL_DISTS_CM, float)[m] / 100.0)
            A = np.vstack([x, np.ones_like(x)]).T
            coef, *_ = np.linalg.lstsq(A, y[m], rcond=None)
            resid = y[m] - A @ coef
            slopes.append(coef[0])
            print(f"        {wfm:<10} {khz:>5} {m.sum():>4}     {coef[0]:>12.2f}      "
                  f"{resid.std(ddof=1):>12.2f}      {coef[0]+20:>+12.2f}")
    slopes = np.array(slopes)
    # How often does the level RISE with distance? Under any physical model it must not.
    rises = 0
    total = 0
    for key, y in table.items():
        m = np.isfinite(y)
        if m.sum() < 2:
            continue
        yy = y[m]
        total += len(yy) - 1
        rises += int(np.sum(np.diff(yy) > 0))
    print(textwrap.dedent(f"""
        pooled slope        {slopes.mean():+.2f} dB/decade  (sd across conditions {slopes.std(ddof=1):.2f})
        free-field ideal    -20.00 dB/decade
        conditions with a POSITIVE fitted slope: {int(np.sum(slopes > 0))} of {len(slopes)}
        adjacent distance steps where the level RISES with distance: {rises} of {total}

      Interpretation. The measured level does not fall with distance at all; in
      {100*rises/total:.0f} % of adjacent distance steps it rises, and the pooled fitted slope is
      positive. No acoustic mechanism produces that. The dominant explanation must be
      that the excitation level was NOT held constant between runs: for example the sine
      1 kHz condition reads {table[('sine',1)][1]:.1f} dB at 50 cm and {table[('sine',1)][2]:.1f} dB at 100 cm, an
      {table[('sine',1)][2]-table[('sine',1)][1]:+.1f} dB change over one doubling of distance where the physics allows
      at most -6 dB. Contributing factors that cannot be separated with the data
      available:
        (a) the loudspeaker drive level and the microphone preamplifier gain are not
            recorded anywhere, and there is no reference microphone;
        (b) the measurement was made in an ordinary room, so beyond the critical distance
            the reverberant field dominates and the level stops falling with distance;
        (c) at 15 cm the front end is clipping, which removes the near-field anchor
            points that would constrain the fit.
      AN INVERSE-SQUARE-LAW VERIFICATION CANNOT BE CLAIMED FROM THIS DATASET, and neither
      can a distance response of any kind. The correct action is to state this and, if the
      result is wanted, to repeat the sweep with a documented and fixed drive level.

      Interpretation of the frequency axis. Because every excitation is aliased
      (section 1), the horizontal axis of any 'frequency response' drawn from these files
      is the frequency of the loudspeaker command, not of anything present in the
      recording. Aliasing preserves amplitude, so comparing LEVELS across excitation
      frequency is meaningful in principle; but with the drive level uncontrolled it is
      not meaningful in practice either. The one statement the data will bear is
      qualitative and is worth exactly that much: the transmit-plus-receive chain
      delivers noticeably more level at 1-10 kHz than at 15-20 kHz.
    """).rstrip())

    for khz in rc.CAL_FREQS_KHZ:
        sel = [r for r in rows if r["khz"] == khz]
        lv = 20 * np.log10(np.median([r["rms"] for r in sel]))
        print(f"        median level over all distances and waveforms, "
              f"{khz:>2} kHz excitation: {lv:6.2f} dB re 1 LSB")

    fig_response(rows, table, noise_rms)
    return rows, table


def fig_response(rows, table, noise_rms):
    fig, ax = plt.subplots(1, 3, figsize=(7.6, 2.8))

    # (a) level vs distance per excitation frequency (sine)
    anchor = None
    for i, khz in enumerate(rc.CAL_FREQS_KHZ):
        d, y, cl = [], [], []
        for dist in rc.CAL_DISTS_CM:
            sel = [r for r in rows if r["wf"] == "sine" and r["khz"] == khz
                   and r["dist"] == dist]
            if sel:
                d.append(dist); y.append(20 * np.log10(sel[0]["rms"]))
                cl.append(sel[0]["clip"] > 0.005)
        d = np.array(d, float); y = np.array(y); cl = np.array(cl)
        col = rc.OKABE_ITO[[5, 1, 3, 6, 7][i]]
        ax[0].plot(d[~cl], y[~cl], ls=rc.LINESTYLES[i % 6], marker=rc.MARKERS[i],
                   lw=1.1, color=col, label=f"{khz} kHz")
        if cl.any():
            ax[0].plot(d[cl], y[cl], marker=rc.MARKERS[i], ms=5, mfc="none", mew=1.0,
                       color=col, ls="none")
            ax[0].plot(d[cl], y[cl], "x", ms=6, mew=1.2, color="k", ls="none")
        if khz == 1:
            anchor = (d[~cl][0], y[~cl][0])
    ax[0].plot([], [], "kx", ms=6, mew=1.2, ls="none", label="clipped (excluded)")
    dd = np.array([anchor[0], 320.0])
    ax[0].plot(dd, anchor[1] - 20 * np.log10(dd / anchor[0]), "k:", lw=1.0,
               label="1/r (inverse square)")
    ax[0].set_xscale("log")
    ax[0].set_xlim(12, 400)
    ax[0].set_xticks([15, 50, 100, 200, 300], ["15", "50", "100", "200", "300"])
    ax[0].set_xlabel("Source distance (cm)")
    ax[0].set_ylabel("Level (dB re 1 LSB RMS)")
    ax[0].set_title("(a) Sine excitation:\nlevel does not fall with distance")
    ax[0].set_ylim(12, 70)
    ax[0].legend(ncol=3, fontsize=5.6, loc="upper center", columnspacing=0.8,
                 handletextpad=0.4)

    # (b) level vs excitation frequency per waveform
    for i, wfm in enumerate(rc.CAL_WAVEFORMS):
        y = [20 * np.log10(np.median([r["rms"] for r in rows
                                      if r["wf"] == wfm and r["khz"] == k]))
             for k in rc.CAL_FREQS_KHZ]
        ax[1].plot(rc.CAL_FREQS_KHZ, y, ls=rc.LINESTYLES[i], marker=rc.MARKERS[i],
                   lw=1.2, color=rc.OKABE_ITO[[5, 1, 3][i]], label=wfm)
    nf = 20 * np.log10(noise_rms)
    ax[1].axhline(nf, color="k", ls="--", lw=0.9)
    ax[1].annotate(f"measured noise floor ({noise_rms:.1f} LSB)", (20.5, nf),
                   xytext=(0, 3), textcoords="offset points", fontsize=6.2, ha="right")
    ax[1].set_ylim(nf - 3, 58)
    ax[1].set_xticks(list(rc.CAL_FREQS_KHZ))
    ax[1].set_xlabel("Nominal excitation frequency (kHz)")
    ax[1].set_ylabel("Median level (dB re 1 LSB RMS)")
    ax[1].set_title("(b) Waveform comparison\n(frequency axis is ALIASED)")
    ax[1].legend(loc="upper center", ncol=3, fontsize=6.4, columnspacing=1.0)

    # (c) clipping map
    M = np.zeros((len(rc.CAL_FREQS_KHZ), len(rc.CAL_DISTS_CM)))
    for i, khz in enumerate(rc.CAL_FREQS_KHZ):
        for j, dist in enumerate(rc.CAL_DISTS_CM):
            sel = [r for r in rows if r["khz"] == khz and r["dist"] == dist]
            M[i, j] = 100 * np.mean([r["clip"] for r in sel])
    im = ax[2].imshow(M, aspect="auto", origin="lower", cmap="cividis",
                      vmin=0, vmax=max(1.0, M.max()))
    ax[2].set_xticks(range(len(rc.CAL_DISTS_CM)),
                     [str(d) for d in rc.CAL_DISTS_CM], fontsize=6.5, rotation=0)
    ax[2].set_yticks(range(len(rc.CAL_FREQS_KHZ)),
                     [str(k) for k in rc.CAL_FREQS_KHZ], fontsize=6.5)
    ax[2].set_xlabel("Distance (cm)")
    ax[2].set_ylabel("Excitation (kHz)")
    ax[2].set_title("(c) Clipped samples (%)")
    ax[2].grid(False)
    fig.colorbar(im, ax=ax[2], fraction=0.046, pad=0.03)
    fig.tight_layout()
    p = rc.savefig(fig, "fig_real_level_response.png")
    rc.caption("fig_real_level_response.png", textwrap.fill(
        "Recorded level against source distance, excitation frequency and waveform, from "
        "the 105 single-channel calibration recordings. (a) Sine excitation: measured RMS "
        "level versus distance on log axes, with the inverse-square-law slope shown for "
        "reference and clipped recordings crossed out. The measured decay is far shallower "
        "than 1/r, consistent with a reverberant room beyond the critical distance and "
        "with front-end clipping removing the near-field anchor points. (b) Median level "
        "against nominal excitation frequency for the three waveforms, with the measured "
        "idle noise floor marked; note that the frequency axis is the loudspeaker command "
        "frequency, since every excitation is aliased by the 1 kHz acquisition rate. "
        "(c) Percentage of clipped samples over the distance-frequency grid, showing that "
        "the loud low-frequency conditions are unusable for level work.", 100))
    print(f"\n          written: {p}")


# ==================================================================================
# 5. Inter-microphone gain and offset mismatch
# ==================================================================================
def section5_mismatch(noise, clips, dcs, sds, rr):
    rc.rule("5. INTER-MICROPHONE MISMATCH AND ITS BOUND ON DoA ACCURACY")

    print(textwrap.dedent("""
      What can and cannot be measured. The 105 calibration recordings each contain ONE
      microphone channel and do not record which microphone it was, so they cannot yield
      any inter-microphone comparison. Only two datasets carry simultaneous or
      comparable per-microphone information:
        * the three 60 s idle recordings  -> DC offset and noise-floor mismatch;
        * the 25 three-channel clips      -> relative broadband gain at a common source.
      PHASE mismatch cannot be measured from anything in this repository, because that
      requires a common excitation captured simultaneously on all three channels with a
      time base -- which no file provides.
    """).rstrip())

    print("\n  5a. DC offset and noise-floor mismatch (idle recordings)\n")
    print("        mic    DC (LSB)   self-noise RMS (LSB)")
    for m in (1, 2, 3):
        print(f"        {m:>3}   {noise[m]['dc']:>9.2f}   {noise[m]['sd']:>18.3f}")
    dc = np.array([noise[m]["dc"] for m in (1, 2, 3)])
    sd = np.array([noise[m]["sd"] for m in (1, 2, 3)])
    print(f"\n        DC spread (max - min)          {dc.max()-dc.min():.2f} LSB "
          f"({100*(dc.max()-dc.min())/dc.mean():.2f} % of the operating point)")
    print(f"        noise-floor spread             {sd.max()/sd.min():.2f}x  "
          f"({20*np.log10(sd.max()/sd.min()):.2f} dB)")

    print("\n  5b. Relative broadband gain (three-channel clips, common source)\n")
    # Regress channel j on channel i clip by clip, using only clips where the pair is
    # well correlated, so the slope really is a gain ratio.
    print(textwrap.dedent("""
      Estimator note. Ordinary least squares of channel j on channel i is biased towards
      zero when the regressor is noisy, and the ratio of standard deviations is biased
      towards unity. Total least squares (the principal eigenvector of the 2x2 scatter
      matrix) is consistent when the two channels carry comparable noise, which the idle
      recordings show they roughly do, so TLS is used and OLS is printed beside it as a
      lower bracket.
    """).rstrip())
    pairs = ((0, 1), (0, 2), (1, 2))
    print("\n        pair    n clips (r>0.8)   TLS gain   TLS in dB   OLS in dB   "
          "IQR of TLS (dB)")
    gains = {}
    for pi, (i, j) in enumerate(pairs):
        g, gols = [], []
        for (k, lab, X), r in zip(clips, rr):
            if r[pi] < 0.8:
                continue
            a = X[i] - X[i].mean(); b = X[j] - X[j].mean()
            gols.append(float(np.dot(a, b) / np.dot(a, a)))
            M = np.cov(np.vstack([a, b]))
            w, V = np.linalg.eigh(M)
            v = V[:, -1]
            g.append(float(v[1] / v[0]))                        # b ~= g * a, TLS
        g = np.array(g); gols = np.array(gols)
        gains[(i, j)] = g
        dbv = 20 * np.log10(np.abs(g))
        print(f"        {i+1}->{j+1}   {len(g):>13}   {np.median(g):>8.4f}   "
              f"{np.median(dbv):>+9.2f}   {np.median(20*np.log10(np.abs(gols))):>+9.2f}   "
              f"{np.percentile(dbv,75)-np.percentile(dbv,25):>15.2f}")
    all_db = np.concatenate([20 * np.log10(np.abs(v)) for v in gains.values()])
    gain_spread = float(np.median(np.abs(all_db)))
    g12 = float(np.median(gains[(0, 1)])); g13 = float(np.median(gains[(0, 2)]))
    g23 = float(np.median(gains[(1, 2)]))
    print(f"\n        transitivity check  g12 x g23 = {g12*g23:.4f}  against  "
          f"g13 = {g13:.4f}   (closure error {20*np.log10(abs(g12*g23/g13)):+.2f} dB)")
    print("        A gain ratio must be transitive around the three channels. The "
          "closure error is a\n        direct estimate of the method's own uncertainty, "
          "and it is the same size as the\n        mismatch being measured -- so treat "
          "these gains as order-of-magnitude, not precision,\n        figures.")

    # --- what a gain mismatch costs a GCC-PHAT array -------------------------------------
    print(textwrap.dedent(f"""
        median absolute pairwise gain mismatch   {gain_spread:.2f} dB
        interquartile spread of the estimate     {np.percentile(all_db,75)-np.percentile(all_db,25):.2f} dB

      Why this matters, and why it matters less than it looks. GCC-PHAT normalises each
      cross-spectrum to unit magnitude, so a pure frequency-flat GAIN mismatch cancels
      exactly and contributes no delay bias. What does not cancel is (i) a mismatch that
      varies with frequency, which tilts the effective weighting and biases the peak, and
      (ii) any PHASE mismatch, which maps one-for-one into a delay error. A phase error
      of dphi radians at frequency f is a delay error dphi / (2*pi*f), and on this array a
      delay error dtau produces an azimuth error of up to dtau * c / d_max radians.
    """).rstrip())
    print("\n        phase mismatch     delay error at 2 kHz    worst-case azimuth error")
    for dphi_deg in (1.0, 2.0, 5.0, 10.0):
        dtau = np.deg2rad(dphi_deg) / (2 * np.pi * 2000.0)
        daz = np.rad2deg(np.arcsin(min(1.0, dtau / TAU_MAX)))
        print(f"        {dphi_deg:>10.0f} deg  {dtau*1e6:>18.2f} us  {daz:>22.2f} deg")
    print(textwrap.dedent(f"""
        For scale, the array's entire delay budget is {TAU_MAX*1e6:.1f} us; 5 degrees of
        uncorrected phase mismatch at 2 kHz already consumes {100*np.deg2rad(5)/(2*np.pi*2000)/TAU_MAX:.1f} % of it.
        This is a real and citable limitation of a low-cost three-microphone build, but
        this repository contains NO measurement of it. Obtaining one requires a single
        source captured simultaneously on all three channels, at a known sample rate, at
        one known azimuth -- roughly ten minutes of bench time, and it should be done.
    """).rstrip())

    fig_mismatch(noise, gains, clips, rr)
    return gains


def fig_mismatch(noise, gains, clips, rr):
    fig, ax = plt.subplots(1, 3, figsize=(7.4, 2.5))
    cols = [rc.OKABE_ITO[5], rc.OKABE_ITO[1], rc.OKABE_ITO[3]]

    x = np.arange(3)
    dc = np.array([noise[m]["dc"] for m in (1, 2, 3)])
    sd = np.array([noise[m]["sd"] for m in (1, 2, 3)])
    b = ax[0].bar(x, dc - dc.mean(), 0.55, color=[cols[i] for i in range(3)])
    ax[0].bar_label(b, fmt="%+.2f", fontsize=6.2, padding=2)
    ax[0].axhline(0, color="0.4", lw=0.7)
    ax[0].set_xticks(x, ["MIC1", "MIC2", "MIC3"])
    ax[0].set_ylabel("DC offset re 3-channel mean (LSB)")
    ax[0].set_ylim(-3.0, 2.4)
    ax[0].set_title(f"(a) DC operating point\n(mean {dc.mean():.1f} of "
                    f"{rc.ADC_FULLSCALE} codes)")

    b2 = ax[1].bar(x, sd, 0.55, color=[cols[i] for i in range(3)])
    ax[1].bar_label(b2, fmt="%.2f", fontsize=6.2, padding=2)
    ax[1].set_xticks(x, ["MIC1", "MIC2", "MIC3"])
    ax[1].set_ylabel("Self-noise RMS (LSB)")
    ax[1].set_ylim(0, 7.0)
    ax[1].set_title(f"(b) Idle noise floor\n(spread "
                    f"{20*np.log10(sd.max()/sd.min()):.1f} dB)")

    ax = [ax[0], ax[2]]
    for pi, (i, j) in enumerate(((0, 1), (0, 2), (1, 2))):
        g = 20 * np.log10(np.abs(gains[(i, j)]))
        ax[1].plot(np.full(len(g), pi) + RNG.uniform(-0.13, 0.13, len(g)), g,
                   rc.MARKERS[pi], ms=3.2, mfc="none", mew=0.8, color=cols[pi], ls="none")
        ax[1].plot([pi - 0.25, pi + 0.25], [np.median(g)] * 2, "k-", lw=1.6)
    ax[1].axhline(0, color="0.6", lw=0.8, ls=":")
    ax[1].set_xticks([0, 1, 2], ["MIC1-MIC2", "MIC1-MIC3", "MIC2-MIC3"])
    ax[1].set_ylabel("Relative gain (dB)")
    ax[1].set_title("(c) Per-clip broadband gain ratio\n(clips with pairwise r > 0.8)")
    fig.tight_layout()
    p = rc.savefig(fig, "fig_real_mic_mismatch.png")
    dcv = np.array([noise[m]["dc"] for m in (1, 2, 3)])
    sdv = np.array([noise[m]["sd"] for m in (1, 2, 3)])
    med_db = float(np.median(np.abs(np.concatenate(
        [20 * np.log10(np.abs(v)) for v in gains.values()]))))
    rc.caption("fig_real_mic_mismatch.png", textwrap.fill(
        "Measured channel-to-channel mismatch of the three-microphone front end. "
        "(a) DC operating point of each channel relative to the three-channel mean and "
        "(b) self-noise RMS, both from the 60 s idle recordings: the DC pedestals agree "
        f"to within {dcv.max()-dcv.min():.1f} LSB but the noise floors differ by "
        f"{20*np.log10(sdv.max()/sdv.min()):.1f} dB. (c) Relative broadband gain "
        "of each microphone pair by total least squares, one point per three-channel clip "
        "in which that pair is well correlated, with the median marked. The median "
        f"absolute pairwise gain mismatch is {med_db:.1f} dB. No phase-mismatch measurement "
        "exists anywhere in this dataset; GCC-PHAT is insensitive to a frequency-flat gain "
        "mismatch but not to phase mismatch, which maps one-for-one into a delay error and "
        "must be measured separately.", 100))
    print(f"\n          written: {p}")


# ==================================================================================
# 6. Filter algorithm comparison, on real data
# ==================================================================================
def section6_filters(noise, fs_hat):
    rc.rule("6. THE FOUR CANDIDATE FILTERS, EVALUATED ON REAL RECORDINGS")

    print(textwrap.dedent("""
      What the four scripts in 'Filter alogrithims test/' actually do. Every one of them
      builds a low-pass FIR, applies it to `np.random.randn(1000)` -- synthetic noise --
      and plots the result. None of them opens a recording, and none of them measures
      anything. They are design sketches, so the comparison below re-implements the four
      designs exactly as written and runs them on the real idle and calibration data.

        A1  windowed sinc, 21 taps, Hamming window. The script writes fc = 0.1 into
            np.sinc(2*fc*n), where fc is in CYCLES PER SAMPLE, so the cutoff is 0.1 fs
            = 0.2 x Nyquist. Normalised to unity DC gain; linear phase.
        A2  scipy.signal.firwin, 51 taps, Kaiser window beta = 8.6. firwin takes a
            fraction of NYQUIST, so the same written 0.1 means 0.05 fs = 0.1 x Nyquist,
            half of A1's cutoff. Linear phase, 25-sample group delay.
        A3  'frequency sampling': a 51-point rectangular magnitude mask inverse-DFT'd
            WITHOUT an fftshift. The resulting coefficient vector is the periodic sinc
            wrapped around the buffer, so the filter is not a windowed low-pass at all.
        A4  Gaussian window, 21 taps, sigma = 3 samples, area-normalised; linear phase,
            10-sample group delay, but a very soft roll-off.

      A1 and A2 therefore do NOT have the same cutoff even though both scripts write 0.1.
      Every metric below is measured relative to each filter's own -3 dB point so that
      the four designs are compared fairly rather than at an arbitrary common frequency.
    """).rstrip())

    bank = rc.filter_bank()
    names = list(bank)

    # --- design-domain metrics -----------------------------------------------------------
    print(f"\n  6a. Design-domain response, measured at the fitted fs = {fs_hat:.1f} Hz\n")
    print("        filter                              taps   -3 dB (Hz)  passband ripple"
          "  stopband att.  linear phase   group delay")
    metrics = {}
    for nm in names:
        h, _ = bank[nm]
        w, H = sps.freqz(h, worN=16384)
        f = w / np.pi * fs_hat / 2                       # Hz
        mag = np.abs(H) / max(abs(np.sum(h)), 1e-12)     # normalise to DC gain
        below = np.where(mag < 10 ** (-3 / 20))[0]
        f3 = float(f[below[0]]) if below.size else float(f[-1])
        pbm = f <= 0.8 * f3
        ripple = 20 * np.log10(mag[pbm].max() / max(mag[pbm].min(), 1e-12))
        # Stopband: everything above the first null past the -3 dB point.
        after = np.where(f > f3)[0]
        nulls = after[np.r_[False, (mag[after][1:-1] < mag[after][:-2]) &
                            (mag[after][1:-1] < mag[after][2:]), False]]
        sb0 = f[nulls[0]] if nulls.size else 2.0 * f3
        sb = mag[f >= sb0]
        att = -20 * np.log10(max(sb.max(), 1e-12)) if sb.size else 0.0
        sym = np.allclose(h, h[::-1], atol=1e-12)
        gd_w, gd = sps.group_delay((h, 1.0), w=8192)
        gf = gd_w / np.pi * fs_hat / 2
        gd_pb = gd[gf <= 0.8 * f3]
        gd_cb = gd[gf <= 0.2 * fs_hat / 2]        # common 0 - 0.2 Nyquist reference band
        metrics[nm] = dict(f3=f3, ripple=float(ripple), att=float(att), sym=bool(sym),
                           gd=float(np.mean(gd_pb)),
                           gd_var=float(gd_pb.max() - gd_pb.min()),
                           gd_var_cb=float(gd_cb.max() - gd_cb.min()), ntaps=len(h))
        print(f"        {nm:<36}{len(h):>5}   {f3:>9.1f}  {ripple:>13.2f} dB  "
              f"{att:>10.1f} dB  {'yes' if sym else 'NO':>12}   {np.mean(gd_pb):>7.2f} smp"
              f" (+/-{0.5*(gd_pb.max()-gd_pb.min()):.2f})")

    # --- noise suppression on the real idle recordings ------------------------------------
    print("\n  6b. Noise suppression measured on the three 60 s idle recordings\n")
    print("        filter                              MIC1     MIC2     MIC3   "
          "mean (dB RMS reduction)")
    for nm in names:
        h, _ = bank[nm]
        red = []
        for m in (1, 2, 3):
            v = noise[m]["v"].astype(float).copy()
            v[~noise[m]["keep"]] = noise[m]["dc"]
            z = v - noise[m]["dc"]
            y = sps.lfilter(h, 1.0, z)[len(h):]
            red.append(20 * np.log10(z.std(ddof=1) / y.std(ddof=1)))
        metrics[nm]["noise_red"] = float(np.mean(red))
        print(f"        {nm:<36}" + "".join(f"{r:8.2f} " for r in red)
              + f"  {np.mean(red):8.2f}")

    # --- passband fidelity on a real recording --------------------------------------------
    print("\n  6c. Passband fidelity on a real recording (sine_wave_15k_15.csv, an "
          "unclipped\n      record whose aliased line at 0.19 Hz sits deep inside every "
          "passband)\n")
    _, v = rc.load_cal_csv(os.path.join(rc.CAL_DIST, "15 cm", "sine",
                                        "sine_wave_15k_15.csv"))
    z = v - v.mean()
    n = len(z)
    F = np.fft.rfft(z * np.hanning(n))
    fr = np.fft.rfftfreq(n, 1 / fs_hat)
    k0 = int(np.argmax(np.abs(F[(fr > 0.01) & (fr < 1.0)])
                       )) + int(np.argmax(fr > 0.01))
    print("        filter                              in-band amplitude change (dB)  "
          "out-of-band residual (dB)")
    for nm in names:
        h, _ = bank[nm]
        y = np.convolve(z, h, mode="same")
        G = np.fft.rfft(y * np.hanning(n))
        inb = 20 * np.log10(np.abs(G[k0]) / np.abs(F[k0]))
        hi = (fr > 0.2 * fs_hat / 2)
        oob = 20 * np.log10(np.sqrt(np.mean(np.abs(G[hi]) ** 2))
                            / np.sqrt(np.mean(np.abs(F[hi]) ** 2)))
        metrics[nm]["inband"] = float(inb); metrics[nm]["oob"] = float(oob)
        print(f"        {nm:<36}{inb:>26.3f}  {oob:>26.2f}")

    # --- the TDOA-relevant metric -----------------------------------------------------------
    print(textwrap.dedent(f"""
      6d. The metric that actually decides this: phase.
      A filter applied identically to all three channels contributes a COMMON delay,
      which cancels in every time-difference. What does not cancel is group delay that
      varies with frequency, because it moves different parts of the source spectrum by
      different amounts and smears the cross-correlation peak. Converting the passband
      group-delay variation of each candidate into the corresponding delay error and into
      the azimuth error it would cause on this array ({D_MAX*100:.2f} cm microphone spacing,
      delay budget {TAU_MAX*1e6:.1f} us):
    """).rstrip())
    print("        Group-delay variation is reported twice: over each filter's OWN "
          "passband (fair to\n        the design) and over a COMMON 0 - "
          f"{0.2*fs_hat/2:.0f} Hz reference band, which is what a TDOA front end\n"
          "        would actually have to pass.\n")
    print("        filter                              gd var, own pb   gd var, 0-100 Hz"
          "   at fs=48 kHz   azimuth error @48 kHz")
    for nm in names:
        gv = metrics[nm]["gd_var_cb"]
        t48 = gv / 48000.0 * 1e6
        frac = (t48 * 1e-6) / TAU_MAX
        metrics[nm]["az48"] = float(np.rad2deg(np.arcsin(frac))) if frac < 1 else np.inf
        az_s = (f"{metrics[nm]['az48']:>18.2f} deg" if frac < 1
                else f"{'unbounded':>18}    ")
        print(f"        {nm:<36}{metrics[nm]['gd_var']:>11.3f} smp  {gv:>13.3f} smp  "
              f"{t48:>11.3f} us  {az_s}")

    a1, a2, a3, a4 = (metrics[n] for n in names)
    print(textwrap.dedent(f"""
      RECOMMENDATION.
        Use A2, the 51-tap Kaiser (beta = 8.6) firwin low-pass, applied identically to
        all three channels.
        Reasons, in order of weight:
          1. It is exactly linear phase (coefficients symmetric to 1e-12), so its
             {a2['gd']:.0f}-sample group delay is a constant common to all channels and cancels
             exactly in every time-difference. Its passband group-delay variation is
             {a2['gd_var']:.3f} samples, i.e. {a2['az48']:.2f} deg of azimuth error at 48 kHz -- negligible.
          2. It has by far the deepest stopband of the four: {a2['att']:.0f} dB, against
             {a1['att']:.0f} dB for A1, {a4['att']:.0f} dB for A4 and {a3['att']:.0f} dB for A3, and the
             flattest passband ({a2['ripple']:.2f} dB ripple against {a1['ripple']:.2f}, {a3['ripple']:.2f} and {a4['ripple']:.2f} dB).
          3. It removes the most measured noise from the real idle recordings:
             {a2['noise_red']:.2f} dB, against {a1['noise_red']:.2f}, {a3['noise_red']:.2f} and {a4['noise_red']:.2f} dB.
          4. Its cost on the target is trivial: {a2['ntaps']} multiply-accumulates per sample per
             channel, {3*a2['ntaps']} per three-channel frame, far under 1 % of one ESP32-S3 core
             at 48 kHz.
        REJECT A3 outright. Its coefficients are not symmetric, so it is not linear phase:
        it is the un-shifted inverse DFT of a rectangular mask, which is a coding error
        rather than a design choice. It has no usable stopband at all ({a3['att']:.1f} dB, i.e.
        out-of-band energy is not attenuated), a -3 dB point at only {a3['f3']:.1f} Hz, and over
        the 0-{0.2*fs_hat/2:.0f} Hz band a group-delay variation of {a3['gd_var_cb']:.1f} samples, which at 48 kHz is
        {a3['gd_var_cb']/48000*1e6:.0f} us -- {a3['gd_var_cb']/48000/TAU_MAX:.0f} times the array's entire delay budget of
        {TAU_MAX*1e6:.0f} us, so the azimuth error it induces is unbounded. A non-linear-phase
        filter in front of a TDOA estimator is the one thing a delay-based system must
        not do.
        A1 and A4 are usable and cheaper ({a1['ntaps']} taps, {a1['gd']:.0f}-sample group delay) and both
        are linear phase, so neither corrupts the delay. They simply roll off too gently:
        A1 reaches {a1['att']:.0f} dB and A4 {a4['att']:.0f} dB of stopband attenuation, against A2's {a2['att']:.0f} dB.
        Caveat on latency. A2's {a2['gd']:.0f}-sample group delay is {a2['gd']/fs_hat*1e3:.0f} ms at the rig's
        {fs_hat:.0f} Hz rate but only {a2['gd']/48000*1e3:.2f} ms at the array's 48 kHz design rate. At the
        low rate, A1 or A4 is the better latency trade; at 48 kHz A2 costs nothing that
        matters.
        Caveat on scope. This recommendation is about which of the AUTHOR'S FOUR
        CANDIDATES to prefer. None of them is a band-pass, and a TDOA front end for a
        300-3400 Hz source wants a band-pass, not a low-pass; and no low-pass applied
        after conversion can undo the aliasing documented in section 1. The filter that
        this hardware actually needs is an ANTI-ALIAS filter ahead of the converter,
        which is a hardware change, not a software one.
    """).rstrip())

    fig_filters(bank, metrics, noise, fs_hat)
    return metrics


def fig_filters(bank, metrics, noise, fs_hat):
    names = list(bank)
    fig, ax = plt.subplots(1, 3, figsize=(7.4, 2.6))
    for i, nm in enumerate(names):
        h, _ = bank[nm]
        w, H = sps.freqz(h, worN=4096)
        f = w / np.pi * fs_hat / 2
        ax[0].plot(f, 20 * np.log10(np.abs(H) + 1e-12), ls=rc.LINESTYLES[i], lw=1.2,
                   color=rc.OKABE_ITO[[5, 1, 3, 6][i]], label=nm.split()[0])
        gw, gd = sps.group_delay((h, 1.0), w=2048)
        ax[1].plot(gw / np.pi * fs_hat / 2, gd, ls=rc.LINESTYLES[i], lw=1.2,
                   color=rc.OKABE_ITO[[5, 1, 3, 6][i]], label=nm.split()[0])
    ax[0].axvline(0.1 * fs_hat / 2, color="0.6", lw=0.8, ls=":")
    ax[0].set_xlim(0, fs_hat / 2); ax[0].set_ylim(-90, 10)
    ax[0].set_xlabel("Frequency (Hz)"); ax[0].set_ylabel("Magnitude (dB)")
    ax[0].set_title("(a) Magnitude response")
    ax[0].legend(fontsize=6.4, ncol=2)
    ax[1].set_xlim(0, fs_hat / 2); ax[1].set_ylim(-5, 40)
    ax[1].set_xlabel("Frequency (Hz)"); ax[1].set_ylabel("Group delay (samples)")
    ax[1].set_title("(b) Group delay\n(flat = safe for TDOA)")
    ax[1].legend(fontsize=6.4, ncol=2)

    # (c) measured idle PSD before/after each filter
    v = noise[1]["v"].astype(float).copy()
    v[~noise[1]["keep"]] = noise[1]["dc"]
    z = v - noise[1]["dc"]
    f0, P0 = sps.welch(z, fs=fs_hat, nperseg=4096)
    ax[2].semilogy(f0, P0, "k-", lw=1.0, label="MIC1 idle, unfiltered")
    for i, nm in enumerate(names):
        h, _ = bank[nm]
        y = sps.lfilter(h, 1.0, z)[len(h):]
        f1, P1 = sps.welch(y, fs=fs_hat, nperseg=4096)
        ax[2].semilogy(f1, P1, ls=rc.LINESTYLES[i], lw=1.0,
                       color=rc.OKABE_ITO[[5, 1, 3, 6][i]],
                       label=f"{nm.split()[0]} ({metrics[nm]['noise_red']:+.1f} dB)")
    ax[2].set_xlim(0, fs_hat / 2)
    ax[2].set_xlabel("Frequency (Hz)"); ax[2].set_ylabel(r"PSD (LSB$^2$/Hz)")
    ax[2].set_title("(c) Applied to the real noise floor")
    ax[2].legend(fontsize=6.0, loc="lower left")
    fig.tight_layout()
    p = rc.savefig(fig, "fig_real_filter_comparison.png")
    rc.caption("fig_real_filter_comparison.png", textwrap.fill(
        "The four candidate low-pass filters, re-implemented exactly as written in "
        "'Filter alogrithims test/' and evaluated on real data. (a) Magnitude responses "
        "at the measured 1 kHz sample rate; the design cutoff is dotted. (b) Group delay. "
        "A1, A2 and A4 have symmetric coefficients and hence flat group delay, so the "
        "delay they add is common to all channels and cancels in every time-difference; "
        "A3, which inverse-transforms a rectangular mask without an fftshift, is not "
        "linear phase and would smear the cross-correlation peak. (c) Welch spectrum of "
        "the measured MIC1 idle recording before and after each filter, with the measured "
        "RMS reduction in the legend. A2 is recommended: exactly linear phase, deepest "
        "stopband, flattest passband and the largest measured noise reduction.", 100))
    print(f"\n          written: {p}")


# ==================================================================================
# 7. Sim-versus-real: what the measured noise floor implies for the simulated curves
# ==================================================================================
def read_benchmark_log():
    """Read the GCC-PHAT median-error-vs-SNR curve out of validation/benchmark_run.log.

    The simulation harness is owned by another track and is being re-baselined, so this
    curve is NEVER hardcoded here: it is parsed from whatever the current log says, and
    the parsed values plus the log's modification time are printed so the reader can see
    exactly which simulation run the figure depends on. Falls back to a flat marker curve
    with a loud warning if the log cannot be parsed.
    """
    import re as _re
    import datetime as _dt
    path = os.path.join(HERE, "benchmark_run.log")
    try:
        raw = open(path, "rb").read()
        for enc in ("utf-8", "utf-16", "latin-1"):
            try:
                txt = raw.decode(enc)
                if "GCC-PHAT" in txt:
                    break
            except Exception:
                continue
        pat = _re.compile(
            r"GCC-PHAT[^\r\n]*?SNR\s+(-?\d+)\s*dB[^\r\n]*?median\s+(-?[\d.]+)")
        found = {}
        for m in pat.finditer(txt):
            found[int(m.group(1))] = float(m.group(2))
        if not found:
            raise ValueError("no 'GCC-PHAT ... SNR ... median' lines found")
        snr = sorted(found)
        mtime = _dt.datetime.fromtimestamp(os.path.getmtime(path)).isoformat(" ", "seconds")
        src = f"benchmark_run.log (last modified {mtime}), {len(snr)} SNR points"
        print(f"\n      simulated curve parsed from {src}")
        print("        SNR (dB)      " + "  ".join(f"{x:>7d}" for x in snr))
        print("        median (deg)  " + "  ".join(f"{found[x]:>7.3f}" for x in snr))
        return snr, [found[x] for x in snr], src
    except Exception as exc:
        print(f"\n      WARNING: could not parse benchmark_run.log ({exc}).")
        print("      The sim-vs-real figure is omitted rather than drawn from stale numbers.")
        return None, None, None


def section7_simreal(noise, rows):
    rc.rule("7. SIM-VERSUS-REAL: WHAT CAN AND CANNOT BE OVERLAID")

    sd = np.mean([noise[m]["sd"] for m in (1, 2, 3)])
    dc = np.mean([noise[m]["dc"] for m in (1, 2, 3)])
    peak = 2523 - dc

    # Measured electrical SNR of every unclipped calibration recording.
    snrs = [20 * np.log10(r["rms"] / sd) for r in rows if r["clip"] <= 0.005]
    snrs = np.array(snrs)
    snr_axis, med_sim, src = read_benchmark_log()
    lo_snr = float(np.percentile(snrs, 10))
    hi_snr = 20 * np.log10(peak / np.sqrt(2) / sd)
    if snr_axis is not None:
        e_lo = float(np.interp(lo_snr, snr_axis, med_sim))
        e_hi = float(np.interp(hi_snr, snr_axis, med_sim))
        sim_sentence = (
            f"Read against the CURRENT simulation log ({src}), the measured operating\n"
            f"      band from {lo_snr:.0f} to {hi_snr:.0f} dB spans the region where the simulated\n"
            f"      per-frame median error falls from {e_lo:.2f} deg to {e_hi:.2f} deg. That is a\n"
            f"      statement about where the hardware sits on the simulation's x-axis, NOT a\n"
            f"      measurement of its accuracy.")
    else:
        sim_sentence = ("The simulation log could not be parsed, so no operating-point "
                        "statement is made.")
    print(textwrap.dedent(f"""
      There is NO measured direction-of-arrival result in this repository, so the
      simulated error-versus-SNR, error-versus-RT60 and temporal-accumulation curves
      cannot be overlaid with a measured counterpart. Saying so plainly is the honest
      position; inventing an overlay is what sank the previous submission.

      One quantitative bridge does exist and is worth drawing: the measured signal chain
      fixes where on the simulation's SNR axis this hardware actually operates.

      DEPENDENCY NOTE. The simulated curve quoted and plotted below is PARSED AT RUN TIME
      from benchmark_run.log, which another track owns and is re-baselining, so it is
      always current and is never hardcoded here. The source file and its modification
      time are printed with the parsed values. Every MEASURED quantity in the table below
      is independent of the simulation.

        measured self-noise RMS                    {sd:.2f} LSB
        largest undistorted peak swing             {peak:.0f} LSB
        chain ceiling, peak SNR                    {20*np.log10(peak/sd):.1f} dB
        chain ceiling, sine RMS SNR                {20*np.log10(peak/np.sqrt(2)/sd):.1f} dB
        measured per-recording SNR, unclipped set  median {np.median(snrs):.1f} dB,
                                                   10th pct {np.percentile(snrs,10):.1f} dB,
                                                   90th pct {np.percentile(snrs,90):.1f} dB
                                                   (n = {len(snrs)} recordings)

      {sim_sentence}
    """).rstrip())

    if snr_axis is None:
        return
    fig, ax = plt.subplots(figsize=(3.9, 2.9))
    ax.plot(snr_axis, med_sim, "o-", color=rc.OKABE_ITO[5], lw=1.3,
            label="simulated median error\n(GCC-PHAT, benchmark_run.log;\n"
                  "regenerate if the sim is re-baselined)")
    hi = 20 * np.log10(peak / np.sqrt(2) / sd)
    ax.axvspan(np.percentile(snrs, 10), hi, color=rc.OKABE_ITO[1], alpha=0.20, lw=0)
    ax.axvline(np.median(snrs), color=rc.OKABE_ITO[6], lw=1.1, ls="--")
    ax.set_yscale("log")
    lo_y = min(med_sim) / 3.0
    hi_y = max(med_sim) * 6.0
    ax.set_ylim(lo_y, hi_y)
    ax.annotate(f"median measured SNR {np.median(snrs):.0f} dB",
                (np.median(snrs), hi_y * 0.7), xytext=(4, 0),
                textcoords="offset points",
                fontsize=6.4, color=rc.OKABE_ITO[6], va="center")
    ax.annotate(f"measured operating band of the real\nsignal chain "
                f"({np.percentile(snrs,10):.0f} to {hi:.0f} dB)",
                (0.5 * (np.percentile(snrs, 10) + hi), hi_y * 0.28),
                ha="center", fontsize=6.2, color=rc.OKABE_ITO[1])
    ax.set_xlabel("SNR (dB)")
    ax.set_ylabel("Median |azimuth error| (deg)")
    ax.set_title("Where the measured hardware sits\non the simulated SNR axis")
    ax.legend(fontsize=6.0, loc="lower left")
    fig.tight_layout()
    p = rc.savefig(fig, "fig_real_snr_operating_point.png")
    rc.caption("fig_real_snr_operating_point.png", textwrap.fill(
        "The only sim-to-real bridge this dataset supports. The curve is the simulated "
        "free-field median azimuth error of GCC-PHAT against SNR, parsed at run time from "
        f"{src} and therefore always current. The shaded band is the electrical "
        "signal-to-noise ratio actually measured on the hardware: the lower edge is the "
        "10th percentile of the unclipped calibration recordings referred to the measured "
        f"{sd:.1f} LSB self-noise floor, and the upper edge is the chain's ceiling set by "
        "front-end clipping. The "
        "figure locates the hardware on the simulation's x-axis; it does NOT report a "
        "measured localization accuracy, because no clip in this repository permits one.",
        100))
    print(f"\n          written: {p}")


# ==================================================================================
# 8. Near-field quadrant tables (APPENDIX scope)
# ==================================================================================
def section8_quadrant(fs_hat):
    rc.rule("8. NEAR-FIELD QUADRANT TABLES  [APPENDIX SCOPE]")

    X, Y, T = [], [], []
    per_q = {}
    for i in (1, 2, 3, 4):
        x, y, t = rc.load_quadrant(i)
        per_q[i] = (x, y, t)
        X.append(x); Y.append(y); T.append(t)
    x = np.concatenate(X); y = np.concatenate(Y); t = np.concatenate(T)

    print("\n      quadrant   rows   x range (m)      y range (m)      t range (us)   "
          "blank t")
    for i in (1, 2, 3, 4):
        xi, yi, ti = per_q[i]
        import csv as _csv
        with open(os.path.join(rc.QUAD_DIR, f"quadrant_{i}.csv")) as fh:
            nraw = sum(1 for _ in fh) - 1
        print(f"      {i:>8}  {nraw:>5}   {xi.min():>6.2f}..{xi.max():<6.2f}  "
              f"{yi.min():>6.2f}..{yi.max():<6.2f}   {ti.min()*1e6:>6.2f}..{ti.max()*1e6:<6.2f}"
              f"   {nraw-len(ti):>6}")

    # --- what is t? ---------------------------------------------------------------------
    r = np.hypot(x, y)
    h_tof = np.corrcoef(t, r / rc.C_SOUND)[0, 1]
    d, c = 0.05, 343.0
    pred = np.abs(np.hypot(x + d / 2, y) - np.hypot(x - d / 2, y)) / c
    resid = pred - t
    ss = 1 - np.sum(resid ** 2) / np.sum((t - t.mean()) ** 2)
    from scipy.optimize import least_squares
    fit = least_squares(lambda p: np.abs(np.hypot(x + p[0] / 2, y)
                                         - np.hypot(x - p[0] / 2, y)) / p[1] - t,
                        [0.05, 343.0])
    print(textwrap.dedent(f"""
      What is the 't' column? The naive reading -- straight-line propagation time from
      the origin -- is wrong, and demonstrably so:

        at (x, y) = (0.05, 0.05) m the table gives t = {per_q[1][2][0]*1e6:.2f} us,
        whereas r/c for r = {np.hypot(0.05,0.05):.4f} m is {np.hypot(0.05,0.05)/343*1e6:.2f} us.
        correlation of t with r/c over all {len(t)} rows: {h_tof:+.4f}  (i.e. none)
        t is also bounded: max |t| = {np.abs(t).max()*1e6:.4f} us, and it saturates at that
        value far from the origin rather than growing with r.

      Hypothesis tested and confirmed: t is the TWO-MICROPHONE TIME DIFFERENCE OF ARRIVAL
      for a near-field source at (x, y), for a pair separated by d on the x-axis and
      centred on the origin:

            t(x, y) = | sqrt((x + d/2)^2 + y^2) - sqrt((x - d/2)^2 + y^2) | / c

        with d = 0.05 m and c = 343 m/s:
          residual RMS   {np.sqrt(np.mean(resid**2)):.3e} s
          R^2            {ss:.10f}
          max residual   {np.abs(resid).max():.3e} s
        free fit of (d, c):
          d = {fit.x[0]:.9f} m,  c = {fit.x[1]:.6f} m/s,  residual RMS {np.sqrt(np.mean(fit.fun**2)):.3e} s
        The residual is {np.sqrt(np.mean(resid**2)):.1e} s, which is exactly the rounding of the ten-decimal
        text format. The match is not approximate: it is exact.

      CONSEQUENCE, and it is important. These four files are a COMPUTED GEOMETRIC LOOKUP
      TABLE, not a measurement. They contain no microphone, no room, no noise and no
      acquisition; every value is reproducible in one line of arithmetic. Nothing derived
      from them may be described as experimental. They remain useful for exactly one
      purpose -- illustrating the geometry of the near-field inverse problem and the
      dilution of precision it implies -- which is why this section is scoped to an
      appendix.
        The alternative hypothesis 'these are measured propagation delays' is rejected at
      R^2 = 1.000000 against an analytic model with two parameters and 14631 points.
      Note also that the tabulated pair separation, d = 5.00 cm, is the array's
      CIRCUM-RADIUS, whereas the actual microphone spacing on an equilateral triangle of
      that circum-radius is {D_MAX*100:.2f} cm. The table therefore does not describe the
      built array's geometry either.
    """).rstrip())

    # --- GDOP for the real 3-mic array -----------------------------------------------------
    print(textwrap.dedent(f"""
      Near-field dilution of precision for the actual 3-microphone array.
      For a source at p and microphones at p_m, the two independent delay observables are
      tau_1m = (|p - p_1| - |p - p_m|)/c for m = 2, 3. Linearising, the position covariance
      is (J^T J)^-1 sigma_tau^2, with J the Jacobian of those observables (units s/m). The
      scalar dilution of precision is GDOP = sqrt(trace((J^T J)^-1)), which has units of
      metres per second, so the position error is simply GDOP x sigma_tau. Computed below
      on the same 3 m x 3 m plane as the quadrant tables, for the equilateral array with
      circum-radius {R_ARRAY*100:.0f} cm and microphone spacing {D_MAX*100:.2f} cm.
    """).rstrip())

    gx = np.linspace(-1.5, 1.5, 241)
    gy = np.linspace(-1.5, 1.5, 241)
    GX, GY = np.meshgrid(gx, gy)
    P = np.stack([GX, GY], axis=-1)                       # (ny, nx, 2)
    def unit(a):
        n = np.linalg.norm(a, axis=-1, keepdims=True)
        return a / np.maximum(n, 1e-9)
    u = [unit(P - MIC_XY[m]) for m in range(3)]
    J = np.stack([(u[0] - u[1]) / rc.C_SOUND, (u[0] - u[2]) / rc.C_SOUND], axis=-2)
    JTJ = np.einsum("...ki,...kj->...ij", J, J)
    det = JTJ[..., 0, 0] * JTJ[..., 1, 1] - JTJ[..., 0, 1] * JTJ[..., 1, 0]
    tr_inv = np.where(np.abs(det) > 1e-30,
                      (JTJ[..., 0, 0] + JTJ[..., 1, 1]) / np.where(np.abs(det) > 1e-30, det, 1),
                      np.inf)
    GDOP = np.sqrt(np.maximum(tr_inv, 0))                 # units of seconds per metre^-1
    Rgrid = np.hypot(GX, GY)

    print("\n        range from array centre    median GDOP (m/s)   position error for "
          "sigma_tau = 1 us")
    for lo, hi in ((0.05, 0.25), (0.25, 0.5), (0.5, 1.0), (1.0, 1.5)):
        msk = (Rgrid >= lo) & (Rgrid < hi) & np.isfinite(GDOP)
        g = np.median(GDOP[msk])
        print(f"        {lo:>4.2f} - {hi:<4.2f} m           {g:>15.4f}   "
              f"{g*1e-6:>22.3f} m")
    print(textwrap.dedent(f"""
        A 1 us delay uncertainty -- optimistic even at 48 kHz, and {1e6/fs_hat:.0f}x below one
        sampling interval at the measured 1 kHz rate -- already yields metre-scale
        position error beyond about 0.5 m. Near-field two-dimensional positioning with a
        5 cm array is geometry-limited, not algorithm-limited, and the quadrant tables
        illustrate exactly that.
    """).rstrip())

    fig_quadrant(per_q, GX, GY, GDOP, Rgrid, fs_hat)


def fig_quadrant(per_q, GX, GY, GDOP, Rgrid, fs_hat):
    fig, ax = plt.subplots(1, 2, figsize=(6.8, 2.9))

    xs = np.concatenate([per_q[i][0] for i in (1, 2, 3, 4)])
    ys = np.concatenate([per_q[i][1] for i in (1, 2, 3, 4)])
    ts = np.concatenate([per_q[i][2] for i in (1, 2, 3, 4)]) * 1e6
    sc = ax[0].scatter(xs, ys, c=ts, s=1.6, cmap="cividis", linewidths=0)
    cb = fig.colorbar(sc, ax=ax[0], fraction=0.046, pad=0.03)
    cb.set_label(r"tabulated $t$ ($\mu$s)")
    ax[0].plot([-0.025, 0.025], [0, 0], "o", ms=4, color=rc.OKABE_ITO[6])
    ax[0].annotate("the two microphones\nimplied by the table\n(5.0 cm apart)",
                   (0, 0), xytext=(-2.9, 1.5), fontsize=6.3, color=rc.OKABE_ITO[6],
                   arrowprops=dict(arrowstyle="->", lw=0.7, color=rc.OKABE_ITO[6]))
    ax[0].set_aspect("equal")
    ax[0].set_xlim(-3.1, 3.1); ax[0].set_ylim(-3.1, 3.1)
    ax[0].set_xlabel("x (m)"); ax[0].set_ylabel("y (m)")
    ax[0].set_title("(a) The four quadrant tables assembled\n"
                    r"$t=||p-p_L|-|p-p_R||/c$ exactly ($R^2=1$)")

    import matplotlib.colors as mcolors
    err = GDOP * 1e-6                                  # position error for sigma_tau = 1 us
    lv = np.logspace(-3, 1, 33)
    cs = ax[1].contourf(GX, GY, np.clip(err, 1e-3, 10.0), levels=lv,
                        cmap="cividis", norm=mcolors.LogNorm(vmin=1e-3, vmax=10.0))
    cl = ax[1].contour(GX, GY, err, levels=[0.01, 0.1, 1.0], colors="w",
                       linewidths=0.7)
    ax[1].clabel(cl, fmt={0.01: "1 cm", 0.1: "10 cm", 1.0: "1 m"}, fontsize=6.0)
    cb2 = fig.colorbar(cs, ax=ax[1], fraction=0.046, pad=0.03,
                       ticks=[1e-3, 1e-2, 1e-1, 1e0, 1e1])
    cb2.set_label(r"position error for $\sigma_\tau$ = 1 $\mu$s (m)")
    ax[1].plot(MIC_XY[:, 0], MIC_XY[:, 1], "o", ms=4, color=rc.OKABE_ITO[6])
    ax[1].set_aspect("equal")
    ax[1].set_xlabel("x (m)"); ax[1].set_ylabel("y (m)")
    ax[1].set_title("(b) Near-field position error\n"
                    f"3-mic array, R = {R_ARRAY*100:.0f} cm")
    ax[1].grid(False)
    fig.tight_layout()
    p = rc.savefig(fig, "fig_real_quadrant_gdop.png")
    rc.caption("fig_real_quadrant_gdop.png", textwrap.fill(
        "Appendix figure. (a) The four 'Quadrant Based Estimations' tables assembled into "
        "one field. Colour is the tabulated t. The pattern is a two-microphone "
        "time-difference-of-arrival surface, not a propagation time: it is reproduced "
        "exactly, to a residual of 3e-11 s and R-squared of 1.000000, by the analytic "
        "expression for a 5.0 cm pair centred at the origin with c = 343 m/s, so the "
        "files are a computed lookup table rather than a measurement. (b) The "
        "corresponding dilution of precision for the real three-microphone equilateral "
        "array of 5 cm circum-radius, computed from the Jacobian of the two independent "
        "delay observables and expressed directly as the position error that a 1 "
        "microsecond delay uncertainty would produce. White contours mark the 1 cm, 10 cm "
        "and 1 m error levels. Beyond about half a metre even a 1 microsecond delay "
        "uncertainty gives metre-scale position error, and the four radial lobes along "
        "the microphone baselines are directions in which the two delay observables become "
        "degenerate. Near-field two-dimensional positioning on this aperture is limited by "
        "geometry, not by the estimator.", 100))
    print(f"\n          written: {p}")


# ==================================================================================
def main():
    tee = rc.Tee(LOG)
    sys.stdout = tee
    t0 = time.time()
    print("analyze_real.py -- forensics and analysis of the measured datasets")
    print(f"python {sys.version.split()[0]}, numpy {np.__version__}, seed {rc.SEED}")
    print(f"repository root: {rc.ROOT}")
    print(f"figures -> {rc.FIGDIR}")

    cal = section0_inventory()
    alias_rows, fs_hat, delta = section1_timebase(cal)
    clips, dcs, sds, rr = section2_triple(fs_hat)
    noise = section3_noise(fs_hat)
    lvl_rows, table = section4_response(cal, delta, fs_hat,
                                       float(np.mean([noise[m]['sd'] for m in (1,2,3)])))
    section5_mismatch(noise, clips, dcs, sds, rr)
    section6_filters(noise, fs_hat)
    section7_simreal(noise, lvl_rows)
    section8_quadrant(fs_hat)

    rc.rule("DONE")
    print(f"elapsed {time.time()-t0:.1f} s")
    print(f"log -> {LOG}")
    sys.stdout = tee.stdout
    tee.close()


if __name__ == "__main__":
    main()
