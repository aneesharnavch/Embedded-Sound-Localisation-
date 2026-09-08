# Draft prose — Sections 1 to 6

> **Status.** Submission-quality prose for Sections 1–6 of the *Acta Acustica* Technical & Applied
> Article. Sections 1 and 2 are final. Sections 3–6 are complete in structure and prose; they carry
> marked slots that other tracks fill.
>
> **Slot conventions used in this file**
>
> | Marker | Meaning | Who fills it |
> |---|---|---|
> | `[MEASURE: ...]` | A board or protocol value that has not yet been measured. | Author / hardware bench |
> | `[VAL: ...]` | A real measured or computed value that exists (or will exist) in the new datasets or in a fit. | Data-analysis track |
> | `[EQ: ...]` | An anchor where a numbered equation from `paper/math_model.md` belongs. | Mathematics track |
> | `[FIG: ...]` | A figure that the data-analysis track is generating. | Data-analysis track |
> | `[VERIFY: ...]` | A citation detail still to be confirmed at the publisher. | Author |
>
> **Citation keys.** Keys with BibTeX in `paper/references.md` are used verbatim
> (`knapp1976gcc`, `schmidt1986music`, `allen1979image`, `grondin2019lightweight`,
> `chan1994hyperbolic`). Keys for entries listed in `references.md` without BibTeX are given
> provisionally here so the LaTeX conversion has something to bind to:
> `dibiase2000srpphat`, `dibiase2001chapter`, `habets2006rir`, `carter1987coherence`,
> `brandstein1997robust`, `litovsky1999precedence`, `valin2007particle`, `argentieri2015survey`,
> `smith1987closedform`, `huang2001lcls`, `brandstein1997closedform`, `brandsteinward2001`,
> `benesty2008microphone`, `vantrees2002optimum`, `kuttruff_roomacoustics`, `espressif_esp32s3`,
> `mems_mic_datasheet`, `farmani2017hearingaid`, `warden2019tinyml`.
> No source outside `paper/references.md` is cited anywhere below.

---

## 1. Introduction

Knowing *where* a sound came from is a small piece of information that unlocks a
disproportionate amount of behavior in a device. A hearing aid that knows the azimuth of the
talker can steer a beam toward them. A voice interface that knows the direction of a wake word
can turn a camera, or suppress the other three people in the room. A mobile robot that knows the
bearing of a call can orient before it has understood the words. A distributed acoustic sensor
that reports a bearing rather than a waveform sends a few bytes instead of a stream, which is
often the difference between a device that runs for a year on a battery and one that does not.
In each of these cases the direction estimate is not the product; it is a cheap input to
something else. That framing sets the engineering problem: the localizer has to be small,
inexpensive, and modest in its use of computation, memory, and energy, because it is competing
for those resources with the application it serves.

The acoustics and array-processing literature has, by contrast, largely optimized for accuracy.
Steered-response power with phase transform (SRP-PHAT) and subspace methods such as MUSIC both
reach high angular accuracy in favorable conditions, and both are robust in ways that simple
time-delay estimation is not, but they buy that with a grid search or an eigendecomposition per
frame, and they generally assume an array with enough elements to give the estimator some
redundancy to work with [argentieri2015survey]. Larger arrays are also physically larger,
which is a problem when the device is a hearing aid, an earbud, or a sensor node the size of a
matchbox, and they are more expensive, which is a problem when the device is meant to be
deployed by the hundred.

There is a real design point that sits below all of this and that the literature has not
characterized cleanly: three microphones, an aperture of a few centimeters, and a general-purpose
microcontroller costing a few dollars. Three is the smallest number of elements that resolves
azimuth over the full circle without a front-back ambiguity, so it is the natural floor for a
planar azimuth sensor. Everything about that configuration is constrained. The aperture sets a
hard limit on how precisely a time delay can be converted into an angle. The microcontroller
sets a hard limit on how much arithmetic can happen between frames. Three elements give exactly
three microphone pairs and two independent time-delay differences, which is the minimum needed to
solve for a two-dimensional direction vector and leaves nothing left over. The practical question
is not whether such a device works — it plainly does, at some accuracy — but *what accuracy is
achievable*, *what actually limits it*, and *which knob is worth turning*.

This paper answers those three questions for a specific, buildable system: three MEMS
microphones in an equilateral triangle on a custom board, driven by an ESP32-S3, running only
generalized cross-correlation with phase transform (GCC-PHAT) time-delay estimation and a
least-squares azimuth solve. We state the main finding up front, because it is the point of the
paper and because it runs against the intuition that usually guides embedded work.

**On a minimal array, the per-frame algorithm barely matters; time does.** We first tried the
obvious per-frame improvement: score each microphone pair by the sharpness of its cross-correlation
peak, reject pairs that are physically infeasible or untrustworthy, and weight the survivors in
the least-squares solve. Across free field and across reverberation times from 0.05 s to 0.8 s,
that layer is statistically indistinguishable from plain GCC-PHAT. The reason is structural
rather than a matter of tuning: with three microphones there are three pairs and two degrees of
freedom, so discarding a pair does not leave a redundant, better-conditioned subset to fall back
on. There is nothing for a gate to exploit. We report this as a negative result rather than
burying it, because it is the most useful thing we learned about the design point.

What does work is accumulation. Successive frames of a stationary or slowly-moving source give
per-frame azimuth estimates whose noise-driven errors are close to independent. Taking a
confidence-weighted circular mean over T frames drives the root-mean-square error down almost
exactly as 1/sqrt(T) — in free-field simulation at 10 dB SNR, from 3.88 degrees at T = 1 to
0.68 degrees at T = 32, against a 1/sqrt(T) prediction of 0.69 degrees. The accumulator costs a
few additions and two floating-point accumulators, so its memory footprint does not grow with T.
It converts latency, which most of these applications have to spare, into accuracy, which they
do not.

Accumulation is not free of limits, and the limit is the second finding. Reverberation does not
behave like noise. A room's early reflections are fixed by the geometry of the room, the source,
and the array, so the delay error they induce is largely deterministic within a measurement
position. Averaging removes the stochastic part and leaves the deterministic part behind. In the
same simulation, accumulation to T = 32 leaves a residual RMSE of 2.14, 2.00, and 2.60 degrees
at RT60 of 0.15, 0.3, and 0.6 s respectively — an order of magnitude above the free-field value
at the same T, and no longer improving at the 1/sqrt(T) rate. That floor is a property of the
room, not of the estimator, and no amount of patience crosses it. Any claim that a small array
achieves sub-degree accuracy in a real room should be read with that in mind.

A third observation completes the design envelope. Growing the array is far more effective than
growing the frame. Increasing the circum-radius from 2 cm to 12 cm improves the median error from
7.31 to 1.10 degrees, close to the inverse-aperture scaling that geometry predicts. Increasing
the snapshot length by the same factor of sixteen, from 5 ms to 85 ms, improves it only from 4.27
to 2.40 degrees. If a design has a spare centimeter, it should spend it on the array before it
spends it on the frame buffer.

The contributions of this paper are deliberately modest and, we believe, all defensible:

1. **A minimal, buildable platform.** An open three-microphone ESP32-S3 direction-of-arrival
   sensor with a total bill of materials of approximately $[MEASURE: total BOM cost], with its
   geometry, acquisition path, and firmware pipeline documented well enough to reproduce
   (Section 3).
2. **A formal statement of the estimator the device actually runs**, including
   confidence-weighted temporal accumulation as the mechanism that produces its accuracy, and an
   explicit complexity account (Section 4).
3. **A quantified design envelope** for minimal azimuth sensors: accuracy against SNR,
   reverberation time, aperture, snapshot length, accumulated frames, and per-estimate compute,
   all produced by one reproducible simulation harness with a fixed random seed (Section 5).
4. **Two negative results, reported as results.** Per-frame confidence gating and weighting are
   indistinguishable from plain GCC-PHAT at M = 3, and the reverberation bias floor bounds what
   temporal accumulation can deliver in a real room.
5. **Hardware validation through the same code path.** Real recordings from the device are
   evaluated by the identical estimator functions used on simulated data, so simulated and
   measured numbers are directly comparable rather than merely adjacent (Section 6).

We are explicit about what this paper is not. We do not propose a new estimator, and we do not
claim theoretical results about time-delay estimation; GCC-PHAT, SRP-PHAT, MUSIC, and the
image-source room model are all used as published. The contribution is applied: a characterization
of a constrained operating point, a platform that makes it concrete, and honest boundaries around
both.

The rest of the paper is organized as follows. Section 2 reviews the estimators we use and
compare against, and positions the work with respect to prior low-cost and embedded localizers
and to the DoA-tracking literature that our accumulator belongs to. Section 3 describes the
hardware platform, the array geometry, the acquisition path, and the firmware pipeline.
Section 4 gives the signal model, the per-frame estimator, the confidence layer, the temporal
accumulator, and the complexity analysis. Section 5 reports the simulation study. Section 6
reports the hardware measurement protocol and results, including measured on-device latency and
an honest comparison of simulated and measured behavior. Section 7 discusses limitations and
Section 8 concludes.

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
sharper and far less sensitive to the spectral coloration that a room and a source impose. In
practice PHAT is the weighting that survives contact with real rooms, and it is the front end of
essentially every lightweight localizer, including ours.

The classical treatment of what limits TDOA accuracy is Carter's review of coherence and time
delay estimation [carter1987coherence]. Two of its results matter directly here. First, the
variance of a delay estimate from independent observations falls inversely with the number of
independent observations, which is the theoretical statement behind the 1/sqrt(T) behavior we
measure in Section 5.5. Second, the achievable accuracy is governed by the magnitude-squared
coherence between the two channels; when coherence is degraded, the estimator does not merely
become noisier, it becomes biased in a way that more data does not remove. Reverberation is
precisely a coherence-destroying mechanism, and this is the theoretical home of the bias floor we
report.

Brandstein and Silverman made the practical version of the same point: in rooms, it is
reverberation and not additive noise that breaks TDOA-based localization, because a strong early
reflection can produce a cross-correlation peak that is taller than the direct-path peak
[brandstein1997robust]. Their response — score each pair's correlation for reliability and treat
unreliable pairs differently — is the direct ancestor of the confidence gate and weighting we
describe in Section 4.3. Our contribution on that point is not the idea but the measurement of
how much it is worth on an array with three elements, and the answer turns out to be: not much,
for a reason specific to M = 3.

### 2.2 Steered-response power

SRP-PHAT, introduced in DiBiase's thesis [dibiase2000srpphat] and given its widely-read exposition
as a chapter in Brandstein and Ward's edited volume [dibiase2001chapter, brandsteinward2001],
avoids committing to a per-pair delay estimate at all. It sums the PHAT-weighted cross-correlation
of every pair, each evaluated at the delay that a candidate direction would produce, and searches
the resulting spatial power map for its maximum. Because a spurious peak in one pair rarely
aligns with spurious peaks in the others at the same candidate direction, the sum is markedly more
robust to reverberation than independent per-pair peak-picking. The cost is the grid search: the
map must be evaluated at every candidate direction, and the resolution of the grid bounds the
resolution of the estimate. On our array and grid this costs roughly four times as much per
estimate as the pairwise method (Section 5.7). SRP-PHAT is our robustness baseline.

