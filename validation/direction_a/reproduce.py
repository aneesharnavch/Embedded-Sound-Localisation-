"""Representative numerical reproduction; explicitly not a second full campaign."""
from pathlib import Path
import argparse,csv,gzip,hashlib,json,subprocess,sys,tempfile,time
import numpy as np
from .common import OUT,ROOT,save_json
from .campaign import run_scene


def run(include_references=False):
    start=time.perf_counter();report={'scope':'Representative reproduction, not a second full revised campaign','main_frames':0,'scenes':[]}
    subprocess.run([sys.executable,'-m','pytest','validation/direction_a/test_direct.py','validation/direction_a/test_room.py','validation/direction_a/test_srp.py','-q'],cwd=ROOT,check=True)
    if include_references:
        for module in ('verify_direct','joint_refinement','verify_revision'):
            subprocess.run([sys.executable,'-m','validation.direction_a.'+module],cwd=ROOT,check=True)
        report['reference_runs']=['full direct controls','joint 1.2 vs 1.5 s check','independent final full-extent room reference and pruning regression']
    folder=OUT/'reproduction';folder.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='representative_',dir=folder) as tmp:
        for job in [(0,0,0,0),(1,1,2,0),(2,1,2,6)]:
            result=run_scene(job,output=tmp);tag=result['scene'];max_error=0.;rows=0
            with gzip.open(Path(tmp)/f'{tag}.csv.gz','rt') as f,gzip.open(OUT/'results/main'/f'{tag}.csv.gz','rt') as g:
                a=list(csv.DictReader(f));b=list(csv.DictReader(g));assert len(a)==len(b)
                for x,y in zip(a,b):
                    for key in x:
                        if key in ('theta_est','error_deg'):max_error=max(max_error,abs(float(x[key])-float(y[key])))
                        else:assert x[key]==y[key],(tag,key)
                    rows+=1
            assert max_error<1e-9
            report['scenes'].append({'scene_id':tag,'frames':rows,'max_angular_difference_deg':max_error});report['main_frames']+=rows
    previous={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (OUT/'figures').glob('fig*.png')}
    subprocess.run([sys.executable,'-m','validation.direction_a.analysis'],cwd=ROOT,check=True)
    subprocess.run([sys.executable,'-m','validation.direction_a.figures'],cwd=ROOT,check=True)
    reproduced={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (OUT/'figures').glob('fig*.png')}
    assert previous==reproduced,'Figure pixels/metadata differ from packaged originals.'
    report.update(passed=True,figure_pngs_identical=list(previous),elapsed_seconds=time.perf_counter()-start,python=sys.version)
    save_json('reproduction/clean_environment_report.json',report);print(json.dumps(report,indent=2),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--references',action='store_true');args=parser.parse_args();run(args.references)
