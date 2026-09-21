# Mathematical model and analysis

**Reference document for the Acta Acustica Technical & Applied Article.**
Every equation is numbered `(M1), (M2), ...` for the writing track to lift.
Every numeric value is either (a) read from a log file or CSV in this repository,
(b) derived in full below, or (c) produced by a verification run whose command is
stated in the surrounding text. Nothing is asserted without one of those three sources.

Citation keys in square brackets refer to `paper/references.md`.

> **Status flags used below**
> `[DERIVED]` analytic result proved here.
> `[VERIFIED n]` analytic result checked numerically against the code; the check is described.
> `[LOG]` value read directly from `validation/benchmark_run.log` or `validation/ablation_run.log`.
> `[NEW RUN]` value produced by a verification run performed for this document; the run is
> described in enough detail to reproduce, but it did **not** modify any repository file.
> `[MEASURE]` a slot for a hardware measurement that does not yet exist.

---

## 0. Summary of the analytical results

1. The array's azimuth error obeys a single closed-form law,
   $\sigma_\theta = c\,\sigma_\tau /(\sqrt{4.5}\,R)$, which reproduces the simulated
   RMSE at 0, 10 and 40 dB to within 2 % (Section 4.4). Accuracy is aperture-limited.
2. For the **equilateral** three-microphone array with uniform weights, the azimuth
   variance is **direction-independent** (isotropic). Direction dependence is introduced
   *only* by weighting or by dropping a pair (Section 4.3). This corrects a common
   assumption and is a reason not to gate.
3. At $M=3$ the linear system has redundancy exactly 1. Fault **detection** is possible;
   fault **exclusion** is provably impossible, because the three single-pair fault
   hypotheses produce residual signatures that are identical up to sign (Section 5.4).
   This is a rigorous statement of the paper's negative result.
4. Temporal accumulation: $\mathrm{MSE}(T) = b^2 + \sigma_1^2/T$ (M62). The free-field fit gives
   $b = 0.30^\circ \pm 0.32^\circ$ (consistent with zero) and reproduces the measured curve
   to 0.04$^\circ$. The reverberation bias $b$ was measured **directly** at fixed RIR and is
   $1.79^\circ / 2.22^\circ / 3.15^\circ$ at RT60 $=0.15/0.30/0.60$ s (Section 6.5). The
   bias floor is real, monotone in RT60, and statistically significant.
5. **Sampling-rate requirement** (Section 3): $I f_s \geq c/(\sqrt{54}\,R\,\varepsilon_q)$.
   At $f_s = 1$ kHz the maximum inter-microphone delay is 0.25 samples and the array is blind.
   The minimum viable rate is $f_s \gtrsim 8$ kHz with $I \geq 8$.
6. **The measured compute ratios in `benchmark_run.log` are not algorithmic complexity ratios.**
   The FLOP model predicts SRP-PHAT $\approx 1.006\times$ GCC-PHAT for this implementation;
   the measured ratio is $4.26\times$, and the gap is fully accounted for by Python
   interpreter overhead in the un-vectorised grid loop (Section 7.4). The one ratio the model
   *does* predict correctly is proposed/GCC ($+7\%$ predicted, $+5\%$ measured).
7. **A defect in the implemented GCC-PHAT front end was found and quantified** (Sections 2.4, 8.3).
   The PHAT weight is applied over the full 0–24 kHz band while the source occupies 300–3400 Hz.
   At 10 dB nominal SNR, 81 % of the bins receiving unit weight are out-of-band noise. Restricting
   the weight to the source band reduces per-frame azimuth RMSE from 4.14$^\circ$ to 0.31$^\circ$
   and brings the estimator to within a factor 1.9 of the Cramér–Rao bound. **All existing logs
   were produced with the full-band version.** How to handle this is a decision for the
   writing track; it is flagged, not silently applied.
8. Near-field 2-D position from a 5 cm array is unusable beyond
   $r_{\mathrm{break}} \approx R^2/(3.8\,c\,\sigma_\tau)$, which is 2.5 m at the CRB and
   0.10 m at the precision the estimator actually achieves (Section 9.5). This quantitatively
   justifies confining the quadrant material to an appendix.

---

## 1. Notation and signal model

### 1.1 Notation

| Symbol | Meaning | Units |
|---|---|---|
| $M$ | number of microphones ($M=3$ throughout) | — |
| $P$ | number of microphone pairs, $P=M(M-1)/2 = 3$ | — |
| $m,i,j$ | microphone indices, $1 \le m \le M$ | — |
| $\mathbf{p}_m$ | position of microphone $m$ in the horizontal plane | m |
| $R$ | circum-radius of the equilateral array | m |
| $D$ | maximum inter-microphone spacing, $D = \sqrt3\,R$ | m |
| $d_{ij}$ | $\|\mathbf{p}_i-\mathbf{p}_j\|$ | m |
| $\theta$ | source azimuth, measured from the $+x$ axis, wrapped to $(-180^\circ,180^\circ]$ | deg or rad |
| $\mathbf{u}(\theta)$ | unit propagation-direction vector $(\cos\theta,\sin\theta)^{\mathsf T}$ | — |
| $\mathbf{e}_\theta$ | unit tangential vector $(-\sin\theta,\cos\theta)^{\mathsf T}$ | — |
| $r$ | source range from the array centroid | m |
| $c$ | speed of sound (343.0 in the code) | m s$^{-1}$ |
| $s(t)$ | source waveform at the array centroid | (arb.) |
| $n_m(t)$ | additive sensor noise at microphone $m$ | (arb.) |
| $x_m(t)$ | signal received at microphone $m$ | (arb.) |
| $\tau_m$ | propagation delay of microphone $m$ relative to the centroid | s |
| $\tau_{ij}$ | time difference of arrival (TDOA) $\tau_i-\tau_j$ | s |
| $\hat\tau_{ij}$ | GCC-PHAT estimate of $\tau_{ij}$ | s |
| $\sigma_\tau$ | standard deviation of the per-pair TDOA error | s |
| $\sigma_\theta$ | standard deviation of the azimuth error | rad |
| $f_s$ | per-channel sample rate (48 000 in the code) | Hz |
| $N$ | snapshot length in samples (2048 in the code) | — |
| $T_{\mathrm{obs}}$ | snapshot duration $N/f_s$ = 42.67 ms | s |
| $H$ | analysis hop between accumulated frames ($H=N$ in `ablation.py`) | samples |
| $n$ | zero-padded FFT length, $n = 2N$ | — |
| $K$ | number of real-FFT bins, $K = n/2+1$ | — |
| $I$ | correlation interpolation factor (`interp=8` in the code) | — |
| $q$ | effective lag quantisation step, $q = 1/(I f_s)$ | s |
| $G$ | number of azimuth grid points in SRP-PHAT / MUSIC ($G=360$) | — |
| $[f_1,f_2]$ | source band, 300–3400 Hz in the code | Hz |
| $B$ | source bandwidth $f_2-f_1$ = 3100 Hz | Hz |
| $\beta$ | root-mean-square radian bandwidth of the source (M81) | rad s$^{-1}$ |
| $\gamma_{ij}(f)$ | magnitude-squared coherence between channels $i$ and $j$ | — |
| $\Psi(f)$ | generalized-correlation frequency weighting | — |
| $\rho_m$ | peak-to-sidelobe ratio (PSR) of pair $m$'s GCC | — |
| $w_t$ | accumulation weight of frame $t$ | — |
| $T$ | number of accumulated frames | — |
| $L$ | accumulation latency, $L = TH/f_s$ | s |
| $b$ | deterministic azimuth bias (reverberation / near-field) | rad or deg |
| $\sigma_1$ | per-frame azimuth error standard deviation | rad or deg |
| $\lambda$ | EWMA forgetting factor | — |
| $\mathbf{A}$ | $P\times 2$ baseline matrix, rows $(\mathbf{p}_i-\mathbf{p}_j)^{\mathsf T}$ | m |
| $\mathbf{b}$ | right-hand side, $b_{ij} = -c\,\hat\tau_{ij}$ | m |
| $\hat{\mathbf{u}}$ | unconstrained least-squares solution of $\mathbf{A}\mathbf{u}=\mathbf{b}$ | — |
| RT60 | reverberation time | s |
| $Q$ | ADC bit depth | bits |

**Notation warning for the writing track.** "5 cm aperture" is ambiguous in the current
draft. In `doa_benchmark.py`, `R = 0.05` is the **circum-radius**; the largest
inter-microphone spacing is $D=\sqrt3 R = 8.66$ cm. The `Quadrant Based Estimations/`
data, by contrast, is generated from a **5 cm two-microphone baseline** (Section 9.1).
The paper must state which quantity it means every time it says "5 cm".

### 1.2 Array geometry as configured

$$\mathbf{p}_m = R\big(\cos\phi_m,\ \sin\phi_m\big)^{\mathsf T},\qquad
\phi_m \in \{90^\circ,\ 210^\circ,\ 330^\circ\},\qquad R = 0.05\ \mathrm{m}. \tag{M1}$$

Numerically $\mathbf{p}_1=(0,\,5)$, $\mathbf{p}_2=(-4.33,\,-2.5)$, $\mathbf{p}_3=(4.33,\,-2.5)$ cm
[LOG, `benchmark_run.log` header]. The centroid is at the origin:

$$\sum_{m=1}^{M}\mathbf{p}_m = \mathbf{0},\qquad
\sum_{m=1}^{M}\mathbf{p}_m\mathbf{p}_m^{\mathsf T} = \tfrac{3}{2}R^2\,\mathbf{I}_2 . \tag{M2}$$

The second identity in (M2) is the reason almost everything below is isotropic; it holds for
any set of $M\ge 3$ equally spaced points on a circle. [VERIFIED: $\mathbf{A}^{\mathsf T}\mathbf{A}$
computed from `MIC_XY` equals $4.5R^2\mathbf{I}$ to machine precision.]

### 1.3 Far-field plane-wave model

$$x_m(t) = s\!\left(t-\tau_m\right) + n_m(t),\qquad
\tau_m = -\frac{\mathbf{p}_m^{\mathsf T}\mathbf{u}(\theta)}{c}, \tag{M3}$$

which is exactly `steering_delays()` in `doa_benchmark.py`. The pairwise TDOA is

$$\tau_{ij} = \tau_i-\tau_j = -\frac{(\mathbf{p}_i-\mathbf{p}_j)^{\mathsf T}\mathbf{u}(\theta)}{c}
= -\frac{d_{ij}}{c}\cos\!\big(\theta-\alpha_{ij}\big), \tag{M4}$$

where $\alpha_{ij}$ is the bearing of the baseline $\mathbf{p}_i-\mathbf{p}_j$. Equation (M4)
immediately gives the physical feasibility bound used by the gate,

$$|\tau_{ij}| \le \frac{d_{ij}}{c} = \frac{\sqrt3\,R}{c} = 252.5\ \mu\mathrm{s}
= 12.12\ \text{samples at } 48\ \mathrm{kHz}. \tag{M5}$$

**Assumptions, stated explicitly.** The paper must list all of these.

* **A1 Single source.** One coherent source is active. No source-separation stage exists.
* **A2 Horizontal plane.** The source lies in the plane of the array. A planar array cannot
  distinguish elevation; an out-of-plane source at elevation $\psi$ produces the delays of an
  in-plane source with an effective aperture $R\cos\psi$, i.e. a *cone of confusion* around
  the array normal. Elevation error therefore maps into an apparent aperture reduction, not
  into an azimuth bias, for a symmetric array.
* **A3 Plane wave.** $r \gg D$; quantified in Section 1.5.
* **A4 Anechoic baseline.** (M3) has no reflections. Reverberation is added in
  `reverb_robustness.py` by an image-source model [CITE Allen & Berkley 1979], [CITE Habets 2006],
  and enters the analysis as the bias term $b$ of Section 6.5.
* **A5 Noise.** $n_m(t)$ are zero-mean, mutually uncorrelated across $m$, and white.
  In `simulate()` they are i.i.d. Gaussian across the **full** band $[0,f_s/2]$, whereas the
  source occupies $[f_1,f_2]$ only. This asymmetry is not cosmetic — see Section 2.4.
* **A6 Non-dispersive, homogeneous medium.** $c$ is constant in space and frequency. Air is
  non-dispersive below 100 kHz to well within any accuracy considered here.
* **A7 Identical, omnidirectional, gain- and phase-matched sensors.** The simulation assumes
  this exactly. Real MEMS microphones have sensitivity tolerance (typically $\pm 1$ dB) and
  phase mismatch; the resulting delay error appears as a *fixed per-pair bias* $\Delta\tau_{ij}$
  and therefore, like reverberation, as a term that temporal accumulation cannot remove.
  [MEASURE: per-channel gain and phase mismatch of the assembled board.]
* **A8 Perfectly synchronous sampling.** Inter-channel clock skew of $\delta$ seconds is
  indistinguishable from a TDOA offset of $\delta$; by (M4) an inter-channel skew of one
  sample period at 48 kHz (20.8 $\mu$s) corresponds to an azimuth error of order $4^\circ$.
  [MEASURE: channel-to-channel sample alignment on the board.]

### 1.4 Speed of sound and its temperature dependence

$$c(T_C) = 331.3\sqrt{1+\frac{T_C}{273.15}}\ \ \mathrm{m\,s^{-1}}
\ \approx\ 331.3 + 0.606\,T_C , \tag{M6}$$

with $T_C$ in $^\circ$C. The code uses $c = 343.0$ m s$^{-1}$, i.e. $T_C \approx 20\,^\circ$C.
Differentiating (M4) at fixed $\tau$, a relative error $\delta c/c$ produces an azimuth error

$$\delta\theta = \frac{\delta c}{c}\,\tan\!\big(\theta-\alpha_{ij}\big) \tag{M7}$$

for a single pair, which is unbounded near endfire. For the three-pair least-squares solution
of Section 4 the sensitivity is bounded, because $\mathbf{u}$ scales uniformly: a relative
error $\delta c/c$ scales $\hat{\mathbf u}$ by $(1+\delta c/c)$ and leaves
$\hat\theta = \operatorname{atan2}(\hat u_y,\hat u_x)$ **exactly unchanged**.

$$\boxed{\ \text{The three-pair LS azimuth estimator of Section 4 is invariant to errors in } c.\ } \tag{M8}$$

This is a genuine and easily-overlooked robustness property of the estimator, and it is worth
one sentence in the paper: a $\pm 10\,^\circ$C temperature uncertainty ($\pm 1.8$ % in $c$)
costs nothing in azimuth. It does *not* hold for the near-field 2-D fix of Section 9, where
$c$ sets the absolute scale.

### 1.5 Far-field validity, and the criterion that actually matters

The textbook Fraunhofer distance is $r_{\mathrm{FF}} = 2D^2/\lambda$ with $D = \sqrt3 R = 8.66$ cm:

| $f$ (Hz) | $\lambda$ (m) | $2D^2/\lambda$ (m) |
|---|---|---|
| 300 | 1.143 | 0.013 |
| 1000 | 0.343 | 0.044 |
| 2000 | 0.172 | 0.088 |
| 3400 | 0.101 | **0.149** |

[VERIFIED by direct evaluation.] The binding case is the top of the source band:
$r \gtrsim 15$ cm. Taken at face value this would say the array is in the far field for
essentially any practical source distance.

**That criterion is too weak for TDOA processing.** $2D^2/\lambda$ corresponds to a maximum
wavefront phase error of $\pi/8$, i.e. a path error of $\lambda/16$, which at 3400 Hz is
6.3 mm, i.e. **18.4 $\mu$s of delay** — far larger than the delay precision the estimator can
achieve (Section 8). The correct criterion is that the curvature-induced TDOA error be small
compared with $\sigma_\tau$.

Expanding the exact range to microphone $m$ for a source at $\mathbf{x}_s = r\mathbf{u}$,

