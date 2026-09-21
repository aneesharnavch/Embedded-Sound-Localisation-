"""Generate manuscript/supplement tables directly from final retained summaries."""
import csv,json
from .common import OUT


def read(name):
    with (OUT/'results/analysis'/name).open() as f:return list(csv.DictReader(f))


def run():
    folder=OUT/'manuscript'
    verification=json.loads((OUT/'results/room/revision_verification.json').read_text())
    sens=json.loads((OUT/'results/sensitivity/run_summary.json').read_text())
    data=[('Full room reference',verification['independent_full_reference']['angular_difference_deg']),
          ('Joint duration/domain',verification['joint_duration_check_max_angle_deg'])]
    for key,label in [('propagation64','Propagation grid 32 to 64'),('extent84','Image extent 76 to 84'),('correlation16','GCC factor 8 to 16'),('srp_grid005','SRP angular grid refinement')]:
        data.append((label,max(r['max_difference_deg'] for r in sens['refinements'] if r['refinement']==key)))
    lines=[r'\begin{table}[t]\centering\small',r'\caption{Final numerical verification. Values are maximum angular discrepancies in the stated checks, not errors against source azimuth.}',r'\label{tab:verification}',r'\begin{tabular}{@{}lr@{}}\toprule',r'Check & Change (deg)\\\midrule']
    lines += [label+' & '+f'{value:.6f}'+r'\\' for label,value in data]
    lines += [r'\bottomrule\end{tabular}\end{table}'];(folder/'main_verification_table.tex').write_text('\n'.join(lines)+'\n')
    simple=read('simple_paired_contrasts.csv');names={'rounding_direct':'Rounding, direct','rounding_reflected':'Rounding, reflected','onset_reflected':'Onset, reflected','reflections_fractional':'Reflections, fractional'}
    lines=[r'\begin{table}[t]\centering\footnotesize',r'\caption{Paired changes in mean squared error (deg$^2$), all 72 attribution scenes. Intervals resample complete records within each fixed scene.}',r'\label{tab:effects}',r'\begin{tabular}{@{}lrr@{}}\toprule',r'Contrast & Change & 95\% interval\\\midrule']
    for r in simple:
        if r['group']=='all' and r['metric']=='squared_deg2' and r['first_frames']=='32':
            lines.append(names[r['contrast']]+' & '+f"{float(r['estimate']):.2f}"+' & ['+f"{float(r['ci_low']):.2f}, {float(r['ci_high']):.2f}"+r']\\')
    lines += [r'\bottomrule\end{tabular}\end{table}'];(folder/'main_effect_table.tex').write_text('\n'.join(lines)+'\n')
    rows=read('core_scene_summary.csv')
    lines=[r'\begin{table}[htbp]\centering\small',r'\caption{Realized descriptors across 12 directions in each room/placement/absorption state. Ranges are across fixed directions, not uncertainty intervals.}',r'\begin{tabular}{@{}rrrlll@{}}\toprule',r'Room & Position & Nominal RT (s) & T20 range (s) & DRR range (dB) & Minimum fit $R^2$\\\midrule']
    for room in range(3):
        for pl in range(2):
            for rt in range(3):
                r=[x for x in rows if int(x['room'])==room and int(x['placement'])==pl and int(x['rt_index'])==rt and float(x['snr_db'])==10]
                ts=[float(x['t20_s']) for x in r];ds=[float(x['component_drr_db']) for x in r]
                lines.append(f"{room+1} & {'C' if pl==0 else 'O'} & {(.15,.3,.6)[rt]:.2f} & {min(ts):.4f}--{max(ts):.4f} & {min(ds):.2f} to {max(ds):.2f} & {min(float(x['t20_r2']) for x in r):.4f}"+r'\\')
    lines += [r'\bottomrule\end{tabular}\end{table}'];(folder/'supp_room_table.tex').write_text('\n'.join(lines)+'\n')
    rows=read('factorial_contrasts.csv')
    lines=[r'\begin{table}[htbp]\centering\small',r'\caption{Factorial squared-error contrasts over the 72 paired scenes. Units are deg$^2$. Positive rounding means Q minus F; onset means O minus S; reflections means R minus D.}',r'\begin{tabular}{@{}lrrr@{}}\toprule',r'Contrast & Estimate & Lower 95\% & Upper 95\%\\\midrule']
    for r in rows:
        if r['group']=='all' and r['metric']=='squared_deg2':
            lines.append(r['contrast'].replace(':',r' $\times$ ')+' & '+f"{float(r['estimate']):.4f} & {float(r['ci_low']):.4f} & {float(r['ci_high']):.4f}"+r'\\')
    lines += [r'\bottomrule\end{tabular}\end{table}'];(folder/'supp_contrast_table.tex').write_text('\n'.join(lines)+'\n')
    report=OUT/'reproduction/clean_environment_report.json'
    if report.exists():
        r=json.loads(report.read_text());assert r['passed']
        text='A fresh Python environment with the pinned packages reproduced the numerical checks, '+f"{r['main_frames']:,}"+' primary estimates in three complete scenes, and the six main PNG figures. The maximum reproduced main-estimate difference was '+f"{max(x['max_angular_difference_deg'] for x in r['scenes']):.3g}"+' degrees. All other frame identities and failure flags matched exactly. The six main PNG files were byte-identical. The recorded reference runs included the complete direct-path sweep, the joint final duration/domain check, and the independent final room reference. This was a representative reproduction, not another full revised campaign. The complete report is supplied as a machine-readable JSON file.\n'
    else:text='The clean-environment reproduction is being completed for this internal draft; its final scope and outcomes will be inserted before delivery.\n'
    (folder/'supp_reproduction.tex').write_text(text)
    print('Five result tables and the reproduction statement generated from retained outputs.')


if __name__=='__main__':run()
