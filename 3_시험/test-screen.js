// 화면(Index.html) 시험 — 실제 브라우저로 눌러 본다. 서버는 Code.gs + 가짜 구글.
// NODE_PATH=$(npm root -g) node 3_시험/test-screen.js [그림 저장 폴더]
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const { chromium } = require('playwright');
const { makeGlobals } = require('./fake-google');

const ROOT = path.join(__dirname, '..');
const CODE = fs.readFileSync(path.join(ROOT, '2_앱스스크립트/Code.gs'), 'utf8');
const HTML = path.join(ROOT, '2_앱스스크립트/Index.html');
const SHOTS = process.argv[2] || path.join(__dirname, '그림');
fs.mkdirSync(SHOTS, { recursive: true });

let pass = 0, fail = 0;
function ok(c, n) { if (c) { pass++; console.log('  ✓ ' + n); } else { fail++; console.log('  ✗ ' + n); } }

function boot() {
  const env = makeGlobals(Date.now());
  const ctx = vm.createContext({ ...env.g });
  vm.runInContext(CODE, ctx);
  const y = env.yt;
  const titles = {
    TwoMinutePapers: ['Two Minute Papers', 'HU', ['This AI learned to walk in 2 hours', 'New video model beats everything']],
    aiexplained_official: ['AI Explained', 'GB', ['Building AI agents that actually work', 'The new benchmark, explained']],
    jocoding: ['조코딩', 'KR', ['이번 주 AI 소식 정리 — 새 모델 셋 비교']],
    karaandnate: ['Kara and Nate', 'US', ['48 Hours in Kyoto — hidden spots', 'Patagonia on a budget']],
    LostLeBlanc: ['Lost LeBlanc', 'CA', ['Bali is not what you think']],
    kwaktube: ['곽튜브', 'KR', ['우즈베키스탄 시골 마을 여행']],
    MarkWiens: ['Mark Wiens', 'TH', ['Thai street food tour — 20 dishes', 'Best noodles in Chiang Mai']],
    JoshuaWeissman: ['Joshua Weissman', 'US', ['Perfect Neapolitan pizza at home']],
    Maangchi: ['Maangchi', 'US', ['Kimchi fried rice (김치볶음밥)']],
    paikscuisine: ['백종원', 'KR', ['집에서 만드는 짜장면']]
  };
  let k = 0;
  for (const [h, [t, cc, vids]] of Object.entries(titles)) {
    const ch = y.addChannel(h.replace('_', '-'), t, cc);
    vids.forEach((title, i) => y.addVideo(ch, { daysAgo: 0.05 + (k++) * 0.4 + i, dur: 300 + k * 97, title }));
  }
  const extra = y.addChannel('kurzgesagt', 'Kurzgesagt', 'DE');
  y.addVideo(extra, { daysAgo: 1.5, dur: 720, title: 'What if the Moon disappeared?' });
  ctx.setup();
  return { ...env, ctx };
}

