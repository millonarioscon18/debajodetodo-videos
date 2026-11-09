"""compose.py DIR : aud/N.mp3 (narrator reading N lines of parts.txt) + aud/<CODE><k>.mp3 character clips
-> vo.wav + timeline.json (one line per parts.txt row, extra 'role')"""
import sys, os, re, json, subprocess, numpy as np
from scipy.io import wavfile
D = os.path.abspath(sys.argv[1]); os.chdir(D); SR = 44100; LEAD, TAIL = 0.3, 1.4
TMP = '/tmp/cmp_' + os.path.basename(D); os.makedirs(TMP, exist_ok=True)
def wav(mp3):
    out = mp3.replace('.mp3', '.wav')
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', mp3, '-ac', '1', '-ar', str(SR), out], check=True)
    return wavfile.read(out)[1].astype(np.float32) / 32768
def voicing(a):
    hop = SR // 100; e = np.array([np.sqrt((a[i:i + hop] ** 2).mean()) for i in range(0, len(a) - hop, hop)])
    return e > 0.06 * np.percentile(e, 99)
def wweight(t): return sum(max(1.0, len(re.findall(r"[aeiouáéíóú]", w.lower())) + len(w) * 0.12) for w in t.split())
parts = [l.rstrip('\n').split('|', 1) for l in open('parts.txt', encoding='utf-8') if l.strip()]
narr = [t for c, t in parts if c == 'N']
N = wav('aud/N.mp3'); v = voicing(N)
# candidate gaps
gaps = []; k = 0
while k < len(v):
    if not v[k]:
        j = k
        while j < len(v) and not v[j]: j += 1
        if j - k >= 25 and k > 0 and j < len(v): gaps.append(((k + j) / 200, (j - k) / 100))
        k = j
    else: k += 1
first = np.argmax(v) / 100; last = (len(v) - np.argmax(v[::-1])) / 100
cw = np.cumsum([wweight(t) for t in narr]); exp = [first + (last - first) * c / cw[-1] for c in cw[:-1]]
# DP: pick len(exp) gaps in order
m, n = len(exp), len(gaps); INF = 1e18
cost = lambda i, g: ((gaps[g][0] - exp[i]) / 3.0) ** 2 - 2.5 * np.log(gaps[g][1] / 0.25)
Dp = np.full((m, n), INF); bk = np.zeros((m, n), int)
for g in range(n): Dp[0, g] = cost(0, g)
for i in range(1, m):
    best, bi = INF, -1
    for g in range(n):
        if g > 0 and Dp[i - 1, g - 1] < best: best, bi = Dp[i - 1, g - 1], g - 1
        if bi >= 0: Dp[i, g] = best + cost(i, g); bk[i, g] = bi
g = int(np.argmin(Dp[m - 1])); sel = [g]
for i in range(m - 1, 0, -1): g = bk[i, g]; sel.append(g)
sel = sel[::-1]; cuts = [0] + [int(gaps[g][0] * SR) for g in sel] + [len(N)]
print('cuts', [round(c / SR, 2) for c in cuts])
def trim(a, pre=0.12, post=0.2):
    idx = np.where(np.abs(a) > 0.015)[0]
    return a[max(0, idx[0] - int(pre * SR)):idx[-1] + int(post * SR)] if len(idx) else a
peak = np.abs(N).max(); out = [np.zeros(int(LEAD * SR), np.float32)]; t = LEAD; lines = []; cnt = {}; ni = 0
for i, (c, txt) in enumerate(parts):
    if c == 'N': a = trim(N[cuts[ni]:cuts[ni + 1]]); ni += 1; gap_after = 0.35
    else:
        cnt[c] = cnt.get(c, 0) + 1; a = trim(wav(f'aud/{c}{cnt[c]}.mp3')); a = a / (np.abs(a).max() + 1e-9) * 0.9 * peak
        out.append(np.zeros(int(0.15 * SR), np.float32)); t += 0.15; gap_after = 0.45
    p = f'{TMP}/p{i}.wav'; wavfile.write(p, SR, (a * 32767).astype(np.int16)); open(p + '.txt', 'w').write(txt + '\n')
    subprocess.run(['python3', '/home/claude/engine/align.py', p, p + '.txt', TMP, '0', '0'], check=True, capture_output=True)
    L = json.load(open(TMP + '/timeline.json'))['lines'][0]
    ws = [dict(w=w['w'], s=round(w['s'] + t, 3), e=round(w['e'] + t, 3)) for w in L['words']]
    lines.append({'i': i, 'who': 'obrero', 'role': c, 'text': txt, 's': ws[0]['s'], 'e': ws[-1]['e'], 'words': ws})
    out += [a, np.zeros(int(gap_after * SR), np.float32)]; t += len(a) / SR + gap_after
out.append(np.zeros(int(TAIL * SR), np.float32)); vo = np.concatenate(out); DUR = round(len(vo) / SR, 3)
fps = 30; nfr = int(DUR * fps) + 2; env = np.zeros(nfr); h2 = SR // fps
for k in range(0, len(vo) - h2, h2):
    if k // h2 < nfr: env[k // h2] = np.sqrt((vo[k:k + h2] ** 2).mean())
env = np.clip(env / (np.percentile(env[env > 0], 90) + 1e-9), 0, 1).round(3).tolist()
wavfile.write('vo.wav', SR, (np.clip(vo, -1, 1) * 32767).astype(np.int16))
json.dump({'dur': DUR, 'lines': lines, 'env': {'obrero': env, 'claude': [0] * nfr}, 'vo': 'vo.wav'}, open('timeline.json', 'w'), ensure_ascii=False)
for L in lines: print(f"{L['i']:2d} {L['role']} {L['s']:6.2f}-{L['e']:6.2f} {L['text'][:55]}")
print('DUR', DUR)