$$\|\mathbf{x}_s-\mathbf{p}_m\| = r - \mathbf{p}_m^{\mathsf T}\mathbf{u}
+ \frac{\|\mathbf{p}_m\|^2-(\mathbf{p}_m^{\mathsf T}\mathbf{u})^2}{2r} + \mathcal{O}(r^{-2}), \tag{M9}$$

and using $\|\mathbf{p}_m\| = R$ for all $m$, the curvature contribution to the TDOA is

$$\Delta\tau_{ij}
= \frac{(\mathbf{p}_j^{\mathsf T}\mathbf{u})^2-(\mathbf{p}_i^{\mathsf T}\mathbf{u})^2}{2rc}
= \frac{R^2}{4rc}\Big[\cos 2(\phi_j-\theta)-\cos 2(\phi_i-\theta)\Big],
\qquad |\Delta\tau_{ij}| \le \frac{R^2}{2rc}. \tag{M10}$$

Propagating (M10) through the least-squares inversion of Section 4 and using
$\sum_m e^{\mathrm{i}\phi_m}=0$, $\sum_m e^{3\mathrm{i}\phi_m}=-3\mathrm{i}$ for
$\phi_m\in\{90^\circ,210^\circ,330^\circ\}$, the azimuth bias caused by using the plane-wave
model at finite range collapses to a remarkably simple closed form:

$$\boxed{\ \delta\theta_{\mathrm{nf}}(r,\theta) \;=\; -\,\frac{R}{4r}\,\cos 3\theta \quad\text{(radians)}\ } \tag{M11}$$

[DERIVED; VERIFIED: maximum discrepancy against the exact spherical-wave TDOA propagated
through the LS solver is $0.001^\circ$ at $r=1$ m, $0.037^\circ$ at $r=0.3$ m, against an
amplitude of $0.716^\circ$ and $2.387^\circ$ respectively.]

Three consequences worth stating in the paper:

1. The near-field bias has **three-fold symmetry** ($\cos 3\theta$), inherited from the
   triangular geometry, and vanishes at $\theta = 30^\circ + k\cdot 60^\circ$.
2. Its amplitude is $R/(4r)$ rad $= 0.716^\circ \times (1\,\mathrm{m}/r)$ for $R = 5$ cm.
3. It is **frame-invariant**, and therefore, exactly like reverberation, it is a bias that
   temporal accumulation cannot remove. It belongs in the $b$ of (M62).

Requiring $|\delta\theta_{\mathrm{nf}}| \le \varepsilon$ gives the operational far-field condition

$$r \ \ge\ \frac{R}{4\varepsilon}\qquad (\varepsilon \text{ in radians}). \tag{M12}$$

For $\varepsilon = 0.5^\circ$ this is $r \ge 1.43$ m; for $\varepsilon=1^\circ$, $r\ge 0.72$ m.
Compare with the Fraunhofer figure of 0.15 m: **the plane-wave assumption is roughly an order
of magnitude more demanding than the Fraunhofer distance suggests, once one asks for
sub-degree accuracy.**

This matters directly for the real data. The `Triple Mic Samples/` headers label source
positions such as `(0,15)`; if those are centimetres, $r = 0.15$ m and (M11) predicts a
systematic azimuth bias of up to $4.8^\circ$ from wavefront curvature alone.
[MEASURE: confirm the units and the exact source coordinates of the `Triple Mic Samples`
campaign. If they are centimetres, the far-field azimuth model does not apply to that data
and the near-field model of Section 9 must be used instead.]

---

## 2. GCC-PHAT and TDOA estimation

### 2.1 Cross-power spectral density and the generalized correlator

With $X_i(f)$ the Fourier transform of the windowed snapshot, the estimated cross-power
spectral density (CPSD) is

$$\hat G_{ij}(f) = X_i(f)\,X_j^{*}(f), \tag{M13}$$

and the generalized cross-correlation with weighting $\Psi(f)$ is

$$R^{(\Psi)}_{ij}(\tau) = \int_{-\infty}^{\infty} \Psi(f)\,\hat G_{ij}(f)\,e^{\mathrm{j}2\pi f\tau}\,\mathrm{d}f .
\tag{M14}$$

[CITE Knapp & Carter 1976]. The phase transform is $\Psi_{\mathrm{PHAT}} = 1/|\hat G_{ij}(f)|$,
so that

$$R^{\mathrm{PHAT}}_{ij}(\tau) = \int \frac{\hat G_{ij}(f)}{|\hat G_{ij}(f)|}\,
e^{\mathrm{j}2\pi f\tau}\,\mathrm{d}f
= \int e^{\mathrm{j}\angle \hat G_{ij}(f)} e^{\mathrm{j}2\pi f\tau}\,\mathrm{d}f . \tag{M15}$$

### 2.2 The regularized PHAT actually implemented

`gcc_phat()` does **not** implement (M15). It implements

$$\Psi_{\mathrm{reg}}(f) = \frac{1}{\max\!\big(|\hat G_{ij}(f)|,\ \epsilon\big)},
\qquad \epsilon = 10^{-3}\max_{f'}|\hat G_{ij}(f')| . \tag{M16}$$

Bins more than 60 dB below the strongest bin are therefore *not* whitened to unit magnitude but
are left attenuated in proportion to their own magnitude. The stated motivation in the source
comment is correct: without (M16) the numerical phase of near-zero bins is amplified to unit
weight and high-SNR accuracy collapses. Section 2.4 shows that the 60 dB floor is nonetheless
far too permissive for the noise model used.

### 2.3 Peak search and sub-sample refinement, as implemented

The implementation computes the correlation on a lag grid $I$ times finer than the sample
period by zero-padding in the frequency domain before the inverse transform:

$$\hat R_{ij}[k] = \mathrm{IRFFT}\Big\{\Psi_{\mathrm{reg}}\hat G_{ij}\Big\}_{\text{length } I n},
\qquad n = 2N,\ I = 8, \tag{M17}$$

$$\hat\tau_{ij} = \frac{\arg\max_{|k|\le In/2}\ \hat R_{ij}[k]}{I f_s}. \tag{M18}$$

**There is no parabolic interpolation in the code.** Frequency-domain zero padding is exact
band-limited (sinc) interpolation of the correlation sequence, so (M17)–(M18) is a plain
argmax on a grid of step

$$q = \frac{1}{I f_s} = \frac{1}{8\times 48000} = 2.604\ \mu\mathrm{s}. \tag{M19}$$

This is worth an explicit sentence in the paper, because the natural embedded implementation
is different. If the firmware instead computes the correlation on the native lag grid and
refines by fitting a parabola to the three samples around the peak,

$$\hat\delta = \frac{1}{2}\,\frac{\hat R[k_0-1]-\hat R[k_0+1]}
{\hat R[k_0-1]-2\hat R[k_0]+\hat R[k_0+1]},\qquad
\hat\tau = \frac{k_0+\hat\delta}{f_s}, \tag{M20}$$

then a *systematic* interpolation bias appears, because a PHAT-whitened correlation peak is a
sinc, not a parabola. [VERIFIED: applying (M20) to an ideal sampled sinc gives a maximum bias
of **0.119 samples** and an r.m.s. bias of 0.085 samples over $\hat\delta\in[-0.5,0.5]$;
for a Gaussian peak the maximum bias is 0.095 samples.] At 48 kHz, 0.119 samples is 2.5 $\mu$s,
which by (M40) corresponds to $0.46^\circ$ of azimuth — comparable to the entire quantisation
budget. The bias is deterministic in $\hat\delta$ and can be removed by a lookup-table
correction, or avoided by using $I\ge 4$ frequency-domain interpolation. Either way, the
paper should not claim parabolic refinement is free.

### 2.4 Why PHAT helps in reverberation and hurts at low SNR

Write $x_i = h_i * s + n_i$, so $G_{ij}(f) = S(f)H_i(f)H_j^{*}(f) + \text{(noise terms)}$.

**Reverberation.** The information about $\tau_{ij}$ lives entirely in $\angle G_{ij}(f)$;
the magnitude $|S(f)H_i(f)H_j^{*}(f)|$ carries the source spectrum *and* the room's
comb-filtering, neither of which is informative. Dividing by $|G_{ij}|$ removes both. The
effect on the correlation shape follows from (M15): the peak width becomes $\sim 1/f_s$
(set by the processing band) instead of $\sim 1/B$ (set by the source band), a sharpening by
the factor $f_s/(2B) = 7.74$ here. A sharper peak is less easily displaced by a reflection
arriving within one correlation width, which is precisely the reverberation benefit
[CITE Knapp & Carter 1976], [CITE Brandstein & Silverman 1997].

**Low SNR.** The maximum-likelihood weighting for the generalized correlator is

$$\Psi_{\mathrm{ML}}(f) = \frac{1}{|G_{ij}(f)|}\cdot
\frac{|\gamma_{ij}(f)|^{2}}{1-|\gamma_{ij}(f)|^{2}} , \tag{M21}$$

so PHAT is exactly ML **if and only if** $|\gamma_{ij}(f)|^2/(1-|\gamma_{ij}(f)|^2)$ is
constant across the processing band [CITE Knapp & Carter 1976]. PHAT discards the coherence
factor and therefore gives a noise-only bin, where $|\gamma|\to 0$, exactly the same weight
as a fully coherent bin. The consequence is quantifiable. Model the whitened cross-spectrum
as unit-modulus with the correct linear phase inside the coherent band $B_{\mathrm{coh}}$ and
uniformly random phase outside it. Then the deterministic part of the correlation has
curvature at the peak

$$\left|R_s''(0)\right| = 2\!\int_{B_{\mathrm{coh}}} (2\pi f)^2\,\mathrm{d}f , \tag{M22}$$

while the derivative of the random part at the peak has standard deviation
$\propto \big(\Delta f \int_{B_{\mathrm{inc}}} (2\pi f)^2\,\mathrm{d}f\big)^{1/2}$, where
$B_{\mathrm{inc}}$ is the incoherent (out-of-band) region and $\Delta f = f_s/n$ the bin
spacing. Since a peak-location error is (noise slope)/(curvature),

$$\frac{\sigma_\tau^{\text{full-band PHAT}}}{\sigma_\tau^{\text{band-limited PHAT}}}
\ \approx\
\left(\frac{\int_{B_{\mathrm{inc}}}(2\pi f)^2\,\mathrm{d}f}
{\int_{B_{\mathrm{coh}}}(2\pi f)^2\,\mathrm{d}f}\right)^{1/2}. \tag{M23}$$

[DERIVED, scaling argument.] For this configuration
($B_{\mathrm{coh}} = 300$–3400 Hz, $B_{\mathrm{inc}} \approx 0$–24 kHz):

$$\frac{\int_0^{24000}f^2\mathrm{d}f}{\int_{300}^{3400}f^2\mathrm{d}f}
= \frac{24000^3}{3400^3-300^3} = 352,\qquad \sqrt{352} = 18.8 . \tag{M24}$$

**This prediction was tested.** [NEW RUN: same array, same source, same noise, same
interpolation; the only change was zeroing the PHAT-weighted cross-spectrum outside
300–3400 Hz before the inverse transform. 275 frames per SNR, azimuths $-150^\circ$ to
$+150^\circ$ in $30^\circ$ steps, 25 trials each.]

| nominal SNR | $\sigma_\tau$ full-band | $\sigma_\tau$ band-limited | ratio | RMSE full-band | RMSE band-limited |
|---|---|---|---|---|---|
| 0 dB | 26.15 $\mu$s | 3.45 $\mu$s | 7.6 | 4.89$^\circ$ | 0.73$^\circ$ |
| 10 dB | 22.49 $\mu$s | 1.49 $\mu$s | 15.1 | 4.14$^\circ$ | 0.31$^\circ$ |
| 20 dB | 14.24 $\mu$s | 0.82 $\mu$s | 17.3 | 2.10$^\circ$ | 0.17$^\circ$ |
| 40 dB | 1493 $\mu$s (outlier-dominated) | 0.78 $\mu$s | — | 11.03$^\circ$ | 0.14$^\circ$ |

The measured ratio at 10–20 dB (15–17) agrees with the predicted 18.8 from (M24) to within
20 %. The full-band 40 dB row is the "RMSE inflated at high SNR by rare wrap outliers"
pathology recorded in `HANDOVER.md` as negative result #2 — and band-limiting removes it
completely.

**Honest framing required.** Part of this gain is an artefact of the simulation's noise model
(assumption A5: white noise over 0–24 kHz against a 3.1 kHz source). A real acquisition chain
band-limits its own noise, so the measured gain on hardware will be smaller. But the
*principle* — weight only the band where the two channels are coherent — is exactly what
(M21) prescribes, and the paper should state that the front end as benchmarked is
$\sim 15\times$ from its own achievable precision because of this. **All numbers in
`benchmark_run.log` and `ablation_run.log` were produced with the full-band version.**

### 2.5 Discretisation and the feasible lag set

* Native sample quantisation step $1/f_s = 20.83\ \mu$s; effective step after $I$-fold
  interpolation $q = 1/(I f_s) = 2.604\ \mu$s (M19).
* Modelling the residual grid error as uniform on $[-q/2,q/2]$,

$$\sigma_{\tau,q} = \frac{q}{\sqrt{12}} = \frac{1}{\sqrt{12}\,I f_s} = 0.752\ \mu\mathrm{s}. \tag{M25}$$

* Feasible lag set (M5): $|\tau_{ij}|\le d_{ij}/c$, i.e. $\pm 252.5\ \mu$s, i.e.
  $\pm 12.12$ native samples, i.e. $\pm 97$ interpolated grid points. `gcc_phat()` searches
  $\pm In/2 = \pm 16384$ points, i.e. $\pm 42.7$ ms — a search range **169 times wider than
  physically possible**. `est_gccphat_ls()` never applies the bound at all; only
  `est_proposed()` applies it, and then only as a confidence of zero. Restricting the argmax
  to the feasible set is free and would by itself remove a large fraction of the wrap outliers.
  This is a second implementation observation for the paper's discussion.

---

## 3. Sampling-rate requirement (design inequality)

This section exists because preliminary inspection of the calibration CSVs suggests an
acquisition rate near 1 kHz. The following establishes, from first principles, what $f_s$
this array requires.

### 3.1 The controlling dimensionless number

$$n_{\max} \;=\; \frac{d_{ij}\,f_s}{c} \;=\; \frac{\sqrt{3}\,R\,f_s}{c}
\qquad\text{(maximum inter-microphone delay, in samples).} \tag{M26}$$

A conventional integer-lag correlation search can resolve at most

$$N_{\mathrm{lag}} = 2\lfloor n_{\max}\rfloor + 1 \tag{M27}$$

distinct delays per pair, hence at most that many distinguishable azimuth cells before
interpolation.

| $f_s$ | $n_{\max}$ ($D=8.66$ cm) | $N_{\mathrm{lag}}$ |
|---|---|---|
| 1 kHz | 0.252 | **1** |
| 4 kHz | 1.010 | 3 |
| 8 kHz | 2.020 | 5 |
| 16 kHz | 4.040 | 9 |
| 44.1 kHz | 11.14 | 23 |
| 48 kHz | 12.12 | 25 |
| 96 kHz | 24.24 | 49 |

[VERIFIED by direct evaluation of (M26)–(M27).]

**At $f_s = 1$ kHz the entire physical delay range of the array lies inside a single sample
interval.** The integer-lag correlation has exactly one admissible lag, namely zero, and the
array is blind. For the 5 cm baseline of the quadrant data ($\tau_{\max}=145.8\ \mu$s) the
figure is 0.146 samples — worse.

### 3.2 Angular quantisation as a function of $f_s$, $I$ and $R$

Substituting (M25) into the array GDOP relation (M40) derived in Section 4:

$$\boxed{\ \sigma_{\theta,q} \;=\; \frac{c}{\sqrt{4.5}\,R}\cdot\frac{1}{\sqrt{12}\,I f_s}
\;=\; \frac{c}{\sqrt{54}\,R\,I f_s}\ }\qquad\text{(radians)} \tag{M28}$$

