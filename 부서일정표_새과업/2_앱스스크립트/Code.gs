/**
 * 구조부 일정 — 구글 앱스 스크립트 (1판)
 *
 * 자료의 집 : 구글 캘린더 「구조부 일정」 (출장 · 휴가 · 외근 … 전부 여기)
 * 시트 다섯
 *   부서원 : 이름 · 켜기 · 순서            ← 전무님이 고치는 곳
 *   종류   : 출장 · 휴가 … 색             ← 전무님이 고치는 곳
 *   과업   : D197 이설표지판 …            ← 전무님이 고치는 곳 (비워도 됨)
 *   설정   : 캘린더 번호 · 공유 열쇠 …     ← setup 이 채움
 *   기록   : 누가 언제 무엇을 올리고 고치고 지웠나 (자동)
 *   가져오기 : 여러 줄을 적고 가져오기 를 ▶ 실행하면 한 번에 캘린더로 (호두 자료 옮길 때)
 *
 * 처음 한 번 : 위 함수 고르는 칸에서 setup 을 골라 ▶ 실행
 */

var 판 = 'v0.1';
var SH = { 부서원: '부서원', 종류: '종류', 과업: '과업', 설정: '설정', 기록: '기록', 가져오기: '가져오기' };

var 부서원_머리 = ['이름', '켜기', '순서', '메모'];
var 종류_머리 = ['종류', '색', '켜기', '설명'];
var 과업_머리 = ['번호', '이름', '켜기', '메모'];
var 기록_머리 = ['때', '무엇', '일정 번호', '제목', '내용', '화면'];
var 가져오기_머리 = ['누가', '종류', '시작', '끝', '시간대', '어디', '메모', '과업', '결과(자동)'];

var 설정_줄 = [
  ['캘린더 번호', '', '비우면 setup 이 「구조부 일정」 캘린더를 새로 만들어 채웁니다'],
  ['공유 열쇠', '', '자동 · 부서원에게 주는 주소 끝의 ?m= 값. 바꾸면 모두 새 주소가 필요합니다'],
  ['캘린더 이름', '구조부 일정', 'setup 이 새로 만들 때 쓰는 이름'],
  ['앞뒤 몇 달', 3, '화면이 한 번에 받아 오는 범위 (앞뒤 각각)'],
  ['마지막 결과', '', '자동']
];

var 부서원_예시 = [['전채만', '예', 1, ''], ['난○○', '예', 2, '예시 — 이름을 고치세요'], ['김○○', '예', 3, '예시'], ['이○○', '예', 4, '예시'], ['박○○', '예', 5, '예시'], ['최○○', '예', 6, '예시']];
var 종류_예시 = [
  ['출장', '#1f6fb2', '예', '하루 이상 · 다른 지역'],
  ['휴가', '#a23b72', '예', '연차 · 병가'],
  ['반차', '#7b4bb7', '예', '오전 · 오후 반일'],
  ['외근', '#0f766e', '예', '당일 현장 · 발주처'],
  ['교육', '#455a64', '예', ''],
  ['회의', '#6b7280', '예', '부서 전체'],
  ['그 밖', '#8a929c', '예', '']
];
var 과업_예시 = [['D197', '이설표지판', '예', '예시 — 지워도 됨'], ['D196', '강릉제진', '예', '예시 — 지워도 됨']];

/* ───────────── 처음 설정 ───────────── */

