const { chromium } = require('playwright'); const path = require('path');
(async () => {
  const b = await chromium.launch(); const src = 'file://' + path.join(__dirname, '아이콘.html');
  const out = path.join(__dirname, '올릴것/icons') + '/';
  for (const [name, size, maskable] of [['icon-512', 512, false], ['icon-512-maskable', 512, true], ['icon-192', 192, false], ['apple-180', 180, true], ['favicon-32', 32, false]]) {
    const scale = size / 512;
    const p = await b.newPage({ viewport: { width: size, height: size }, deviceScaleFactor: 1 });
    await p.goto(src);
    if (maskable) await p.evaluate(() => { const r = document.querySelectorAll('svg > rect'); r[0].setAttribute('x', 0); r[0].setAttribute('y', 0); r[0].setAttribute('width', 512); r[0].setAttribute('height', 512); r[0].setAttribute('rx', 0); r[0].removeAttribute('filter'); r[1].setAttribute('x', 0); r[1].setAttribute('y', 0); r[1].setAttribute('width', 512); r[1].setAttribute('height', 512); r[1].setAttribute('rx', 0); });
    await p.evaluate(s => { document.querySelector('svg').style.transform = 'scale(' + s + ')'; document.querySelector('svg').style.transformOrigin = '0 0'; }, scale);
    await p.screenshot({ path: out + name + '.png', omitBackground: !maskable });
    await p.close();
  }
  await b.close(); console.log('icons ok');
})();