which inverts to the **design inequality**

$$\boxed{\ I\,f_s \ \ge\ \frac{c}{\sqrt{54}\;R\;\varepsilon_q}\ } \tag{M29}$$

for a target azimuth quantisation standard deviation $\varepsilon_q$ in radians.

| target $\varepsilon_q$ | required $I f_s$ | e.g. $I=1$ | e.g. $I=8$ |
|---|---|---|---|
| 2.0$^\circ$ | 26.7 kHz | 26.7 kHz | 3.3 kHz |
| 1.0$^\circ$ | 53.5 kHz | 53.5 kHz | 6.7 kHz |
| 0.5$^\circ$ | 107.0 kHz | 107.0 kHz | 13.4 kHz |
| 0.25$^\circ$ | 213.9 kHz | 213.9 kHz | 26.7 kHz |

At the configured $f_s=48$ kHz, $I=8$, $R=5$ cm, (M28) gives $\sigma_{\theta,q}=0.139^\circ$.
[VERIFIED: the band-limited estimator at 40 dB SNR achieves $\sigma_\tau = 0.783\ \mu$s
against the predicted quantisation floor of $0.752\ \mu$s (M25), i.e. it sits exactly on the
interpolation grid limit, and the corresponding measured azimuth RMSE is $0.142^\circ$ against
the predicted $0.139^\circ$. This is a two-place confirmation of (M25) and (M28).]

### 3.3 What interpolation can and cannot recover

Sub-sample interpolation is not a free lunch, and it is important to say exactly which part
of the problem it fixes.

* **It does fix the grid.** The sampled correlation of a signal band-limited below $f_s/2$
  determines the continuous correlation exactly (sampling theorem), so in the noiseless case
  the true delay is recoverable from an arbitrarily coarse grid. Zero-padded inverse FFT
  (M17) realises this exactly; parabolic fitting (M20) does not, and carries the bias
  quantified in Section 2.3.
* **It does not fix bandwidth.** The Cramér–Rao bound depends on $f_s$ *only* through the
  usable signal band $[f_1,\min(f_2,f_s/2)]$, via the mean-square bandwidth $\beta^2$ (M81).
  Reducing $f_s$ below $2f_2$ truncates the band and the bound degrades as $1/\beta$.

  | $f_s$ | usable band | r.m.s. bandwidth | CRB $\sigma_\theta$ at 18.9 dB in-band SNR |
  |---|---|---|---|
  | 1 kHz | 300–500 Hz | 404 Hz | **3.476$^\circ$** |
  | 2 kHz | 300–1000 Hz | 681 Hz | 1.103$^\circ$ |
  | 4 kHz | 300–2000 Hz | 1250 Hz | 0.385$^\circ$ |
  | 8 kHz | 300–3400 Hz | 2055 Hz | 0.174$^\circ$ |
  | 48 kHz | 300–3400 Hz | 2055 Hz | 0.174$^\circ$ |

  [VERIFIED by direct evaluation of (M82) with $T_{\mathrm{obs}} = 42.67$ ms and the in-band
  SNR convention (M84).]
* **It amplifies noise sensitivity in a specific sense.** Interpolation does not change
  $\sigma_\tau$, but as $f_s$ falls the *ratio* of the physical delay range to the interpolation
  step falls with it, so a fixed relative peak-location error consumes a larger fraction of the
  whole angular range. At $f_s = 1$ kHz an interpolation factor $I \approx 32$ is needed merely
  to bring $\sigma_{\theta,q}$ below $1.7^\circ$ (M28), and $I\approx 100$ for sub-degree work.
* **It cannot undo aliasing.** A 1 kHz sampler without a genuine anti-alias filter folds the
  entire 300–3400 Hz source band back into 0–500 Hz with scrambled phase, destroying the
  inter-channel coherence that (M21) depends on. The CRB row above assumes an ideal
  anti-alias filter and is therefore optimistic.

### 3.4 Minimum viable sample rate

Collecting the three constraints:

$$\boxed{\ f_s \ \ge\ \max\left\{\underbrace{2f_2}_{\text{bandwidth}},\
\underbrace{\frac{c}{\sqrt{54}\,R\,I\,\varepsilon_q}}_{\text{quantisation}},\
\underbrace{\frac{\kappa\,c}{\sqrt3\,R}}_{\text{peak search, }\kappa\approx 5\text{--}10}\right\}\ } \tag{M30}$$

The third term ensures the correlation peak is sampled over enough native lags for the argmax
to be well posed before interpolation; with $\kappa=10$, $R=5$ cm it gives $f_s\ge 39.6$ kHz,
and with $\kappa=5$, $f_s\ge 19.8$ kHz.

**Conclusion.** For the accuracy this paper claims ($\sim 1^\circ$ after accumulation, from
$\sim 4^\circ$ per frame):

* $f_s \approx 1$ kHz is **not viable**. Even granting an ideal anti-alias filter and
  $I=32$, the CRB alone is $3.48^\circ$ and the quantisation floor is $1.67^\circ$; and
  without an anti-alias filter the coherence collapses entirely. None of the simulated results
  transfer.
* $f_s = 8$ kHz preserves the full speech band and, with $I\ge 8$, gives
  $\sigma_{\theta,q}=0.84^\circ$ — marginal but workable for a $\sim 2^\circ$ target.
* $f_s = 16$–48 kHz with $I\ge 8$ satisfies all three terms of (M30) comfortably and is what
  the simulation assumes.

[MEASURE: the actual per-channel acquisition rate of the ESP32-S3 firmware, and whether the
three channels are sampled simultaneously or round-robin. A round-robin ADC introduces a
deterministic inter-channel skew of one conversion interval, which by A8 is a direct TDOA bias.]

**Separate but related problem.** Each `Triple Mic Samples/sample_*.xlsx` contains 30 samples
per channel. Whatever $f_s$ is, 30 samples cannot support the front end: at 48 kHz the
physical lag range alone is 12.1 samples, i.e. 40 % of the record, so the correlation is
dominated by edge effects; at 1 kHz the lag range is 0.25 samples. These clips are not usable
snapshots as they stand.

---

## 4. Pairwise-to-azimuth inversion

### 4.1 The linear system

Stacking (M4) over the $P=3$ pairs, with $\mathbf{a}_{ij}=\mathbf{p}_i-\mathbf{p}_j$:

$$\mathbf{A}\,\mathbf{u} = \mathbf{b},\qquad
\mathbf{A} = \begin{bmatrix}\mathbf{a}_{12}^{\mathsf T}\\ \mathbf{a}_{13}^{\mathsf T}\\ \mathbf{a}_{23}^{\mathsf T}\end{bmatrix}\in\mathbb{R}^{P\times 2},
\qquad
\mathbf{b} = -c\begin{bmatrix}\hat\tau_{12}\\ \hat\tau_{13}\\ \hat\tau_{23}\end{bmatrix}. \tag{M31}$$

This is exactly `est_gccphat_ls()`. The unconstrained least-squares solution is

$$\hat{\mathbf u} = \big(\mathbf{A}^{\mathsf T}\mathbf{A}\big)^{-1}\mathbf{A}^{\mathsf T}\mathbf{b}
= \mathbf{A}^{+}\mathbf{b}, \tag{M32}$$

and the azimuth is read off as

$$\hat\theta = \operatorname{atan2}(\hat u_y,\ \hat u_x). \tag{M33}$$

For the equilateral array, using (M2),

$$\mathbf{A}^{\mathsf T}\mathbf{A} = \tfrac32 D^2\,\mathbf{I}_2 = \tfrac92 R^2\,\mathbf{I}_2
= 4.5\,R^2\,\mathbf{I}_2 . \tag{M34}$$

[VERIFIED numerically from `MIC_XY`: $\mathbf{A}^{\mathsf T}\mathbf{A} =
\operatorname{diag}(0.01125,0.01125)$ and $4.5R^2 = 0.01125$; both singular values equal
0.10607, condition number 1.000.]

### 4.2 The unit-norm constraint

The physical parameter $\mathbf{u}$ satisfies $\|\mathbf{u}\|=1$, so (M31) is a *constrained*
least-squares problem. **The code does not impose the constraint.** It solves (M32) in
$\mathbb{R}^2$ and then applies (M33), which is invariant to the norm of $\hat{\mathbf u}$.
Three points follow.

1. The estimator is therefore not the constrained maximum-likelihood estimator. It is,
   however, consistent: the radial component of $\hat{\mathbf u}$ carries no azimuth
   information, and discarding it via `atan2` is the correct projection to first order.
2. As shown in (M8), this is exactly what makes the estimator invariant to errors in $c$.
3. $\big|\|\hat{\mathbf u}\| - 1\big|$ is a *free* consistency statistic that the code computes
   and throws away. It is a natural candidate for the confidence measure the gate needs.
   [NEW RUN, 550 free-field frames at 10 dB: the Spearman rank correlation between
   $\big|\|\hat{\mathbf u}\|-1\big|$ and the frame's absolute azimuth error is $-0.046$.
   It carries no usable information either — see Section 5.6.]

### 4.3 Error propagation and geometric dilution of precision

Let $\delta\boldsymbol\tau$ be the vector of TDOA errors, with
$\operatorname{Cov}(\delta\boldsymbol\tau)=\boldsymbol\Sigma_\tau$. From (M32),

$$\operatorname{Cov}(\hat{\mathbf u}) = c^{2}\,\mathbf{A}^{+}\boldsymbol\Sigma_\tau\,
\mathbf{A}^{+\mathsf T}. \tag{M35}$$

Linearising (M33) about the true $\mathbf{u}$ (unit norm) with $\mathbf{e}_\theta =
(-\sin\theta,\cos\theta)^{\mathsf T}$,

$$\delta\theta = \mathbf{e}_\theta^{\mathsf T}\,\delta\hat{\mathbf u}
\quad\Longrightarrow\quad
\sigma_\theta^{2} = c^{2}\,
\mathbf{e}_\theta^{\mathsf T}\mathbf{A}^{+}\boldsymbol\Sigma_\tau\mathbf{A}^{+\mathsf T}\mathbf{e}_\theta .
\tag{M36}$$

Equation (M36) is the general GDOP expression for this estimator. Specialising to
independent, equal-variance per-pair errors, $\boldsymbol\Sigma_\tau = \sigma_\tau^2\mathbf{I}_P$:

$$\operatorname{Cov}(\hat{\mathbf u}) = c^{2}\sigma_\tau^{2}
\big(\mathbf{A}^{\mathsf T}\mathbf{A}\big)^{-1}
\overset{\text{(M34)}}{=} \frac{c^{2}\sigma_\tau^{2}}{4.5\,R^{2}}\ \mathbf{I}_2 , \tag{M37}$$

$$\sigma_\theta^{2}
= \frac{c^{2}\sigma_\tau^{2}}{4.5\,R^{2}}\ \ \text{for every }\theta . \tag{M38}$$

$$\boxed{\ \text{On an equilateral 3-microphone array with uniform weights, the azimuth
variance is isotropic.}\ } \tag{M39}$$

$$\boxed{\ \sigma_\theta \;=\; \frac{c\,\sigma_\tau}{\sqrt{4.5}\,R}
\;=\; \frac{c\,\sigma_\tau}{2.1213\,R}\ } \tag{M40}$$

[DERIVED; VERIFIED numerically as above.]

**This corrects an assumption that would otherwise go into the paper unchallenged.** The
azimuth error of this array is *not* intrinsically direction-dependent. Direction dependence
appears only when the isotropy of (M34) is broken, which happens in exactly three ways:

* **(a) Non-uniform weights.** With diagonal weights $\mathbf{W}$, (M34) becomes
  $\mathbf{A}^{\mathsf T}\mathbf{W}\mathbf{A}$, which is generally anisotropic. The PSR
  weighting of Section 5.3 therefore *creates* direction-dependent error where none existed.
* **(b) Dropping a pair.** Section 5.5.
* **(c) Unequal per-pair TDOA variance**, e.g. when one pair is broadside to a strong
  reflection.

**Aperture law.** (M40) gives $\sigma_\theta \propto 1/R$: error is aperture-limited, not
algorithm-limited. Checking against `ablation_run.log` (median $|$error$|$ versus circum-radius,
free field, 10 dB):

| $R$ (cm) | 2 | 3 | 5 | 8 | 12 |
|---|---|---|---|---|---|
| median error (deg) [LOG] | 7.31 | 4.63 | 2.95 | 1.65 | 1.10 |
| $R\times$ median (cm·deg) | 14.6 | 13.9 | 14.8 | 13.2 | 13.2 |

The product is constant to $\pm 6$ %, and the log–log slope is $-1.06$ against the predicted
$-1$. [VERIFIED.] The residual steepening at small $R$ is consistent with the onset of
wrap/ambiguity outliers as the delay range shrinks toward the interpolation grid.

**Snapshot law and an anomaly, resolved.** The CRB (Section 8) gives
$\sigma_\tau\propto T_{\mathrm{obs}}^{-1/2}$, hence $\sigma_\theta\propto N^{-1/2}$, i.e. a
log–log slope of $-0.5$. The log gives:

| $N$ | 256 | 512 | 1024 | 2048 | 4096 |
|---|---|---|---|---|---|
| median error (deg) [LOG] | 4.27 | 3.40 | 3.06 | 2.72 | 2.40 |

slope $-0.208$ — far shallower than theory. [NEW RUN: reproducing the sweep gives
$-0.235$ with the as-implemented front end (values 4.84, 3.62, 3.50, 2.87, 2.41, matching the
log), and $-0.512$ with the band-limited PHAT of Section 2.4 (values 0.574, 0.346, 0.341,
0.198, $<$0.05).] The anomalous snapshot scaling is therefore **entirely an artefact of the
full-band PHAT weighting**, and the $N^{-1/2}$ law is recovered exactly once the weight is
restricted to the coherent band. This is a clean, complete diagnosis and should be reported
as such rather than left as an unexplained deviation.

### 4.4 Validation of the GDOP law against the benchmark

[NEW RUN: per-pair TDOA error standard deviation measured directly, 275 frames per SNR.]
Feeding the measured $\sigma_\tau$ into (M40) and comparing with `benchmark_run.log`
(GCC-PHAT, RMSE over 630 trials):

| nominal SNR | measured $\sigma_\tau$ | $\sigma_\theta$ predicted by (M40) | RMSE measured [LOG] | median measured [LOG] | $0.6745\,\sigma_\theta$ |
|---|---|---|---|---|---|
| 0 dB | 26.1 $\mu$s | 4.84$^\circ$ | 4.93$^\circ$ | 3.45$^\circ$ | 3.26$^\circ$ |
| 10 dB | 22.3 $\mu$s | 4.13$^\circ$ | 4.23$^\circ$ | 2.82$^\circ$ | 2.79$^\circ$ |
| 20 dB | 14.1 $\mu$s | 2.61$^\circ$ | **7.14$^\circ$** | 1.67$^\circ$ | 1.76$^\circ$ |
| 40 dB | 9.4 $\mu$s | 1.74$^\circ$ | 1.74$^\circ$ | 0.35$^\circ$ | 1.17$^\circ$ |

The law (M40) reproduces the measured RMSE at 0, 10 and 40 dB to within 2 %, and the
Gaussian-median relation $\mathrm{median}|e| = 0.6745\,\sigma_\theta$ holds at 0, 10 and 20 dB.
The two entries in bold type are the paper's negative result #2 made quantitative:

* At 20 dB the RMSE (7.14$^\circ$) *exceeds* the 10 dB RMSE (4.23$^\circ$) while the median
  falls monotonically. The bulk of the distribution behaves exactly as (M40) predicts
  (median 1.67$^\circ$ vs 1.76$^\circ$ predicted); the RMSE is inflated by rare large errors.
* At 40 dB the median (0.35$^\circ$) is far *below* the Gaussian prediction (1.17$^\circ$),
  i.e. the error distribution is strongly heavy-tailed: most frames are nearly exact and a
  few are wildly wrong.

