// Cinematic slideshow compositor: AI stills + clip frames, Ken Burns, glitch cuts, grain, captions (hud.js)
import { makeHUD, clamp, sm, eio, eout, lerp } from './hud.js';
const W = 1080, H = 1920;
const TL = await (await fetch('timeline.json')).json();
for (const [fam, url] of [['Inter', 'fonts/Inter.ttf'], ['Mont', 'fonts/Montserrat.ttf']]) { const f = new FontFace(fam, `url(${url})`, { weight: '100 900' }); await f.load(); document.fonts.add(f); }
const L = TL.lines; const C = await (await fetch('shots.json')).json();
const W_ = (i, sub) => (L[i].words.find(w => w.w.toLowerCase().includes(sub)) || L[i].words[0]).s;
const at = a => typeof a === 'number' ? a : (a.w ? W_(a.l, a.w) + (a.d || 0) : L[a.l].s - 0.15 + (a.d || 0));
function rng(seed) { let s = seed >>> 0 || 1; return () => (s = (s * 1664525 + 1013904223) >>> 0) / 4294967296; }
const loadImg = src => new Promise((res, rej) => { const im = new Image(); im.onload = () => res(im); im.onerror = rej; im.src = src; });
// shots
const shots = []; for (const s of C.shots) { const o = { ...s, t0: Math.max(0, at(s.at)) }; if (s.seq) { o.frames = []; for (let k = 1; k <= s.n; k++) o.frames.push(await loadImg(s.seq.replace('%04d', String(k).padStart(4, '0')))); } else o.im = await loadImg(s.img); shots.push(o); }
shots.sort((a, b) => a.t0 - b.t0); shots.forEach((s, k) => s.t1 = k < shots.length - 1 ? shots[k + 1].t0 : TL.dur + 0.5);
const pulses = (C.pulses || []).map(at); const flashes = (C.flashes || []).map(at);
// grain
const grains = []; { const r = rng(9); for (let g = 0; g < 8; g++) { const c = document.createElement('canvas'); c.width = 540; c.height = 960; const x = c.getContext('2d'); const id = x.createImageData(540, 960); for (let k = 0; k < id.data.length; k += 4) { const v = r() * 255; id.data[k] = id.data[k + 1] = id.data[k + 2] = v; id.data[k + 3] = 255; } x.putImageData(id, 0, 0); grains.push(c); } }
const out = document.getElementById('out'); const ctx = out.getContext('2d');
const acc = document.createElement('canvas'); acc.width = W; acc.height = H; const a = acc.getContext('2d');
const tmp = document.createElement('canvas'); tmp.width = W; tmp.height = H; const tx = tmp.getContext('2d');
function frameOf(s, t) { if (!s.seq) return s.im; const k = Math.min(s.frames.length - 1, Math.floor((t - s.t0) * (s.fps || 24) * (s.speed || 1))); return s.frames[Math.max(0, k)]; }
function drawShot(g, s, t, alpha) {
  const im = frameOf(s, t); const p = clamp((t - s.t0) / Math.max(0.1, s.t1 - s.t0)); const e = s.ease === 'lin' ? p : eio(p);
  let sc = 1.08, dx = 0, dy = 0; const m = s.move || 'in', amt = s.amt || 1;
  if (m === 'in') sc = lerp(1.04, 1.04 + 0.16 * amt, e); if (m === 'out') sc = lerp(1.04 + 0.16 * amt, 1.04, e); if (m === 'push') sc = lerp(1.0, 1.0 + 0.35 * amt, eout(p));
  if (m === 'panL') { sc = 1.18; dx = lerp(0.06, -0.06, e) * amt; } if (m === 'panR') { sc = 1.18; dx = lerp(-0.06, 0.06, e) * amt; }
  if (m === 'panU') { sc = 1.18; dy = lerp(0.07, -0.07, e) * amt; } if (m === 'panD') { sc = 1.18; dy = lerp(-0.07, 0.07, e) * amt; }
  if (m === 'still') sc = 1.03;
  for (const pt of pulses) { const d = t - pt; if (d > 0 && d < 0.5) sc *= 1 + 0.05 * Math.exp(-d * 8); }
  let sx = 0, sy = 0; if (s.shake) { const k = s.shake; sx = (Math.sin(t * 37.1) + Math.sin(t * 23.3)) * 6 * k; sy = (Math.cos(t * 31.7) + Math.sin(t * 19.1)) * 6 * k; }
  const iw = im.naturalWidth || im.width, ih = im.naturalHeight || im.height; const base = Math.max(W / iw, H / ih) * sc; const dw = iw * base, dh = ih * base;
  const fx = s.fx || '';
  g.save(); g.globalAlpha = alpha; g.filter = (fx.includes('bw') ? 'grayscale(1) contrast(1.15) ' : '') + (s.filter || 'contrast(1.08) saturate(0.9)');
  if (fx.includes('flicker')) g.globalAlpha = alpha * (0.82 + 0.18 * (Math.sin(t * 41) * Math.sin(t * 13.7) > -0.3 ? 1 : 0.4));
  g.drawImage(im, (W - dw) / 2 + dx * W + sx, (H - dh) / 2 + dy * H + sy, dw, dh); g.restore();
}
function glitch(g, src, k, seed) { // horizontal slice offsets + rgb split
  const r = rng(seed); const n = 14; for (let i = 0; i < n; i++) { const y = Math.floor(r() * H), h = 20 + r() * 120, off = (r() - 0.5) * 160 * k; g.drawImage(src, 0, y, W, h, off, y, W, h); }
  g.save(); g.globalCompositeOperation = 'screen'; g.globalAlpha = 0.5 * k; g.filter = 'sepia(1) saturate(6) hue-rotate(-50deg)'; g.drawImage(src, 14 * k, 0); g.filter = 'sepia(1) saturate(6) hue-rotate(140deg)'; g.drawImage(src, -14 * k, 0); g.restore();
}
function visuals(t) {
  a.fillStyle = '#000'; a.fillRect(0, 0, W, H);
  let ci = 0; for (let k = 0; k < shots.length; k++) if (t >= shots[k].t0) ci = k; const s = shots[ci];
  const into = t - s.t0; const tr = s.tr || 'fade';
  if (tr === 'fade' && ci > 0 && into < 0.35) { drawShot(a, shots[ci - 1], t, 1); drawShot(a, s, t, sm(into / 0.35)); } else drawShot(a, s, t, 1);
  if (tr === 'glitch' && into < 0.28 && ci > 0) { tx.clearRect(0, 0, W, H); tx.drawImage(acc, 0, 0); glitch(a, tmp, 1 - into / 0.28, Math.floor(t * 24)); }
  if (tr === 'flash' && into < 0.3) { a.fillStyle = `rgba(255,255,255,${0.9 * (1 - into / 0.3)})`; a.fillRect(0, 0, W, H); }
  if (tr === 'black' && into < 0.4) { a.fillStyle = `rgba(0,0,0,${1 - into / 0.4})`; a.fillRect(0, 0, W, H); }
  if ((s.fx || '').includes('glitchy') && Math.sin(t * 7.3) > 0.93) { tx.clearRect(0, 0, W, H); tx.drawImage(acc, 0, 0); glitch(a, tmp, 0.6, Math.floor(t * 24)); }
  if ((s.fx || '').includes('red')) { a.save(); a.globalCompositeOperation = 'multiply'; a.fillStyle = 'rgba(255,60,60,0.35)'; a.fillRect(0, 0, W, H); a.restore(); }
  for (const f of flashes) { const d = t - f; if (d > 0 && d < 0.35) { a.fillStyle = `rgba(255,255,255,${0.7 * (1 - d / 0.35)})`; a.fillRect(0, 0, W, H); } }
  // grade: teal shadows
  a.save(); a.globalCompositeOperation = 'soft-light'; a.fillStyle = C.tint || 'rgba(40,90,110,0.35)'; a.fillRect(0, 0, W, H); a.restore();
  // vignette
  const vg = a.createRadialGradient(W / 2, H * 0.48, H * 0.25, W / 2, H * 0.5, H * 0.75); vg.addColorStop(0, 'rgba(0,0,0,0)'); vg.addColorStop(1, 'rgba(0,0,0,0.78)'); a.fillStyle = vg; a.fillRect(0, 0, W, H);
  // grain + scratches
  a.save(); a.globalCompositeOperation = 'overlay'; a.globalAlpha = C.grain ?? 0.16; a.drawImage(grains[Math.floor(t * 24) % grains.length], 0, 0, W, H); a.restore();
  const r = rng(Math.floor(t * 12) + 7); if (C.scratches !== false && r() < 0.35) { a.fillStyle = 'rgba(255,255,255,0.10)'; a.fillRect(r() * W, 0, 2, H); }
  // flicker
  const fl = 0.04 * Math.max(0, Math.sin(t * 17.3) * Math.sin(t * 5.1)); a.fillStyle = `rgba(0,0,0,${fl})`; a.fillRect(0, 0, W, H);
  // top/bottom shade for text legibility
  const tg = a.createLinearGradient(0, H * 0.55, 0, H); tg.addColorStop(0, 'rgba(0,0,0,0)'); tg.addColorStop(1, 'rgba(0,0,0,0.55)'); a.fillStyle = tg; a.fillRect(0, H * 0.55, W, H * 0.45);
}
const CHAPTERS = (C.chapters || []).map(([l, txt]) => [l === 0 ? 0 : L[l].s - 0.14, txt]);
const ACCENT = new Set(C.accent || []);
const CARDS = (C.cards || []).map(c => ({ ...c, t0: at(c.from), t1: c.to === 'end' ? TL.dur : at(c.to) - 0.1 }));
const hud = makeHUD(ctx, L, { chapters: CHAPTERS, accent: ACCENT, speaker: null, theme: { brand: C.brand || '', solid: true, hazard: '#c1121f', pill: '#b0001a', active: C.active || '#ff4040' } });
window.renderClean = function (t) { visuals(t); return acc.toDataURL('image/jpeg', 0.92); };
window.compose = async function (t, url) { const img = new Image(); img.src = url; await img.decode(); ctx.drawImage(img, 0, 0, W, H); hud.draw(t, CARDS); return out.toDataURL('image/jpeg', 0.92); };
window.TLDUR = TL.dur; window.ready = true;
