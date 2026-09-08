'''Generate publication figures from the tables in rebaseline_results.md.

Only tabulated simulation results are plotted. No hardware result is inferred or
fabricated. Each figure is emitted as a 300 dpi PNG and a vector SVG.
'''

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use('Agg')

import matplotlib.pyplot as plt
import numpy as np


SOURCE_NOTE = (
    'Source: rebaseline_results.md, sections 4.1--4.5 and 7.3. '
    'Values are transcribed from the reported tables; hardware data are excluded.'
)

FIGURE_STEMS = (
    'fig_free_field_snr',
    'fig_reverb_estimators',
    'fig_confidence_ablation',
    'fig_resource_scaling',
    'fig_bias_floor',
    'fig_compute_envelope',
)

COLORS = {
    'Proposed': '#0072B2',
    'GCC-PHAT': '#009E73',
    'SRP-PHAT': '#E69F00',
    'MUSIC': '#D55E00',
    'Weight only': '#CC79A7',
    'Gate only': '#56B4E9',
}

MARKERS = {
    'Proposed': 'o',
    'GCC-PHAT': 's',
    'SRP-PHAT': '^',
    'MUSIC': 'D',
    'Weight only': '^',
    'Gate only': 's',
}


def _set_style() -> None:
    plt.rcParams.update(
        {
            'font.size': 9,
            'axes.titlesize': 10,
            'axes.labelsize': 9,
            'legend.fontsize': 8,
            'xtick.labelsize': 8,
            'ytick.labelsize': 8,
            'axes.spines.top': False,
            'axes.spines.right': False,
            'axes.grid': True,
            'grid.alpha': 0.25,
            'grid.linewidth': 0.6,
            'figure.dpi': 120,
            'savefig.dpi': 300,
            'svg.fonttype': 'none',
        }
    )


def bias_floor_rmse(t, bias: float, sigma_one: float):
    '''Evaluate sqrt(bias^2 + sigma_one^2 / t).'''
    values = np.sqrt(bias**2 + sigma_one**2 / np.asarray(t, dtype=float))
    return float(values) if values.ndim == 0 else values


def _save(fig: plt.Figure, output_dir: Path, stem: str) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    png = output_dir / f'{stem}.png'
    svg = output_dir / f'{stem}.svg'
    fig.savefig(
        png,
        bbox_inches='tight',
        facecolor='white',
        metadata={'Description': SOURCE_NOTE},
    )
    fig.savefig(
        svg,
        bbox_inches='tight',
        facecolor='white',
        metadata={'Description': SOURCE_NOTE},
    )
    plt.close(fig)
    return [png, svg]


def _errorbar(ax, x, y, yerr, label: str, **kwargs) -> None:
    ax.errorbar(
        x,
        y,
        yerr=yerr,
        label=label,
        color=COLORS[label],
        marker=MARKERS[label],
        markersize=4,
        linewidth=1.4,
        capsize=2,
        **kwargs,
    )