(async () => {
  const E = boot();
  const b = await chromium.launch();
  const page = await b.newPage({ viewport: { width: 390, height: 844 } });
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  await page.route('**/*', r => (r.request().url().startsWith('file:') ? r.continue() : r.abort()));
  let failNext = null;
  await page.exposeFunction('__gas', (fn, args) => {
    try {
      if (failNext === fn) { failNext = null; throw new Error('시험용 실패'); }
      return JSON.stringify({ value: E.ctx[fn](...JSON.parse(args)) });
    } catch (e) { return JSON.stringify({ error: e.message }); }
  });
  await page.addInitScript(() => {
    function runner(okf, failf) {
      return new Proxy({}, { get(_, k) {
        if (k === 'withSuccessHandler') return f => runner(f, failf);
        if (k === 'withFailureHandler') return f => runner(okf, f);
        return (...args) => window.__gas(k, JSON.stringify(args)).then(s => {
          const o = JSON.parse(s); if (o.error) failf && failf(new Error(o.error)); else okf && okf(o.value);
        });
      } });
    }
    window.google = { script: { get run() { return runner(null, null); } } };
  });
  const sheetState = id => {
    const s = E.ss.getSheetByName('영상');
    return s.getRange(2, 1, s.getLastRow() - 1, 8).getValues().find(r => r[0] === id)[6];
  };
  const tabs = () => page.$$eval('.tab', els => els.map(e => e.textContent));
  const cardCount = () => page.locator('#grid .card').count();

  console.log('1. 처음 열기 (휴대폰 폭)');
  await page.goto('file://' + HTML);
  await page.waitForSelector('#grid .card');
  const feed = E.ctx.getFeed();
  const t = await tabs();
  ok(t[0].startsWith('전체') && t.some(x => x.startsWith('AI')) && t.some(x => x.startsWith('여행')) && t.some(x => x.startsWith('음식/레시피')) && t.at(-1) === '찾기', '탭: ' + t.join(' | '));
  ok(await cardCount() === feed.videos.length, '카드 ' + feed.videos.length + '장 = 시트 영상 수');
  ok(await page.evaluate(() => document.documentElement.scrollWidth) === 390, '옆으로 밀리지 않음 (폭 390)');
  const first = await page.locator('#grid .card .t').first().textContent();
  ok(first === feed.videos[0].t, '맨 위가 가장 최근 영상 — ' + first);
  await page.screenshot({ path: path.join(SHOTS, '1_휴대폰_전체.png') });

  console.log('2. 카테고리 탭');
  await page.click('.tab:has-text("여행")');
  const cats = await page.$$eval('#grid .card .cat', els => els.map(e => e.textContent));
  ok(cats.length > 0 && cats.every(c => c === '여행'), '여행 탭에는 여행만 (' + cats.length + '장)');

  console.log('3. 봤음 · 나중에 · 숨김');
  await page.click('.tab:has-text("전체")');
  const id0 = feed.videos[0].id;
  await page.locator('#grid .card').first().locator('[data-s="봤음"]').click();
  await page.waitForTimeout(100);
  ok(await page.locator('#grid .card').first().evaluate(e => e.classList.contains('seen')), '봤음 → 흐리게');
  ok(sheetState(id0) === '봤음', '시트에도 봤음');
  await page.locator('#grid .card').first().locator('[data-s="나중에"]').click();
  await page.waitForTimeout(100);
  ok(sheetState(id0) === '나중에', '나중에 → 시트 저장');
  ok((await tabs()).find(x => x.startsWith('나중에 보기')) === '나중에 보기1', '「나중에 보기」 탭 숫자 1');
  await page.locator('#grid .card').first().locator('[data-s="숨김"]').click();
  await page.waitForTimeout(100);
  ok(sheetState(id0) === '숨김' && await cardCount() === feed.videos.length - 1, '숨김 → 카드 빠짐 · 시트 숨김');
  await page.uncheck('#chkSeen');
  ok(await page.locator('#grid .card.seen').count() === 0, '「본 영상도 보기」 끄면 본 것 안 보임');
  await page.check('#chkSeen');

  console.log('4. 저장 실패하면 되돌림');
  failNext = 'setState';
  const id1 = await page.evaluate(() => S.videos[0].id);
  await page.locator('#grid .card').first().locator('[data-s="나중에"]').click();
  await page.waitForTimeout(150);
  ok(await page.locator('#toast').textContent() === '저장하지 못했습니다 — 시험용 실패', '실패 알림');
  ok(await page.evaluate(() => S.videos[0].st) === '새 영상' && sheetState(id1) === '새 영상', '화면 · 시트 모두 그대로');

  console.log('5. 재생');
  await page.locator('#grid .card').first().locator('.thumb').click();
  await page.waitForTimeout(100);
  ok(await page.locator('#playModal').isVisible(), '재생 창 열림');
  ok((await page.getAttribute('#frame', 'src')).startsWith('https://www.youtube-nocookie.com/embed/' + id1), '화면 안 재생 (기록 덜 남는 주소)');
  ok(await page.getAttribute('#playOpen', 'href') === 'https://www.youtube.com/watch?v=' + id1, '「유튜브에서 열기」 주소');
  ok(sheetState(id1) === '봤음', '재생하면 저절로 봤음');
  await page.screenshot({ path: path.join(SHOTS, '2_휴대폰_재생.png') });
  await page.click('#playClose');
  ok(!(await page.locator('#playModal').isVisible()) && (await page.getAttribute('#frame', 'src')) === 'about:blank', '닫으면 소리도 멈춤');

  console.log('6. ＋ 채널 (새 카테고리)');
  await page.click('#btnAdd');
  await page.fill('#addUrl', 'https://www.youtube.com/@kurzgesagt');
  await page.selectOption('#addCat', '__new__');
  await page.fill('#addNewCat', '과학');
  await page.screenshot({ path: path.join(SHOTS, '3_휴대폰_채널담기.png') });
  await page.click('#addOk');
  await page.waitForSelector('.tab:has-text("과학")');
  ok(/「Kurzgesagt」을 과학에 담았습니다/.test(await page.locator('#toast').textContent()), '담았다는 알림');
  await page.click('.tab:has-text("과학")');
  ok(await cardCount() === 1, '과학 탭에 영상 1장');
  await page.click('#btnAdd');
  await page.fill('#addUrl', 'https://www.youtube.com/@kurzgesagt');
  await page.click('#addOk');
  await page.waitForTimeout(150);
  ok(/이미 담은 채널/.test(await page.locator('#addMsg').textContent()), '같은 채널은 창 안에서 이유를 보여 줌');
  await page.click('#addCancel');

  console.log('7. 찾기 → 이 채널 담기');
  await page.click('.tab:has-text("찾기")');
  await page.fill('#q', 'street food');
  await page.click('#btnFind');
  await page.waitForSelector('#grid .card');
  const n = await cardCount();
  ok(n > 0, '찾은 영상 ' + n + '장');
  const disabled = await page.locator('#grid [data-a="add"]:disabled').count();
  ok(disabled === n, '이미 담은 채널은 「✓ 이미 담음」 (' + disabled + '/' + n + ')');
  await page.screenshot({ path: path.join(SHOTS, '4_휴대폰_찾기.png') });

  console.log('8. 지금 모으기');
  const y = E.yt; const mw = Object.values(y.channels).find(c => c.title === 'Mark Wiens');
  y.addVideo(mw, { daysAgo: 0.001, dur: 999, title: '방금 올라온 영상' });
  await page.click('.tab:has-text("전체")');
  await page.click('#btnCollect');
  await page.waitForFunction(() => /새 영상 1개/.test(document.getElementById('toast').textContent));
  await page.waitForTimeout(150);
  ok(await page.locator('#grid .card .t').first().textContent() === '방금 올라온 영상', '새 영상이 맨 위에');

  console.log('9. PC 폭 · 어두운 화면');
  await page.setViewportSize({ width: 1280, height: 860 });
  await page.screenshot({ path: path.join(SHOTS, '5_PC_전체.png') });
  await page.emulateMedia({ colorScheme: 'dark' });
  await page.screenshot({ path: path.join(SHOTS, '6_PC_어두운화면.png') });
  ok(await page.evaluate(() => document.documentElement.scrollWidth) === 1280, 'PC 폭에서도 밀리지 않음');

  console.log('10. 빈 시트');
  const E2 = makeGlobals(Date.now()); // 영상이 하나도 없을 때
  const ctx2 = vm.createContext({ ...E2.g }); vm.runInContext(CODE, ctx2); ctx2.setup();
  E.ctx = ctx2;
  await page.reload();
  await page.waitForSelector('.empty');
  ok(/아직 모은 영상이 없습니다/.test(await page.locator('.empty').textContent()), '빈 화면 안내 문구');

  ok(errors.length === 0, '화면 오류 없음' + (errors.length ? ' — ' + errors.join(' / ') : ''));
  await b.close();
  console.log('\n통과 ' + pass + ' · 실패 ' + fail + ' · 그림: ' + SHOTS);
  process.exit(fail ? 1 : 0);
})();
