"""Original creepy underscore: low drone + detuned music box + wind. bed(dur, seed) -> mono float array @48k."""
import numpy as np
SR = 48000

def _rev(x, t=1.6, mix=0.35, seed=1):
    r = np.random.default_rng(seed); n = int(t * SR)
    ir = r.standard_normal(n) * np.exp(-np.linspace(0, 6, n)); ir /= np.sqrt((ir ** 2).sum())
    from numpy.fft import rfft, irfft
    L = len(x) + n; N = 1 << (L - 1).bit_length()
    w = irfft(rfft(x, N) * rfft(ir, N), N)[:len(x)]
    return x * (1 - mix) + w * mix * 3

def _lp(x, a):
    y = np.empty_like(x); acc = 0.0
    for i in range(0, len(x), 1):
        acc += a * (x[i] - acc); y[i] = acc
    return y

def note(f, dur=2.2, amp=1.0, detune=0.0):
    t = np.arange(int(dur * SR)) / SR; f = f * (2 ** (detune / 1200))
    parts = [(1, 1.0, 2.2), (2.01, 0.35, 3.5), (3.02, 0.18, 5), (4.2, 0.12, 7), (5.4, 0.05, 9)]
    s = sum(a * np.sin(2 * np.pi * f * m * t) * np.exp(-t * d) for m, a, d in parts)
    att = np.minimum(1, t / 0.004)
    return s * att * amp

def bed(dur, seed=7, motif=None, step=0.62):
    r = np.random.default_rng(seed); N = int(dur * SR); t = np.arange(N) / SR
    # drone
    lfo = 0.6 + 0.4 * np.sin(2 * np.pi * 0.07 * t)
    dr = (np.sin(2 * np.pi * 55 * t) + 0.8 * np.sin(2 * np.pi * 55.35 * t) + 0.45 * np.sin(2 * np.pi * 82.2 * t + 1) + 0.25 * np.sin(2 * np.pi * 110.6 * t)) * lfo
    dr *= np.minimum(1, t / 3.0)
    # wind
    nz = r.standard_normal(N); wind = np.convolve(nz, np.ones(60) / 60, 'same'); wind = np.convolve(wind, np.ones(30) / 30, 'same')
    wind *= (0.5 + 0.5 * np.sin(2 * np.pi * 0.05 * t + 2)) ** 2 * 6
    # music box
    A4 = 440.0; semis = motif or [0, 3, 7, 5, 3, 2, -1, 0, None, 0, 3, 8, 7, 3, 5, 2, None, None]
    mb = np.zeros(N + SR * 3); k = 0; tt = 2.0
    while tt < dur - 1.0:
        s = semis[k % len(semis)]; k += 1
        if s is not None:
            seg = note(A4 * 2 ** (s / 12), 2.4, 0.5 + 0.2 * r.random(), detune=r.normal(0, 14))
            i0 = int(tt * SR); mb[i0:i0 + len(seg)] += seg
        tt += step * (1 + r.normal(0, 0.03))
        if k % len(semis) == 0: tt += step * 4
    mb = mb[:N]
    mix = 0.55 * dr / (np.abs(dr).max() + 1e-9) + 0.18 * wind / (np.abs(wind).max() + 1e-9) + 0.5 * mb / (np.abs(mb).max() + 1e-9)
    mix = _rev(mix, 2.2, 0.4, seed)
    mix *= np.minimum(1, (dur - t) / 1.5).clip(0, 1)
    return mix / (np.abs(mix).max() + 1e-9)