Both features are consistent with wrap/ambiguity outliers on an unrestricted lag search
(Section 2.5) and with the full-band PHAT weighting (Section 2.4), and both are removed by
band-limiting (Section 2.4 table).

---

## 5. Confidence gate and weighting, and why they cannot work at $M=3$

### 5.1 Peak-to-sidelobe ratio, as computed

From `_pair_confidence()`, with $k_0=\arg\max_k \hat R[k]$ and exclusion half-width
$w = \max(1, \lceil In/100\rceil)$:

$$\rho_{ij} \;=\; \frac{\hat R[k_0]}{\big|\max_{|k-k_0|>w}\hat R[k]\big| + 10^{-9}} \tag{M41}$$

$\rho_{ij}\in[1,\infty)$ in principle; in practice $\rho\ge 1$ by construction since the
excluded window contains the global maximum. [NEW RUN, free field: mean $\rho$ = 1.84 at
0 dB, 2.51 at 10 dB, 7.73 at 20 dB, 15.65 at 40 dB.]

### 5.2 The two gates

$$\text{(feasibility)}\qquad
\rho_{ij}\leftarrow 0 \quad\text{if}\quad |\hat\tau_{ij}| > 1.05\,\frac{d_{ij}}{c}, \tag{M42}$$

$$\text{(relative PSR)}\qquad
\text{keep pair }ij \iff \rho_{ij} \ \ge\ \eta\,\max_{kl}\rho_{kl},\qquad \eta = 0.5, \tag{M43}$$

with the safeguard that if fewer than two pairs survive, the highest-$\rho$ pairs are restored
until two remain.

[NEW RUN, free field, 275 frames per SNR: gate (M43) fires (rejects at least one pair) in
20.0 % of frames at 0 dB, 9.8 % at 10 dB, 17.5 % at 20 dB, 37.5 % at 40 dB, and changes the
resulting azimuth in 19.6 / 9.8 / 10.9 / 12.0 % of frames respectively, with a maximum change
of 15.8$^\circ$ (0 dB) and 3.9$^\circ$ (10 dB). The feasibility gate (M42) fires on
56/825, 27/825, 13/825 and 1/825 pairs.] So the gate is *active*; it is not a no-op. It simply
does not improve accuracy, which is the thing that has to be explained.

### 5.3 Weighted least squares

With $\mathbf{W} = \operatorname{diag}(w_{ij})$, $w_{ij}=\rho_{ij}$ over the surviving pairs,

$$\hat{\mathbf u}_{\mathrm W}
= \big(\mathbf{A}^{\mathsf T}\mathbf{W}\mathbf{A}\big)^{-1}\mathbf{A}^{\mathsf T}\mathbf{W}\mathbf{b},
\tag{M44}$$

implemented in the code by row-scaling with $\sqrt{w}$ before an ordinary `lstsq`, which is
algebraically identical to (M44). Weighted LS is the BLUE if and only if
$w_{ij}\propto 1/\sigma_{\tau,ij}^2$; PSR is not calibrated to that, and Section 5.6 shows it
is not even monotonically related to it.

### 5.4 Rank, redundancy, and the impossibility of fault exclusion

This is the rigorous form of the paper's negative result #1.

**(i) Redundancy is exactly 1.** $\mathbf{A}\in\mathbb{R}^{3\times 2}$ has
$\operatorname{rank}\mathbf{A}=2$ for any non-collinear array, so the redundancy is
$P - \operatorname{rank} = 3-2 = 1$. [VERIFIED: `matrix_rank(A) = 2`.]

**(ii) The dependency is the TDOA cocycle.** Because $\tau_{ij}=\tau_i-\tau_j$ derives from
$M$ arrival times, the pairwise delays satisfy an exact closure (cocycle) identity, and the
baselines satisfy the matching identity:

$$\mathbf{a}_{13} = \mathbf{a}_{12}+\mathbf{a}_{23},
\qquad \tau_{13} = \tau_{12}+\tau_{23}\ \ \text{(noiseless)}. \tag{M45}$$

Hence the left null space of $\mathbf{A}$ is one-dimensional and spanned by

$$\mathbf{v} = \tfrac{1}{\sqrt3}\,(1,\,-1,\,1)^{\mathsf T}
\quad\text{(pair order }12,\,13,\,23\text{)},\qquad \mathbf{v}^{\mathsf T}\mathbf{A}=\mathbf{0}^{\mathsf T}.
\tag{M46}$$

[VERIFIED: `null_space(A.T)` returns $(1,-1,1)/\sqrt3$.]

**(iii) There is exactly one testable statistic, and it is the closure error.** The residual
of (M32) is $\mathbf{r}=(\mathbf{I}-\mathbf{A}\mathbf{A}^{+})\mathbf{b}
= \mathbf{v}\mathbf{v}^{\mathsf T}\mathbf{b}$, a rank-1 projector. [VERIFIED: the numerically
computed residual projector is

$$\mathbf{I}-\mathbf{A}\mathbf{A}^{+}
= \frac{1}{3}\begin{bmatrix}1&-1&1\\ -1&1&-1\\ 1&-1&1\end{bmatrix}
= \mathbf{v}\mathbf{v}^{\mathsf T},$$

with all diagonal entries equal to $1/3$.] Therefore

$$\mathbf{r} = \big(\mathbf{v}^{\mathsf T}\mathbf{b}\big)\,\mathbf{v},
\qquad
\mathbf{v}^{\mathsf T}\mathbf{b} = -\frac{c}{\sqrt3}\underbrace{\big(\hat\tau_{12}-\hat\tau_{13}+\hat\tau_{23}\big)}_{\displaystyle \equiv\ \varepsilon_{\mathrm{clo}}} . \tag{M47}$$

The **whole** of the geometric redundancy of a three-microphone array is the scalar closure
error $\varepsilon_{\mathrm{clo}}$, which is zero in the noiseless case by (M45).

**(iv) Fault exclusion is impossible.** Suppose pair $k$ carries an unmodelled bias
$\delta$ (a reflection-induced peak shift, say), i.e. $\mathbf{b}\to\mathbf{b}+\delta\,\mathbf{e}_k$.
The observable change in the test statistic is

$$\Delta\big(\mathbf{v}^{\mathsf T}\mathbf{b}\big) = \delta\,v_k
= \pm\frac{\delta}{\sqrt3}, \tag{M48}$$

with $v_k = +1/\sqrt3$ for $k\in\{12,23\}$ and $-1/\sqrt3$ for $k=13$. **The magnitude is
identical for all three pairs**, and the sign differs only between pair 13 and the other two.
Since the sign of $\delta$ is unknown a priori, the three single-fault hypotheses produce
*exactly* the same distribution of the only available statistic. In the standard terminology
of integrity monitoring, with $P$ measurements and $p$ unknowns, fault **detection** requires
$P \ge p+1$ and fault **identification/exclusion** requires $P \ge p+2$. Here $P=3$, $p=2$:

$$\boxed{\ P = p+1 = 3 \ \Longrightarrow\ \text{a faulty pair can be \emph{detected} but never
\emph{identified}.}\ } \tag{M49}$$

Any hard gate is an exclusion mechanism. At $M=3$ no exclusion mechanism can do better than
chance at picking the right pair, whatever statistic it uses in place of the residual, unless
that statistic carries genuinely independent side information. PSR is offered as such side
information; Section 5.6 shows empirically that it carries almost none.

**(v) A note on what the third pair does buy.** Equation (M45) holds for the *true* delays,
but GCC-PHAT estimates each pair independently, so the three measured delays do *not* satisfy
it and the redundancy is statistically real. [VERIFIED: at 10 dB the measured mean
$|\varepsilon_{\mathrm{clo}}|$ is 29.6 $\mu$s; for three independent errors of standard
deviation $\sigma_\tau$, $\varepsilon_{\mathrm{clo}}$ has standard deviation $\sqrt3\sigma_\tau$
and a half-normal mean of $\sqrt{2/\pi}\sqrt3\sigma_\tau = 1.382\,\sigma_\tau$, giving
$\sigma_\tau = 21.4\ \mu$s — in agreement with the directly measured $22.3\ \mu$s. The
per-pair errors are therefore essentially independent, as assumed in (M37).] The three-pair
least-squares solution consequently *does* average noise: by (M38) versus Section 5.5 it is
up to $\sqrt3$ better than a two-pair solve. What it cannot do is tell you *which* pair to
throw away.

### 5.5 The quantitative cost of dropping a pair

Removing row $k$ leaves $\mathbf{A}_2\in\mathbb{R}^{2\times 2}$, an exactly determined system
with identically zero residual (so no further consistency check is possible, confirming
(M49) constructively). For the equilateral array, for every choice of $k$,

$$R^{2}\big(\mathbf{A}_2^{\mathsf T}\mathbf{A}_2\big)^{-1}
\ \text{has eigenvalues}\ \{0.2222,\ 0.6667\}
\quad\text{versus}\quad \{0.2222,\ 0.2222\}\ \text{for all three pairs.} \tag{M50}$$

[VERIFIED numerically for all three choices of $k$.] Hence

$$\frac{\sigma_\theta^{\text{2 pairs}}}{\sigma_\theta^{\text{3 pairs}}}
\in \big[1,\ \sqrt3\,\big] = [1,\ 1.732], \tag{M51}$$

depending on look direction: **gating leaves the azimuth variance unchanged along one axis and
triples it along the orthogonal axis, and destroys the isotropy (M39).** The gate therefore
carries a definite cost (up to $1.73\times$ in $\sigma_\theta$ over part of the field of view)
in exchange for a benefit that (M49) shows cannot be realised. That is the complete
explanation of the ablation result.

### 5.6 The confidence statistics carry no usable information

The argument above says exclusion is impossible *using the residual*. It leaves open whether
PSR supplies useful side information. It does not.

[NEW RUN, free field, 10 dB, 550 frames, ordinary 3-pair LS; correlating each frame's
absolute azimuth error against three candidate confidence statistics.]

| statistic | Pearson $r$ | Spearman $\rho_s$ | median $|e|$, best third | median $|e|$, worst third |
|---|---|---|---|---|
| mean PSR $\bar\rho$ | $-0.139$ | $-0.129$ | 2.58$^\circ$ | 3.30$^\circ$ |
| $\big|\|\hat{\mathbf u}\|-1\big|$ | $-0.036$ | $-0.046$ | 2.46$^\circ$ | 3.02$^\circ$ |
| $|\varepsilon_{\mathrm{clo}}|$ | $-0.019$ | $+0.006$ | 2.66$^\circ$ | 2.59$^\circ$ |

[NEW RUN, image-source room, RT60 = 0.30 s, 10 dB, 490 frames:] mean PSR versus
$|e|$ gives $\rho_s = -0.040$; the highest-PSR third of frames has median error
4.57$^\circ$ against 4.47$^\circ$ for the lowest-PSR third — i.e. the confidence measure is,
if anything, very slightly *anti*-informative in reverberation.

A rank correlation of $-0.13$ explains under 2 % of the rank variance; in reverberation, where
the gate is supposed to earn its keep, it explains none. Combined with (M49) and (M51) this is
a complete, three-part explanation of the ablation table in `ablation_run.log`:

| RT60 (s) | 0.05 | 0.15 | 0.30 | 0.45 | 0.60 | 0.80 |
|---|---|---|---|---|---|---|
| gate + weight | 2.3 | 2.7 | 4.4 | 4.7 | 5.3 | 4.7 |
| weight only | 2.3 | 2.7 | 4.4 | 4.7 | 5.3 | 4.5 |
| gate only | 2.2 | 2.7 | 4.3 | 4.8 | 5.9 | 5.0 |
| neither (= GCC-PHAT) | 2.2 | 2.7 | 4.3 | 4.8 | 5.9 | 5.0 |

[LOG, median $|$error$|$ in degrees at 10 dB.] The four variants are indistinguishable.

**Statement for the paper.** The negative result is not "we tried it and it did not help".
It is: *at $M=3$ the linear system has redundancy 1, so a faulty pair is detectable but
provably not identifiable (M49); hard gating additionally costs up to a factor $\sqrt3$ in
azimuth standard deviation and destroys the isotropy of the estimator (M50)–(M51); and the
confidence statistic offered as external side information is empirically uninformative
($\rho_s = -0.13$ free field, $-0.04$ reverberant). Redundancy sufficient for exclusion
requires $P\ge 4$, i.e. $M\ge 4$ microphones (giving $P=6$, redundancy 4).*

---

## 6. Confidence-weighted temporal accumulation

### 6.1 The estimator

Over a window of $T$ frames, with per-frame azimuth estimates $\hat\theta_t$ and weights
$w_t\ge 0$:

$$C_T = \sum_{t=1}^{T} w_t\cos\hat\theta_t,\qquad
S_T = \sum_{t=1}^{T} w_t\sin\hat\theta_t,\qquad
\hat\theta_T = \operatorname{atan2}\big(S_T,\ C_T\big). \tag{M52}$$

This is `accumulate_doa()`, with $w_t$ the mean surviving PSR of frame $t$ (or $w_t\equiv 1$
for the plain-mean ablation). Equation (M52) is the *weighted circular mean*, not the
arithmetic mean; the distinction matters at $\pm 180^\circ$ and, as Section 6.3 shows, in the
presence of outliers.

### 6.2 Variance reduction, derived in circular statistics

Model the per-frame estimate as

$$\hat\theta_t = \theta_0 + b + e_t \pmod{2\pi}, \tag{M53}$$

with $b$ a deterministic, frame-invariant bias and $e_t$ i.i.d. zero-mean circular errors,
independent of $w_t$. Two standard families are used below: the **wrapped normal**
$\mathrm{WN}(0,\sigma^2)$ and the **von Mises** $\mathrm{VM}(0,\kappa)$. Define the mean
resultant length (first trigonometric moment) and the second moment

$$\bar\rho_1 = \mathbb{E}\big[\cos e\big] = \mathbb{E}\big[e^{\mathrm{i}e}\big],\qquad
\bar\rho_2 = \mathbb{E}\big[\cos 2e\big], \tag{M54}$$

$$\text{WN:}\quad \bar\rho_1 = e^{-\sigma^2/2},\ \ \bar\rho_2 = e^{-2\sigma^2};
\qquad
\text{VM:}\quad \bar\rho_1 = \frac{I_1(\kappa)}{I_0(\kappa)} \equiv A(\kappa),\ \
\bar\rho_2 = \frac{I_2(\kappa)}{I_0(\kappa)}. \tag{M55}$$

Write $W = \sum_t w_t$ and let $Z = \frac{1}{W}\sum_t w_t e^{\mathrm{i}\hat\theta_t}$. Then

$$Z\,e^{-\mathrm{i}(\theta_0+b)} = \frac{1}{W}\sum_t w_t e^{\mathrm{i}e_t}
= \bar\rho_1 + \xi,\qquad \mathbb{E}[\xi]=0. \tag{M56}$$

For $|\xi|\ll\bar\rho_1$, $\hat\theta_T-(\theta_0+b) = \arg(\bar\rho_1+\xi)
\approx \operatorname{Im}(\xi)/\bar\rho_1$, and

$$\operatorname{Im}(\xi) = \frac{1}{W}\sum_t w_t\sin e_t,\qquad
\operatorname{Var}\big(\operatorname{Im}\xi\big)
= \frac{\sum_t w_t^{2}}{W^{2}}\,\mathbb{E}\big[\sin^{2}e\big]
= \frac{\sum_t w_t^{2}}{W^{2}}\cdot\frac{1-\bar\rho_2}{2}. \tag{M57}$$

Defining the **effective sample size** (Kish)

$$T_{\mathrm{eff}} = \frac{\big(\sum_t w_t\big)^{2}}{\sum_t w_t^{2}}\ \le\ T,
\qquad\text{with equality iff all } w_t \text{ are equal,} \tag{M58}$$

we obtain the general result

