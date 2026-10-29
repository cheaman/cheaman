// 시험용 가짜 구글 — 시트 · 캘린더 · 속성 · HtmlService 를 흉내 낸다. 실제 구글에서는 쓰이지 않는다.
// (29번 나만의 유튜브 fake-google.js 의 시트 부분을 가져오고 CalendarApp 을 더함)

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
    if (typeof v === 'string' && v !== '' && !isNaN(v) && v.trim() !== '') v = Number(v);
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

// ── 가짜 캘린더 ──
const DAY = 86400000;
let evSeq = 0;
class CalendarEvent {
  constructor(cal, title, start, endExclusive, allDay) {
    this.cal = cal; this.id = 'ev' + (++evSeq) + '@google.com'; this.title = title;
    this.start = new Date(start); this.end = new Date(endExclusive); this.allDay = allDay; this.tags = {}; this.desc = ''; this.deleted = false;
  }
  getId() { return this.id; }
  getTitle() { return this.title; } setTitle(t) { this.title = t; return this; }
  isAllDayEvent() { return this.allDay; }
  getAllDayStartDate() { return new Date(this.start); } getAllDayEndDate() { return new Date(this.end); }
  getStartTime() { return new Date(this.start); } getEndTime() { return new Date(this.end); }
  setAllDayDates(s, e) { this.start = new Date(s); this.end = new Date(e); this.allDay = true; return this; }
  getTag(k) { return this.tags[k] === undefined ? null : this.tags[k]; }
  setTag(k, v) { if (String(v) === '') throw new Error('Invalid argument: value'); this.tags[k] = String(v); return this; }
  deleteTag(k) { delete this.tags[k]; return this; }
  setDescription(d) { this.desc = d; return this; } getDescription() { return this.desc; }
  deleteEvent() { this.deleted = true; this.cal.events = this.cal.events.filter(e => e !== this); }
}
class Calendar {
  constructor(name, id) { this.name = name; this.id = id; this.events = []; }
  getId() { return this.id; } getName() { return this.name; }
  createAllDayEvent(title, start, endExclusive) {
    if (Object.prototype.toString.call(start) !== '[object Date]' || isNaN(start)) throw new Error('createAllDayEvent: 날짜 아님');
    const e = new CalendarEvent(this, title, start, endExclusive || new Date(start.getTime() + DAY), true); this.events.push(e); return e;
  }
  createEvent(title, start, end) { const e = new CalendarEvent(this, title, start, end, false); this.events.push(e); return e; }
  getEvents(from, to) { return this.events.filter(e => e.start < to && e.end > from).sort((a, b) => a.start - b.start); }
  getEventById(id) { return this.events.find(e => e.id === id) || null; }
}

function makeGlobals(now) {
  const ss = new Spreadsheet();
  const props = {};
  const calendars = {};
  let calSeq = 0;
  const outputs = [];
  const html = {
    outputOf(src) {
      const o = { src, title: '', meta: [], xframe: null, kind: 'html',
        setTitle(t) { o.title = t; return o; }, addMetaTag(n, v) { o.meta.push([n, v]); return o; },
        setXFrameOptionsMode(m) { o.xframe = m; return o; }, getContent() { return o.src; } };
      outputs.push(o); return o;
    }
  };
  const g = {
    SpreadsheetApp: { getActiveSpreadsheet: () => ss, openById: () => ss },
    PropertiesService: { getScriptProperties: () => ({ setProperty: (k, v) => { props[k] = v; }, getProperty: k => (props[k] === undefined ? null : props[k]) }) },
    LockService: { getScriptLock: () => ({ tryLock: () => true, waitLock: () => {}, releaseLock: () => {} }) },
    Utilities: {
      getUuid: () => 'uuid-' + Math.random().toString(16).slice(2) + '-' + Math.random().toString(16).slice(2),
      formatDate: (d, tz, fmt) => d.toISOString()
    },
    CalendarApp: {
      createCalendar: name => { const id = 'cal' + (++calSeq) + '@group.calendar.google.com'; const c = new Calendar(name, id); calendars[id] = c; return c; },
      getCalendarById: id => calendars[id] || null,
      subscribeToCalendar: id => { if (id === 'no-such#holiday') throw new Error('캘린더를 찾지 못함'); const c = new Calendar('공휴일', id); calendars[id] = c; c.createAllDayEvent('한글날', new Date(2026, 9, 9)); c.createAllDayEvent('추석', new Date(2026, 9, 5), new Date(2026, 9, 8)); c.createAllDayEvent('크리스마스', new Date(2026, 11, 25)); return c; }
    },
    ContentService: {
      MimeType: { JSON: 'application/json' },
      createTextOutput: s => { const o = { kind: 'text', body: s, mime: '', setMimeType(m) { o.mime = m; return o; }, getContent() { return o.body; } }; outputs.push(o); return o; }
    },
    HtmlService: {
      XFrameOptionsMode: { ALLOWALL: 'ALLOWALL', DEFAULT: 'DEFAULT' },
      createHtmlOutput: s => html.outputOf(s),
      createHtmlOutputFromFile: f => html.outputOf('<file:' + f + '>'),
      createTemplateFromFile: f => {
        const t = { file: f, evaluate() { const vars = Object.assign({}, t); delete vars.file; delete vars.evaluate; const o = html.outputOf('<template:' + f + '>'); o.vars = vars; return o; } };
        return t;
      }
    },
    Logger: { log: () => {} },
    Session: { getActiveUser: () => ({ getEmail: () => '' }) }
  };
  return { g, ss, props, calendars, outputs, DAY };
}

module.exports = { makeGlobals, DAY };
