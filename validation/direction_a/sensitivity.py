"""Fixed sensitivity and SRP subset; no tuning to confirmatory results."""
from dataclasses import asdict,replace
from itertools import product
import csv,gzip,json,time
import numpy as np
from .common import OUT,EstimatorConfig,source_hashes,wrapped_error,save_json,canonical_hash
from .room import build_rirs,positions
from .recording import inputs,render_record
from .protocol import scene,ANGLES
from .estimator import estimate
from .srp import estimate_srp


def run():
    start=time.perf_counter();folder=OUT/'results/sensitivity';folder.mkdir(parents=True,exist_ok=True)
    summary=[];refinements=[];all_rows=0
    for room,(pl,rt),aid in product(range(3),((0,0),(1,2)),(0,3,6,9)):
        tag=f'r{room}p{pl}t{rt}a{aid:02d}';base=scene(room,pl,rt,ANGLES[aid])
        path=folder/f'{tag}.csv.gz'
        if path.exists() and (folder/f'{tag}.json').exists():
            m=json.loads((folder/f'{tag}.json').read_text());summary.append(m);refinements.extend(m['refinements']);all_rows+=m['rows'];continue
        hh={};cache=OUT/'cache/rirs'/f'{tag}.npz'
        if cache.exists():
            z=np.load(cache);hh['base']=(z['fractional_room'],z['fractional_direct'])
        else:hh['base']=(build_rirs(base)[0],build_rirs(replace(base,reflections=False))[0])
        base_h,base_d=hh['base']
        fine=build_rirs(replace(base,oversample=64))[0];more=build_rirs(replace(base,image_extent=84))[0]
        variations={'base':(base,(300.,3400.)),
            'rotation17':(replace(base,rotation_deg=17.),(300.,3400.)),
            'non_equilateral':(replace(base,non_equilateral=True),(300.,3400.)),
            'unequal_walls':(replace(base,absorption_multipliers=(.5,1.5,1.,1.,1.,1.)),(300.,3400.)),
            'lower_band':(base,(300.,1700.))}
        rows=[];local=[];configs={}
        for label,(cfg,band) in variations.items():
            if label=='lower_band':h,d=hh['base']
            elif label=='base':h,d=hh['base']
            else:h=build_rirs(cfg)[0];d=build_rirs(replace(cfg,reflections=False))[0]
            _,_,xy=positions(cfg)
            configs[label]={'room':asdict(cfg),'source_band_hz':band}
            for rid in range(5):
                # The baseline exactly reproduces the matching core record.
                record=inputs(cfg,d,32,rid,10.,'main_v2' if label=='base' else 'sensitivity_v2_'+label,band)
                y=render_record(h,record,cfg.fs);gcc=estimate(y,xy)
                methods={'GCC-PHAT':gcc}
                if label=='base':
                    srp=estimate_srp(y,xy);srp_fine=estimate_srp(y,xy,step=.05);methods['SRP-PHAT']=srp
                    refined={'propagation64':estimate(render_record(fine,record,cfg.fs),xy),
                        'extent84':estimate(render_record(more,record,cfg.fs),xy),
                        'correlation16':estimate(y,xy,EstimatorConfig(interp=16)),
                        'srp_grid005':srp_fine}
                    for key,value in refined.items():
                        reference=srp if key=='srp_grid005' else gcc;diff=wrapped_error(value,reference)
                        local.append({'scene':tag,'record_id':rid,'refinement':key,'max_difference_deg':float(np.max(abs(diff))),
                            'rms_difference_deg':float(np.sqrt(np.mean(diff*diff))),'above_005_count':int(np.sum(abs(diff)>.05)),
                            'mse_difference_deg2':float(np.mean(wrapped_error(value,cfg.theta_deg)**2-wrapped_error(reference,cfg.theta_deg)**2))})
                        # Preserve individual refined estimates so unstable frames cannot disappear in summaries.
                        methods['refined_'+key]=value
                for method,theta in methods.items():
                    errors=wrapped_error(theta,cfg.theta_deg)
                    for k,err in enumerate(errors):
                        rows.append({'scene_id':tag,'variation':label,'record_id':rid,'frame':k,'method':method,
                            'theta_true':cfg.theta_deg,'theta_est':float(theta[k]),'error_deg':float(err),'failure_gt5':int(abs(err)>5)})
        with gzip.open(path,'wt',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=rows[0].keys());writer.writeheader();writer.writerows(rows)
        m={'scene_id':tag,'configs':configs,'rows':len(rows),'refinements':local,'source_hashes':source_hashes()}
        (folder/f'{tag}.json').write_text(json.dumps(m,indent=2)+'\n');summary.append(m);refinements.extend(local);all_rows+=len(rows)
        print(f'sensitivity {tag}: {len(rows)} rows',flush=True)
    save_json('results/sensitivity/run_summary.json',{'scenes':len(summary),'rows':all_rows,'refinements':refinements,'elapsed_seconds':time.perf_counter()-start,'source_hashes':source_hashes()})
    for key in sorted({x['refinement'] for x in refinements}):
        rr=[x for x in refinements if x['refinement']==key]
        print(key,'max',max(x['max_difference_deg'] for x in rr),'above005',sum(x['above_005_count'] for x in rr),flush=True)


if __name__=='__main__':run()
