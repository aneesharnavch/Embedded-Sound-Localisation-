"""Deterministic band-limited verification signals and causal FIR delays."""
import numpy as np
from scipy.signal import fftconvolve
from .common import rng_for


def tone_parameters(seed=11, count=96, band=(300, 3400)):
    r = rng_for('verification_multitone', seed)
    frequencies = r.uniform(band[0], band[1], count)
    phases = r.uniform(-np.pi, np.pi, count)
    amplitudes = np.ones(count) * np.sqrt(2/count)
    return frequencies, amplitudes, phases


def harmonic_signal(t, parameters):
    f, a, p = parameters
    t = np.asarray(t)
    out = np.zeros(t.shape)
    # Independent of the sampled FIR path; exact continuous harmonic expression.
    for frequency, amplitude, phase in zip(f, a, p):
        out += amplitude * np.cos(2*np.pi*frequency*t + phase)
    return out


def delay_kernel(delay_samples, half_width=32, beta=8.6):
    center = int(np.rint(delay_samples))
    offsets = np.arange(-half_width, half_width+1)
    h = np.sinc(offsets - (delay_samples-center)) * np.kaiser(2*half_width+1, beta)
    h /= h.sum()
    return center-half_width, h


def fir_delay(x, delay_samples, half_width=32):
    offset, h = delay_kernel(delay_samples, half_width)
    convolution = fftconvolve(np.asarray(x), h)
    indices = np.arange(len(x)) - offset
    good = (indices >= 0) & (indices < len(convolution))
    out = np.zeros(len(x))
    out[good] = convolution[indices[good]]
    return out


def direct_waveforms(arrivals, fs, samples, parameters, half_width=32, gains=None):
    arrivals = np.asarray(arrivals)
    if half_width > 256:
        raise ValueError('Increase the fixed verification guard before this refinement.')
    # Fixed physical observation time across kernel AND sampling-rate refinements.
    start_s = max(.125, np.ceil((max(0.0, arrivals.max())+.05)*8)/8)
    start = int(round(start_s*fs))
    n = start + samples + 512
    t = np.arange(n)/fs
    source = harmonic_signal(t, parameters)
    oracle = np.stack([harmonic_signal(t[start:start+samples] - tau, parameters)
                       for tau in arrivals])
    fir = np.stack([fir_delay(source, tau*fs, half_width)[start:start+samples]
                    for tau in arrivals])
    if gains is not None:
        oracle *= np.asarray(gains)[:, None]
        fir *= np.asarray(gains)[:, None]
    return oracle, fir
