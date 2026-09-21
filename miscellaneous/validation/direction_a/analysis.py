"""Record-stratified uncertainty, paired factorial contrasts and held-out averaging."""
from itertools import product,combinations
import csv,gzip,hashlib,json
import numpy as np
from .common import OUT,rng_for,wrapped_error,save_json
from .protocol import VARIANTS,subset
from .campaign import jobs,code_hashes


def write_csv(name,rows):
    p=OUT/'results/analysis'/name;p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)


def load_campaign():
    core={};attr={};long={};metadata={};counts={};all_inputs=set();main_seeds=set();long_seeds=set();train_seeds=set();holdout_seeds=set();rows=0
    protocol=json.loads((OUT/'configs/main_protocol.json').read_text())
    for room,pl,rt,aid in jobs():
        tag=f'r{room}p{pl}t{rt}a{aid:02d}';p=OUT/'results/main'/f'{tag}.csv.gz'
        m=json.loads(p.with_suffix('').with_suffix('.json').read_text());metadata[tag]=m
        assert m['protocol_hash']==protocol['protocol_hash'] and m['code_hashes']==code_hashes()
        assert hashlib.sha256(p.read_bytes()).hexdigest()==m['csv_sha256']
        blocks={};identities={}
        with gzip.open(p,'rt') as f:
            for row in csv.DictReader(f):
                exp=row['experiment'];rid=int(row['record_id']);snr=float(row['snr_db']);variant=row['variant'];frame=int(row['frame'])
                key=(exp,snr,variant,rid)
                if key not in blocks:blocks[key]={};identities[key]=set()
                assert frame not in blocks[key];blocks[key][frame]=float(row['error_deg']);identities[key].add(row['input_id'])
                assert row['config_hash']==m['config_hashes'][variant]
                assert abs(float(wrapped_error(float(row['theta_est']),float(row['theta_true'])))-float(row['error_deg']))<1e-10
                assert int(row['failure_gt5'])==int(abs(float(row['error_deg']))>5)
                counts[exp]=counts.get(exp,0)+1;rows+=1
        for key,b in blocks.items():
            n=128 if key[0].startswith('long') else 32
            assert set(b)==set(range(n)) and len(identities[key])==1
        for snr in (0.,10.,20.):
            core[(tag,snr)]=np.array([[blocks[('core',snr,'F_S_R',rid)][k] for k in range(32)] for rid in range(5)])
        if subset(room,pl,rt):
            for v in VARIANTS:
                exp='core' if v=='F_S_R' else 'attribution'
                attr[(tag,v)]=np.array([[blocks[(exp,10.,v,rid)][k] for k in range(32)] for rid in range(5)])
                for rid in range(5):assert identities[(exp,10.,v,rid)]==identities[('core',10.,'F_S_R',rid)]
            long[tag]=np.array([[blocks[('long_train' if rid<5 else 'long_holdout',10.,'F_S_R',rid)][k] for k in range(128)] for rid in range(10)])
        for r in m['input_records']:
            assert r['input_id'] not in all_inputs;all_inputs.add(r['input_id'])
            (main_seeds if r['experiment']=='core' else long_seeds).add(r['source_sha256'])
            if r['experiment']=='long_train':train_seeds.add(r['source_sha256'])
            if r['experiment']=='long_holdout':holdout_seeds.add(r['source_sha256'])
    assert rows==276480 and counts=={'core':103680,'attribution':80640,'long_train':46080,'long_holdout':46080}
    assert not main_seeds.intersection(long_seeds)
    assert not train_seeds.intersection(holdout_seeds)
    audit={'passed':True,'rows':rows,'counts':counts,'physical_scenes':len(metadata),'unique_input_records':len(all_inputs),
        'paired_attribution_scenes':len(attr)//8,'long_scenes':len(long),'train_holdout_source_hash_overlap':0,
        'protocol_hash':protocol['protocol_hash'],'all_scene_file_hashes_checked':True,'all_frames_and_pairs_checked':True}
    save_json('results/analysis/completeness_audit.json',audit)
    return core,attr,long,metadata


