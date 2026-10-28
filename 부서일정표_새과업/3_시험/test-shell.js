// 폰 껍데기(4_폰앱/올릴것) 시험 — NODE_PATH=$(npm root -g) node 3_시험/test-shell.js
const { chromium } = require('playwright'); const fs = require('fs'); const os = require('os'); const path = require('path');
(async () => {
  const fake = path.join(os.tmpdir(), '가짜화면.html');
  fs.writeFileSync(fake, '<!doctype html><meta charset="utf-8"><body>가짜 화면<script>setTimeout(()=>window.top.postMessage({부서일정:"떴음"},"*"),300)</script>');
  const shell = 'file://' + path.join(__dirname, '../4_폰앱/올릴것/index.html');
  const b = await chromium.launch(); let ok = 0, bad = 0; const t = (c, n) => { c ? ok++ : bad++; console.log((c ? '  ✓ ' : '  ✗ ') + n); };
  let p = await b.newPage({ viewport: { width: 375, height: 812 } }); const errs = []; p.on('pageerror', e => errs.push(e.message));
  await p.goto(shell); await p.waitForTimeout(300);
  t(await p.locator('#qr').isVisible() && /열쇠가 없습니다/.test(await p.textContent('#msg')), '열쇠 없음 → QR 안내');
  await p.close(); p = await b.newPage({ viewport: { width: 375, height: 812 } }); p.on('pageerror', e => errs.push(e.message));
  await p.goto(shell + '?x=1#m=abc123'); await p.waitForTimeout(300);
  t(await p.evaluate(() => localStorage.getItem('구조부일정.열쇠')) === 'abc123' && !(await p.evaluate(() => location.hash)), '#m= 저장 · 주소에서 지움 (' + await p.evaluate(() => location.hash) + ')');
  t((await p.getAttribute('#app', 'src')).endsWith('/exec?m=abc123'), 'iframe 주소에 열쇠 붙음');
  await p.goto(shell + '?화면=file://' + fake); await p.waitForTimeout(800);
  t(await p.locator('#app').isVisible() && !(await p.locator('#cover').isVisible()), '「떴음」 받으면 덮개 걷힘');
  t(errs.length === 0, '오류 0');
  await b.close(); console.log('통과 ' + ok + ' · 실패 ' + bad); process.exit(bad ? 1 : 0);
})();
