// 화면(Index.html) 시험 — 실제 브라우저로 눌러 본다. 서버는 Code.gs + 가짜 구글 (진짜 캘린더에 닿지 않음)
// NODE_PATH=$(npm root -g) node 3_시험/test-screen.js [그림 저장 폴더]
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
function ok(c, n) { if (c) { pass++; console.log('  ✓ ' + n); } else { fail++; console.log('  ✗ ' + n); } }
const F = d => d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
const addD = (d, n) => { const x = new Date(d); x.setDate(x.getDate() + n); return x; };

function boot() {
  const env = makeGlobals(Date.now());
  const ctx = vm.createContext({ ...env.g });
  vm.runInContext(CODE, ctx);
  ctx.setup();
  const rows = env.ss.getSheetByName('설정').getRange(2, 1, 5, 2).getValues();
  const key = rows.find(r => r[0] === '공유 열쇠')[1];
  const today = new Date(); today.setHours(0, 0, 0, 0);
  // 본보기 일정 — 오늘 기준
  ctx.일정올리기(key, { 누가: '난○○', 종류: '출장', 시작: F(today), 어디: '대전 · 발주처', 메모: 'D197 심의', 과업: 'D197', 화면: '시험' });
  ctx.일정올리기(key, { 누가: '이○○', 종류: '휴가', 시작: F(addD(today, -1)), 끝: F(addD(today, 1)), 메모: '연차 3일', 화면: '시험' });
  ctx.일정올리기(key, { 누가: '박○○', 종류: '외근', 시작: F(addD(today, 2)), 어디: '양촌 과도교', 화면: '시험' });
  ctx.일정올리기(key, { 누가: '김○○', 종류: '반차', 시작: F(addD(today, -5)), 시간대: '오전', 화면: '시험' });
  ctx.일정올리기(key, { 누가: '최○○', 종류: '교육', 시작: F(addD(today, 20)), 끝: F(addD(today, 22)), 메모: '내진 설계', 화면: '시험' });
  // 공휴일(시험용 · 사흘 뒤) · 과업 캘린더(오늘 심의)
  const hol = env.calendars['ko.south_korea#holiday@group.v.calendar.google.com'];
  hol.createAllDayEvent('시험공휴일', addD(today, 3));
  const tc = env.g.CalendarApp.createCalendar('구조부 과업');
  const st = env.ss.getSheetByName('설정'); st.getRange(2, 1, 8, 2).getValues().forEach((r, i) => { if (r[0] === '과업 캘린더 번호') st.getRange(i + 2, 2).setValue(tc.getId()); });
  tc.createAllDayEvent('[심의] D197 이설표지판 · 대전', today);
  tc.createAllDayEvent('[납품] D196 강릉제진', addD(today, 4));
  return { ...env, ctx, key, today };
}

