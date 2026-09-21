"""Geometry-only deterministic arrival-precision bounds and independent checks."""
from itertools import product
import csv,json
import numpy as np
from .common import OUT,C,triangle,pairs,spherical_arrivals,solve_arrivals,wrapped_error,rng_for,save_json
from .reference import direction as reference_solve


def bound(theta,distance,xy,epsilon_max):
    a=np.array([xy[i]-xy[j] for i,j in pairs(len(xy))])
    incidence=np.array([[1,-1,0],[1,0,-1],[0,1,-1]])
    jacobian=-C*np.linalg.pinv(a)@incidence
    times=spherical_arrivals(theta,distance,xy)
    u=-C*np.linalg.pinv(a)@(incidence@times)
    vertices=epsilon_max*np.array(list(product((-1.,1.),repeat=3)))
    delta=vertices@jacobian.T
    rho=np.linalg.norm(delta,axis=1).max();norm=np.linalg.norm(u)
    if rho>=norm:return 180.,180.,float(rho/norm),jacobian,u
    truth=np.rad2deg(np.arctan2(u[1],u[0]))
    angles=np.rad2deg(np.arctan2((u+delta)[:,1],(u+delta)[:,0]))
    exact=float(np.max(abs(wrapped_error(angles,truth))))
    disk=float(np.rad2deg(np.arcsin(rho/norm)))
    return exact,disk,float(rho/norm),jacobian,u


def run():
    rows=[];rng=rng_for('precision_independent_v1');max_violation=-100.;checks=0
    for radius,distance,fs in product((.025,.05,.1),(.5,1.5,5.,20.),(16000,48000,96000,192000)):
        xy=triangle(radius)
        for theta in np.arange(720)*.5-179.87:
            t=spherical_arrivals(theta,distance,xy);exact=solve_arrivals(t,xy);rounded=solve_arrivals(np.rint(t*fs)/fs,xy)
            corner,disk,rho,j,u=bound(theta,distance,xy,.5/fs)
            actual=abs(float(wrapped_error(rounded,exact)))
            assert actual<=corner+1e-9
            tangent=np.array([-u[1],u[0]])/np.linalg.norm(u)
            linear=np.rad2deg(.5/fs*np.sum(abs(tangent@j))/np.linalg.norm(u))
            rows.append({'radius_m':radius,'distance_m':distance,'fs_hz':fs,'theta_deg':theta,'actual_rounding_shift_deg':actual,
                'corner_bound_deg':corner,'disk_bound_deg':disk,'linear_bound_deg':float(linear),'rho_over_u':rho})
    for case in range(600):
        radius=float(rng.uniform(.025,.1));xy=triangle(radius,float(rng.uniform(0,360)))
        if case%2:xy[0]*=.7;xy-=xy.mean(axis=0)
        theta=float(rng.uniform(-180,180));distance=float(rng.uniform(.5,20));fs=int(rng.integers(16000,192001));eps=.5/fs
        corner,disk,rho,j,u=bound(theta,distance,xy,eps)
        times=spherical_arrivals(theta,distance,xy)
        exact=reference_solve(times.tolist(),xy.tolist())
        for k in range(20):
            perturbation=rng.uniform(-eps,eps,3)
            result=reference_solve((times+perturbation).tolist(),xy.tolist())
            violation=abs(float(wrapped_error(result,exact)))-corner
            max_violation=max(max_violation,violation);checks+=1
            assert violation<1e-8
    folder=OUT/'results/precision';folder.mkdir(parents=True,exist_ok=True)
    with (folder/'criterion_trials.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
    summary={'analytical_rounding_conditions':len(rows),'independent_perturbation_checks':checks,'max_violation_deg':max_violation,
        'allowed_absolute_arrival_error_us_for_005m_radius_and_05deg_plane_tolerance':3*.05/(4*C)*np.sin(np.deg2rad(.5))*1e6,
        'domain':'ideal arrival times -> uniform planar LS; rho<norm(u); excludes waveform GCC peak selection, noise and reflections'}
    save_json('results/precision/verification_summary.json',summary);print(json.dumps(summary,indent=2))


if __name__=='__main__':run()
