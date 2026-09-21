# The reverberation bias floor of a minimal three-microphone direction-of-arrival sensor

**Aneesh Arnav Chikkala**

*Target venue:* Acta Acustica (EAA / EDP Sciences), Technical & Applied Article.
*Section:* Audio Signal Processing and Transducers.
*Candidate topical issue:* Benchmarking Acoustics.

> **Draft status.** Sections 1 to 6 are drafted here. Sections 7 and 8, the appendix and the back
> matter are outlined but not yet written. Slot conventions: `[MEASURE: ...]` is a board or
> protocol value that has not been measured; `[VERIFY: ...]` is a citation detail to confirm at
> the publisher. There are no `[VAL: ...]` slots left in Sections 1 to 5 — every simulated number
> is final and traceable to a named log. Section 6 carries `[MEASURE]` slots only, because the
> measurements it specifies have not yet been performed; this is stated in the text rather than
> hidden.
>
> Provenance for every number: `paper/rebaseline_results.md` (simulation, post-correction),
> `paper/data_results.md` (measured hardware data), `paper/math_model.md` (equations M1–M105).
> Logs: `validation/benchmark_run.log`, `validation/reverb_run.log`, `validation/ablation_run.log`,
> `validation/rebaseline_checks_ABC.log`, `validation/rebaseline_checks_D.log`,
> `validation/realdata_run.log`.

---

## Abstract

Real-time sound-source localization is increasingly wanted on small, low-power, low-cost edge
devices — assistive hearing systems, wearable interfaces, robots and distributed sensors — where
direction-of-arrival (DoA) estimation must run under severe constraints on computation, memory and
energy. We ask how far a deliberately minimal system can go: three microphones on a 5 cm aperture
driven by a single microcontroller, running only generalized cross-correlation with phase transform
(GCC-PHAT) time-delay estimation and a least-squares azimuth solve. We characterize that operating
point exhaustively in simulation, with standard errors on every quantity, and we report what the
accuracy is actually limited by.

The answer is not the estimator. Once the PHAT weight is restricted to the band the source
occupies — a one-line change that we show is worth a factor of 3 to 13 depending on acquisition
bandwidth — the per-frame azimuth RMSE in free field at 10 dB SNR is 0.301 ± 0.006°, within 1.39×
of the precision attainable given the correlation interpolation grid, at 4.23 MFLOP per frame. In
any reverberant room the accuracy is instead set by a **deterministic multipath bias floor** of
1.481 ± 0.115°, 1.978 ± 0.092° and 2.557 ± 0.087° at RT60 = 0.15, 0.30 and 0.60 s. We measure that
floor two independent ways — a direct per-azimuth circular mean over 3840 frames, and a
two-parameter fit of MSE(T) = b² + σ₁²/T to accumulation curves extended to T = 128 — and they
agree to three decimal places. The floor is monotone in RT60, is reached in under 250 ms of
accumulation, and is the same for every correlation-based estimator we tested.

We report four negative results rather than suppressing them. A per-frame confidence gate and
peak-to-sidelobe weighting reduce the error by 0.02–0.09°, which is statistically significant over
540 matched frames but is 1–3 % of the error; with three microphones the pairwise system has
redundancy exactly one, which permits fault detection but never fault identification, so the
decision layer cannot pay for itself. Confidence weighting of the temporal accumulator differs from
a plain circular mean by 0.0001–0.006° and changes sign with the room, so the accumulator
simplifies to an unweighted circular mean costing five operations per frame. Temporal accumulation
itself, which reduces error as 1/√T exactly in free field (0.308° to 0.027° over 128 frames), buys
only 5.8–19.6 % in rooms because the bias floor is reached by T = 4. And incoherent wideband MUSIC,
which appears far more accurate than GCC-PHAT when the two are compared with mismatched front-end
bands, is in a fair comparison worse in free field and collapses in reverberation, with RMSE
reaching 28–36° above RT60 = 0.3 s.

We give the design envelope this implies: azimuth error scales as 1/R in aperture (log-log slope
−0.946 ± 0.032) and as N^(−1/2) in snapshot length (−0.461 ± 0.020); a sampling-rate inequality
that a 5 cm array must satisfy for the delay to be observable at all; and an implementation
recommendation — a native-length inverse FFT with parabolic peak refinement is 5.1× cheaper by the
FLOP model, uses 8× less memory, and is more accurate above 20 dB. Finally, we characterize a
physical acquisition chain against these predictions and report, from measurement, that it cannot
presently support a DoA claim: its sample rate is 999.988 Hz against a requirement in the tens of
kilohertz, so the entire azimuth range collapses into one correlation lag bin. We specify the
acquisition a valid campaign requires. The contribution is a quantified, reproducible design
envelope for minimal DoA sensors, and the identification of reverberation bias — not noise, not
compute, and not the choice of estimator — as the binding constraint.

**Keywords:** sound source localization; direction of arrival; GCC-PHAT; microphone array;
embedded systems; reverberation; benchmarking.

---

## 1. Introduction

Knowing where a sound came from is a small piece of information that unlocks a disproportionate
amount of behaviour in a device. A hearing aid that knows the azimuth of the talker can steer a
beam toward them. A voice interface that knows the direction of a wake word can turn a camera, or
suppress the other three people in the room. A mobile robot that knows the bearing of a call can
orient before it has understood the words. A distributed acoustic sensor that reports a bearing
rather than a waveform sends a few bytes instead of a stream, which is often the difference between
a device that runs for a year on a battery and one that does not. In each case the direction
estimate is not the product; it is a cheap input to something else. That framing sets the
engineering problem: the localizer has to be small, inexpensive and modest in its use of
computation, memory and energy, because it is competing for those resources with the application it
serves.

The acoustics and array-processing literature has, by contrast, largely optimized for accuracy.
Steered-response power with phase transform (SRP-PHAT) and subspace methods such as MUSIC both
reach high angular accuracy in favourable conditions, and both are robust in ways that simple
time-delay estimation is not, but they buy that with a grid search or an eigendecomposition per
frame, and they generally assume an array with enough elements to give the estimator some
redundancy to work with [argentieri2015survey]. Larger arrays are also physically larger, which is
a problem when the device is a hearing aid, an earbud or a sensor node the size of a matchbox, and
they are more expensive, which is a problem when the device is meant to be deployed by the hundred.

There is a real design point below all of this that the literature has not characterized cleanly:
three microphones, an aperture of a few centimetres, and a general-purpose microcontroller costing
a few dollars. Three is the smallest number of elements that resolves azimuth over the full circle
without a front-back ambiguity, so it is the natural floor for a planar azimuth sensor. Everything
about that configuration is constrained. The aperture bounds how precisely a time delay converts
into an angle. The microcontroller bounds how much arithmetic can happen between frames. Three
elements give exactly three microphone pairs and two independent time-delay differences, which is
the minimum needed to solve for a two-dimensional direction vector and leaves nothing over. The
practical question is not whether such a device works — it plainly does, at some accuracy — but
what accuracy is achievable, what actually limits it, and which knob is worth turning.

This paper answers those three questions for a specific, buildable configuration. We state the
main finding up front, because it is the point of the paper and because it is not the answer we
expected.

**The accuracy of a minimal array in a room is set by deterministic reverberation bias, not by
noise, not by compute, and not by the choice of estimator.** Once the front end is implemented
correctly, a single 42.7 ms frame gives an azimuth RMSE of 0.301 ± 0.006° in free field at 10 dB
SNR. That is within 1.39× of the precision attainable given the correlation interpolation grid, and
it is already finer than any plausible hardware tolerance: a one-sample inter-channel clock skew is
worth about 4°, and near-field wavefront curvature alone contributes 0.72° of bias at one metre.
There is almost no stochastic error left to remove. What remains, in any real room, is a bias
contributed by early reflections whose geometry is fixed during a measurement. We measure that
floor at 1.481 ± 0.115°, 1.978 ± 0.092° and 2.557 ± 0.087° at RT60 = 0.15, 0.30 and 0.60 s, by two
independent methods that agree to three decimal places. It is monotone in RT60, it is reached
within four frames, and it is identical across the three correlation-based estimators we tested.
No amount of accumulation, gating, weighting or subspace processing crosses it.

The route to that finding ran through an implementation defect, and reporting it is part of the
contribution. Our original harness applied the PHAT weight across the full 0–24 kHz Nyquist band
while the source occupied 300–3400 Hz. PHAT normalizes every bin to unit magnitude, so bins
containing nothing but sensor noise received the same influence as bins containing the source, and
their essentially random phase was promoted to full weight. At 10 dB SNR, 80.9 % of the bins left at
unit weight were out-of-band noise. Restricting the weight to the source band reduces per-frame
RMSE from 4.105 ± 0.142° to 0.307 ± 0.011°. We are careful about how much of that factor is real:
part of it is an artefact of a simulation that adds white noise across the whole Nyquist band
against a 3.1 kHz source. Repeating the comparison with the additive noise band-limited to a
realistic 8 kHz acquisition chain, the improvement is 7.0×; with a 4 kHz chain, 3.2×. The corrected
estimator's absolute accuracy, 0.301–0.327° across every acquisition bandwidth tested, does not
depend on the noise model and is the number we quote. We report this because a thirteen-fold error
contributed by a one-line weighting choice is more consequential than any algorithmic difference
measured in this paper, and because the same defect is easy to reproduce in any implementation that
follows the textbook definition of PHAT literally.

Four negative results follow, and we report each as a result.

1. **Per-frame confidence gating and weighting do not pay for themselves at M = 3.** Over 540
   matched frames the decision layer reduces mean absolute error by 0.02–0.09°, which is 3 to 7
   standard errors and therefore real, but amounts to 1–3 % of an error of 2.5–3.2°. The reason is
   structural. The three pairwise TDOAs sum to zero around the triangle, so the system has
   redundancy exactly one, its left null space is spanned by (1, −1, 1)/√3, and the only available
   test statistic is the closure error. A bias on any one pair shifts that statistic by exactly
   ±δ/√3, so the three fault hypotheses are indistinguishable up to sign. This is the classical
   detection-versus-exclusion condition: with P = p + 1 measurements a fault can be detected but
   never identified. Empirically the peak-to-sidelobe ratio correlates with frame error at Spearman
   −0.13 in free field and −0.04 at RT60 = 0.3 s, so it carries almost no usable information.
2. **Confidence weighting of the temporal accumulator is a tie.** Weighted and plain circular means
   differ by 0.0001–0.006°, and the sign of the difference changes with the room. The accumulator
   simplifies to an unweighted circular mean at five floating-point operations per frame, with no
   confidence to compute or store.
3. **Temporal accumulation is largely unnecessary in free field and largely ineffective in rooms.**
   It works exactly as theory predicts where the error is stochastic — 0.308° to 0.027° over 128
   frames in free field, a factor 11.4, with a fitted bias of 0.000 ± 0.007° — but going from 43 ms
   to 5.5 s of latency in a reverberant room buys 5.8 %, 15.9 % and 19.6 % at the three RT60 values.
   Accumulation is over by T = 4.
4. **MUSIC's apparent advantage was a comparison artefact, and its real behaviour in reverberation
   is a failure.** With both front ends band-limited, GCC-PHAT (0.301°) is more accurate than MUSIC
   (0.697°) in free field at 10 dB, and above RT60 = 0.3 s MUSIC's RMSE reaches 28–36° while its
   median stays near 3.4° — gross wrap and front-back failures in a large minority of frames.

The contributions are deliberately modest and, we believe, all defensible:

1. **A quantified design envelope** for minimal azimuth sensors: accuracy against SNR,
   reverberation time, aperture, snapshot length, accumulated frames and per-frame compute,
   produced by one reproducible harness with a fixed seed, with a standard error on every number.