### 2.3 Subspace methods

MUSIC [schmidt1986music] takes a different route: it estimates the spatial covariance matrix of
the array, splits its eigenvectors into signal and noise subspaces, and reports the directions
whose steering vectors are most nearly orthogonal to the noise subspace. Under its assumptions —
enough snapshots to estimate the covariance, a known array manifold, and a source count known in
advance — it resolves far more finely than the aperture would suggest for a delay-domain
estimator. It is our accuracy ceiling and our compute floor. It is also the baseline whose
assumptions are hardest to satisfy on a cheap board: the array manifold depends on microphone
positions known to a fraction of a wavelength and on channels matched in gain and phase, neither
of which is guaranteed by a low-cost build. We return to this in Section 6.4. General treatments
of both the delay-domain and subspace families are available in the standard array-processing
references [benesty2008microphone, brandsteinward2001, vantrees2002optimum].

### 2.4 Small and embedded localizers

The closest prior work in spirit is the ManyEars and ODAS line, of which Grondin and Michaud's
account of lightweight and optimized localization and tracking is the clearest statement
[grondin2019lightweight]. That work asks how to make sound-source localization cheap enough to
run continuously on a robot, and answers with careful engineering of the search and the tracking
stage. The important contrast for us is the array: it operates on eight microphones in open and
closed configurations, and much of its robustness comes from having enough elements that outliers
can be outvoted. We are asking a strictly harder version of the question — what remains when the
array has three elements and no redundancy at all — and our negative result in Section 5.4 is,
in effect, a measurement of what is lost when the element count drops that far.

Argentieri, Danès, and Souères survey localization in robotics from binaural methods through
array processing and name the constraints that define our design point: embeddability, real-time
operation, and degradation under noise and reverberation [argentieri2015survey]. Their survey is
also a convenient single reference for the claim that the accurate classical methods are
compute-heavy, microphone-heavy, or both. On the application side, direction estimation for
hearing devices is an established motivation for small-aperture work
[farmani2017hearingaid; VERIFY: publication year, journal volume and pages], and the broader
practice of running signal-processing and inference workloads on microcontroller-class hardware
is well enough established to make a dollar-class DoA sensor a reasonable design target
[warden2019tinyml].

### 2.5 Temporal integration and tracking

Averaging or tracking direction estimates over time is not new, and we do not present it as new.
The tracking literature for acoustic sources is mature: Valin, Michaud, and Rouat combine
beamforming with particle filtering to follow multiple moving sources [valin2007particle], and
recursive Bayesian filters of that kind are the standard tool when sources move, appear, and
disappear. Those methods maintain a state distribution, need a motion model, and cost memory and
arithmetic proportional to the number of particles or the dimension of the state.

Our accumulator is the minimal member of that family. It maintains two scalar accumulators — a
weighted sum of the sine and a weighted sum of the cosine of the per-frame azimuths — and reports
their arctangent. It has no motion model, assumes the source is stationary over the accumulation
window, and uses O(1) memory regardless of T. We claim no advantage over particle or Kalman
tracking in generality; we claim that on this class of hardware the minimal version captures most
of the available benefit, and we quantify how much benefit that is and where it stops. The
theoretical justification for the rate at which it improves, and for the floor at which it stops,
comes from the coherence framework already cited [carter1987coherence].

### 2.6 Reverberation modeling

Our reverberant simulations use the image-source method of Allen and Berkley [allen1979image] in
the uniform-wall formulation, with the Sabine relation converting a target reverberation time into
a wall reflection coefficient [kuttruff_roomacoustics]. Our implementation follows the structure
of the widely-used reference implementation described by Habets [habets2006rir], so that the room
model is the standard one rather than an ad hoc construction. Lowering the reverberation floor
that we report would require exploiting the precedence effect — that is, gating on the direct
sound before reflections arrive rather than averaging over them — and we point to that literature
in the discussion rather than attempting it here [litovsky1999precedence].

### 2.7 Scope: what this paper claims and does not claim

We state this plainly because it determines how the rest of the paper should be read. We do not
introduce a new estimator, a new weighting function, or a new statistical result about time-delay
estimation. Every algorithm we run is taken from the references above and used as published. What
we contribute is applied and empirical:

- a characterization of a specific, extreme operating point (three microphones, centimeter-class
  aperture, microcontroller-class compute), including the point at which each resource stops
  paying;
- a quantitative negative result about per-frame confidence gating at M = 3, which is a design
  recommendation rather than a theorem;
- a measured statement of the reverberation bias floor that bounds temporal accumulation;
- a documented platform and a shared simulation-and-measurement harness that make all of the above
  reproducible.

Framed that way, the work is a technical and applied characterization study, and we intend it to
be read and judged as one.

---

## 3. System and hardware platform

### 3.1 Overview

The device is a single custom printed circuit board carrying three MEMS microphones, their
acquisition path, and an ESP32-S3 module [espressif_esp32s3]. It captures three synchronized
channels, computes an azimuth estimate per frame, accumulates estimates over a short window, and
emits a bearing. There is no host computer in the loop and no off-board processing; the numbers in
Section 6.3 are for the complete on-device path.

`[FIG: system block diagram — three microphones, acquisition path, ESP32-S3, DoA output]`
`[FIG: photograph of the assembled board with the three microphone positions marked]`

The transducers on the direction-of-arrival array are InvenSense INMP441 MEMS microphones: bottom-
ported omnidirectional elements with an integrated sigma-delta converter and a digital I2S output,
so the microphone delivers a multi-bit pulse-code sample stream directly to the microcontroller
with no external preamplifier or analog-to-digital converter in the path. The relevant rated
quantities from the datasheet are a signal-to-noise ratio of 61 dB(A), a sensitivity of
`[MEASURE: rated sensitivity, dBFS at 94 dB SPL]`, and an acoustic overload point of
`[MEASURE: rated AOP, dB SPL]` [mems_mic_datasheet; VERIFY: datasheet revision and the exact rated
values]. These are rated figures and we use them only as a reference against which the measured
idle floor of Section 3.6 is compared; we do not restate them as measurements of this build.

Two properties of this part matter to the estimator rather than to the audio quality. First, all
channels are clocked from a single I2S bit clock and word-select line, so the microphones sample
on a common timebase and there is no inter-channel timing offset to correct — which is the
property a TDOA estimator most needs and the reason a digital multi-microphone part is the right
choice here. Second, the sigma-delta converter and its decimation filter impose a fixed group
delay, which is common to all three channels and therefore cancels in every pairwise difference,
but any channel-to-channel variation in it does not cancel and appears as an azimuth bias. The
calibration measurement of Section 3.6 is what bounds that residual.

We flag one unresolved inconsistency rather than paper over it, because it affects how the
measured data in Section 6 must be interpreted. The preliminary three-channel capture files
available from the bench contain integer samples in a 12-bit range centered near
`[VAL: measured DC offset of each channel, ADC counts]` counts. A digital I2S microphone produces
a signed, nominally zero-mean sample stream with no DC pedestal, so those files are not consistent
with an INMP441 path; a centered 12-bit code is the signature of an analog capsule digitized by
the ESP32-S3 internal successive-approximation ADC. The most likely explanation is that the
direction-of-arrival array and the rig used for those particular captures are not the same
hardware — that the preliminary and calibration recordings were taken with an earlier analog
front end. We therefore leave the confirmed signal path as an explicit open item:
`[MEASURE: confirm, per dataset, the signal path used — digital I2S INMP441 versus analog capsule
into the internal SAR ADC — together with the sample bit depth and the origin of the ~1250-count
DC offset]`.

The prose that follows is written to remain correct under either resolution, and the distinction
has one concrete consequence that Sections 6.1 and 6.4 test directly. On the I2S path the three
channels are sampled simultaneously and there is no fixed inter-channel offset. On a multiplexed
SAR path they are not: the converter visits the channels in sequence, adding a deterministic
offset to every measured TDOA and hence a systematic rotation to every reported azimuth. That
offset must be either eliminated in the acquisition configuration or measured once and subtracted.
Which of the two applies to each dataset is an empirical question, and Section 6.1 specifies the
measurement that settles it.

### 3.2 Array geometry

The three microphones sit at the vertices of an equilateral triangle in the horizontal plane. A
triangle is the smallest planar arrangement that resolves azimuth over the full 360 degrees
without a front-back ambiguity; a three-element *linear* array of the same footprint resolves only
a half-plane and would be the wrong choice for a sensor that has to report a bearing rather than
a cone. Placing the microphones on a circle also makes the geometry isotropic, so azimuth accuracy
does not depend strongly on which way the board is facing — a property we test directly in the
accuracy matrix of Section 5.2 and in the full-circle measurement grid of Section 6.1.

The nominal design is a circum-radius of R = `[MEASURE: measured circum-radius, cm]` cm, giving
microphone coordinates of `[MEASURE: measured microphone coordinates in the board frame, cm]` and
an inter-microphone spacing of d = R sqrt(3) = `[MEASURE: measured inter-microphone spacing, cm]`
cm. The corresponding maximum physical time difference of arrival between a pair is d/c =
`[MEASURE: maximum pair TDOA, microseconds]` microseconds at c = 343 m/s, which is the bound the
feasibility gate of Section 4.3 enforces. Geometry must be measured on the assembled board rather
than taken from the layout file: the quantity that matters to the estimator is the acoustic port
separation, and it enters the azimuth solution linearly, so a one-millimeter error on a 50 mm
baseline is a two-percent scale error on every delay-to-angle conversion. The simulation study in
Section 5 uses R = 5 cm as its nominal configuration and, in Section 5.6, sweeps R from 2 to 12 cm
so that the sensitivity of accuracy to this dimension is explicit.

`[FIG: measured array geometry with the microphone coordinates annotated]`

### 3.3 Acquisition

Sampling is at fs = `[MEASURE: measured per-channel sample rate, kHz]` kHz per channel, with all
three channels `[MEASURE: confirm simultaneous versus sequential/multiplexed sampling]`. The
estimator operates on snapshots of N = `[MEASURE: snapshot length, samples]` samples, which is
`[MEASURE: snapshot duration, ms]` ms per frame; this is the quantity that sets both the
per-frame latency and the real-time compute budget, and it is the horizontal axis of the snapshot
sweep in Section 5.6. Samples are `[MEASURE: sample word length, bits]` bits, and the usable
dynamic range of the captured stream is `[MEASURE: usable dynamic range, dB]` dB. Frames are
`[MEASURE: confirm whether consecutive frames overlap, and by how much]`, which matters for
Section 4.4 because the 1/sqrt(T) argument assumes the noise contributions of successive frames
are close to independent, and overlapping frames are not.

