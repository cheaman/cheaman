// 서버 쪽(Code.gs) 시험 — node 3_시험/test-server.js
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const { makeGlobals } = require('./fake-google');

const CODE = fs.readFileSync(path.join(__dirname, '../2_앱스스크립트/Code.gs'), 'utf8');
let pass = 0, fail = 0;
function ok(cond, name) { if (cond) { pass++; console.log('  ✓ ' + name); } else { fail++; console.log('  ✗ ' + name); } }
function throws(fn, re, name) { try { fn(); ok(false, name + ' (안 터짐)'); } catch (e) { ok(re.test(e.message), name + ' — ' + e.message); } }

function boot() {
  const now = Date.now();
  const env = makeGlobals(now);
  const ctx = vm.createContext({ ...env.g });
  vm.runInContext(CODE, ctx, { filename: 'Code.gs' });
  const { yt } = env;
  // 예시 채널 중 일부만 "유튜브에 있음" — 나머지는 못 찾는 것 시험
  const a = yt.addChannel('TwoMinutePapers', 'Two Minute Papers', 'HU');
  yt.addVideo(a, { daysAgo: 1, dur: 400 });
  yt.addVideo(a, { daysAgo: 3, dur: 45 });                 // 쇼츠 (UULF 가 거름)
  yt.addVideo(a, { daysAgo: 200, dur: 500 });              // 보관 기간 밖
  const b = yt.addChannel('MarkWiens', 'Mark Wiens', 'TH', { noUULF: true });
  yt.addVideo(b, { daysAgo: 0.1, dur: 1500 });
  yt.addVideo(b, { daysAgo: 2, dur: 30 });                 // 쇼츠 (UULF 없음 → 길이로 거름)
  yt.addVideo(b, { daysAgo: 0.05, dur: 0, live: 'upcoming' }); // 예정 방송
  const c = yt.addChannel('paikscuisine', '백종원 PAIK JONG WON', 'KR');
  yt.addVideo(c, { daysAgo: 5, dur: 900, title: 'Tom & Jerry <b>' });
  const d = yt.addChannel('LostLeBlanc', 'Lost LeBlanc', 'CA');
  yt.addVideo(d, { daysAgo: 4, dur: 1000 });
  return { ...env, ctx, a, b, c, d };
}

const rowsOf = (env, name) => { const s = env.ss.getSheetByName(name); return s.getRange(2, 1, Math.max(0, s.getLastRow() - 1), 9).getValues(); };

console.log('1. 처음 설정');
let E = boot();
let msg = E.ctx.setup();
ok(['채널목록', '영상', '설정'].every(n => E.ss.getSheetByName(n)), '시트 셋이 생김');
ok(!E.ss.getSheetByName('시트1'), '빈 「시트1」 정리');
ok(E.triggers.length === 1 && E.triggers[0].fn === 'collect' && E.triggers[0].hours === 1, '매시간 트리거 하나');
E.ctx.setup();
ok(E.triggers.length === 1, 'setup 을 두 번 해도 트리거는 하나');
let ch = rowsOf(E, '채널목록');
ok(ch.length === 11, '예시 채널 11줄');
const two = ch.find(r => r[1] === 'Two Minute Papers');
ok(two[7] === E.a.id && two[8] === '정상', '채널 번호 채움 · 상태 정상');
ok(two[3] === 'HU', '나라 칸 채움');
const miss = ch.find(r => r[1] === '조코딩');
ok(/^못 받음: 유튜브에서 이 채널을 찾지 못함/.test(miss[8]), '없는 채널은 상태 칸에 이유 — ' + miss[8]);
console.log('   결과: ' + msg);

console.log('2. 모은 영상');
let vids = rowsOf(E, '영상');
const ids = vids.map(r => r[0]);
ok(new Set(ids).size === ids.length, '같은 영상 두 번 안 들어감');
ok(!ids.includes(E.a.items.find(i => i.dur === 500).id), '보관 기간(90일) 밖 영상은 안 넣음');
ok(!ids.includes(E.a.items.find(i => i.dur === 45).id), 'UULF 로 쇼츠 거름');
const bShort = vids.find(r => r[0] === E.b.items.find(i => i.dur === 30).id);
ok(bShort && bShort[6] === '쇼츠', 'UULF 없는 채널은 길이로 쇼츠 표시');
ok(!ids.includes(E.b.items.find(i => i.live === 'upcoming').id), '예정 방송은 안 넣음');
ok(vids.every(r => r[4] && typeof r[4].getTime === 'function'), '올린 때는 날짜');
ok(vids.find(r => r[1] === 'Tom & Jerry <b>')[5] === 900, '길이(초) 채움');

