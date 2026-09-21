"""Independent image enumeration and exact frequency-domain propagation.

Images are indexed by reflected tiles j, not the production (n,parity) formula.
No production room, path, deposition, or coefficient helper is imported.
"""
from itertools import product,islice
import numpy as np


def image_response(dimensions,microphones,source,coefficients,extent,duration,frequencies,c=343.):
    frequencies=np.asarray(frequencies)
    axes=[]
    for length,position,lo,hi in zip(dimensions,source,coefficients[0::2],coefficients[1::2]):
        axis=[]
        # Equivalent explicit rectangular image-domain boundary, independent indexing.
        for j in range(-2*extent-1,2*extent+1):
            point=j*length+(position if j%2==0 else length-position)
            n=abs(j);first=(n+1)//2;second=n//2
            left,right=(first,second) if j<0 else (second,first)
            axis.append((point,lo**left*hi**right))
        axes.append(axis)
    response=np.zeros((len(microphones),len(frequencies)),dtype=complex)
    count=np.zeros(len(microphones),dtype=int)
    iterator=product(*axes)
    while True:
        block=list(islice(iterator,10000))
        if not block:break
        images=np.array([[x[0],y[0],z[0]] for x,y,z in block])
        weights=np.array([x[1]*y[1]*z[1] for x,y,z in block])
        for i,mic in enumerate(microphones):
            r=np.sqrt(np.sum((images-mic)**2,axis=1))
            keep=r<=c*duration;r=r[keep];w=weights[keep]/(4*np.pi*r)
            count[i]+=len(r)
            response[i]+=np.sum(w[:,None]*np.exp(-2j*np.pi*r[:,None]/c*frequencies[None,:]),axis=0)
    return response,count.tolist()


def direct_response(microphones,source,frequencies,c=343.):
    r=np.sqrt(np.sum((np.asarray(microphones)-source)**2,axis=1))
    return np.exp(-2j*np.pi*r[:,None]/c*np.asarray(frequencies)[None,:])/(4*np.pi*r[:,None])