The sample rate is not a free parameter, and it is worth stating the constraint explicitly here
because Section 6 returns to it. The largest time difference of arrival any real source can
produce on a pair is d/c, so the whole observable range of the measurement is that wide. Resolving
azimuth to within about one degree requires resolving delay to roughly (pi/180) d/c, which for the
nominal geometry of Section 3.2 is a few microseconds. Sub-sample interpolation of the correlation
peak supplies part of this — an eightfold interpolation at 48 kHz gives a lag grid of 2.6
microseconds — but interpolation cannot recover information the sample rate never captured. A
capture at a rate low enough that the sample period approaches or exceeds d/c does not merely
degrade the estimate; it makes the delay unobservable, since every admissible source direction
maps to the same integer lag. Any acquisition intended for direction-of-arrival work on this
aperture must therefore run in the tens of kilohertz.

The simulation study uses fs = 48 kHz and N = 2048 samples (42.7 ms), which was the nominal board
configuration at the time the sweeps were run. Where the measured board values differ, Section 6.4
states the difference and its expected effect rather than silently re-running the figures.

### 3.4 Firmware pipeline

The real-time pipeline is: capture the frame into a double buffer; remove the DC offset and apply
a band-limiting FIR filter over `[MEASURE: filter passband, Hz]`; compute the PHAT-weighted
cross-correlation for each of the three microphone pairs; take each pair's peak lag and
peak-to-sidelobe ratio; solve the gated, weighted least-squares problem for the direction vector;
and fold the resulting azimuth into the running accumulator. Only the accumulator state persists
between frames, so the memory cost of the temporal stage does not grow with the accumulation
length.

The ESP32-S3 has two cores and the work splits naturally across them: one core owns acquisition
and the DMA-fed ring buffer, the other owns the transform-domain work, so that a frame is being
captured while the previous frame is being processed. Measured resource use is
`[MEASURE: peak SRAM footprint, kB]` kB of SRAM (of which `[MEASURE: FFT and correlation working
buffers, kB]` kB is transform working space) and `[MEASURE: sustained CPU load, percent]` percent
sustained CPU load at the operating frame rate, leaving `[MEASURE: headroom, percent]` percent
headroom for an application. Section 6.3 reports the measured per-estimate latency distribution
that these figures summarize.

### 3.5 Cost

`[MEASURE: bill of materials table — line items, quantities, unit costs, extended costs]`

The complete bill of materials comes to approximately $`[MEASURE: total BOM cost]` in single-unit
quantities, of which the microcontroller module is $`[MEASURE: MCU cost]` and the three
microphones together are $`[MEASURE: microphone cost]`. We give this figure because the design
point is defined as much by its cost as by its element count: the argument of this paper is about
what is reachable at the bottom of the market, and a reader deciding whether to adopt this
configuration needs to know what it costs relative to a commercial array. We deliberately do not
make quantitative accuracy-per-dollar comparisons against specific commercial products, because we
have not measured those products under our protocol.

### 3.6 Characterization datasets

Four measurement campaigns characterize the platform independently of any localization result, and
they populate this section. Each is reported with the marked slots below and analyzed by the
data-analysis track.

**Idle noise floor.** A recording of `[VAL: number of samples in the idle recording]` samples with
no source present, in a quiet room, gives the self-noise floor of the complete acquisition chain.
We report the per-channel RMS in ADC least-significant bits, `[VAL: measured idle noise floor, ADC
LSB RMS, per channel]`, its spectral shape, and the channel-to-channel spread. The floor is what
grounds the SNR axis of Section 5 in a physical quantity: an SNR of 10 dB in simulation
corresponds to a source level of `[VAL: source SPL corresponding to 10 dB SNR at the array, dB
SPL]` at the array given this floor. We compare the measured floor against the microphone's rated
noise specification to establish whether the chain is transducer-limited or electronics-limited
`[VAL: measured floor versus the rated datasheet noise specification, dB]`. Because of the
signal-path ambiguity noted in Section 3.1, each noise measurement is reported together with the
acquisition path it was taken on `[MEASURE: signal path used for the idle recording]`; a floor
measured on an analog front end does not characterize an I2S digital microphone path, and we do
not transfer a figure from one to the other.
`[FIG: measured noise floor PSD, three channels overlaid]`

**Inter-channel calibration.** A common-sound-field recording, with all three microphones exposed
to nominally the same signal, quantifies the gain and phase mismatch between channels. We report
the gain spread `[VAL: inter-channel gain mismatch, dB]` and the residual inter-channel delay
`[VAL: inter-channel delay offset per pair, microseconds]`. The latter is the quantity that
directly biases azimuth, and it is also the measurement that reveals a multiplexed-converter
offset if one exists. A delay offset can only be resolved to a fraction of the sample period, so
this measurement is meaningful only if the calibration recording was itself captured at a rate
adequate for the aperture; we therefore report the sample rate of the calibration dataset
alongside its result `[MEASURE: sample rate of the calibration recordings]`, and treat any
inter-channel delay smaller than one sample period as unresolved rather than as zero.
`[FIG: inter-channel gain and phase mismatch versus frequency]`

**Frequency response.** A swept-sine measurement of each channel gives the passband, the
low-frequency roll-off imposed by the acquisition path, and any resonance from the acoustic port
or the enclosure. We report the usable band `[VAL: measured usable band, Hz]` and compare it with
the 300–3400 Hz band used by the simulated source.
`[FIG: measured per-channel frequency response]`

**Distance response.** A sequence of recordings at increasing source distance characterizes the
level-versus-distance behavior and identifies the distance at which the direct-to-reverberant
ratio in a given room drops far enough to matter. It also marks the boundary of the far-field
assumption for this aperture. `[VAL: measured level versus distance, and the estimated
critical distance for each test room]` `[FIG: measured level versus source distance]`

A fifth dataset — a grid of arrival-time measurements over a horizontal plane, recorded per
quadrant — supports a secondary near-field position-estimation result that is reported in the
appendix and is not part of the azimuth study.

### 3.7 Reproducibility

The complete simulation and evaluation harness is four Python files depending only on NumPy,
SciPy, and Matplotlib, with a fixed random seed, so every simulated figure in Section 5 regenerates
bit-identically. Crucially, the same estimator functions are called on measured clips as on
simulated ones; there is no separate "real data" implementation that could quietly diverge. Source
code, firmware, board files, and the measurement datasets are archived at
`[MEASURE: repository URL and Zenodo DOIs for code, hardware, and data]`.

---

## 4. Method

This section states the estimator formally. It is deliberately explicit about which parts are
standard and which parts constitute the method of this paper: Sections 4.1 and 4.2 are textbook,
Section 4.3 is the layer we tried and found to be marginal, Section 4.4 is the mechanism that
produces the accuracy, and Section 4.5 accounts for the cost. Numbered equations are supplied in
the companion mathematical development and anchored here.

### 4.1 Signal model

We model a single source in the horizontal plane, far enough from the array that the wavefront
crossing the aperture is planar. Write the M = 3 microphone positions in the array plane as p_1,
p_2, p_3, and the direction of arrival as the unit vector u(theta) pointing from the array toward
the source at azimuth theta. Relative to the array origin, the wavefront reaches microphone m at a
delay proportional to the projection of that microphone's position onto the direction vector.

`[EQ: per-microphone steering delay tau_m = -(p_m . u(theta))/c]`

The far-field assumption is what makes the delay depend on the direction only, not on the range,
and it is what reduces localization to a two-parameter problem with one parameter (the range)
discarded. It holds when the source range is large compared with the aperture; for a
centimeter-class array this is satisfied at conversational distances, and Section 3.6 reports the
measured distance at which it begins to fail.

The observed signal at microphone m is the source signal delayed by tau_m, convolved with the
room's impulse response from source to that microphone, plus additive sensor and ambient noise.

`[EQ: multichannel observation model x_m(t) = h_m * s(t - tau_m) + n_m(t)]`

For a pair (i, j) the observable quantity is the difference of the two delays, the TDOA, which
depends on the direction through the *baseline* vector p_i - p_j. This is the central geometric
relation of the paper: a pair does not measure a direction, it measures the projection of the
direction onto its own baseline.

`[EQ: pairwise TDOA tau_ij = -((p_i - p_j) . u)/c]`

With M = 3 there are three pairs, hence three such projections, but only two of them are
independent: the three TDOAs sum to zero around the triangle. Two independent projections and two
unknown components of the unit vector is an exactly determined system with no redundancy. That
observation is not a technicality; it is the reason for the negative result in Section 5.4, and
the redundancy argument is developed formally in the companion mathematics.

`[EQ: TDOA sum-to-zero constraint and the rank of the pairwise system at M = 3]`

*Remark (near field).* When the source is close enough that wavefront curvature over the aperture
is not negligible, the delay depends on range as well as bearing and a pair's TDOA defines a
hyperbola rather than a ray. Everything in Sections 4 to 6 assumes the far-field limit; the
near-field model and the position estimator built on it are given in the appendix.
`[EQ: near-field range-difference model and its far-field limit — appendix]`

### 4.2 Per-frame estimate

For each frame of N samples and each of the three pairs, we compute the PHAT-weighted generalized
cross-correlation [knapp1976gcc]: transform both channels, form the cross-spectrum, normalize
every bin to unit magnitude, and inverse-transform to obtain a correlation function of lag whose
peak marks the TDOA.

`[EQ: GCC-PHAT cross-correlation R_ij(tau)]`

Two implementation details matter enough to state, because both change the numbers.

First, the PHAT normalization is regularized. Dividing every bin by its own magnitude gives unit
weight to bins that contain nothing but numerical noise — out-of-band bins, in particular — and
amplifies their essentially random phase to full influence. We therefore floor the divisor at a
fixed fraction (10^-3) of the largest cross-spectral magnitude in the frame, so that empty bins
are down-weighted rather than promoted. Without this regularization the estimator's accuracy
degrades as the SNR *improves*, which is a diagnostic worth naming: it happens because a higher
SNR makes the out-of-band bins relatively emptier and their phases correspondingly more random.

`[EQ: regularized PHAT weighting]`

Second, the correlation is evaluated on an interpolated lag grid — we use an eightfold
oversampling of the inverse transform — because at fs = 48 kHz one sample of lag corresponds to a
substantial fraction of the maximum physical TDOA on a centimeter-class array, and integer-lag
peak-picking alone would quantize the azimuth coarsely. The resulting lag resolution is
1/(8 fs) `[EQ: lag quantization and its azimuth equivalent]`.

Given the three pair delays, azimuth follows from a linear least-squares solve. Stacking the
baseline vectors as the rows of a matrix A and the scaled delays as a vector b, the direction
vector u is the least-squares solution of A u = b, and the azimuth is the four-quadrant arctangent
of its components. We do not constrain the solution to unit norm; the norm of the unconstrained
solution is itself a weak consistency indicator, since a solution far from unit length signals
delays that no single plane wave explains.

