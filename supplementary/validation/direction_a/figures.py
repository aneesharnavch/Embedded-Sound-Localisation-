"""Deterministic, vector scientific figures from retained results only."""
from pathlib import Path
import csv,json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle,Rectangle,FancyArrowPatch
from .common import OUT,triangle
from .protocol import VARIANTS

COLORS=('#0072B2','#D55E00','#009E73','#CC79A7')
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'axes.labelsize':8,'axes.titlesize':9,
    'legend.fontsize':7,'xtick.labelsize':7,'ytick.labelsize':7,'axes.spines.top':False,'axes.spines.right':False,
    'axes.linewidth':.6,'lines.linewidth':1.3,'grid.alpha':.22,'svg.fonttype':'none','pdf.fonttype':42,
    'savefig.dpi':180})


def read(name):
    with (OUT/'results'/name).open() as f:return list(csv.DictReader(f))


def save(fig,name):
    folder=OUT/'figures';folder.mkdir(exist_ok=True)
    for ext in ('pdf','svg','png'):fig.savefig(folder/f'{name}.{ext}',bbox_inches='tight')
    plt.close(fig)


def line_ci(ax,rows,xkey,label,color,marker='o',style='-'):
    x=np.array([float(r[xkey]) for r in rows]);y=np.array([float(r['rmse_deg']) for r in rows])
    lo=np.array([float(r['rmse_ci_low']) for r in rows]);hi=np.array([float(r['rmse_ci_high']) for r in rows])
    ax.plot(x,y,style,marker=marker,markersize=3,color=color,label=label)
    ax.fill_between(x,lo,hi,color=color,alpha=.13,linewidth=0)


