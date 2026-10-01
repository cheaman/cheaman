/**
 * 나만의 유튜브 창 — 구글 앱스 스크립트
 *
 * 시트 셋
 *   채널목록 : 내가 고치는 곳 (카테고리 · 채널 주소 …)
 *   영상     : 스크립트가 채우는 곳 (손대지 않음)
 *   설정     : 쇼츠 빼기 · 채널마다 최근 몇 개 · 보관 일수
 *
 * 처음 한 번 : 위 함수 고르는 칸에서 setup 을 골라 ▶ 실행
 */

var SHEET_CH = '채널목록';
var SHEET_V = '영상';
var SHEET_SET = '설정';

var CH_HEAD = ['카테고리', '채널 이름', '채널 주소', '나라·언어', '켜기', '메모', '넣은 날', '채널 번호(자동)', '상태(자동)'];
var CH = { cat: 0, name: 1, url: 2, country: 3, on: 4, memo: 5, added: 6, id: 7, status: 8 };

var V_HEAD = ['영상 번호', '제목', '채널 번호', '채널 이름', '올린 때', '길이(초)', '상태', '모은 때'];
var V = { id: 0, title: 1, chId: 2, chName: 3, published: 4, dur: 5, state: 6, collected: 7 };

var STATES = ['새 영상', '봤음', '나중에', '숨김'];
var SHORTS_STATE = '쇼츠';
var SHORTS_MAX_SEC = 60;
var FEED_MAX = 400;

var SET_ROWS = [
  ['쇼츠 빼기', '예', '예 / 아니오'],
  ['채널마다 최근 몇 개', 10, '한 번에 확인하는 채널별 최근 영상 수 (1~50)'],
  ['보관 일수', 90, '이보다 오래된 영상은 정리합니다. 「나중에」로 둔 것은 남깁니다'],
  ['마지막으로 모은 때', '', '자동'],
  ['마지막 결과', '', '자동']
];

// 처음 넣어 두는 예시 채널 — 지워도 됩니다
var SAMPLE = [
  ['AI', 'Two Minute Papers', 'https://www.youtube.com/@TwoMinutePapers', '', '예', '예시 — 지워도 됨'],
  ['AI', 'AI Explained', 'https://www.youtube.com/@aiexplained-official', '', '예', '예시 — 지워도 됨'],
  ['AI', '3Blue1Brown', 'https://www.youtube.com/@3blue1brown', '', '예', '예시 — 지워도 됨'],
  ['AI', '조코딩', 'https://www.youtube.com/@jocoding', '', '예', '예시 — 지워도 됨'],
  ['여행', 'Kara and Nate', 'https://www.youtube.com/@karaandnate', '', '예', '예시 — 지워도 됨'],
  ['여행', 'Lost LeBlanc', 'https://www.youtube.com/@LostLeBlanc', '', '예', '예시 — 지워도 됨'],
  ['여행', '곽튜브', 'https://www.youtube.com/@kwaktube', '', '예', '예시 — 지워도 됨'],
  ['음식/레시피', 'Mark Wiens', 'https://www.youtube.com/@MarkWiens', '', '예', '예시 — 지워도 됨'],
  ['음식/레시피', 'Joshua Weissman', 'https://www.youtube.com/@JoshuaWeissman', '', '예', '예시 — 지워도 됨'],
  ['음식/레시피', 'Maangchi', 'https://www.youtube.com/@Maangchi', '', '예', '예시 — 지워도 됨'],
  ['음식/레시피', '백종원', 'https://www.youtube.com/@paikscuisine', '', '예', '예시 — 지워도 됨']
];

/* ───────────── 처음 설정 ───────────── */