(async () => {
  const E = boot();
  // 틀 변수(<?= 열쇠 ?>) 를 채운 시험용 HTML
  const tmp = path.join(os.tmpdir(), 'Index.시험.html');
  fs.writeFileSync(tmp, HTML_SRC.replace('<?= 열쇠 ?>', E.key).replace('<?= 판 ?>', 'v시험'));
  const b = await chromium.launch();
  const errors = [];
  const calls = [];
  async function open(viewport) {
    const page = await b.newPage({ viewport, deviceScaleFactor: 1 });
    page.on('pageerror', e => errors.push(e.message));
    page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
    await page.route('**/*', r => (r.request().url().startsWith('file:') ? r.continue() : r.abort()));
    await page.exposeFunction('__gas', (fn, args) => {
      calls.push(fn);
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
      window.__msgs = []; window.top.addEventListener('message', e => window.__msgs.push(e.data));
    });
    await page.goto('file://' + tmp);
    await page.waitForSelector('#now:not(:empty)');
    await page.waitForFunction(() => !/받는 중/.test(document.getElementById('now').textContent));
    return page;
  }
  const calEvents = () => E.calendars[Object.keys(E.calendars)[0]].events;

  console.log('1. 폰 첫 화면 (375)');
  let p = await open({ width: 375, height: 812 });
  ok(await p.evaluate(() => document.documentElement.scrollWidth) === 375, '옆으로 안 밀림');
  ok(await p.evaluate(() => window.__msgs.some(m => m && m.부서일정 === '떴음')), '「떴음」 신호 보냄');
  let now = await p.textContent('#now');
  ok(/오늘 부서 밖 2명/.test(now) && /출장 1/.test(now) && /휴가 1/.test(now), '상황 줄 : ' + now.trim().slice(0, 60));
  ok(await p.locator('#todayPanel').isVisible() && !(await p.locator('#calBody').isVisible()), '오늘 판이 먼저 · 달력은 접힘');
  let cards = await p.$$eval('#todayCards .card', els => els.map(e => e.textContent));
  ok(cards.length >= 3 && /난○○출장/.test(cards[0].replace(/\s/g, '')) && /이○○휴가/.test(cards[1].replace(/\s/g, '')), '오늘 카드 : 난○○ 출장 · 이○○ 휴가');
  ok(/2\/3 일째|둘째/.test(cards[1]) || /일째/.test(cards[1]), '여러 날 일정은 «n/n 일째» — ' + cards[1].trim().slice(0, 40));
  ok(/자리에 있음/.test(await p.textContent('#todayCards')) && /전채만/.test(await p.textContent('#todayCards .inside')), '자리에 있음 줄');
  ok((await p.$$('#days .day')).length === 7 && await p.locator('#days .day.on').count() === 1, '날짜 띠 7칸 · 오늘 표시');
  ok(/이번 주 나머지/.test(await p.textContent('#todayCards')), '이번 주 나머지 칸');
  ok(/과업 날짜 · \[심의\] D197 이설표지판 · 대전/.test(await p.textContent('#todayCards .taskline')), '오늘 과업 날짜 줄 (부서 밖 셈에는 안 들어감)');
  ok(await p.locator('#days .day.hol').count() === (addD(E.today, 3) <= addD(E.today, 6 - ((E.today.getDay() + 6) % 7)) ? 1 : 0), '날짜 띠 공휴일 빨강 (이번 주 안이면 1)');
  await p.screenshot({ path: path.join(SHOTS, '1_폰_오늘.png') });

  console.log('2. 폰에서 올리기');
  await p.click('#fab');
  await p.waitForTimeout(300);
  ok(await p.locator('#form.open').isVisible() && (await p.textContent('#formTitle')) === '일정 올리기', '큰 단추 → 올리기 판 열림');
  await p.click('#whoPick .chip:has-text("전채만")');
  await p.click('#kindPick .chip:has-text("출장")');
  await p.click('.quick [data-q="내일"]');
  await p.fill('#where', '대전');
  await p.fill('#memo', '심의');
  await p.click('#taskPick .chip:has-text("D197")');
  const pv = await p.textContent('#preview');
  ok(/\[출장\] 전채만 · 대전 · D197/.test(pv), '미리 보기 : ' + pv.trim());
  await p.screenshot({ path: path.join(SHOTS, '2_폰_올리기.png') });
  const n0 = calEvents().length;
  await p.click('#btnSave');
  await p.waitForSelector('#result.ok');
  ok(calEvents().length === n0 + 1 && /\[출장\] 전채만 · 대전 · D197/.test(calEvents()[n0].getTitle()), '캘린더에 들어감 : ' + calEvents()[n0].getTitle());
  ok(/됨/.test(await p.textContent('#result')), '결과 글 「됨」');
  ok(await p.locator('#toast:not(.hidden)').isVisible() && (await p.textContent('#toastBtn')) === '되돌리기', '띠에 「되돌리기」');
  ok(await p.evaluate(() => localStorage.getItem('구조부일정.나')) === '전채만', '이름 기억');
  await p.waitForTimeout(1000);
  ok(!(await p.locator('#form.open').isVisible()), '폰은 올린 뒤 판이 닫힘');
  const 내일카드 = await p.textContent('#todayCards');
  ok(/내일/.test(내일카드) && /전채만/.test(내일카드), '내일 칸에 전채만 보임');

  console.log('3. 폰에서 고치기 · 지우기 · 되돌리기');
  await p.click('#todayCards .card:has-text("난○○")');
  await p.waitForTimeout(300);
  ok((await p.textContent('#formTitle')) === '일정 고치기' && (await p.inputValue('#where')) === '대전 · 발주처', '카드 누르면 고치기 판 · 값 채워짐');
  await p.fill('#where', '세종');
  await p.click('#btnSave');
  await p.waitForSelector('#result.ok');
  const e난 = calEvents().find(e => /난○○/.test(e.getTitle()));
  ok(/세종/.test(e난.getTitle()) && e난.getTag('과업') === 'D197', '어디만 바뀜 · 과업 그대로 : ' + e난.getTitle());
  await p.click('#btnDel');
  await p.waitForTimeout(300);
  ok(!calEvents().some(e => /난○○/.test(e.getTitle())), '지우면 캘린더에서 빠짐');
  ok(!(await p.$$eval('#todayCards .card', els => els.map(e => e.textContent).join())).includes('난○○'), '오늘 카드에서도 빠짐');
  await p.click('#toastBtn');
  await p.waitForTimeout(300);
  ok(calEvents().some(e => /\[출장\] 난○○ · 세종 · D197/.test(e.getTitle())), '되돌리기 → 같은 내용으로 다시 올라감');
  ok((await p.$$eval('#todayCards .card', els => els.map(e => e.textContent).join())).includes('난○○'), '오늘 카드에 다시 보임');
  const 기록 = E.ss.getSheetByName('기록'); const 기록줄 = 기록.getRange(2, 1, 기록.getLastRow() - 1, 6).getValues();
  ok(기록줄.slice(-4).map(r => r[1]).join(',') === '올림,고침,지움,올림' && /전채만 폰/.test(기록줄.at(-1)[5]), '기록 : ' + 기록줄.slice(-4).map(r => r[1] + '(' + r[5] + ')').join(' '));

  console.log('4. 폰 달력 펼치기 · 날짜 띠');
  await p.click('#calHead');
  ok(await p.locator('#calBody').isVisible() && (await p.$$('#cal .d')).length === 42, '달력 펼침 · 42칸');
  ok(await p.locator('#cal .d.today .dots i').count() >= 2, '오늘 칸에 점 2개 이상');
  const 띠 = await p.$$('#days .day');
  await 띠[6].click();
  ok(await p.locator('#days .day.on').count() === 1 && !(await p.locator('#days .day').nth(6).evaluate(e => !e.classList.contains('on'))), '날짜 띠 일요일 누르면 그날로');
  await p.click('#goToday');
  await p.screenshot({ path: path.join(SHOTS, '3_폰_달력.png') });
  ok(errors.length === 0, '폰 화면 오류 0' + (errors.length ? ' — ' + errors.join(' | ') : ''));
  await p.close();

  console.log('5. PC (1366)');
  p = await open({ width: 1366, height: 768 });
  ok(await p.evaluate(() => document.documentElement.scrollWidth) === 1366, '옆으로 안 밀림');
  ok(!(await p.locator('#todayPanel').isVisible()) && await p.locator('#calBody').isVisible() && await p.locator('#form').isVisible(), 'PC 는 달력 + 올리기 카드 나란히');
  ok(await p.locator('#cal .d.today').count() === 1 && (await p.locator('#cal .d.today').boundingBox()).width > 50 && (await p.$$('#cal .d')).length === 42, '오늘 칸 하나 · 보임 · 42칸');
  ok(await p.locator('#cal .d.today .ev.task').count() === 1 && /\[심의\] D197/.test(await p.textContent('#cal .d.today .ev.task')), '오늘 칸에 과업 띠(회색 점선)');
  ok(/시험공휴일/.test(await p.textContent('#cal')) && await p.locator('#cal .d.hol').count() >= 1, '공휴일 이름 · 빨강');
  ok(await p.locator('#kindChips .chip[data-k="과업"]').count() === 1, '종류 칩에 「과업」');
  ok(await p.locator('#weekRows tr.taskrow').count() >= 1, '이번 주 표에 과업 줄');
  const evTexts = await p.$$eval('#cal .ev', els => els.map(e => e.textContent.trim()).filter(Boolean));
  ok(evTexts.some(t => /출장 난○○ · 세종/.test(t)) && evTexts.some(t => /휴가 이○○/.test(t)), '달력에 글 띠 : ' + evTexts.slice(0, 3).join(' | '));
  const 첫칸 = await p.$$eval('#cal .dow', els => els.map(e => e.textContent));
  ok(첫칸[0] === '월' && 첫칸[6] === '일', '월요일 시작');
  const rows = await p.$$eval('#weekRows tr.row', els => els.map(e => e.textContent));
  ok(rows.length >= 3 && rows.some(r => /휴가/.test(r) && /이○○/.test(r)), '이번 주 표 ' + rows.length + '줄');
  ok(await p.locator('#weekRows tr.is-now').count() >= 2, '오늘 걸린 줄 강조');
  await p.screenshot({ path: path.join(SHOTS, '4_PC.png'), fullPage: true });

  console.log('6. PC 거르기 · 달 넘기기 · 표에서 고치기');
  await p.click('#kindChips .chip:has-text("휴가")');
  let evs = await p.$$eval('#cal .ev', els => els.map(e => e.textContent.trim()).filter(Boolean));
  ok(evs.length > 0 && evs.every(t => /^휴가/.test(t)), '종류 칩 「휴가」 → 휴가만 (과업 띠도 빠짐)');
  await p.click('#kindChips .chip[data-k="과업"]');
  evs = await p.$$eval('#cal .ev', els => els.map(e => e.textContent.trim()).filter(Boolean));
  ok(evs.length === 2 && evs.every(t => /^\[/.test(t)), '종류 칩 「과업」 → 과업 날짜만 ' + evs.length);
  await p.click('#cal .ev.task');
  ok(/업무현황/.test(await p.textContent('#toastMsg')), '과업 띠 누르면 안내 띠');
  await p.click('#kindChips .chip:has-text("휴가")');
  await p.click('#whoChips .chip:has-text("전채만")');
  ok((await p.$$('#cal .ev')).length === 0, '휴가 + 전채만 → 없음');
  await p.click('#kindChips .chip:has-text("전체")'); await p.click('#whoChips .chip:has-text("전체")');
  const t0 = await p.textContent('#calTitle');
  await p.click('#nextM');
  ok((await p.textContent('#calTitle')) !== t0, '다음 달 : ' + await p.textContent('#calTitle'));
  await p.click('#goToday');
  ok((await p.textContent('#calTitle')) === t0, '오늘 단추로 돌아옴');
  await p.click('#weekRows tr.row:has-text("이○○")');
  ok((await p.textContent('#formTitle')) === '일정 고치기' && (await p.inputValue('#memo')) === '연차 3일', '표 줄 누르면 오른쪽 카드가 고치기로');
  await p.click('#btnNew');
  ok((await p.textContent('#formTitle')) === '일정 올리기', '「새로 올리기」 로 돌아옴');
  // 서버가 거절하면 결과 칸에 까닭
  await p.click('#whoPick .chip:has-text("전채만")'); await p.click('#kindPick .chip:has-text("휴가")');
  await p.fill('#d1', '2026-01-10'); await p.fill('#d2', '2026-01-05');
  await p.click('#btnSave');
  await p.waitForSelector('#result.bad');
  ok(/앞입니다/.test(await p.textContent('#result')), '거절 까닭이 결과 칸에 : ' + (await p.textContent('#result')).trim());
  // 다른 PC 에서 바뀐 것 — ↻ 로 받기
  E.ctx.일정올리기(E.key, { 누가: '박○○', 종류: '회의', 시작: F(E.today), 메모: '다른 PC 에서', 화면: '다른PC' });
  await p.click('#btnReload');
  await p.waitForFunction(() => /부서 밖 3명/.test(document.getElementById('now').textContent));
  ok(true, '↻ 뒤 상황 줄 「부서 밖 3명」');
  ok(errors.length === 0, 'PC 화면 오류 0' + (errors.length ? ' — ' + errors.join(' | ') : ''));
  await p.screenshot({ path: path.join(SHOTS, '5_PC_고치기.png') });
  await p.close();
  await b.close();
  fs.unlinkSync(tmp);
  console.log('\n통과 ' + pass + ' · 실패 ' + fail + ' · 서버 부른 횟수 ' + calls.length + ' · 그림 ' + SHOTS);
  process.exit(fail ? 1 : 0);
})().catch(e => { console.error('시험 자체가 터짐:', e); process.exit(2); });
