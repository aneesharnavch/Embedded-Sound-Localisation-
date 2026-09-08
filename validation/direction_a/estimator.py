"""Physically bounded band-limited GCC-PHAT and uniform planar least squares."""
from dataclasses import asdict
import numpy as np
from scipy.fft import rfft, irfft, next_fast_len
from .common import EstimatorConfig, pairs, solve_pairs


def estimate(x, mic_xy, config=EstimatorConfig(), return_delays=False):
    """Input (..., microphones, samples); output azimuth in degrees.

    Each channel is mean-removed and multiplied by the same symmetric Hann
    window. Cross spectra use X_i conj(X_j), so t_ij=t_i-t_j and A u=-c t.
    Only lags inside the geometric interval are candidates. A quadratic peak
    refinement uses neighboring correlation samples and is clipped to that
    interval. Every pair has equal weight in the least-squares direction solve.
    """
    x = np.asarray(x, dtype=np.float64)
    if x.shape[-2] != len(mic_xy):
        raise ValueError('Channel count does not match geometry.')
    n = x.shape[-1]
    if n < 8 or config.band[1] >= config.fs / 2:
        raise ValueError('Invalid frame length or analysis band.')
    if config.mean_remove:
        x = x - x.mean(axis=-1, keepdims=True)
    if config.window == 'symmetric_hann':
        x = x * np.hanning(n)
    elif config.window != 'rectangular':
        raise ValueError(config.window)
    nfft = next_fast_len(2*n)
    ft = rfft(x, n=nfft, axis=-1)
    f = np.fft.rfftfreq(nfft, 1/config.fs)
    mask = (f >= config.band[0]) & (f <= config.band[1])
    estimates = []
    for i, j in pairs(len(mic_xy)):
        cross = ft[..., i, :] * np.conj(ft[..., j, :])
        mag = np.abs(cross)
        floor = config.relative_floor * mag.max(axis=-1, keepdims=True) + config.absolute_floor
        weighted = cross / np.maximum(mag, floor)
        weighted[..., ~mask] = 0
        cc = irfft(weighted, n=config.interp*nfft, axis=-1)
        bound = np.linalg.norm(np.asarray(mic_xy[i]) - mic_xy[j]) / config.sound_speed
        last = int(np.floor(bound * config.fs * config.interp))
        lag_indices = np.arange(-last, last+1)
        indices = lag_indices % cc.shape[-1]
        local = cc[..., indices]
        peak = np.argmax(local, axis=-1)
        discrete = lag_indices[peak]
        sample = discrete % cc.shape[-1]
        delta = np.zeros_like(discrete, dtype=float)
        if config.parabolic:
            v0 = np.take_along_axis(cc, sample[..., None], axis=-1)[..., 0]
            vm = np.take_along_axis(cc, ((sample-1) % cc.shape[-1])[..., None], axis=-1)[..., 0]
            vp = np.take_along_axis(cc, ((sample+1) % cc.shape[-1])[..., None], axis=-1)[..., 0]
            denom = vm - 2*v0 + vp
            np.divide(0.5*(vm-vp), denom, out=delta, where=denom < -1e-20)
            # At the feasible boundary the closest unrestricted grid point may
            # lie outside the candidate interval; allow one interpolation step.
            delta = np.clip(delta, -1.0, 1.0)
        delay = np.clip((discrete+delta)/(config.fs*config.interp), -bound, bound)
        estimates.append(delay)
    delays = np.stack(estimates, axis=-1)
    result = solve_pairs(delays, np.asarray(mic_xy), config.sound_speed)
    return (result, delays) if return_delays else result