def make_free_field_snr(output_dir: Path) -> list[Path]:
    snr = np.array([0, 5, 10, 20, 40])
    data = {
        'Proposed': {
            'median': [0.529, 0.308, 0.212, 0.127, 0.108],
            'median_se': [0.015, 0.009, 0.006, 0.004, 0.004],
            'rmse': [0.750, 0.456, 0.301, 0.176, 0.148],
            'rmse_se': [0.014, 0.009, 0.006, 0.003, 0.003],
        },
        'GCC-PHAT': {
            'median': [0.527, 0.308, 0.212, 0.125, 0.108],
            'median_se': [0.016, 0.009, 0.007, 0.004, 0.004],
            'rmse': [0.749, 0.456, 0.301, 0.176, 0.148],
            'rmse_se': [0.014, 0.009, 0.006, 0.003, 0.003],
        },
        'SRP-PHAT': {
            'median': [0.558, 0.358, 0.275, 0.258, 0.250],
            'median_se': [0.018, 0.013, 0.010, 0.008, 0.009],
            'rmse': [0.792, 0.523, 0.390, 0.309, 0.295],
            'rmse_se': [0.015, 0.010, 0.007, 0.005, 0.004],
        },
        'MUSIC': {
            'median': [1.008, 0.592, 0.358, 0.258, 0.250],
            'median_se': [0.034, 0.023, 0.014, 0.008, 0.009],
            'rmse': [6.470, 5.096, 0.697, 0.346, 0.290],
            'rmse_se': [1.984, 1.847, 0.036, 0.013, 0.004],
        },
    }

    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.0), sharex=True)
    for method, values in data.items():
        _errorbar(axes[0], snr, values['median'], values['median_se'], method)
        _errorbar(axes[1], snr, values['rmse'], values['rmse_se'], method)

    axes[0].set_title('(a) Median absolute error')
    axes[1].set_title('(b) RMSE exposes MUSIC outliers')
    for ax in axes:
        ax.set_xlabel('SNR (dB)')
        ax.set_ylabel('Azimuth error (deg)')
        ax.set_yscale('log')
        ax.set_xticks(snr)
    axes[1].legend(frameon=False, ncol=2, loc='upper right')
    fig.suptitle('Free-field accuracy is monotone after band-limited PHAT weighting', y=1.02)
    fig.tight_layout()
    return _save(fig, output_dir, FIGURE_STEMS[0])


def make_reverb_estimators(output_dir: Path) -> list[Path]:
    rt60 = np.array([0.05, 0.10, 0.20, 0.30, 0.45, 0.60, 0.80])
    median = {
        'Proposed': ([0.446, 0.460, 1.897, 2.565, 2.775, 2.757, 2.876], [0.124, 0.354, 0.195, 0.090, 0.111, 0.088, 0.111]),
        'GCC-PHAT': ([0.444, 0.444, 1.882, 2.630, 2.920, 2.948, 3.030], [0.202, 0.280, 0.220, 0.107, 0.092, 0.102, 0.107]),
        'SRP-PHAT': ([0.444, 0.444, 1.778, 2.667, 2.667, 2.667, 2.667], [0.324, 0.265, 0.333, 0.051, 0.006, 0.025, 0.043]),
        'MUSIC': ([0.778, 1.000, 2.667, 3.333, 3.444, 3.667, 3.667], [0.351, 0.391, 0.081, 0.327, 0.200, 0.162, 0.129]),
    }
    rmse = {
        'Proposed': ([3.018, 3.013, 3.075, 3.540, 3.991, 4.280, 4.661], [0.072, 0.072, 0.078, 0.099, 0.116, 0.132, 0.149]),
        'GCC-PHAT': ([3.018, 3.013, 3.189, 3.630, 4.044, 4.402, 4.736], [0.072, 0.072, 0.081, 0.101, 0.115, 0.132, 0.149]),
        'SRP-PHAT': ([3.134, 3.156, 3.129, 3.504, 3.976, 4.300, 4.639], [0.076, 0.076, 0.079, 0.099, 0.119, 0.140, 0.160]),
        'MUSIC': ([3.093, 3.091, 14.020, 28.446, 31.420, 36.113, 30.445], [0.076, 0.075, 2.989, 2.857, 2.779, 2.949, 2.841]),
    }

    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.0), sharex=True)
    for method in median:
        _errorbar(axes[0], rt60, *median[method], method)
        _errorbar(axes[1], rt60, *rmse[method], method)
    axes[0].set_title('(a) Median error remains moderate')
    axes[1].set_title('(b) MUSIC develops catastrophic tails')
    for ax in axes:
        ax.set_xlabel('RT60 (s)')
        ax.set_ylabel('Azimuth error (deg)')
    axes[1].legend(frameon=False, ncol=2, loc='upper left')
    fig.suptitle('Correlation estimators converge in reverberation; MUSIC does not', y=1.02)
    fig.tight_layout()
    return _save(fig, output_dir, FIGURE_STEMS[1])


