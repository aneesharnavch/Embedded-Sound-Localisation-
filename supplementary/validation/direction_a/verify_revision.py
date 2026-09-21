"""Verify the v2 room domain, independent full reference and safe tile pruning."""
from dataclasses import asdict
from itertools import product
import json,time,importlib.util,sys
import numpy as np
from .common import OUT,save_json,wrapped_error,source_hashes
from .room import RoomConfig,build_rirs,positions,reflection_coefficients
from .protocol import scene,ANGLES
from .reference_room import image_response
from .verify_room import FREQUENCIES,PHASES,PROBE_BINS,transfer,direction_from_transfer


def run():
    start=time.perf_counter();pruning=[];archive=OUT/'superseded/v1_duration_0p9'
    for room,(pl,rt) in product(range(3),((0,0),(1,2))):
        tag=f'r{room}p{pl}t{rt}a00'
        meta=json.loads((archive/'results/main'/f'{tag}.json').read_text())
        cfg=RoomConfig(**meta['config']);h,info=build_rirs(cfg)
        cached=archive/'cache/rirs'/f'{tag}.npz'
        if cached.exists():original=np.load(cached)['fractional_room']
        else:
            # Release archives omit the optional large cache; the preserved
            # original builder provides the same optimization regression check.
            name='validation.direction_a._preserved_v1_room'
            if name not in sys.modules:
                spec=importlib.util.spec_from_file_location(name,archive/'source/room.py')
                module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module)
            original=sys.modules[name].build_rirs(cfg)[0]
        assert np.array_equal(h,original)
        assert info['path_counts']==meta['rir_metadata']['path_counts']
        pruning.append({'scene_id':tag,'identical_response':True,'identical_path_counts':True})
    cfg=scene(1,1,2,ANGLES[0]);h,info=build_rirs(cfg);m,s,xy=positions(cfg)
    pick=np.arange(0,96,8);freq=FREQUENCIES[pick]
    exact,counts=image_response(cfg.dimensions,m,s,reflection_coefficients(cfg),cfg.image_extent,cfg.path_duration_s,freq)
    actual=transfer(h,PROBE_BINS[pick]);error=float(np.linalg.norm(actual-exact)/np.linalg.norm(exact))
    ad=abs(float(wrapped_error(direction_from_transfer(actual,xy,freq,PHASES[pick]),direction_from_transfer(exact,xy,freq,PHASES[pick]))))
    assert list(counts)==info['path_counts'] and error<1e-4 and ad<.05
    joint=json.loads((OUT/'results/room/joint_refinement_1p2_vs1p5.json').read_text());assert joint['passed']
    result={'passed':True,'settings':asdict(cfg),'safe_pruning_checks':pruning,'independent_full_reference':{'path_counts':list(counts),'relative_spectrum_error':error,'angular_difference_deg':ad},
        'joint_duration_check_max_angle_deg':max(r['max_angle_change_deg'] for r in joint['scenes']),'elapsed_seconds':time.perf_counter()-start,'source_hashes':source_hashes()}
    save_json('results/room/revision_verification.json',result);print(json.dumps(result,indent=2),flush=True)


if __name__=='__main__':run()