2. **The reverberation bias floor**, measured two independent ways that agree to three decimals,
   established as the binding constraint at this design point, together with the accuracy-latency
   law and the futility knee that tell a designer exactly how much latency is worth budgeting.
3. **The four negative results above**, each bounded quantitatively rather than asserted, and the
   rank argument that explains the first of them.
4. **Two implementation results with direct firmware consequences**: band-limiting the PHAT weight,
   and replacing the eightfold zero-padded inverse FFT with a native-length transform and parabolic
   peak refinement, which is 5.1× cheaper by the FLOP model, uses 8× less memory, and is *more*
   accurate above 20 dB.
5. **A measured characterization of a physical acquisition chain** against these requirements,
   including the honest finding that the chain as built cannot support a DoA claim, and a
   specification of the acquisition that would.

We are explicit about what this paper is not. We do not propose a new estimator, and we claim no
theoretical result about time-delay estimation; GCC-PHAT, SRP-PHAT, MUSIC and the image-source room
model are all used as published. The contribution is applied: a characterization of a constrained
operating point, and honest boundaries around it.

The rest of the paper is organized as follows. Section 2 reviews the estimators and positions the
work. Section 3 describes the hardware platform and the measured characterization of its
acquisition chain. Section 4 gives the signal model, the estimator, the accumulator and the
complexity analysis. Section 5 reports the simulation study. Section 6 reports the hardware
measurement protocol, the adequacy of the recordings in hand, and what they do and do not
establish. Section 7 discusses limitations and Section 8 concludes.

---

## 2. Background and related work

### 2.1 Time-delay estimation and GCC-PHAT

The cheapest route to a direction estimate is to measure the time difference of arrival (TDOA)
between microphone pairs and invert the geometry. Knapp and Carter formalized the generalized
cross-correlation family for this purpose and introduced the weighting functions that distinguish
its members [knapp1976gcc]. The phase transform (PHAT) weighting normalizes each frequency bin of
the cross-spectrum to unit magnitude before the inverse transform, so the estimate depends on
cross-spectral phase alone. This discards the amplitude information that a maximum-likelihood
weighting would use, which is a loss under additive noise, but it makes the correlation peak far
sharper and far less sensitive to the spectral colouration that a room and a source impose. In
practice PHAT is the weighting that survives contact with real rooms, and it is the front end of
essentially every lightweight localizer, including ours.

That normalization carries a hazard which Section 5.1 shows is the largest single effect in this
paper. Unit-magnitude normalization is applied to every bin, including bins in which there is no
source energy at all. In those bins the phase is essentially random, and PHAT promotes it to the
same influence as a bin carrying the signal. The standard formulation is usually written without an
explicit band restriction, and the hazard is proportional to the ratio of the transform bandwidth
to the source bandwidth — which on a 48 kHz system with a speech-band source is a factor of seven.
We have not found this stated quantitatively in the literature, and we suspect it is a common silent
error.

The classical treatment of what limits TDOA accuracy is Carter's review of coherence and time delay
estimation [carter1987coherence]. Two of its results matter directly. First, the variance of a
delay estimate from independent observations falls inversely with the number of independent
observations, which is the theoretical statement behind the 1/√T behaviour we measure in
Section 5.6. Second, the achievable accuracy is governed by the magnitude-squared coherence between
channels; when coherence is degraded the estimator does not merely become noisier, it becomes
biased in a way that more data does not remove. Reverberation is precisely a coherence-destroying
mechanism, and this is the theoretical home of the bias floor that is this paper's subject.

Brandstein and Silverman made the practical version of the same point: in rooms it is reverberation
and not additive noise that breaks TDOA-based localization, because a strong early reflection can
produce a cross-correlation peak taller than the direct-path peak [brandstein1997robust]. Their
response — score each pair's correlation for reliability and treat unreliable pairs differently —
is the direct ancestor of the confidence gate and weighting we describe in Section 4.4. Our
contribution on that point is not the idea but a measurement of how much it is worth on an array
with three elements, and a rank argument for why the answer is: almost nothing.

### 2.2 Steered-response power

SRP-PHAT, introduced in DiBiase's thesis [dibiase2000srpphat] and given its widely-read exposition
as a chapter in Brandstein and Ward's edited volume [dibiase2001chapter, brandsteinward2001],
avoids committing to a per-pair delay estimate. It sums the PHAT-weighted cross-correlation of every
pair, each evaluated at the delay a candidate direction would produce, and searches the resulting
spatial power map for its maximum. Because a spurious peak in one pair rarely aligns with spurious
peaks in the others at the same candidate direction, the sum is more robust to reverberation than
independent per-pair peak-picking. The cost is the grid search, and the grid resolution bounds the
estimate's resolution.

Two points about SRP-PHAT that Section 5.7 establishes and that are worth flagging here. It shares
the identical PHAT-weighted pairwise correlations with the pairwise estimator, so a FLOP model puts
it at 1.006× the cost of GCC-PHAT, not the several-fold factor that a naive implementation
measures. And on three microphones the steered power sum has only three cross-correlations to
combine, so the outlier suppression that makes it strong on larger arrays has little to work with.

### 2.3 Subspace methods

MUSIC [schmidt1986music] estimates the spatial covariance matrix of the array, splits its
eigenvectors into signal and noise subspaces, and reports the directions whose steering vectors are
most nearly orthogonal to the noise subspace. Under its assumptions — enough snapshots to estimate
the covariance, a known array manifold, and a source count known in advance — it resolves more
finely than the aperture would suggest for a delay-domain estimator. It is also the baseline whose
assumptions are hardest to satisfy on a cheap board: the array manifold depends on microphone
positions known to a fraction of a wavelength and on channels matched in gain and phase, neither of
which a low-cost build guarantees. Section 5.3 reports that at M = 3 its narrow-band covariance
model does not survive strong early reflections. General treatments of both the delay-domain and
subspace families are available in the standard array-processing references
[benesty2008microphone, brandsteinward2001, vantrees2002optimum].

### 2.4 Small and embedded localizers

The closest prior work in spirit is the ManyEars and ODAS line, of which Grondin and Michaud's
account of lightweight and optimized localization and tracking is the clearest statement
[grondin2019lightweight]. That work asks how to make sound-source localization cheap enough to run
continuously on a robot, and answers with careful engineering of the search and the tracking stage.
The important contrast is the array: it operates on eight microphones, and much of its robustness
comes from having enough elements that outliers can be outvoted. We ask a strictly harder version
of the question — what remains when the array has three elements and no redundancy at all — and our
first negative result is, in effect, a measurement of what is lost when the element count drops
that far.

Argentieri, Danès and Souères survey localization in robotics from binaural methods through array
processing and name the constraints that define our design point: embeddability, real-time
operation, and degradation under noise and reverberation [argentieri2015survey]. On the application
side, direction estimation for hearing devices is an established motivation for small-aperture work
[farmani2017hearingaid; VERIFY: publication year, journal volume and pages], and the broader
practice of running signal-processing workloads on microcontroller-class hardware is established
enough to make a dollar-class DoA sensor a reasonable design target [warden2019tinyml].

### 2.5 Temporal integration and tracking

Averaging or tracking direction estimates over time is not new, and we do not present it as new.
Valin, Michaud and Rouat combine beamforming with particle filtering to follow multiple moving
sources [valin2007particle], and recursive Bayesian filters of that kind are the standard tool when
sources move, appear and disappear. Those methods maintain a state distribution, need a motion
model, and cost memory and arithmetic proportional to the number of particles or the state
dimension.

Our accumulator is the minimal member of that family: two scalar accumulators holding the sums of
the sine and cosine of the per-frame azimuths, and an arctangent. It has no motion model, assumes
the source is stationary over the window, and uses O(1) memory regardless of T. We claim no
advantage over particle or Kalman tracking in generality. What we contribute is a measurement of
where this family stops helping on a minimal array, which turns out to be after about four frames
in any real room — a result that applies to the more elaborate members of the family as well, since
none of them can average away a bias that is identical in every frame.

### 2.6 Reverberation modelling

Our reverberant simulations use the image-source method of Allen and Berkley [allen1979image] in
the uniform-wall formulation, with the Sabine relation converting a target reverberation time into
a wall reflection coefficient [kuttruff_roomacoustics]. Our implementation follows the structure of
the widely-used reference implementation described by Habets [habets2006rir], so that the room model
is the standard one rather than an ad hoc construction. Lowering the reverberation floor we report
would require exploiting the precedence effect — gating on the direct sound before reflections
arrive rather than averaging over them — and we point to that literature in the discussion rather
than attempting it here [litovsky1999precedence].

### 2.7 Scope: what this paper claims and does not claim

We state this plainly because it determines how the rest should be read. We do not introduce a new
estimator, a new weighting function, or a new statistical result about time-delay estimation. Every
algorithm we run is taken from the references above and used as published. What we contribute is
applied and empirical:

- a characterization of a specific, extreme operating point — three microphones, centimetre-class
  aperture, microcontroller-class compute — including the point at which each resource stops paying;
- the identification and two-way measurement of the reverberation bias floor as the binding
  constraint at that operating point;
- four quantitative negative results, which are design recommendations rather than theorems;
- two implementation findings with direct firmware consequences;
- a documented platform and a shared harness that make all of the above reproducible.

Framed that way the work is a technical and applied characterization study, and we intend it to be
read and judged as one.

---

## 3. System and hardware platform

### 3.1 Overview

The device is a single custom printed circuit board carrying three microphones, their acquisition
path, and an ESP32-S3 module [espressif_esp32s3]. It captures three synchronized channels, computes
an azimuth estimate per frame, accumulates estimates over a short window, and emits a bearing.
There is no host computer in the loop.

This section serves two purposes, and we keep them separate. Sections 3.2 to 3.5 specify the
platform the simulation study characterizes. Section 3.6 reports what we measured on the physical
acquisition chain that exists, which is a different and more limited thing. We do not conflate the
two, because they disagree.

### 3.2 Array geometry

The three microphones sit at the vertices of an equilateral triangle in the horizontal plane. A
triangle is the smallest planar arrangement that resolves azimuth over the full 360° without a
front-back ambiguity; a three-element *linear* array of the same footprint resolves only a
half-plane. Placing the microphones on a circle also makes the geometry isotropic. Section 5.5
verifies that the azimuth error standard deviation is in fact direction-independent for this
geometry under uniform weights, which is what the analysis predicts: for the equilateral array
AᵀA = 4.5 R² I exactly.

The nominal configuration is a circum-radius R = 5 cm, giving microphone coordinates (0, 5),
(−4.33, −2.5) and (4.33, −2.5) cm and an inter-microphone spacing d = R√3 = 8.66 cm. The
corresponding maximum physical TDOA between a pair is d/c = 252.5 µs at c = 343 m/s, which is the
bound the feasibility gate of Section 4.4 enforces.

Geometry must be measured on the assembled board rather than taken from the layout file: the
quantity that matters is the acoustic port separation, it enters the azimuth solution linearly, and
a one-millimetre error on a 50 mm baseline is a two-percent scale error on every delay-to-angle
conversion. We flag one ambiguity in our own documentation that a reader should not inherit: the
phrase "5 cm aperture" is ambiguous between the circum-radius, which gives 8.66 cm spacing and a
252.5 µs maximum delay, and the spacing itself, which gives 145.8 µs. We carry the circum-radius
reading throughout, and the assembled board requires
`[MEASURE: the three microphone coordinates in the board frame, by caliper, and which of the two
readings the built array corresponds to]`.

One useful robustness property falls out of the geometry. The three-pair least-squares azimuth is
*exactly* invariant to errors in the assumed speed of sound: c enters only as a scale factor on the
solved direction vector, and scaling cancels in the four-quadrant arctangent. A ±10 °C temperature
uncertainty, which moves c by about 2 %, costs nothing in azimuth. This does not extend to the
near-field two-dimensional fix of the appendix, where range is recovered and the scale matters.

