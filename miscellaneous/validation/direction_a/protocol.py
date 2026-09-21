"""Scene definitions and acoustic descriptors shared by pilot and main drivers."""
from dataclasses import asdict,replace
from itertools import product
import numpy as np
from .common import C
from .room import RoomConfig,positions,reflection_coefficients,acquisition_filter,room_metrics

ROOMS=((6.,5.,3.),(5.,4.,2.8),(8.,6.,3.2))
PLACEMENTS=((.5,.5,.5),(.6,.45,.5))
RTS=(.15,.3,.6)
ANGLES=tuple(7.37+30*k for k in range(12))
VARIANTS=tuple(f'{a}_{s}_{r}' for a,s,r in product(('F','Q'),('S','O'),('D','R')))


def scene(room,placement,rt,angle,**kwargs):
    defaults={'image_extent':76,'path_duration_s':1.2,'oversample':32}
    defaults.update(kwargs)
    return RoomConfig(dimensions=ROOMS[room],array_fraction=PLACEMENTS[placement],
        nominal_rt60=RTS[rt],theta_deg=float(angle),**defaults)


def subset(room,placement,rt):
    return (placement==0 and rt==0) or (placement==1 and rt==2)


def descriptors(config,h,direct):
    metrics,db=room_metrics(h,config.fs)
    d=acquisition_filter(direct,config.fs)
    r=acquisition_filter(h-direct,config.fs)
    metrics['component_drr_db']=float(10*np.log10(np.sum(d*d)/np.sum(r*r)))
    metrics['direct_band_energy']=float(np.sum(d*d))
    metrics['reflection_band_energy']=float(np.sum(r*r))
    metrics['component_energy_cross_term']=float(2*np.sum(d*r))
    microphones,source,_=positions(config)
    direct_distance=np.linalg.norm(source-microphones,axis=1)
    metrics['direct_arrival_s']=(direct_distance/C).tolist()
    metrics['direct_pressure_gain']=(1/(4*np.pi*direct_distance)).tolist()
    beta=reflection_coefficients(config)
    early=[]
    for axis in range(3):
        for side in range(2):
            image=source.copy()
            image[axis]=-source[axis] if side==0 else 2*config.dimensions[axis]-source[axis]
            distance=np.linalg.norm(image-microphones,axis=1)
            early.append({'wall':f'{"xyz"[axis]}_{"low" if side==0 else "high"}',
                          'arrival_s':(distance/C).tolist(),
                          'pressure_gain':(beta[2*axis+side]/(4*np.pi*distance)).tolist()})
    metrics['first_order_reflections']=early
    all_points=np.concatenate((microphones,source[None,:]),axis=0)
    metrics['minimum_wall_clearance_m']=float(np.minimum(all_points,np.asarray(config.dimensions)-all_points).min())
    return metrics,db
