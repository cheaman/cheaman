// 서버 쪽(Code.gs) 시험 — node 3_시험/test-server.js   (가짜 구글 · 진짜 캘린더에 닿지 않음)
process.env.TZ = 'Asia/Seoul';
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const { makeGlobals } = require('./fake-google');

const CODE = fs.readFileSync(path.join(__dirname, '../2_앱스스크립트/Code.gs'), 'utf8');
let pass = 0, fail = 0;
function ok(cond, name) { if (cond) { pass++; console.log('  ✓ ' + name); } else { fail++; console.log('  ✗ ' + name); } }
function throws(fn, re, name) { try { fn(); ok(false, name + ' (안 터짐)'); } catch (e) { ok(re.test(e.message), name + ' — ' + e.message); } }

function boot() {
  const env = makeGlobals(Date.now());
  const ctx = vm.createContext({ ...env.g });
  vm.runInContext(CODE, ctx, { filename: 'Code.gs' });
  return { ...env, ctx };
}
const rows = (E, name, w) => { const s = E.ss.getSheetByName(name); const n = s.getLastRow() - 1; return n > 0 ? s.getRange(2, 1, n, w).getValues() : []; };
const key = E => rows(E, '설정', 2).find(r => r[0] === '공유 열쇠')[1];

console.log('1. 처음 설정');
let E = boot();
let msg = E.ctx.setup();
ok(['부서원', '종류', '과업', '설정', '기록'].every(n => E.ss.getSheetByName(n)), '시트 다섯이 생김');
ok(!E.ss.getSheetByName('시트1'), '빈 「시트1」 정리');
const k = key(E);
ok(typeof k === 'string' && k.length >= 16, '공유 열쇠가 생김 (' + String(k).length + '자)');
const calId = rows(E, '설정', 2).find(r => r[0] === '캘린더 번호')[1];
ok(E.calendars[calId] && E.calendars[calId].getName() === '구조부 일정', '캘린더 「구조부 일정」 새로 만들어 번호를 설정에 적음');
ok(/캘린더 「구조부 일정」 새로 만듦/.test(msg), '결과 글 — ' + msg);
const msg2 = E.ctx.setup();
ok(key(E) === k && Object.keys(E.calendars).length === 1 && /있는 캘린더 씀/.test(msg2), 'setup 두 번 해도 열쇠 · 캘린더 그대로');
ok(rows(E, '부서원', 4).length === 6 && rows(E, '종류', 4).length === 7, '부서원 예시 6 · 종류 예시 7');

console.log('2. 열쇠 · 웹 화면');
throws(() => E.ctx.화면자료('틀린열쇠'), /열쇠/, '틀린 열쇠는 막힘');
let out = E.ctx.doGet({ parameter: {} });
ok(out.kind === 'html' && /열쇠가 없거나/.test(out.src) && out.xframe === 'ALLOWALL' && /못받음/.test(out.src), '열쇠 없이 열면 거절 화면 (ALLOWALL · 못받음 신호)');
out = E.ctx.doGet({ parameter: { m: k } });
ok(out.src === '<template:Index>' && out.vars.열쇠 === k && out.xframe === 'ALLOWALL' && out.meta.some(m => m[0] === 'viewport'), '맞는 열쇠면 Index 틀 + 열쇠 · ALLOWALL · viewport');
out = E.ctx.doGet({ parameter: { 오늘: '', m: k } });
let j = JSON.parse(out.body);
ok(out.kind === 'text' && out.mime === 'application/json' && j.전체 === 6 && j.밖.length === 0, '?오늘 → JSON 요약 (전체 6 · 밖 0)');
j = JSON.parse(E.ctx.doGet({ parameter: { 오늘: '', m: 'x' } }).body);
ok(!!j.오류, '?오늘 도 열쇠 없으면 오류');