(Fig. `fig_geometry.png`.)

### 3.3 Acquisition requirements

The sample rate is not a free parameter, and because Section 3.6 reports a chain that violates the
requirement badly, we state it as a design inequality rather than a preference.

The largest TDOA any real source can produce on a pair is d/c, so that is the entire observable
range of the measurement. If the sample period approaches or exceeds d/c, every admissible source
direction maps to the same integer lag and the delay is not merely noisy but *unobservable*. Writing
I for the correlation interpolation factor and ε_q for the target angular quantization in radians,
the requirement is

  I · f_s ≥ c / (√54 · R · ε_q),

together with f_s ≥ 2 f₂ for a source with upper band edge f₂ and an anti-alias filter that actually
enforces it. For the nominal geometry, sub-degree quantization needs I·f_s of order 10⁵ s⁻¹;
practically, f_s ≳ 8 kHz with I ≥ 8, and 16–48 kHz is comfortable. The simulation study uses
f_s = 48 kHz and N = 2048 samples (42.7 ms).

Interpolation is not a substitute for sample rate. It recovers the sub-sample position of a peak
that the sampling has already resolved; it cannot recover directional information that was never
captured. Section 6.2 gives the arithmetic for the chain we measured, where the entire azimuth
range spans a quarter of one lag bin.

Aliasing deserves separate mention because it corrupts delay estimation far more severely than it
corrupts spectral estimation, and the distinction is not obvious. A component folded from f₀ to an
alias f_a retains the phase of its original frequency, so it enters the cross-spectrum with an
apparent group delay inflated by the ratio f₀/f_a. For a 20 kHz component folded by a 1 kHz sampler,
that inflation reaches 31.7 rad — five complete phase wraps — across the array's maximum delay. An
anti-alias filter is therefore mandatory for TDOA work in a way that it is not for level
measurement.

### 3.4 Firmware pipeline

The real-time pipeline is: capture the frame into a double buffer; remove the DC offset and apply a
band-limiting FIR filter over the source band; compute the band-limited PHAT-weighted
cross-correlation for each of the three pairs; take each pair's peak lag with parabolic refinement;
solve the least-squares problem for the direction vector; and fold the resulting azimuth into the
running circular mean. Only the accumulator state persists between frames, so the temporal stage's
memory cost does not grow with the accumulation length.

Two results from Sections 5.1 and 5.7 are firmware requirements rather than suggestions. The
band-limiting FIR is not sufficient on its own — the PHAT weight must *also* be restricted to the
source band, for two separately measured reasons given in Section 5.1. And the correlation should
use a native-length inverse FFT with parabolic peak refinement rather than an eightfold zero-padded
transform: 5.1× cheaper by the FLOP model, 16 kB rather than 128 kB of correlation buffer per pair,
and more accurate above 20 dB.

On filter choice we have a measured recommendation. Four candidate low-pass designs were
re-implemented as written and run on real idle and excitation recordings (Section 3.6;
Fig. `fig_real_filter_comparison.png`). Three of the four are linear phase, so the delay they add is
common to all channels and cancels in every pairwise difference. The fourth, an un-shifted inverse
DFT of a rectangular mask, is not linear phase: its group delay varies by 285 samples over
0–100 Hz and its stopband attenuation is −2.3 dB. A filter with channel-common but
frequency-dependent group delay smears the cross-correlation peak and directly degrades TDOA, so
this design must not be used. We recommend the 51-tap Kaiser design: linear phase, 87 dB stopband,
and the largest measured noise reduction of the four at 5.22 dB on real idle data.

The ESP32-S3 has two cores and the work splits across them: one owns acquisition and the DMA-fed
ring buffer, the other the transform-domain work. Measured resource use is
`[MEASURE: peak SRAM footprint, kB; sustained CPU load, percent]`.

### 3.5 Cost

`[MEASURE: bill of materials table — line items, quantities, unit costs]`

The complete bill of materials comes to approximately $`[MEASURE: total BOM cost]` in single-unit
quantities. We give this because the design point is defined as much by its cost as by its element
count. We deliberately do not make quantitative accuracy-per-dollar comparisons against specific
commercial products, because we have not measured those products under our protocol.

### 3.6 Measured characterization of the acquisition chain

We characterized the physical acquisition chain that exists, using 105 distinct single-channel
recordings and three 60 s idle recordings. The results are reported here because several of them
are useful platform measurements, and because one of them determines what Section 6 can claim.
Script: `validation/analyze_real.py`; log: `validation/realdata_run.log`.

**The acquisition chain is not the one the array specification describes.** Every stored value is
even, and the greatest common divisor of successive differences is 2, indicating a 12-bit
conversion left-shifted into a 13-bit field. The samples are unsigned on a 4096-code grid with a DC
pedestal at 1266.5 codes and hard analogue rails at 42 and 2523 codes. This is an analogue capsule
digitized by the microcontroller's internal successive-approximation converter, and it is
inconsistent with the digital I²S MEMS part the array was specified around, which would deliver a
signed, zero-mean, 24-bit stream with no pedestal. We therefore report all levels in ADC codes and
make no comparison against any microphone datasheet: without a sensitivity in mV/Pa and an acoustic
reference level, a datasheet comparison would not be meaningful. Confirming the part actually fitted
is an open item: `[MEASURE: the microphone part number on the assembled board, and which signal path
each dataset was recorded through]`.

**Sample rate: 999.988 Hz.** This is measured, not assumed, by two independent methods agreeing to
9 ppm. The decisive one exploits aliasing rather than the recorded timestamps. Writing the true
sampling interval as T = (1 + δ)/1000 s, the alias of an excitation at f₀ falls at f_alias = δ·f₀,
so the observed spectral line must be *proportional* to the excitation frequency under one shared
δ. Across 21 sine recordings spanning 5, 10, 15 and 20 kHz and seven distances, δ = 11.44 ± 0.89
ppm; a one-parameter global scan over all 84 recordings gives 12.20 ppm with a scan peak-to-median
ratio of 16.3. Every excitation in the campaign is therefore between two and forty times above
Nyquist and appears only as a sub-hertz folded image; a nominal "5 kHz" recording is a 0.061 Hz
clipped square wave. (Figs. `fig_real_timebase.png`, `fig_real_alias_demo.png`.)

**The logged time column is a host artefact.** Its inter-sample interval scatters with 279 µs RMS,
which at 5 kHz would correspond to 8.8 rad of phase error per sample and would destroy the alias
line entirely — yet that line stays coherent over 30 s. The conversion loop is uniformly clocked;
the column timestamps host reception. Anything derived from those timestamps measures the host link,
not the acquisition.

**Self-noise.** Per-channel RMS is 5.56, 4.03 and 5.59 LSB over 60 s of idle recording, a mean of
5.06 LSB, against an ideal 12-bit quantization floor of 1/√12 = 0.289 LSB. The measured floor is
therefore 17.5× — 24.9 dB — above the converter's own floor. **The analogue front end sets the
noise floor and adding converter bits would buy nothing.** This is a positive design finding. The
noise is not Gaussian: excess kurtosis is 3.58–7.86, a sharp core with heavy tails, which matters
for any threshold or gate. Isolated single-sample dropouts occur at 0.02–0.09 % of samples and are
excluded from the RMS but reported as a real hardware property. With the largest undistorted swing
at 1256 LSB the chain ceiling is 47.9 dB peak SNR.
(Fig. `fig_real_noise_floor.png`.)

**Inter-channel mismatch.** DC pedestals agree across channels to 3.8 LSB, idle noise floors differ
by 2.84 dB, and the total-least-squares broadband gain ratio has a median mismatch of 1.21 dB; the
transitivity closure error across the three pairs is −0.39 dB, so that figure should be read as
order-of-magnitude. GCC-PHAT is insensitive to a flat gain mismatch, which is the useful part of
this result. It is *not* insensitive to phase mismatch, and no phase-mismatch measurement is
possible from any recording in hand, because no file contains a common excitation captured
simultaneously on all three channels with a known time base. Obtaining one is ten minutes of bench
time and is specified in Section 6.4. (Fig. `fig_real_mic_mismatch.png`.)

**Level versus distance and frequency: a negative result.** Recorded level *rises* with distance in
43 of 79 adjacent distance steps, and the pooled slope is +4.8 dB per decade against the −20 dB per
decade that free-field spreading requires; the 1 kHz sine gains 18.7 dB between 50 and 100 cm. No
acoustic mechanism produces this. The drive level was not documented or held constant between runs.
We therefore report no distance response and no inverse-square-law verification, and we note that
the frequency axis of these measurements is the loudspeaker command frequency rather than anything
the microphone resolved. (Fig. `fig_real_level_response.png`.)

Section 6.4 specifies the acquisition that would replace these measurements with usable ones.

### 3.7 Reproducibility

The simulation and evaluation harness is pure NumPy, SciPy and Matplotlib with a fixed seed (7).
Each experiment reseeds from a named tag before it starts, so every experiment is reproducible
independently of the order in which experiments are run; two independent invocations produce
byte-identical numeric output. The same estimator functions are called on measured clips as on
simulated ones; there is no separate real-data implementation that could quietly diverge.
Superseded logs and figures from before the correction of Section 5.1 are retained under
`validation/archive/` and `validation/figs_archive_prerebaseline/`, with a README mapping each to
its replacement, so that the correction is auditable rather than merely asserted. Source code,
firmware, board files and datasets are archived at
`[MEASURE: repository URL and Zenodo DOIs for code, hardware and data]`.

---

## 4. Method

This section states the estimator formally. Sections 4.1 to 4.3 are textbook, Section 4.4 is a
layer we tried and found not to pay for itself, Section 4.5 is the temporal stage, and Section 4.6
accounts for cost. Equation numbers in parentheses refer to the companion derivation in
`paper/math_model.md`.

### 4.1 Signal model

We model a single source in the horizontal plane, far enough from the array that the wavefront
crossing the aperture is planar. Write the M = 3 microphone positions as **p**₁, **p**₂, **p**₃ and
the direction of arrival as the unit vector **u**(θ) pointing from the array toward the source at
azimuth θ. The wavefront reaches microphone m at a delay

  τ_m = −(**p**_m · **u**(θ)) / c.   (M6)

The observed signal at microphone m is the source delayed by τ_m, convolved with the room impulse
response h_m from source to that microphone, plus additive sensor and ambient noise:

  x_m(t) = (h_m * s)(t − τ_m) + n_m(t).   (M9)

For a pair (i, j) the observable is the difference of delays, which depends on direction only
through the baseline vector:

  τ_ij = −((**p**_i − **p**_j) · **u**) / c.   (M12)

A pair does not measure a direction; it measures the projection of the direction onto its own
baseline. With M = 3 there are three pairs, hence three projections, but only two are independent —
the three TDOAs sum to zero around the triangle:

  τ₁₂ + τ₂₃ + τ₃₁ = 0.   (M14)

Two independent projections and two unknown components of a unit vector is an exactly determined
system with no redundancy. This is not a technicality; Section 4.4 shows it is the reason the
confidence layer cannot work.

**Far-field validity.** The plane-wave assumption fails gradually, and the criterion that matters
here is not the Fraunhofer distance. Expanding the spherical wavefront to first order in R/r gives a
frame-invariant azimuth bias

  δθ_nf(r, θ) = −(R / 4r) · cos 3θ,   (M11)