function setup() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  PropertiesService.getScriptProperties().setProperty('SHEET_ID', ss.getId());

  var 부서원 = 시트확보_(ss, SH.부서원, 부서원_머리);
  if (부서원.getLastRow() < 2) 부서원.getRange(2, 1, 부서원_예시.length, 부서원_머리.length).setValues(부서원_예시);
  var 종류 = 시트확보_(ss, SH.종류, 종류_머리);
  if (종류.getLastRow() < 2) 종류.getRange(2, 1, 종류_예시.length, 종류_머리.length).setValues(종류_예시);
  var 과업 = 시트확보_(ss, SH.과업, 과업_머리);
  if (과업.getLastRow() < 2) 과업.getRange(2, 1, 과업_예시.length, 과업_머리.length).setValues(과업_예시);
  var 설정 = 시트확보_(ss, SH.설정, ['이름', '값', '설명']);
  if (설정.getLastRow() < 2) 설정.getRange(2, 1, 설정_줄.length, 3).setValues(설정_줄);
  var 기록 = 시트확보_(ss, SH.기록, 기록_머리);
  기록.getRange('A:A').setNumberFormat('yyyy-mm-dd hh:mm');
  var 가져 = 시트확보_(ss, SH.가져오기, 가져오기_머리);
  가져.getRange('C:C').setNumberFormat('yyyy-mm-dd');
  가져.getRange('D:D').setNumberFormat('yyyy-mm-dd');

  ss.getSheets().forEach(function (s) {
    var n = s.getName();
    if ((n === '시트1' || n === 'Sheet1') && s.getLastRow() === 0 && ss.getSheets().length > 1) ss.deleteSheet(s);
  });

  // 공유 열쇠
  if (!설정값_('공유 열쇠')) 설정쓰기_('공유 열쇠', Utilities.getUuid().replace(/-/g, '').slice(0, 20));

  // 캘린더
  var 만든말 = '있는 캘린더 씀';
  var cal = 캘린더_(true);
  if (!cal) {
    cal = CalendarApp.createCalendar(String(설정값_('캘린더 이름') || '구조부 일정'));
    설정쓰기_('캘린더 번호', cal.getId());
    만든말 = '캘린더 「' + cal.getName() + '」 새로 만듦';
  }
  var 결과 = '처음 설정 끝 — ' + 만든말 + ' · 부서원 ' + 부서원목록_().length + '명 · 종류 ' + 종류목록_().length + '개';
  설정쓰기_('마지막 결과', 결과);
  Logger.log(결과);
  return 결과;
}

/* ───────────── 가져오기 — 시트 「가져오기」 의 줄을 한 번에 캘린더로 (호두 자료 옮길 때) ─────────────
 * 열 : 누가 · 종류 · 시작 · 끝(비우면 하루) · 시간대(오전/오후/비움) · 어디 · 메모 · 과업 · 결과(자동)
 * 결과 칸이 「됨 …」 인 줄은 건너뜀 → 같은 줄을 두 번 올리지 않음. 틀린 줄은 결과 칸에 까닭만 적고 다음 줄로 */
function 가져오기() {
  var s = ss_().getSheetByName(SH.가져오기);
  if (!s) throw new Error('「가져오기」 시트가 없습니다 — setup 을 먼저 실행해 주세요');
  var rows = 값들_(SH.가져오기, 가져오기_머리.length);
  var 됨 = 0, 건너뜀 = 0, 안됨 = 0;
  rows.forEach(function (r, i) {
    var 결과 = String(r[8] || '');
    var 비었나 = r.slice(0, 8).every(function (v) { return String(v).trim() === ''; });
    if (비었나) return;
    if (/^됨/.test(결과)) { 건너뜀++; return; }
    try {
      var v = 입력검사_({ 누가: r[0], 종류: r[1], 시작: 셀날짜_(r[2]), 끝: 셀날짜_(r[3]), 시간대: r[4], 어디: r[5], 메모: r[6], 과업: r[7], 화면: '가져오기' });
      var ev = 캘린더_().createAllDayEvent(제목_(v), v.시작, 다음날_(v.끝));
      태그쓰기_(ev, v);
      var out = 일정꼴_(ev);
      기록_('올림', out, '가져오기');
      s.getRange(i + 2, 9).setValue('됨 ' + 글때_(new Date()) + ' · ' + out.제목);
      됨++;
    } catch (e) {
      s.getRange(i + 2, 9).setValue('안 됨 · ' + e.message);
      안됨++;
    }
  });
  var 글 = '가져오기 끝 — 올림 ' + 됨 + ' · 이미 올린 줄 ' + 건너뜀 + ' · 안 됨 ' + 안됨 + (안됨 ? ' (결과 칸을 보고 고친 뒤 다시 ▶ 실행)' : '');
  설정쓰기_('마지막 결과', 글);
  Logger.log(글);
  return 글;
}
// 시트 칸의 날짜 — 날짜 꼴이면 그대로 · 「2026-11-03」 · 「11/3」 · 「2026.11.3」 글도 받음
function 셀날짜_(v) {
  if (v === '' || v === null || v === undefined) return '';
  if (Object.prototype.toString.call(v) === '[object Date]') return 글날짜_(v);
  var t = String(v).trim();
  var m = t.match(/^(\d{4})[.\-\/]\s*(\d{1,2})[.\-\/]\s*(\d{1,2})/);
  if (m) return m[1] + '-' + 두자리_(Number(m[2])) + '-' + 두자리_(Number(m[3]));
  m = t.match(/^(\d{1,2})[.\/]\s*(\d{1,2})$/);
  if (m) return new Date().getFullYear() + '-' + 두자리_(Number(m[1])) + '-' + 두자리_(Number(m[2]));
  return t;
}