`[EQ: least-squares azimuth, A u = b with rows p_i - p_j and entries -c tau_ij]`

The estimator is therefore three FFT pairs, three peak searches, and a 3-by-2 least-squares solve
per frame, with no search over candidate directions and no eigendecomposition.

### 4.3 Confidence gate and weighting

Not all three pairs deserve equal trust in a given frame. A pair whose cross-correlation has one
tall isolated peak has measured its delay well; a pair whose correlation has several comparable
peaks — because a reflection arrived with comparable energy, or because the frame was mostly noise
— has not. We score each pair by the peak-to-sidelobe ratio (PSR) of its correlation: the height
of the global maximum divided by the height of the largest local maximum outside a small exclusion
window around it.

`[EQ: peak-to-sidelobe ratio definition]`

The PSR feeds two mechanisms, which we keep separable so that the ablation in Section 5.4 can
isolate them.

The **gate** rejects a pair outright on either of two grounds. The first is physical
infeasibility: a delay whose magnitude exceeds the pair's baseline divided by the speed of sound
cannot have been produced by any plane wave, so it is a reflection or a spurious peak, and we
reject it. We allow a five-percent tolerance on this bound to absorb geometry and clock error
rather than rejecting marginal but genuine peaks. The second is relative untrustworthiness: a pair
whose PSR falls below a fixed fraction (we use one half) of the best pair's PSR in the same frame
is rejected. The gate is prevented from starving the solver — with two unknowns, at least two
pairs must survive — so if the criteria would leave fewer than two, the highest-confidence pairs
are reinstated in order.

`[EQ: feasibility bound |tau_ij| <= d_ij / c and the relative-PSR gate condition]`

The **weighting** is softer: surviving pairs enter the least-squares solve with weights
proportional to their PSR, so that a confident pair dominates a marginal one instead of being
averaged with it on equal terms. In implementation this is the standard weighted least-squares
solution, applied by scaling each row of A and the corresponding entry of b by the square root of
its weight.

`[EQ: weighted least-squares azimuth with PSR weights]`

With both mechanisms disabled the estimator reduces *exactly* to the unweighted, ungated
pairwise GCC-PHAT least-squares estimator of Section 4.2 — the same code path, the same peaks —
which is what makes the ablation a clean comparison rather than a comparison of two
implementations.

We state the outcome here rather than saving it: **on this array the confidence layer is a
marginal effect.** Section 5.4 shows that gate and weighting, separately and together, are
statistically indistinguishable from plain GCC-PHAT across reverberation times from 0.05 to 0.8 s.
The explanation is the rank argument of Section 4.1. Discarding one of three pairs leaves two,
which is exactly the number needed, so the gate cannot trade a corrupted measurement for a
redundant clean one; it can only make the remaining system worse conditioned. Weighting
redistributes influence within a system that has no spare degrees of freedom to redistribute it
into. Both mechanisms are known to help on larger arrays, and we would expect them to help here
too if there were more elements. We keep the layer in the described system because it costs
essentially nothing and because the feasibility bound is a cheap guard against pathological
outputs, but we do not present it as a source of accuracy.

`[EQ: redundancy argument — why hard gating cannot help at M = 3]`

### 4.4 Confidence-weighted temporal accumulation

This is the mechanism that produces the paper's accuracy, and it is deliberately simple.

Over a window of T consecutive frames from a source that is stationary or slowly moving, each
frame yields an azimuth estimate and a frame confidence, the latter taken as the mean PSR of the
surviving pairs. Azimuths are circular quantities, so they cannot be averaged arithmetically —
the mean of 179 and -179 degrees is not 0 — and we therefore accumulate the confidence-weighted
sine and cosine of the per-frame estimates separately and report the arctangent of their ratio.

`[EQ: weighted circular mean, theta_hat = atan2(sum_t w_t sin theta_t, sum_t w_t cos theta_t)]`

Why this improves the estimate, and by how much, follows from the structure of the per-frame
error. Decompose the per-frame azimuth error into a term driven by the additive noise and the
particular realization of the source signal in that frame, and a term driven by the room. The
first term changes from frame to frame and is close to zero-mean and independent across frames, so
averaging T of them reduces its variance by a factor of T and its standard deviation by sqrt(T).
The second term is set by the geometry of the source, the array, and the room's reflecting
surfaces, all of which are fixed during a measurement; it is very nearly the same in every frame,
so averaging leaves it untouched. The mean-square error of the accumulated estimate therefore
separates into a term that decays as 1/T and a term that does not.

`[EQ: MSE(T) = b^2 + sigma^2/T]`
`[EQ: 1/sqrt(T) convergence of the stochastic term]`

Two consequences follow and both are load-bearing for this paper. First, in free field, where the
bias term is essentially absent, the accumulated RMSE should track 1/sqrt(T) over the whole range
of T, and Section 5.5 shows it does so to within a few percent. Second, in a reverberant room the
curve should peel away from 1/sqrt(T) and flatten at a floor set by the bias, and Section 5.5 shows
that too. The floor is a property of the room and the measurement position, not of the estimator;
it is the honest boundary on what temporal accumulation delivers, and it is why we do not claim
sub-degree accuracy in rooms.

The confidence weighting is a refinement of the plain circular mean, on the reasoning that frames
in which the correlation peaks were sharp should count for more. We report it and its unweighted
ablation side by side in Section 5.5, and we do not overstate what it buys.

The accumulator costs two multiply-accumulates, a sine, and a cosine per frame, plus one
arctangent per reported estimate, and it stores exactly two floating-point values regardless of T.
This is the property that makes the accuracy-for-latency trade available on a microcontroller at
all: a device that cannot afford a heavier per-frame estimator can afford to wait.

For sources that move, a fixed window is the wrong shape, and the natural variant is a recursive
one — an exponentially-weighted version of the same accumulator, or the wrapped-angle
proportional-integral-derivative tracker we implement — which trades some of the variance
reduction for the ability to follow a change. The window length is then bounded above by how
fast the source moves, as discussed in Section 7. The fixed-window form analyzed here is the one
whose behavior we characterize, because it is the one whose error obeys the clean decomposition
above.

`[EQ: recursive/exponentially-weighted accumulator and its effective window length]`

### 4.5 Complexity

The per-frame cost of the proposed estimator is dominated by the transforms: for M microphones
there are M(M-1)/2 pairs, each requiring a forward transform of each channel — shared across pairs
— a cross-spectrum product, and an inverse transform onto the interpolated lag grid, followed by a
peak search and a small least-squares solve of fixed size. With M = 3 this is three channel
transforms, three cross-spectra, three interpolated inverse transforms, three peak searches over
the lag grid, and a 3-by-2 solve.

`[EQ: per-frame complexity of the proposed estimator]`

SRP-PHAT reuses the same three cross-correlations but then evaluates a steered power sum at every
point of an azimuth grid, adding a term proportional to the grid size times the number of pairs.

`[EQ: per-frame complexity of SRP-PHAT]`

MUSIC replaces peak-picking with a per-frequency-bin covariance estimate and eigendecomposition
over the source band, followed by a projection of the array manifold onto the noise subspace at
every grid point, adding terms in the number of bins, the cube of the element count, and the grid
size.

`[EQ: per-frame complexity of MUSIC]`

The memory picture differs in the same direction. The proposed estimator needs the frame buffers
and the transform working space, and its temporal stage needs two scalars. SRP-PHAT additionally
needs the correlation functions of all pairs resident while the grid is swept. MUSIC needs a
covariance matrix per frequency bin and a precomputed or recomputed steering manifold over the
grid.

Measured wall-clock times in Section 5.7 confirm the ordering: the proposed estimator and plain
GCC-PHAT are within five percent of each other, and both are about a quarter of the cost of
SRP-PHAT or MUSIC. Those measurements are on an x86 host and only their ratios should be carried
over to the microcontroller; the absolute on-device figure is measured directly in Section 6.3.

---

## 5. Simulation study

### 5.1 Setup

All simulated results come from a single harness so that every number in this section is
comparable with every other. The harness is pure NumPy and SciPy with a fixed random seed (7), and
regenerates identically on re-run.

**Array and sampling.** The nominal configuration is the equilateral triangle of Section 3.2 with
circum-radius R = 5 cm, so the microphone coordinates are (0, 5), (-4.33, -2.5), and (4.33, -2.5)
cm and the inter-microphone spacing is 8.66 cm. Sampling is at fs = 48 kHz and the snapshot is
N = 2048 samples, or 42.7 ms. The speed of sound is 343 m/s.
(Fig. `fig_geometry.png`.)

**Source.** The default source is band-limited Gaussian noise over 300–3400 Hz, chosen to
approximate the spectral support of speech while remaining a stationary, well-characterized signal
whose realizations are independent between frames. Tone and chirp sources are available in the
harness and were used for diagnostic checks; all reported numbers use the band-limited noise
source.

**Free-field propagation.** For a source at azimuth theta, the per-microphone delays follow the
steering relation of Section 4.1 and are applied as fractional delays in the frequency domain, so
that sub-sample delays are represented exactly rather than rounded to the sample grid. Independent
Gaussian noise is then added to every channel at the specified array-wide SNR.

**Reverberant propagation.** Reverberation uses an image-source room model [allen1979image] in the
uniform-wall formulation of the standard reference implementation [habets2006rir], with images up
to order 12 in each dimension and an impulse response length of 0.8 s. The room is 6.0 by 5.0 by
3.0 m with the array at its center and the source at 1.5 m in the horizontal plane. A target RT60
is converted to a wall pressure-reflection coefficient by the Sabine relation
[kuttruff_roomacoustics], with the absorption coefficient capped at 0.99. The source is convolved
with each microphone's impulse response and additive noise is applied to the specified SNR as
before. The room impulse responses depend on the source azimuth and the RT60 but not on the trial,
so within a condition the reflections are fixed and only the source realization and the noise
vary — which is precisely the structure that produces a bias floor under accumulation.

**Estimators compared.** Four: the proposed gated and weighted estimator of Section 4.3; plain
GCC-PHAT with unweighted least squares; SRP-PHAT on a 1-degree azimuth grid; and incoherent
wideband MUSIC over the 300–3400 Hz band with 512-sample sub-snapshots, a Hann window, 50 percent
overlap, one assumed source, and a 1-degree grid. SRP-PHAT and MUSIC both know the array geometry
exactly, which on real hardware they would not; Section 6.4 returns to this.
(Fig. `fig_srp_spectrum.png` shows a single SRP-PHAT spatial spectrum for a source at 37 degrees
at 10 dB SNR, included as an illustration of what the grid search is searching.)

