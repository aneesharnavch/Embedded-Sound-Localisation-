"""Independent spectral checks and room numerical-refinement controls."""
from dataclasses import replace,asdict
import json,time
import numpy as np
from scipy.fft import rfft
from .common import OUT,save_json,source_hashes,rng_for,wrapped_error
from .room import RoomConfig,positions,reflection_coefficients,build_rirs,room_metrics
from .reference_room import image_response
from .estimator import estimate
from .verify_direct import write_csv

NFFT=131072
PROBE_BINS=np.sort(rng_for('room_verification_bins').choice(np.arange(820,9284),size=96,replace=False))
FREQUENCIES=PROBE_BINS*48000/NFFT
PHASES=rng_for('room_verification_phases').uniform(-np.pi,np.pi,96)


def transfer(h,bins=PROBE_BINS):return rfft(h,n=NFFT,axis=-1)[:,bins]


def direction_from_transfer(response,xy,frequencies=FREQUENCIES,phases=PHASES):
    t=.25+np.arange(2048)/48000
    x=np.real((response*np.exp(1j*phases)[None,:]) @ np.exp(2j*np.pi*frequencies[:,None]*t[None,:]))
    return float(estimate(x,xy))


def run():
    started=time.monotonic();rows=[];selected=[];references=[]
    configs=[]
    for i,room in enumerate([(6.,5.,3.),(5.,4.,2.8),(8.,6.,3.2)]):
        for j,rt in enumerate([.15,.6]):
            configs.append(RoomConfig(dimensions=room,array_fraction=(.5,.5,.5) if j==0 else (.6,.45,.5),
                                      nominal_rt60=rt,theta_deg=7.37+60*i+120*j))
    for scene,cfg in enumerate(configs):
        m,s,xy=positions(cfg)
        previous=None;consecutive=0;chosen=None
        for extent in [6,10,14,18,24,32,40,48,56]:
            current=replace(cfg,image_extent=extent)
            t0=time.monotonic();h,meta=build_rirs(current);hertz=transfer(h)
            az=direction_from_transfer(hertz,xy);metrics,_=room_metrics(h,cfg.fs)
            row={'scene':scene,'nominal_rt60_s':cfg.nominal_rt60,'image_extent':extent,'path_duration_s':cfg.path_duration_s,
                 'estimated_azimuth_deg':az,'elapsed_seconds':time.monotonic()-t0,**metrics}
            if previous is None:delta_angle=delta_t20=delta_spectrum=float('inf')
            else:
                delta_angle=abs(float(wrapped_error(az,previous['az'])))
                delta_t20=abs(metrics['t20_s']/previous['metrics']['t20_s']-1)
                delta_spectrum=float(np.linalg.norm(hertz-previous['H'])/np.linalg.norm(hertz))
            row.update({'angle_change_deg':None if previous is None else delta_angle,
                        't20_relative_change':None if previous is None else delta_t20,
                        'spectral_relative_change':None if previous is None else delta_spectrum})
            rows.append(row)
            passed=delta_angle<.05 and delta_t20<.01 and delta_spectrum<.001
            consecutive=consecutive+1 if passed else 0
            print(f'scene={scene} RT={cfg.nominal_rt60:.2f} K={extent} T20={metrics["t20_s"]:.4f} angle_delta={delta_angle:.5g} H_delta={delta_spectrum:.4g} seconds={row["elapsed_seconds"]:.2f}',flush=True)
            previous={'az':az,'metrics':metrics,'H':hertz}
            if consecutive>=2:
                chosen=current;break
        if chosen is None:
            write_csv(OUT/'results/room/refinement_trials.csv',rows)
            save_json('results/room/verification_failure.json',{'scene':scene,'reason':'image refinement did not meet two successive convergence checks','source_hashes':source_hashes()})
            raise SystemExit('Room image coverage has not converged; extend or diagnose.')
        # Independently assess path-duration support with image coverage held fixed.
        hr,_=build_rirs(replace(chosen,path_duration_s=1.2))
        Hlong=transfer(hr);azlong=direction_from_transfer(Hlong,xy)
        duration_delta=abs(float(wrapped_error(azlong,previous['az'])))
        duration_H=float(np.linalg.norm(Hlong-previous['H'])/np.linalg.norm(Hlong))
        if duration_delta>=.05 or duration_H>=.001:
            save_json('results/room/verification_failure.json',{'scene':scene,'reason':'path-duration refinement failed','delta_deg':duration_delta,'spectral_relative':duration_H})
            raise SystemExit('Room response duration has not converged.')
        selected.append({'scene':scene,'config':asdict(chosen),'metrics':previous['metrics'],
                         'duration_0p9_vs_1p2_angle_deg':duration_delta,'duration_0p9_vs_1p2_relative_spectrum':duration_H})
        # A different reflected-tile enumeration evaluates exact arrival phases.
        check_cfg=replace(cfg,image_extent=4,path_duration_s=.4)
        exact,count=image_response(cfg.dimensions,m,s,reflection_coefficients(cfg),4,.4,FREQUENCIES)
        exact_az=direction_from_transfer(exact,xy)
        for oversample in [8,16,32]:
            hc,info=build_rirs(replace(check_cfg,oversample=oversample))
            actual=transfer(hc);actual_az=direction_from_transfer(actual,xy)
            err=float(np.linalg.norm(actual-exact)/np.linalg.norm(exact))
            delta=abs(float(wrapped_error(actual_az,exact_az)))
            assert info['path_counts']==count
            references.append({'scene':scene,'extent':4,'oversample':oversample,'relative_spectrum_error':err,'angular_difference_deg':delta,'path_counts':count})
            print(f'reference scene={scene} oversample={oversample} spectral={err:.6g} angle={delta:.6g}',flush=True)
            # Oversample 8 is a coarse refinement control, not the preselected
            # production representation (16). Retain its error even if it misses
            # the production tolerance. Both 16 and 32 must pass.
            if oversample>=16 and (err>=1e-4 or delta>=.05):
                save_json('results/room/verification_failure.json',{'scene':scene,'reason':'selected fractional propagation reference failed','oversample':oversample,'relative_spectrum_error':err,'angular_difference_deg':delta})
                raise SystemExit('Independent room propagation reference failed.')
        print(f'scene={scene} independent reference passed; selected K={chosen.image_extent}',flush=True)
        save_json('results/room/partial_summary.json',{'selected':selected,'references':references,'source_hashes':source_hashes()})
    # Full selected-extent independent cross-check in the highest tested decay setting.
    hardest=max(selected,key=lambda x:(x['config']['image_extent'],x['config']['nominal_rt60']))
    cfg=RoomConfig(**hardest['config']);m,s,xy=positions(cfg)
    ix=np.arange(0,96,8);freq=FREQUENCIES[ix];phase=PHASES[ix]
    exact,count=image_response(cfg.dimensions,m,s,reflection_coefficients(cfg),cfg.image_extent,cfg.path_duration_s,freq)
    h,meta=build_rirs(cfg);actual=transfer(h,PROBE_BINS[ix])
    full_error=float(np.linalg.norm(actual-exact)/np.linalg.norm(exact))
    full_angle=abs(float(wrapped_error(direction_from_transfer(actual,xy,freq,phase),direction_from_transfer(exact,xy,freq,phase))))
    assert count==meta['path_counts']
    passed=full_error<1e-4 and full_angle<.05
    write_csv(OUT/'results/room/refinement_trials.csv',rows)
    summary={'stage':'G2','passed':passed,'selected':selected,'references':references,
             'full_extent_reference':{'scene':hardest['scene'],'extent':cfg.image_extent,'relative_spectrum_error':full_error,'angular_difference_deg':full_angle,'path_counts':count},
             'selected_main_extent':max(x['config']['image_extent'] for x in selected),
             'selected_path_duration_s':.9,'selected_oversample':16,'selected_half_width':32,
             'elapsed_seconds':time.monotonic()-started,'source_hashes':source_hashes()}
    save_json('results/room/verification_summary.json',summary)
    doc=['# Room-model verification report','',f'**G2 numerical checks: {"PASS" if passed else "FAIL"}.**','',
         'The model is a frequency-independent, specular shoebox image-source model. This is computational verification, not validation against a real room.', '',
         '| Scene | Requested RT60 (s) | Realized band T20 (s) | Selected image extent |','|---|---:|---:|---:|']
    for item in selected:doc.append(f'| {item["scene"]} | {item["config"]["nominal_rt60"]:.2f} | {item["metrics"]["t20_s"]:.4f} | {item["config"]["image_extent"]} |')
    doc+=['', 'Convergence requires two successive image refinements with angular change below 0.05 degrees, relative T20 change below 1%, and relative probe-spectrum change below 0.1%. Extending path duration from 0.9 to 1.2 s is checked separately at fixed image extent.', '',
          'Fractional room responses deposit each image between two samples of a finer time grid, then apply a Kaiser-windowed sinc decimation filter. Grid oversampling 8, 16, and 32 is compared against an independent exact-phase image sum. This differs from the direct-path FIR implementation and has its own verification.', '',
          f'The full-extent independent reference has relative spectral discrepancy {full_error:.6g} and angular discrepancy {full_angle:.6g} degrees. Path counts also agree.', '',
          'Room decay is estimated after a common fourth-order 300-3400 Hz Butterworth acquisition filter using the Schroeder energy decay. T20 is extrapolated from -5 to -25 dB, and fit R-squared values are stored. Requested and realized decay are distinct.', '',
          'The recording tests separately verify identical paired source/noise realizations, exact direct-band SNR calibration, and onset transients that disappear with sufficient history. The common acquisition filter is causal. The source onset condition includes the spectral broadening of switching on the source.', '',
          'Detailed configurations, path counts, refinement results, reference errors, fit quality and source hashes are stored in results/room.']
    (OUT/'ROOM_VERIFICATION_REPORT.md').write_text('\n'.join(doc)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k not in ['selected','references','source_hashes']},indent=2),flush=True)
    if not passed:raise SystemExit('Full-extent room reference failed.')


if __name__=='__main__':run()