function 시트확보_(ss, name, head) {
  var s = ss.getSheetByName(name) || ss.insertSheet(name);
  if (s.getLastRow() === 0) {
    s.getRange(1, 1, 1, head.length).setValues([head]).setFontWeight('bold');
    s.setFrozenRows(1);
  }
  return s;
}

/* ───────────── 웹 화면 ───────────── */

function doGet(e) {
  var p = (e && e.parameter) || {};
  var 열쇠 = String(설정값_('공유 열쇠') || '');

  // 현황판 등 다른 도구용 — 오늘 요약 JSON
  if (p['오늘'] !== undefined) {
    var body = (열쇠 && p.m === 열쇠) ? 오늘요약_(new Date()) : { 오류: '열쇠가 맞지 않습니다' };
    return ContentService.createTextOutput(JSON.stringify(body)).setMimeType(ContentService.MimeType.JSON);
  }

  if (!열쇠 || p.m !== 열쇠) {
    return HtmlService.createHtmlOutput(
      '<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">' +
      '<body style="font-family:sans-serif;padding:24px;color:#1f2328"><h2>구조부 일정</h2>' +
      '<p>주소에 부서 열쇠가 없거나 맞지 않습니다.</p><p>→ 전무님께 받은 주소(QR)로 다시 열어 주세요.</p>' +
      '<script>try{window.top.postMessage({부서일정:"못받음"},"*")}catch(e){}</script></body>')
      .setTitle('구조부 일정').setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
  }
  var t = HtmlService.createTemplateFromFile('Index');
  t.열쇠 = 열쇠;
  t.판 = 판;
  return t.evaluate()
    .setTitle('구조부 일정')
    .addMetaTag('viewport', 'width=device-width, initial-scale=1, viewport-fit=cover')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}

/* ───────────── 화면이 부르는 함수 ───────────── */

// 화면 자료 한 번에 — 부서원 · 종류 · 과업 · 일정(앞뒤 몇 달) · 오늘 요약
function 화면자료(열쇠, 기준일) {
  열쇠확인_(열쇠);
  var 오늘 = 날짜_(기준일) || 자정_(new Date());
  var 달 = Math.max(1, parseInt(설정값_('앞뒤 몇 달'), 10) || 3);
  var 시작 = new Date(오늘.getFullYear(), 오늘.getMonth() - 달, 1);
  var 끝 = new Date(오늘.getFullYear(), 오늘.getMonth() + 달 + 1, 1);
  return {
    판: 판,
    오늘: 글날짜_(오늘),
    부서원: 부서원목록_(),
    종류: 종류목록_(),
    과업: 과업목록_(),
    일정: 일정목록_(시작, 끝),
    범위: [글날짜_(시작), 글날짜_(끝)],
    요약: 오늘요약_(오늘)
  };
}

// 일정 올리기 — 들어온 것 : {누가, 종류, 시작, 끝, 시간대, 어디, 메모, 과업, 화면}
function 일정올리기(열쇠, 입력) {
  열쇠확인_(열쇠);
  var v = 입력검사_(입력);
  var cal = 캘린더_();
  var ev = cal.createAllDayEvent(제목_(v), v.시작, 다음날_(v.끝));
  태그쓰기_(ev, v);
  var out = 일정꼴_(ev);
  기록_('올림', out, v.화면);
  return out;
}