def make_confidence_ablation(output_dir: Path) -> list[Path]:
    rt60 = np.array([0.05, 0.15, 0.30, 0.45, 0.60, 0.80])
    data = {
        'Proposed': ([-0.0001, -0.0245, -0.0878, -0.0721, -0.0862, -0.0672], [0.0006, 0.0037, 0.0135, 0.0145, 0.0167, 0.0183]),
        'Weight only': ([-0.0004, -0.0180, -0.0802, -0.0575, -0.0710, -0.0437], [0.0005, 0.0032, 0.0107, 0.0137, 0.0154, 0.0179]),
        'Gate only': ([0.0004, -0.0093, -0.0150, -0.0167, -0.0203, -0.0179], [0.0004, 0.0024, 0.0093, 0.0062, 0.0088, 0.0071]),
    }
    offsets = {'Proposed': -0.008, 'Weight only': 0.0, 'Gate only': 0.008}

    fig, ax = plt.subplots(figsize=(5.2, 3.2))
    ax.axhline(0, color='0.25', linewidth=1)
    for method, (difference, se) in data.items():
        _errorbar(ax, rt60 + offsets[method], difference, se, method)
    ax.set_xlabel('RT60 (s)')
    ax.set_ylabel('Paired change in |error| (deg)')
    ax.set_title('Confidence logic is statistically detectable but practically small')
    ax.text(0.79, -0.099, 'negative = better', ha='right', va='bottom', color='0.35')
    ax.legend(frameon=False, ncol=3, loc='lower center')
    fig.tight_layout()
    return _save(fig, output_dir, FIGURE_STEMS[2])


def make_resource_scaling(output_dir: Path) -> list[Path]:
    radius = np.array([2, 3, 5, 8, 12], dtype=float)
    radius_median = np.array([0.459, 0.338, 0.203, 0.126, 0.087])
    radius_se = np.array([0.017, 0.017, 0.010, 0.007, 0.004])
    snapshots = np.array([256, 512, 1024, 2048, 4096], dtype=float)
    snapshot_median = np.array([0.554, 0.390, 0.273, 0.219, 0.149])
    snapshot_se = np.array([0.026, 0.014, 0.011, 0.010, 0.006])

    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.0))
    axes[0].errorbar(radius, radius_median, yerr=radius_se, color=COLORS['GCC-PHAT'], marker='o', capsize=2, label='measured')
    axes[0].plot(radius, 0.203 * (radius / 5) ** -1, '--', color='0.35', label='1/R reference')
    axes[0].set_xlabel('Array radius R (cm)')
    axes[0].set_ylabel('Median azimuth error (deg)')
    axes[0].set_title('(a) Aperture slope: -0.946 ± 0.032')

    axes[1].errorbar(snapshots, snapshot_median, yerr=snapshot_se, color=COLORS['Proposed'], marker='o', capsize=2, label='measured')
    axes[1].plot(snapshots, 0.219 * (snapshots / 2048) ** -0.5, '--', color='0.35', label='N^-1/2 reference')
    axes[1].set_xlabel('Snapshot length N (samples)')
    axes[1].set_ylabel('Median azimuth error (deg)')
    axes[1].set_title('(b) Snapshot slope: -0.461 ± 0.020')

    for ax in axes:
        ax.set_xscale('log', base=2)
        ax.set_yscale('log')
        ax.legend(frameon=False)
    axes[0].set_xticks(radius, labels=['2', '3', '5', '8', '12'])
    axes[1].set_xticks(snapshots, labels=['256', '512', '1024', '2048', '4096'])
    fig.suptitle('Accuracy follows aperture and snapshot scaling laws', y=1.02)
    fig.tight_layout()
    return _save(fig, output_dir, FIGURE_STEMS[3])


