"""Align a single voice take to its script.
Usage: python3 align.py take.wav script.txt out_dir [lead] [tail]
script.txt: one sentence per line, optional "who|" prefix (default obrero).
Writes out_dir/vo.wav (with lead silence) and out_dir/timeline.json (lines = sentences)."""
import json, re, sys, numpy as np
from scipy.io import wavfile

wav, script, out = sys.argv[1], sys.argv[2], sys.argv[3]
LEAD = float(sys.argv[4]) if len(sys.argv) > 4 else 0.2
TAIL = float(sys.argv[5]) if len(sys.argv) > 5 else 1.2
sr, a = wavfile.read(wav); a = a.astype(float)
if a.ndim > 1: a = a.mean(1)
a /= 32768
hop = sr // 100
e = np.array([np.sqrt((a[i:i + hop] ** 2).mean()) for i in range(0, len(a) - hop, hop)])
voiced = e > 0.06 * np.percentile(e, 99)
# silences >= 0.18 s
sil = []; k = 0
while k < len(voiced):
    if not voiced[k]:
        j = k
        while j < len(voiced) and not voiced[j]: j += 1
        if (j - k) >= 18 and k > 0 and j < len(voiced): sil.append((k, j))
        k = j
    else: k += 1

sents = []
for ln in open(script, encoding='utf-8'):
    ln = ln.strip()
    if not ln: continue
    who, txt = (ln.split('|', 1) if '|' in ln else ('obrero', ln))
    sents.append((who.strip(), txt.strip()))
toks = []  # (sent idx, word)
for si, (_, t) in enumerate(sents):
    for w in t.split(): toks.append((si, w))
wts = np.array([max(1.0, len(re.findall(r"[aeiouáéíóú]", w.lower())) + len(w) * 0.12) for _, w in toks])
# boundary after token k is "strong" if punctuation; candidate anchor points
cumw = np.concatenate([[0], np.cumsum(wts)]); tw = cumw[-1]
cumv = np.concatenate([[0], np.cumsum(voiced)]); tv = cumv[-1]
first = int(np.argmax(voiced)); last = len(voiced) - int(np.argmax(voiced[::-1]))
# anchors: (word boundary index, frame) — start and end fixed
anchors = [(0, first), (len(toks), last)]
punct = [k + 1 for k, (_, w) in enumerate(toks[:-1]) if re.search(r"[.,;:?!…]$", w) or w.endswith('...')]
# monotonic DP: match pauses (time order) to punctuation boundaries
P = sorted(sil); B = punct
def bpen(b):
    w = toks[b - 1][1]
    return 4.0 if re.search(r"[.?!]$", w) and not w.endswith('...') else (2.5 if w.endswith('...') else 0.8)
INF = 1e18; nP, nB = len(P), len(B)
D = np.full((nP + 1, nB + 1), INF); D[0, 0] = 0; bk = {}
for i in range(nP + 1):
    for j in range(nB + 1):
        if D[i, j] >= INF: continue
        if i < nP:  # skip pause
            c = D[i, j] + 0.6 + (P[i][1] - P[i][0]) / 100 * 6
            if c < D[i + 1, j]: D[i + 1, j] = c; bk[(i + 1, j)] = (i, j, None)
        if j < nB:  # skip boundary
            c = D[i, j] + bpen(B[j])
            if c < D[i, j + 1]: D[i, j + 1] = c; bk[(i, j + 1)] = (i, j, None)
        if i < nP and j < nB:
            vpos = cumv[(P[i][0] + P[i][1]) // 2] / tv; wpos = cumw[B[j]] / tw
            c = D[i, j] + ((vpos - wpos) * 25) ** 2
            if c < D[i + 1, j + 1]: D[i + 1, j + 1] = c; bk[(i + 1, j + 1)] = (i, j, (B[j], P[i]))
i, j = nP, nB
while (i, j) != (0, 0):
    pi, pj, m = bk[(i, j)]
    if m: anchors.append(m)
    i, j = pi, pj
anchors.sort()
import os
if os.environ.get("DBG"):
    for b,f in anchors: print("A", " ".join(w for _,w in toks[max(0,b-2):b]), "|", f if isinstance(f,int) else (round(f[0]/100,2), round(f[1]/100,2)))
    print("SIL", [(round(a/100,2), round(b/100,2)) for a,b in sil])
# piecewise mapping: between anchors, distribute words by voiced frames
words = []
def frame_of(anc, side):
    f = anc[1]
    return f if isinstance(f, int) else (f[1] if side == 'start' else f[0])
for (b0, f0), (b1, f1) in zip(anchors[:-1], anchors[1:]):
    fa, fb = frame_of((b0, f0), 'start'), frame_of((b1, f1), 'end')
    seg = voiced[fa:fb]; cs = np.concatenate([[0], np.cumsum(seg)]); tot = max(1, cs[-1])
    wsum = cumw[b1] - cumw[b0]
    for k in range(b0, b1):
        p0 = (cumw[k] - cumw[b0]) / wsum * tot; p1 = (cumw[k + 1] - cumw[b0]) / wsum * tot
        i0 = int(np.searchsorted(cs, max(0.5, p0))); i1 = int(np.searchsorted(cs, max(0.5, p1)))
        words.append({"w": toks[k][1], "si": toks[k][0], "s": round(LEAD + (fa + max(0, i0 - 1)) * hop / sr, 3), "e": round(LEAD + (fa + i1) * hop / sr, 3)})
lines = []
for si, (who, t) in enumerate(sents):
    ws = [dict(w=w["w"], s=w["s"], e=w["e"]) for w in words if w["si"] == si]
    lines.append({"i": si, "who": who, "text": t, "s": ws[0]["s"], "e": ws[-1]["e"], "words": ws})
DUR = round(LEAD + len(a) / sr + TAIL, 3)
fps = 30; n = int(DUR * fps) + 2; env = np.zeros(n); h2 = sr // fps
for k in range(0, len(a) - h2, h2):
    f = int(round(LEAD * fps)) + k // h2
    if f < n: env[f] = np.sqrt((a[k:k + h2] ** 2).mean())
env = np.clip(env / (np.percentile(env[env > 0], 90) + 1e-9), 0, 1).round(3).tolist()
# padded voice file
pad = np.concatenate([np.zeros(int(LEAD * sr)), a, np.zeros(int(TAIL * sr))])
wavfile.write(f"{out}/vo.wav", sr, (pad * 32767).astype(np.int16))
json.dump({"dur": DUR, "lines": lines, "env": {"obrero": env, "claude": [0] * n}, "vo": "vo.wav"}, open(f"{out}/timeline.json", "w"), ensure_ascii=False)
for L in lines: print(f"{L['i']:2d} {L['s']:6.2f}-{L['e']:6.2f}  {L['text'][:60]}")
print("DUR", DUR, "anchors", len(anchors) - 2, "of", len(punct))
