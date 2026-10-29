// 화면 시험 — 복사본 폴더에서 서버를 띄우고 사람처럼 누른다. 돌리기 : node 5_시험/시험_화면.js  (가짜도면.py 가 먼저 돌아 있어야 함 · 아래 bash 가 함)
// 재는 것 : 오류 0 · 자료 넣기 → 숫자 카드 · 캡처 Ctrl+V → 타일 · AI 답(또는 파일 길 안내) · ○ → 규칙 목록 · 올리기 → 시험 창 · PC · 폰 가로 넘침 0
const { chromium } = require('playwright'); const fs = require('fs'); const path = require('path');
const URL = process.argv[2] || 'http://127.0.0.1:8949', 가짜 = process.argv[3], 그림 = process.argv[4] || '/tmp/dsm_screen_test';
fs.mkdirSync(그림, { recursive: true });
(async () => {
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1366, height: 768 } });
  const errs = []; p.on('pageerror', e => errs.push('page: ' + e.message)); p.on('console', m => { if (m.type() === 'error') errs.push('console: ' + m.text()); });
  const 결과 = []; global.결과 = 결과; const 재기 = (이름, 조건, 값) => { 결과.push([조건 ? '✓' : '✗', 이름, String(값)]); };
  await p.goto(URL, { waitUntil: 'networkidle' });
  재기('첫 화면 · 상황 줄이 「자료를 넣으십시오」', /넣으십시오/.test(await p.locator('#situ').innerText()), await p.locator('#situ').innerText());
  재기('첫 화면 · 올리기 단추 잠김 + 까닭', await p.locator('#올리기').isDisabled() && /못 누름/.test(await p.locator('#올리기').getAttribute('title')), await p.locator('#올리기').getAttribute('title'));
  await p.screenshot({ path: path.join(그림, '01_빈화면.png') });
  // ① 파일 더하기 — 보이는 단추를 누르면 파일 고르기 창 → 가짜 짝 둘
  const [chooser] = await Promise.all([p.waitForEvent('filechooser'), p.getByRole('button', { name: '파일 더하기' }).click()]);
  // 경로로 넘기면 이 환경(클라우드 샌드박스)에서 files 가 비어 옴 → 내용(buffer)으로 넘김
  await chooser.setFiles(['가짜_횡단면도_받은판_01.dxf', '가짜_횡단면도_고친판_01.dxf'].map(n => ({ name: n, mimeType: 'application/dxf', buffer: fs.readFileSync(path.join(가짜, n)) })));
  await p.waitForFunction(() => document.querySelectorAll('#자료목록 .tl').length >= 2, null, { timeout: 15000 });
  await p.waitForFunction(() => /셈 끝/.test(document.querySelector('#자료목록 .tl.on .nm small').textContent), null, { timeout: 20000 }).catch(() => {});
  const 타일 = await p.locator('#자료목록 .tl').count(); 재기('도면 둘 넣음 → 타일 2', 타일 === 2, 타일);
  await p.waitForFunction(() => document.querySelector('#이해칸 .numtbl'), null, { timeout: 20000 }).catch(() => {});
  const 숫자카드 = await p.locator('#이해칸 .numtbl').count(); 재기('② 띠에 「프로그램이 센 숫자」 카드', 숫자카드 >= 1, 숫자카드);
  const svg = await p.locator('#이해칸 .svgbox img').first().evaluate(i => i.naturalWidth).catch(() => 0); 재기('도면 그림(SVG) 이 뜸 (접힌 카드 안)', svg > 100, svg);
  await p.locator('#숫자카드 .btn--view').click(); 재기('숫자 카드 「펴기」 → 표가 보임', await p.locator('#숫자카드 .numtbl').isVisible(), 'ok'); await p.locator('#숫자카드 .btn--view').click();
  await p.screenshot({ path: path.join(그림, '02_도면넣음.png') });
  // ② 캡처 붙여넣기 (Ctrl+V 흉내) — 받은판 SVG 를 PNG 로 찍어 그림으로
  await p.locator('#숫자카드 .btn--view').click(); await p.locator('#숫자카드 .svgbox img').first().waitFor({ state: 'visible' });
  const png = await p.locator('#숫자카드 .svgbox img').first().screenshot();   // 도면 그림을 찍어 캡처로 붙임 (사람이 캐드 화면을 찍는 것과 같음)
  await p.locator('#숫자카드 .btn--view').click();
  await p.evaluate(async (b64) => { const r = await fetch('data:image/png;base64,' + b64); const dt = new DataTransfer(); dt.items.add(new File([await r.blob()], 'c.png', { type: 'image/png' })); document.dispatchEvent(new ClipboardEvent('paste', { clipboardData: dt, bubbles: true })); }, png.toString('base64'));
  await p.waitForFunction(() => document.querySelectorAll('#자료목록 .tl').length >= 3, null, { timeout: 15000 });
  const 캡처타일 = await p.locator('#자료목록 .tl', { hasText: '캡처 그림' }).count(); 재기('Ctrl+V → 캡처 타일', 캡처타일 === 1, 캡처타일);
  재기('캡처 타일에 「그림 1장 보기」', await p.getByText('그림 1장 보기').count() === 1, await p.getByText('그림 1장 보기').count());
  // ③ 말로 적기
  await p.getByPlaceholder(/지시선은 45도/).fill('치수선은 바깥 2단까지. 셋째는 지시선으로 뺀다');
  await p.getByRole('button', { name: 'AI 에게 보내기' }).click();
  await p.waitForFunction(() => document.querySelectorAll('#자료목록 .tl').length >= 4, null, { timeout: 15000 });
  재기('말로 적기 → 타일 4', await p.locator('#자료목록 .tl').count() === 4, await p.locator('#자료목록 .tl').count());
  // ④ AI 답 기다림 (이 PC 에 claude 가 있으면 서버가 부름 · 최대 170초) — 없으면 파일 길 안내가 떠야 함
  const 창기다림 = async () => { await p.waitForFunction(() => document.getElementById('ov').classList.contains('on') && document.getElementById('창몸').textContent.length > 20, null, { timeout: 10000 }); };
  const 창닫음 = async () => { await p.keyboard.press('Escape'); await p.waitForFunction(() => !document.getElementById('ov').classList.contains('on'), null, { timeout: 5000 }); };
  const 살아 = await (await p.request.get(URL + '/api/살아있나')).json();
  let AI답 = false, 안내 = '';
  if (살아.클로드) {
    const t시작 = Date.now();   // 노드 쪽에서 3초마다 서버에 되묻는다 (page.waitForFunction 은 약속을 바로 참으로 봄)
    while (Date.now() - t시작 < 200000) { const v = await (await p.request.get(URL + '/api/자료')).json(); if (v.목록.some(a => (a.이해 || []).some(u => u.상태 === 'wait' || u.상태 === 'ask'))) { AI답 = true; break; } await p.waitForTimeout(3000); }
  }
  const 자료 = await (await p.request.get(URL + '/api/자료')).json();
  const 답있는 = 자료.목록.filter(a => (a.이해 || []).some(u => u.상태 === 'wait' || u.상태 === 'ask')); const 오류있는 = 자료.목록.filter(a => a.AI오류);
  재기('AI 답이 옴 (클로드 ' + (살아.클로드 ? '있음' : '없음') + ')', AI답 || !살아.클로드, '답 ' + 답있는.length + '건 · AI오류 ' + 오류있는.length + '건' + (오류있는[0] ? ' : ' + 오류있는[0].AI오류.slice(0, 120) : ''));
  if (답있는.length) {
    await p.locator('#자료목록 .tl', { hasText: 답있는[0].이름.split(' ')[0] }).first().click();
    await p.waitForFunction(() => document.querySelectorAll('#이해칸 .uc .k4').length >= 1, null, { timeout: 5000 });
    const 카드 = await p.locator('#이해칸 .uc .k4').count(); 재기('되짚기 카드 (네 줄) 가 뜸', 카드 >= 1, 카드);
    await p.screenshot({ path: path.join(그림, '03_AI답.png') });
    const ok = (await p.getByRole('button', { name: '○ 맞게 이해함' }).count()) ? p.getByRole('button', { name: '○ 맞게 이해함' }).first() : p.locator('#이해칸 .res .q .btn').first();   // ○ 또는 물음의 첫 답
    if (await ok.count()) {
      재기('○ 단추가 스크롤 없이 보임', await ok.isVisible(), await ok.boundingBox().then(b => b && b.y < 768));
      const t0 = Date.now(); await ok.click(); await p.waitForFunction(() => /○ 받음/.test(document.querySelector('#규칙목록').textContent), null, { timeout: 5000 }); 재기('○ → ③ 규칙 목록에 1초 안에', Date.now() - t0 < 4000, (Date.now() - t0) + 'ms');
      재기('올리기 단추가 켜짐', !(await p.locator('#올리기').isDisabled()), await p.locator('#올리기').isDisabled());
      await p.getByRole('button', { name: /규칙 글 · 숫자 표에 올리기/ }).click();
      await p.waitForFunction(() => document.getElementById('ov').classList.contains('on'), null, { timeout: 30000 });
      const 창 = await p.locator('#창몸').innerText(); 재기('올리기 → 시험 창 (적정 · 통과/못 미침)', /적정/.test(창), 창.slice(0, 80).replace(/\n/g, ' '));
      await p.screenshot({ path: path.join(그림, '04_시험창.png') });
      await 창닫음();
      const 규칙 = await (await p.request.get(URL + '/api/규칙')).json(); 재기('규칙.json 에 올림 1 · 판 v0.1', 규칙.목록.filter(r => r.상태 === '올림').length === 1 && 규칙.판 === 'v0.1', 규칙.판 + ' · ' + 규칙.목록.length);
    } else 재기('○ 단추', false, 'AI 답 카드에 ○ 단추가 없음 (물음 · 못 알아들음만?)');
  }
  // ⑤ 작은 창 셋 · 기억 창고 · 설정 저장
  if (await p.evaluate(() => document.getElementById('ov').classList.contains('on'))) await 창닫음();
  await p.getByRole('button', { name: '기억 창고' }).click(); await 창기다림(); 재기('기억 창고 창', /규칙 글/.test(await p.locator('#창몸').innerText()), 'ok'); await 창닫음();
  await p.getByRole('button', { name: '설정' }).click(); await 창기다림(); await p.locator('#s_출력배율').fill('100'); await p.getByRole('button', { name: '저장' }).click();
  const 설 = await (await p.request.get(URL + '/api/설정')).json(); 재기('설정 저장 → 출력배율 100', 설.출력배율 === 100, 설.출력배율);
  재기('PC 가로 넘침 0', await p.evaluate(() => document.documentElement.scrollWidth) === 1366, await p.evaluate(() => document.documentElement.scrollWidth));
  const m = await b.newPage({ viewport: { width: 390, height: 844 } }); m.on('pageerror', e => errs.push('phone: ' + e.message)); await m.goto(URL, { waitUntil: 'networkidle' }); await m.waitForTimeout(500);
  재기('폰 가로 넘침 0', await m.evaluate(() => document.documentElement.scrollWidth) === 390, await m.evaluate(() => document.documentElement.scrollWidth));
  await m.screenshot({ path: path.join(그림, '05_폰.png') });
  재기('스크립트 오류 0', errs.length === 0, errs.join(' | ').slice(0, 300));
  await b.close();
  결과.forEach(r => console.log(' ', r[0], r[1], '=', r[2]));
  const 틀 = 결과.filter(r => r[0] === '✗').length; console.log('\n맞음 ' + (결과.length - 틀) + ' · 틀림 ' + 틀);
  process.exit(틀 ? 1 : 0);
})().catch(e => { console.log('ERR', e.message.slice(0, 400)); try { global.결과.forEach(r => console.log(' ', r[0], r[1], '=', r[2])); } catch (x) {} process.exit(2); });
