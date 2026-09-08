import numpy as np
from .common import triangle,wrapped_error
from .signals import direct_waveforms
from .srp import estimate_srp


def test_srp_plane_sign_and_refinement():
    # An independent periodic harmonic construction avoids interpolated steering delays.
    xy=triangle();fs=48000;t=(np.arange(2048)+7000)/fs
    freq=np.linspace(340,3300,49);phase=np.arange(49)**1.3
    for theta in (0.,37.37,90.,-120.):
        u=np.array([np.cos(np.deg2rad(theta)),np.sin(np.deg2rad(theta))])
        delay=-xy@u/343
        x=np.sum(np.cos(2*np.pi*freq[None,:,None]*(t[None,None,:]-delay[:,None,None])+phase[None,:,None]),axis=1)
        a=estimate_srp(x,xy);b=estimate_srp(x,xy,step=.05)
        assert abs(wrapped_error(a,theta))<.05
        assert abs(wrapped_error(a,b))<.005
