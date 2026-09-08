"""Paired continuous source/noise records and causal acquisition filtering."""
from dataclasses import replace
import numpy as np
from scipy.signal import fftconvolve
from scipy.fft import rfft,irfft
from .common import rng_for,EstimatorConfig
from .room import acquisition_filter


def band_noise(n,fs,identity,band=(300.,3400.)):
    raw=rng_for(*identity).standard_normal(n)
    spectrum=rfft(raw)
    f=np.fft.rfftfreq(n,1/fs)
    spectrum[(f<band[0])|(f>band[1])]=0
    x=irfft(spectrum,n=n)
    return x/np.sqrt(np.mean(x*x))


def inputs(config,direct_rirs,frames,record_id,snr_db,experiment='main',band=(300.,3400.)):
    """Reference power uses clean direct-only, steady-state acquired signals."""
    n=frames*2048
    prefix=direct_rirs.shape[-1]+2048
    total=prefix+n
    identity=(experiment,config.dimensions,config.array_fraction,config.theta_deg,config.distance_m,
              config.radius_m,config.rotation_deg,config.non_equilateral,config.nominal_rt60,record_id)
    source=band_noise(total,config.fs,identity+('source',),band)
    direct=np.stack([fftconvolve(source,h)[:total] for h in direct_rirs])
    direct=acquisition_filter(direct,config.fs)[:,prefix:]
    power=float(np.mean(direct*direct))
    raw=rng_for(*identity,'noise',float(snr_db)).standard_normal((3,total))
    noise=acquisition_filter(raw,config.fs)[:,prefix:]
    if np.isinf(snr_db):noise*=0
    else:noise*=np.sqrt(power/(10**(snr_db/10)*np.mean(noise*noise)))
    return {'source':source,'noise':noise,'prefix':prefix,'samples':n,'reference_power':power,
            'identity':identity,'snr_db':float(snr_db)}


def render_record(rirs,record,fs,startup=False):
    source=record['source']
    if startup:
        source=source.copy();source[:record['prefix']]=0
    total=len(source)
    y=np.stack([fftconvolve(source,h)[:total] for h in rirs])
    y=acquisition_filter(y,fs)[:,record['prefix']:]
    y+=record['noise']
    return y.reshape(3,-1,2048).transpose(1,0,2)