// 일정 고치기 — 바뀜 : 올리기와 같은 꼴 (바꿀 칸만 있어도 됨)
function 일정고치기(열쇠, id, 바뀜) {
  열쇠확인_(열쇠);
  var ev = 일정찾기_(id);
  var 지금 = 일정꼴_(ev);
  var 합침 = {};
  ['누가', '종류', '시작', '끝', '시간대', '어디', '메모', '과업'].forEach(function (k) { 합침[k] = (바뀜 && 바뀜[k] !== undefined && 바뀜[k] !== null) ? 바뀜[k] : 지금[k]; });
  합침.화면 = 바뀜 && 바뀜.화면;
  var v = 입력검사_(합침);
  ev.setTitle(제목_(v));
  ev.setAllDayDates(v.시작, 다음날_(v.끝));
  태그쓰기_(ev, v);
  var out = 일정꼴_(ev);
  기록_('고침', out, v.화면, '전: ' + 지금.제목 + ' ' + 지금.시작 + '~' + 지금.끝);
  return out;
}

// 일정 지우기 — 지운 내용을 돌려주어 화면이 「되돌리기」 할 수 있게
function 일정지우기(열쇠, id, 화면) {
  열쇠확인_(열쇠);
  var ev = 일정찾기_(id);
  var out = 일정꼴_(ev);
  ev.deleteEvent();
  기록_('지움', out, 화면);
  return out;
}

/* ───────────── 안쪽 ───────────── */

function 열쇠확인_(열쇠) {
  var 참 = String(설정값_('공유 열쇠') || '');
  if (!참 || String(열쇠 || '') !== 참) throw new Error('열쇠가 맞지 않습니다 — 전무님께 받은 주소로 다시 열어 주세요');
}

function 입력검사_(입력) {
  var 입 = 입력 || {};
  var 누가 = String(입.누가 || '').trim();
  var 종류 = String(입.종류 || '').trim();
  if (!누가) throw new Error('「누가」 를 골라 주세요');
  if (!종류) throw new Error('「종류」 를 골라 주세요');
  var 사람들 = 부서원목록_().map(function (p) { return p.이름; });
  if (사람들.indexOf(누가) < 0) throw new Error('「' + 누가 + '」 은 부서원 시트에 없습니다 — 시트 「부서원」 에 먼저 넣어 주세요');
  var 종류들 = 종류목록_().map(function (k) { return k.종류; });
  if (종류들.indexOf(종류) < 0) throw new Error('「' + 종류 + '」 은 종류 시트에 없습니다');
  var 시작 = 날짜_(입.시작);
  if (!시작) throw new Error('「날짜」 를 넣어 주세요 (보기 2026-11-03)');
  var 끝 = 날짜_(입.끝) || 시작;
  if (끝 < 시작) throw new Error('끝 날짜가 시작보다 앞입니다');
  if ((끝 - 시작) / 86400000 > 60) throw new Error('한 번에 60일을 넘는 일정은 올릴 수 없습니다 — 나눠서 올려 주세요');
  var 시간대 = String(입.시간대 || '').trim();
  if (시간대 && 시간대 !== '오전' && 시간대 !== '오후') throw new Error('시간대는 비우거나 「오전」 · 「오후」 만');
  var 과업 = String(입.과업 || '').trim();
  return {
    누가: 누가, 종류: 종류, 시작: 시작, 끝: 끝, 시간대: 시간대,
    어디: String(입.어디 || '').trim().slice(0, 80),
    메모: String(입.메모 || '').trim().slice(0, 200),
    과업: 과업.slice(0, 40),
    화면: String(입.화면 || '').trim().slice(0, 40)
  };
}

function 제목_(v) {
  var t = '[' + v.종류 + '] ' + v.누가;
  if (v.어디) t += ' · ' + v.어디;
  if (v.과업) t += ' · ' + v.과업;
  if (v.시간대) t += ' (' + v.시간대 + ')';
  return t;
}