**Error metric.** All errors are angular differences wrapped to the interval (-180, 180] degrees.
We report the median absolute error, the 90th percentile of the absolute error, and the RMSE. We
report all three deliberately, because they disagree in an informative way on this array: the
median describes the typical frame, while the RMSE is dominated by rare gross errors in which the
estimate lands on the wrong side of the array. Reporting only one of them would hide the phenomenon
described in Section 5.2.

### 5.2 Free-field accuracy versus SNR

We swept azimuth from -150 to 150 degrees in 15-degree steps and SNR over 0, 5, 10, 20, and 40 dB,
with 30 trials per combination, for all four estimators.

**Table 1.** Free-field angular error in degrees (median / 90th percentile / RMSE), 21 azimuths x
30 trials per cell.

| Estimator | 0 dB | 5 dB | 10 dB | 20 dB | 40 dB |
|---|---|---|---|---|---|
| Proposed (gated) | 3.43 / 8.08 / 5.02 | 3.14 / 7.66 / 4.69 | 2.88 / 7.02 / 4.32 | 1.67 / 4.61 / 7.23 | 0.34 / 2.28 / 1.95 |
| GCC-PHAT | 3.45 / 8.07 / 4.93 | 3.09 / 7.41 / 4.60 | 2.82 / 6.89 / 4.23 | 1.67 / 4.28 / 7.14 | 0.35 / 2.21 / 1.74 |
| SRP-PHAT | 4.00 / 11.00 / 6.66 | 4.00 / 10.00 / 6.12 | 4.00 / 9.00 / 5.60 | 2.00 / 5.00 / 3.21 | 0.00 / 3.00 / 2.32 |
| MUSIC | 1.00 / 3.00 / 12.93 | 1.00 / 2.00 / 6.00 | 0.00 / 1.00 / 0.81 | 0.00 / 0.00 / 0.13 | 0.00 / 0.00 / 0.00 |

(Figs. `fig_rmse_vs_snr.png`, `fig_error_cdf.png`, `fig_accuracy_matrix.png`.)

Four things in this table are worth drawing out.

**The median is well-behaved and the delay-domain estimators are equivalent.** For the proposed
estimator the median absolute error falls monotonically from 3.43 degrees at 0 dB to 0.34 degrees
at 40 dB, and plain GCC-PHAT tracks it within 0.06 degrees at every SNR. That equivalence is the
first appearance of the negative result of Section 5.4, here in free field: on this array the
confidence layer changes nothing measurable.

**The RMSE is not monotone, and this is a real effect rather than a bug.** For the proposed
estimator the RMSE falls from 5.02 degrees at 0 dB to 4.32 degrees at 10 dB, then rises to 7.23
degrees at 20 dB, then falls to 1.95 degrees at 40 dB, while the median at those points is 2.88, 1.67
and 0.34 degrees. A statistic that rises while the median falls is the signature of a heavy tail:
the typical frame is getting better while a small number of frames are getting catastrophically
worse. The mechanism is ambiguity. On an 8.66 cm baseline the whole physically-admissible range of
TDOA is narrow, competing correlation peaks are close together, and when the peak search selects
the wrong one the resulting azimuth can be wrong by a large angle — a wrap-type error rather than
a precision error. Nothing about a higher SNR prevents this, because the competing peaks are a
property of the source's autocorrelation and the array's geometry, not of the noise. The 90th
percentile shows the same story more gently: it improves monotonically, from 8.08 to 2.28 degrees,
so the tail responsible for the RMSE excursion lies above the 90th percentile and involves a small
fraction of frames.

This matters beyond bookkeeping. A device that reports one estimate per frame will occasionally
report a badly wrong bearing even in excellent conditions, and no amount of per-frame cleverness
on three microphones removes that. It is one of the two independent motivations for temporal
accumulation, which suppresses isolated gross errors by outvoting them. The other is the ordinary
variance reduction of Section 5.5.

**SRP-PHAT does not beat pairwise GCC-PHAT here.** Its median sits at 4.00 degrees from 0 to 10 dB
and its RMSE is the worst of the four at low SNR. This is not an indictment of SRP-PHAT; it
reflects that on three microphones the steered power sum has only three cross-correlations to
combine, so the outlier-suppression that makes it strong on larger arrays has little to work with,
while its 1-degree grid puts a floor under its resolution. It is a further instance of the paper's
general finding: at M = 3, algorithmic sophistication has little material to act on.

**MUSIC has the best median and the worst low-SNR tail.** Its median error is at or below 1 degree
at every SNR and reaches the grid resolution from 10 dB upward, which is what makes it the accuracy
ceiling for this study. But its RMSE at 0 dB is 12.93 degrees, the largest of any estimator at any
SNR, meaning that when its covariance estimate is poor it fails badly rather than gracefully. We
note also that MUSIC in simulation is given the exact array manifold; Section 6.4 discusses why
that advantage is not free on a real board.

The accuracy matrix (Fig. `fig_accuracy_matrix.png`) resolves the median error jointly over azimuth
and SNR and shows no strong azimuthal structure, which is the expected consequence of the isotropic
triangular geometry and confirms that the aggregate numbers in Table 1 are not averaging over a
strongly direction-dependent performance.

### 5.3 Reverberation

We swept RT60 with the image-source room model, holding the source at 1.5 m and sweeping azimuth
from -120 to 120 degrees in 30-degree steps, 12 trials per condition, at 10 dB SNR. The relevant
numbers are the "neither gate nor weight" row of the ablation, which by construction is exactly
plain GCC-PHAT.

**Table 2.** Median absolute azimuth error in degrees versus RT60, at 10 dB SNR, single frame.

| RT60 (s) | 0.05 | 0.15 | 0.30 | 0.45 | 0.60 | 0.80 |
|---|---|---|---|---|---|---|
| Median error (deg) | 2.2 | 2.7 | 4.3 | 4.8 | 5.9 | 5.0 |

(Fig. `fig_accuracy_vs_rt60.png`.)

The pattern is the expected one. In an almost anechoic room the single-frame median is 2.2 degrees,
consistent with the free-field figure of 2.88 degrees at the same SNR in Section 5.2 given the
different azimuth grid and trial count. As RT60 grows through the range typical of rooms that
people actually use — roughly 0.2 to 0.5 s for offices, living rooms, and small meeting rooms —
the median roughly doubles, to between 4 and 5 degrees. Beyond 0.6 s the curve flattens and at
0.8 s is slightly below its value at 0.6 s. We do not read that non-monotonicity as a real
improvement: at 12 trials per condition and with the room impulse responses fixed within a
condition, the spread between adjacent RT60 points is comparable with the difference between them.
The defensible statement is that the error saturates in the 5-degree region once the room is
strongly reverberant, rather than continuing to grow.

The four-estimator comparison at this operating point, including how SRP-PHAT's outlier suppression
and MUSIC's subspace separation behave as coherence degrades, requires re-running the dedicated
RT60 sweep with its numeric output retained: `[VAL: median and 90th-percentile error versus RT60
for all four estimators, from the reverb_robustness.py sweep]`. Fig. `fig_accuracy_vs_rt60.png`
already plots this comparison; the tabulated values behind it were not preserved in the run log and
we will not restate them from the figure.

### 5.4 Ablation of the confidence layer

The ablation switches the gate and the weighting independently and sweeps RT60, at 10 dB SNR,
7 azimuths and 12 trials per condition. With both disabled the estimator is identically plain
GCC-PHAT, so the four rows differ only in the decision layer and share every other line of code.

**Table 3.** Median absolute azimuth error in degrees versus RT60, at 10 dB SNR, by ablation
variant.

| Variant | 0.05 s | 0.15 s | 0.30 s | 0.45 s | 0.60 s | 0.80 s |
|---|---|---|---|---|---|---|
| Gate + weight (proposed) | 2.3 | 2.7 | 4.4 | 4.7 | 5.3 | 4.7 |
| Weight only | 2.3 | 2.7 | 4.4 | 4.7 | 5.3 | 4.5 |
| Gate only | 2.2 | 2.7 | 4.3 | 4.8 | 5.9 | 5.0 |
| Neither (= GCC-PHAT) | 2.2 | 2.7 | 4.3 | 4.8 | 5.9 | 5.0 |

(Fig. `fig_ablation_rt60.png`.)

**This is the paper's first negative result and we state it without qualification: the confidence
layer does not help.** Across the whole range of reverberation the four variants agree to within
0.1 degree at five of the six RT60 values. The only points where the spread reaches 0.6 degree are
at RT60 = 0.6 and 0.8 s, where the weighted variants happen to sit below the unweighted ones, and
at 12 trials per condition that difference is not separable from the sampling variability visible
elsewhere in the same table — the same variants swap order between 0.45 and 0.60 s. Note also that
"gate only" reproduces "neither" to the digit at every RT60, which is what one expects when the
feasibility bound and the relative-PSR threshold almost never fire in a way that changes the
solution.

The explanation is structural, not a matter of threshold tuning, and we set the gate floor at
one half of the best PSR without tuning it against these results precisely so that the comparison
would not be circular. With three microphones there are three pairs and two independent
constraints. A gate that rejects one pair leaves exactly the two required, so it does not select a
better-conditioned subset from a redundant set; it merely removes a constraint and, if the rejected
pair was in fact usable, makes the solution worse. A weighting redistributes influence across a
system with no spare degrees of freedom. On an array with six or eight microphones the same layer
has redundancy to exploit, which is consistent with the effectiveness reported for reliability
weighting in the literature [brandstein1997robust] and with the eight-microphone configurations of
prior embedded systems [grondin2019lightweight].

We keep the layer in the deployed firmware, because it costs nothing measurable (Section 5.7) and
because the physical-feasibility bound is a cheap guard against reporting an azimuth derived from
an impossible delay. We do not present it as a contribution to accuracy, and a reader building a
three-microphone localizer should not expect one from it.

### 5.5 Temporal accumulation

This is the paper's principal result. We accumulate T consecutive frames from a stationary source
using the confidence-weighted circular mean of Section 4.4, and report the RMSE over 11 azimuths
from -150 to 150 degrees at 10 dB SNR (8 trials per condition in free field, 7 azimuths and 6
trials per condition in the reverberant rooms).

**Table 4.** RMSE in degrees versus accumulated frames T, at 10 dB SNR. The last row is the
1/sqrt(T) prediction anchored at the measured free-field value at T = 1.

| Condition | T=1 | T=2 | T=4 | T=8 | T=16 | T=32 |
|---|---|---|---|---|---|---|
| Free field, confidence-weighted | 3.88 | 2.90 | 2.20 | 1.33 | 0.96 | 0.68 |
| Free field, plain circular mean | 4.10 | 2.92 | 2.07 | 1.38 | 0.99 | 0.75 |
| Room, RT60 = 0.15 s | 4.70 | 4.28 | 2.91 | 2.77 | 2.36 | 2.14 |
| Room, RT60 = 0.30 s | 8.13 | 4.29 | 3.58 | 3.11 | 2.74 | 2.00 |
| Room, RT60 = 0.60 s | 7.04 | 6.66 | 5.92 | 4.23 | 3.75 | 2.60 |
| 1/sqrt(T) reference (free field) | 3.88 | 2.74 | 1.94 | 1.37 | 0.97 | 0.69 |

