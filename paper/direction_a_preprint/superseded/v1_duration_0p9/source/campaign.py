"""Frozen main campaign, atomic per-scene outputs, repeatable record identities."""
from dataclasses import asdict,replace
from itertools import product
from pathlib import Path
import argparse,concurrent.futures,csv,gzip,hashlib,json,os,time
import numpy as np
from .common import OUT,EstimatorConfig,canonical_hash,source_hashes,save_json,wrapped_error
from .room import build_rirs,positions
from .recording import inputs,render_record
from .protocol import scene,subset,descriptors,ANGLES,VARIANTS
from .estimator import estimate

DEPENDENCIES=('common.py','estimator.py','room.py','recording.py','protocol.py','campaign.py')
FIELDS=('experiment','scene_id','record_id','snr_db','variant','frame','method','theta_true','theta_est',
        'error_deg','failure_gt5','bound_pairs','config_hash','input_id')


def code_hashes():
    all_hashes=source_hashes()
    return {k:all_hashes[k] for k in DEPENDENCIES}


def digest_array(a):return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()


def jobs():return list(product(range(3),range(2),range(3),range(12)))


def run_scene(job,output=None):
    room,placement,rt,angle_id=job;cfg=scene(room,placement,rt,ANGLES[angle_id])
    tag=f'r{room}p{placement}t{rt}a{angle_id:02d}'
    folder=Path(output) if output else OUT/'results/main'
    folder.mkdir(parents=True,exist_ok=True)
    frozen=json.loads((OUT/'configs/main_protocol.json').read_text())
    if frozen['code_hashes']!=code_hashes():raise RuntimeError('Frozen numerical code differs from current source.')
    final=folder/f'{tag}.csv.gz';meta_path=folder/f'{tag}.json'
    if final.exists() and meta_path.exists():
        m=json.loads(meta_path.read_text())
        if m['protocol_hash']!=frozen['protocol_hash'] or hashlib.sha256(final.read_bytes()).hexdigest()!=m['csv_sha256']:
            raise RuntimeError(f'Existing scene {tag} has invalid provenance.')
        return {'scene':tag,'status':'reused','rows':m['rows']}
    started=time.perf_counter()
    h,info=build_rirs(cfg);d,_=build_rirs(replace(cfg,reflections=False))
    is_subset=subset(room,placement,rt)
    rirs={('F','R'):h,('F','D'):d}
    if is_subset:
        for r,ref in [('D',False),('R',True)]:rirs[('Q',r)],_=build_rirs(replace(cfg,arrival_mode='rounded',reflections=ref))
    descriptors_value,_=descriptors(cfg,h,d)
    _,_,xy=positions(cfg);pair_bounds=np.array([np.linalg.norm(xy[i]-xy[j])/343 for i,j in ((0,1),(0,2),(1,2))])
    configs={}
    for variant in VARIANTS:
        a,s,r=variant.split('_')
        configs[variant]=canonical_hash({'room':asdict(replace(cfg,arrival_mode='fractional' if a=='F' else 'rounded',reflections=r=='R')),
            'startup':s=='O','estimator':asdict(EstimatorConfig())})
    record_info=[];counts={'core':0,'attribution':0,'long_train':0,'long_holdout':0};rows=0
    temp=folder/f'{tag}.partial.csv.gz'
    with gzip.open(temp,'wt',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=FIELDS);writer.writeheader()
        def evaluate(record,record_id,snr,variant,experiment):
            nonlocal rows
            a,s,r=variant.split('_');y=render_record(rirs[(a,r)],record,cfg.fs,startup=s=='O')
            angles,delays=estimate(y,xy,return_delays=True)
            errors=wrapped_error(angles,cfg.theta_deg)
            if not np.all(np.isfinite(errors)):raise RuntimeError(f'Nonfinite estimate in {tag}')
            bounded=np.sum(np.abs(np.abs(delays)-pair_bounds)<1e-10,axis=-1)
            identity=canonical_hash({'identity':record['identity'],'snr_db':snr,'frames':len(y)})
            for k,(theta,err,bound) in enumerate(zip(angles,errors,bounded)):
                writer.writerow(dict(zip(FIELDS,(experiment,tag,record_id,snr,variant,k,'GCC-PHAT',cfg.theta_deg,
                    float(theta),float(err),int(abs(err)>5),int(bound),configs[variant],identity))))
            rows+=len(y);counts[experiment]+=len(y)
        def remember(record,record_id,snr,experiment,frames):
            record_info.append({'experiment':experiment,'record_id':record_id,'snr_db':snr,'frames':frames,
                'seed_identity':record['identity'],'input_id':canonical_hash({'identity':record['identity'],'snr_db':snr,'frames':frames}),
                'source_sha256':digest_array(record['source']),'noise_sha256':digest_array(record['noise']),
                'prefix_samples':record['prefix'],'reference_direct_band_power':record['reference_power']})
        for snr,record_id in product((0.,10.,20.),range(5)):
            record=inputs(cfg,d,32,record_id,snr,'main_v1');remember(record,record_id,snr,'core',32)
            evaluate(record,record_id,snr,'F_S_R','core')
            if is_subset and snr==10:
                for variant in VARIANTS:
                    if variant!='F_S_R':evaluate(record,record_id,snr,variant,'attribution')
        if is_subset:
            for record_id in range(10):
                experiment='long_train' if record_id<5 else 'long_holdout'
                record=inputs(cfg,d,128,record_id,10.,'long_v1');remember(record,record_id,10.,experiment,128)
                evaluate(record,record_id,10.,'F_S_R',experiment)
    temp.replace(final)
    metadata={'scene_id':tag,'indices':job,'config':asdict(cfg),'config_hashes':configs,'rir_metadata':info,
        'room_descriptors':descriptors_value,'input_records':record_info,'rows':rows,'counts':counts,
        'protocol_hash':frozen['protocol_hash'],'code_hashes':code_hashes(),
        'csv_sha256':hashlib.sha256(final.read_bytes()).hexdigest(),'elapsed_seconds':time.perf_counter()-started}
    meta_path.write_text(json.dumps(metadata,indent=2)+'\n')
    # Responses are a local speed cache, not required by the reproducibility package.
    if output is None:
        cache=OUT/'cache/rirs';cache.mkdir(parents=True,exist_ok=True)
        np.savez_compressed(cache/f'{tag}.npz',fractional_room=h,fractional_direct=d)
    return {'scene':tag,'status':'done','rows':rows,'seconds':metadata['elapsed_seconds']}


def run(workers=2):
    started=time.perf_counter();results=[]
    with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as pool:
        for result in pool.map(run_scene,jobs()):
            results.append(result);print(json.dumps({'completed_scenes':len(results),**result}),flush=True)
    summary={'scenes':len(results),'rows':sum(r['rows'] for r in results),'elapsed_seconds':time.perf_counter()-started,
        'workers':workers,'scene_results':results,'code_hashes':code_hashes()}
    save_json('results/main/run_summary.json',summary);print(json.dumps({k:v for k,v in summary.items() if k!='scene_results'}),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--workers',type=int,default=2)
    args=parser.parse_args();run(args.workers)
