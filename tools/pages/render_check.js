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

      // A dataset drawn in a colour nobody set. Chart.js fills points and bars
      // from backgroundColor; leaving it unset takes Chart.defaults, which on
      // these dark pages is near-black and therefore invisible. The canvas still
      // has plenty of ink from the other series, so the blank-canvas test above
      // passes while a whole series is missing -- which is exactly what happened
      // to three series on the European grid page.
      const invisible = [];
      if (window.Chart && Chart.instances) {
        for (const c of Object.values(Chart.instances)) {
          for (const d of c.data.datasets) {
            const shows = (d.pointRadius && d.pointRadius > 0) ||
                          (d.type || c.config.type) === 'bar';
            const bg = d.pointBackgroundColor || d.backgroundColor;
            if (shows && !bg) {
              invisible.push((c.canvas.id || '?') + ' :: ' +
                             (d.label || '(unlabelled)'));
            }
          }
        }
      }

      // What a point is actually painted, rather than what it was told to be.
      // Chart.js sorts datasets by `order` and then draws that list BACKWARDS, so
      // when every order is equal, dataset 0 paints LAST -- on top of everything
      // after it. A bar series declared first therefore covers the point series
      // that were meant to sit over it, and the check above cannot see it: the
      // colours are all correctly declared, they are simply painted over.
      //
      // So sample the canvas at each point's own centre and compare it with the
      // colour that point asked for. A point hidden underneath another series
      // reads as the blend, not as itself.
      const occluded = [];
      const rgbOf = (v) => {
        if (typeof v !== 'string') return null;
        let m = /^#([0-9a-f]{6})$/i.exec(v.trim());
        if (m) return [parseInt(m[1].slice(0,2),16), parseInt(m[1].slice(2,4),16),
                       parseInt(m[1].slice(4,6),16)];
        m = /^#([0-9a-f]{3})$/i.exec(v.trim());
        if (m) return m[1].split('').map(h => parseInt(h + h, 16));
        m = /^rgba?\(([^)]+)\)$/i.exec(v.trim());
        if (m) {
          const n = m[1].split(',').map(Number);
          // a translucent fill blends with whatever is behind it by design
          if (n.length > 3 && n[3] < 0.98) return null;
          return [n[0], n[1], n[2]];
        }
        return null;                                  // named or gradient: skip
      };
      if (window.Chart && Chart.instances) {
        const dpr = window.devicePixelRatio || 1;
        for (const c of Object.values(Chart.instances)) {
          const g = c.canvas.getContext('2d');
          // every point on the chart, so a point covered by another point can be
          // told apart from a point covered by a bar
          const all = [];
          c.data.datasets.forEach((d, i) => {
            const meta = c.getDatasetMeta(i);
            if (meta.hidden) return;
            (meta.data || []).forEach(e => all.push({ i, x: e.x, y: e.y }));
          });
          c.data.datasets.forEach((d, i) => {
            const r = d.pointRadius;
            if (!(typeof r === 'number' && r > 0)) return;
            const want = rgbOf(d.pointBackgroundColor || d.backgroundColor);
            if (!want) return;
            const meta = c.getDatasetMeta(i);
            if (meta.hidden) return;
            for (let k = 0; k < (meta.data || []).length; k++) {
              const e = meta.data[k];
              if (!isFinite(e.x) || !isFinite(e.y)) continue;
              // a null in the series still gets an element positioned on the
              // scale, but nothing is painted at it -- education's senior-high
              // line has six leading nulls and sampled as transparent black
              if (e.skip || d.data[k] === null || d.data[k] === undefined) continue;
              // another series' point sitting on this one is a legible overlap,
              // not an occlusion bug; only flag what a non-point series covered
              if (all.some(o => o.i !== i && Math.hypot(o.x - e.x, o.y - e.y) < r + 2))
                continue;
              let got;
              try {
                got = g.getImageData(Math.round(e.x * dpr), Math.round(e.y * dpr),
                                     1, 1).data;
              } catch (err) { continue; }
              const off = Math.max(Math.abs(got[0] - want[0]),
                                   Math.abs(got[1] - want[1]),
                                   Math.abs(got[2] - want[2]));
              if (off > 40) {
                occluded.push((c.canvas.id || '?') + ' :: ' +
                  (d.label || '(unlabelled)') + ' wanted rgb(' + want.join(',') +
                  ') got rgb(' + got[0] + ',' + got[1] + ',' + got[2] + ')');
                break;                                // one report per dataset
              }
            }
          });
        }
      }

      return { canvases: document.querySelectorAll('canvas').length, blank, hidden,
               wide, invisible, occluded, h: document.body.scrollHeight };
    });
    const ok = !errs.length && !r.blank.length && !r.hidden.length &&
               !r.wide && !r.invisible.length && !r.occluded.length;
    if (!ok) bad++;
    console.log((ok ? '  ok   ' : '  FAIL ') + path.split('/').pop() +
      '  canvases=' + r.canvases + ' blank=' + r.blank.length +
      ' hidden=' + r.hidden.length +
      ' nocolour=' + r.invisible.length +
      ' buried=' + r.occluded.length +
      ' h=' + r.h + (r.wide ? ' H-SCROLL' : ''));
    if (r.blank.length) console.log('         blank: ' + r.blank.join(', '));
    if (r.hidden.length) console.log('         hidden: ' + r.hidden.slice(0,4).join(' | '));
    if (r.invisible.length) console.log('         no backgroundColor: ' +
      r.invisible.slice(0, 5).join(', '));
    if (r.occluded.length) console.log('         painted over: ' +
      r.occluded.slice(0, 5).join(', '));
    if (errs.length) console.log('         errors: ' + errs.slice(0, 4).join(' | '));
    await p.close();
  }
  await b.close();
  process.exit(bad ? 1 : 0);
})();