verified against exact spherical propagation to 0.14 % at 1 m. It is three-fold symmetric in
azimuth, reflecting the triangular geometry, and it is 0.72° at r = 1 m for R = 5 cm. The
operational far-field condition r ≥ R/(4ε) for an azimuth error budget ε is about ten times
stricter than the Fraunhofer criterion — 1.43 m for a 0.5° budget, against 0.15 m. Because this bias
is fixed for a given source position it does not average away, so it joins reverberation in the
un-averagable term of Section 4.5. Any measurement campaign at conversational distances must either
respect this bound or correct for it.

### 4.2 Per-frame time-delay estimate

For each frame of N samples and each pair we compute the PHAT-weighted generalized
cross-correlation [knapp1976gcc]: transform both channels, form the cross-spectrum, normalize each
bin to unit magnitude, and inverse-transform to a correlation function of lag whose peak marks the
TDOA:

  R_ij(τ) = ∫ [X_i(f) X_j*(f) / |X_i(f) X_j*(f)|] e^{j2πfτ} df.   (M15)

Three implementation details change the numbers, and the first is the largest single effect
reported in this paper.

**The weight is restricted to the source band.** The normalization in (M15) is applied to every
bin, including bins containing only sensor noise, whose phase is essentially random. We therefore
apply the weight only over the band the source occupies, zeroing the weighted cross-spectrum
outside it:

  Ψ_ij(f) = 0 for f ∉ [f₁, f₂].   (M17)

Section 5.1 quantifies what this is worth. It is not a refinement; without it the estimator is 3 to
13 times worse depending on acquisition bandwidth, and it dominates every algorithmic difference
measured in this paper.

**The normalization is separately regularized.** Dividing each retained bin by its own magnitude
still gives unit weight to bins that are near-empty *within* the retained band, so the divisor is
floored at a fixed fraction of the largest cross-spectral magnitude in the frame. The band
restriction and the magnitude floor address different failure modes and both are required.

**The peak is refined to sub-sample resolution.** One sample of lag at 48 kHz is a substantial
fraction of the maximum physical TDOA on a centimetre-class array, so integer-lag peak-picking
would quantize the azimuth coarsely. We use parabolic interpolation about the integer peak on a
native-length correlation. Section 5.7 shows this is both cheaper than the eightfold zero-padded
transform it replaces and more accurate above 20 dB; the interpolation bias is 0.0026 samples,
because band-limiting the weight widens the correlation main lobe to about seven samples and a
parabola models it well.

### 4.3 Pairwise-to-azimuth inversion

Given the three pair delays, azimuth follows from a linear least-squares solve. Stacking the
baseline vectors as the rows of **A** and the scaled delays as **b**,

  **A** **u** = **b**,  **A**_row(i,j) = (**p**_i − **p**_j)ᵀ,  b_(i,j) = −c τ_ij,   (M31)

and θ̂ = atan2(u_y, u_x). We do not constrain the solution to unit norm; the norm of the
unconstrained solution is a weak consistency indicator, since a solution far from unit length
signals delays that no single plane wave explains.

Error propagation gives the geometric dilution of precision. For the equilateral array with uniform
weights, **A**ᵀ**A** = 4.5 R² **I** exactly, so the azimuth variance is isotropic and

  σ_θ = c σ_τ / (√4.5 · R).   (M40)

This is the source of the 1/R aperture law verified in Section 5.5. Section 5.5 also reports a
correction: the three per-pair TDOA errors are *correlated* on this array, at ±0.33 to 0.44 at low
SNR, because the same three channels appear in all three pairs. The isotropic form (M40) therefore
under-predicts the azimuth error by 15–18 % at low SNR, while the general form (M36) evaluated with
the measured error covariance is accurate to 2 %. We use (M40) as the design law, because it is
correct in its scaling and convenient, and (M36) where accuracy matters.

The estimator is three FFT pairs, three peak searches and a 3×2 least-squares solve per frame, with
no search over candidate directions and no eigendecomposition.

### 4.4 Confidence gate and weighting, and why they cannot pay at M = 3

Not all three pairs deserve equal trust in a given frame. A pair whose cross-correlation has one
tall isolated peak has measured its delay well; a pair with several comparable peaks has not. We
score each pair by the peak-to-sidelobe ratio (PSR): the global maximum divided by the largest
local maximum outside a small exclusion window around it (M43). The PSR feeds two mechanisms, kept
separable so the ablation of Section 5.4 can isolate them.

The **gate** rejects a pair on either of two grounds: physical infeasibility, |τ_ij| > d_ij/c, with
a five-percent tolerance to absorb geometry and clock error (M45); or relative untrustworthiness, a
PSR below half the best pair's PSR in the same frame (M46). The gate cannot starve the solver — if
the criteria would leave fewer than two pairs, the highest-confidence pairs are reinstated. The
**weighting** enters surviving pairs into the solve with weights proportional to PSR (M48). With
both disabled the estimator reduces *exactly* to the estimator of Section 4.3, the same code path
and the same peaks, which makes the ablation a clean comparison.

**We state the outcome here, with its reason, because the reason is structural rather than a
matter of tuning.** The pairwise system has three measurements and two unknowns, so its redundancy
is exactly one. The left null space of **A** is one-dimensional and spanned by (1, −1, 1)/√3, so
there is exactly one scalar test statistic available — the TDOA closure error of (M14). A bias δ on
any single pair shifts that statistic by exactly ±δ/√3, identically for all three pairs up to sign.
The three fault hypotheses are therefore indistinguishable: the geometry permits a fault to be
*detected* and never *identified*. This is the classical detection-versus-exclusion condition, which
requires P = p + 2 measurements for identification and supplies only P = p + 1 here. Dropping a pair
additionally costs up to a factor √3 in σ_θ (M50), because it leaves the exactly-determined system
that remains worse conditioned than the least-squares solution over all three.

Consistent with that, the PSR carries almost no information about frame error: the Spearman rank
correlation between PSR and absolute azimuth error is −0.13 in free field and −0.04 at
RT60 = 0.3 s. Section 5.4 bounds the resulting benefit at 1–3 % of the error. We keep the
feasibility bound in the deployed firmware because it is a cheap guard against reporting an azimuth
derived from an impossible delay, and we drop the PSR weighting entirely, for the reason in
Section 4.5.

### 4.5 Temporal accumulation

Over a window of T consecutive frames from a stationary or slowly moving source, each frame yields
an azimuth estimate. Azimuths are circular quantities and cannot be averaged arithmetically — the
mean of 179° and −179° is not 0° — so we accumulate the sine and cosine separately and report the
arctangent of their ratio:

  θ̂_T = atan2( Σ_t w_t sin θ_t , Σ_t w_t cos θ_t ).   (M55)

**The weights are unity.** We originally weighted frames by their mean PSR. Section 5.6 reports
that weighted and unweighted circular means differ by 0.0001–0.006° and that the sign of the
difference changes with the room, so the weighting is dropped and retained only as an ablation.
This is a simplification rather than a loss: it removes the PSR computation from the per-frame cost
(7 % of the front end by the FLOP model), removes the need to store a confidence at all, and
reduces the recursive form to

  **z**_t = (1 − λ) **z**_{t−1} + λ **u**_t / ‖**u**_t‖,   (M68)

five floating-point operations per frame with no transcendental function.

**Why accumulation helps, and where it stops.** Decompose the per-frame azimuth error into a term
driven by additive noise and the particular signal realization in that frame, and a term driven by
the room. The first changes from frame to frame, is close to zero-mean and is independent across
frames, so averaging T of them reduces its variance by T. The second is set by the fixed geometry
of source, array and reflecting surfaces, is very nearly identical in every frame of a measurement,
and averaging reproduces it rather than removing it. The mean-square error therefore separates:

  MSE(T) = b² + σ₁²/T.   (M62)

Everything about the behaviour of this system in rooms follows from that equation. In free field
b ≈ 0 and the error falls as 1/√T without limit. In a room the curve flattens at |b|, and the frame
count beyond which further accumulation is futile — defined as the T at which the stochastic term
has fallen to a tenth of the bias term — is

  T_futile = σ₁² / (0.1 b²).   (M67)

Section 5.6 measures b, σ₁ and T_futile directly, finds the fit residual to be 0.0002–0.0015°, and
reports T_futile of 1.3, 4.1 and 5.5 frames at RT60 = 0.15, 0.30 and 0.60 s. The accuracy-latency
law follows immediately: with hop H and rate f_s the latency is L = T·H/f_s, so the entire useful
range of the temporal stage in a real room is under 250 ms.

**Moving sources.** A fixed window is the wrong shape for a source that moves, and the recursive
form (M68) is the natural variant. For a source with angular rate ω, accumulation over latency L
incurs a smearing bias of about ωL/2, which trades against the noise term to give an optimal window
(M74). In a reverberant room this is rarely the binding consideration, because T_futile is reached
before smearing matters for any plausible source speed.

### 4.6 Complexity

Per frame, for M microphones, P = M(M−1)/2 pairs, snapshot N, interpolation factor I and a search
grid of G directions, the cost is dominated by transforms. The pairwise estimator needs M forward
transforms, P cross-spectra, P inverse transforms of length IN, P peak searches and one small
least-squares solve. SRP-PHAT reuses the identical correlations and adds a steered sum over the
grid. MUSIC replaces peak-picking with a per-bin covariance estimate and eigendecomposition over the
source band, plus a manifold projection at every grid point. The closed forms are (M85)–(M90).

Evaluated at the nominal configuration the FLOP model gives 4.227 MFLOP for GCC-PHAT, 4.522 (1.070×)
for the gated variant, 4.251 (1.006×) for SRP-PHAT and 3.193 (0.755×) for MUSIC. Section 5.7
explains why the measured host timings disagree with this, and why the model rather than the
measurement is what a system designer should use. Memory is 24 kB of input, a reusable correlation
buffer of 128 kB per pair at I = 8 or 16 kB at I = 1, and 8 bytes of accumulator state.

---

## 5. Simulation study

All simulated results come from a single harness with a fixed seed, so every number is comparable
with every other. Trial counts, standard errors and the log each number came from are stated
throughout. Where a result supersedes a previously reported one, the change is recorded in
`paper/rebaseline_results.md` §5 number by number.

**Setup.** The nominal array is the equilateral triangle of Section 3.2 at R = 5 cm, f_s = 48 kHz,
N = 2048 samples (42.7 ms), c = 343 m/s. The default source is band-limited Gaussian noise over
300–3400 Hz, chosen to approximate the spectral support of speech while remaining stationary and
independent between frames. Free-field propagation applies the delays of (M6) as exact fractional
delays in the frequency domain. Reverberation uses an image-source room model [allen1979image] in
the uniform-wall formulation of the standard reference implementation [habets2006rir], images to
order 12, impulse response 0.8 s, room 6.0 × 5.0 × 3.0 m with the array at its centre and the source
at 1.5 m; a target RT60 is converted to a wall reflection coefficient by the Sabine relation
[kuttruff_roomacoustics]. Within a condition the impulse responses are fixed and only the source
realization and the noise vary — which is precisely the structure that produces a bias floor.
Four estimators are compared: the gated and weighted variant, plain GCC-PHAT, SRP-PHAT on a 1°
azimuth grid, and incoherent wideband MUSIC over 300–3400 Hz with 512-sample sub-snapshots, one
assumed source and a 1° grid. Errors are wrapped to (−180°, 180°] and we report median, 90th
percentile and RMSE. (Figs. `fig_geometry.png`, `fig_srp_spectrum.png`.)

