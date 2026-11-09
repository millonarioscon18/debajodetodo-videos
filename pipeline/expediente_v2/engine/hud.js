// Shared HUD: brand bug, chapter tag, speaker tag, 3-word karaoke subtitles, info cards (safe-zone aware).
export const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
export const sm = x => { x = clamp(x); return x * x * (3 - 2 * x); };
export const eio = x => { x = clamp(x); return x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2; };
export const eout = x => 1 - Math.pow(1 - clamp(x), 3);
export const back = x => { x = clamp(x); const c = 1.7; return 1 + (c + 1) * Math.pow(x - 1, 3) + c * Math.pow(x - 1, 2); };
export const lerp = (a, b, k) => a + (b - a) * k;
export const SX = 500;

export function makeHUD(ctx, L, { chapters, accent, speaker = 'EL OBRERO', theme = {} }) {
  const yellow = theme.active || '#FFD43B', pill = theme.pill || '#ff7a1a', hz = theme.hazard || '#ff6b00';
  const CH = []; for (const l of L) { let cur = []; const flush = () => { if (cur.length) CH.push({ s: cur[0].s, e: cur[cur.length - 1].e, w: cur.map(x => x.w.replace(/[¿¡]/g, '')), ws: cur.map(x => x.s) }); cur = []; };
    for (const w of l.words) { cur.push(w); if (/[.,?!:]$/.test(w.w) || w.w.endsWith('...') || cur.length === 3) flush(); } flush(); }
  for (let i = 0; i < CH.length - 1; i++) CH[i].e = (CH[i + 1].s - CH[i].e < 0.5) ? CH[i + 1].s : CH[i].e + 0.25;
  CH[CH.length - 1].e += 0.6;
  function txt(s, x, y, size, color, { w = 900, fam = 'Mont', align = 'center', stroke = 0, shadow = 0 } = {}) {
    ctx.font = `${w} ${size}px ${fam}`; ctx.textAlign = align; ctx.textBaseline = 'middle'; ctx.lineJoin = 'round';
    if (shadow) { ctx.save(); ctx.shadowColor = 'rgba(0,0,0,0.6)'; ctx.shadowBlur = shadow; ctx.shadowOffsetY = shadow * 0.35; ctx.fillStyle = color; ctx.fillText(s, x, y); ctx.restore(); }
    if (stroke) { ctx.lineWidth = stroke; ctx.strokeStyle = 'rgba(0,0,0,0.85)'; ctx.strokeText(s, x, y); } ctx.fillStyle = color; ctx.fillText(s, x, y); }
  function hazard(x, y, w, h, off) { ctx.save(); ctx.beginPath(); ctx.roundRect(x, y, w, h, Math.min(8, h / 2)); ctx.clip(); ctx.fillStyle = hz; ctx.fillRect(x, y, w, h); ctx.fillStyle = '#111';
    if (!theme.solid) for (let i = -h * 2; i < w + h * 2; i += 30) { const o = off % 30; ctx.beginPath(); ctx.moveTo(x + i + o, y + h); ctx.lineTo(x + i + 15 + o, y + h); ctx.lineTo(x + i + 15 + h + o, y); ctx.lineTo(x + i + h + o, y); ctx.fill(); } ctx.restore(); }
  // info card: {t0, t1, icon, title, sub, color}
  function card(c, t) {
    const k = clamp((t - c.t0) / 0.35), ko = clamp((c.t1 - t) / 0.25); if (k <= 0 || ko <= 0) return; const s = back(k) * (0.9 + 0.1 * ko); const a = Math.min(k * 2, ko);
    const y = c.y || 470; ctx.save(); ctx.globalAlpha = a; ctx.translate(SX, y); ctx.scale(s, s);
    ctx.font = '900 64px Mont'; const tw = Math.max(ctx.measureText(c.title).width, c.sub ? (ctx.font = '700 38px Mont', ctx.measureText(c.sub).width) : 0);
    const w = Math.min(860, tw + (c.icon ? 190 : 90)), h = c.sub ? 190 : 140;
    ctx.fillStyle = 'rgba(12,14,20,0.82)'; ctx.beginPath(); ctx.roundRect(-w / 2, -h / 2, w, h, 30); ctx.fill();
    ctx.lineWidth = 5; ctx.strokeStyle = c.color || pill; ctx.stroke();
    let x0 = -w / 2 + 45;
    if (c.icon) { ctx.fillStyle = c.color || pill; ctx.beginPath(); ctx.arc(x0 + 45, 0, 52, 0, 7); ctx.fill(); txt(c.icon, x0 + 45, 4, c.iconSize || 56, '#111'); x0 += 120; }
    const fs = Math.min(1, (w - (x0 + w / 2) - 30) / tw);
    ctx.save(); ctx.translate(x0, 0); ctx.scale(fs, fs);
    txt(c.title, 0, c.sub ? -30 : 4, 64, '#fff', { align: 'left' }); if (c.sub) txt(c.sub, 0, 44, 38, 'rgba(255,255,255,0.78)', { w: 700, align: 'left' });
    ctx.restore(); ctx.restore(); }
  function draw(t, cards = []) {
    if (theme.brand !== '') hazard(60, 218, 14, 40, t * 30); if (theme.brand !== '') txt(theme.brand || 'DEBAJO DE TODO', 86, 238, 28, '#fff', { align: 'left', shadow: 10 });
    let ch = chapters[0]; for (const c of chapters) if (t >= c[0]) ch = c;
    const pk = back((t - ch[0]) / 0.4); ctx.save(); ctx.font = '900 32px Mont'; const tw = ctx.measureText(ch[1]).width; const x = 60, y = 272;
    ctx.translate(x, y); ctx.scale(pk, pk); ctx.fillStyle = 'rgba(14,16,22,0.72)'; ctx.beginPath(); ctx.roundRect(0, 0, tw + 70, 62, 16); ctx.fill();
    ctx.strokeStyle = 'rgba(255,255,255,0.16)'; ctx.lineWidth = 2; ctx.stroke(); ctx.restore();
    ctx.save(); ctx.translate(x, y); ctx.scale(pk, pk); ctx.translate(-x, -y); hazard(x + 16, y + 16, 14, 30, t * 30); txt(ch[1], x + 46, y + 32, 32, '#fff', { align: 'left' }); ctx.restore();
    for (const c of cards) card(c, t);
    const Lc = L.find(l => t >= l.s - 0.1 && t <= l.e + 0.2);
    if (Lc && speaker) { ctx.font = '900 30px Mont'; const nw = ctx.measureText(speaker).width;
      ctx.fillStyle = theme.tag || 'rgba(255,122,26,0.95)'; ctx.beginPath(); ctx.roundRect(SX - nw / 2 - 20, 1120, nw + 40, 48, 24); ctx.fill(); txt(speaker, SX, 1145, 30, '#111'); }
    const c = CH.find(c => t >= c.s && t < c.e);
    if (c) { const d = t - c.s; const pop = 0.72 + 0.28 * back(d / 0.16); const y = 1235 + (1 - eout(d / 0.16)) * 24; const size = 78;
      ctx.font = `900 ${size}px Mont`; const words = c.w.map(w => w.toUpperCase()); const gap = 30; const widths = words.map(w => ctx.measureText(w).width);
      const total = widths.reduce((a, b) => a + b, 0) + gap * (words.length - 1); const fs = Math.min(1, 820 / total);
      ctx.save(); ctx.translate(SX, y); ctx.scale(pop * fs, pop * fs); let x = -total / 2;
      words.forEach((w, i) => { const active = t >= c.ws[i] && (i === words.length - 1 || t < c.ws[i + 1]); const cx = x + widths[i] / 2;
        const acc = accent.has(c.w[i].toLowerCase().replace(/[.,?!:…]/g, ''));
        if (active) { const ak = eout((t - c.ws[i]) / 0.1); ctx.save(); ctx.translate(cx, 0); ctx.scale(1 + 0.08 * ak, 1 + 0.08 * ak);
          if (acc) { ctx.fillStyle = pill; ctx.beginPath(); ctx.roundRect(-widths[i] / 2 - 16, -size * 0.62, widths[i] + 32, size * 1.2, 18); ctx.fill(); txt(w, 0, 4, size, '#fff'); }
          else txt(w, 0, 4, size, yellow, { stroke: 12, shadow: 22 }); ctx.restore(); }
        else txt(w, cx, 4, size, '#ffffff', { stroke: 12, shadow: 22 });
        x += widths[i] + gap; });
      ctx.restore(); }
  }
  return { draw, txt, hazard };
}