console.log('3. 다시 모으기 (한 시간 뒤)');
const before = vids.length, u0 = E.yt.units.n;
msg = E.ctx.collect();
ok(rowsOf(E, '영상').length === before, '새 영상 없으면 줄 수 그대로');
ok(E.yt.units.n - u0 <= 2 * 11, '유튜브 한도 적게 씀 — 이번에 ' + (E.yt.units.n - u0) + '점 (채널 11줄 · 못 찾은 7줄은 매시간 다시 찾음) · 하루 ' + 24 * (E.yt.units.n - u0) + '점 / 10,000');
E.yt.addVideo(E.d, { daysAgo: 0.01, dur: 700 });
msg = E.ctx.collect();
ok(/새 영상 1개/.test(msg), '새로 올라온 것 1개 들어옴 — ' + msg);
const setRows = rowsOf(E, '설정');
ok(setRows.find(r => r[0] === '마지막 결과')[1] === msg, '설정에 마지막 결과 기록');

console.log('4. 화면용 목록');
let feed = E.ctx.getFeed();
ok(JSON.stringify(feed.cats) === JSON.stringify(['AI', '여행', '음식/레시피']), '카테고리 순서 = 채널목록 순서');
ok(feed.videos.every((v, i, a) => i === 0 || a[i - 1].pub >= v.pub), '최신순');
ok(!feed.videos.some(v => v.st === '쇼츠'), '쇼츠는 화면에 안 나옴');
ok(feed.videos.find(v => v.ch === 'Mark Wiens').cc === 'TH', '나라 표시 넘김');
ok(typeof feed.last === 'number' && feed.last > 0, '마지막으로 모은 때 = 숫자');
ok(JSON.parse(JSON.stringify(feed)).videos.length === feed.videos.length, '화면으로 넘길 수 있는 꼴 (날짜 없음)');

console.log('5. 봤음 · 나중에 · 숨김');
const v0 = feed.videos[0].id;
E.ctx.setState(v0, '나중에');
ok(E.ctx.getFeed().videos.find(v => v.id === v0).st === '나중에', '나중에 저장');
E.ctx.setState(v0, '숨김');
ok(!E.ctx.getFeed().videos.find(v => v.id === v0), '숨김은 화면에서 빠짐');
E.ctx.setState(v0, '새 영상');
ok(!!E.ctx.getFeed().videos.find(v => v.id === v0), '새 영상으로 되돌리면 다시 보임');
throws(() => E.ctx.setState(v0, '지움'), /알 수 없는 상태/, '모르는 상태는 거절');
throws(() => E.ctx.setState('없는영상', '봤음'), /찾지 못함/, '없는 영상은 거절');

console.log('6. 채널 끄기');
const chSheet = E.ss.getSheetByName('채널목록');
const rowNo = rowsOf(E, '채널목록').findIndex(r => r[1] === 'Mark Wiens') + 2;
chSheet.getRange(rowNo, 5).setValue('아니오');
ok(!E.ctx.getFeed().videos.some(v => v.ch === 'Mark Wiens'), '켜기=아니오 인 채널 영상은 안 보임');
chSheet.getRange(rowNo, 5).setValue('예');

console.log('7. 채널 담기');
const e = E.yt.addChannel('kurzgesagt', 'Kurzgesagt', 'DE');
E.yt.addVideo(e, { daysAgo: 2, dur: 720 });
let r = E.ctx.addChannel('https://www.youtube.com/@kurzgesagt?si=abc', '과학');
ok(r.name === 'Kurzgesagt' && /새 영상 1개/.test(r.message), '주소로 담고 바로 영상 받음 — ' + r.message);
feed = E.ctx.getFeed();
ok(feed.cats.includes('과학') && feed.videos.some(v => v.cat === '과학'), '새 카테고리 탭 생김');
throws(() => E.ctx.addChannel('https://www.youtube.com/channel/' + e.id, 'AI'), /이미 담은 채널/, '같은 채널 두 번 안 담김');
throws(() => E.ctx.addChannel('https://www.youtube.com/@nobody', 'AI'), /찾지 못함/, '없는 채널은 이유를 알려 줌');
throws(() => E.ctx.addChannel('그냥 글자 아무거나', 'AI'), /알아볼 수 없음/, '주소가 아니면 알려 줌');
throws(() => E.ctx.addChannel('@kurzgesagt', ''), /카테고리/, '카테고리 없으면 거절');

