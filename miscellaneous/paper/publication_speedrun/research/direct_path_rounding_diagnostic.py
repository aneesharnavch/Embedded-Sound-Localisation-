"""Independent geometric check, using only Python's standard library.

This is an analytic direct-path diagnostic, not an end-to-end waveform/GCC test.
Geometry and seven directions reproduce the current benchmark's settings, but
this implementation imports none of its estimator or propagation code.
Run with Python 3; JSON is written to standard output.
"""
import json
import math

C = 343.0
R = 0.05
DISTANCE = 1.5
MICS = [(R * math.cos(math.radians(a)), R * math.sin(math.radians(a)))
        for a in (90, 210, 330)]
PAIRS = [(0, 1), (0, 2), (1, 2)]
A = [(MICS[i][0] - MICS[j][0], MICS[i][1] - MICS[j][1])
     for i, j in PAIRS]


def direction(times):
    """Solve the two-component far-field least-squares system explicitly."""
    rhs = [-C * (times[i] - times[j]) for i, j in PAIRS]
    xx = sum(x*x for x, y in A)
    yy = sum(y*y for x, y in A)
    xy = sum(x*y for x, y in A)
    xb = sum(a[0]*v for a, v in zip(A, rhs))
    yb = sum(a[1]*v for a, v in zip(A, rhs))
    determinant = xx*yy - xy*xy
    ux = (yy*xb - xy*yb) / determinant
    uy = (xx*yb - xy*xb) / determinant
    return math.degrees(math.atan2(uy, ux))


def error(estimated, true):
    return (estimated - true + 180.0) % 360.0 - 180.0


def rmse(errors):
    return math.sqrt(sum(e*e for e in errors) / len(errors))


def evaluate(angles, sample_rate):
    exact_errors, rounded_errors = [], []
    for theta in angles:
        sx = DISTANCE * math.cos(math.radians(theta))
        sy = DISTANCE * math.sin(math.radians(theta))
        times = [math.hypot(sx-x, sy-y)/C for x, y in MICS]
        rounded = [round(t*sample_rate)/sample_rate for t in times]
        exact_errors.append(error(direction(times), theta))
        rounded_errors.append(error(direction(rounded), theta))
    return {
        'rounded_arrival_rmse_deg': rmse(rounded_errors),
        'exact_spherical_delay_far_field_solve_rmse_deg': rmse(exact_errors),
        'max_abs_rounded_deg': max(map(abs, rounded_errors)),
    }


if __name__ == '__main__':
    angle_sets = {
        'existing_7': [a + (i+0.5)/7 - 0.5
                       for i, a in enumerate(range(-120, 121, 40))],
        'full_circle_720': [-180 + 0.5*i + 0.13 for i in range(720)],
    }
    result = {label: {str(fs): evaluate(angles, fs)
                      for fs in (16000, 48000, 96000, 192000)}
              for label, angles in angle_sets.items()}
    result['caveat'] = ('Analytic noiseless direct-path delay diagnostic; not a new '
                        'end-to-end GCC-PHAT benchmark or correction of published '
                        'draft numbers. It isolates a possible propagation-delay '
                        'discretization confound.')
    result['configuration'] = {
        'speed_m_s': C, 'circumradius_m': R, 'source_distance_m': DISTANCE,
        'microphones_xy_m': MICS, 'angles_deg': angle_sets,
        'implementation': 'Independent standard-library geometry and 2x2 least squares',
    }
    print(json.dumps(result, indent=2))
