// 시험용 가짜 구글 — 시트 · 유튜브 API · 트리거 · RSS 를 흉내 낸다
// 실제 구글에서는 쓰이지 않는다.

function colToNum(s) { let n = 0; for (const ch of s) n = n * 26 + (ch.charCodeAt(0) - 64); return n; }

class Range {
  constructor(sheet, r, c, nr, nc) { Object.assign(this, { sheet, r, c, nr, nc }); }
  getValues() {
    const out = [];
    for (let i = 0; i < this.nr; i++) {
      const row = this.sheet.data[this.r - 1 + i] || [];
      const o = [];
      for (let j = 0; j < this.nc; j++) { const v = row[this.c - 1 + j]; o.push(v === undefined ? '' : v); }
      out.push(o);
    }
    return out;
  }
  setValues(vals) {
    if (vals.length !== this.nr || vals.some(r => r.length !== this.nc)) throw new Error('setValues 크기 다름 ' + vals.length + 'x' + (vals[0] || []).length + ' vs ' + this.nr + 'x' + this.nc);
    vals.forEach((row, i) => row.forEach((v, j) => this.sheet.put(this.r + i, this.c + j, v)));
    return this;
  }
  setValue(v) { this.sheet.put(this.r, this.c, v); return this; }
  clearContent() { for (let i = 0; i < this.nr; i++) for (let j = 0; j < this.nc; j++) this.sheet.put(this.r + i, this.c + j, ''); return this; }
  setNumberFormat() { return this; }
  setFontWeight() { return this; }
}

class Sheet {
  constructor(name) { this.name = name; this.data = []; }
  getName() { return this.name; }
  put(r, c, v) {
    if (typeof v === 'string' && v !== '' && !isNaN(v) && v.trim() !== '') v = Number(v); // 시트처럼 숫자로 바뀜
    while (this.data.length < r) this.data.push([]);
    this.data[r - 1][c - 1] = v;
  }
  getLastRow() {
    for (let i = this.data.length; i > 0; i--) if ((this.data[i - 1] || []).some(v => v !== '' && v !== undefined)) return i;
    return 0;
  }
  getRange(a, b, c, d) {
    if (typeof a === 'string') { const m = a.match(/^([A-Z]+):([A-Z]+)$/); const col = colToNum(m[1]); return new Range(this, 1, col, 1000, 1); }
    return new Range(this, a, b, c || 1, d || 1);
  }
  setFrozenRows() {}
}

class Spreadsheet {
  constructor() { this.sheets = [new Sheet('시트1')]; }
  getId() { return 'SHEET123'; }
  getSheetByName(n) { return this.sheets.find(s => s.name === n) || null; }
  insertSheet(n) { const s = new Sheet(n); this.sheets.push(s); return s; }
  getSheets() { return this.sheets.slice(); }
  deleteSheet(s) { this.sheets = this.sheets.filter(x => x !== s); }
}

