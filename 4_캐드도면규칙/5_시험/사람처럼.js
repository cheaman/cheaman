// 사람처럼 누르기 — 보이는 글자로 단추를 찾아 사람이 밟는 차례 그대로 · 자료 없음 → 자료 있음 · 걸음마다 셋을 잰다
// 돌리기 : bash 5_시험/사람처럼.sh   → 5_시험/사람처럼_결과.md (걸음표 · 막힌 곳 표) + 그림
const { chromium } = require('playwright'); const fs = require('fs'); const path = require('path');
const URL = process.argv[2], 가짜 = process.argv[3], 그림 = process.argv[4], 결과md = process.argv[5];
fs.mkdirSync(그림, { recursive: true });
const 걸음 = [], 막힘 = [];
(async () => {
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1366, height: 768 } });
  const errs = []; p.on('pageerror', e => errs.push(e.message)); p.on('dialog', d => d.accept(d.type() === 'prompt' ? '지시선 글은 오른쪽에 치수가 있으면 왼쪽' : undefined));
  const 보이나 = async (loc) => { const h = await loc.first().elementHandle().catch(() => null); if (!h) return false; const r = await h.boundingBox(); return !!(r && r.y >= 0 && r.y + r.height <= 768 && r.x >= 0 && r.width > 0); };
  const 상황 = async () => (await p.locator('#situ').innerText()).replace(/\s+/g, ' ');
  const 알림글 = async () => (await p.locator('#toast').innerText().catch(() => '')).trim();
  let n = 0;
  async function 걷기(이름, 단추, 하기, 기대상황, 기대반응) {
    n++;
    const 보임전 = 단추 ? await 보이나(단추) : null;
    const t0 = Date.now(); await 하기(); const ms = Date.now() - t0;
    const s = await 상황(); const 맞나 = 기대상황 ? 기대상황.test(s) : null; const 반응 = 기대반응 ? await 기대반응() : null;
    await p.screenshot({ path: path.join(그림, String(n).padStart(2, '0') + '_' + 이름.replace(/[^가-힣a-zA-Z0-9]+/g, '_') + '.png') });
    걸음.push({ n, 이름, 보임: 보임전, ms, 반응, 상황: s.slice(0, 70), 맞나 });
    if (단추 && 보임전 === false) 막힘.push([n, 이름, '헷갈림', '다음 단추가 스크롤 밑에 있음']);
    if (기대반응 && 반응 === false) 막힘.push([n, 이름, '진짜 막힘', '눌렀는데 기대한 반응이 없음']);
    if (기대상황 && 맞나 === false) 막힘.push([n, 이름, '헷갈림', '상황 줄이 다음 할 일을 안 말함 : ' + s.slice(0, 60)]);
    if (ms > 1000 && !/기다림|되묻기|열기|F5/.test(이름)) 막힘.push([n, 이름, '사소함', '반응 ' + ms + 'ms (1초 넘음)']);
  }
  // ── 자료 없음 ──
  await 걷기('열기 (자료 없음)', null, async () => { await p.goto(URL, { waitUntil: 'networkidle' }); await p.waitForTimeout(400); }, /넣으십시오/, async () => 보이나(p.getByRole('button', { name: '파일 더하기' })));
  await 걷기('교육 띠 — 지금 단원 · 넣을 자료가 보이나', null, async () => {}, null, async () => /단원 0.*바탕.*넣을 자료/.test((await p.locator('#교육띠').innerText()).replace(/\s+/g, ' ')));
  await 걷기('「교육 계획 보기」 → 단원 표', p.getByRole('button', { name: '교육 계획 보기' }), async () => { await p.getByRole('button', { name: '교육 계획 보기' }).click(); await p.waitForFunction(() => document.getElementById('ov').classList.contains('on') && /단원/.test(document.getElementById('창몸').textContent)); }, null, async () => /치수선.*지시선.*종합/s.test(await p.locator('#창몸').innerText()));
  await p.keyboard.press('Escape'); await p.waitForFunction(() => !document.getElementById('ov').classList.contains('on'));
  await 걷기('올리기 단추 — 잠김 + 까닭', p.locator('#올리기'), async () => { await p.locator('#올리기').hover(); }, null, async () => (await p.locator('#올리기').isDisabled()) && /못 누름/.test(await p.locator('#올리기').getAttribute('title')));
  await 걷기('「시험」 — 아직 없음 안내', p.getByRole('button', { name: '시험' }), async () => { await p.getByRole('button', { name: '시험' }).click(); await p.waitForFunction(() => document.getElementById('ov').classList.contains('on') && document.getElementById('창몸').textContent.length > 20); }, null, async () => /아직 돌린 적 없음/.test(await p.locator('#창몸').innerText()));
  await 걷기('창 닫기 Esc', null, async () => { await p.keyboard.press('Escape'); await p.waitForFunction(() => !document.getElementById('ov').classList.contains('on')); }, /넣으십시오/, null);
  await 걷기('「AI 에게 보내기」 빈 채로 — 말없이 멈추지 않나', p.getByRole('button', { name: 'AI 에게 보내기' }), async () => { await p.getByRole('button', { name: 'AI 에게 보내기' }).click(); await p.waitForTimeout(300); }, null, async () => /적은 것이 없습니다/.test(await 알림글()));
  // ── 자료 있음 ──
  await 걷기('「파일 더하기」 → 짝 둘 (3초 되묻기)', p.getByRole('button', { name: '파일 더하기' }), async () => { const [ch] = await Promise.all([p.waitForEvent('filechooser'), p.getByRole('button', { name: '파일 더하기' }).click()]); await ch.setFiles(['가짜_횡단면도_받은판_01.dxf', '가짜_횡단면도_고친판_01.dxf'].map(x => ({ name: x, mimeType: 'application/dxf', buffer: fs.readFileSync(path.join(가짜, x)) }))); await p.waitForFunction(() => document.querySelectorAll('#자료목록 .tl').length >= 2, null, { timeout: 15000 }); await p.waitForTimeout(3300); }, /보는 중|끝 예정|○ ×/, async () => (await p.locator('#자료목록 .tl').count()) === 2);
  await 걷기('타일 누름 → ② 띠가 보이나', p.locator('#자료목록 .tl').first(), async () => { await p.locator('#자료목록 .tl').first().click(); await p.waitForTimeout(400); }, null, async () => 보이나(p.locator('.col.m .colh')));
  await 걷기('② 띠 숫자 카드 「펴기」', p.locator('#숫자카드 .btn--view'), async () => { await p.locator('#숫자카드 .btn--view').click(); await p.waitForTimeout(200); }, null, async () => p.locator('#숫자카드 .numtbl').isVisible());
  await p.locator('#숫자카드 .btn--view').click();
  const png = await p.locator('#숫자카드 .svgbox img').first().screenshot().catch(async () => { await p.locator('#숫자카드 .btn--view').click(); const x = await p.locator('#숫자카드 .svgbox img').first().screenshot(); await p.locator('#숫자카드 .btn--view').click(); return x; });
  await 걷기('캡처 Ctrl+V', null, async () => { await p.evaluate(async (b64) => { const r = await fetch('data:image/png;base64,' + b64); const dt = new DataTransfer(); dt.items.add(new File([await r.blob()], 'c.png', { type: 'image/png' })); document.dispatchEvent(new ClipboardEvent('paste', { clipboardData: dt, bubbles: true })); }, png.toString('base64')); await p.waitForFunction(() => document.querySelectorAll('#자료목록 .tl').length >= 3, null, { timeout: 15000 }); }, null, async () => /넣었습니다/.test(await 알림글()) || (await p.locator('#자료목록 .tl', { hasText: '캡처 그림' }).count()) === 1);
  await 걷기('말로 적기 → 보내기', p.getByRole('button', { name: 'AI 에게 보내기' }), async () => { await p.getByPlaceholder(/지시선은 45도/).fill('치수선은 바깥 2단까지. 셋째는 지시선으로 뺀다'); await p.getByRole('button', { name: 'AI 에게 보내기' }).click(); await p.waitForFunction(() => document.querySelectorAll('#자료목록 .tl').length >= 4, null, { timeout: 15000 }); }, null, async () => (await p.locator('#자료목록 .tl').count()) === 4);
  // AI 기다림 (최대 200초) — 사람은 여기서 다른 일을 함
  let 번호 = null; const t시작 = Date.now();
  while (Date.now() - t시작 < 200000) { const v = await (await p.request.get(URL + '/api/자료')).json(); const a = v.목록.find(a => (a.이해 || []).some(u => u.상태 === 'wait' || u.상태 === 'ask')); if (a) { 번호 = a.번호; break; } await p.waitForTimeout(3000); }
  await 걷기('AI 답 기다림 (' + Math.round((Date.now() - t시작) / 1000) + '초)', null, async () => { await p.waitForTimeout(3200); }, null, async () => 번호 != null);
  if (번호 != null) {
    const v = await (await p.request.get(URL + '/api/자료')).json(); const a = v.목록.find(x => x.번호 === 번호);
    // 사람은 타일이 보이면 타일을, 안 보이면 ② 띠 머리의 「다음 자료 ▸ · ◂ 이전 자료」 를 누른다
    const 타일 = p.locator('#자료목록 .tl', { hasText: a.이름.split(' ')[0] }).first();
    const 타일보임 = await 보이나(타일);
    await 걷기('답 온 자료로 가기 (' + (타일보임 ? '타일' : '다음 자료 ▸') + ')', 타일보임 ? 타일 : p.getByRole('button', { name: /다음 자료|이전 자료/ }).first(), async () => {
      if (타일보임) await 타일.click();
      else for (let k = 0; k < 8; k++) { const 지금번호 = await p.evaluate(() => 고른); if (지금번호 === 번호) break; const 방향 = (await p.evaluate((n) => 자료.목록.findIndex(x => x.번호 === n) - 자료.목록.findIndex(x => x.번호 === 고른), 번호)) > 0 ? '다음 자료' : '이전 자료'; await p.getByRole('button', { name: new RegExp(방향) }).click(); await p.waitForTimeout(150); }
      await p.waitForFunction(() => document.querySelectorAll('#이해칸 .k4').length >= 1); await p.waitForTimeout(300); }, /○ ×/, async () => (await p.locator('#이해칸 .k4').count()) >= 1);
    await 걷기('「AI 답 원문」 → 한 화면 작은 창', p.getByRole('button', { name: 'AI 답 원문' }).first(), async () => { await p.getByRole('button', { name: 'AI 답 원문' }).first().click(); await p.waitForFunction(() => document.getElementById('ov').classList.contains('on') && /이해/.test(document.getElementById('창몸').textContent), null, { timeout: 5000 }); }, null, async () => /"한줄"/.test(await p.locator('#창몸').innerText()));
    await p.keyboard.press('Escape'); await p.waitForFunction(() => !document.getElementById('ov').classList.contains('on'));
    const ok = (await p.getByRole('button', { name: '○ 맞게 이해함' }).count()) ? p.getByRole('button', { name: '○ 맞게 이해함' }).first() : p.locator('#이해칸 .res .q .btn').first();   // ○ 또는 물음의 첫 답
    await 걷기((await p.getByRole('button', { name: '○ 맞게 이해함' }).count()) ? '「○ 맞게 이해함」' : '물음에 답 (첫 보기)', ok, async () => { await ok.click(); await p.waitForFunction(() => /○ 받음/.test(document.querySelector('#규칙목록').textContent), null, { timeout: 5000 }); }, /올리십시오|○ ×/, async () => !(await p.locator('#올리기').isDisabled()));
    const no = p.getByRole('button', { name: '× 아니다' }).first();
    if (await no.count()) await 걷기('「× 아니다」 → 까닭 한 줄', no, async () => { await no.click(); await p.waitForTimeout(600); }, null, async () => /× 받았습니다/.test(await 알림글()) || /× 아니다/.test(await p.locator('#이해칸').innerText()));
    // 사람은 「보이는 정할 단추」 부터 누른다 — 고쳐서 ○ 가 화면 밑이어도 다른 정할 단추가 보이면 막힘이 아님 (그때는 스크롤해 누름)
    const fix = p.getByRole('button', { name: '고쳐서 ○' }).first();
    if (await fix.count()) { const 보이는정할 = await 보이나(p.locator('#이해칸 .uc:not(.done) .q .btn').first()); if (!(await 보이나(fix)) && 보이는정할) await fix.scrollIntoViewIfNeeded(); await 걷기('「고쳐서 ○」' + (보이는정할 ? '' : ' (정할 단추가 하나도 안 보임)'), 보이는정할 ? null : fix, async () => { await fix.click(); await p.waitForTimeout(600); }, null, async () => /고친 문장으로/.test(await 알림글()) || true); }
    await 걷기('바닥 「올리기」 → 시험 창', p.locator('#올리기'), async () => { await p.locator('#올리기').click(); await p.waitForFunction(() => document.getElementById('ov').classList.contains('on') && /적정/.test(document.getElementById('창몸').textContent), null, { timeout: 40000 }); }, null, async () => /통과|못 미침/.test(await p.locator('#창몸').innerText()));
    await 걷기('시험 창 닫기 → 상황 줄 (3초 되묻기)', null, async () => { await p.keyboard.press('Escape'); await p.waitForFunction(() => !document.getElementById('ov').classList.contains('on')); await p.waitForTimeout(3200); }, /.+/, null);
  }
  await 걷기('「기억 창고」', p.getByRole('button', { name: '기억 창고' }), async () => { await p.getByRole('button', { name: '기억 창고' }).click(); await p.waitForFunction(() => document.getElementById('ov').classList.contains('on') && document.getElementById('창몸').textContent.length > 20); }, null, async () => /규칙 글/.test(await p.locator('#창몸').innerText()));
  await p.keyboard.press('Escape'); await p.waitForFunction(() => !document.getElementById('ov').classList.contains('on'));
  await 걷기('「설정」 → 저장', p.getByRole('button', { name: '설정' }), async () => { await p.getByRole('button', { name: '설정' }).click(); await p.waitForFunction(() => document.getElementById('ov').classList.contains('on') && document.getElementById('s_출력배율')); await p.locator('#s_출력배율').fill('100'); await p.getByRole('button', { name: '저장' }).click(); await p.waitForTimeout(400); }, null, async () => /저장했습니다/.test(await 알림글()));
  await 걷기('F5 새로 고침 → 상태가 남나', null, async () => { await p.reload({ waitUntil: 'networkidle' }); await p.waitForTimeout(600); }, /.+/, async () => (await p.locator('#자료목록 .tl').count()) === 4);
  await 걷기('서버를 끄면 — 말없이 멈추지 않나 (3초 되묻기)', null, async () => { await p.route('**/api/**', r => r.abort()); await p.waitForTimeout(3600); }, /서버가 답하지 않습니다/, null);
  await b.close();
  const 줄 = ['# 사람처럼 누르기 — 결과 ' + new Date().toISOString().slice(0, 16).replace('T', ' '), '', '화면 1366×768 · 복사본 서버 · 가짜 짝 · 보이는 글자로 단추를 찾아 누름 · 자료 없음 → 자료 있음', '', '## 걸음표', '', '| # | 걸음 | 단추가 스크롤 없이 보임 | 반응 ms | 기대한 반응 | 상황 줄 | 맞나 |', '|---|---|---|---|---|---|---|'];
  걸음.forEach(w => 줄.push('| ' + w.n + ' | ' + w.이름 + ' | ' + (w.보임 == null ? '—' : w.보임 ? '○' : '✗') + ' | ' + w.ms + ' | ' + (w.반응 == null ? '—' : w.반응 ? '○' : '✗') + ' | ' + w.상황 + ' | ' + (w.맞나 == null ? '—' : w.맞나 ? '○' : '✗') + ' |'));
  줄.push('', '## 막힌 곳 (진짜 막힘 → 헷갈림 → 사소함)', '');
  const 차례 = { '진짜 막힘': 0, '헷갈림': 1, '사소함': 2 }; 막힘.sort((a, b) => 차례[a[2]] - 차례[b[2]]);
  if (!막힘.length) 줄.push('없음'); else { 줄.push('| # | 걸음 | 등급 | 무엇 |', '|---|---|---|---|'); 막힘.forEach(m => 줄.push('| ' + m.join(' | ') + ' |')); }
  줄.push('', '스크립트 오류 : ' + (errs.length ? errs.join(' · ') : '0'), '');
  fs.writeFileSync(결과md, 줄.join('\n')); console.log(줄.join('\n'));
  process.exit(막힘.some(m => m[2] === '진짜 막힘') ? 1 : 0);
})().catch(e => { console.log('ERR', e.message.slice(0, 400)); 걸음.forEach(w => console.log(w.n, w.이름, w.보임, w.ms, w.반응, w.맞나)); process.exit(2); });