console.log('3. 일정 올리기');
const 화면 = E.ctx.화면자료(k);
ok(화면.부서원.map(p => p.이름)[0] === '전채만' && 화면.종류.length === 7 && 화면.과업.length === 2 && 화면.일정.length === 0, '화면자료 : 부서원 · 종류 · 과업 · 일정 0');
ok(/^\d{4}-\d{2}-\d{2}$/.test(화면.오늘) && 화면.범위[0] < 화면.오늘 && 화면.범위[1] > 화면.오늘, '오늘 · 범위 글 날짜');
let a = E.ctx.일정올리기(k, { 누가: '난○○', 종류: '출장', 시작: '2026-11-03', 끝: '2026-11-04', 어디: '대전 · 발주처', 메모: '심의', 과업: 'D197', 화면: '폰-난' });
ok(a.id && a.제목 === '[출장] 난○○ · 대전 · 발주처 · D197' && a.시작 === '2026-11-03' && a.끝 === '2026-11-04', '이틀 출장 — 제목 · 시작 · 끝 : ' + a.제목);
const ev = E.calendars[calId].getEventById(a.id);
ok(ev.isAllDayEvent() && ev.getAllDayEndDate().getDate() === 5, '캘린더에는 종일 · 끝은 다음날(11/5) 로');
ok(/누가: 난○○/.test(ev.getDescription()) && ev.getTag('과업') === 'D197', '설명 · 태그에 담김');
let b = E.ctx.일정올리기(k, { 누가: '김○○', 종류: '반차', 시작: '2026-11-03', 시간대: '오후', 화면: 'PC' });
ok(b.끝 === '2026-11-03' && b.제목 === '[반차] 김○○ (오후)' && b.시간대 === '오후', '하루 반차 (끝 비움 → 시작과 같음) : ' + b.제목);
throws(() => E.ctx.일정올리기(k, { 종류: '출장', 시작: '2026-11-03' }), /누가/, '누가 없으면');
throws(() => E.ctx.일정올리기(k, { 누가: '홍길동', 종류: '출장', 시작: '2026-11-03' }), /부서원 시트에 없습니다/, '부서원 밖 이름');
throws(() => E.ctx.일정올리기(k, { 누가: '전채만', 종류: '야근', 시작: '2026-11-03' }), /종류 시트에 없습니다/, '없는 종류');
throws(() => E.ctx.일정올리기(k, { 누가: '전채만', 종류: '출장', 시작: '11월 3일' }), /날짜/, '날짜 꼴 틀림');
throws(() => E.ctx.일정올리기(k, { 누가: '전채만', 종류: '출장', 시작: '2026-11-05', 끝: '2026-11-03' }), /앞입니다/, '끝이 앞');
throws(() => E.ctx.일정올리기(k, { 누가: '전채만', 종류: '휴가', 시작: '2026-11-01', 끝: '2027-03-01' }), /60일/, '60일 넘음');
throws(() => E.ctx.일정올리기(k, { 누가: '전채만', 종류: '반차', 시작: '2026-11-03', 시간대: '저녁' }), /시간대/, '시간대 틀림');
let 기록 = rows(E, '기록', 6);
ok(기록.length === 2 && 기록[0][1] === '올림' && 기록[0][5] === '폰-난' && 기록[1][5] === 'PC', '기록 두 줄 (올림 · 화면 이름)');