// ── 가짜 유튜브 ──
const DAY = 86400000;
function makeYouTube(now) {
  const units = { n: 0 };
  const channels = {
    // id: {handle, title, country, long:[...], shorts:[...], noUULF}
  };
  const videos = {}; // id -> {dur, live}
  let vc = 0;
  function addChannel(handle, title, country, opts = {}) {
    const id = 'UC' + (handle.replace(/[^\w]/g, 'x') + '0000000000000000000000').slice(0, 22);
    const ch = { id, handle, title, country, items: [], noUULF: !!opts.noUULF };
    channels[id] = ch;
    return ch;
  }
  function addVideo(ch, { daysAgo = 1, dur = 600, live = 'none', title } = {}) {
    const id = 'v' + String(++vc).padStart(10, '0');
    const item = { id, title: title || ch.title + ' 영상 ' + vc, published: new Date(now - daysAgo * DAY), dur, live };
    ch.items.unshift(item);
    ch.items.sort((a, b) => b.published - a.published);
    videos[id] = item;
    return item;
  }
  const err404 = () => { const e = new Error('API call to youtube.playlistItems.list failed with error: The playlist identified with the request\'s playlistId parameter cannot be found.'); return e; };
  const YouTube = {
    Channels: {
      list(part, opt) {
        units.n += 1;
        let ch;
        if (opt.id) ch = channels[opt.id];
        else if (opt.forHandle) ch = Object.values(channels).find(c => '@' + c.handle.toLowerCase() === opt.forHandle.toLowerCase());
        else if (opt.forUsername) ch = Object.values(channels).find(c => c.handle === opt.forUsername);
        return { items: ch ? [{ id: ch.id, snippet: { title: ch.title, country: ch.country } }] : [] };
      }
    },
    PlaylistItems: {
      list(part, opt) {
        units.n += 1;
        const pid = opt.playlistId;
        const prefix = pid.startsWith('UULF') ? 'UULF' : 'UU';
        const ch = channels['UC' + pid.slice(prefix.length)];
        if (!ch || (prefix === 'UULF' && ch.noUULF)) throw err404();
        let items = ch.items;
        if (prefix === 'UULF') items = items.filter(i => i.dur > 180 || i.live !== 'none');
        return {
          items: items.slice(0, opt.maxResults).map(i => ({
            snippet: { title: i.title, publishedAt: i.published.toISOString() },
            contentDetails: { videoId: i.id, videoPublishedAt: i.published.toISOString() }
          }))
        };
      }
    },
    Videos: {
      list(part, opt) {
        units.n += 1;
        const ids = opt.id.split(',');
        if (ids.length > 50) throw new Error('50개 넘음');
        return {
          items: ids.filter(id => videos[id]).map(id => {
            const v = videos[id]; const m = Math.floor(v.dur / 60), s = v.dur % 60, h = Math.floor(m / 60);
            return { id, contentDetails: { duration: 'PT' + (h ? h + 'H' : '') + (m % 60 ? (m % 60) + 'M' : '') + (s ? s + 'S' : '') }, snippet: { liveBroadcastContent: v.live } };
          })
        };
      }
    },
    Search: {
      list(part, opt) {
        units.n += 100;
        units.lastSearch = opt;
        const all = Object.values(channels).flatMap(c => c.items.map(i => ({ c, i })));
        return {
          items: all.slice(0, opt.maxResults).map(({ c, i }) => ({
            id: { videoId: i.id },
            snippet: { title: i.title.replace(/&/g, '&amp;'), channelTitle: c.title, channelId: c.id, publishedAt: i.published.toISOString() }
          }))
        };
      }
    }
  };
  return { YouTube, units, channels, addChannel, addVideo };
}

function makeGlobals(now) {
  const ss = new Spreadsheet();
  const props = {};
  const triggers = [];
  const yt = makeYouTube(now);
  const rss = {}; // channelId -> xml
  const g = {
    SpreadsheetApp: { getActiveSpreadsheet: () => ss, openById: () => ss },
    PropertiesService: { getScriptProperties: () => ({ setProperty: (k, v) => { props[k] = v; }, getProperty: k => props[k] }) },
    LockService: { getScriptLock: () => ({ tryLock: () => true, waitLock: () => {}, releaseLock: () => {} }) },
    ScriptApp: {
      getProjectTriggers: () => triggers.slice(),
      deleteTrigger: t => { triggers.splice(triggers.indexOf(t), 1); },
      newTrigger: fn => {
        const t = { fn, getHandlerFunction: () => fn };
        const chain = { timeBased: () => chain, everyHours: h => { t.hours = h; return chain; }, create: () => { triggers.push(t); return t; } };
        return chain;
      }
    },
    UrlFetchApp: {
      fetch: url => {
        const id = (url.match(/channel_id=([\w-]+)/) || [])[1];
        const body = rss[id];
        return { getResponseCode: () => (body ? 200 : 404), getContentText: () => body || '' };
      }
    },
    HtmlService: {
      createHtmlOutputFromFile: f => { const o = { file: f, setTitle: t => { o.title = t; return o; }, addMetaTag: () => o }; return o; }
    },
    Logger: { log: () => {} },
    YouTube: yt.YouTube
  };
  return { g, ss, props, triggers, yt, rss };
}

module.exports = { makeGlobals, DAY };