$$\boxed{\
\operatorname{Var}\big(\hat\theta_T\big)\ \simeq\
\frac{1-\bar\rho_2}{2\,\bar\rho_1^{2}\ T_{\mathrm{eff}}}\ }
\qquad
\Big(\text{VM: } \operatorname{Var}\to \frac{1}{\kappa A(\kappa)\,T_{\mathrm{eff}}}\Big). \tag{M59}$$

[DERIVED.] In the concentrated limit ($\sigma\to 0$, i.e. $\bar\rho_1\to 1$,
$1-\bar\rho_2\to 2\sigma^2$) this reduces to $\operatorname{Var}(\hat\theta_T)=\sigma^2/T_{\mathrm{eff}}$,
recovering the linear-Gaussian $1/\sqrt{T}$ law — but (M59) shows the conditions under which it
holds and how it fails. Two consequences:

* The $1/\sqrt{T}$ law is **not** automatic for angles. It requires per-frame concentration.
  As $\sigma$ grows, the factor $(1-\bar\rho_2)/(2\bar\rho_1^2)$ grows faster than $\sigma^2$:
  it equals $1.000\,\sigma^2$ at $\sigma=10^\circ$, $1.013\,\sigma^2$ at $30^\circ$,
  $1.065\,\sigma^2$ at $45^\circ$, $1.213\,\sigma^2$ at $60^\circ$ and $2.372\,\sigma^2$ at
  $90^\circ$ [VERIFIED by direct evaluation]; as $\sigma\to\infty$ the estimator converges to a
  uniform distribution and (M52) carries no information at all. The correction is negligible
  for the per-frame dispersions actually measured here ($\sigma_1 \le 10.3^\circ$), which is
  why the simple $\sigma_1^2/T$ form is used from (M62) onward — but the paper should state
  that accumulation buys $1/\sqrt{T}$ only while the per-frame estimate is concentrated.
* Conversely, the circular mean **is** robust to wrap outliers in a way the arithmetic mean is
  not: an outlier at $\hat\theta_t = \theta_0+180^\circ$ contributes a unit vector that
  partially cancels, not an error of $180^\circ$. Given that the measured per-frame error
  distribution is strongly heavy-tailed (Section 4.4), this is a substantive reason to use
  (M52), and one the paper can state.

### 6.3 Weight efficiency: when weighting helps and when it cannot

By (M58)–(M59), if the per-frame error variance is *constant* across frames then $T_{\mathrm{eff}}\le T$
means **any** non-uniform weighting is strictly worse than the plain mean. If the per-frame
variances $\sigma_t^2$ differ, the minimum-variance choice is $w_t\propto 1/\sigma_t^2$, and
the efficiency loss of any other choice is

$$\mathcal{L}(\mathbf{w}) = \frac{\big(\sum_t w_t^{2}\sigma_t^{2}\big)\big(\sum_t \sigma_t^{-2}\big)}
{\big(\sum_t w_t\big)^{2}} \ \ge\ 1, \tag{M60}$$

by Cauchy–Schwarz, with equality iff $w_t\propto \sigma_t^{-2}$. [DERIVED.]

Checking against `ablation_run.log`, free field, 10 dB:

| $T$ | 1 | 2 | 4 | 8 | 16 | 32 |
|---|---|---|---|---|---|---|
| confidence-weighted RMSE (deg) [LOG] | 3.88 | 2.90 | 2.20 | 1.33 | 0.96 | 0.68 |
| plain circular mean (deg) [LOG] | 4.10 | 2.92 | 2.07 | 1.38 | 0.99 | 0.75 |

The weighted variant is 9 % better at $T=32$. **This difference is not statistically
significant.** Each RMSE is estimated from $11\ \text{angles}\times 8\ \text{trials} = 88$
samples; the relative standard error of an RMSE from $n$ samples is
$\approx 1/\sqrt{2n} = 7.5\,\%$. [DERIVED; sample count read from `ablation.py`:
`temporal_freefield(Ts, tang, SNR, trials=8)` with `tang = range(-150,151,30)`.] The paper
must say that PSR weighting gives no measurable benefit in free field on the present evidence,
consistent with (M60) and with the PSR correlations of Section 5.6.

### 6.4 The bias–variance decomposition: the reverberation bias floor

This is the paper's central analytical result. Decompose the per-frame error into a
deterministic, frame-invariant part and a zero-mean stochastic part:

$$\hat\theta_t - \theta_0 = \underbrace{b(\theta_0,\mathrm{RT}_{60})}_{\text{multipath / near-field / sensor mismatch}}
\ +\ \underbrace{e_t}_{\text{i.i.d., } \operatorname{Var}=\sigma_1^{2}} . \tag{M61}$$

Applying (M59) with $T_{\mathrm{eff}}=T$ and adding the squared bias:

$$\boxed{\ \mathrm{MSE}(T)\ =\ b^{2}\ +\ \frac{\sigma_1^{2}}{T},
\qquad
\mathrm{RMSE}(T)\ =\ \sqrt{b^{2}+\frac{\sigma_1^{2}}{T}}
\ \xrightarrow[T\to\infty]{}\ |b| \ } \tag{M62}$$

[DERIVED.] The physical content: reverberation adds two things to the estimate. Diffuse late
reverberation, and any component of the multipath that changes between frames, behaves as
additional zero-mean noise and is removed by accumulation. Early reflections from a *fixed*
room and a *fixed* source position produce a systematic displacement of the GCC peak that is
the same in every frame; it is not noise and no amount of averaging removes it.

**$b$ was measured directly, not fitted.** [NEW RUN: for each azimuth, the image-source RIRs
are built once (`build_rirs(theta, rt60)`, deterministic given $(\theta,\mathrm{RT}_{60})$),
then 150 independent frames are generated with fresh source and noise realisations and the
circular mean of the per-frame errors is taken. Frames per condition: 150; azimuths:
$-120^\circ$ to $+120^\circ$ in $40^\circ$ steps (7 angles) for reverberation, $-150^\circ$ to
$+150^\circ$ in $30^\circ$ steps (11 angles) for free field; SNR 10 dB.]

| condition | $b$ per azimuth (deg) | r.m.s. $b$ over azimuth | mean $\sigma_1$ |
|---|---|---|---|
| free field | $-0.49,-0.33,+0.26,-0.15,+0.21,+0.08,+0.41,+0.51,+0.15,-0.17,+0.10$ | **0.30$^\circ$** | 3.96$^\circ$ |
| RT60 0.15 s | $-0.08,+2.89,+0.91,-0.20,+3.40,+1.08,-0.63$ | **1.79$^\circ$** | 4.53$^\circ$ |
| RT60 0.30 s | $+2.30,+2.66,-0.51,+0.29,+3.94,+2.45,+0.42$ | **2.22$^\circ$** | 6.25$^\circ$ |
| RT60 0.60 s | $+4.44,+1.42,-2.67,+0.18,+5.54,+0.84,+3.05$ | **3.15$^\circ$** | 10.34$^\circ$ |

The standard error on each individual $b$ is $\sigma_1/\sqrt{150}$, i.e. 0.30–0.41$^\circ$ at
RT60 = 0.15 s. The largest entries ($+3.40^\circ$ at $\theta=+40^\circ$) are therefore
$\approx 9.6$ standard errors from zero. In free field every entry is within
$1.7$ standard errors of zero and the r.m.s. bias (0.30$^\circ$) is comparable to the
per-entry standard error (0.32$^\circ$), i.e. **consistent with $b=0$**.

$$\boxed{\ b_{\mathrm{rms}} = 1.79^\circ,\ 2.22^\circ,\ 3.15^\circ \ \text{at}\
\mathrm{RT}_{60}=0.15,\ 0.30,\ 0.60\ \mathrm{s};\quad b_{\mathrm{rms}}\approx 0 \ \text{in free field.}\ } \tag{M63}$$

**The reverberation bias floor is real, monotone in RT60, and statistically significant.**

**Predictive check of (M62).** Substituting the measured $b$ and $\sigma_1$:

| condition | $b$ | $\sigma_1$ | (M62) at $T=1$ | [LOG] $T=1$ | (M62) at $T=32$ | [LOG] $T=32$ |
|---|---|---|---|---|---|---|
| free field | 0 (0.30) | 3.96$^\circ$ | 3.98$^\circ$ | 3.88$^\circ$ | 0.70–0.76$^\circ$ | 0.68$^\circ$ |
| RT60 0.15 s | 1.79$^\circ$ | 4.53$^\circ$ | 4.87$^\circ$ | 4.70$^\circ$ | 1.96$^\circ$ | 2.14$^\circ$ |
| RT60 0.30 s | 2.22$^\circ$ | 6.25$^\circ$ | 6.63$^\circ$ | 8.13$^\circ$ | 2.48$^\circ$ | 2.00$^\circ$ |
| RT60 0.60 s | 3.15$^\circ$ | 10.34$^\circ$ | 10.81$^\circ$ | 7.04$^\circ$ | 3.70$^\circ$ | 2.60$^\circ$ |

The free-field prediction is exact to 0.02–0.10$^\circ$. The RT60 = 0.15 s prediction is
within one standard error. The RT60 = 0.30 s and 0.60 s predictions over-shoot at $T=32$ by
2.2 and 3.9 standard errors respectively. **Two honest explanations, both of which should be
stated:**

1. The log's reverberant RMSEs are estimated from only $7\times 6 = 42$ samples
   (`temporal_reverb(..., trials=6)`, `angles = range(-120,121,40)`), giving a relative
   standard error of $1/\sqrt{2\cdot 42} = 10.9\,\%$. The measured floors are therefore
   $2.14\pm 0.23$, $2.00\pm 0.22$ and $2.60\pm 0.28$ degrees, and the apparent
   non-monotonicity between RT60 = 0.15 s and 0.30 s is **within noise**. The paper must not
   claim the floor decreases from 0.15 s to 0.30 s.
2. $\sigma_1$ in the table is a *linear* standard deviation and is inflated by outliers
   (at RT60 = 0.6 s two azimuths give $\sigma_1 = 15.1^\circ$ and $16.7^\circ$). The circular
   mean suppresses those outliers better than $\sigma_1^2/T$ predicts (Section 6.2), so
   (M62) over-predicts the residual variance term in exactly the heavy-tailed cases.

**Direct fit of (M62) to the logged curves** (non-negative least squares on
$\mathrm{MSE}$ versus $1/T$):

| curve | fitted $b$ | fitted $\sigma_1$ | fit residual | log–log slope |
|---|---|---|---|---|
| free field, weighted | 0.51$^\circ$ | 3.90$^\circ$ | 0.14$^\circ$ | $-0.516$ |
| free field, plain | **0.00$^\circ$** | 4.10$^\circ$ | **0.036$^\circ$** | $-0.501$ |
| RT60 0.15 s | 2.22$^\circ$ | 4.34$^\circ$ | 0.25$^\circ$ | $-0.238$ |
| RT60 0.30 s | 0.00$^\circ$ | 7.76$^\circ$ | 0.69$^\circ$ | $-0.350$ |
| RT60 0.60 s | 3.77$^\circ$ | 6.48$^\circ$ | 0.77$^\circ$ | $-0.290$ |

The free-field curve is described by (M62) with $b=0$ to 0.036$^\circ$ and has a log–log slope
of $-0.501$ against the theoretical $-0.5$ — a textbook confirmation of the $1/\sqrt{T}$ law.
The reverberant curves have shallower slopes ($-0.24$ to $-0.35$), qualitatively consistent
with a bias floor, but the *fits* are poor and the fitted $b$ is unstable (2.22, 0.00, 3.77).
**The logged $T\le 32$ curves alone do not establish the floor**; the direct measurement (M63)
does. The paper should quote (M63) for the floor and cite the accumulation curves as
consistent with it, not as the proof of it. Extending the sweep to $T = 128$ or 256 with
$\ge 30$ trials would let the accumulation curves establish it independently, and is
recommended (see Section 11).

### 6.5 The accuracy–latency law

With hop $H$ samples between accumulated frames, the window latency is

$$L = \frac{T H}{f_s}. \tag{M64}$$

In `ablation.py` the frames are independent, non-overlapping snapshots, so $H=N=2048$ and
$H/f_s = 42.67$ ms per frame. Substituting $T=Lf_s/H$ into (M62):

$$\boxed{\ \mathrm{RMSE}(L) = \sqrt{\,b^{2} + \frac{\sigma_1^{2}\,H}{f_s\,L}\,}\ } \tag{M65}$$

Inverting for the frames (and latency) needed to reach a target RMSE $\varepsilon$:

$$\boxed{\ T^{*}(\varepsilon) = \left\lceil\frac{\sigma_1^{2}}{\varepsilon^{2}-b^{2}}\right\rceil,
\qquad
L^{*}(\varepsilon) = \frac{H}{f_s}\cdot\frac{\sigma_1^{2}}{\varepsilon^{2}-b^{2}},
\qquad \text{defined only for } \varepsilon > |b| . \ } \tag{M66}$$

[DERIVED.] Worked values using the measured $(b,\sigma_1)$ of (M63) and $H/f_s = 42.67$ ms:

| condition | $\varepsilon = 1^\circ$ | $\varepsilon = 2^\circ$ | $\varepsilon = 3^\circ$ |
|---|---|---|---|
| free field ($b\!=\!0$, $\sigma_1\!=\!3.96^\circ$) | $T^*=16$, $L^*=0.67$ s | $T^*=4$, $L^*=0.17$ s | $T^*=2$, $L^*=0.07$ s |
| RT60 0.15 s ($b\!=\!1.79$, $\sigma_1\!=\!4.53$) | unreachable | $T^*=26$, $L^*=1.10$ s | $T^*=4$, $L^*=0.15$ s |
| RT60 0.30 s ($b\!=\!2.22$, $\sigma_1\!=\!6.25$) | unreachable | unreachable | $T^*=10$, $L^*=0.41$ s |
| RT60 0.60 s ($b\!=\!3.15$, $\sigma_1\!=\!10.3$) | unreachable | unreachable | unreachable |

[VERIFIED by direct evaluation of (M66).]

**Futility condition.** Accumulation is worth continuing only while the variance term is not
already negligible against the bias. Defining "negligible" as
$\sigma_1^2/T \le \alpha\,b^2$,

$$T_{\mathrm{futile}}(\alpha) = \frac{\sigma_1^{2}}{\alpha\,b^{2}}
\qquad\Longrightarrow\qquad
\frac{\mathrm{d}\,\mathrm{RMSE}}{\mathrm{d}T}
= -\frac{\sigma_1^{2}}{2T^{2}\sqrt{b^{2}+\sigma_1^{2}/T}} . \tag{M67}$$

At $\alpha = 0.1$ (variance term 10 % of the bias term, i.e. RMSE within 5 % of the floor):
$T_{\mathrm{futile}} = 65$ frames (2.8 s) at RT60 = 0.15 s, 80 frames (3.4 s) at 0.30 s, and
108 frames (4.6 s) at 0.60 s. Beyond those points, additional latency buys nothing. This is
the honest ceiling statement the paper needs, and it also says that the $T\le 32$ sweep in
`ablation_run.log` stops *before* the floor is reached — which is exactly why the fits in
Section 6.4 are ambiguous.

### 6.6 The recursive, constant-memory form

Equation (M52) is already a running sum, but a fixed window requires either storing $T$ frames
or re-deriving the sum. The exponentially weighted form avoids both. Maintain a single complex
accumulator $z_t\in\mathbb{C}$:

$$z_t = (1-\lambda)\,z_{t-1} + \lambda\,w_t\,e^{\mathrm{i}\hat\theta_t},
\qquad
\hat\theta^{(t)} = \arg z_t . \tag{M68}$$

The implicit weights are $\lambda(1-\lambda)^{k}$, $k\ge 0$, so

$$\sum_k w_k = 1,\qquad \sum_k w_k^{2} = \frac{\lambda^{2}}{1-(1-\lambda)^{2}}
= \frac{\lambda}{2-\lambda}, \tag{M69}$$