function setup() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  PropertiesService.getScriptProperties().setProperty('SHEET_ID', ss.getId());

  var ch = ensureSheet_(ss, SHEET_CH, CH_HEAD);
  if (ch.getLastRow() < 2) {
    var today = new Date();
    var rows = SAMPLE.map(function (r) { return r.concat([today, '', '']); });
    ch.getRange(2, 1, rows.length, CH_HEAD.length).setValues(rows);
  }
  var v = ensureSheet_(ss, SHEET_V, V_HEAD);
  v.getRange('E:E').setNumberFormat('yyyy-mm-dd hh:mm');
  v.getRange('H:H').setNumberFormat('yyyy-mm-dd hh:mm');
  var st = ensureSheet_(ss, SHEET_SET, ['이름', '값', '설명']);
  if (st.getLastRow() < 2) st.getRange(2, 1, SET_ROWS.length, 3).setValues(SET_ROWS);

  // 빈 기본 시트(시트1 · Sheet1) 정리
  ss.getSheets().forEach(function (s) {
    var n = s.getName();
    if ((n === '시트1' || n === 'Sheet1') && s.getLastRow() === 0 && ss.getSheets().length > 1) ss.deleteSheet(s);
  });

  installTrigger_();
  var result = collect();
  Logger.log('처음 설정 끝 — ' + result);
  return result;
}

function installTrigger_() {
  ScriptApp.getProjectTriggers().forEach(function (t) {
    if (t.getHandlerFunction() === 'collect') ScriptApp.deleteTrigger(t);
  });
  ScriptApp.newTrigger('collect').timeBased().everyHours(1).create();
}

function ensureSheet_(ss, name, head) {
  var s = ss.getSheetByName(name) || ss.insertSheet(name);
  if (s.getLastRow() === 0) {
    s.getRange(1, 1, 1, head.length).setValues([head]).setFontWeight('bold');
    s.setFrozenRows(1);
  }
  return s;
}

/* ───────────── 영상 모으기 (매시간) ───────────── */

function collect() {
  return collect_(null);
}

function collect_(onlyChannelId) {
  var lock = LockService.getScriptLock();
  if (!lock.tryLock(20000)) return '다른 모으기가 도는 중이라 건너뜀';
  try {
    var set = settings_();
    var noShorts = String(set['쇼츠 빼기']).trim() !== '아니오';
    var perCh = Math.min(50, Math.max(1, parseInt(set['채널마다 최근 몇 개'], 10) || 10));
    var keepDays = Math.max(1, parseInt(set['보관 일수'], 10) || 90);
    var cutoff = new Date(Date.now() - keepDays * 86400000);

    var chSheet = sheet_(SHEET_CH);
    var chRows = values_(chSheet, CH_HEAD.length);
    var vSheet = sheet_(SHEET_V);
    var known = {};
    values_(vSheet, V_HEAD.length).forEach(function (r) { known[r[V.id]] = true; });

    var fresh = [];
    var ok = 0, failed = 0;
    chRows.forEach(function (r, i) {
      if (!String(r[CH.url]).trim() && !String(r[CH.id]).trim()) return;
      if (String(r[CH.on]).trim() === '아니오') return;
      if (onlyChannelId && r[CH.id] !== onlyChannelId) return;
      var rowNo = i + 2;
      try {
        if (!r[CH.id]) {
          var info = resolveChannel_(r[CH.url]);
          r[CH.id] = info.id;
          chSheet.getRange(rowNo, CH.id + 1).setValue(info.id);
          if (!String(r[CH.name]).trim()) { r[CH.name] = info.name; chSheet.getRange(rowNo, CH.name + 1).setValue(info.name); }
          if (!String(r[CH.country]).trim() && info.country) chSheet.getRange(rowNo, CH.country + 1).setValue(info.country);
        }
        latestUploads_(r[CH.id], perCh, noShorts).forEach(function (it) {
          if (known[it.id] || it.published < cutoff) return;
          known[it.id] = true;
          it.chId = r[CH.id];
          it.chName = r[CH.name];
          fresh.push(it);
        });
        if (r[CH.status] !== '정상') chSheet.getRange(rowNo, CH.status + 1).setValue('정상');
        ok++;
      } catch (e) {
        failed++;
        chSheet.getRange(rowNo, CH.status + 1).setValue('못 받음: ' + shortMsg_(e));
      }
    });

    var details = videoDetails_(fresh.map(function (it) { return it.id; }));
    var now = new Date();
    var out = [];
    fresh.forEach(function (it) {
      var d = details[it.id] || {};
      if (d.live === 'upcoming' || d.live === 'live') return; // 예정·생방송은 끝난 뒤 다음 시간에 다시 봄
      var dur = d.dur === undefined ? '' : d.dur;
      var state = (noShorts && dur !== '' && dur <= SHORTS_MAX_SEC) ? SHORTS_STATE : '새 영상';
      out.push([it.id, it.title, it.chId, it.chName, it.published, dur, state, now]);
    });
    if (out.length) vSheet.getRange(vSheet.getLastRow() + 1, 1, out.length, V_HEAD.length).setValues(out);
    var added = out.filter(function (r) { return r[V.state] !== SHORTS_STATE; }).length;

    if (!onlyChannelId) prune_(vSheet, cutoff);

    var msg = '채널 ' + ok + '개 확인 · 새 영상 ' + added + '개' +
      (failed ? ' · 못 받은 채널 ' + failed + '개 (채널목록 「상태」 칸 보기)' : '') +
      (hasApi_() ? '' : ' · 유튜브 API 서비스가 꺼져 있어 RSS로 받음');
    if (!onlyChannelId) {
      setSetting_('마지막으로 모은 때', now);
      setSetting_('마지막 결과', msg);
    }
    return msg;
  } finally {
    lock.releaseLock();
  }
}