def run():
    fig,axes=plt.subplots(1,2,figsize=(6.9,2.45),layout='constrained')
    ax=axes[0];xy=triangle()
    ax.add_patch(Circle((0,0),.05,fill=False,color='0.6',ls=':'))
    ax.plot(*np.vstack([xy,xy[0]]).T,color='0.45',lw=.8)
    ax.scatter(*xy.T,s=27,color=COLORS[0],zorder=3)
    for k,(x,y) in enumerate(xy):ax.text(x+.004,y+.002,f'M{k+1}',fontsize=8)
    th=np.deg2rad(37.37);u=np.array([np.cos(th),np.sin(th)])
    ax.arrow(0,0,*(.077*u),width=.0008,head_width=.004,color=COLORS[1],length_includes_head=True)
    ax.text(.027,.035,'source direction',rotation=37.37,fontsize=7,color=COLORS[1])
    ax.plot([0,0],[0,.05],'k--',lw=.7);ax.text(-.023,.024,'R = 5 cm',fontsize=7)
    ax.text(-.059,-.063,'Pair spacing = 8.66 cm',fontsize=7)
    ax.set(xlim=(-.067,.08),ylim=(-.068,.068),aspect='equal',xlabel='x (m)',ylabel='y (m)',title='(a) Horizontal three-microphone array')
    ax=axes[1];ax.axis('off');ax.set_title('(b) Paired attribution controls',loc='left')
    labels=[('Arrival construction','Fractional (F)   /   Rounded (Q)'),('Source history','Steady (S)   /   Onset (O)'),('Propagation','Direct (D)   /   Reflected (R)')]
    for i,(title,label) in enumerate(labels):
        y=.77-.27*i;ax.add_patch(Rectangle((.01,y),.98,.19,transform=ax.transAxes,fill=False,edgecolor='0.65',lw=.7))
        ax.text(.04,y+.125,title,weight='bold',transform=ax.transAxes,fontsize=8)
        ax.text(.04,y+.043,label,transform=ax.transAxes,fontsize=7.5)
    ax.text(.5,.025,'Eight combinations share each source/noise record',ha='center',transform=ax.transAxes,fontsize=7)
    save(fig,'fig1_geometry_controls')
    direct=read('direct/analytic_trials.csv')
    fig,axes=plt.subplots(1,2,figsize=(6.9,2.55),layout='constrained')
    for fs,color,style in [(16000,COLORS[1],'-'),(48000,COLORS[0],'--'),(192000,COLORS[2],':')]:
        r=[x for x in direct if float(x['radius_m'])==.05 and float(x['distance_m'])==1.5 and int(x['fs_hz'])==fs]
        axes[0].plot([float(x['truth_deg']) for x in r],[float(x['rounded_signed_error_deg']) for x in r],style,color=color,lw=.75,label=f'Rounded, {fs//1000} kHz')
    axes[0].plot([float(x['truth_deg']) for x in r],[float(x['exact_signed_error_deg']) for x in r],'k-',lw=1.1,label='Exact spherical')
    axes[0].set(xlabel='Source azimuth (deg)',ylabel='Signed angular error (deg)',title='(a) Geometry and arrival rounding',xlim=(-180,180));axes[0].legend(ncol=2,fontsize=6,loc='lower center');axes[0].grid()
    pilot=json.loads((OUT/'results/pilot/summary.json').read_text());sens=json.loads((OUT/'results/sensitivity/run_summary.json').read_text())
    names=['Propagation','Image coverage','GCC sampling','SRP grid'];keys=['propagation64','extent84','correlation16','srp_grid005']
    v=[max(x['max_difference_deg'] for x in sens['refinements'] if x['refinement']==k) for k in keys]
    axes[1].bar(np.arange(4),v,color=[COLORS[0],COLORS[1],COLORS[2],COLORS[3]],width=.6,edgecolor='0.2',lw=.4)
    axes[1].axhline(.05,color='k',ls='--',lw=1,label='0.05° target')
    axes[1].set(xticks=np.arange(4),xticklabels=['Propagation\nP32 → P64','Image extent\n76 → 84','GCC factor\n8 → 16','SRP grid\n0.25° → 0.05°'],ylabel='Largest angular change (deg)',title='(b) Confirmatory subset refinement',ylim=(0,.061))
    axes[1].legend(loc='upper right',fontsize=7);axes[1].grid(axis='y')
    save(fig,'fig2_numerical_verification')
    group=read('analysis/core_group_summary.csv')
    fig,axes=plt.subplots(1,3,figsize=(6.9,2.35),layout='constrained',sharey=True)
    for room,ax in enumerate(axes):
        for snr,color,mark,sty in [(0,COLORS[1],'s','--'),(10,COLORS[0],'o','-'),(20,COLORS[2],'^',':')]:
            r=[x for x in group if int(x['room'])==room and float(x['snr_db'])==snr]
            for x in r:x['rt_s']=(.15,.3,.6)[int(x['rt_index'])]
            line_ci(ax,r,'rt_s',f'{snr} dB',color,mark,sty)
        ax.set(title=f'({"abc"[room]}) Room {room+1}: '+('6 × 5 × 3 m','5 × 4 × 2.8 m','8 × 6 × 3.2 m')[room],xlabel='Nominal RT setting (s)',xticks=[.15,.3,.6]);ax.grid()
    axes[0].set_ylabel('Wrapped-error RMSE (deg)');axes[0].legend();save(fig,'fig3_core_rooms')
    variants=read('analysis/attribution_variants.csv');onset=read('analysis/onset_trajectory.csv')
    fig,axes=plt.subplots(1,2,figsize=(6.9,2.8),layout='constrained')
    display=['F_S_D','Q_S_D','F_O_D','Q_O_D','F_S_R','Q_S_R','F_O_R','Q_O_R']
    for group,color,marker in [('low',COLORS[0],'o'),('high',COLORS[1],'s')]:
        rows=[next(x for x in variants if x['group']==group and x['variant']==v) for v in display]
        y=np.array([float(x['rmse_deg']) for x in rows]);lo=np.array([float(x['rmse_ci_low']) for x in rows]);hi=np.array([float(x['rmse_ci_high']) for x in rows])
        offset=-.12 if group=='low' else .12
        axes[0].errorbar(np.arange(8)+offset,y,yerr=[y-lo,hi-y],fmt=marker,color=color,markersize=4,capsize=2,label=f'{group.capitalize()} subset')
    axes[0].set(xticks=range(8),xticklabels=[v.replace('_','') for v in display],yscale='log',ylabel='RMSE (deg)',title='(a) Eight paired conditions at 10 dB');axes[0].legend(loc='upper left',fontsize=7);axes[0].grid(axis='y')
    for v,label,color,marker,sty in [('F_S_R','Steady',COLORS[1],'s','--'),('F_O_R','Single onset',COLORS[0],'o','-')]:
        r=[x for x in onset if x['group']=='high' and x['variant']==v]
        line_ci(axes[1],r,'midpoint_s',label,color,marker,sty)
    axes[1].set(xlabel='Time since recording begins (s)',ylabel='Frame RMSE (deg)',title='(b) High subset: source-history effect',xlim=(0,1.37),ylim=(0,60));axes[1].grid();axes[1].legend(loc='lower right')
    save(fig,'fig4_paired_attribution')
    avg=read('analysis/averaging_global_summary.csv')
    fig,axes=plt.subplots(1,2,figsize=(6.9,2.65),layout='constrained')
    for group,color,marker,sty in [('low',COLORS[0],'o','-'),('high',COLORS[1],'s','--')]:
        r=[x for x in avg if x['group']==group];line_ci(axes[0],r,'duration_s',group.capitalize()+' subset',color,marker,sty)
    axes[0].set(xscale='log',yscale='log',xlabel='Averaging duration (s)',ylabel='Held-out RMSE (deg)',title='(a) All held-out scenes');axes[0].legend();axes[0].grid(which='both')
    r=[x for x in avg if x['group']=='eligible'];line_ci(axes[1],r,'duration_s','Held-out observations',COLORS[0])
    x=[float(v['duration_s']) for v in r]
    axes[1].plot(x,[float(v['cov_prediction_rmse_deg']) for v in r],'--',color=COLORS[1],label='Bias + covariance model')
    axes[1].plot(x,[float(v['iid_prediction_rmse_deg']) for v in r],':',color='0.2',label='Bias + independent-frame model')
    axes[1].set(xscale='log',xlabel='Averaging duration (s)',ylabel='RMSE (deg)',title=f'(b) {r[0]["scenes"]} scenes passing training rule');axes[1].legend();axes[1].grid()
    save(fig,'fig5_heldout_averaging')
    precision=read('precision/criterion_trials.csv')
    fig,axes=plt.subplots(1,2,figsize=(6.9,2.6),layout='constrained')
    r=[x for x in precision if float(x['radius_m'])==.05 and float(x['distance_m'])==1.5 and int(x['fs_hz'])==48000]
    for key,label,col,sty in [('actual_rounding_shift_deg','Actual rounding shift',COLORS[0],'-'),('corner_bound_deg','Exact box bound',COLORS[1],'--'),('disk_bound_deg','Conservative disk bound','0.2',':')]:
        axes[0].plot([float(x['theta_deg']) for x in r],[float(x[key]) for x in r],sty,color=col,lw=.9,label=label)
    axes[0].set(xlabel='Source azimuth (deg)',ylabel='Change from exact spherical estimate (deg)',title='(a) Geometry-only precision criterion',xlim=(-180,180));axes[0].legend(fontsize=6.5);axes[0].grid()
    s=read('analysis/sensitivity_summary.csv');names=['base','rotation17','non_equilateral','unequal_walls','lower_band']
    for i,var in enumerate(names):
        rr=next(x for x in s if x['variation']==var and x['method']=='GCC-PHAT');y=float(rr['rmse_deg']);lo=float(rr['rmse_ci_low']);hi=float(rr['rmse_ci_high'])
        axes[1].errorbar(i,y,yerr=[[y-lo],[hi-y]],fmt='o',color=COLORS[0],capsize=3,markersize=4)
    axes[1].set(xticks=range(5),xticklabels=['Base','Rotation\n17°','Unequal\ntriangle','Unequal\nwalls','300–1700\nHz source'],ylabel='RMSE (deg)',title='(b) Fixed 24-scene sensitivity subset');axes[1].grid(axis='y')
    save(fig,'fig6_precision_sensitivity')
    scenes=read('analysis/core_scene_summary.csv');fig,axes=plt.subplots(1,3,figsize=(6.9,3.4),layout='constrained',sharey=True)
    for room,ax in enumerate(axes):
        a=np.zeros((6,12))
        for r in scenes:
            if int(r['room'])==room and float(r['snr_db'])==10:a[int(r['placement'])*3+int(r['rt_index']),int(r['angle_index'])]=float(r['rmse_deg'])
        im=ax.imshow(a,aspect='auto',cmap='viridis',vmin=0,vmax=90)
        ax.set(title=f'Room {room+1}',xlabel='Direction index',xticks=[0,3,6,9],yticks=range(6),yticklabels=['C / .15','C / .30','C / .60','O / .15','O / .30','O / .60'])
    fig.colorbar(im,ax=axes,label='RMSE (deg)',shrink=.75);save(fig,'supp_core_scene_map')
    manifest={'generator':'validation/direction_a/figures.py','provenance':'Deterministic matplotlib figures generated with AI-authored plotting code from retained simulation results. No generative-image model was used.',
        'figures':[p.name for p in sorted((OUT/'figures').glob('fig*.pdf'))]}
    (OUT/'figures/manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('Six main figures and one supplement figure saved as PDF, SVG and PNG.')


if __name__=='__main__':run()