$$\boxed{\ T_{\mathrm{eff}}^{\mathrm{EWMA}} = \frac{2-\lambda}{\lambda}\ \approx\ \frac{2}{\lambda}
\quad (\lambda\ll 1),
\qquad
\text{time constant } \tau_c = \frac{-1}{\ln(1-\lambda)} \approx \frac{1}{\lambda}\ \text{frames.}\ } \tag{M70}$$

[DERIVED via (M58).] Design table at $H/f_s = 42.67$ ms per frame:

| $\lambda$ | $T_{\mathrm{eff}}$ (frames) | $\tau_c$ (frames) | equivalent latency |
|---|---|---|---|
| 0.50 | 3.0 | 2.0 | 0.13 s |
| 0.25 | 7.0 | 4.0 | 0.30 s |
| 0.10 | 19.0 | 10.0 | 0.81 s |
| 0.05 | 39.0 | 20.0 | 1.66 s |
| 0.02 | 99.0 | 50.0 | 4.22 s |

**Cost.** State $= 2$ floats (8 bytes), independent of $T$ — the $O(1)$-memory claim.
Per frame: 2 multiply–adds and 2 multiplies plus one $\sin$ and one $\cos$. The
transcendentals can be eliminated entirely, because the least-squares solution
$\hat{\mathbf u}$ of (M32) is *already* a vector along $(\cos\hat\theta,\sin\hat\theta)$.
Accumulating the normalised vector directly,

$$z_t = (1-\lambda)z_{t-1} + \lambda\,w_t\,\frac{\hat{\mathbf u}_t}{\|\hat{\mathbf u}_t\|},
\tag{M71}$$

is algebraically identical to (M68) and costs one reciprocal square root, two multiplies and
two multiply–adds per frame: **five floating-point operations and no transcendental**, with a
single `atan2` needed only when a numeric bearing is to be output. This makes the "a few adds
per frame" claim exact rather than rhetorical.

### 6.7 Stationarity, smearing, and the optimal window for a moving source

Let the source move at constant angular rate $\omega$ (rad s$^{-1}$), so
$\theta(t) = \theta_0 + \omega t$. Over a window of latency $L$ the true bearing sweeps
$\Delta\Theta = \omega L$. With uniform weights, the circular mean of the true track is the
mid-window bearing, so relative to the bearing at the *end* of the window the estimator lags by

$$b_{\mathrm{smear}} = \frac{\omega L}{2} = \frac{\omega T H}{2 f_s}. \tag{M72}$$

[DERIVED; exact for uniform weights and small $\Delta\Theta$, where the circular mean of a
uniformly swept arc is its midpoint. For an EWMA the corresponding lag is $\omega\tau_c H/f_s$.]
Adding (M72) in quadrature to (M62):

$$\mathrm{MSE}(T) = b^{2} + \frac{\sigma_1^{2}}{T} + \left(\frac{\omega T H}{2 f_s}\right)^{2}.
\tag{M73}$$

Minimising over $T$ (or equivalently over $L$):

$$\frac{\partial}{\partial L}\!\left[\frac{\sigma_1^{2}H}{f_s L} + \frac{\omega^{2}L^{2}}{4}\right] = 0
\quad\Longrightarrow\quad
\boxed{\ L_{\mathrm{opt}} = \left(\frac{2\,\sigma_1^{2}\,H}{f_s\,\omega^{2}}\right)^{1/3},
\qquad
T_{\mathrm{opt}} = \frac{f_s}{H}\left(\frac{2\sigma_1^{2}H}{f_s\omega^{2}}\right)^{1/3}
= \left(\frac{2\,\sigma_1^{2}f_s^{2}}{\omega^{2}H^{2}}\right)^{1/3}. \ } \tag{M74}$$

[DERIVED.] With the measured free-field $\sigma_1 = 3.96^\circ = 0.0691$ rad and
$H/f_s = 42.67$ ms:

| $\omega$ | $L_{\mathrm{opt}}$ | $T_{\mathrm{opt}}$ | minimum achievable RMSE (excl. $b$) |
|---|---|---|---|
| 1$^\circ$/s | 1102 ms | 25.8 | 0.95$^\circ$ |
| 5$^\circ$/s | 377 ms | 8.8 | 1.63$^\circ$ |
| 10$^\circ$/s | 237 ms | 5.6 | 2.06$^\circ$ |
| 30$^\circ$/s | 114 ms | 2.7 | 2.97$^\circ$ |
| 90$^\circ$/s | 55 ms | 1.3 | 4.28$^\circ$ |

[VERIFIED by direct evaluation of (M73)–(M74).] The interpretation for the paper: the
$T=20$–32 windows that give sub-degree free-field accuracy are only admissible for sources
moving slower than about $1^\circ$/s. A walking talker at 1 m subtends roughly $60^\circ$/s,
for which $T_{\mathrm{opt}}\approx 1.6$ frames and accumulation buys almost nothing. The
accuracy–latency trade is real but is confined to quasi-stationary sources, and (M74) is the
quantitative statement of that limit.

---

## 7. Complexity

### 7.1 Cost model

Costs are quoted in floating-point operations per frame. A length-$L$ real FFT is charged
$C_{\mathrm{FFT}}(L) = 2.5\,L\log_2 L$ (half the standard $5L\log_2 L$ for a complex FFT).
Parameters: $N=2048$, $M=3$, $P=3$, $n=2N=4096$, $K=n/2+1=2049$, $I=8$, $G=360$.

### 7.2 Proposed estimator and GCC-PHAT (shared front end)

$$C_{\mathrm{GCC}} =
\underbrace{M\,C_{\mathrm{FFT}}(n)}_{\text{forward}}
+ \underbrace{P\,(6K + 4K + 2K)}_{\text{CPSD, }|\cdot|,\text{ divide}}
+ \underbrace{P\,C_{\mathrm{FFT}}(I n)}_{\text{interpolated inverse}}
+ \underbrace{P\,(In+1)}_{\text{argmax}}
+ \underbrace{\mathcal{O}(P)}_{\text{LS}} \tag{M75}$$

| term | MFLOP | share |
|---|---|---|
| forward FFTs | 0.369 | 8.7 % |
| CPSD + PHAT | 0.074 | 1.7 % |
| **interpolated inverse FFTs** | **3.686** | **87.2 %** |
| argmax | 0.098 | 2.3 % |
| least squares | $5\times10^{-5}$ | $<$0.1 % |
| **total** | **4.227** | |

The proposed estimator adds only the PSR computation (M41), which is three additional passes
over the length-$In$ correlation per pair:

$$C_{\mathrm{prop}} = C_{\mathrm{GCC}} + 3P\,In = 4.522\ \mathrm{MFLOP},
\qquad \frac{C_{\mathrm{prop}}}{C_{\mathrm{GCC}}} = 1.070 . \tag{M76}$$

**Measured** [LOG]: 1.353 ms versus 1.289 ms, i.e. a ratio of **1.050**. Predicted $+7.0$ %,
measured $+5.0$ %. This is the ratio the paper actually needs (the decision layer is
computationally free) and the FLOP model predicts it correctly.

### 7.3 SRP-PHAT and MUSIC

$$C_{\mathrm{SRP}} = C_{\mathrm{GCC}} + G\big[\,\underbrace{2M+M}_{\text{steering}}
+ P(\underbrace{\log_2(In)}_{\text{table search}} + 4)\big] + G
= 4.253\ \mathrm{MFLOP}, \tag{M77}$$

$$C_{\mathrm{MUSIC}} = K_{\mathrm{sn}} M\big[L + C_{\mathrm{FFT}}(L)\big]
+ F_{\mathrm{band}}\Big[\underbrace{8M^{2}K_{\mathrm{sn}}}_{\hat{\mathbf R}}
+ \underbrace{\mathcal{O}(M^{3})}_{\text{eigh}}
+ \underbrace{c_{\exp} G M}_{\text{manifold}}
+ \underbrace{8GM^{2}}_{\mathbf{P}_n\mathbf{A}} + \underbrace{8GM}_{\text{reduce}}\Big] , \tag{M78}$$

with $L=512$, hop $=256$, $K_{\mathrm{sn}}=7$ snapshots, $F_{\mathrm{band}}=33$ bins in
300–3400 Hz, $G=360$, and $c_{\exp}\approx 50$ flop-equivalents per complex exponential:
$C_{\mathrm{MUSIC}} = 3.239$ MFLOP.

### 7.4 Analytical versus measured, stated honestly

| method | predicted MFLOP | predicted ratio to GCC | measured ms [LOG] | measured ratio |
|---|---|---|---|---|
| GCC-PHAT | 4.227 | 1.000 | 1.289 | 1.00 |
| Proposed (gated) | 4.522 | 1.070 | 1.353 | 1.05 |
| SRP-PHAT | 4.253 | **1.006** | 5.494 | **4.26** |
| MUSIC | 3.239 | **0.766** | 5.459 | **4.24** |

**The model and the measurement disagree by a factor of 4 for SRP-PHAT and MUSIC, and the
disagreement is fully explained.** It is not a modelling failure; it is interpreter overhead.

* **SRP-PHAT.** As implemented, SRP reuses the *same* pairwise GCC-PHAT correlations and then
  performs $G=360$ table lookups per pair. Arithmetically that is 0.026 MFLOP on top of
  4.227 MFLOP, i.e. $+0.6$ %. But the grid search is a Python-level loop of 360 iterations,
  each issuing one `steering_delays` call and three `np.interp` calls, i.e. 1440 NumPy calls
  per estimate. [NEW RUN, isolating the two stages: the GCC front end alone takes 1.440 ms and
  the grid loop alone takes 3.275 ms, i.e. **2.27 $\mu$s per NumPy call** — pure dispatch
  overhead. The two stages sum to 4.72 ms against the logged 5.49 ms.] The measured
  SRP/GCC ratio measures the Python interpreter, not the algorithm.
* **MUSIC.** The FLOP model predicts MUSIC should be *cheaper* than this GCC implementation,
  because $M=3$ makes the eigendecomposition trivial. The measured cost is dominated by
  (i) 33 LAPACK `eigh` calls on $3\times 3$ matrices, whose per-call overhead is far larger
  than their arithmetic, and (ii) $33\times 1080 = 35\,640$ complex exponentials for the
  steering manifold, whose true cost per element far exceeds the 50 flop-equivalents charged
  in (M78).

**What the paper may and may not claim.**

* **May claim:** the proposed decision layer is computationally free relative to GCC-PHAT
  ($+5$ % measured, $+7$ % predicted), which is the claim the ablation needs.
* **May claim (asymptotically):** SRP-PHAT costs $\mathcal{O}(MIn\log(In) + GP)$ and MUSIC
  $\mathcal{O}(F_{\mathrm{band}}(M^{3}+GM^{2}))$ against GCC's $\mathcal{O}(MIn\log(In))$; the
  $G$ and $M$ terms are what make them expensive on larger arrays and finer grids. At
  $M=3$, $G=360$ those terms happen to be small.
* **Must not claim:** that the measured $4.3\times$ ratio is an algorithmic complexity ratio.
  It should be reported as "wall-clock time for the reference NumPy implementation on x86",
  with the overhead caveat stated. Presenting it otherwise would be exactly the kind of
  overclaim this project is trying to avoid.

### 7.5 The dominant cost is the interpolation factor, and it is avoidable

87 % of $C_{\mathrm{GCC}}$ is the length-$In$ inverse FFT. Replacing $I=8$ frequency-domain
interpolation with a length-$n$ inverse FFT plus parabolic refinement (M20) gives

| term | $I=8$ (MFLOP) | $I=1$ + parabolic (MFLOP) |
|---|---|---|
| forward FFTs | 0.369 | 0.369 |
| CPSD + PHAT | 0.074 | 0.074 |
| inverse FFTs | 3.686 | 0.369 |
| argmax | 0.098 | 0.012 |
| **total** | **4.227** | **0.823** |

a reduction of $5.13\times$ overall and $10.0\times$ in the inverse-transform term. The price
is the interpolation bias of Section 2.3 (up to 0.119 samples, i.e. $0.46^\circ$), which a
lookup-table correction removes. **The benchmark's compute figures are therefore pessimistic
by a factor of about 5 relative to a sensible embedded implementation**, and the paper should
say so rather than quoting 4.2 MFLOP as the cost of the method.

### 7.6 Memory and an order-of-magnitude MCU estimate

| buffer | $I=8$ | $I=1$ |
|---|---|---|
| input, $MN$ float32 | 24 kB | 24 kB |
| correlation, $In$ float32 (per pair, reusable) | 128 kB | 16 kB |
| accumulator (M68) | 8 B | 8 B |
| SRP grid table, $GM$ float32 | 4.2 kB | 4.2 kB |
| MUSIC manifold, $GM$ complex64 per bin | 8.4 kB | 8.4 kB |

At 240 MHz and one FLOP per cycle on the ESP32-S3 scalar FPU, 4.227 MFLOP is 17.6 ms and
0.823 MFLOP is 3.4 ms, against a frame period of 42.7 ms. These are *lower bounds* (they
ignore memory stalls, integer overhead and the absence of an optimised FFT), and they are
offered only to show the design point is plausible. [MEASURE: real per-estimate latency via
`real_data.py --latency` on device.]

---

## 8. A theoretical accuracy bound

### 8.1 Cramér–Rao bound on azimuth for this array

Take the discrete-time model matching `simulate()` exactly: $x_m[k] = s[k-\tau_m f_s] + w_m[k]$,
$k=0,\dots,N-1$, with $w_m$ i.i.d. $\mathcal{N}(0,\sigma_w^2)$, mutually independent across $m$.
Treating $s$ as known (an optimistic bound; the unknown-waveform bound is looser), the Fisher
information for $\theta$ is

$$J_\theta = \frac{1}{\sigma_w^{2}}\left(\sum_{k}\dot s[k]^{2}\right)
\sum_{m=1}^{M}\left(\frac{\partial\tau_m}{\partial\theta}\right)^{2}. \tag{M79}$$

Because only *relative* delays are observable, the sensitivity vector must be centred; for the
equilateral array $\sum_m \partial\tau_m/\partial\theta = 0$ automatically by (M2), so no
centring is needed. From (M3),

$$\frac{\partial\tau_m}{\partial\theta} = -\frac{\mathbf{p}_m^{\mathsf T}\mathbf{e}_\theta}{c},
\qquad
\sum_{m}\left(\frac{\partial\tau_m}{\partial\theta}\right)^{2}
= \frac{\mathbf{e}_\theta^{\mathsf T}\big(\sum_m\mathbf{p}_m\mathbf{p}_m^{\mathsf T}\big)\mathbf{e}_\theta}{c^{2}}
\overset{\text{(M2)}}{=} \frac{3R^{2}}{2c^{2}}, \tag{M80}$$

**again direction-independent**, in agreement with (M39). With $E_s=\sum_k s[k]^2 = N P_s$ and
the mean-square radian bandwidth

$$\beta^{2} = \frac{\sum_k (2\pi f_k)^{2}|S_k|^{2}}{\sum_k |S_k|^{2}}
\ \overset{\text{flat band}}{=}\ \frac{4\pi^{2}\,(f_2^{3}-f_1^{3})}{3\,(f_2-f_1)}, \tag{M81}$$

so that $\sum_k \dot s[k]^2 = \beta^2 E_s$, and with $\mathrm{SNR} = P_s/\sigma_w^2$,

$$\boxed{\ J_\theta = N\cdot\mathrm{SNR}\cdot\beta^{2}\cdot\frac{3R^{2}}{2c^{2}},
\qquad
\sigma_\theta \ \ge\ \frac{1}{\sqrt{J_\theta}}
= \frac{c}{R}\sqrt{\frac{2}{3\,N\,\mathrm{SNR}\,\beta^{2}}} \ } \tag{M82}$$

[DERIVED.] For the source band 300–3400 Hz, (M81) gives $\beta = 12\,913$ rad s$^{-1}$, i.e.
an r.m.s. bandwidth of **2055 Hz**.