(Fig. `fig_temporal_accumulation.png`.)

**In free field the accumulator follows 1/sqrt(T) closely.** The measured RMSE falls from 3.88
degrees at a single frame to 0.68 degrees at 32 frames, a factor of 5.7 against the theoretical
factor of sqrt(32) = 5.66. Agreement with the reference row is within 0.05 degree at T = 8, 16, and
32, and the largest departure anywhere on the curve is 0.26 degree at T = 4. This is a
consequential result for the design point: an estimator that is mediocre per frame becomes
sub-degree by waiting, using two scalar accumulators and a handful of arithmetic operations per
frame. At the simulation's snapshot length of 42.7 ms and without frame overlap, T = 8 corresponds
to 0.34 s of accumulation, T = 16 to 0.68 s, and T = 32 to 1.37 s. Sub-degree free-field accuracy
therefore costs somewhere between half a second and a second and a half of latency, and no extra
memory.

**In rooms the curve flattens against a floor, exactly as the bias decomposition predicts.**
At T = 32 the residual RMSE is 2.14 degrees at RT60 = 0.15 s, 2.00 degrees at 0.30 s, and 2.60
degrees at 0.60 s — three to four times the free-field value at the same T, and still improving
only slowly. The gap between the measured curve and the 1/sqrt(T) reference grows monotonically
with T in every room, which is the signature of an additive term that does not average away. If the
error were purely stochastic, the RT60 = 0.30 s curve would reach 8.13/sqrt(32) = 1.44 degrees at
T = 32; it reaches 2.00. The fitted bias floor and per-frame variance for each room, obtained by
fitting the two-parameter mean-square model of Section 4.4 to these curves, are `[VAL: fitted bias
floor b and per-frame standard deviation sigma per RT60, from the fit to Table 4]`.

The interpretation follows Section 4.4 and Carter's coherence framework [carter1987coherence]. The
noise-driven part of the per-frame error is independent across frames and averages away. The part
contributed by early reflections is set by the fixed geometry of the room, the source, and the
array, and is therefore nearly identical in every frame of a measurement; averaging reproduces it
rather than removing it. A practical corollary worth stating for anyone deploying such a sensor:
the floor is a property of the *position*, so it varies from one placement to another within the
same room, and a device that is accurate at one spot may be consistently biased at another. It is
also why the three room curves are not ordered strictly by RT60 — the 0.30 s room reaches a
slightly lower floor than the 0.15 s room — since the floor depends on the specific reflection
pattern at that source and array placement and not on RT60 alone.

**The confidence weighting is not the source of the gain.** In free field, weighted accumulation
beats the plain circular mean at four of the six values of T (by 0.22, 0.02, 0.05, 0.03 and 0.07
degree at T = 1, 2, 8, 16 and 32) and loses at T = 4 (by 0.13 degree). Averaged over the curve this
is a small and inconsistent advantage, and we do not claim it as a real one in free field. The
mechanism that produces the accuracy is the averaging itself, not the weights. The reverberant
runs in Table 4 used the weighted accumulator only, so we cannot report a weighted-versus-plain
comparison in rooms from these data; establishing whether the weighting earns its keep where the
per-frame confidences actually differ — which is the reverberant case — requires the unweighted
reverberant sweep: `[VAL: RMSE versus T for the plain circular mean in the three reverberant
rooms]`. Until that is run, the honest position is that the weighting is unproven, and that a plain
circular mean would capture essentially all of the demonstrated benefit.

Finally, note the relationship between this result and the heavy-tailed RMSE of Section 5.2.
Accumulation attacks both parts of the problem at once: it reduces ordinary estimation variance,
and because a wrap-type gross error in one frame is outvoted by the surrounding frames in the
circular mean, it also suppresses the rare catastrophic errors that inflate the single-frame RMSE.
The two effects are why the accumulated free-field RMSE at T = 32 (0.68 degree) is below even the
*median* single-frame error at the same SNR (2.88 degrees).

### 5.6 Resource scaling

Two sweeps map the physical design envelope, both in free field at 10 dB SNR with 11 azimuths and
25 trials per condition, using the proposed estimator on a single frame.

**Table 5.** Median absolute azimuth error versus array circum-radius (snapshot fixed at 2048
samples) and versus snapshot length (radius fixed at 5 cm).

| Circum-radius (cm) | 2 | 3 | 5 | 8 | 12 |
|---|---|---|---|---|---|
| Median error (deg) | 7.31 | 4.63 | 2.95 | 1.65 | 1.10 |

| Snapshot (samples) | 256 | 512 | 1024 | 2048 | 4096 |
|---|---|---|---|---|---|
| Snapshot (ms) | 5 | 11 | 21 | 43 | 85 |
| Median error (deg) | 4.27 | 3.40 | 3.06 | 2.72 | 2.40 |

(Fig. `fig_resource_scaling.png`.)

**Aperture is the strongest physical lever, and it scales close to inversely.** Growing the
circum-radius by a factor of six, from 2 to 12 cm, improves the median error by a factor of 6.6,
from 7.31 to 1.10 degrees. An exactly inverse relationship anchored at the 2 cm point would predict
1.22 degrees at 12 cm; the measured value is slightly better than that. The behavior is what the
geometry predicts: a fixed delay-estimation error converts into an angular error inversely
proportional to the baseline over which the delay is measured, so the dilution of precision falls
as the array grows. `[EQ: GDOP azimuth variance]` The practical reading for a designer is direct.
A 2 cm array is a 7-degree device and a 12 cm array is a 1-degree device, from the same silicon and
the same code. If the enclosure allows the microphones to be moved apart, that is the cheapest
accuracy available anywhere in this design space.

**Snapshot length is a much weaker lever than its sample count suggests.** Increasing the snapshot
by the same factor of sixteen in samples, from 256 to 4096, improves the median error only from
4.27 to 2.40 degrees, a factor of 1.78. Had the error fallen as the inverse square root of the
sample count, the expected factor would have been 4. The comparison with Section 5.5 is the
striking one: sixteen times more samples inside one frame buys a factor of 1.78, while sixteen
times more samples spread across sixteen accumulated frames buys a factor of about 4 (3.88 to 0.96
degrees). Both configurations observe the same total quantity of signal, and the segmented one is
substantially more accurate.

We do not have a fully verified explanation for the size of that gap and we will not manufacture
one. Several mechanisms plausibly contribute, and separating them would need a dedicated
experiment: the source is band-limited to 300–3400 Hz so successive samples are correlated and the
effective number of independent looks grows more slowly than N; a longer frame contributes
additional low-amplitude correlation structure that can raise a competing sidelobe as easily as it
sharpens the main peak; and a single frame yields a single peak-pick, so a frame that resolves onto
the wrong peak is wrong regardless of its length, whereas the accumulator gets an independent
peak-pick per frame and outvotes the bad ones. The last of these is consistent with the
gross-error behavior of Section 5.2 and is, in our view, the most likely dominant term.

The design recommendation that follows is concrete: with a fixed sample budget, prefer many short
frames accumulated over one long frame. This is also the cheaper choice on a microcontroller,
because transform cost grows faster than linearly in the frame length while accumulation cost is
constant per frame.

### 5.7 Accuracy versus compute

We measured wall-clock time per estimate for each estimator over 80 repetitions on the same input,
after a warm-up call, on an x86 laptop.

**Table 6.** Measured compute per estimate and free-field RMSE at 10 dB SNR.

| Estimator | ms per estimate | Relative cost | RMSE at 10 dB (deg) | Median at 10 dB (deg) |
|---|---|---|---|---|
| Proposed (gated) | 1.353 | 1.0x | 4.32 | 2.88 |
| GCC-PHAT | 1.289 | 1.0x | 4.23 | 2.82 |
| SRP-PHAT | 5.494 | 4.3x | 5.60 | 4.00 |
| MUSIC | 5.459 | 4.2x | 0.81 | 0.00 |

(Fig. `fig_pareto.png`.)

These absolute timings are host-machine numbers and do not transfer to the ESP32-S3; only the
ratios between estimators do, since all four are dominated by the same kinds of operation
(transforms, elementwise complex arithmetic, and search). The measured on-device latency is
reported in Section 6.3 and is the figure a system designer should budget against.

Three readings of the table.

First, **the confidence layer is free.** The proposed estimator costs five percent more than plain
GCC-PHAT, which is the cost of computing three peak-to-sidelobe ratios. Since Section 5.4 shows it
also delivers nothing, the honest summary is that it is a cheap no-op on this array, retained as a
sanity guard rather than as an accuracy mechanism.

Second, **SRP-PHAT is dominated here.** It costs 4.3 times as much as the pairwise method and is
less accurate at this operating point by both median and RMSE. That is specific to M = 3 and to a
1-degree grid; we would not expect it to hold on a larger array.

Third, **MUSIC is not dominated, and we say so.** It attains 0.81 degree RMSE at 10 dB against the
pairwise method's 4.23, for 4.2 times the per-estimate compute. On free-field simulated data with a
perfectly known array manifold, MUSIC is the better estimator, and a Pareto plot of these four
points shows it on the frontier. Three qualifications bound that conclusion, and they are the
reason the platform does not run MUSIC. Its accuracy is fragile: at 0 dB its RMSE is 12.93 degrees,
worse than any other estimator at any SNR in Table 1, so its good behavior is conditional on
adequate covariance estimation. It requires the array manifold, which on a low-cost board means
microphone positions and inter-channel phase known to a precision that Section 3.6 measures rather
than assumes. And its cost is in *peak per-frame* compute and in memory — a covariance matrix per
frequency bin and a manifold over the grid — which are exactly the resources a microcontroller
running an application alongside the localizer has least of.

The comparison that actually characterizes the design point is between spending compute per frame
and spending frames. Accumulating 32 frames of the pairwise estimator reaches 0.68 degree RMSE in
free field, better than single-frame MUSIC's 0.81, at 1.353 ms of peak per-frame compute rather
than 5.459 ms, with two scalars of state, at the price of about 1.4 s of latency. If the
application can wait, time is the cheaper currency. If it cannot, the extra per-frame compute is
the only route to that accuracy, and whether the microcontroller can supply it is the design
question. In a room neither route reaches sub-degree accuracy, because the reverberation floor of
Section 5.5 binds first.

**A scoped secondary result.** Everything above concerns far-field azimuth, which is the design
point this paper characterizes. The same three delays also support a different question when the
source is close to the array: estimating a two-dimensional position by multilateration rather than
a bearing by triangulation, using one of the standard closed-form range-difference estimators
[smith1987closedform, chan1994hyperbolic, brandstein1997closedform, huang2001lcls]. We have
collected arrival-time data over a horizontal grid for this purpose and report it, with its model
and its own limitations, in the appendix. It is a secondary result and none of the conclusions of
this paper depend on it.