def make_bias_floor(output_dir: Path) -> list[Path]:
    frames = np.array([1, 2, 4, 8, 16, 32, 64, 128], dtype=float)
    measured = {
        'free field': ([0.308, 0.218, 0.153, 0.109, 0.076, 0.054, 0.038, 0.027], [0.001] * 8),
        'RT60 0.15 s': ([1.572, 1.527, 1.503, 1.492, 1.486, 1.483, 1.482, 1.481], [0.010, 0.014, 0.020, 0.029, 0.040, 0.057, 0.081, 0.115]),
        'RT60 0.30 s': ([2.351, 2.173, 2.076, 2.028, 2.002, 1.988, 1.981, 1.978], [0.010, 0.013, 0.017, 0.024, 0.033, 0.046, 0.065, 0.092]),
        'RT60 0.60 s': ([3.180, 2.883, 2.725, 2.638, 2.597, 2.574, 2.564, 2.557], [0.012, 0.015, 0.018, 0.024, 0.032, 0.044, 0.062, 0.087]),
    }
    fits = {
        'free field': (0.000, 0.308),
        'RT60 0.15 s': (1.480, 0.529),
        'RT60 0.30 s': (1.977, 1.272),
        'RT60 0.60 s': (2.553, 1.896),
    }
    palette = {
        'free field': '#000000',
        'RT60 0.15 s': '#009E73',
        'RT60 0.30 s': '#E69F00',
        'RT60 0.60 s': '#D55E00',
    }
    dense = np.geomspace(1, 128, 300)

    fig, ax = plt.subplots(figsize=(5.5, 3.5))
    for label, (values, se) in measured.items():
        color = palette[label]
        ax.errorbar(frames, values, yerr=se, color=color, marker='o', linestyle='none', markersize=4, capsize=2, label=f'{label}: measured')
        bias, sigma_one = fits[label]
        ax.plot(dense, bias_floor_rmse(dense, bias, sigma_one), color=color, linewidth=1.4, label=f'{label}: fit')
    ax.set_xscale('log', base=2)
    ax.set_yscale('log')
    ax.set_xticks(frames, labels=[str(int(value)) for value in frames])
    ax.set_xlabel('Accumulated frames T')
    ax.set_ylabel('Azimuth RMSE (deg)')
    ax.set_title('Accumulation removes variance but not reverberation bias')
    ax.legend(frameon=False, ncol=2, fontsize=7)
    fig.tight_layout()
    return _save(fig, output_dir, FIGURE_STEMS[4])


def make_compute_envelope(output_dir: Path) -> list[Path]:
    methods = ['Proposed', 'GCC-PHAT', 'SRP-PHAT', 'MUSIC']
    mflop = [4.522, 4.227, 4.251, 3.193]
    rmse = [0.301, 0.301, 0.390, 0.697]
    rmse_se = [0.006, 0.006, 0.007, 0.036]

    fig, ax = plt.subplots(figsize=(5.2, 3.2))
    for method, x, y, err in zip(methods, mflop, rmse, rmse_se):
        ax.errorbar(x, y, yerr=err, color=COLORS[method], marker=MARKERS[method], markersize=7, capsize=2, linestyle='none')
        offset = (5, 5) if method != 'GCC-PHAT' else (5, -13)
        ax.annotate(method, (x, y), xytext=offset, textcoords='offset points', fontsize=8)
    ax.set_xlabel('Analytical cost (MFLOP/frame)')
    ax.set_ylabel('Free-field RMSE at 10 dB (deg)')
    ax.set_title('More decision logic does not improve the accuracy-compute envelope')
    ax.set_xlim(3.0, 4.8)
    ax.set_ylim(0.24, 0.76)
    fig.tight_layout()
    return _save(fig, output_dir, FIGURE_STEMS[5])


def generate_all(output_dir: Path) -> list[Path]:
    _set_style()
    output_dir = Path(output_dir)
    generated = []
    for make_figure in (
        make_free_field_snr,
        make_reverb_estimators,
        make_confidence_ablation,
        make_resource_scaling,
        make_bias_floor,
        make_compute_envelope,
    ):
        generated.extend(make_figure(output_dir))
    return generated


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        'output_dir',
        nargs='?',
        type=Path,
        default=Path(__file__).resolve().parent / 'generated',
    )
    args = parser.parse_args()
    for path in generate_all(args.output_dir):
        print(path)


if __name__ == '__main__':
    main()
