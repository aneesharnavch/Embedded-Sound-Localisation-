"""Run analytical and waveform controls, exporting complete stage-G1 evidence."""
from dataclasses import replace,asdict
from pathlib import Path
import csv,itertools,json,time
import numpy as np
from .common import (OUT,ROOT,C,triangle,plane_arrivals,spherical_arrivals,
                     solve_arrivals,wrapped_error,EstimatorConfig,save_json,source_hashes)
from . import reference
from .signals import direct_waveforms,tone_parameters
from .estimator import estimate


def rmse(x): return float(np.sqrt(np.mean(np.asarray(x)**2)))


def write_csv(path,rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)


def run():
    start=time.monotonic();out=OUT/'results/direct';out.mkdir(parents=True,exist_ok=True)
    angles=-180+np.arange(720)*.5+.13
    rows=[]; summaries=[];reference_max=0.;plane_max=0.
    for radius in [.025,.05,.10]:
        m=triangle(radius)
        plane_max=max(plane_max,float(np.max(abs(wrapped_error(solve_arrivals(plane_arrivals(angles,m),m),angles)))))
        for dist in [.5,1.5,5.,20.]:
            times=spherical_arrivals(angles,dist,m)
            exact=solve_arrivals(times,m)
            e=wrapped_error(exact,angles)
            for ai in [0,79,180,361,540,719]:
                ts=reference.exact_times(float(angles[ai]),dist,m.tolist())
                rr=reference.direction(ts,m.tolist())
                reference_max=max(reference_max,float(abs(wrapped_error(exact[ai],rr))))
            for fs in [16000,48000,96000,192000]:
                rounded=solve_arrivals(np.rint(times*fs)/fs,m)
                er=wrapped_error(rounded,angles)
                summaries.append({'radius_m':radius,'distance_m':dist,'fs_hz':fs,
                                  'exact_spherical_rmse_deg':rmse(e),'rounded_rmse_deg':rmse(er),
                                  'rounded_vs_exact_rmse_deg':rmse(wrapped_error(rounded,exact))})
                for k,th in enumerate(angles):
                    rows.append({'radius_m':radius,'distance_m':dist,'fs_hz':fs,'truth_deg':float(th),
                                 'exact_estimate_deg':float(exact[k]),'rounded_estimate_deg':float(rounded[k]),
                                 'exact_signed_error_deg':float(e[k]),'rounded_signed_error_deg':float(er[k])})
    write_csv(out/'analytic_trials.csv',rows);write_csv(out/'analytic_summary.csv',summaries)
    print(f'Analytical controls: {len(rows)} angle/rate/geometry conditions.',flush=True)
    # Reproduce every scalar in the earlier saved geometric diagnostic.
    old=json.loads((ROOT/'paper/publication_speedrun/research/direct_path_rounding_diagnostic.json').read_text())
    reproduction={};audit_max=0.
    for label, aa in [('existing_7',np.arange(-120,121,40)+(np.arange(7)+.5)/7-.5),('full_circle_720',angles)]:
        reproduction[label]={}
        ts=spherical_arrivals(aa,1.5,triangle())
        for fs in [16000,48000,96000,192000]:
            er=wrapped_error(solve_arrivals(np.rint(ts*fs)/fs,triangle()),aa)
            values={'rounded_arrival_rmse_deg':rmse(er),
                    'exact_spherical_delay_far_field_solve_rmse_deg':rmse(wrapped_error(solve_arrivals(ts,triangle()),aa)),
                    'max_abs_rounded_deg':float(np.max(abs(er)))}
            reproduction[label][str(fs)]=values
            audit_max=max(audit_max,max(abs(values[k]-old[label][str(fs)][k]) for k in values))
    save_json('results/direct/audit_reproduction.json',reproduction)
    waveform=[];interp_rows=[]
    m=triangle()
    for fs in [16000,48000,96000,192000]:
        n=round(2048*fs/48000);cfg=replace(EstimatorConfig(),fs=fs,samples=n)
        for seed in [11,29]:
            params=tone_parameters(seed)
            for th in 7.37+30*np.arange(12):
                ts=spherical_arrivals(th,1.5,m);gains=1/(4*np.pi*C*ts)
                for half in [16,32,64]:
                    oracle,fir=direct_waveforms(ts,fs,n,params,half,gains)
                    exact=estimate(oracle,m,cfg);actual=estimate(fir,m,cfg)
                    waveform.append({'fs_hz':fs,'samples':n,'duration_s':n/fs,'seed':seed,'truth_deg':float(th),
                                     'kernel_half_width':half,'relative_waveform_l2':float(np.linalg.norm(fir-oracle)/np.linalg.norm(oracle)),
                                     'propagation_angular_difference_deg':float(wrapped_error(actual,exact)),
                                     'oracle_angular_error_deg':float(wrapped_error(exact,th)),
                                     'fir_angular_error_deg':float(wrapped_error(actual,th))})
                high=estimate(oracle,m,replace(cfg,interp=64))
                for factor in [8,16,32,64]:
                    az=estimate(oracle,m,replace(cfg,interp=factor))
                    interp_rows.append({'fs_hz':fs,'seed':seed,'truth_deg':float(th),'interp':factor,
                                        'difference_from_64_deg':float(wrapped_error(az,high)),
                                        'oracle_error_deg':float(wrapped_error(az,th))})
        print(f'Waveform controls done at {fs} Hz.',flush=True)
    write_csv(out/'waveform_trials.csv',waveform);write_csv(out/'interpolation_trials.csv',interp_rows)
    kernel_summary=[]
    for h in [16,32,64]:
        selected=[r for r in waveform if r['kernel_half_width']==h]
        kernel_summary.append({'half_width':h,'cases':len(selected),
                               'max_relative_waveform_l2':max(r['relative_waveform_l2'] for r in selected),
                               'max_abs_angular_difference_deg':max(abs(r['propagation_angular_difference_deg']) for r in selected)})
    interp_max=max(abs(r['difference_from_64_deg']) for r in interp_rows if r['interp']==8)
    summary={'stage':'G1','analytic_conditions':len(rows),'waveform_conditions':len(waveform),
             'plane_max_abs_error_deg':plane_max,'independent_reference_max_difference_deg':reference_max,
             'audit_reproduction_max_difference_deg':audit_max,'kernel_refinement':kernel_summary,
             'interp8_vs_64_max_difference_deg':interp_max,'tolerance_deg':.05,
             'selected_half_width':32,'config':asdict(EstimatorConfig()),
             'source_hashes':source_hashes(),'elapsed_seconds':time.monotonic()-start}
    summary['passed']=bool(plane_max<1e-9 and reference_max<1e-9 and audit_max<1e-9 and
                           kernel_summary[1]['max_abs_angular_difference_deg']<.05 and
                           kernel_summary[2]['max_abs_angular_difference_deg']<.05 and interp_max<.05)
    save_json('results/direct/verification_summary.json',summary)
    print(json.dumps(summary,indent=2),flush=True)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots(1,2,figsize=(9,3.5))
    ts=spherical_arrivals(angles,1.5,m)
    for fs in [16000,48000,192000]:
        az=solve_arrivals(np.rint(ts*fs)/fs,m)
        ax[0].plot(angles,wrapped_error(az,angles),label=f'{fs//1000} kHz',lw=.7)
    ax[0].plot(angles,wrapped_error(solve_arrivals(ts,m),angles),'k--',label='Exact spherical',lw=1.1)
    ax[0].set(xlabel='True azimuth (degrees)',ylabel='Signed direction error (degrees)',title='Noiseless delay-level controls')
    ax[0].legend(fontsize=7,ncol=2)
    for fs in [16000,48000,96000,192000]:
        vals=[]
        for h in [16,32,64]:
            vals.append(max(abs(r['propagation_angular_difference_deg']) for r in waveform if r['fs_hz']==fs and r['kernel_half_width']==h))
        ax[1].semilogy([16,32,64],vals,marker='o',label=f'{fs//1000} kHz')
    ax[1].axhline(.05,color='k',ls='--',label='Declared tolerance')
    ax[1].set(xlabel='Fractional-delay kernel half-width (samples)',ylabel='Maximum angular discrepancy (degrees)',title='FIR versus analytical waveforms')
    ax[1].legend(fontsize=7)
    for a in ax:a.grid(alpha=.2)
    fig.tight_layout()
    (OUT/'figures').mkdir(exist_ok=True)
    fig.savefig(OUT/'figures/direct_verification.svg');fig.savefig(OUT/'figures/direct_verification.png',dpi=180)
    plt.close(fig)
    doc=['# Direct-path verification report','',f'**G1 numerical checks: {"PASS" if summary["passed"] else "FAIL"}.**','',
         'This report concerns analytical delays and noiseless deterministic harmonic verification signals. It is not a room-performance or hardware result.','',
         f'- Analytical conditions saved: {len(rows):,}.',f'- Waveform/kernel conditions saved: {len(waveform)}.',
         f'- Maximum plane-wave inversion error: {plane_max:.3g} degrees.',
         f'- Maximum difference from the independent scalar solve: {reference_max:.3g} degrees.',
         f'- Maximum discrepancy reproducing the old geometric diagnostic: {audit_max:.3g} degrees.',
         f'- Maximum interpolation-factor 8 versus 64 difference: {interp_max:.6g} degrees.','',
         '| Kernel half-width | Maximum relative waveform error | Maximum angular discrepancy |','|---|---:|---:|']
    for r in kernel_summary:doc.append(f'| {r["half_width"]} | {r["max_relative_waveform_l2"]:.6g} | {r["max_abs_angular_difference_deg"]:.6g} degrees |')
    doc += ['', 'The 0.05-degree tolerance bounds numerical discrepancies in these reference comparisons. It is not an absolute estimator-accuracy promise. Finite-window effects and spherical-to-plane model mismatch can remain in both waveform implementations.', '',
            'A fixed analysis interval is used across FIR refinements; sampling-rate comparisons retain approximately 42.667 ms with nearest-integer sample counts. The source band remains 300-3400 Hz.', '',
            'The legacy seven-direction 48 kHz rounding diagnostic reproduces about 1.44385 degrees RMSE. The full-circle value is about 2.14307 degrees. Exact spherical delays leave curvature error under the far-field solve; neither number measures a universal reverberant floor.', '',
            'Per-condition outputs and the verification summary are in the results/direct directory. Source hashes and environment versions accompany the run. The core scientific correctness tests must also pass before G1 is recorded complete.']
    (OUT/'DIRECT_PATH_REPORT.md').write_text('\n'.join(doc)+'\n')
    if not summary['passed']:raise SystemExit('G1 numerical tolerance failed; inspect the report.')


if __name__=='__main__':run()