def stats(y,identity):
    y=np.asarray(y);y=y[None] if y.ndim==2 else y
    s,r,n=y.shape;ms=np.mean(y*y,axis=-1);failure=np.mean(abs(y)>5,axis=-1)
    z=np.mean(np.exp(1j*np.deg2rad(y)),axis=-1);zm=z.mean();bias=float(np.rad2deg(np.angle(zm)))
    idx=rng_for('bootstrap_v1',identity).integers(0,r,(2000,s,r))
    bms=np.take_along_axis(ms[None],idx,axis=2).mean(axis=(1,2))
    bf=np.take_along_axis(failure[None],idx,axis=2).mean(axis=(1,2))
    bz=np.take_along_axis(z[None],idx,axis=2).mean(axis=(1,2));bd=wrapped_error(np.rad2deg(np.angle(bz)),bias)
    return {'scenes':s,'records':s*r,'frames':s*r*n,'rmse_deg':float(np.sqrt(ms.mean())),
        'rmse_ci_low':float(np.sqrt(np.quantile(bms,.025))),'rmse_ci_high':float(np.sqrt(np.quantile(bms,.975))),
        'median_abs_deg':float(np.median(abs(y))),'p90_abs_deg':float(np.quantile(abs(y),.9)),
        'mean_signed_deg':float(y.mean()),'circular_bias_deg':bias,'circular_resultant':float(abs(zm)),
        'bias_ci_low':float(bias+np.quantile(bd,.025)),'bias_ci_high':float(bias+np.quantile(bd,.975)),
        'failure_rate':float(failure.mean()),'failure_ci_low':float(np.quantile(bf,.025)),'failure_ci_high':float(np.quantile(bf,.975))}


def paired_summary(value,identity):
    # value: fixed scenes x independent records; all frames already paired/averaged.
    value=np.asarray(value);s,r=value.shape
    idx=rng_for('paired_bootstrap_v1',identity).integers(0,r,(2000,s,r))
    b=np.take_along_axis(value[None],idx,axis=2).mean(axis=(1,2))
    return {'estimate':float(value.mean()),'ci_low':float(np.quantile(b,.025)),'ci_high':float(np.quantile(b,.975))}


def circular_blocks(e,n):
    return np.rad2deg(np.angle(np.mean(np.exp(1j*np.deg2rad(e.reshape(e.shape[0],-1,n))),axis=-1)))