function 태그쓰기_(ev, v) {
  // 빈 값은 태그를 지움 — 구글이 빈 글 태그를 거절할 수 있어서
  [['종류', v.종류], ['누가', v.누가], ['시간대', v.시간대], ['어디', v.어디], ['메모', v.메모], ['과업', v.과업]].forEach(function (kv) {
    if (kv[1]) ev.setTag(kv[0], kv[1]);
    else if (ev.getTag(kv[0]) !== null) { try { ev.deleteTag(kv[0]); } catch (e) { ev.setTag(kv[0], ''); } }
  });
  if (!ev.getTag('올린')) ev.setTag('올린', (v.화면 || '화면') + ' ' + 글때_(new Date()));
  ev.setDescription(['종류: ' + v.종류, '누가: ' + v.누가, v.어디 ? '어디: ' + v.어디 : '', v.메모 ? '메모: ' + v.메모 : '', v.과업 ? '과업: ' + v.과업 : '', v.시간대 ? '시간대: ' + v.시간대 : '', '— 구조부 일정 화면에서 올림'].filter(Boolean).join('\n'));
}

function 일정꼴_(ev) {
  var 시작 = ev.isAllDayEvent() ? ev.getAllDayStartDate() : ev.getStartTime();
  var 끝 = ev.isAllDayEvent() ? new Date(ev.getAllDayEndDate().getTime() - 86400000) : ev.getEndTime();
  var 제목 = ev.getTitle();
  var 종류 = ev.getTag('종류'), 누가 = ev.getTag('누가');
  // 화면 밖(구글 캘린더 앱)에서 바로 넣은 일정도 보이게 — 제목 「[출장] 홍길동 · 대전」 꼴이면 읽음
  if (!종류 || !누가) {
    var m = 제목.match(/^\[([^\]]+)\]\s*([^·(]+)/);
    종류 = 종류 || (m ? m[1].trim() : '그 밖');
    누가 = 누가 || (m ? m[2].trim() : (제목.split(' ')[0] || '?'));
  }
  return {
    id: ev.getId(), 제목: 제목, 종류: 종류, 누가: 누가,
    시작: 글날짜_(시작), 끝: 글날짜_(끝),
    시간대: ev.getTag('시간대') || '', 어디: ev.getTag('어디') || '', 메모: ev.getTag('메모') || '',
    과업: ev.getTag('과업') || '', 올린: ev.getTag('올린') || '', 화면밖: !ev.getTag('종류')
  };
}

function 일정목록_(시작, 끝) {
  var cal = 캘린더_();
  return cal.getEvents(시작, 끝).map(일정꼴_).sort(function (a, b) { return a.시작 < b.시작 ? -1 : a.시작 > b.시작 ? 1 : (a.누가 < b.누가 ? -1 : 1); });
}

function 일정찾기_(id) {
  var ev = 캘린더_().getEventById(String(id || ''));
  if (!ev) throw new Error('그 일정을 찾지 못했습니다 — 이미 지워졌을 수 있습니다. 화면을 새로 고쳐 주세요');
  return ev;
}

function 오늘요약_(날) {
  var 오늘 = 자정_(날);
  var 글 = 글날짜_(오늘);
  var 목록 = 일정목록_(오늘, 다음날_(오늘)).filter(function (e) { return e.시작 <= 글 && 글 <= e.끝; });
  var 사람 = 부서원목록_().map(function (p) { return p.이름; });
  var 밖이름 = {};
  목록.forEach(function (e) { 밖이름[e.누가] = true; });
  return {
    날짜: 글, 전체: 사람.length,
    밖: 목록, 밖수: Object.keys(밖이름).length,
    자리: 사람.filter(function (n) { return !밖이름[n]; })
  };
}

function 기록_(무엇, e, 화면, 더) {
  var s = ss_().getSheetByName(SH.기록);
  if (!s) return;
  var 내용 = e.시작 + (e.끝 !== e.시작 ? '~' + e.끝 : '') + (e.시간대 ? ' ' + e.시간대 : '') + (e.메모 ? ' · ' + e.메모 : '') + (더 ? ' · ' + 더 : '');
  s.getRange(s.getLastRow() + 1, 1, 1, 기록_머리.length).setValues([[new Date(), 무엇, e.id, e.제목, 내용, 화면 || '']]);
}

