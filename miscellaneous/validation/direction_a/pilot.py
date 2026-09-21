"""Paired pilot, startup diagnostic, and stochastic numerical refinement."""
from dataclasses import replace,asdict
from itertools import product
import csv,json,time,resource
import numpy as np
from scipy.signal import fftconvolve
from .common import OUT,EstimatorConfig,wrapped_error,save_json,source_hashes
from .room import build_rirs,positions,acquisition_filter
from .recording import inputs,render_record
from .protocol import scene,descriptors,VARIANTS
from .estimator import estimate


def legacy_reset(h,record,fs):
    # Same source/noise samples inside each frame; discard all preceding history.
    frames=record['source'][record['prefix']:].reshape(-1,2048)
    y=np.stack([np.stack([fftconvolve(x,v)[:2048] for v in h]) for x in frames])
    y=acquisition_filter(y,fs)
    return y+record['noise'].reshape(3,-1,2048).transpose(1,0,2)


def run():
    start=time.perf_counter();rows=[];numerical=[];acoustics=[];timing=[];evals=0
    folder=OUT/'results/pilot';folder.mkdir(parents=True,exist_ok=True)
    for room,(placement,rt),angle in product(range(3),((0,0),(1,2)),(37.37,217.37)):
        cfg=scene(room,placement,rt,angle)
        tag=f'r{room}p{placement}t{rt}a{angle}'
        t=time.perf_counter();h,info=build_rirs(cfg);d,_=build_rirs(replace(cfg,reflections=False))
        qh,_=build_rirs(replace(cfg,arrival_mode='rounded'));qd,_=build_rirs(replace(cfg,arrival_mode='rounded',reflections=False))
        timing.append({'scene':tag,'four_rirs_s':time.perf_counter()-t})
        metrics,db=descriptors(cfg,h,d);acoustics.append({'scene':tag,'config':asdict(cfg),**metrics})
        _,_,xy=positions(cfg)
        fine,_=build_rirs(replace(cfg,oversample=64));more,_=build_rirs(replace(cfg,image_extent=84))
        for record_id,snr in product(range(2),(10.,float('inf'))):
            record=inputs(cfg,d,32,record_id,snr,'pilot_v2')
            t=time.perf_counter()
            base_y=render_record(h,record,cfg.fs);base=estimate(base_y,xy)
            for label,fh,ec in [('propagation64',fine,EstimatorConfig()),('extent84',more,EstimatorConfig()),('correlation16',h,EstimatorConfig(interp=16))]:
                fy=base_y if label=='correlation16' else render_record(fh,record,cfg.fs)
                estimates=estimate(fy,xy,ec);dif=wrapped_error(estimates,base)
                numerical.append({'scene':tag,'record_id':record_id,'snr_db':snr if np.isfinite(snr) else 'inf',
                    'refinement':label,'max_angle_difference_deg':float(np.max(np.abs(dif))),
                    'rms_difference_deg':float(np.sqrt(np.mean(dif*dif))),
                    'above_005_count':int(np.sum(np.abs(dif)>.05))})
                evals+=32
            for variant in VARIANTS+('F_L_R',):
                a,s,r=variant.split('_');hh={('F','R'):h,('F','D'):d,('Q','R'):qh,('Q','D'):qd}[(a,r)]
                y=legacy_reset(hh,record,cfg.fs) if s=='L' else render_record(hh,record,cfg.fs,startup=s=='O')
                estimates=estimate(y,xy);err=wrapped_error(estimates,cfg.theta_deg);evals+=len(err)
                for k,e in enumerate(err):rows.append({'scene':tag,'record_id':record_id,'snr_db':snr,
                    'variant':variant,'frame':k,'theta_true':cfg.theta_deg,'error_deg':float(e)})
            timing.append({'scene':tag,'record_id':record_id,'snr_db':snr if np.isfinite(snr) else 'inf','paired_record_s':time.perf_counter()-t})
        print(f'pilot {tag} complete: T20={metrics["t20_s"]:.3f} s, DRR={metrics["component_drr_db"]:.2f} dB',flush=True)
    p=folder/'frame_trials.csv'
    with p.open('w') as f:
        w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
    summary={'elapsed_seconds':time.perf_counter()-start,'peak_memory_mib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,
        'primary_and_refined_evaluations':evals,'frame_rows':len(rows),'result_bytes':p.stat().st_size,
        'numerical_refinements':numerical,'timing':timing,'acoustics':acoustics,'source_hashes':source_hashes()}
    save_json('results/pilot/summary.json',summary)
    for label in ('propagation64','extent84','correlation16'):
        sub=[r for r in numerical if r['refinement']==label]
        print(label,max(r['max_angle_difference_deg'] for r in sub),sum(r['above_005_count'] for r in sub),flush=True)
    print(json.dumps({k:summary[k] for k in ('elapsed_seconds','peak_memory_mib','primary_and_refined_evaluations','frame_rows')},indent=2),flush=True)


if __name__=='__main__':run()
