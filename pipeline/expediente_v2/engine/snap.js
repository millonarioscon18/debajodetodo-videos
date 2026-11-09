// render a few times to snapshots: node snap.js port out_prefix t1 t2 ...
const { chromium } = require('playwright'); const fs = require('fs');
(async () => { const [, , port, pre, ...ts] = process.argv;
  const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const page = await browser.newPage(); page.on('pageerror', e => console.log('ERR', e.message)); page.on('console', m => { if (m.type() === 'error') console.log('CONSOLE', m.text()); });
  await page.goto('http://127.0.0.1:' + port + '/index.html'); await page.waitForFunction(() => window.ready === true, null, { timeout: 300000 });
  for (const t of ts) { const t0 = Date.now(); const c = await page.evaluate(t => window.renderClean(t), +t); const d = await page.evaluate(([t, u]) => window.compose(t, u), [+t, c]);
    fs.writeFileSync(`${pre}_${t}.jpg`, Buffer.from(d.split(',')[1], 'base64')); console.log(t, Date.now() - t0, 'ms'); }
  await browser.close(); })();