**Two methodological corrections applied throughout.** First, test azimuths are tiled off the
search grid by offsets covering (−0.5°, +0.5°]. In earlier runs every test azimuth was a whole
number of degrees and therefore lay exactly on the 1° search grid of SRP-PHAT and MUSIC, which
allowed those estimators to return the exact answer; after the front-end correction below this
produced RMSE values of exactly 0.000°. Tiling rather than randomizing makes the pooled
quantization error uniform with RMS exactly 1/√12 = 0.289°, a number the reader can check. The same
offsets randomize the phase of the true delays relative to the correlation interpolation grid,
which matters for the correlation estimators for the same reason: without it the residual
quantization error is identical in every frame and behaves as a bias, which would have contaminated
the bias-floor measurement of Section 5.6. Second, every point estimate carries a standard error —
bootstrap for quantiles, delta method for RMSE — and variants that share snapshots are compared as
*paired* differences, which is far more sensitive than comparing independently estimated medians.

### 5.1 The PHAT weighting band, and what it is worth

We report this first because it is the largest effect in the paper and because it changes how every
subsequent number should be read.

PHAT divides each frequency bin by its own magnitude, so after weighting a bin containing only
sensor noise has exactly the same influence on the correlation as a bin containing the source,
while its phase is uniformly random. Measured on the nominal configuration: of 2049 real-FFT bins
per pair, 265 (12.9 %) lie inside the 300–3400 Hz source band; at 10 dB SNR, 68.4 % of all bins
remain at unit weight after regularization, and **80.9 % of those are outside the source band**.
The 60 dB regularization floor does not help, because at any usable SNR almost no bin is 60 dB below
the strongest. (Fig. `fig_phat_band_defect.png`.)

Restricting the weight to the source band, on matched snapshots so that the difference is
attributable to the weight and nothing else (440 frames per cell, `rebaseline_checks_ABC.log`):

| SNR | PHAT weight | RMSE (deg) | median (deg) | σ_τ (µs) |
|---|---|---|---|---|
| 0 dB | full band | 4.927 ± 0.164 | 3.212 ± 0.204 | 26.64 |
| 0 dB | 300–3400 Hz | **0.740 ± 0.023** | 0.528 ± 0.027 | **3.374** |
| 10 dB | full band | 4.046 ± 0.137 | 2.695 ± 0.142 | 22.55 |
| 10 dB | 300–3400 Hz | **0.321 ± 0.011** | 0.227 ± 0.012 | **1.494** |
| 20 dB | full band | 2.093 ± 0.079 | 1.435 ± 0.086 | 13.94 |
| 20 dB | 300–3400 Hz | **0.174 ± 0.005** | 0.121 ± 0.007 | **0.863** |
| 40 dB | full band | 0.816 ± 0.062 | 0.238 ± 0.014 | 9.620 |
| 40 dB | 300–3400 Hz | **0.151 ± 0.004** | 0.107 ± 0.007 | **0.752** |

The paired mean reduction in absolute error is 3.329 ± 0.143° at 0 dB (23.3 σ) and 2.946 ± 0.118° at
10 dB (25.0 σ). The delay-estimation precision moves from 21.0× to 1.39× the attainable value.

**How much of this is real, and how much is an artefact of the simulation.** The harness adds white
noise across the whole 0–24 kHz Nyquist band, whereas real hardware has an anti-alias filter and a
transducer of finite bandwidth, so its out-of-band bins are not filled with noise in the same way.
We therefore model the acquisition chain explicitly as a band-pass applied to signal and noise
together, with the nominal SNR fixing the noise power *spectral density* so that narrowing the
acquisition band removes out-of-band noise without changing the in-band SNR. All cells below are
matched snapshots at 10 dB. (Fig. `fig_phat_artefact_decomposition.png`.)

| configuration | RMSE (deg) | improvement |
|---|---|---|
| full-band weight, full-band noise (as originally simulated) | 4.105 ± 0.142 | 1.00× |
| band-limited weight, full-band noise | **0.307 ± 0.011** | **13.39×** |
| band-limited weight, band-limited noise (8 kHz chain) | **0.317 ± 0.011** | 12.96× |
| full-band weight, band-limited noise (8 kHz chain) | 2.205 ± 0.087 | 1.86× |

Two facts point in different directions and both must be stated. **The absolute accuracy of the
corrected estimator is genuine**: 0.301–0.327° across every acquisition bandwidth from 3.4 to
24 kHz, flat to ±4 %, so the re-baselined numbers in the rest of this section do not depend on the
noise model at all. **The size of the improvement is inflated by the noise model**: the honest
measure of what the fix buys on hardware is 7.0× for an 8 kHz chain and 3.2× for a 4 kHz chain. The
defensible headline is a factor of 3 to 13 depending on acquisition bandwidth, with a
bandwidth-independent per-frame RMSE of 0.31°.

Even when the acquisition band is set exactly equal to the source band, the full-band weight still
costs a factor 3.5, for two separately measured reasons. Where the acquisition band is wider than
the source band, the bins between them hold noise and no source and still receive unit weight; this
dominates. And even when the two coincide, zero-padding from N to 2N before the forward transform
means a brick wall on the length-N grid is not a brick wall on the length-2N grid, so interleaved
bins carry sinc leakage from the retained band. Those leaked bins sit at high frequency where the f²
leverage on the correlation slope is large, and 32 of them are enough to matter. **The practical
consequence is that an anti-alias filter is not a substitute for band-limiting the weight; both are
required.**

### 5.2 Free-field accuracy versus SNR

21 azimuths × 60 trials = 1260 frames per cell. Absolute azimuth error in degrees.
`benchmark_run.log`. (Figs. `fig_rmse_vs_snr.png`, `fig_error_cdf.png`, `fig_accuracy_matrix.png`.)

| method | SNR | median | p90 | RMSE |
|---|---|---|---|---|
| Proposed (gated) | 0 dB | 0.529 ± 0.015 | 1.221 ± 0.026 | 0.750 ± 0.014 |
| | 10 dB | 0.212 ± 0.006 | 0.493 ± 0.013 | 0.301 ± 0.006 |
| | 40 dB | 0.108 ± 0.004 | 0.244 ± 0.005 | 0.148 ± 0.003 |
| GCC-PHAT | 0 dB | 0.527 ± 0.016 | 1.219 ± 0.029 | 0.749 ± 0.014 |
| | 5 dB | 0.308 ± 0.009 | 0.762 ± 0.020 | 0.456 ± 0.009 |
| | 10 dB | 0.212 ± 0.007 | 0.493 ± 0.012 | 0.301 ± 0.006 |
| | 20 dB | 0.125 ± 0.004 | 0.293 ± 0.008 | 0.176 ± 0.003 |
| | 40 dB | 0.108 ± 0.004 | 0.244 ± 0.005 | 0.148 ± 0.003 |
| SRP-PHAT | 0 dB | 0.558 ± 0.018 | 1.308 ± 0.028 | 0.792 ± 0.015 |
| | 10 dB | 0.275 ± 0.010 | 0.625 ± 0.016 | 0.390 ± 0.007 |
| | 40 dB | 0.250 ± 0.009 | 0.458 ± 0.005 | 0.295 ± 0.004 |
| MUSIC | 0 dB | 1.008 ± 0.034 | 3.125 ± 0.144 | 6.470 ± 1.984 |
| | 5 dB | 0.592 ± 0.023 | 1.727 ± 0.071 | 5.096 ± 1.847 |
| | 10 dB | 0.358 ± 0.014 | 0.942 ± 0.030 | 0.697 ± 0.036 |
| | 20 dB | 0.258 ± 0.008 | 0.508 ± 0.009 | 0.346 ± 0.013 |
| | 40 dB | 0.250 ± 0.009 | 0.458 ± 0.008 | 0.290 ± 0.004 |

Four observations.

**RMSE is monotone in SNR for every estimator.** An earlier version of this study reported
non-monotone RMSE, inflated at high SNR by rare wrap-type gross errors, and treated it as a property
of small arrays. It was not; it was a symptom of the unbanded PHAT weight. The heavy-tail signature
RMSE/median at 40 dB falls from 3.43 with the full-band weight to 1.41 with the band-limited weight.
We retract the earlier claim.

**The gated variant and plain GCC-PHAT are indistinguishable.** They agree to within 0.002° at every
SNR, against standard errors of 0.003–0.014°. This is the first appearance of the negative result
that Section 5.4 quantifies in reverberation.

**SRP-PHAT and MUSIC saturate at 0.29–0.31° above 20 dB, and that is their search grid, not their
accuracy.** The 1° grid contributes a quantization RMS of exactly 1/√12 = 0.289°. This must be
quoted whenever those rows are quoted; a finer grid would lower it at proportionally higher cost.

**MUSIC's low-SNR RMSE is outlier-driven.** At 0 and 5 dB its RMSE is 6.47° and 5.10° while its
median is 1.01° and 0.59°. MUSIC breaks catastrophically in a small fraction of low-SNR frames
rather than degrading gracefully — behaviour that Section 5.3 shows becomes dominant in
reverberation.

The accuracy matrix resolves median error jointly over azimuth and SNR and shows no azimuthal
structure, as the isotropy result of Section 4.3 predicts.

### 5.3 Reverberation

9 azimuths × 60 trials = 540 frames per cell at 15 dB SNR. `reverb_run.log`.
(Fig. `fig_accuracy_vs_rt60.png`.)

Median absolute error, degrees:

| RT60 (s) | Proposed | GCC-PHAT | SRP-PHAT | MUSIC |
|---|---|---|---|---|
| 0.05 | 0.446 ± 0.124 | 0.444 ± 0.202 | 0.444 ± 0.324 | 0.778 ± 0.351 |
| 0.20 | 1.897 ± 0.195 | 1.882 ± 0.220 | 1.778 ± 0.333 | 2.667 ± 0.081 |
| 0.30 | 2.565 ± 0.090 | 2.630 ± 0.107 | 2.667 ± 0.051 | 3.333 ± 0.327 |
| 0.60 | 2.757 ± 0.088 | 2.948 ± 0.102 | 2.667 ± 0.025 | 3.667 ± 0.162 |
| 0.80 | 2.876 ± 0.111 | 3.030 ± 0.107 | 2.667 ± 0.043 | 3.667 ± 0.129 |

RMSE, degrees:

| RT60 (s) | Proposed | GCC-PHAT | SRP-PHAT | MUSIC |
|---|---|---|---|---|
| 0.05 | 3.018 ± 0.072 | 3.018 ± 0.072 | 3.134 ± 0.076 | 3.093 ± 0.076 |
| 0.20 | 3.075 ± 0.078 | 3.189 ± 0.081 | 3.129 ± 0.079 | **14.020 ± 2.989** |
| 0.30 | 3.540 ± 0.099 | 3.630 ± 0.101 | 3.504 ± 0.099 | **28.446 ± 2.857** |
| 0.45 | 3.991 ± 0.116 | 4.044 ± 0.115 | 3.976 ± 0.119 | **31.420 ± 2.779** |
| 0.60 | 4.280 ± 0.132 | 4.402 ± 0.132 | 4.300 ± 0.140 | **36.113 ± 2.949** |
| 0.80 | 4.661 ± 0.149 | 4.736 ± 0.149 | 4.639 ± 0.160 | **30.445 ± 2.841** |

**MUSIC collapses in reverberation.** Its RMSE reaches 28–36° above RT60 = 0.3 s while its median
stays near 3.4°, which is the signature of gross front-back and wrap failures in a large minority of
frames rather than a general loss of precision. The narrow-band covariance model underlying
incoherent wideband MUSIC does not survive strong early reflections at M = 3, where there are only
three sensors from which to estimate a covariance and separate a signal subspace.

This result also corrects the record on the comparison itself. An earlier version of this study
reported MUSIC at 0.81° RMSE against GCC-PHAT's 4.23° in free field and read it as evidence that
subspace processing is far more accurate on this array. That comparison was invalid: MUSIC had
always accumulated only bins inside the source band and so was never affected by the weighting
defect of Section 5.1, so the measurement was of a band-limited front end against a full-band one.
With both corrected, GCC-PHAT (0.301°) is more accurate than MUSIC (0.697°) in free field, and the
reverberation results above show MUSIC failing outright where the correlation estimators do not.
The claim that MUSIC is an order of magnitude more accurate than GCC-PHAT on this array is withdrawn.