---

## 6. Hardware validation

Simulation establishes the shape of the design envelope. It cannot establish that a physical board
sits inside it, because the model omits everything specific to a real build: microphones that do
not match, an acquisition path with its own timing behavior, a self-noise floor, a real room, and
a source that is neither a point nor perfectly known in position. This section describes the
measurement campaign that tests those things, reports the results, and states plainly where
measurement and simulation agree and where they do not.

The methodological commitment that makes the comparison meaningful is stated first: **measured
clips pass through the same estimator functions as simulated ones.** There is no separate
implementation for real data. The evaluation script loads a clip, orients it so the microphone axis
matches the simulation's convention, and calls the identical functions used to produce every number
in Section 5, with identical parameters. Nothing is retuned per room, per source, or per distance;
the PHAT regularization constant, the interpolation factor, the feasibility tolerance, and the gate
floor are frozen at their simulation values before any measured data is evaluated. Any disagreement
between Sections 5 and 6 is therefore a property of the physical world and not of two divergent
code paths.

### 6.1 Protocol

**Array mounting.** The board is mounted horizontally on a `[MEASURE: mount type — tripod, turntable
plate]` at a height of `[MEASURE: array height above floor, m]` m, with the microphone plane level
to within `[MEASURE: levelling tolerance, degrees]` degrees. The board is mounted so that no part of
the mount lies within `[MEASURE: clearance radius, cm]` cm of the microphone plane in the horizontal
directions, to avoid reflections from the mount arriving within the direct-path window. The array
reference direction is marked physically on the board and aligned with the turntable's zero index.

**Source.** A single loudspeaker, `[MEASURE: loudspeaker model and driver diameter]`, is mounted on
a separate stand with its acoustic center at the same height as the microphone plane, to within
`[MEASURE: height matching tolerance, cm]` cm, so that the source lies in the array's horizontal
plane and the measurement is genuinely an azimuth-only problem. The loudspeaker is driven at
`[MEASURE: source level at 1 m, dB SPL]` dB SPL at 1 m, verified with a sound level meter.

**Distances.** Measurements are taken at source distances of `[MEASURE: source distances, m]`. At
least three distances are used so that the direct-to-reverberant ratio varies within each room,
with the shortest distance chosen well inside the critical distance and the longest chosen at or
beyond it. Distances are measured from the acoustic center of the loudspeaker to the centroid of
the microphone triangle with a laser rangefinder, to `[MEASURE: distance uncertainty, cm]` cm.

**Azimuth grid.** The full circle is covered in steps of `[MEASURE: azimuth step, degrees]` degrees,
giving `[MEASURE: number of azimuth positions]` positions per room and distance. Azimuth is varied
by **rotating the array on the turntable** rather than by moving the loudspeaker. This is
deliberate: rotating the array holds the source position, the room geometry, and therefore the
reflection pattern fixed, so that the azimuth sweep isolates the array's directional behavior
rather than convolving it with a changing set of early reflections. It also makes the ground-truth
angle a turntable reading rather than a distance measurement, which is far more precise. The array
centroid is aligned to the rotation axis to within `[MEASURE: centering error, mm]` mm.

**Rooms.** At least two rooms with contrasting acoustics are used: a damped room with
RT60 = `[MEASURE: RT60 of the damped room, s]` s and a live room with
RT60 = `[MEASURE: RT60 of the live room, s]` s, with dimensions
`[MEASURE: damped room dimensions, m]` and `[MEASURE: live room dimensions, m]` respectively. The
pair is chosen to bracket the range over which the simulation predicts a strong effect, so that the
measured reverberation floor can be compared with the simulated one at two separated points rather
than one.

**RT60 estimation.** Reverberation time is estimated from measured room impulse responses rather
than from the Sabine formula, so that the reported RT60 is a property of the actual room. At each
of `[MEASURE: number of RIR measurement positions]` source-receiver positions we record the room's
response to an exponential sine sweep, deconvolve it to obtain the impulse response, and apply
Schroeder backward integration to the squared impulse response; RT60 is taken from the slope of the
decay curve over the `[MEASURE: decay evaluation range, e.g. -5 to -25 dB]` range, extrapolated to
60 dB [kuttruff_roomacoustics]. We report the mean and spread across positions,
`[VAL: measured RT60 per room, mean and spread across positions and octave bands]`, and the
octave-band values from 250 Hz to 4 kHz, since the source band spans a range over which absorption
is not flat. `[FIG: measured energy decay curves and octave-band RT60 for both rooms]`

**Source signals.** Three signals are used at every position. Band-limited Gaussian noise over
300–3400 Hz matches the simulated source exactly and is the primary signal for the
accuracy comparison. Recorded speech from `[MEASURE: speech corpus or recording used]` tests
behavior under a non-stationary source with silent intervals, which is the realistic case for the
motivating applications. An exponential sine sweep supplies the impulse responses used for the
RT60 estimate above and for the direct-to-reverberant ratio at each position. Each signal is
recorded for `[MEASURE: clip duration, s]` s at each position, yielding
`[MEASURE: frames per position]` non-overlapping frames per position and per signal, which is the
number available to the temporal accumulator.

**Ground-truth uncertainty.** We give an explicit budget rather than a single assertion. Three
terms contribute: the turntable index resolution, `[MEASURE: turntable resolution, degrees]`
degrees; the angular error induced by the offset between the array centroid and the rotation axis,
which at a centering error e and a source distance d contributes approximately arctan(e/d), giving
`[MEASURE: centering-induced angular error at the shortest distance, degrees]` degrees at the
shortest distance used; and the uncertainty in locating the loudspeaker's acoustic center,
`[MEASURE: acoustic-center-induced angular error, degrees]` degrees. Combining these in quadrature
gives a ground-truth azimuth uncertainty of `[MEASURE: total ground-truth uncertainty, degrees]`
degrees. This figure bounds what the campaign can resolve: measured errors below it are not
interpretable, which is the relevant caveat when comparing against simulated sub-degree accumulated
results.

**Labeling and evaluation.** Every clip is named with its ground-truth azimuth encoded in the
filename, so that the ground truth travels with the data and cannot be reassociated by mistake
during analysis. Evaluation reports median, 90th-percentile, and RMSE per estimator, per room, per
distance, and per source signal, and produces a measured error CDF directly overlayable on the
simulated one.

**Acquisition adequacy check, performed before any accuracy analysis.** Because a
direction-of-arrival result computed from a recording that cannot represent the delay would be
meaningless rather than merely noisy, every dataset is screened against three necessary conditions
before it is evaluated, and datasets that fail are excluded and reported as excluded. The
conditions are: (i) the sample period must be small compared with the maximum physical delay d/c
on the array, so that distinct source directions map to distinct lags — as a working criterion we
require at least ten samples across the full admissible delay range, which for the nominal
geometry means a sample rate in the tens of kilohertz; (ii) each clip must contain at least one
complete snapshot of N samples, and enough snapshots to exercise the accumulator; and (iii) the
three channels must be time-aligned by construction, or their fixed offset must be measured, per
the calibration of Section 3.6. We report the measured values of all three for every dataset used
`[VAL: per-dataset sample rate, clip length in samples and seconds, channel count, and
simultaneity of sampling]`, so that the reader can verify the screen rather than take it on trust.

### 6.2 Measured accuracy

We report this subsection in two parts, and the division is deliberate. Section 6.2.1 states which
of the recordings in hand passed the adequacy screen of Section 6.1 and are therefore admissible
for an accuracy claim. Section 6.2.2 reports the accuracy of the admissible data. Keeping the two
apart means that a shortfall in the recordings is reported as a finding about the acquisition
rather than absorbed into an accuracy number that the data cannot support.

#### 6.2.1 Which recordings support an accuracy claim

`[VAL: for each dataset — sample rate, samples per clip, channel count, number of labeled
azimuths, and pass or fail against each of the three adequacy conditions of Section 6.1]`

The preliminary three-channel bench set consists of 25 recordings labeled with source positions.
Each contains `[VAL: samples per clip in the seed dataset]` samples per channel at
`[VAL: sample rate of the seed dataset, if recoverable]`, and the files carry
`[VAL: whether the seed clips carry sample timestamps or a stated sample rate]`. Against the
adequacy conditions this gives `[VAL: pass or fail per condition for the seed dataset]`.

If, as preliminary inspection suggests, these clips are both far too short and sampled far too
slowly for the aperture, then the correct statement is the following one and we make it plainly:
**the recordings presently available cannot resolve time differences of arrival on this array, and
no direction-of-arrival accuracy can honestly be computed from them.** The arithmetic is not
marginal. The whole admissible delay range on a pair is d/c, which for a centimeter-class baseline
is on the order of one to three hundred microseconds; a sample period of a millisecond is several
times that entire range, so every source direction in the plane produces the same integer lag and
the cross-correlation carries no directional information at all. A clip of a few tens of samples
is likewise shorter than the shortest snapshot characterized anywhere in Section 5.6 by more than
an order of magnitude, and too short to form a usable cross-correlation regardless of rate. No
choice of estimator, interpolation factor, or post-processing recovers information that was never
sampled. Such recordings remain useful for the acquisition-path checks of Section 3.6 — DC offset,
per-channel level, relative gain — and we use them for exactly that and nothing more.

Reporting this outcome, rather than filling the gap, is a deliberate choice. A three-microphone
localizer is easy to make look accurate by evaluating it on data that cannot contradict it, and
the resulting number would not be a measurement of anything.

**Acquisition required for a valid campaign.** The screen also specifies what a sufficient
recording is, and we state it in a form another group can implement:

| Requirement | Value |
|---|---|
| Sample rate per channel | at least `[MEASURE: minimum adequate sample rate, kHz]` kHz, giving at least ten samples across the full d/c delay range |
| Channels | 3, sampled simultaneously on a common clock, or with a measured fixed offset |
| Clip length | at least `[MEASURE: minimum clip length, s]` s, giving at least 32 non-overlapping snapshots of N samples so the accumulator can be exercised to T = 32 |
| Bit depth | `[MEASURE: minimum adequate bit depth, bits]` bits, sufficient that quantization sits below the acoustic noise floor of Section 3.6 |
| Labeling | ground-truth azimuth encoded in the filename, plus room, distance, and source-signal identifiers |
| Metadata | stated sample rate and, where the capture is not continuous, per-sample or per-block timestamps |
| Coverage | the full azimuth grid, at least two rooms, and at least three distances per room, as specified in Section 6.1 |

#### 6.2.2 Accuracy of the admissible data

The results below are computed from `[VAL: which datasets passed the screen and are used here]`.
If no dataset passes, this subsection reports that fact and the paper's hardware claim is limited
to the platform characterization of Section 3.6 and the on-device timing of Section 6.3, with the
localization results standing as simulation only — a limitation we would state in Section 7 and in
the abstract rather than obscure.