console.log('8. 찾기');
const u1 = E.yt.units.n;
const found = E.ctx.search('street food', 'en', 'US');
ok(found.length > 0 && found[0].chId && found[0].id, '검색 결과에 채널 번호 · 영상 번호');
ok(E.yt.units.lastSearch.relevanceLanguage === 'en' && E.yt.units.lastSearch.regionCode === 'US', '언어 · 나라 넘김');
ok(E.yt.units.n - u1 === 100, '검색 한 번 = 100점');
const f2 = E.ctx.search('x', '', '');
ok(!('relevanceLanguage' in E.yt.units.lastSearch) && !('regionCode' in E.yt.units.lastSearch), '가리지 않음이면 조건 안 붙임');
throws(() => E.ctx.search('  ', 'en', 'US'), /낱말/, '빈 검색 거절');

console.log('9. 오래된 것 정리 — 나중에는 남김');
const vs = E.ss.getSheetByName('영상');
const all = rowsOf(E, '영상');
const old1 = all[0][0], old2 = all[1][0];
vs.getRange(2, 5).setValue(new (vm.runInContext('Date', E.ctx))(Date.now() - 100 * 86400000));
vs.getRange(3, 5).setValue(new (vm.runInContext('Date', E.ctx))(Date.now() - 100 * 86400000));
vs.getRange(3, 7).setValue('나중에');
E.ctx.collect();
const after = rowsOf(E, '영상').map(r => r[0]);
ok(!after.includes(old1), '100일 지난 영상 정리');
ok(after.includes(old2), '「나중에」는 오래돼도 남김');

console.log('10. 쇼츠 빼기 = 아니오');
E = boot(); E.ctx.setup();
const st = E.ss.getSheetByName('설정');
st.getRange(2, 2).setValue('아니오');
const s2 = E.yt.addChannel('shortsguy', 'Shorts Guy', 'US');
E.yt.addVideo(s2, { daysAgo: 1, dur: 40 });
E.ctx.addChannel('@shortsguy', '여행');
ok(E.ctx.getFeed().videos.some(v => v.ch === 'Shorts Guy' && v.dur === 40), '쇼츠도 화면에 나옴');

console.log('11. 유튜브 API 서비스가 꺼져 있을 때 (RSS 보조 길)');
E = boot();
delete E.ctx.YouTube;
E.ss.insertSheet('채널목록').getRange(1, 1, 2, 9).setValues([
  ['카테고리', '채널 이름', '채널 주소', '나라·언어', '켜기', '메모', '넣은 날', '채널 번호(자동)', '상태(자동)'],
  ['AI', 'RSS 채널', 'https://www.youtube.com/channel/UCabcdefghijklmnopqrstuv', '', '예', '', '', '', '']
]);
E.rss['UCabcdefghijklmnopqrstuv'] = '<feed><entry><yt:videoId>rss1</yt:videoId><title>A &amp; B</title><published>' + new Date().toISOString() + '</published></entry></feed>';
msg = E.ctx.setup();
ok(/RSS로 받음/.test(msg) && /새 영상 1개/.test(msg), 'RSS 로 영상 받음 — ' + msg);
ok(rowsOf(E, '영상')[0][1] === 'A & B', 'RSS 제목 글자 되살림');
ok(!E.ctx.getFeed().canSearch, '찾기는 꺼짐으로 알림');
throws(() => E.ctx.search('x'), /서비스를 켜야/, '찾기는 이유를 알려 줌');

console.log('12. 작은 도우미');
ok(E.ctx.parseDuration_('PT1H2M3S') === 3723 && E.ctx.parseDuration_('PT45S') === 45 && E.ctx.parseDuration_('P0D') === 0, '길이 읽기');
const p = E.ctx.parseChannelInput_;
ok(p('https://www.youtube.com/@MarkWiens/videos').handle === 'MarkWiens', '@주소/videos');
ok(p('https://youtube.com/channel/UCabcdefghijklmnopqrstuv?si=1').id === 'UCabcdefghijklmnopqrstuv', '/channel/UC…');
ok(p('https://www.youtube.com/@%EB%B0%B1%EC%A2%85%EC%9B%90').handle === '백종원', '한글 @주소');
ok(p('https://m.youtube.com/user/Maangchi').user === 'Maangchi', '/user/ 옛 주소');
ok(p('@jocoding').handle === 'jocoding', '@이름만');

console.log('\n통과 ' + pass + ' · 실패 ' + fail);
process.exit(fail ? 1 : 0);