// 채널의 최근 영상 — 쇼츠를 빼면 「긴 영상만」 목록(UULF)부터 시도
function latestUploads_(chId, n, noShorts) {
  if (!hasApi_()) return rssUploads_(chId, n);
  var tail = String(chId).slice(2);
  var lists = noShorts ? ['UULF' + tail, 'UU' + tail] : ['UU' + tail];
  var lastErr;
  for (var i = 0; i < lists.length; i++) {
    try {
      var res = YouTube.PlaylistItems.list('snippet,contentDetails', { playlistId: lists[i], maxResults: n });
      return (res.items || [])
        .filter(function (it) { return it.contentDetails && it.contentDetails.videoPublishedAt; }) // 비공개·삭제 영상 거름
        .map(function (it) {
          return { id: it.contentDetails.videoId, title: it.snippet.title, published: new Date(it.contentDetails.videoPublishedAt) };
        });
    } catch (e) { lastErr = e; }
  }
  try { return rssUploads_(chId, n); } catch (e2) { throw lastErr; }
}

// 유튜브 API가 막힐 때 쓰는 보조 길
function rssUploads_(chId, n) {
  var res = UrlFetchApp.fetch('https://www.youtube.com/feeds/videos.xml?channel_id=' + chId, { muteHttpExceptions: true });
  if (res.getResponseCode() !== 200) throw new Error('RSS 응답 ' + res.getResponseCode());
  var xml = res.getContentText();
  var out = [];
  var entries = xml.split('<entry>').slice(1);
  for (var i = 0; i < entries.length && out.length < n; i++) {
    var e = entries[i];
    var id = tag_(e, 'yt:videoId'), title = tag_(e, 'title'), pub = tag_(e, 'published');
    if (id) out.push({ id: id, title: unescapeXml_(title), published: new Date(pub) });
  }
  return out;
}

function tag_(s, name) {
  var m = s.match(new RegExp('<' + name + '>([\\s\\S]*?)</' + name + '>'));
  return m ? m[1] : '';
}

function unescapeXml_(s) {
  return s.replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/&amp;/g, '&');
}

// 영상 길이 · 생방송 여부 (50개씩 묶어 한 번에)
function videoDetails_(ids) {
  var out = {};
  if (!hasApi_() || !ids.length) return out;
  for (var i = 0; i < ids.length; i += 50) {
    var chunk = ids.slice(i, i + 50);
    try {
      var res = YouTube.Videos.list('contentDetails,snippet', { id: chunk.join(','), maxResults: 50 });
      (res.items || []).forEach(function (v) {
        out[v.id] = { dur: parseDuration_(v.contentDetails.duration), live: v.snippet.liveBroadcastContent };
      });
    } catch (e) { /* 길이를 못 받아도 영상은 넣는다 */ }
  }
  return out;
}

