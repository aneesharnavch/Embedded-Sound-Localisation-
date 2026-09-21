"""Configuration, repeatable random streams, and provenance helpers."""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'paper' / 'direction_a_preprint'
C = 343.0


@dataclass(frozen=True)
class EstimatorConfig:
    fs: int = 48000
    samples: int = 2048
    band: tuple[float, float] = (300.0, 3400.0)
    interp: int = 8
    relative_floor: float = 1e-3
    absolute_floor: float = 1e-12
    window: str = 'symmetric_hann'
    mean_remove: bool = True
    parabolic: bool = True
    sound_speed: float = C


def canonical_hash(value):
    text = json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)
    return hashlib.sha256(text.encode()).hexdigest()


def rng_for(*identity):
    """Stable per-record streams, independent of dispatch or call order."""
    digest = hashlib.sha256(json.dumps(identity, separators=(',', ':')).encode()).digest()
    return np.random.default_rng(np.random.SeedSequence(np.frombuffer(digest, dtype='<u4')))


def save_json(relative_path, value):
    p = OUT / relative_path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
    return p


def source_hashes():
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(Path(__file__).parent.glob('*.py'))}


def triangle(radius=0.05, rotation_deg=0.0):
    a = np.deg2rad(np.array([90.0, 210.0, 330.0]) + rotation_deg)
    return radius * np.column_stack((np.cos(a), np.sin(a)))


def pairs(m):
    return [(i, j) for i in range(m) for j in range(i + 1, m)]


def wrapped_error(estimate, truth):
    return (np.asarray(estimate) - np.asarray(truth) + 180.0) % 360.0 - 180.0


def plane_arrivals(theta_deg, mic_xy, c=C):
    th = np.deg2rad(np.asarray(theta_deg))
    u = np.stack((np.cos(th), np.sin(th)), axis=-1)
    return -(u @ np.asarray(mic_xy).T) / c


def spherical_arrivals(theta_deg, distance, mic_xy, c=C):
    th = np.deg2rad(np.asarray(theta_deg))
    src = distance * np.stack((np.cos(th), np.sin(th)), axis=-1)
    ranges = np.linalg.norm(src[..., None, :] - np.asarray(mic_xy), axis=-1)
    return ranges / c


def solve_arrivals(times, mic_xy, c=C):
    ps = pairs(len(mic_xy))
    delays = np.stack([np.asarray(times)[..., i] - np.asarray(times)[..., j]
                       for i, j in ps], axis=-1)
    return solve_pairs(delays, mic_xy, c)


def solve_pairs(delays, mic_xy, c=C):
    ps = pairs(len(mic_xy))
    a = np.array([mic_xy[i] - mic_xy[j] for i, j in ps])
    if np.linalg.matrix_rank(a) != 2:
        raise ValueError('Planar direction solve requires non-collinear microphones.')
    u = (-c * np.asarray(delays)) @ np.linalg.pinv(a).T
    return np.rad2deg(np.arctan2(u[..., 1], u[..., 0]))