**The three correlation-based estimators are indistinguishable in reverberation**, agreeing to
about one standard error at every RT60. Note also that the RMSE at RT60 = 0.05 s is 3.0°, far above
the free-field figure at the same SNR: even a nearly anechoic image-source room places a strong
first reflection, and reverberation bias dominates from the very first point of the sweep.

### 5.4 Ablation of the confidence layer

Gate and weighting switched independently, 9 azimuths × 60 trials = 540 *matched* frames per cell at
10 dB SNR; all four variants see the identical snapshot. `ablation_run.log`.
(Fig. `fig_ablation_rt60.png`.)

Paired mean difference in absolute error against plain GCC-PHAT, degrees (negative = better):

| RT60 (s) | Proposed − GCC | Weight only − GCC | Gate only − GCC |
|---|---|---|---|
| 0.05 | −0.0001 ± 0.0006 (0.1 σ) | −0.0004 ± 0.0005 (0.8 σ) | +0.0004 ± 0.0004 (1.0 σ) |
| 0.15 | −0.0245 ± 0.0037 (6.7 σ) | −0.0180 ± 0.0032 (5.6 σ) | −0.0093 ± 0.0024 (3.9 σ) |
| 0.30 | −0.0878 ± 0.0135 (6.5 σ) | −0.0802 ± 0.0107 (7.5 σ) | −0.0150 ± 0.0093 (1.6 σ) |
| 0.45 | −0.0721 ± 0.0145 (5.0 σ) | −0.0575 ± 0.0137 (4.2 σ) | −0.0167 ± 0.0062 (2.7 σ) |
| 0.60 | −0.0862 ± 0.0167 (5.2 σ) | −0.0710 ± 0.0154 (4.6 σ) | −0.0203 ± 0.0088 (2.3 σ) |
| 0.80 | −0.0672 ± 0.0183 (3.7 σ) | −0.0437 ± 0.0179 (2.4 σ) | −0.0179 ± 0.0071 (2.5 σ) |

With 540 matched frames the decision layer's improvement is *statistically detectable* — 3 to 7
standard errors — and it is **0.02 to 0.09°, which is 1 to 3 % of an error of 2.5 to 3.2°**. Almost
all of it comes from the PSR weighting rather than the gate; the gate alone is at or below 2.7 σ at
every RT60 above 0.15 s. The correct statement is therefore not that the layer makes no difference,
but that with three microphones it cannot pay for itself: the effect is real, bounded at a few
percent, and lies far below the reverberation bias floor that Section 5.6 shows dominates. This is
a stronger and more defensible negative result than a failure to reject, because it is quantitative
and bounded.

The explanation is the rank argument of Section 4.4, and it is not a matter of threshold tuning. We
set the gate floor at half the best PSR without tuning it against these results, precisely so the
comparison would not be circular. On an array with six or eight microphones the same layer has
redundancy to exploit, consistent with the effectiveness reported for reliability weighting in the
literature [brandstein1997robust] and with the eight-microphone configurations of prior embedded
systems [grondin2019lightweight].

### 5.5 Resource scaling and isotropy

11 azimuths × 60 trials = 660 frames per point, free field at 10 dB SNR.
`ablation_run.log`. (Figs. `fig_resource_scaling.png`, `fig_isotropy.png`.)

| R (cm) | median | RMSE | R × median (cm·deg) |
|---|---|---|---|
| 2 | 0.459 ± 0.017 | 0.785 ± 0.022 | 0.92 |
| 3 | 0.338 ± 0.017 | 0.516 ± 0.014 | 1.01 |
| 5 | 0.203 ± 0.010 | 0.317 ± 0.009 | 1.01 |
| 8 | 0.126 ± 0.007 | 0.190 ± 0.005 | 1.01 |
| 12 | 0.087 ± 0.004 | 0.128 ± 0.004 | 1.04 |

| N | duration | median | RMSE |
|---|---|---|---|
| 256 | 5.3 ms | 0.554 ± 0.026 | 0.818 ± 0.024 |
| 512 | 10.7 ms | 0.390 ± 0.014 | 0.577 ± 0.017 |
| 1024 | 21.3 ms | 0.273 ± 0.011 | 0.403 ± 0.011 |
| 2048 | 42.7 ms | 0.219 ± 0.010 | 0.317 ± 0.009 |
| 4096 | 85.3 ms | 0.149 ± 0.006 | 0.220 ± 0.006 |

**Aperture obeys the 1/R law.** The log-log slope of median error against R is −0.946 ± 0.032
against the −1 predicted by (M40), and the product R × median is constant to within 8 % over a 6:1
range of aperture, and to within 3 % excluding the smallest array. The practical reading is direct:
from the same silicon and the same code, a 2 cm array is a 0.46° device and a 12 cm array is a
0.09° device. If the enclosure allows the microphones to be moved apart, that is the cheapest
accuracy in this design space. It is also, in a room, entirely academic — Section 5.6 shows that
reverberation bias exceeds all of these figures by an order of magnitude.

**Snapshot length obeys the N^(−1/2) law.** The log-log slope is −0.461 ± 0.020 against the −0.5
predicted, the residual gap being the correlation interpolation grid. An earlier version of this
study measured −0.208 and could not explain it; that anomaly was another symptom of the unbanded
weight, and it is resolved.

**Isotropy.** With uniform weights the azimuth error standard deviation shows no dependence on look
direction, as **A**ᵀ**A** = 4.5 R² **I** predicts. We had expected PSR weighting to break this and
so to constitute a second, independent argument against gating; measured over 24 azimuths × 400
trials, it does not measurably do so. We report that expectation as unsupported and do not use it.

### 5.6 Temporal accumulation and the reverberation bias floor

This is the paper's central result. Free field: 11 azimuths × 30 records × 128 frames.
Reverberant: 7 azimuths × 30 records × 128 frames per room. Each record is split into disjoint
blocks of T, giving 42240/T and 26880/T independent error samples — 330 and 210 blocks at T = 128.
10 dB SNR. `ablation_run.log`. (Figs. `fig_temporal_accumulation.png`, `fig_bias_floor.png`.)

RMSE, degrees:

| T | latency | free field | RT60 0.15 s | RT60 0.30 s | RT60 0.60 s |
|---|---|---|---|---|---|
| 1 | 43 ms | 0.308 ± 0.001 | 1.572 ± 0.010 | 2.351 ± 0.010 | 3.180 ± 0.012 |
| 2 | 85 ms | 0.218 ± 0.001 | 1.527 ± 0.014 | 2.173 ± 0.013 | 2.883 ± 0.015 |
| 4 | 171 ms | 0.153 ± 0.001 | 1.503 ± 0.020 | 2.076 ± 0.017 | 2.725 ± 0.018 |
| 8 | 341 ms | 0.109 ± 0.001 | 1.492 ± 0.029 | 2.028 ± 0.024 | 2.638 ± 0.024 |
| 16 | 683 ms | 0.076 ± 0.001 | 1.486 ± 0.040 | 2.002 ± 0.033 | 2.597 ± 0.032 |
| 32 | 1.37 s | 0.054 ± 0.001 | 1.483 ± 0.057 | 1.988 ± 0.046 | 2.574 ± 0.044 |
| 64 | 2.73 s | 0.038 ± 0.001 | 1.482 ± 0.081 | 1.981 ± 0.065 | 2.564 ± 0.062 |
| 128 | 5.46 s | **0.027 ± 0.001** | **1.481 ± 0.115** | **1.978 ± 0.092** | **2.557 ± 0.087** |

**In free field accumulation behaves exactly as theory predicts and is largely unnecessary.** The
error falls from 0.308° to 0.027°, a factor of 11.4 over 128 frames, with no floor: the fitted bias
is 0.000 ± 0.007° and the directly measured bias is 0.004 ± 0.005°, both indistinguishable from
zero. But the single-frame figure of 0.308° at 43 ms is already finer than any hardware tolerance
that matters. A one-sample inter-channel clock skew is worth about 4°; the near-field curvature bias
of (M11) is 0.72° at one metre; the measured inter-channel gain mismatch of Section 3.6 is 1.2 dB.
Accumulating to sub-tenth-of-a-degree in free field is optimizing a term that is not the limit.

**In every reverberant room accumulation is over by T = 4.** Going from one frame to 128 — from
43 ms to 5.5 s of latency — buys 5.8 % at RT60 = 0.15 s, 15.9 % at 0.30 s and 19.6 % at 0.60 s.
Going only to T = 8, that is 341 ms, already captures 87–88 % of even that. The reason is the bias
term of (M62), and we measure it two independent ways.

Fitting MSE(T) = b² + σ₁²/T to the curves above, and separately measuring the per-azimuth bias
directly as the circular mean of 3840 per-frame errors per azimuth:

| condition | fitted b (deg) | measured b_rms (deg) | fitted σ₁ (deg) | fit residual (deg) | T_futile |
|---|---|---|---|---|---|
| free field | 0.000 ± 0.007 | 0.004 | 0.308 ± 0.001 | 0.0003 | ∞ |
| RT60 0.15 s | 1.480 ± 0.016 | 1.481 | 0.529 ± 0.058 | 0.0002 | 1.3 |
| RT60 0.30 s | 1.977 ± 0.014 | 1.976 | 1.272 ± 0.031 | 0.0015 | 4.1 |
| RT60 0.60 s | 2.553 ± 0.014 | 2.554 | 1.896 ± 0.032 | 0.0008 | 5.5 |

**The fitted and directly measured bias agree to three decimal places in all four conditions**, and
the fitted σ₁ matches the measured value to within 1 %. The fit residuals are 0.0002–0.0015°. The
model (M62) is confirmed to a precision that our earlier, thinner data could not approach: an
earlier analysis over T ≤ 32 with 6–8 trials per condition gave fit residuals of 0.14–0.77°,
unstable bias estimates, and floors carrying about 11 % standard error — enough that the apparent
non-monotonicity across rooms in that data was noise. With 30 records of 128 frames the floor is
resolved to 1 % and **is monotone in RT60**.

Three consequences for a system designer.

1. **The floor is the specification.** A three-microphone array of this aperture will not do better
   than about 1.5° in a well-damped room or 2.6° in a live one, whatever is done downstream. Sub-
   degree accuracy claims for small arrays should be read as free-field claims.
2. **The useful latency budget is under 250 ms.** T_futile is 1.3, 4.1 and 5.5 frames. Beyond that,
   latency buys nothing, and a designer who budgets a second of accumulation is paying for
   responsiveness and receiving no accuracy.
3. **The floor is estimator-independent.** Section 5.3 shows the three correlation estimators sit
   on it together. It is a property of the room and the measurement position, not of the algorithm,
   so it bounds any method in this family — including the more elaborate tracking filters of
   Section 2.5, which can no more average away a frame-invariant bias than a circular mean can.

**Confidence weighting is a tie: the third negative result.** Weighted and unweighted circular means
computed from the *same* per-frame estimates, so the comparison is paired:

| T | free field | RT60 0.15 s | RT60 0.30 s | RT60 0.60 s |
|---|---|---|---|---|
| 8 | +0.0001 (0.7 σ) | +0.0019 (4.7 σ) | +0.0000 (0.0 σ) | −0.0016 (1.1 σ) |
| 32 | +0.0001 (0.7 σ) | +0.0018 (3.9 σ) | −0.0008 (0.7 σ) | −0.0049 (3.1 σ) |
| 128 | −0.0001 (0.5 σ) | +0.0020 (3.7 σ) | −0.0005 (0.4 σ) | −0.0059 (3.6 σ) |

