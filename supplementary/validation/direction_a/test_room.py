"""Independent checks of room geometry, propagation, and recording history."""
from dataclasses import replace
import numpy as np
from .room import RoomConfig,positions,build_rirs,reflection_coefficients,room_metrics
from .reference_room import image_response,direct_response
from .recording import inputs,render_record


def transform(h,f,fs):
    return h@np.exp(-2j*np.pi*np.arange(h.shape[-1])[:,None]/fs*f[None,:])


def test_room_direct_path_matches_exact_frequency_reference():
    cfg=RoomConfig(reflections=False,path_duration_s=.2)
    m,s,_=positions(cfg);h,_=build_rirs(cfg)
    f=np.linspace(300,3400,31)
    exact=direct_response(m,s,f)
    actual=transform(h,f,cfg.fs)
    assert np.linalg.norm(actual-exact)/np.linalg.norm(exact)<1e-4


def test_independent_reflection_enumeration_and_fractional_response():
    for weights in [(1.,)*6,(.4,1.6,.8,1.2,.7,1.3)]:
        cfg=RoomConfig(image_extent=3,path_duration_s=.4,absorption_multipliers=weights,
                       array_fraction=(.6,.45,.5),theta_deg=127.37)
        m,s,_=positions(cfg);h,meta=build_rirs(cfg)
        f=np.linspace(300,3400,31)
        exact,count=image_response(cfg.dimensions,m,s,reflection_coefficients(cfg),cfg.image_extent,cfg.path_duration_s,f)
        assert count==meta['path_counts']
        assert np.linalg.norm(transform(h,f,cfg.fs)-exact)/np.linalg.norm(exact)<1e-4


def test_record_pairing_startup_and_direct_snr():
    cfg=RoomConfig(reflections=False,path_duration_s=.2)
    direct,_=build_rirs(cfg)
    a=inputs(cfg,direct,4,2,10.,experiment='test')
    b=inputs(cfg,direct,4,2,10.,experiment='test')
    assert np.array_equal(a['source'],b['source'])
    assert np.array_equal(a['noise'],b['noise'])
    assert abs(10*np.log10(a['reference_power']/np.mean(a['noise']**2))-10)<1e-10
    steady=render_record(direct,a,cfg.fs)
    onset=render_record(direct,a,cfg.fs,startup=True)
    assert np.linalg.norm(onset[0]-steady[0])>0
    assert np.max(abs(onset[-1]-steady[-1]))<1e-7
