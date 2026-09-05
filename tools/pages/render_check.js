// Load a page in a real browser and report what it actually paints.
//
// Every static check on this repo passed while two pages were blank -- the
// markup was present, the facts verified, the tags balanced. Only a browser
// knows whether a canvas has pixels in it or a .fade-up ever became visible.
const { chromium } = require('/Users/allanninal/Projects/GuroOS/node_modules/playwright-core');
(async () => {
  const b = await chromium.launch();
  let bad = 0;
  for (const path of process.argv.slice(2)) {
    const p = await b.newPage({ viewport: { width: 1440, height: 1000 } });
    const errs = [];
    // Ad and analytics endpoints fail or 403 in headless and say nothing about
    // the page, so only same-origin resources count as an error here.
    const ours = t => !/google|doubleclick|gstatic|facebook|clarity|hotjar/.test(t);
    // A console error for a failed subresource carries no URL in its text, only
    // in its location, so both are checked before it counts.
    p.on('console', m => {
      if (m.type() !== 'error') return;
      const where = (m.location() && m.location().url) || '';
      if (ours(m.text()) && ours(where)) errs.push(m.text() + ' <- ' + where);
    });
    p.on('requestfailed', r => { if (ours(r.url())) errs.push('REQFAIL ' + r.url()); });
    p.on('response', r => { if (r.status() >= 400 && ours(r.url()))
        errs.push(r.status() + ' ' + r.url()); });
    p.on('pageerror', e => errs.push('PAGEERROR: ' + e.message));
    await p.goto(path, { waitUntil: 'load' });
    await p.waitForTimeout(1200);
    // scroll the whole page so the IntersectionObserver fires everywhere
    await p.evaluate(async () => {
      for (let y = 0; y < document.body.scrollHeight; y += 500) {
        window.scrollTo(0, y);
        await new Promise(r => setTimeout(r, 40));
      }
      window.scrollTo(0, 0);
    });
    await p.waitForTimeout(1500);
    const r = await p.evaluate(() => {
      const blank = [];
      for (const c of document.querySelectorAll('canvas')) {
        const g = c.getContext('2d');
        let ink = 0;
        try {
          const d = g.getImageData(0, 0, c.width, c.height).data;
          for (let i = 3; i < d.length; i += 400) if (d[i] > 8) ink++;
        } catch (e) { ink = -1; }
        if (ink === 0) blank.push(c.id || '(unnamed)');
      }
      const hidden = [...document.querySelectorAll('.fade-up')]
        .filter(e => getComputedStyle(e).opacity < 0.9)
        .map(e => e.className + ' :: ' + (e.textContent || '').trim().slice(0, 40));
      const wide = document.documentElement.scrollWidth >
                   document.documentElement.clientWidth + 2;
      return { canvases: document.querySelectorAll('canvas').length, blank, hidden,
               wide, h: document.body.scrollHeight };
    });
    const ok = !errs.length && !r.blank.length && !r.hidden.length && !r.wide;
    if (!ok) bad++;
    console.log((ok ? '  ok   ' : '  FAIL ') + path.split('/').pop() +
      '  canvases=' + r.canvases + ' blank=' + r.blank.length +
      ' hidden=' + r.hidden.length + ' h=' + r.h + (r.wide ? ' H-SCROLL' : ''));
    if (r.blank.length) console.log('         blank: ' + r.blank.join(', '));
    if (r.hidden.length) console.log('         hidden: ' + r.hidden.slice(0,4).join(' | '));
    if (errs.length) console.log('         errors: ' + errs.slice(0, 4).join(' | '));
    await p.close();
  }
  await b.close();
  process.exit(bad ? 1 : 0);
})();
