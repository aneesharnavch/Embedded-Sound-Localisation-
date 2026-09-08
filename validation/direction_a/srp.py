"""Continuous-delay frequency-domain SRP-PHAT with refined angular search."""
from functools import lru_cache
import numpy as np
from scipy.fft import rfft,next_fast_len
from .common import EstimatorConfig,pairs


@lru_cache(maxsize=24)
def steering(coords,n,fs,lo,hi,step,c):
    xy=np.asarray(coords).reshape(-1,2);nfft=next_fast_len(2*n)
    f=np.fft.rfftfreq(nfft,1/fs);mask=(f>=lo)&(f<=hi);f=f[mask]
    angles=np.arange(-180.,180.,step);th=np.deg2rad(angles)
    directions=np.stack([np.cos(th),np.sin(th)])
    matrices=[]
    for i,j in pairs(len(xy)):
        delay=-(xy[i]-xy[j])@directions/c
        matrices.append(np.exp(2j*np.pi*f[:,None]*delay[None,:]))
    return mask,angles,matrices


def estimate_srp(x,xy,config=EstimatorConfig(),step=.25):
    x=np.asarray(x,dtype=float);n=x.shape[-1]
    if config.mean_remove:x=x-x.mean(axis=-1,keepdims=True)
    if config.window=='symmetric_hann':x=x*np.hanning(n)
    elif config.window!='rectangular':raise ValueError(config.window)
    ft=rfft(x,n=next_fast_len(2*n),axis=-1)
    mask,angles,matrices=steering(tuple(np.asarray(xy).ravel()),n,config.fs,*config.band,float(step),config.sound_speed)
    score=np.zeros(x.shape[:-2]+(len(angles),))
    for (i,j),matrix in zip(pairs(len(xy)),matrices):
        cross=ft[...,i,:]*np.conj(ft[...,j,:]);mag=abs(cross)
        floor=config.relative_floor*mag.max(axis=-1,keepdims=True)+config.absolute_floor
        weighted=cross/np.maximum(mag,floor)
        score+=(weighted[...,mask]@matrix).real
    peak=np.argmax(score,axis=-1)
    mid=np.take_along_axis(score,peak[...,None],axis=-1)[...,0]
    left=np.take_along_axis(score,((peak-1)%len(angles))[...,None],axis=-1)[...,0]
    right=np.take_along_axis(score,((peak+1)%len(angles))[...,None],axis=-1)[...,0]
    denom=left-2*mid+right;delta=np.zeros_like(mid)
    np.divide(.5*(left-right),denom,out=delta,where=denom<-1e-20)
    return (angles[peak]+step*np.clip(delta,-.5,.5)+180)%360-180