The differences are 0.0001° to 0.006°, which is 0.004 % to 0.23 % of the error, and their sign is
not consistent: weighting is significantly *worse* at RT60 = 0.15 s, indistinguishable at 0.30 s and
significantly *better* at 0.60 s. Nothing that changes sign with the room at the fourth decimal
place is a mechanism. We therefore drop the weighting, as recorded in Section 4.5.

### 5.7 Compute

**We withdraw a claim made in an earlier version of this work**, that measured host timing ratios
transfer to the microcontroller. They do not, and the reason is instructive.

| method | FLOP model (MFLOP) | model ratio | measured host (ms) | measured ratio |
|---|---|---|---|---|
| GCC-PHAT | 4.227 | 1.000 | 0.940 | 1.00× |
| Proposed (gated) | 4.522 | 1.070 | 1.020 | 1.08× |
| SRP-PHAT, reference loop | 4.251 | 1.006 | 4.008 | 4.26× |
| SRP-PHAT, vectorized | 4.251 | 1.006 | **0.886** | **0.94×** |
| MUSIC | 3.193 | 0.755 | 2.927 | 3.11× |
| GCC-PHAT, I = 1 + parabolic | 0.823 | 0.195 | 0.310 | 0.33× |

SRP-PHAT reuses the identical PHAT-weighted correlations that the pairwise estimator computes, so
the FLOP model puts it at 1.006× GCC-PHAT. Our reference implementation measured 4.26×. Isolating
the stages shows the shared front end costs 1.231 ms and the azimuth grid loop 2.471 ms, spread over
1440 NumPy calls at 1.716 µs each — dispatch overhead, not arithmetic. Vectorizing the grid search,
with byte-identical output verified, takes SRP-PHAT to 0.94× GCC-PHAT. **The 4.3× was a property of
the Python loop.** (Fig. `fig_pareto.png`, which plots measured host time and the FLOP model side by
side.)

Which should a designer use? The FLOP and memory model, without qualification. The measured host
times are properties of one NumPy implementation on x86. Where model and measurement agree — the
gated variant at +7 % predicted against +8 % measured — the measurement corroborates. Where they
disagree by a factor of four, the model is right and the measurement is measuring CPython. We report
host timings only under that heading, and only with the vectorized row alongside, because that row
is what demonstrates the point. On-device latency must be measured on the device; Section 6.5
specifies how, and reports that we have not yet done so.

**An implementation recommendation follows from the cost breakdown.** The eightfold zero-padded
inverse FFT accounts for 3.686 of the 4.227 MFLOP front-end cost, or 87.2 %. Replacing it with a
native-length inverse transform and parabolic peak refinement gives:

| term | I = 8 (MFLOP) | I = 1 + parabolic (MFLOP) |
|---|---|---|
| forward FFTs | 0.369 | 0.369 |
| CPSD + PHAT | 0.074 | 0.074 |
| inverse FFTs | 3.686 (87.2 %) | 0.369 (44.8 %) |
| argmax | 0.098 | 0.012 |
| **total** | **4.227** | **0.823** |

That is 5.13× cheaper by model, 3.03× measured on the host, and it reduces the correlation buffer
from 128 kB to 16 kB per pair. The accuracy penalty we expected does not materialize — it is
*more* accurate above 20 dB, by a factor of 3.4 at 40 dB, because parabolic refinement produces a
continuous estimate whereas the I = 8 argmax is quantized to a 2.604 µs grid and cannot resolve
better than 0.139°. The interpolation bias that a full-band analysis warns of, up to 0.119 samples,
measures 0.0026 samples here — a factor of 46 smaller — because band-limiting the weight widens the
correlation main lobe to about seven samples, and a parabola models that well. The two changes are
complementary and should be adopted together.

### 5.8 Summary of the design envelope

At 10 dB SNR on a 5 cm three-microphone array with a correctly band-limited GCC-PHAT front end:
per-frame azimuth RMSE is 0.301 ± 0.006° in free field at 4.23 MFLOP and 42.7 ms of latency;
accuracy scales as 1/R in aperture and N^(−1/2) in snapshot; temporal accumulation reduces error as
1/√T exactly, without limit, in free field; and in any real room the error is pinned within four
frames to a reverberation bias floor of 1.5 to 2.6° that no accumulation, gating, weighting or
subspace method crosses. The per-frame estimator is within 1.39× of the precision attainable given
the interpolation grid and 1.85× of the Cramér–Rao bound, so there is little left to win by
improving it.

---

## 6. Hardware validation

Simulation establishes the shape of the design envelope. It cannot establish that a physical board
sits inside it, because the model omits everything specific to a real build: microphones that do
not match, an acquisition path with its own timing behaviour, a self-noise floor, a real room, and a
source that is neither a point nor perfectly known in position. This section specifies the campaign
that tests those things, reports what the recordings currently in hand do and do not establish, and
states the acquisition a valid campaign requires.

**We report the outcome of that assessment up front, because it is a finding and not a gap.** The
recordings available to us cannot support a direction-of-arrival accuracy claim. Their acquisition
rate is 999.988 Hz against a requirement in the tens of kilohertz, so the entire range of source
azimuths maps into a single correlation lag bin; they carry no anti-alias filter, so what signal
they do contain is folded; the three-channel clips are 30 samples long at an inferred rate near
167 Hz; and none carries a ground-truth azimuth. Sections 6.2 and 6.3 give the evidence and the
arithmetic. Section 6.4 specifies what would be sufficient. We report this rather than computing an
accuracy figure from inadequate data, because a three-microphone localizer is easy to make look
accurate by evaluating it on data that cannot contradict it, and the resulting number would not be a
measurement of anything.

The methodological commitment that will make the eventual comparison meaningful is stated here:
**measured clips pass through the same estimator functions as simulated ones.** There is no separate
implementation for real data. The evaluation script loads a clip, orients it to the simulation's
convention, and calls the identical functions that produced every number in Section 5, with
identical parameters. Nothing is retuned per room, per source or per distance; the PHAT band, the
regularization constant, the feasibility tolerance and the gate floor are frozen at their simulation
values before any measured data is evaluated. Any disagreement between Sections 5 and 6 will
therefore be a property of the physical world rather than of two divergent code paths.

### 6.1 Protocol

The following specifies the campaign. It has not yet been performed; every value marked
`[MEASURE]` is outstanding.

**Array mounting.** The board is mounted horizontally on a turntable at
`[MEASURE: array height above floor, m]` m, with the microphone plane level to within
`[MEASURE: levelling tolerance, degrees]`. No part of the mount lies within
`[MEASURE: clearance radius, cm]` cm of the microphone plane in the horizontal directions, so that
mount reflections do not arrive within the direct-path window. The array reference direction is
marked physically and aligned with the turntable zero index.

**Source.** A single loudspeaker, `[MEASURE: model and driver diameter]`, on a separate stand with
its acoustic centre at the microphone-plane height to within `[MEASURE: height tolerance, cm]` cm,
so the measurement is genuinely azimuth-only. Driven at `[MEASURE: level at 1 m, dB SPL]` dB SPL,
verified with a sound level meter — and, given the negative result of Section 3.6, held constant
across every distance and logged for each run.

**Distances.** At least three source distances, `[MEASURE: distances, m]`, the shortest well inside
and the longest at or beyond the critical distance, so the direct-to-reverberant ratio varies within
each room. Measured from the loudspeaker's acoustic centre to the microphone-triangle centroid with
a laser rangefinder to `[MEASURE: distance uncertainty, cm]` cm. **The shortest distance must
respect the near-field bound of Section 4.1**: for a 0.5° curvature-bias budget on a 5 cm array that
is 1.43 m, and any measurement closer than that carries a known, computable bias of −(R/4r)cos3θ
which must be either avoided or corrected.

**Azimuth grid.** The full circle in steps of `[MEASURE: azimuth step, degrees]`, giving
`[MEASURE: number of positions]` positions per room and distance. Azimuth is varied by **rotating
the array on the turntable**, not by moving the loudspeaker. This holds the source position, the
room geometry and therefore the reflection pattern fixed, so the sweep isolates the array's
directional behaviour instead of convolving it with a changing set of early reflections; it also
makes the ground truth a turntable reading rather than a distance measurement. The array centroid is
aligned to the rotation axis to within `[MEASURE: centering error, mm]` mm. Grid angles should not
be whole degrees, for the reason given in Section 5: a grid-search estimator evaluated at angles
lying on its own search grid returns a flattered result.

**Rooms.** At least two with contrasting acoustics, a damped room at
`[MEASURE: RT60, s]` and a live room at `[MEASURE: RT60, s]`, dimensions
`[MEASURE: room dimensions, m]`, chosen to bracket the range over which Section 5.6 predicts a
strong effect so that the measured floor can be compared with the simulated one at two separated
points.

**RT60 estimation.** From measured room impulse responses rather than from Sabine's formula, so the
reported RT60 is a property of the actual room. At each of `[MEASURE: number of positions]`
source-receiver positions, record the response to an exponential sine sweep, deconvolve, and apply
Schroeder backward integration; take RT60 from the decay slope over
`[MEASURE: evaluation range, e.g. −5 to −25 dB]` extrapolated to 60 dB [kuttruff_roomacoustics].
Report mean and spread across positions and octave-band values from 250 Hz to 4 kHz, since the
source band spans a range over which absorption is not flat.

**Source signals.** Band-limited Gaussian noise over 300–3400 Hz, matching the simulated source
exactly, as the primary signal. Recorded speech, to test a non-stationary source with silent
intervals. An exponential sine sweep for the impulse responses. Each recorded for
`[MEASURE: clip duration, s]` s per position, yielding at least 128 non-overlapping frames so the
accumulator can be exercised over the full range of Section 5.6.

**Ground-truth uncertainty.** An explicit budget rather than an assertion. Three terms: turntable
index resolution `[MEASURE: degrees]`; the angular error from centroid-to-axis offset e at source
distance d, approximately arctan(e/d), giving `[MEASURE: degrees]` at the shortest distance; and
uncertainty in locating the loudspeaker's acoustic centre, `[MEASURE: degrees]`. Combined in
quadrature, `[MEASURE: total, degrees]`. This bounds what the campaign can resolve. Note the
implication of Section 5.6: since the simulated free-field per-frame error is 0.30° and the
accumulated free-field error reaches 0.03°, a ground-truth uncertainty above a few tenths of a
degree makes the free-field predictions untestable — though the reverberation floor of 1.5–2.6°,
which is the paper's central claim, remains comfortably testable.

**Labelling.** Ground-truth azimuth encoded in each filename, with room, distance and source
identifiers, so the ground truth travels with the data.

### 6.2 Acquisition adequacy of the recordings in hand

Every dataset is screened against three necessary conditions before any accuracy analysis, and
datasets that fail are excluded and reported as excluded.

1. The sample period must be small compared with the maximum physical delay d/c, so that distinct
   directions map to distinct lags. As a working criterion we require at least ten samples across
   the admissible delay range, which for the nominal geometry means tens of kilohertz, consistent
   with the inequality of Section 3.3. An anti-alias filter enforcing f_s ≥ 2f₂ is part of this
   condition, not separate from it, for the phase-inflation reason given in Section 3.3.
2. Each clip must contain at least one complete snapshot of N samples, and enough snapshots to
   exercise the accumulator.
3. The three channels must be time-aligned by construction, or their fixed offset measured.

| dataset | rate | samples/clip | channels | ground truth | verdict |
|---|---|---|---|---|---|
| calibration and response recordings (105 distinct) | 999.988 Hz | 30 001 | 1 | none | **fail** (1), (3) |
| three-channel bench clips (25) | ≈167 Hz inferred | 30 | 3 | position label only | **fail** (1), (2), (3) |
| idle recordings (3 × 60 s) | 999.988 Hz | ~62 000 | 1 | not applicable | pass, for noise characterization only |
| quadrant tables (4) | not a recording | — | — | — | **excluded**, see below |

