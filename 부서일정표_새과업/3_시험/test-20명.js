// 부서원 20명이 2주 쓰는 것처럼 — 서버(건수 · 크기 · 시간) + 화면(폰 4대 · PC 2대 동시 올리기)
// NODE_PATH=$(npm root -g) node 3_시험/test-20명.js [그림 폴더]
process.env.TZ = 'Asia/Seoul';
const fs = require('fs');
const path = require('path');
const os = require('os');
const vm = require('vm');
const { chromium } = require('playwright');
const { makeGlobals } = require('./fake-google');

const ROOT = path.join(__dirname, '..');
const CODE = fs.readFileSync(path.join(ROOT, '2_앱스스크립트/Code.gs'), 'utf8');
const HTML_SRC = fs.readFileSync(path.join(ROOT, '2_앱스스크립트/Index.html'), 'utf8');
const SHOTS = process.argv[2] || path.join(__dirname, '그림');
fs.mkdirSync(SHOTS, { recursive: true });
let pass = 0, fail = 0;
const ok = (c, n) => { if (c) { pass++; console.log('  ✓ ' + n); } else { fail++; console.log('  ✗ ' + n); } };
const F = d => d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
const addD = (d, n) => { const x = new Date(d); x.setDate(x.getDate() + n); return x; };
// 같은 결과가 나오게 정해진 난수
let seed = 20261029; const rnd = () => { seed = (seed * 1103515245 + 12345) % 2147483648; return seed / 2147483648; };
const pick = a => a[Math.floor(rnd() * a.length)];

const 이름들 = ['전채만', '난○○', '김○○', '이○○', '박○○', '최○○', '정○○', '강○○', '조○○', '윤○○', '장○○', '임○○', '한○○', '오○○', '서○○', '신○○', '권○○', '황○○', '안○○', '송○○'];
const 종류들 = ['출장', '휴가', '반차', '외근', '교육', '회의', '그 밖'];
const 어디들 = ['대전 · 발주처', '세종', '양촌 과도교', '강릉 제진', '서대전 현장', '', '', ''];
const 과업들 = ['D197', 'D196', 'D201', 'D188', '', '', ''];

function boot() {
  const env = makeGlobals(Date.now());
  const ctx = vm.createContext({ ...env.g });
  vm.runInContext(CODE, ctx);
  ctx.setup();
  const ps = env.ss.getSheetByName('부서원');
  ps.getRange(2, 1, 이름들.length, 4).setValues(이름들.map((n, i) => [n, '예', i + 1, '']));
  const ts = env.ss.getSheetByName('과업');
  ts.getRange(2, 1, 4, 4).setValues([['D197', '이설표지판', '예', ''], ['D196', '강릉제진', '예', ''], ['D201', '서대전지하차도', '예', ''], ['D188', '양촌과도교', '예', '']]);
  const key = env.ss.getSheetByName('설정').getRange(2, 1, 8, 2).getValues().find(r => r[0] === '공유 열쇠')[1];
  const today = new Date(); today.setHours(0, 0, 0, 0);
  return { ...env, ctx, key, today };
}
const cal = E => E.calendars[Object.keys(E.calendars).find(k => !/holiday/.test(k))];
const 기록수 = E => { const s = E.ss.getSheetByName('기록'); return s.getLastRow() - 1; };