console.log('4. 목록 · 오늘 요약');
let lst = E.ctx.화면자료(k, '2026-11-03');
ok(lst.일정.length === 2 && lst.일정[0].누가 === '김○○' && lst.일정[1].누가 === '난○○', '같은 날은 이름 순');
ok(lst.요약.날짜 === '2026-11-03' && lst.요약.밖수 === 2 && lst.요약.자리.length === 4 && lst.요약.자리.indexOf('난○○') < 0, '11/3 요약 : 밖 2 · 자리 4');
lst = E.ctx.화면자료(k, '2026-11-04');
ok(lst.요약.밖수 === 1 && lst.요약.밖[0].누가 === '난○○', '11/4 요약 : 출장 둘째 날만 (반차는 끝남)');
lst = E.ctx.화면자료(k, '2026-11-05');
ok(lst.요약.밖수 === 0, '11/5 요약 : 아무도 없음');
// 화면 밖(구글 캘린더 앱)에서 바로 넣은 일정
E.calendars[calId].createAllDayEvent('[휴가] 이○○ · 연차', new Date(2026, 10, 10), new Date(2026, 10, 12));
E.calendars[calId].createAllDayEvent('부서 회식', new Date(2026, 10, 11), new Date(2026, 10, 12));
lst = E.ctx.화면자료(k, '2026-11-11');
const 밖 = lst.일정.filter(e => e.화면밖);
ok(밖.length === 2 && 밖[0].종류 === '휴가' && 밖[0].누가 === '이○○' && 밖[0].끝 === '2026-11-11', '캘린더 앱에서 넣은 「[휴가] 이○○」 도 읽힘');
ok(밖[1].종류 === '그 밖' && 밖[1].누가 === '부서', '꼴이 다른 제목은 「그 밖」 으로');

console.log('5. 고치기 · 지우기 · 되돌리기');
let c = E.ctx.일정고치기(k, a.id, { 끝: '2026-11-05', 어디: '대전', 화면: 'PC' });
ok(c.id === a.id && c.끝 === '2026-11-05' && c.어디 === '대전' && c.누가 === '난○○' && c.제목 === '[출장] 난○○ · 대전 · D197', '끝 · 어디만 바꿔도 나머지 그대로 : ' + c.제목);
ok(E.calendars[calId].getEventById(a.id).getAllDayEndDate().getDate() === 6, '캘린더 끝(다음날) 11/6');
throws(() => E.ctx.일정고치기(k, a.id, { 종류: '야근' }), /종류/, '고칠 때도 검사');
throws(() => E.ctx.일정고치기(k, 'ev999@google.com', { 어디: 'x' }), /찾지 못했습니다/, '없는 일정');
let d = E.ctx.일정지우기(k, b.id, 'PC');
ok(d.id === b.id && !E.calendars[calId].getEventById(b.id), '지우면 캘린더에서 빠지고 내용을 돌려줌');
let r = E.ctx.일정올리기(k, { 누가: d.누가, 종류: d.종류, 시작: d.시작, 끝: d.끝, 시간대: d.시간대, 어디: d.어디, 메모: d.메모, 과업: d.과업, 화면: 'PC' });
ok(r.제목 === b.제목 && r.시작 === b.시작, '되돌리기 = 돌려받은 내용으로 다시 올리기');
기록 = rows(E, '기록', 6);
ok(기록.map(x => x[1]).join(',') === '올림,올림,고침,지움,올림', '기록 차례 : ' + 기록.map(x => x[1]).join(','));

console.log('6. 부서원 끄기 · 순서');
const ps = E.ss.getSheetByName('부서원');
ps.getRange(3, 2).setValue('아니오');          // 난○○ 끔
ps.getRange(7, 3).setValue(0);                 // 최○○ 순서 0 → 맨 앞
let p = E.ctx.화면자료(k).부서원.map(x => x.이름);
ok(p[0] === '최○○' && p.indexOf('난○○') < 0 && p.length === 5, '꺼진 사람 빠지고 순서대로 : ' + p.join(' '));
throws(() => E.ctx.일정올리기(k, { 누가: '난○○', 종류: '출장', 시작: '2026-11-20' }), /부서원 시트에 없습니다/, '꺼진 사람으로는 못 올림');
ok(E.ctx.화면자료(k, '2026-11-04').요약.전체 === 5, '요약 전체 5');

console.log('\n통과 ' + pass + ' · 실패 ' + fail);
process.exit(fail ? 1 : 0);