/* ─── 시트 읽기 ─── */

function 부서원목록_() {
  return 값들_(SH.부서원, 부서원_머리.length)
    .filter(function (r) { return String(r[0]).trim() && String(r[1]).trim() !== '아니오'; })
    .map(function (r, i) { var n = Number(r[2]); return { 이름: String(r[0]).trim(), 순서: (String(r[2]).trim() === '' || isNaN(n)) ? 100 + i : n }; })
    .sort(function (a, b) { return a.순서 - b.순서; });
}
function 종류목록_() {
  return 값들_(SH.종류, 종류_머리.length)
    .filter(function (r) { return String(r[0]).trim() && String(r[2]).trim() !== '아니오'; })
    .map(function (r) { return { 종류: String(r[0]).trim(), 색: String(r[1]).trim() || '#8a929c', 설명: String(r[3] || '') }; });
}
function 과업목록_() {
  return 값들_(SH.과업, 과업_머리.length)
    .filter(function (r) { return String(r[0]).trim() && String(r[2]).trim() !== '아니오'; })
    .map(function (r) { return { 번호: String(r[0]).trim(), 이름: String(r[1] || '').trim() }; });
}
function 값들_(name, width) {
  var s = ss_().getSheetByName(name);
  if (!s) throw new Error('「' + name + '」 시트가 없습니다 — setup 을 먼저 실행해 주세요');
  var n = s.getLastRow() - 1;
  return n > 0 ? s.getRange(2, 1, n, width).getValues() : [];
}
function 설정값_(이름) {
  var s = ss_().getSheetByName(SH.설정);
  if (!s) return '';
  var rows = 값들_(SH.설정, 2);
  for (var i = 0; i < rows.length; i++) if (String(rows[i][0]).trim() === 이름) return rows[i][1];
  return '';
}
function 설정쓰기_(이름, 값) {
  var s = ss_().getSheetByName(SH.설정);
  var rows = 값들_(SH.설정, 2);
  for (var i = 0; i < rows.length; i++) if (String(rows[i][0]).trim() === 이름) { s.getRange(i + 2, 2).setValue(값); return; }
  s.getRange(s.getLastRow() + 1, 1, 1, 2).setValues([[이름, 값]]);
}
function ss_() {
  var id = PropertiesService.getScriptProperties().getProperty('SHEET_ID');
  return id ? SpreadsheetApp.openById(id) : SpreadsheetApp.getActiveSpreadsheet();
}
function 캘린더_(없어도됨) {
  var id = String(설정값_('캘린더 번호') || '').trim();
  var cal = id ? CalendarApp.getCalendarById(id) : null;
  if (!cal && !없어도됨) throw new Error('캘린더를 찾지 못했습니다 — setup 을 다시 실행하거나 시트 「설정」 의 캘린더 번호를 확인해 주세요');
  return cal;
}

/* ─── 날짜 ─── */

function 자정_(d) { return new Date(d.getFullYear(), d.getMonth(), d.getDate()); }
function 다음날_(d) { return new Date(d.getFullYear(), d.getMonth(), d.getDate() + 1); }
function 날짜_(s) {
  if (!s) return null;
  if (Object.prototype.toString.call(s) === '[object Date]') return 자정_(s);
  var m = String(s).match(/^(\d{4})-(\d{1,2})-(\d{1,2})/);
  if (!m) return null;
  var d = new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3]));
  return isNaN(d.getTime()) ? null : d;
}
function 두자리_(n) { return (n < 10 ? '0' : '') + n; }
function 글날짜_(d) { return d.getFullYear() + '-' + 두자리_(d.getMonth() + 1) + '-' + 두자리_(d.getDate()); }
function 글때_(d) { return 글날짜_(d) + ' ' + 두자리_(d.getHours()) + ':' + 두자리_(d.getMinutes()); }