function parseDuration_(iso) {
  var m = String(iso || '').match(/P(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?/);
  if (!m) return '';
  return (+(m[1] || 0)) * 86400 + (+(m[2] || 0)) * 3600 + (+(m[3] || 0)) * 60 + (+(m[4] || 0));
}

// 오래된 영상 정리 — 「나중에」는 남김
function prune_(vSheet, cutoff) {
  var rows = values_(vSheet, V_HEAD.length);
  var keep = rows.filter(function (r) {
    return r[V.state] === '나중에' || !(r[V.published] instanceof Date) || r[V.published] >= cutoff;
  });
  if (keep.length === rows.length) return;
  vSheet.getRange(2, 1, rows.length, V_HEAD.length).clearContent();
  if (keep.length) vSheet.getRange(2, 1, keep.length, V_HEAD.length).setValues(keep);
}

/* ───────────── 채널 주소 → 채널 번호 ───────────── */

function parseChannelInput_(input) {
  var s = String(input || '').trim();
  var m;
  if ((m = s.match(/(UC[\w-]{22})/))) return { id: m[1] };
  if ((m = s.match(/@([^\/?#\s]+)/))) return { handle: decodeURIComponent(m[1]) };
  if ((m = s.match(/youtube\.com\/user\/([^\/?#\s]+)/))) return { user: m[1] };
  if ((m = s.match(/youtube\.com\/c\/([^\/?#\s]+)/))) return { handle: decodeURIComponent(m[1]) };
  if (/^[\w.\-가-힣]+$/.test(s)) return { handle: s };
  return {};
}

function resolveChannel_(input) {
  var p = parseChannelInput_(input);
  if (!p.id && !p.handle && !p.user) throw new Error('채널 주소를 알아볼 수 없음 — youtube.com/@이름 꼴로 넣어 주세요');
  if (!hasApi_()) {
    if (p.id) return { id: p.id, name: '', country: '' };
    throw new Error('유튜브 API 서비스가 꺼져 있어 @이름 주소를 못 찾음 — 설치 안내 3번을 봐 주세요');
  }
  var opt = p.id ? { id: p.id } : p.handle ? { forHandle: '@' + p.handle } : { forUsername: p.user };
  var res = YouTube.Channels.list('snippet', opt);
  var it = res.items && res.items[0];
  if (!it) throw new Error('유튜브에서 이 채널을 찾지 못함 — 주소를 다시 확인해 주세요');
  return { id: it.id, name: it.snippet.title, country: it.snippet.country || '' };
}

/* ───────────── 웹 화면 ───────────── */

function doGet() {
  return HtmlService.createHtmlOutputFromFile('Index')
    .setTitle('나만의 유튜브')
    .addMetaTag('viewport', 'width=device-width, initial-scale=1');
}

// 화면이 처음 열릴 때 부르는 것
function getFeed() {
  var chRows = values_(sheet_(SHEET_CH), CH_HEAD.length);
  var chans = {}, cats = [];
  chRows.forEach(function (r) {
    var cat = String(r[CH.cat]).trim();
    if (!cat || !r[CH.id] || String(r[CH.on]).trim() === '아니오') return;
    if (cats.indexOf(cat) < 0) cats.push(cat);
    chans[r[CH.id]] = { cat: cat, name: String(r[CH.name]), cc: String(r[CH.country]) };
  });

  var vids = values_(sheet_(SHEET_V), V_HEAD.length)
    .filter(function (r) { return chans[r[V.chId]] && r[V.state] !== '숨김' && r[V.state] !== SHORTS_STATE; })
    .map(function (r) {
      var c = chans[r[V.chId]];
      return {
        id: String(r[V.id]), t: String(r[V.title]), ch: c.name || String(r[V.chName]), cat: c.cat, cc: c.cc,
        pub: r[V.published] instanceof Date ? r[V.published].getTime() : 0,
        dur: r[V.dur] === '' ? null : Number(r[V.dur]), st: String(r[V.state]) || '새 영상'
      };
    })
    .sort(function (a, b) { return b.pub - a.pub; })
    .slice(0, FEED_MAX);

  var set = settings_();
  var last = set['마지막으로 모은 때'];
  return {
    cats: cats,
    videos: vids,
    channelIds: Object.keys(chans),
    last: last instanceof Date ? last.getTime() : 0,
    lastResult: String(set['마지막 결과'] || ''),
    canSearch: hasApi_()
  };
}

// 봤음 · 나중에 · 숨김 · 새 영상
function setState(videoId, state) {
  if (STATES.indexOf(state) < 0) throw new Error('알 수 없는 상태: ' + state);
  var lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    var s = sheet_(SHEET_V);
    var rows = values_(s, V_HEAD.length);
    for (var i = 0; i < rows.length; i++) {
      if (String(rows[i][V.id]) === String(videoId)) {
        s.getRange(i + 2, V.state + 1).setValue(state);
        return state;
      }
    }
    throw new Error('영상을 찾지 못함');
  } finally {
    lock.releaseLock();
  }
}

// 화면의 「＋ 채널」 · 찾기의 「이 채널 담기」
function addChannel(input, category) {
  category = String(category || '').trim();
  if (!category) throw new Error('카테고리를 골라 주세요');
  var info = resolveChannel_(input);
  var s = sheet_(SHEET_CH);
  var rows = values_(s, CH_HEAD.length);
  for (var i = 0; i < rows.length; i++) {
    if (rows[i][CH.id] === info.id) {
      throw new Error('이미 담은 채널입니다 (' + (rows[i][CH.name] || info.name) + ' · ' + rows[i][CH.cat] + ')');
    }
  }
  var url = /^https?:/.test(String(input)) ? String(input).trim() : 'https://www.youtube.com/channel/' + info.id;
  s.getRange(s.getLastRow() + 1, 1, 1, CH_HEAD.length).setValues([[
    category, info.name, url, info.country, '예', '화면에서 담음', new Date(), info.id, '정상'
  ]]);
  var msg = collect_(info.id);
  return { name: info.name, message: msg };
}

function collectNow() {
  return collect();
}

// 찾기 탭 — 내 시청 기록과 상관없는 검색
function search(q, lang, region) {
  if (!hasApi_()) throw new Error('찾기를 쓰려면 유튜브 API 서비스를 켜야 합니다 (설치 안내 3번)');
  q = String(q || '').trim();
  if (!q) throw new Error('찾을 낱말을 넣어 주세요');
  var opt = { q: q, type: 'video', maxResults: 15, safeSearch: 'moderate' };
  if (lang) opt.relevanceLanguage = lang;
  if (region) opt.regionCode = region;
  var res = YouTube.Search.list('snippet', opt);
  return (res.items || []).map(function (it) {
    return {
      id: it.id.videoId, t: it.snippet.title, ch: it.snippet.channelTitle, chId: it.snippet.channelId,
      pub: new Date(it.snippet.publishedAt).getTime()
    };
  });
}

/* ───────────── 작은 도우미 ───────────── */

function hasApi_() {
  return typeof YouTube !== 'undefined';
}

function ss_() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  if (ss) return ss;
  return SpreadsheetApp.openById(PropertiesService.getScriptProperties().getProperty('SHEET_ID'));
}

function sheet_(name) {
  var s = ss_().getSheetByName(name);
  if (!s) throw new Error('「' + name + '」 시트가 없습니다 — setup 을 먼저 실행해 주세요');
  return s;
}

function values_(s, width) {
  var n = s.getLastRow() - 1;
  return n > 0 ? s.getRange(2, 1, n, width).getValues() : [];
}

function settings_() {
  var out = {};
  values_(sheet_(SHEET_SET), 2).forEach(function (r) { out[String(r[0]).trim()] = r[1]; });
  return out;
}

function setSetting_(name, value) {
  var s = sheet_(SHEET_SET);
  var rows = values_(s, 1);
  for (var i = 0; i < rows.length; i++) {
    if (String(rows[i][0]).trim() === name) { s.getRange(i + 2, 2).setValue(value); return; }
  }
  s.getRange(s.getLastRow() + 1, 1, 1, 3).setValues([[name, value, '자동']]);
}

function shortMsg_(e) {
  var m = String((e && e.message) || e);
  if (/quota/i.test(m)) return '오늘 유튜브 한도를 다 씀 — 내일 저절로 다시 받음';
  return m.length > 120 ? m.slice(0, 120) + '…' : m;
}