**Table 7.** Measured angular error in degrees by estimator and room, single frame, band-limited
noise source at `[MEASURE: reference distance, m]` m.
`[VAL: measured per-estimator median / p90 / RMSE, damped room]`
`[VAL: measured per-estimator median / p90 / RMSE, live room]`
`[VAL: number of clips and frames contributing to each cell]`

| Estimator | Damped room, median / p90 / RMSE | Live room, median / p90 / RMSE |
|---|---|---|
| Proposed (gated) | `[VAL]` | `[VAL]` |
| GCC-PHAT | `[VAL]` | `[VAL]` |
| SRP-PHAT | `[VAL]` | `[VAL]` |
| MUSIC | `[VAL]` | `[VAL]` |

We measured a single-frame median error of `[VAL: measured single-frame median error, damped room,
deg]` degrees in the damped room and `[VAL: measured single-frame median error, live room, deg]`
degrees in the live room, against simulated values of 2.2 and roughly 4 to 5 degrees at comparable
reverberation times (Table 2). The measured error CDF is shown overlaid on the simulated CDF at the
matching SNR in Fig. `fig_real_error_cdf.png`; the two curves `[VAL: qualitative statement of
agreement between measured and simulated error CDFs, with the vertical separation at the median and
at the 90th percentile]`.

We also report accuracy as a function of the two protocol variables that simulation could not
capture. Across source distance, the measured median error is `[VAL: measured median error versus
source distance, per room]`, which tests the direct-to-reverberant dependence directly. Across
source signal type, the measured median error for speech is `[VAL: measured median error for the
speech source, per room]` against `[VAL: measured median error for the noise source, per room]` for
band-limited noise; speech is expected to be worse because its silent intervals contain frames with
no source energy at all, and we report `[VAL: fraction of speech frames rejected or producing
low-confidence estimates]` as the fraction of frames in which that occurred.
`[FIG: measured error versus azimuth, both rooms, showing any directional structure]`

**Measured temporal accumulation.** The central claim of the paper is tested on the measured clips
by accumulating consecutive frames from each stationary recording and evaluating the accumulated
estimate against the same ground truth.
`[VAL: measured RMSE versus accumulated frames T for T = 1, 2, 4, 8, 16, 32, per room]`
`[FIG: measured accumulation curve with the 1/sqrt(T) reference and the simulated curve overlaid]`
Specifically, we measured `[VAL: measured single-frame RMSE, deg]` degrees at T = 1 falling to
`[VAL: measured RMSE at T = 32, deg]` degrees at T = 32 in the damped room, against a 1/sqrt(T)
prediction of `[VAL: 1/sqrt(T) prediction anchored at the measured T = 1 value, deg]` degrees; in
the live room the curve flattens at `[VAL: measured accumulated RMSE floor, live room, deg]`
degrees, to be compared with the simulated floors of 2.14 to 2.60 degrees over RT60 from 0.15 to
0.60 s. The measured floor is the number that determines whether the simulated bias-floor account
survives contact with a real room, and we report it whichever way it falls.

Every number in this subsection comes from recordings that passed the adequacy screen of
Section 6.2.1, and the count of clips and frames behind each cell is reported with it, so that the
weight of evidence behind each figure is visible.

### 6.3 Measured on-device cost

Per-estimate latency was measured on the ESP32-S3 itself by reading the hardware timer immediately
before and after the estimator call and logging the difference for
`[MEASURE: number of timed estimates]` consecutive estimates during normal operation. We report the
distribution rather than a single figure, because the tail is what determines whether frames are
dropped.

**Table 8.** Measured on-device per-estimate latency, ESP32-S3 at
`[MEASURE: CPU clock, MHz]` MHz.

| Quantity | Value |
|---|---|
| Mean | `[MEASURE: mean latency, ms]` |
| Median | `[MEASURE: median latency, ms]` |
| 95th percentile | `[MEASURE: p95 latency, ms]` |
| Maximum | `[MEASURE: maximum latency, ms]` |
| Snapshot duration | `[MEASURE: snapshot duration, ms]` |
| Real-time budget used (mean) | `[MEASURE: mean latency as a percentage of the snapshot duration]` |
| Real-time budget used (p95) | `[MEASURE: p95 latency as a percentage of the snapshot duration]` |

The system is real-time if the per-estimate latency stays below the snapshot duration, since a new
frame arrives every snapshot period; the appropriate figure to check is the 95th percentile or the
maximum, not the mean. On this build the measured margin is `[MEASURE: real-time margin, ms]` ms at
the 95th percentile, and `[MEASURE: number of frames dropped during the timing run]` frames were
dropped over the timing run.

We also report the cost of the temporal stage separately, because it is the part of the method that
is claimed to be nearly free: accumulating one frame's estimate into the running circular mean
takes `[MEASURE: per-frame accumulator latency, microseconds]` microseconds and the accumulator
state occupies `[MEASURE: accumulator state size, bytes]` bytes irrespective of T. Total resource
use during operation is `[MEASURE: peak SRAM footprint, kB]` kB of SRAM and
`[MEASURE: sustained CPU load, percent]` percent of one core.

We note explicitly that these are the first measured timing figures for this system. Earlier
internal documentation of this project circulated a per-estimate figure that was never measured on
the device and that is not supported by any data in this or any other campaign. It should be
regarded as superseded by Table 8, and it should not be cited. We record this because a plausible
but unmeasured number, once repeated, is difficult to withdraw.

### 6.4 Simulation versus measurement

This subsection states where the model held and where it did not. Both outcomes are reported in the
same voice, because the value of a simulation study is in knowing which of its predictions
transfer.

**Where they agree.** `[VAL: list of quantities in which measured and simulated values agree, with
the numerical comparison for each — expected candidates are the ordering of the estimators, the
single-frame median error in the damped room, the direction of the reverberation effect, and the
initial slope of the accumulation curve]`

**Where they disagree.** `[VAL: list of quantities in which measured and simulated values differ,
with the magnitude and sign of each difference]`

**Whether the measured error sits at the predicted floor.** The specific quantitative test of the
paper's central account is whether the measured accumulated error in each room stops falling at the
level the bias decomposition predicts for that room's measured RT60. We measured an accumulated
floor of `[VAL: measured accumulated floor, per room, deg]` against a simulated floor of
`[VAL: simulated floor interpolated to the measured RT60 of each room, deg]`, a discrepancy of
`[VAL: floor discrepancy, deg]`. `[VAL: interpretation — whether the discrepancy is within the
ground-truth uncertainty of Section 6.1, and if not, which of the error sources below is the
leading candidate]`

Whatever the outcome, the following mechanisms are present in the measured system and absent from
the simulation, and they are the candidate explanations for any excess measured error. We list them
with the measurement that quantifies each, so that the account is testable rather than rhetorical.

*Inter-channel gain and phase mismatch.* Microphones from the same reel differ in sensitivity, and
the analog or digital path adds its own frequency-dependent phase. A frequency-dependent phase
difference between channels is indistinguishable, to a cross-correlator, from a delay, and
therefore appears directly as an azimuth bias. The calibration dataset of Section 3.6 quantifies
this as `[VAL: inter-channel gain mismatch, dB]` and `[VAL: inter-channel delay offset per pair,
microseconds]`; converting the latter to an equivalent azimuth error on the measured baseline gives
`[VAL: azimuth bias equivalent to the measured inter-channel delay offset, degrees]`.

*Acquisition timing.* A digital I2S array samples all three channels on a common bit clock, so
there is no inter-channel offset by construction. A multiplexed converter that visits the channels
in sequence does have one, and it adds to every TDOA and produces a systematic azimuth rotation
rather than random error. Given the signal-path ambiguity of Section 3.1 this is not something to
assume either way: the acquisition used for the reported clips is `[MEASURE: confirm simultaneous
I2S versus multiplexed SAR sampling for each dataset]` and the measured fixed offset is
`[VAL: measured fixed inter-channel timing offset, microseconds]`. Separately from the offset,
because all three channels derive from the same oscillator there is no relative clock *drift*
between channels within a clip, and drift between the device and the ground-truth timeline does
not affect a TDOA estimator. We distinguish the two because the fixed offset does matter and the
drift does not.

*Self-noise.* The measured idle floor of `[VAL: measured idle noise floor, ADC LSB RMS, per
channel]` sets the SNR that the array actually achieves at a given source level and distance, and
therefore locates the measured points on the horizontal axis of Section 5.2. We report the measured
SNR at each protocol distance as `[VAL: measured SNR per distance and room, dB]`, so that measured
and simulated points are compared at matched SNR rather than at nominal SNR.

*Near-field curvature.* At the shortest protocol distance the far-field assumption of Section 4.1 is
weakest. The plane-wave model's delay error grows as the source approaches, and it produces a
distance-dependent bias rather than added variance. Whether this is visible in the measured
distance sweep is reported as `[VAL: measured azimuth bias versus source distance]`.

*Diffraction and shadowing.* The microphones are mounted on a finite board with components on it,
so for directions where the board lies between a microphone and the source there is shadowing and
diffraction that the free-space model omits, and it is direction-dependent. The measured
error-versus-azimuth curve is the diagnostic: a free-space array should show no strong azimuthal
structure, as the simulated accuracy matrix of Section 5.2 does, while a shadowed one should show
lobes at the directions where each microphone is occluded. `[VAL: measured azimuthal structure of
the error, and whether it is consistent with board shadowing]`

*Quantization and dynamic range.* At `[MEASURE: sample word length, bits]` bits, and after any DC
pedestal is accounted for, the usable dynamic range is `[MEASURE: usable dynamic range, dB]` dB.
This sets a lower bound on the achievable SNR at low source levels and is the reason we report
measured rather than nominal SNR above. It is also the quantity most affected by the signal-path
question of Section 3.1: a 24-bit digital microphone stream and a 12-bit converted analog stream
are not interchangeable here, and results from the two are reported separately rather than
pooled.

*Room and source realism.* The simulated room has rigid rectangular geometry, frequency-independent
uniform wall absorption, and an omnidirectional point source, none of which is true of the
measurement rooms or the loudspeaker. The image-source model is known to be an idealization
[allen1979image, habets2006rir]; the octave-band RT60 spread reported in Section 6.1 is the direct
evidence of the frequency-dependence that the model omits. We would expect this to make the
measured reverberation floor differ from the simulated one in magnitude while preserving its
existence, and the measured floor above is the test of that expectation.

Finally, one asymmetry deserves naming. SRP-PHAT and MUSIC are given the exact array geometry in
simulation, and on hardware they are given the measured geometry, which carries the uncertainty of
Section 3.2 and the phase mismatch quantified above. MUSIC depends on the array manifold most
sharply of the four estimators, so if its measured accuracy degrades relative to simulation by more
than the others do, manifold error is the expected cause rather than anything about reverberation.
`[VAL: measured degradation of each estimator relative to its simulated value at matched SNR and
RT60]`
