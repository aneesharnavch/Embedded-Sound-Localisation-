"""Internal-review check: refine image domain and response duration together."""
from dataclasses import replace
from itertools import product
import concurrent.futures,json,time
import numpy as np
from .common import OUT,wrapped_error,save_json,source_hashes
from .room import build_rirs,positions,room_metrics
from .protocol import scene,ANGLES
from .recording import inputs,render_record
from .estimator import estimate
from .verify_room import transfer


def check(job):
    room,aid=job;cfg=scene(room,1,2,ANGLES[aid]);tag=f'r{room}p1t2a{aid:02d}'
    cfg=replace(cfg,image_extent=76,path_duration_s=1.2,oversample=32)
    short=build_rirs(cfg)[0]
    longer=replace(cfg,image_extent=96,path_duration_s=1.5)
    long,info=build_rirs(longer);d,_=build_rirs(replace(longer,reflections=False))
    hs=transfer(short);hl=transfer(long);_,_,xy=positions(cfg)
    spectral=float(np.linalg.norm(hl-hs)/np.linalg.norm(hl))
    ms,_=room_metrics(short,cfg.fs);ml,_=room_metrics(long,cfg.fs)
    deltas=[];mse_changes=[]
    for rid in range(5):
        record=inputs(cfg,d,32,rid,10.,'joint_duration_review_v2')
        a=estimate(render_record(short,record,cfg.fs),xy);b=estimate(render_record(long,record,cfg.fs),xy)
        deltas.extend(abs(wrapped_error(b,a)).tolist())
        mse_changes.append(float(np.mean(wrapped_error(b,cfg.theta_deg)**2-wrapped_error(a,cfg.theta_deg)**2)))
    return {'scene_id':tag,'relative_spectrum_change':spectral,'relative_t20_change':abs(ms['t20_s']/ml['t20_s']-1),
        'max_angle_change_deg':max(deltas),'frames_above_005':sum(x>.05 for x in deltas),
        'mse_change_deg2':float(np.mean(mse_changes)),'refined_path_counts':info['path_counts'],'frames':len(deltas)}


def run():
    start=time.perf_counter()
    with concurrent.futures.ProcessPoolExecutor(max_workers=2) as p:
        result=list(p.map(check,product(range(3),(0,6))))
    summary={'status':'corrective pre-campaign numerical review','settings':'K76/T1.2/P32 -> K96/T1.5/P32 with paired inputs and enough history for both',
        'scenes':result,'elapsed_seconds':time.perf_counter()-start,'passed':all(x['relative_spectrum_change']<.001 and x['relative_t20_change']<.01 and x['frames_above_005']==0 for x in result),'source_hashes':source_hashes()}
    save_json('results/room/joint_refinement_1p2_vs1p5.json',summary);print(json.dumps(summary,indent=2),flush=True)
    if not summary['passed']:raise RuntimeError('Joint refinement failed; diagnose before finalizing.')


if __name__=='__main__':run()
