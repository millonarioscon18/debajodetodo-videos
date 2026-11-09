import json, sys
sys.path.insert(0, '/home/claude/engine'); sys.path.insert(0, '/home/claude'); sys.path.insert(0, '/home/claude/miedo')
from sfx import *
from music import bed as horror_bed
tl = json.load(open('timeline.json')); L = tl['lines']; N = int((tl['dur'] + 0.3) * SR)
W_ = lambda i, s: next((w['s'] for w in L[i]['words'] if s in w['w'].lower()), L[i]['words'][0]['s'])
vo = np.zeros(N); sfx = np.zeros(N)
put(vo, 0, load_vo('vo.wav'))
for i in range(1, len(L)): put(sfx, L[i]['s'] - 0.45, whoosh(), 0.25)
EV = json.load(open('sfx.json'))
for kind, l, w, g in EV:
    t = W_(l, w) if w else L[l]['s']
    if kind == 'boom': put(sfx, t, boom(1.6, 42), g)
    elif kind == 'boomhi': put(sfx, t, boom(1.0, 60), g)
    elif kind == 'heart':
        for k in range(3): put(sfx, t + k * 0.7, heartbeat(), g)
    elif kind == 'riser': put(sfx, t - 1.0, riser(1.0), g)
    elif kind == 'thud': put(sfx, t, thud(), g)
    elif kind == 'stamp': put(sfx, t, stamp(), g)
    elif kind == 'blips':
        rc = np.random.default_rng(l)
        for k in range(30): put(sfx, t + rc.random() * 2.0, blip(2600 + rc.random() * 900), 0.12)
    elif kind == 'wind': put(sfx, t, wind(6.0), g)
    elif kind == 'slide': put(sfx, t, slide(), g)
bd = horror_bed(N / SR, seed=7); bd = np.pad(bd, (0, max(0, N - len(bd))))[:N] * 0.24
print('ok', master(vo, sfx, bd, duck=0.45))