(async () => {
  const E = boot();
  const t0 = Date.now();

  console.log('1. 서버 — 20명이 2주(지난 1주 + 다음 1주) 동안 올림 · 고침 · 지움');
  let 올림 = 0, 고침 = 0, 지움 = 0, 거절 = 0;
  const ids = [];
  이름들.forEach(n => {
    const k = 2 + Math.floor(rnd() * 3); // 사람마다 2~4건
    for (let i = 0; i < k; i++) {
      const 종류 = pick(종류들); const d = addD(E.today, Math.floor(rnd() * 14) - 7);
      const 끝 = 종류 === '출장' || 종류 === '휴가' || 종류 === '교육' ? addD(d, Math.floor(rnd() * 3)) : d;
      try {
        const out = E.ctx.일정올리기(E.key, { 누가: n, 종류, 시작: F(d), 끝: F(끝), 시간대: 종류 === '반차' ? pick(['오전', '오후']) : '', 어디: pick(어디들), 메모: rnd() < .3 ? '메모 ' + i : '', 과업: pick(과업들), 화면: n + (rnd() < .7 ? ' 폰' : ' PC') });
        ids.push(out.id); 올림++;
      } catch (e) { 거절++; }
    }
  });
  // 고침 15건 · 지움 8건 · 틀린 입력 5건
  for (let i = 0; i < 15; i++) { E.ctx.일정고치기(E.key, pick(ids), { 어디: '고친 어디 ' + i, 화면: 'PC' }); 고침++; }
  const 지울 = ids.splice(0, 8); 지울.forEach(id => { E.ctx.일정지우기(E.key, id, '폰'); 지움++; });
  [{ 누가: '없는사람', 종류: '출장', 시작: F(E.today) }, { 누가: '전채만', 종류: '야근', 시작: F(E.today) }, { 누가: '전채만', 종류: '출장', 시작: 'x' }, { 누가: '전채만', 종류: '출장', 시작: F(E.today), 끝: F(addD(E.today, -1)) }, { 누가: '', 종류: '출장', 시작: F(E.today) }]
    .forEach(bad => { try { E.ctx.일정올리기(E.key, bad); } catch (e) { 거절++; } });
  const evN = cal(E).events.length;
  ok(evN === 올림 - 지움, '캘린더 건수 = 올림 ' + 올림 + ' − 지움 ' + 지움 + ' = ' + evN);
  ok(기록수(E) === 올림 + 고침 + 지움, '기록 줄 = 올림 + 고침 + 지움 = ' + 기록수(E) + ' (거절 ' + 거절 + ' 은 기록 안 남음)');
  const 기록 = E.ss.getSheetByName('기록').getRange(2, 1, 기록수(E), 6).getValues();
  ok(기록.every(r => r[0] && r[1] && r[2] && r[3]), '기록 줄마다 때 · 무엇 · 번호 · 제목이 다 있음 (겹쳐 쓴 줄 0)');

  const t1 = Date.now(); const 화면 = E.ctx.화면자료(E.key); const ms = Date.now() - t1;
  const bytes = Buffer.byteLength(JSON.stringify(화면));
  ok(화면.부서원.length === 20 && 화면.일정.length === evN, '화면자료 : 부서원 20 · 일정 ' + 화면.일정.length);
  ok(bytes < 200 * 1024, '화면자료 크기 ' + (bytes / 1024).toFixed(1) + ' KB (< 200 KB · 일정 한 건 약 ' + Math.round(bytes / Math.max(1, 화면.일정.length)) + ' 바이트)');
  ok(ms < 500, '화면자료 셈 ' + ms + ' ms (가짜 구글 · 진짜는 구글 왕복 1~3초가 더 붙음)');
  const q = 화면.요약;
  ok(q.전체 === 20 && q.밖수 + q.자리.length === 20 && q.밖수 === new Set(q.밖.map(e => e.누가)).size, '오늘 요약 : 밖 ' + q.밖수 + ' + 자리 ' + q.자리.length + ' = 20 · 같은 사람 두 건이어도 1명');
  // 하루 최대 몇 명이 나가 있나 · 하루 최대 몇 건
  let maxOut = 0, maxEv = 0, maxDay = '';
  for (let i = -7; i <= 7; i++) { const g = F(addD(E.today, i)); const r = E.ctx.화면자료(E.key, g).요약; if (r.밖수 > maxOut) { maxOut = r.밖수; maxDay = g; } maxEv = Math.max(maxEv, r.밖.length); }
  ok(maxOut <= 20, '하루 최대 부서 밖 ' + maxOut + '명 (' + maxDay + ') · 하루 최대 ' + maxEv + '건 → 달력 칸에는 3건 + «+n»');
  const wk = E.ctx.doGet({ parameter: { 주간: '', m: E.key } });
  ok(wk.kind === 'text' && JSON.parse(wk.body).날마다.length === 7, '현황판용 ?주간 JSON ' + (Buffer.byteLength(wk.body) / 1024).toFixed(1) + ' KB');
  // 가져오기 60줄 (호두에서 옮기는 상황)
  const gs = E.ss.getSheetByName('가져오기');
  gs.getRange(2, 1, 60, 8).setValues(Array.from({ length: 60 }, (_, i) => [pick(이름들), pick(종류들.slice(0, 4)), F(addD(E.today, 8 + Math.floor(i / 5))), '', '', pick(어디들), '호두에서', '']));
  const t2 = Date.now(); const gmsg = E.ctx.가져오기(); const gms = Date.now() - t2;
  ok(/올림 60 · 이미 올린 줄 0 · 안 됨 0/.test(gmsg) && gms < 2000, '가져오기 60줄 ' + gms + ' ms — ' + gmsg);

  console.log('2. 화면 — 폰 4대 · PC 2대가 동시에 올림 (각 3건)');
  const tmp = path.join(os.tmpdir(), 'Index.20명.html');
  fs.writeFileSync(tmp, HTML_SRC.replace('<?= 열쇠 ?>', E.key).replace('<?= 판 ?>', 'v시험'));
  const b = await chromium.launch();
  const errors = [];
  let calls = 0;
  async function open(viewport, who) {
    const page = await b.newPage({ viewport });
    page.on('pageerror', e => errors.push(who + ': ' + e.message));
    page.on('console', m => { if (m.type() === 'error') errors.push(who + ': ' + m.text()); });
    await page.route('**/*', r => (r.request().url().startsWith('file:') ? r.continue() : r.abort()));
    await page.exposeFunction('__gas', async (fn, args) => {
      calls++;
      await new Promise(r => setTimeout(r, 30 + Math.random() * 120)); // 구글 왕복 흉내
      try { return JSON.stringify({ value: E.ctx[fn](...JSON.parse(args)) }); } catch (e) { return JSON.stringify({ error: e.message }); }
    });
    await page.addInitScript(() => {
      function runner(okf, failf) {
        return new Proxy({}, { get(_, k) {
          if (k === 'withSuccessHandler') return f => runner(f, failf);
          if (k === 'withFailureHandler') return f => runner(okf, f);
          return (...args) => window.__gas(k, JSON.stringify(args)).then(s => { const o = JSON.parse(s); if (o.error) failf && failf(new Error(o.error)); else okf && okf(o.value); });
        } });
      }
      window.google = { script: { get run() { return runner(null, null); } } };
    });
    const t = Date.now();
    await page.goto('file://' + tmp);
    await page.waitForFunction(() => !/받는 중/.test(document.getElementById('now').textContent));
    return { page, who, loadMs: Date.now() - t };
  }
  const 기기 = [];
  for (let i = 0; i < 4; i++) 기기.push(await open({ width: 375, height: 812 }, 이름들[i + 1] + ' 폰'));
  for (let i = 0; i < 2; i++) 기기.push(await open({ width: 1366, height: 768 }, 이름들[i + 10] + ' PC'));
  ok(기기.every(k => k.loadMs < 4000), '여섯 기기 첫 화면 ' + 기기.map(k => k.loadMs + 'ms').join(' · '));
  ok(await 기기[0].page.evaluate(() => document.documentElement.scrollWidth) === 375, '폰 · 20명이어도 옆으로 안 밀림');
  await 기기[0].page.screenshot({ path: path.join(SHOTS, '20명_1_폰_오늘.png') });

  const before = cal(E).events.length;
  async function 올리기(k, idx) {
    const { page, who } = k; const name = who.split(' ')[0];
    for (let j = 0; j < 3; j++) {
      await page.click('#fab').catch(() => {});
      if (!(await page.locator('#form.open').count()) && await page.locator('#form').isVisible()) { /* PC 는 늘 보임 */ }
      await page.waitForTimeout(150);
      await page.click('#whoPick .chip:has-text("' + name + '")');
      await page.click('#kindPick .chip:nth-child(' + (1 + ((idx + j) % 7)) + ')');
      await page.fill('#d1', F(addD(E.today, 1 + j)));
      await page.fill('#d2', '');
      await page.fill('#where', who + ' ' + j);
      await page.click('#btnSave');
      await page.waitForSelector('#result.ok', { timeout: 10000 });
      await page.waitForTimeout(1000);
    }
  }
  const t3 = Date.now();
  await Promise.all(기기.map((k, i) => 올리기(k, i)));
  const dur = Date.now() - t3;
  ok(cal(E).events.length === before + 18, '여섯 기기 × 3건 = 18건 모두 들어감 (' + (cal(E).events.length - before) + ') · ' + (dur / 1000).toFixed(1) + '초');
  ok(기록수(E) === 올림 + 고침 + 지움 + 60 + 18, '기록 줄도 18 늘어남 · 겹친 줄 0 (' + 기록수(E) + ')');
  // 여섯 기기가 ↻ 뒤 같은 숫자를 보나
  for (const k of 기기) { await k.page.click('#btnReload'); await k.page.waitForFunction(() => !/받는 중/.test(document.getElementById('now').textContent)); }
  const nows = await Promise.all(기기.map(k => k.page.textContent('#now')));
  ok(new Set(nows.map(s => s.replace(/\s+/g, ' ').trim())).size === 1, '↻ 뒤 여섯 기기 상황 줄이 같음 — ' + nows[0].replace(/\s+/g, ' ').trim().slice(0, 50));
  const pcEv = await 기기[4].page.$$eval('#cal .d', els => els.map(e => e.querySelectorAll('.ev').length));
  ok(Math.max(...pcEv) <= 3 && await 기기[4].page.locator('#cal .more').count() >= 1, 'PC 달력 칸은 최대 3건 + «+n» (제일 많은 칸 ' + Math.max(...pcEv) + '건 · +n 표시 ' + await 기기[4].page.locator('#cal .more').count() + '칸)');
  const rows0 = await 기기[4].page.locator('#weekRows tr.row').count();
  ok(rows0 <= 12 && await 기기[4].page.locator('#weekMore').count() === 1, 'PC 이번 주 표는 처음 ' + rows0 + '줄 + [모두 보기]');
  await 기기[4].page.click('#weekMore');
  ok(await 기기[4].page.locator('#weekRows tr.row').count() > 12, '[모두 보기] 누르면 전부 (' + await 기기[4].page.locator('#weekRows tr.row').count() + '줄)');
  const memoW = await 기기[4].page.evaluate(() => document.querySelector('#weekRows tr.row td:nth-child(5)').getBoundingClientRect().width);
  ok(memoW >= 120, '메모 칸 폭 ' + Math.round(memoW) + 'px (글자가 세로로 안 꺾임)');
  await 기기[4].page.screenshot({ path: path.join(SHOTS, '20명_2_PC.png'), fullPage: true });
  // 폰 올리기 판 — 이름 칩 20개가 몇 줄이나 · 올리기 단추까지 스크롤 얼마나
  const ph = 기기[0].page; await ph.click('#fab'); await ph.waitForTimeout(300);
  const 칩 = await ph.evaluate(() => { const c = [...document.querySelectorAll('#whoPick .chip')]; const tops = new Set(c.map(e => Math.round(e.getBoundingClientRect().top))); return { n: c.length, rows: tops.size, formH: document.getElementById('form').scrollHeight, saveTop: document.getElementById('btnSave').getBoundingClientRect().top }; });
  ok(칩.n === 20 && 칩.rows <= 5, '폰 올리기 판 : 이름 칩 20개가 ' + 칩.rows + '줄 · 판 높이 ' + 칩.formH + 'px (올리기 단추까지 한 번 밀면 닿음)');
  await ph.screenshot({ path: path.join(SHOTS, '20명_3_폰_올리기.png') });
  // 폰 오늘 판 — 제일 사람 많은 날
  await ph.click('#btnClose'); await ph.waitForTimeout(200);
  await ph.evaluate(d => { document.querySelector('#days .day[data-d="' + d + '"]')?.click(); }, maxDay);
  await ph.waitForTimeout(200);
  const cards = await ph.locator('#todayCards .cards').first().locator('.card').count();
  ok(cards >= 1, '폰 오늘 판 · 제일 많은 날 ' + maxDay + ' 카드 ' + cards + '장 (스크롤로 다 보임)');
  const restN = await ph.locator('#todayCards .cards').last().locator('.card').count();
  ok(restN <= 8 && (await ph.locator('#restMore').count()) <= 1, '폰 이번 주 나머지는 처음 ' + restN + '장' + (await ph.locator('#restMore').count() ? ' + [더 보기]' : ''));
  await ph.screenshot({ path: path.join(SHOTS, '20명_4_폰_많은날.png'), fullPage: true });
  ok(errors.length === 0, '화면 오류 0' + (errors.length ? ' — ' + errors.slice(0, 3).join(' | ') : ''));
  await b.close(); fs.unlinkSync(tmp);

  console.log('3. 구글 한도 어림 (하루)');
  const perLoad = 1; // 화면자료 한 번
  const 열기 = 20 * 6, 올리기수 = 20 * 1.5, 고치기수 = 5;
  const 서버부름 = 열기 * perLoad + 올리기수 + 고치기수;
  ok(서버부름 < 20000, '하루 서버 부름 약 ' + 서버부름 + '회 (20명 × 하루 6번 열기 + 올림 30 + 고침 5) — 앱스 스크립트 하루 한도(웹앱 부름 · 캘린더 쓰기 5,000 · 트리거 90분)에 한참 못 미침');
  ok(true, '시험에서 실제 서버 부름 ' + calls + '회 · 전체 ' + ((Date.now() - t0) / 1000).toFixed(1) + '초');

  console.log('\n통과 ' + pass + ' · 실패 ' + fail + ' · 그림 ' + SHOTS);
  process.exit(fail ? 1 : 0);
})().catch(e => { console.error('시험 자체가 터짐:', e); process.exit(2); });