def run():
    core,attr,long,meta=load_campaign();scene_rows=[];group_rows=[];global_rows=[]
    for (tag,snr),e in sorted(core.items()):
        room,pl,rt,aid=meta[tag]['indices'];m=meta[tag]['room_descriptors']
        scene_rows.append({'scene_id':tag,'room':room,'placement':pl,'rt_index':rt,'angle_index':aid,'snr_db':snr,
            'nominal_rt60_s':meta[tag]['config']['nominal_rt60'],'t20_s':m['t20_s'],'t20_r2':m['t20_s_r2'],
            'component_drr_db':m['component_drr_db'],**stats(e,('scene',tag,snr))})
    for room,rt,snr in product(range(3),range(3),(0.,10.,20.)):
        tags=[t for t,m in meta.items() if m['indices'][0]==room and m['indices'][2]==rt]
        group_rows.append({'room':room,'rt_index':rt,'snr_db':snr,**stats(np.stack([core[(t,snr)] for t in tags]),('group',room,rt,snr))})
    for rt,snr in product(range(3),(0.,10.,20.)):
        tags=[t for t,m in meta.items() if m['indices'][2]==rt]
        global_rows.append({'rt_index':rt,'snr_db':snr,**stats(np.stack([core[(t,snr)] for t in tags]),('global',rt,snr))})
    write_csv('core_scene_summary.csv',scene_rows);write_csv('core_group_summary.csv',group_rows);write_csv('core_global_summary.csv',global_rows)
    tags=sorted(long);variant_rows=[];factor_rows=[];onset_rows=[]
    for group in ('all','low','high'):
        ts=[t for t in tags if group=='all' or (meta[t]['indices'][2]==0)==(group=='low')]
        cube=np.stack([np.stack([attr[(t,v)] for v in VARIANTS]) for t in ts]) # scenes,variants,records,frames
        for j,v in enumerate(VARIANTS):variant_rows.append({'group':group,'variant':v,**stats(cube[:,j],('variant',group,v))})
        codes=np.array([[1 if x=='Q' else -1,1 if y=='O' else -1,1 if z=='R' else -1] for x,y,z in (v.split('_') for v in VARIANTS)])
        for k in (1,2,3):
            for axes in combinations(range(3),k):
                weights=np.prod(codes[:,axes],axis=1)*2**k/8;name=':'.join(('rounding','onset','reflections')[a] for a in axes)
                for metric,values in [('signed_deg',cube),('squared_deg2',cube*cube)]:
                    contrast=np.einsum('svrn,v->srn',values,weights).mean(axis=-1)
                    factor_rows.append({'group':group,'contrast':name,'metric':metric,**paired_summary(contrast,(group,name,metric))})
        for frame in range(32):
            for v in ('F_S_R','F_O_R'):
                e=np.stack([attr[(t,v)][:,frame:frame+1] for t in ts])
                onset_rows.append({'group':group,'variant':v,'frame':frame,'midpoint_s':(frame+.5)*2048/48000,**stats(e,('onset',group,v,frame))})
    write_csv('attribution_variants.csv',variant_rows);write_csv('factorial_contrasts.csv',factor_rows);write_csv('onset_trajectory.csv',onset_rows)
    simple=[]
    for group in ('all','low','high'):
        ts=[t for t in tags if group=='all' or (meta[t]['indices'][2]==0)==(group=='low')]
        for name,left,right in [('rounding_direct','Q_S_D','F_S_D'),('rounding_reflected','Q_S_R','F_S_R'),
             ('onset_reflected','F_O_R','F_S_R'),('reflections_fractional','F_S_R','F_S_D')]:
            for metric in ('signed_deg','squared_deg2'):
                for length in ([1,4,32] if name=='onset_reflected' else [32]):
                    vals=[]
                    for t in ts:
                        a=attr[(t,left)][:,:length];b=attr[(t,right)][:,:length]
                        vals.append(np.mean(a-b if metric=='signed_deg' else a*a-b*b,axis=1))
                    simple.append({'group':group,'contrast':name,'first_frames':length,'metric':metric,
                        **paired_summary(np.stack(vals),('simple',group,name,length,metric))})
    write_csv('simple_paired_contrasts.csv',simple)
    averaging=[];averaging_global=[];eligibility=[];predictions={}
    for tag,e in long.items():
        train=e[:5];hold=e[5:];mean_z=np.mean(np.exp(1j*np.deg2rad(train)));bias=float(np.rad2deg(np.angle(mean_z)))
        eligible=bool(abs(mean_z)>=.95 and abs(bias)<=15)
        # Center each training record before estimating short-lag stationary covariance.
        centered=wrapped_error(train,bias);centered-=centered.mean(axis=1,keepdims=True)
        gamma=np.array([np.mean(centered[:,:128-l]*centered[:,l:]) for l in range(33)])
        eligibility.append({'scene_id':tag,'eligible':int(eligible),'train_bias_deg':bias,'train_resultant':float(abs(mean_z)),'gamma0_deg2':float(gamma[0])})
        predictions[tag]={}
        for n in (1,2,4,8,16,32,64,128):
            l=np.arange(1,min(n,33));cov=float((gamma[0]+2*np.sum((1-l/n)*(1-l/33)*gamma[l]))/n)
            iid=gamma[0]/n;predictions[tag][n]=(bias*bias+max(0.,cov),bias*bias+iid,eligible)
            avg=circular_blocks(hold,n)
            averaging.append({'scene_id':tag,'frames_averaged':n,'duration_s':n*2048/48000,'prediction_eligible':int(eligible),
                'predicted_cov_rmse_deg':float(np.sqrt(bias*bias+max(0.,cov))),'predicted_iid_rmse_deg':float(np.sqrt(bias*bias+iid)),
                **stats(avg,('average',tag,n))})
    for group in ('all','low','high','eligible'):
        ts=[t for t in tags if group=='all' or (group=='eligible' and predictions[t][1][2]) or (group in ('low','high') and (meta[t]['indices'][2]==0)==(group=='low'))]
        if not ts:continue
        for n in (1,2,4,8,16,32,64,128):
            avg=np.stack([circular_blocks(long[t][5:],n) for t in ts])
            averaging_global.append({'group':group,'frames_averaged':n,'duration_s':n*2048/48000,
                'cov_prediction_rmse_deg':float(np.sqrt(np.mean([predictions[t][n][0] for t in ts]))),
                'iid_prediction_rmse_deg':float(np.sqrt(np.mean([predictions[t][n][1] for t in ts]))),
                **stats(avg,('average_global',group,n))})
    write_csv('averaging_scene_summary.csv',averaging);write_csv('averaging_global_summary.csv',averaging_global);write_csv('prediction_eligibility.csv',eligibility)
    # Load every sensitivity frame, retaining numerical-refinement exceptions.
    sensitivities={};sensitivity_rows=[];method_pairs=[];reference_equal=True
    for p in sorted((OUT/'results/sensitivity').glob('r*.csv.gz')):
        with gzip.open(p,'rt') as f:
            for r in csv.DictReader(f):
                key=(r['scene_id'],r['variation'],r['method']);rid=int(r['record_id']);k=int(r['frame'])
                if key not in sensitivities:sensitivities[key]=np.full((5,32),np.nan)
                sensitivities[key][rid,k]=float(r['error_deg'])
    assert len({k[0] for k in sensitivities})==24
    for (tag,var,method),e in sensitivities.items():
        assert np.isfinite(e).all()
        if var=='base' and method=='GCC-PHAT':reference_equal=reference_equal and bool(np.array_equal(e,core[(tag,10.)]))
    assert reference_equal
    for var,method in sorted({(v,m) for t,v,m in sensitivities}):
        es=[e for (t,v,m),e in sorted(sensitivities.items()) if v==var and m==method]
        sensitivity_rows.append({'variation':var,'method':method,**stats(np.stack(es),('sensitivity',var,method))})
    for group in ('all','low','high'):
        ts=sorted({t for t,v,m in sensitivities if group=='all' or (meta[t]['indices'][2]==0)==(group=='low')})
        contrast=np.stack([np.mean(sensitivities[(t,'base','SRP-PHAT')]**2-sensitivities[(t,'base','GCC-PHAT')]**2,axis=1) for t in ts])
        method_pairs.append({'group':group,'contrast':'SRP minus GCC squared error','units':'deg2',**paired_summary(contrast,('srp_pair',group))})
    write_csv('sensitivity_summary.csv',sensitivity_rows);write_csv('baseline_paired_contrast.csv',method_pairs)
    result={'passed':True,'bootstrap_draws':2000,'core_groups':len(group_rows),'attribution_scenes':len(tags),
        'prediction_eligible_scenes':sum(x['eligible'] for x in eligibility),'sensitivity_base_equals_core':reference_equal,
        'decay_t20_range_s':[min(m['room_descriptors']['t20_s'] for m in meta.values()),max(m['room_descriptors']['t20_s'] for m in meta.values())],
        'interpretation':'Bootstrap intervals condition on the fixed scenes; records are resampled jointly across paired variants. Pooled circular bias is descriptive and may conceal opposite scene biases.'}
    save_json('results/analysis/summary.json',result);print(json.dumps(result,indent=2))


if __name__=='__main__':run()
