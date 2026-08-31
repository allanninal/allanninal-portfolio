import { chromium } from 'playwright';
const b = await chromium.launch({ executablePath: '/opt/homebrew/bin/chromium' });
const p = await b.newPage({ viewport: { width: 1400, height: 900 } });
await p.goto(process.argv[2], { waitUntil: 'networkidle' });
console.log(await p.evaluate(() => {
  const d = document.querySelector('.diagram');
  const pr = document.querySelector('.prose');
  return JSON.stringify({diagram: d && d.getBoundingClientRect().width, viewBox: d && d.getAttribute('viewBox'), prose: pr && pr.getBoundingClientRect().width});
}));
await b.close();