**The arithmetic is not marginal.** The entire admissible delay range on a pair is d/c = 252.5 µs.
At 999.988 Hz the sample period is 1.000 ms, so the whole range spans **0.25 of one sample**: every
source direction in the plane produces the same integer lag and the cross-correlation carries no
directional information whatever. For the three-channel clips the inferred rate is lower still. We
established that rate from the data rather than assuming it: the clips' bias-corrected lag-1
autocorrelation is −0.0013 ± 0.0320, statistically white, whereas the same front end at 1 kHz gives
+0.545; matching the measured idle autocorrelation backwards places these clips at approximately
167 Hz per channel or slower, at which the full azimuth range spans 0.042 of a sample and the
Cramér–Rao azimuth standard deviation is of order 32° at 10 dB. Their 30-sample length is
independently disqualifying, being an order of magnitude shorter than the shortest snapshot
characterized in Section 5.5. (Fig. `fig_real_triplemic.png`, which shows a clip, its
cross-correlation with the physically possible delay window shaded, the 5 × 5 position-label map,
and the peak-lag histogram against the physical bound.)

Interpolation does not rescue this. Sub-sample interpolation recovers the position of a peak that
sampling has already resolved; it cannot recover directional information that was never captured.
Nor would a faster converter alone be sufficient, because without an anti-alias filter the folded
components carry the phase of their original frequencies and enter the cross-spectrum with group
delays inflated by f₀/f_a — up to five complete phase wraps across the array's delay range for a
20 kHz component at 1 kHz sampling.

**On the quadrant tables.** The four `(x, y, t)` grids are excluded from the experimental account
entirely, because they are not measurements. The t field is reproduced to a residual RMS of
0.029 ns, R² = 1.0000000000 over 14 631 rows, by the exact analytic spherical-wave range difference
for a two-microphone pair at (∓0.025, 0) m with c = 343.000 m/s. They are a computed forward model
containing no acoustic data and no error information. They can illustrate the hyperbolic geometry of
near-field multilateration, and they do so in the appendix, but they cannot support any accuracy
claim. We note also that the 5 cm pair they encode is not the geometry of the triangular array used
elsewhere in this paper. (Fig. `fig_real_quadrant_gdop.png`.)

**We also exclude one artefact from our own repository.** A script accompanying the three-channel
clips generates an accuracy heatmap using a uniform random draw rescaled to a preset 77 % mean; it
never reads a recording. No figure or number derived from it appears anywhere in this paper, and we
record its existence here so that it cannot be mistaken for a result in the archived materials.

### 6.3 What the present recordings do establish

The recordings are inadequate for localization but not worthless. Section 3.6 reports the platform
measurements they support, and we summarize them here as the current extent of the hardware
account: an acquisition rate established two independent ways at 999.988 Hz; a self-noise floor of
5.06 LSB RMS mean across three channels, 24.9 dB above the 12-bit quantization floor, establishing
that the analogue front end and not the converter limits the chain; a chain ceiling of 47.9 dB peak
SNR set by clipping rails at 42 and 2523 codes; non-Gaussian noise with excess kurtosis 3.58–7.86;
inter-channel DC agreement to 3.8 LSB with a 2.84 dB noise-floor spread and a 1.21 dB median
broadband gain mismatch; and a measured comparison of four candidate filter designs yielding the
recommendation of Section 3.4.

One sim-to-real bridge is available and it is a modest one. The measured electrical SNR band of the
chain can be placed against the simulated median-error-versus-SNR curve, locating the hardware on
the simulation's horizontal axis. This says what accuracy the simulation *predicts* for a chain of
this noise performance. It is not a measured accuracy and we do not present it as one.
(Fig. `fig_real_snr_operating_point.png`.)

### 6.4 Acquisition required for a valid campaign

The screen also specifies what a sufficient recording is, in a form another group can implement.

| requirement | value |
|---|---|
| Sample rate per channel | ≥ 16 kHz, hardware-timed; ≥ 8 kHz is the arithmetic minimum with I ≥ 8, per Section 3.3 |
| Anti-alias filter | mandatory, enforcing f_s ≥ 2f₂; not optional at any sample rate |
| Timing | driven by a hardware timer or I²S clock, not a software loop; host receive timestamps are not an acquisition time base |
| Channels | 3, sampled simultaneously on a common clock, or with a measured fixed offset |
| Clip length | ≥ 128 non-overlapping snapshots of N samples, so the accumulator can be exercised past T_futile |
| Bit depth | sufficient that quantization sits below the analogue noise floor; 12 bits already exceeds this by 25 dB on the measured chain |
| Drive level | documented and held constant across distances, with a calibrated reference microphone at a fixed position |
| Labelling | ground-truth azimuth in the filename, plus room, distance and source identifiers |
| Coverage | full azimuth grid at non-integer angles, ≥ 2 rooms with measured RT60, ≥ 3 distances per room |
| Acoustic calibration | a pistonphone or class-1 calibrator measurement to fix sensitivity in mV/Pa, without which no dB SPL figure can be reported |
| Phase calibration | one clip of a single broadband source at a known azimuth captured simultaneously on all three channels — approximately ten minutes of bench time, and currently the single highest-value missing measurement |

### 6.5 Measured on-device cost

Per-estimate latency must be measured on the microcontroller itself by reading the hardware timer
around the estimator call and logging the difference over `[MEASURE: number of timed estimates]`
consecutive estimates during normal operation, reporting the distribution rather than a single
figure, because the tail determines whether frames are dropped. The system is real-time if the 95th
percentile, not the mean, stays below the snapshot duration.

| quantity | value |
|---|---|
| Mean / median / p95 / maximum latency | `[MEASURE: ms]` |
| Snapshot duration | `[MEASURE: ms]` |
| Real-time budget used at p95 | `[MEASURE: percent]` |
| Frames dropped during the timing run | `[MEASURE: count]` |
| Per-frame accumulator cost | `[MEASURE: µs]` |
| Accumulator state | 8 bytes, independent of T |
| Peak SRAM / sustained CPU load | `[MEASURE: kB]` / `[MEASURE: percent]` |

**No such measurement exists yet, and no timing log exists anywhere in our repository.** We state
this explicitly because earlier internal documentation of this project circulated a per-estimate
figure of order ten microseconds that was never measured on the device and is not supported by any
data in this or any other campaign. It should be regarded as withdrawn and should not be cited. We
record the withdrawal because a plausible but unmeasured number, once repeated, is difficult to
retract.

### 6.6 Simulation versus measurement

No measured localization result exists, so no sim-versus-real accuracy comparison can be made. What
we can do is enumerate, in advance and with the measurement that quantifies each, the mechanisms
present in the physical system and absent from the simulation. Stating these before the campaign
rather than after it is a guard against explaining away whatever discrepancy appears.

*Inter-channel phase mismatch.* A frequency-dependent phase difference between channels is
indistinguishable, to a cross-correlator, from a delay, and therefore appears directly as an azimuth
bias. This is the largest known unquantified risk to the eventual result, and no recording in hand
permits its measurement. One ten-minute bench capture would settle it.

*Inter-channel gain mismatch.* Measured at 1.21 dB median (Section 3.6). GCC-PHAT is insensitive to
flat gain mismatch, so this is expected to be benign; the measurement is reported so that
expectation is testable rather than assumed.

*Acquisition timing.* A common-clocked digital array has no inter-channel offset by construction. A
multiplexed converter visiting channels in sequence does, and it adds to every TDOA to produce a
systematic azimuth rotation rather than random error. Given the signal-path finding of Section 3.6
this must not be assumed either way; the fixed offset is `[MEASURE: µs]`. Relative clock *drift*
between channels does not arise, since all channels derive from one oscillator, and drift against
the ground-truth timeline does not affect a TDOA estimator. We distinguish the two because the fixed
offset matters and the drift does not.

*Self-noise.* The measured floor of Section 3.6 sets the SNR the array actually achieves at a given
source level and distance, and therefore locates the measured points on the horizontal axis of
Section 5.2. Measured and simulated points must be compared at matched SNR, not at nominal SNR.

*Near-field curvature.* A distance-dependent, frame-invariant bias of −(R/4r)cos3θ, 0.72° at one
metre, with three-fold azimuthal symmetry. Unlike the other terms this one is exactly predicted, so
the measured error-versus-azimuth curve at short range is a direct test of the model: a cos3θ
component of the predicted amplitude should be visible and should vanish as 1/r.

*Diffraction and shadowing.* The microphones sit on a finite populated board, so for directions
where the board lies between a microphone and the source there is shadowing the free-space model
omits. The diagnostic is the error-versus-azimuth curve: a free-space array shows no azimuthal
structure, as the isotropy result of Section 5.5 confirms in simulation, while a shadowed one should
show lobes where each microphone is occluded. Distinguishing this from the near-field cos3θ term
requires the distance sweep, since only the latter scales as 1/r.

*Room and source realism.* The simulated room has rigid rectangular geometry, frequency-independent
uniform absorption and an omnidirectional point source, none of which is true of a real room or
loudspeaker. The image-source model is a known idealization [allen1979image, habets2006rir]; the
octave-band RT60 spread specified in Section 6.1 is the direct evidence of the frequency dependence
it omits. We expect this to change the measured reverberation floor in magnitude while preserving
its existence, and the measured floor is the test of that expectation.

*Estimator asymmetry.* SRP-PHAT and MUSIC are given the exact array manifold in simulation and the
measured one on hardware, carrying the geometry uncertainty of Section 3.2 and the phase mismatch
above. MUSIC depends on the manifold most sharply, so if its measured accuracy degrades relative to
simulation by more than the others do, manifold error is the expected cause rather than anything
about reverberation.

**The single quantitative test that matters.** The paper's central claim is that accumulated error
in a room stops falling at a bias floor set by that room. The campaign tests it by measuring the
accumulated error curve at each position and comparing its asymptote against the simulated floor
interpolated to that room's measured RT60. The prediction is specific and falsifiable: 1.5° in a
well-damped room, 2.6° in a live one, reached within four frames. That is what we would report
whichever way it falls.

---

## 7. Discussion and limitations

*To be written. Planned content: azimuth-only, single-source, horizontal-plane scope; no elevation
and no multi-source separation. Three microphones give redundancy one, so per-frame fault exclusion
is geometrically impossible and accuracy is aperture- and reverberation-limited rather than
algorithm-limited. The reverberation bias floor as a real ceiling, and precedence-effect or
direct-path gating [litovsky1999precedence] as the only principled route below it. The
latency-accuracy trade is nearly worthless in rooms, which inverts the usual embedded intuition.
Simulation-only status of the localization results and what the campaign of Section 6 would settle.
Applications: assistive hearing direction cue, wake-word DoA.*

## 8. Conclusion

*To be written.*

## Appendix A. Near-field two-dimensional position: model and scope

*To be written. Planned content: the spherical-wavefront range-difference model, hyperbolic
intersection, the closed-form estimator [chan1994hyperbolic, smith1987closedform, huang2001lcls,
brandstein1997closedform], and the near-field GDOP σ_r ≈ 3.8 c σ_τ r²/R². The scoping argument: the
break range R²/(3.8 c σ_τ) is 2.52 m at the Cramér–Rao bound but 0.099 m at the precision the front
end actually achieves, and joint (x, y) estimation degrades azimuth by a factor of four against
azimuth-only estimation. The quadrant tables are presented as an analytic illustration of the
geometry, explicitly labelled as a forward model rather than measurement.*

## Back matter

*Data and code availability; acknowledgements; conflicts of interest; funding; references.*