### 8.2 The pairwise Knapp–Carter bound, for cross-checking

The classical delay-variance bound for the generalized correlator is

$$\sigma_\tau^{2} \ \ge\ \left[2\,T_{\mathrm{obs}}\int_{f_1}^{f_2}(2\pi f)^{2}
\frac{|\gamma(f)|^{2}}{1-|\gamma(f)|^{2}}\,\mathrm{d}f\right]^{-1} \tag{M83}$$

[CITE Knapp & Carter 1976], [CITE Carter 1987]. For equal-noise channels with per-channel
in-band SNR $\Gamma$, $|\gamma| = \Gamma/(1+\Gamma)$ and
$|\gamma|^2/(1-|\gamma|^2) = \Gamma^2/(1+2\Gamma)$. Feeding the resulting $\sigma_\tau$ through
the GDOP law (M40) should reproduce (M82) up to the difference between three independent
pairwise estimates and the two independent delays actually present.

**Important bookkeeping.** The simulation's nominal SNR is defined over the full 0–24 kHz
band while the source occupies 3100 Hz, so the in-band SNR is

$$\Gamma = \mathrm{SNR}\cdot\frac{f_s/2}{f_2-f_1} = \mathrm{SNR}\times 7.742
\qquad (+8.89\ \mathrm{dB}). \tag{M84}$$

The paper must quote in-band SNR when comparing with the bound, or the comparison is wrong by
8.9 dB.

### 8.3 Bound versus achieved

| nominal SNR | in-band $\Gamma$ | (M82) CRB $\sigma_\theta$ | (M83) CRB $\sigma_\tau$ | (M83)$\to$(M40) $\sigma_\theta$ | achieved $\sigma_\tau$ (full-band PHAT) | achieved $\sigma_\tau$ (band-limited) |
|---|---|---|---|---|---|---|
| 0 dB | 8.89 dB | 0.549$^\circ$ | 2.497 $\mu$s | 0.463$^\circ$ | 26.1 $\mu$s | 3.45 $\mu$s |
| 10 dB | 18.89 dB | **0.174$^\circ$** | **0.768 $\mu$s** | 0.142$^\circ$ | 22.3 $\mu$s | 1.49 $\mu$s |
| 20 dB | 28.89 dB | 0.055$^\circ$ | 0.242 $\mu$s | 0.045$^\circ$ | 14.1 $\mu$s | 0.82 $\mu$s |
| 40 dB | 48.89 dB | 0.0055$^\circ$ | 0.024 $\mu$s | 0.0045$^\circ$ | 9.4 $\mu$s | 0.78 $\mu$s |

[VERIFIED: the two independent bounds agree to within a factor 1.22 at every SNR, which is the
expected consequence of (M83) treating the three pairwise delays as independent when only two
are.]

**How far from optimal is the estimator? Blunt answer.**

* **As implemented (full-band PHAT):** at 10 dB the achieved per-pair $\sigma_\tau$ is
  22.3 $\mu$s against a bound of 0.768 $\mu$s — a factor **29 in standard deviation, 29 dB in
  variance**. The corresponding azimuth RMSE is 4.23$^\circ$ [LOG] against a bound of
  0.174$^\circ$, a factor 24. The estimator is nowhere near optimal.
* **The gap is explained, not hand-waved.** Equation (M23)–(M24) predicts a loss of
  $\sqrt{352} = 18.8$ from applying the PHAT weight over the full band; the remaining factor
  of $29/18.8 = 1.5$ is attributable to the plain argmax over an unrestricted lag range
  (Section 2.5) and to the sub-optimality of PHAT relative to (M21) even in band.
* **With the band-limited weight:** at 10 dB $\sigma_\tau = 1.49\ \mu$s against a bound of
  0.768 $\mu$s. Adding the interpolation-grid floor (M25) in quadrature,
  $\sqrt{0.768^2+0.752^2} = 1.075\ \mu$s, the estimator is within a factor **1.39** of the
  attainable precision. At 20 and 40 dB it is *at* the interpolation floor
  ($\sigma_\tau = 0.82$ and $0.78\ \mu$s against $\sigma_{\tau,q}=0.752\ \mu$s), i.e. no longer
  noise-limited at all.

**Statement for the paper.** GCC-PHAT is not intrinsically 25 dB from the bound. The
benchmarked implementation is, because of a weighting choice; corrected, the same estimator is
within 40 % of the bound at 10 dB and grid-limited above 20 dB. Whether the paper re-runs the
harness with the corrected weight, or reports the current numbers and this analysis as a
limitation, is a decision for the writing track — but it must be one or the other, and stated
explicitly.

---

## 9. Near-field two-dimensional localisation (appendix material)

**Scope.** This section is written to support an appendix, not a body section. The decisive
content is Section 9.5, which shows quantitatively at what range a 5 cm array stops supporting
a meaningful 2-D fix, and therefore justifies the scoping decision.

### 9.1 What `t` in the quadrant CSVs actually is — determined empirically

The four files `Quadrant Based Estimations/quadrant_{1..4}.csv` contain columns `x, y, t` on a
0.05 m grid, $x,y\in[-3,3]$ m, 3600–3721 rows each, 14 631 valid rows in total (there are 10
`NaN` entries in `t`, all at $x = -0.0$, five in each of `quadrant_3` and `quadrant_4`).

At $(0.05,0.05)$, $t = 99.82\ \mu$s. Straight-line propagation from the origin would be
$\sqrt{2}\times 0.05/343 = 206\ \mu$s, so the naive reading is indeed wrong.
The maximum value over all four files is $t_{\max} = 145.77\ \mu$s, and
$343\,t_{\max} = 0.0500000018$ m. That is the signature of a **5 cm baseline TDOA**, not a
propagation time.

Fitting the two-parameter model
$t = \big|\,\|\mathbf{x}-(-a,0)\| - \|\mathbf{x}-(+a,0)\|\,\big|/c$ over all 14 631 rows by
nonlinear least squares recovers

$$a = 0.025000\ \mathrm{m}\ \ (\text{baseline } 2a = 0.0500\ \mathrm{m}),
\qquad c = 343.000\ \mathrm{m\,s^{-1}}, \tag{M85}$$

with residual r.m.s. **0.029 ns** and maximum residual 0.2 ns — i.e. exactly the rounding of
the stored $10^{-10}$ s precision. [VERIFIED; three alternative hypotheses (baseline along
$y$; microphones at $(0,0)$ and $(0.05,0)$; and a signed rather than absolute TDOA) were
tested and rejected with residuals of 80.7 $\mu$s, 2.30 $\mu$s and "no match" respectively.]

$$\boxed{\ t = \frac{\Big|\,\|\mathbf{x}-\mathbf{m}_1\| - \|\mathbf{x}-\mathbf{m}_2\|\,\Big|}{c},
\quad \mathbf{m}_{1,2} = (\mp 0.025,\ 0)\ \mathrm{m},\quad c = 343\ \mathrm{m\,s^{-1}}. \ } \tag{M86}$$

**Three conclusions that must be stated in the paper.**

1. `t` is the **absolute inter-microphone TDOA** across a 5 cm two-microphone baseline lying
   along the $x$ axis and centred at the origin, evaluated with the exact spherical-wave
   (near-field) range difference. It is not an arrival time, and it is not referenced to the
   three-microphone triangular array of the rest of the paper.
2. The residual of 0.029 ns proves these files are the output of an **analytic forward model**,
   not a measurement and not an estimator output. They contain no acoustic data and no error
   information. They are a geometry visualisation.
3. Consequently they can legitimately be used to *illustrate* the hyperbolic TDOA geometry
   (Section 9.3) but cannot support any accuracy claim whatever. Using them as evidence of
   localisation performance would repeat the `Triple Mic Samples/python.py` problem.

[MEASURE / metadata needed: the intended microphone coordinates of the board, whether the
5 cm baseline in these files corresponds to a real pair on the PCB, and whether any measured
TDOA data exists for these grid positions.]

### 9.2 Near-field spherical-wavefront TDOA model

Drop assumption A3. For a source at $\mathbf{x}_s\in\mathbb{R}^2$,

$$\tau_m = \frac{\|\mathbf{x}_s-\mathbf{p}_m\|}{c} + t_0,
\qquad
\tau_{ij} = \frac{\|\mathbf{x}_s-\mathbf{p}_i\| - \|\mathbf{x}_s-\mathbf{p}_j\|}{c}, \tag{M87}$$

with $t_0$ the unknown emission time, which cancels in the TDOA. Writing
$r_m = \|\mathbf{x}_s-\mathbf{p}_m\|$ and $R_{ij} = c\,\tau_{ij} = r_i - r_j$, each pair
constrains $\mathbf{x}_s$ to one branch of a hyperbola with foci $\mathbf{p}_i,\mathbf{p}_j$
and transverse semi-axis $|R_{ij}|/2$:

$$\frac{(\mathbf{x}_s\!\cdot\!\hat{\mathbf a}_{ij} - \mu_{ij})^{2}}{(R_{ij}/2)^{2}}
- \frac{(\mathbf{x}_s\!\cdot\!\hat{\mathbf a}^{\perp}_{ij} - \nu_{ij})^{2}}
{(d_{ij}/2)^{2}-(R_{ij}/2)^{2}} = 1, \tag{M88}$$

with $\hat{\mathbf a}_{ij}$ the unit baseline direction and $(\mu_{ij},\nu_{ij})$ the baseline
midpoint in those coordinates. The 2-D fix is the intersection of $M-1 = 2$ independent
hyperbola branches. The far-field limit $R_{ij}\to d_{ij}\cos(\theta-\alpha_{ij})$ recovers
(M4): the hyperbolae degenerate into their asymptotic rays and range information is lost.

### 9.3 Closed-form solution (Chan–Ho form)

Linearising by introducing the nuisance variable $r_1 = \|\mathbf{x}_s-\mathbf{p}_1\|$ and
using $r_i = r_1 + R_{i1}$ with $r_i^2 = \|\mathbf{x}_s\|^2 - 2\mathbf{p}_i^{\mathsf T}\mathbf{x}_s + \|\mathbf{p}_i\|^2$:

$$R_{i1}^{2} + 2R_{i1}r_1
= \|\mathbf{p}_i\|^{2}-\|\mathbf{p}_1\|^{2} - 2(\mathbf{p}_i-\mathbf{p}_1)^{\mathsf T}\mathbf{x}_s ,
\qquad i = 2,\dots,M, \tag{M89}$$

which is **linear** in the augmented unknown $\boldsymbol\zeta = (\mathbf{x}_s^{\mathsf T},\,r_1)^{\mathsf T}$:

$$\mathbf{G}\boldsymbol\zeta = \mathbf{h},\qquad
\mathbf{G} = \begin{bmatrix}(\mathbf{p}_2-\mathbf{p}_1)^{\mathsf T} & R_{21}\\
\vdots & \vdots\\ (\mathbf{p}_M-\mathbf{p}_1)^{\mathsf T} & R_{M1}\end{bmatrix},
\quad
h_i = \tfrac12\Big(\|\mathbf{p}_i\|^{2}-\|\mathbf{p}_1\|^{2} - R_{i1}^{2}\Big). \tag{M90}$$

The Chan–Ho estimator [CITE Chan & Ho 1994] is a two-stage weighted least squares: stage one
solves (M90) treating $\boldsymbol\zeta$ as unconstrained with weight
$\mathbf{W}_1 = (c^2\boldsymbol\Sigma_\tau)^{-1}$ scaled by the range Jacobian; stage two
imposes the constraint $r_1 = \|\mathbf{x}_s-\mathbf{p}_1\|$ that stage one ignored, by a
second weighted least squares on the squared components. At $M=3$ the system (M90) is
$2\times 3$, i.e. **under-determined without the constraint**: two TDOAs cannot determine
$(x,y,r_1)$, and the fix rests entirely on the second-stage nonlinear constraint. This is a
structural fragility of a three-microphone 2-D fix and should be stated. [CITE Smith & Abel 1987],
[CITE Huang et al. 2001] give the alternative spherical-interpolation and linear-correction
formulations.

### 9.4 Near-field GDOP

The Jacobian of the range differences with respect to source position is

$$\mathbf{J}(\mathbf{x}_s) = \begin{bmatrix}
(\hat{\mathbf r}_1-\hat{\mathbf r}_2)^{\mathsf T}\\
(\hat{\mathbf r}_2-\hat{\mathbf r}_3)^{\mathsf T}\end{bmatrix},
\qquad
\hat{\mathbf r}_m = \frac{\mathbf{x}_s-\mathbf{p}_m}{\|\mathbf{x}_s-\mathbf{p}_m\|}, \tag{M91}$$

$$\operatorname{Cov}(\hat{\mathbf x}_s) = c^{2}\sigma_\tau^{2}\,
\big(\mathbf{J}^{\mathsf T}\mathbf{J}\big)^{-1}. \tag{M92}$$

The far-field expansion of (M91) is the key to the whole scoping argument. Using
$\hat{\mathbf r}_m \approx \mathbf{u} - \mathbf{P}_\perp\mathbf{p}_m/r$ with
$\mathbf{P}_\perp = \mathbf{I}-\mathbf{u}\mathbf{u}^{\mathsf T}$:

$$\hat{\mathbf r}_i - \hat{\mathbf r}_j
= -\frac{\mathbf{P}_\perp(\mathbf{p}_i-\mathbf{p}_j)}{r} + \mathcal{O}(r^{-2}). \tag{M93}$$

* The **cross-range** (tangential) sensitivity is $\mathcal{O}(1/r)$, and a cross-range
  displacement of $r\,\delta\theta$ produces a range-difference change independent of $r$ —
  i.e. azimuth remains estimable at any range, as it must.
* The **radial** sensitivity is $\mathcal{O}(1/r^{2})$: from (M10),
  $\partial(c\tau_{ij})/\partial r = -[(\mathbf{p}_j^{\mathsf T}\mathbf{u})^{2}
  -(\mathbf{p}_i^{\mathsf T}\mathbf{u})^{2}]/(2r^{2}) = \mathcal{O}(R^{2}/r^{2})$.
  **Range is observable only through wavefront curvature**, and curvature dies as $1/r^2$.

Hence, to leading order,

$$\sigma_r \ \sim\ \frac{2\,c\,\sigma_\tau\,r^{2}}{\kappa\,R^{2}},\qquad \kappa = \mathcal{O}(1) .
\tag{M94}$$

[VERIFIED: evaluating (M92) exactly and taking the median over azimuth gives
$\sigma_r/(c\sigma_\tau) = 380.5,\ 1505.2,\ 6018.4,\ 24\,069.8$ at $r = 0.5,\ 1,\ 2,\ 4$ m,
i.e. exactly the $r^2$ law, with the empirical constant

$$\sigma_r \ \simeq\ 3.8\ c\,\sigma_\tau\,\frac{r^{2}}{R^{2}} \qquad (R = 5\ \mathrm{cm}).\ ]
\tag{M95}$$

### 9.5 The range at which the 2-D fix becomes meaningless

Setting $\sigma_r = r$ in (M95):

$$\boxed{\ r_{\mathrm{break}} \ \simeq\ \frac{R^{2}}{3.8\,c\,\sigma_\tau}\ } \tag{M96}$$

| assumed $\sigma_\tau$ | source of the figure | $r_{\mathrm{break}}$ (exact numeric) |
|---|---|---|
| 0.768 $\mu$s | CRB at 10 dB, Section 8.3 | **2.52 m** |
| 20.83 $\mu$s | one sample period at 48 kHz | 0.105 m |
| 22.3 $\mu$s | achieved by the implemented front end | **0.099 m** |
| 1.49 $\mu$s | achieved with band-limited PHAT | 1.29 m (by (M96)) |

[VERIFIED: $r_{\mathrm{break}}$ solved by root-finding on the exact (M92), median over 180
azimuths; the closed form (M96) reproduces the CRB row to 1 %.] Detailed values at the CRB:

| $r$ | median $\sigma_r$ | as % of $r$ | median cross-range $\sigma$ |
|---|---|---|---|
| 0.10 m | 3.5 mm | 3.5 % | 1.0 mm |
| 0.25 m | 25 mm | 10.2 % | — |
| 0.50 m | 100 mm | 20.0 % | 4.4 mm |
| 1.00 m | 397 mm | 39.7 % | 9.8 mm |
| 2.00 m | 1585 mm | 79.3 % | 26.9 mm |

**Scoping conclusion (the argument for keeping this in an appendix).**

* Range is estimable to better than 20 % of true range only inside about **0.5 m**, and only
  at the Cramér–Rao bound, i.e. with an ideally-weighted front end that the present code does
  not implement.
* With the TDOA precision the front end **actually achieves** (22.3 $\mu$s), $r_{\mathrm{break}}
  \approx 0.10$ m: range is unrecoverable essentially everywhere. Even with the band-limited
  correction (1.49 $\mu$s) it is $\approx 1.3$ m.
* Cross-range (azimuth) accuracy, by contrast, is unaffected by range.
* A further, separate penalty: jointly estimating $(x,y)$ rather than $\theta$ alone degrades
  the **azimuth** too. [VERIFIED: at $r=1$ m with $\sigma_\tau = 0.768\ \mu$s the 2-D fit gives
  a cross-range standard deviation of 9.8 mm, i.e. $\sigma_\theta = 0.56^\circ$, against
  $0.14^\circ$ for the azimuth-only three-pair estimator (M40) — a factor of 4. Part is the
  use of 2 rather than 3 pairs ($\sqrt{1.5}=1.22$); the rest is the range–azimuth coupling.]

Therefore: azimuth-only is not merely a modelling convenience, it is the *better* estimator,
and the 2-D result belongs in an appendix framed as a geometric feasibility analysis with an
explicit range limit — not as a localisation capability.

---

## 10. Noise floor and SNR definition

### 10.1 Operational definition of SNR

Three different SNRs appear in this project and they must not be conflated.

$$\mathrm{SNR}_{\mathrm{wb}} = \frac{P_s}{P_n}\bigg|_{[0,\,f_s/2]}
\qquad\text{(what \texttt{simulate()} sets)} \tag{M97}$$

$$\mathrm{SNR}_{\mathrm{ib}} = \Gamma = \frac{\int_{f_1}^{f_2}\!S_{ss}(f)\,\mathrm{d}f}
{\int_{f_1}^{f_2}\!S_{nn}(f)\,\mathrm{d}f}
\qquad\text{(what the CRB (M83) uses)} \tag{M98}$$

$$\mathrm{SNR}_{\mathrm{op}} = 10\log_{10}
\frac{\overline{(x_m[k]-\bar x_m)^{2}}\Big|_{\text{source active}}
- \overline{(x_m[k]-\bar x_m)^{2}}\Big|_{\text{idle}}}
{\overline{(x_m[k]-\bar x_m)^{2}}\Big|_{\text{idle}}}\ \ \mathrm{dB}
\qquad\text{(what the hardware section should report)} \tag{M99}$$

Definition (M99) is referenced to a **measured** idle floor and is the only one obtainable on
the bench. For the simulation's configuration, $\mathrm{SNR}_{\mathrm{ib}} =
\mathrm{SNR}_{\mathrm{wb}} + 8.89$ dB by (M84). **Every SNR figure in the paper must state
which definition it uses.**

### 10.2 Quantisation noise floor, parametric in bit depth

For an ideal $Q$-bit uniform converter of full-scale range $V_{\mathrm{FS}}$, step
$\Delta = V_{\mathrm{FS}}/2^{Q}$, and quantisation error uniform on $[-\Delta/2,\Delta/2]$:

$$\sigma_q^{2} = \frac{\Delta^{2}}{12} = \frac{V_{\mathrm{FS}}^{2}}{12\cdot 2^{2Q}},
\qquad
\sigma_q = \frac{V_{\mathrm{FS}}}{2^{Q}\sqrt{12}}
\;=\; \frac{1}{\sqrt{12}}\ \text{LSB}\;=\;0.2887\ \text{LSB}. \tag{M100}$$

$$\mathrm{SQNR}_{\max} = 6.02\,Q + 1.76\ \ \mathrm{dB}\quad\text{(full-scale sine)}
\qquad\Longrightarrow\qquad
\begin{cases} Q=12: & 74.0\ \mathrm{dB}\\ Q=16: & 98.1\ \mathrm{dB}\\ Q=24: & 146.2\ \mathrm{dB}\end{cases}
\tag{M101}$$

Spread over the band, the one-sided quantisation-noise PSD is

$$S_{qq}(f) = \frac{2\sigma_q^{2}}{f_s}\ \ \left[\text{LSB}^{2}\,\mathrm{Hz}^{-1}\right],
\qquad
\text{in-band power} = \frac{2\sigma_q^{2}(f_2-f_1)}{f_s}. \tag{M102}$$

Processing gain from band-limiting to $[f_1,f_2]$ is $10\log_{10}\big(f_s/2(f_2-f_1)\big)$
= 8.89 dB for $f_s = 48$ kHz, $B=3100$ Hz.

### 10.3 Measured idle floor — preliminary, with the slot marked

[NEW RUN, preliminary; the analysis track owns this number.] `idle mic data/data.xlsx`
column 0 contains 16 854 numeric entries of which **8171 lie in the plausible ADC range
(1000–1600 counts)**; the remainder are non-sample artefacts of the export. Over those 8171
samples:

$$\bar x = 1261.88\ \mathrm{LSB},\qquad \hat\sigma_{\mathrm{idle}} = 9.803\ \mathrm{LSB}
\quad\text{(sample standard deviation).} \tag{M103}$$

`idle mic data/filtered_data.xlsx` contains 8170 samples with $\bar x = 1261.88$,
$\hat\sigma = 9.803$ LSB — i.e. the same record.

> **SLOT — measured noise floor.** The values in (M103) are a preliminary read of a single
> channel from a partially malformed export and must be replaced by the analysis track's
> characterisation. The paper needs, per channel:
> `sigma_idle = [MEASURE] LSB` (or dBFS), `A-weighted equivalent input noise = [MEASURE] dB(A) SPL`,
> the acquisition rate at which the idle record was taken, and the idle PSD shape (white
> versus $1/f$).

Two observations that must be resolved before this number is used:

1. $\hat\sigma_{\mathrm{idle}} = 9.80$ LSB is **34 times** the ideal 12-bit quantisation floor
   of 0.289 LSB (M100), i.e. the idle record is 30.6 dB above the converter's own floor.
   The chain is therefore not quantisation-limited; it is limited by microphone self-noise,
   analogue-front-end noise, supply noise, or ADC INL/DNL. Which of those dominates is
   determined by the PSD shape and by a shorted-input measurement.
2. The DC offset of $\approx 1262$ counts and the LSB-valued data are characteristic of a
   **single-ended 12-bit SAR ADC on an analogue microphone**, and are inconsistent with an
   INMP441, which is an $I^2$S digital MEMS microphone delivering 24-bit two's-complement
   samples with no DC bias and no host ADC involvement.
   [MEASURE / resolve: which acquisition chain produced this data. The treatment above is
   deliberately parametric in $Q$ and $V_{\mathrm{FS}}$ so it holds for either.]

If the part is confirmed as an INMP441, the relevant datasheet figures are its SNR
(specified relative to 94 dB SPL) and its acoustic overload point; the equivalent input noise
in dB(A) SPL is then $94 - \mathrm{SNR}_{\mathrm{spec}}$, and (M103) should be replaced by a
digital-domain floor in dBFS. Both routes feed the same downstream quantity, below.

### 10.4 From electrical SNR to TDOA variance

The link the paper needs is (M83). For a flat in-band source spectrum and in-band SNR $\Gamma$
(referenced to the measured floor via (M99)), (M83) evaluates in closed form to

$$\boxed{\ \sigma_\tau^{2}\ \ge\
\left[\frac{8\pi^{2}}{3}\,T_{\mathrm{obs}}\,\big(f_2^{3}-f_1^{3}\big)\,
\frac{\Gamma^{2}}{1+2\Gamma}\right]^{-1} \ } \tag{M104}$$

and combining with the array GDOP law (M40) gives the end-to-end relation from a measured
noise floor to an azimuth accuracy:

$$\boxed{\ \sigma_\theta \ \ge\ \frac{c}{\sqrt{4.5}\,R}
\left[\frac{8\pi^{2}}{3}\,T_{\mathrm{obs}}\,\big(f_2^{3}-f_1^{3}\big)\,
\frac{\Gamma^{2}}{1+2\Gamma}\right]^{-1/2}\ } \tag{M105}$$

[DERIVED from (M83) and (M40); consistent with the direct array CRB (M82) to within a factor
1.22, as tabulated in Section 8.3.] In the high-SNR limit $\Gamma\gg 1$ the bracket scales as
$\Gamma/2$, so $\sigma_\theta\propto \Gamma^{-1/2}$: **every 6 dB of measured SNR improvement
halves the azimuth standard deviation**, until the interpolation floor (M28) is reached.

Equations (M104)–(M105) are the intended use of the idle measurement: measure
$\hat\sigma_{\mathrm{idle}}$, form $\Gamma$ from (M99) for each real clip, and predict the
azimuth accuracy that clip can support — then compare against the accuracy actually obtained
by `real_data.py`. That comparison is the honest sim-to-real bridge for Section 6.4 of the
paper.

---

## 11. Open mathematical issues

These are the points I could not resolve, with the data that would resolve each.

1. **The band-limiting result changes the paper's baseline.** Restricting the PHAT weight to
   the source band improves per-frame azimuth RMSE at 10 dB from 4.14$^\circ$ to 0.31$^\circ$
   (Section 2.4) and restores the theoretical $N^{-1/2}$ snapshot law (Section 4.3). Every
   number in `benchmark_run.log` and `ablation_run.log` was produced with the full-band
   version. I have not re-run the harness, and I should not: the decision on whether to
   re-baseline, or to report the current numbers plus this analysis as a limitation, belongs
   to the writing track and to the author. **Resolved by:** an explicit decision, and if
   re-baselining, a full re-run of `doa_benchmark.py`, `reverb_robustness.py` and
   `ablation.py`.
   *Caveat that must accompany either choice:* part of the improvement is an artefact of the
   simulation's full-band white-noise model (assumption A5) and will be smaller on hardware.

2. **The accumulation sweep stops before the floor.** The futility analysis (M67) puts the
   knee at $T\approx 64$–107 frames, but `ablation.py` sweeps only to $T=32$, and each
   reverberant point uses 42 samples (10.9 % relative standard error). The logged curves are
   therefore consistent with (M62) but do not establish the floor; only the direct bias
   measurement (M63) does. **Resolved by:** re-running `temporal_reverb` with
   $T\in\{1,2,4,\dots,128\}$ and $\ge 30$ trials per angle. This is the single most valuable
   additional simulation for the paper's headline claim.

3. **The reverberation bias is source-realisation dependent, and the model does not capture
   that.** Equation (M61) treats $b$ as a fixed constant, but in `temporal_reverb` the RIR is
   fixed while the source waveform is redrawn each frame, so the multipath interference
   pattern changes frame to frame. Part of what (M62) calls "bias" therefore does average out,
   and part of what it calls "noise" is reverberation. The direct measurement (M63) gives the
   correct asymptotic $b$ for this stochastic-source case, but the decomposition of the
   reverberant error into RIR-determined and realisation-determined parts has not been done.
   **Resolved by:** repeating the bias measurement with a *fixed* source waveform (varying only
   the additive noise), which isolates the pure RIR-induced bias, and comparing.

4. **The prediction of $\mathrm{RMSE}(T=32)$ from $(b,\sigma_1)$ overshoots at high RT60** by
   2.2 and 3.9 standard errors at RT60 = 0.30 and 0.60 s (Section 6.4). The likely cause is
   that $\sigma_1$ is a linear standard deviation inflated by outliers, while the circular
   mean suppresses those outliers. **Resolved by:** replacing $\sigma_1$ with the circular
   dispersion $\sqrt{(1-\bar\rho_2)/(2\bar\rho_1^{2})}$ from (M59), estimated from the same
   frames, and re-checking. I did not do this because it requires re-running the bias
   measurement with the resultant lengths retained.

5. **No analytic model of $b(\theta,\mathrm{RT}_{60})$.** The measured biases are strongly
   azimuth-dependent (e.g. $+3.40^\circ$ at $\theta=+40^\circ$ versus $-0.08^\circ$ at
   $-120^\circ$ at RT60 = 0.15 s) and the paper currently has no theory for that structure.
   A single-dominant-early-reflection model (direct path plus one image source at relative
   amplitude $\alpha$ and delay $\Delta$) predicts a GCC peak pull of the form
   $\arctan\!\big(\alpha\sin\varphi/(1+\alpha\cos\varphi)\big)$, which could be fitted, but I
   have not derived the mapping from the room geometry in `build_rirs` to $(\alpha,\Delta)$
   per azimuth. **Resolved by:** extracting the first two arrivals from each RIR in
   `build_rirs` and testing the two-path prediction against the measured $b$.

6. **The FLOP model cannot predict the SRP and MUSIC wall-clock times** (Section 7.4). This is
   not resolvable analytically — it is interpreter overhead — and the correct response is the
   labelling change recommended in Section 7.4, not a better model. If the paper wants
   defensible compute ratios it needs either operation counts (which are given in Section 7)
   or measurements from vectorised/C implementations of all four methods.
   **Resolved by:** either dropping the wall-clock ratios in favour of the FLOP table, or
   re-measuring with all four methods implemented at comparable optimisation level.

7. **Aperture ambiguity in the source data.** The triangular array has $R = 5$ cm and
   $D = 8.66$ cm; the quadrant CSVs encode a 5 cm two-microphone baseline (M86). Whether the
   physical board has a 5 cm circum-radius, a 5 cm inter-microphone spacing, or a 5 cm
   two-microphone baseline changes $\sigma_\theta$ by up to $\sqrt3$ through (M40).
   **Resolved by:** measured microphone coordinates from the PCB.

8. **Acquisition rate unknown.** Section 3 shows the requirement is
   $f_s\gtrsim 8$ kHz and preferably $\ge 16$ kHz. If the hardware really samples near 1 kHz,
   none of the simulated performance transfers and the array is effectively blind at integer
   lag resolution. **Resolved by:** a firmware-side measurement of the per-channel sample rate
   and of the inter-channel sampling skew (assumption A8).

9. **Source range for the `Triple Mic Samples` campaign is unknown.** If the header labels
   such as `(0,15)` are centimetres, (M11) predicts a systematic near-field azimuth bias of up
   to $4.8^\circ$, and the far-field model of Sections 1–8 does not apply to that data.
   **Resolved by:** the measurement protocol (units and coordinate origin) for those clips.

10. **Elevation is unmodelled.** Assumption A2 is stated but its cost is not quantified. A
    source at elevation $\psi$ reduces the effective aperture to $R\cos\psi$, which by (M40)
    inflates $\sigma_\theta$ by $\sec\psi$ ($+15$ % at $\psi=30^\circ$, $+100$ % at
    $60^\circ$). I have not verified this against the simulation because `simulate()` is
    strictly two-dimensional. **Resolved by:** a 3-D extension of `steering_delays`, or a
    stated protocol constraint that the loudspeaker is at array height.

11. **Sensor gain and phase mismatch (A7) is an unmeasured bias term.** By the argument of
    Section 6.4 it enters (M62) as part of $b$ and is therefore *not* removable by
    accumulation — potentially a floor comparable to the reverberation floor. It has not been
    modelled. **Resolved by:** a free-field or coupler measurement of relative channel gain
    and phase across 300–3400 Hz, which converts directly into a per-pair delay bias
    $\Delta\tau_{ij}$ and hence into a $b$ via (M32).

---

*End of `paper/math_model.md`. Equations (M1)–(M105).*
