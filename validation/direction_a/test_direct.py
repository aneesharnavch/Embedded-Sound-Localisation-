"""Physical/numerical correctness checks, independent of historical scores."""
import itertools
from dataclasses import replace
import numpy as np
from . import reference
from .common import (triangle, plane_arrivals, spherical_arrivals, solve_arrivals,
                     wrapped_error, EstimatorConfig, rng_for)
from .estimator import estimate
from .signals import tone_parameters, direct_waveforms, harmonic_signal


def test_exact_plane_and_independent_spherical_reference():
    m=triangle()
    for th in [0,90,180,-90,37.37,-179.87]:
        assert abs(wrapped_error(solve_arrivals(plane_arrivals(th,m),m),th)) < 1e-10
        for dist in [.5,1.5,5,20]:
            ts=spherical_arrivals(th,dist,m)
            rt=reference.exact_times(th,dist,m.tolist())
            assert np.max(abs(ts-rt)) < 1e-16
            assert abs(wrapped_error(solve_arrivals(ts,m),reference.direction(rt,m.tolist()))) < 1e-9


def test_channel_permutations_preserve_direction():
    m=triangle(); t=spherical_arrivals(37.37,1.5,m)
    truth=solve_arrivals(t,m)
    x,_=direct_waveforms(t,48000,2048,tone_parameters())
    est=estimate(x,m)
    for order in itertools.permutations(range(3)):
        ix=list(order)
        assert abs(wrapped_error(solve_arrivals(t[ix],m[ix]),truth)) < 1e-10
        assert abs(wrapped_error(estimate(x[ix],m[ix]),est)) < 1e-8


def test_harmonic_oracle_against_scalar_math():
    p=tone_parameters();t=np.array([-.0073,0,.00719,.1537])
    expected=reference.harmonic_samples(t.tolist(),*p)
    assert np.max(abs(harmonic_signal(t,p)-expected)) < 2e-12


def test_fractional_propagation_and_peak_resolution():
    m=triangle()
    for fs in [16000,48000,192000]:
        n=round(2048*fs/48000)
        cfg=replace(EstimatorConfig(),fs=fs,samples=n)
        for th in [7.37,67.37,157.37,247.37]:
            times=spherical_arrivals(th,1.5,m)
            oracle,fir=direct_waveforms(times,fs,n,tone_parameters(),half_width=64)
            assert np.linalg.norm(fir-oracle)/np.linalg.norm(oracle) < 1e-4
            actual=estimate(fir,m,cfg)
            exact=estimate(oracle,m,cfg)
            assert abs(wrapped_error(actual,exact)) < .05
            refined=estimate(oracle,m,replace(cfg,interp=64))
            assert abs(wrapped_error(exact,refined)) < .05
            assert abs(wrapped_error(exact,th)) < 2 # catches swapped lag sign


def test_feasible_pair_delays_and_independent_record_rng():
    m=triangle()
    x=rng_for('test',0,'noise').normal(size=(5,3,2048))
    _,delays=estimate(x,m,return_delays=True)
    bounds=np.array([np.linalg.norm(m[i]-m[j])/343 for i,j in [(0,1),(0,2),(1,2)]])
    assert np.all(np.abs(delays)<=bounds+1e-15)
    a=rng_for('scene',1,'source').normal(size=20)
    rng_for('another_scene').normal(size=100)
    assert np.array_equal(a,rng_for('scene',1,'source').normal(size=20))
    assert not np.array_equal(a,rng_for('scene',1,'noise').normal(size=20))
