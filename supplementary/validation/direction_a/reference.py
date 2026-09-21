"""Independent direct-path reference: standard library only, explicit 2x2 solve.

This module deliberately imports neither NumPy nor the production geometry,
propagation, estimator, or configuration functions. Constants are explicit inputs.
"""
import math


def exact_times(angle_deg, distance, coordinates, c=343.0):
    th = math.radians(angle_deg)
    if distance is None:
        return [-(x * math.cos(th) + y * math.sin(th)) / c for x, y in coordinates]
    sx, sy = distance * math.cos(th), distance * math.sin(th)
    return [math.hypot(sx - x, sy - y) / c for x, y in coordinates]


def direction(times, coordinates, c=343.0):
    xx = xy = yy = bx = by = 0.0
    for i in range(len(coordinates)):
        for j in range(i + 1, len(coordinates)):
            x = coordinates[i][0] - coordinates[j][0]
            y = coordinates[i][1] - coordinates[j][1]
            b = -c * (times[i] - times[j])
            xx += x*x
            xy += x*y
            yy += y*y
            bx += x*b
            by += y*b
    det = xx*yy - xy*xy
    if det <= 0:
        raise ValueError('Degenerate geometry')
    return math.degrees(math.atan2((xx*by - xy*bx)/det, (yy*bx - xy*by)/det))


def harmonic_samples(times, frequencies, amplitudes, phases):
    """Scalar evaluation for independent spot checks of the waveform oracle."""
    return [sum(a * math.cos(2*math.pi*f*t + p)
                for f, a, p in zip(frequencies, amplitudes, phases)) for t in times]
