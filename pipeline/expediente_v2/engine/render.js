// renders clean 3D frames (frames_clean) + composited frames (frames). mode=hud only recomposes from frames_clean.
const { chromium } = require('playwright'); const fs = require('fs');
(async () => { const [, , a, b, fps, mode, port] = process.argv; const F = +fps;
  const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const page = await browser.newPage(); page.on('pageerror', e => console.log('ERR', e.message));
  await page.goto('http://127.0.0.1:' + port + '/index.html'); await page.waitForFunction(() => window.ready === true, null, { timeout: 300000 });
  fs.mkdirSync('frames', { recursive: true }); fs.mkdirSync('frames_clean', { recursive: true }); const t0 = Date.now();
  for (let f = +a; f < +b; f++) { const n = String(f).padStart(5, '0'); const t = f / F; let clean;
    if (mode === 'hud') clean = 'data:image/jpeg;base64,' + fs.readFileSync(`frames_clean/${n}.jpg`).toString('base64');
    else { if (fs.existsSync(`frames/${n}.jpg`)) continue; clean = await page.evaluate(t => window.renderClean(t), t); fs.writeFileSync(`frames_clean/${n}.jpg`, Buffer.from(clean.split(',')[1], 'base64')); }
    const d = await page.evaluate(([t, u]) => window.compose(t, u), [t, clean]); fs.writeFileSync(`frames/${n}.jpg`, Buffer.from(d.split(',')[1], 'base64'));
    if (f % 25 === 0) console.log('frame', f, ((Date.now() - t0) / 1000).toFixed(0) + 's'); }
  await browser.close(); console.log('DONE'); })();
