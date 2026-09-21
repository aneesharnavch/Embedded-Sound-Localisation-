"""Explicit shoebox image-source model with convergent fractional deposition.

Pressure reflection coefficients are frequency-independent. This is an ideal
specular model, not a measured room. The image-domain extent and path-duration
cutoff are explicit and independently refined during verification.
"""
from dataclasses import dataclass,asdict
from itertools import product
import numpy as np
from scipy.signal import firwin,resample_poly,butter,sosfilt
from .common import C,triangle


@dataclass(frozen=True)
class RoomConfig:
    dimensions: tuple[float,float,float] = (6.,5.,3.)
    array_fraction: tuple[float,float,float] = (.5,.5,.5)
    nominal_rt60: float = .3
    theta_deg: float = 37.37
    distance_m: float = 1.5
    radius_m: float = .05
    rotation_deg: float = 0.
    fs: int = 48000
    image_extent: int = 12
    path_duration_s: float = .9
    oversample: int = 16
    half_width: int = 32
    arrival_mode: str = 'fractional'
    reflections: bool = True
    # Relative absorption multipliers, ordered x-low,x-high,y-low,y-high,z-low,z-high.
    absorption_multipliers: tuple[float,...] = (1.,1.,1.,1.,1.,1.)
    non_equilateral: bool = False


def positions(config):
    room=np.asarray(config.dimensions);center=room*np.asarray(config.array_fraction)
    xy=triangle(config.radius_m,config.rotation_deg)
    if config.non_equilateral:
        xy=xy.copy();xy[0,1]*=.65
        xy-=xy.mean(axis=0)
    microphones=center+np.column_stack((xy,np.zeros(3)))
    th=np.deg2rad(config.theta_deg)
    source=center+config.distance_m*np.array([np.cos(th),np.sin(th),0.])
    if np.any(microphones<=0) or np.any(microphones>=room) or np.any(source<=0) or np.any(source>=room):
        raise ValueError('All coordinates must lie strictly inside the room.')
    return microphones,source,xy


def reflection_coefficients(config):
    lx,ly,lz=config.dimensions
    areas=np.array([ly*lz,ly*lz,lx*lz,lx*lz,lx*ly,lx*ly])
    base=.161*lx*ly*lz/(areas.sum()*config.nominal_rt60)
    weights=np.asarray(config.absorption_multipliers)
    weights=weights/(np.sum(areas*weights)/areas.sum())
    alpha=np.clip(base*weights,.0001,.99)
    return np.sqrt(1-alpha)


def paths(config):
    """Yield (microphone, arrival seconds, pressure gains) in parity chunks."""
    microphones,source,_=positions(config)
    if not config.reflections:
        for i,mic in enumerate(microphones):
            distance=np.linalg.norm(source-mic)
            yield i,np.array([distance/C]),np.array([1/(4*np.pi*distance)])
        return
    r=np.arange(-config.image_extent,config.image_extent+1)
    indices=np.stack(np.meshgrid(r,r,r,indexing='ij'),axis=-1).reshape(-1,3)
    beta=reflection_coefficients(config)
    room=np.asarray(config.dimensions)
    for parity in product((0,1),repeat=3):
        p=np.asarray(parity)
        images=2*indices*room+(1-2*p)*source
        low=np.abs(indices-p);high=np.abs(indices)
        pressure=np.prod(beta[0::2]**low * beta[1::2]**high,axis=1)
        for i,mic in enumerate(microphones):
            distance=np.linalg.norm(images-mic,axis=1)
            keep=distance<=C*config.path_duration_s
            yield i,distance[keep]/C,pressure[keep]/(4*np.pi*distance[keep])


def build_rirs(config):
    microphones,source,_=positions(config)
    shortest=np.linalg.norm(microphones-source,axis=1).min()/C
    if shortest*config.fs<=config.half_width:
        raise ValueError('Direct arrival is inside the fractional-kernel head support; add a common guard delay.')
    n=int(np.ceil(config.path_duration_s*config.fs))+config.half_width+2
    counts=np.zeros(3,dtype=int)
    if config.arrival_mode=='rounded':
        out=np.zeros((3,n))
        for i,t,g in paths(config):
            q=np.rint(t*config.fs).astype(int)
            out[i]+=np.bincount(q,weights=g,minlength=n)[:n];counts[i]+=len(t)
    elif config.arrival_mode=='fractional':
        p=config.oversample
        if p<2:raise ValueError('Fractional grid oversampling must be at least two.')
        high=np.zeros((3,n*p))
        for i,t,g in paths(config):
            position=t*config.fs*p
            lower=np.floor(position).astype(int);frac=position-lower
            high[i]+=np.bincount(lower,weights=g*p*(1-frac),minlength=n*p)[:n*p]
            high[i]+=np.bincount(lower+1,weights=g*p*frac,minlength=n*p)[:n*p]
            counts[i]+=len(t)
        kernel=firwin(2*config.half_width*p+1,1/p,window=('kaiser',8.6))
        out=resample_poly(high,1,p,axis=-1,window=kernel)
    else:raise ValueError(config.arrival_mode)
    return out,{'path_counts':counts.tolist(),'reflection_coefficients':reflection_coefficients(config).tolist(),
                'samples':n,'config':asdict(config)}


def acquisition_filter(x,fs):
    sos=butter(4,[300.,3400.],btype='bandpass',fs=fs,output='sos')
    return sosfilt(sos,np.asarray(x),axis=-1)


def room_metrics(h,fs):
    filtered=acquisition_filter(h,fs)
    energy=np.sum(filtered**2,axis=0)
    edc=np.cumsum(energy[::-1])[::-1]
    db=10*np.log10(np.maximum(edc/edc[0],1e-30))
    t=np.arange(len(db))/fs
    result={}
    for name,top,bottom in [('edt_s',0.,-10.),('t20_s',-5.,-25.),('t30_s',-5.,-35.)]:
        selected=(db<=top)&(db>=bottom)
        if selected.sum()<20:
            result[name]=None;result[name+'_r2']=None;continue
        slope,intercept=np.polyfit(t[selected],db[selected],1)
        predicted=slope*t[selected]+intercept
        r2=1-np.sum((db[selected]-predicted)**2)/np.sum((db[selected]-db[selected].mean())**2)
        result[name]=float(-60/slope);result[name+'_r2']=float(r2)
    result['band_energy']=float(energy.sum())
    return result,db
