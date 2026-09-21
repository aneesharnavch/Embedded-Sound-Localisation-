"""Read-only manuscript/result audit; all generated files stay in this audit folder."""
from pathlib import Path
import collections, contextlib, csv, gzip, hashlib, io, json, sys
import numpy as np

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT))
OUT = ROOT / 'paper/direction_a_preprint'
AUDIT = Path(__file__).resolve().parent
EVIDENCE = AUDIT / 'evidence'
RECOMPUTED = EVIDENCE / 'recomputed'
RECOMPUTED.mkdir(parents=True, exist_ok=True)

from validation.direction_a import analysis

def save_json(relative, value):
    (RECOMPUTED / Path(relative).name).write_text(json.dumps(value, indent=2) + '\n')

def write_csv(name, rows):
    with (RECOMPUTED / name).open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

analysis.save_json = save_json
analysis.write_csv = write_csv
with (EVIDENCE / 'analysis_log.txt').open('w') as log, contextlib.redirect_stdout(log):
    analysis.run()
comparisons = {}
for path in sorted(RECOMPUTED.iterdir()):
    original = OUT / 'results/analysis' / path.name
    if not original.exists():
        continue  # Audit-only diagnostics from an earlier run are not source outputs.
    if path.suffix == '.csv':
        comparisons[path.name] = path.read_bytes() == original.read_bytes()
    else:
        comparisons[path.name] = json.loads(path.read_text()) == json.loads(original.read_text())
assert all(comparisons.values()), comparisons

# Re-read the primary results independently of the production analysis loader.
records = {}
metadata = {}
counts = collections.Counter()
source_sets = collections.defaultdict(set)
noise_sets = collections.defaultdict(set)
max_wrap_discrepancy = 0.0
for path in sorted((OUT / 'results/main').glob('r*.csv.gz')):
    tag = path.name.split('.')[0]
    meta = json.loads(path.with_suffix('').with_suffix('.json').read_text())
    metadata[tag] = meta
    for rec in meta['input_records']:
        source_sets[rec['experiment']].add(rec['source_sha256'])
        noise_sets[rec['experiment']].add(rec['noise_sha256'])
    with gzip.open(path, 'rt') as f:
        for row in csv.DictReader(f):
            counts[row['experiment']] += 1
            key = (tag, row['experiment'], float(row['snr_db']), row['variant'], int(row['record_id']))
            frames = records.setdefault(key, {})
            k = int(row['frame'])
            assert k not in frames
            frames[k] = float(row['error_deg'])
            wrapped = (float(row['theta_est']) - float(row['theta_true']) + 180) % 360 - 180
            max_wrap_discrepancy = max(max_wrap_discrepancy, abs(wrapped - frames[k]))
            assert int(row['failure_gt5']) == (abs(frames[k]) > 5)
for key, frames in records.items():
    length = 128 if key[1].startswith('long_') else 32
    assert set(frames) == set(range(length))
    records[key] = np.array([frames[k] for k in range(length)])

def stack_records(tags, experiment, variant='F_S_R', snr=10.0):
    ids = range(5, 10) if experiment == 'long_holdout' else range(5)
    return np.stack([np.stack([records[(tag, experiment, snr, variant, rid)] for rid in ids]) for tag in tags])

def rmse(e):
    return float(np.sqrt(np.mean(np.asarray(e)**2)))

def circ(e, axis=-1):
    return np.rad2deg(np.angle(np.mean(np.exp(1j*np.deg2rad(e)), axis=axis)))

tags = sorted(tag for tag, m in metadata.items() if (m['indices'][1], m['indices'][2]) in ((0, 0), (1, 2)))
first_vs_blocks = []
for group in ('low', 'high'):
    selected = [tag for tag in tags if (metadata[tag]['indices'][2] == 0) == (group == 'low')]
    held = stack_records(selected, 'long_holdout')
    for n in (1, 2, 4, 8, 16, 32, 64, 128):
        prefix = circ(held[:, :, :n])
        blocks = circ(held.reshape(len(selected), 5, 128//n, n))
        first_vs_blocks.append({'group': group, 'frames_averaged': n,
            'first_N_rmse_deg': rmse(prefix), 'all_blocks_rmse_deg': rmse(blocks),
            'first_N_estimates': int(prefix.size), 'all_block_estimates': int(blocks.size)})
write_csv('first_N_versus_all_blocks.csv', first_vs_blocks)

core_points = []
for rt in range(3):
    selected = [tag for tag in metadata if metadata[tag]['indices'][2] == rt]
    for snr in (0.0, 10.0, 20.0):
        values = stack_records(selected, 'core', snr=snr)
        core_points.append({'rt_index': rt, 'snr_db': snr, 'rmse_deg': rmse(values),
            'gt5_fraction': float(np.mean(abs(values)>5))})

variants = {}
for variant in ('F_S_D', 'Q_S_D', 'F_S_R', 'Q_S_R', 'F_O_R'):
    exp = 'core' if variant == 'F_S_R' else 'attribution'
    variants[variant] = stack_records(tags, exp, variant)
high = [tag for tag in tags if metadata[tag]['indices'][2] == 2]
onset = stack_records(high, 'attribution', 'F_O_R')
steady = stack_records(high, 'core')

# Quantify the limited covariance model rather than treating concentration as a guarantee.
eligible = []
covariances = []
for tag in tags:
    train = stack_records([tag], 'long_train')[0]
    z = np.mean(np.exp(1j*np.deg2rad(train)))
    b = np.rad2deg(np.angle(z))
    if abs(z) >= .95 and abs(b) <= 15:
        eligible.append(tag)
        centered = (train-b+180)%360-180
        means = centered.mean(axis=1)
        pooled = centered - centered.mean()
        within = centered - means[:, None]
        covariances.append({'scene': tag, 'pooled_variance_deg2': float(np.mean(pooled**2)),
            'within_record_variance_deg2': float(np.mean(within**2)),
            'record_mean_variance_deg2': float(np.var(means)),
            'training_errors_gt90': int(np.sum(abs(train)>90))})
write_csv('eligible_covariance_diagnostics.csv', covariances)

report = {
    'primary_counts': dict(counts), 'physical_scenes': len(metadata),
    'analysis_files_match': comparisons,
    'independent_angular_error_check_max_difference_deg': max_wrap_discrepancy,
    'source_train_holdout_overlap': len(source_sets['long_train'] & source_sets['long_holdout']),
    'noise_train_holdout_overlap': len(noise_sets['long_train'] & noise_sets['long_holdout']),
    'core_points_independent': core_points,
    'variant_rmse_independent': {key: rmse(value) for key,value in variants.items()},
    'rounding_direct_MSE_change': float(np.mean(variants['Q_S_D']**2-variants['F_S_D']**2)),
    'rounding_reflected_MSE_change': float(np.mean(variants['Q_S_R']**2-variants['F_S_R']**2)),
    'startup_high_first_frame_RMSE': {'onset': rmse(onset[:,:,0]), 'steady': rmse(steady[:,:,0])},
    'startup_high_last_frame_RMSE': {'onset': rmse(onset[:,:,-1]), 'steady': rmse(steady[:,:,-1])},
    'eligible_scenes': len(eligible),
    'first_N_versus_all_blocks': first_vs_blocks,
}
(EVIDENCE / 'independent_audit.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({'matched_analysis_files': sum(comparisons.values()), 'analysis_files': len(comparisons),
                  'primary_counts': dict(counts), 'first_N': [r for r in first_vs_blocks if r['frames_averaged']==1],
                  'eligible_scenes': len(eligible)}, indent=2))
