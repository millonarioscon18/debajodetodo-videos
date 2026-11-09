import json, numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfilt, resample_poly
SR = 48000
rng = np.random.default_rng(7)
bp = lambda x, lo, hi: sosfilt(butter(2, [lo, hi], 'band', fs=SR, output='sos'), x)
lp = lambda x, f: sosfilt(butter(2, f, 'low', fs=SR, output='sos'), x)
hp = lambda x, f: sosfilt(butter(2, f, 'high', fs=SR, output='sos'), x)
ts = lambda d: np.arange(int(d * SR)) / SR
def env(n, a=0.005, d=0.2):
    t = np.arange(n) / SR; return np.minimum(1, t / a) * np.exp(-t / d)
def put(buf, t, x, g=1.0):
    i = int(t * SR)
    if i < 0: x = x[-i:]; i = 0
    if i >= len(buf): return
    x = x[:len(buf) - i]; buf[i:i + len(x)] += x * g
def load_vo(path):
    sr, a = wavfile.read(path); a = a.astype(float) / 32768
    if a.ndim > 1: a = a.mean(1)
    if sr != SR: a = resample_poly(a, SR, sr)
    a = hp(a, 70); return a / (np.sqrt((a[np.abs(a) > 0.01] ** 2).mean()) + 1e-9) * 0.11
def whoosh(d=0.5):
    t = ts(d); x = rng.standard_normal(len(t)); return (bp(x, 250, 1500) * 0.6 + bp(x, 1500, 6000) * 0.3) * np.sin(np.pi * t / d) ** 3 * 0.5
def blip(f=880):
    t = ts(0.35); return (np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * f * 1.5 * t)) * env(len(t), 0.003, 0.08) * 0.25
def stamp():
    t = ts(0.8); return (lp(rng.standard_normal(len(t)), 1800) * np.exp(-t / 0.04) + np.sin(2 * np.pi * 75 * t) * np.exp(-t / 0.18)) * 0.8
def ding():
    t = ts(1.2); return sum(np.sin(2 * np.pi * f * t) * a for f, a in [(1568, 1), (2349, .5), (3136, .3)]) * env(len(t), 0.002, 0.35) * 0.3
def boom(d=1.5, f0=60):
    t = ts(d); f = f0 * np.exp(-t * 1.2) + 30; return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.5) * 0.9
def thud():
    t = ts(0.6); return (np.sin(2 * np.pi * (45 + 40 * np.exp(-t * 20)) * t) * np.exp(-t / 0.15) + lp(rng.standard_normal(len(t)), 500) * np.exp(-t / 0.05) * 0.6) * 0.9
def buzz(d):
    t = ts(d); x = np.sign(np.sin(2 * np.pi * 100 * t)) * 0.08 + bp(rng.standard_normal(len(t)), 2000, 6000) * 0.05; return x * (0.5 + 0.5 * (np.sin(2 * np.pi * 13 * t) > 0))
def hum(d):
    t = ts(d); return (np.sin(2 * np.pi * 60 * t) * 0.5 + np.sin(2 * np.pi * 120 * t) * 0.25 + lp(rng.standard_normal(len(t)), 300) * 0.3) * 0.15
def bell(d=1.6):
    t = ts(d); r = (np.sin(2 * np.pi * 22 * t) > 0).astype(float)
    return (np.sin(2 * np.pi * 1800 * t) * 0.5 + np.sin(2 * np.pi * 2700 * t) * 0.3) * r * 0.18 * np.minimum(1, (d - t) / 0.1)
def dtmf(lo, hi, d=0.16):
    t = ts(d); return (np.sin(2 * np.pi * lo * t) + np.sin(2 * np.pi * hi * t)) * 0.12 * np.minimum(1, np.minimum(t, d - t) / 0.01)
def twang():
    t = ts(1.2); f = 180 * np.exp(-t * 2) + 60; x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.4)
    return (x + bp(rng.standard_normal(len(t)), 2000, 7000) * np.exp(-t / 0.05) * 0.8) * 0.7
def screech(d=1.4):
    t = ts(d); f = 2400 + 300 * np.sin(2 * np.pi * 7 * t); x = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.25 + bp(rng.standard_normal(len(t)), 3000, 8000) * 0.4
    return x * np.minimum(1, t / 0.03) * np.exp(-t / (d * 0.5)) * 0.6
def slide(d=1.0):
    t = ts(d); return bp(rng.standard_normal(len(t)), 300, 2500) * np.sin(np.pi * t / d) ** 2 * 0.25
def static(d):
    t = ts(d); x = bp(rng.standard_normal(len(t)), 800, 5000); g = (rng.random(int(d * 40) + 1) > 0.3).astype(float)
    return x * np.repeat(g, int(SR / 40) + 1)[:len(t)] * 0.35
def step():
    t = ts(0.25); return (lp(rng.standard_normal(len(t)), 900) * np.exp(-t / 0.03) + np.sin(2 * np.pi * 70 * t) * np.exp(-t / 0.05) * 0.5) * 0.5
def heartbeat():
    t = ts(0.9); b = lambda o: np.sin(2 * np.pi * 50 * (t - o)) * np.exp(-np.maximum(0, t - o) / 0.06) * (t > o)
    return (b(0) + 0.7 * b(0.28)) * 0.8
def drone(d, base=55):
    t = ts(d); x = sum(np.sin(2 * np.pi * base * m * t + np.sin(2 * np.pi * 0.1 * m * t) * 2) * a for m, a in [(1, 0.5), (1.5, 0.25), (2.02, 0.2), (3.01, 0.08)])
    x += lp(rng.standard_normal(len(t)), 200) * 0.25; return x * 0.18
def wind(d):
    t = ts(d); x = bp(rng.standard_normal(len(t)), 200, 1200); m = 0.5 + 0.5 * np.sin(2 * np.pi * 0.13 * t) * np.sin(2 * np.pi * 0.07 * t + 1)
    return x * m * 0.25
def riser(d=1.5):
    t = ts(d); return bp(rng.standard_normal(len(t)), 800, 6000) * (t / d) ** 2 * 0.4
def master(vo, sfx, bed, duck=0.45, sfxg=0.6, out='mix.wav'):
    ve = lp(np.abs(vo), 6); k = np.clip(ve / 0.06, 0, 1)
    mix = vo + sfx * (1 - 0.35 * k) * sfxg + bed * (1 - duck * k)
    mix = mix / np.abs(mix).max() * 0.95
    wavfile.write(out, SR, (mix * 32767).astype(np.int16)); return len(mix) / SR
