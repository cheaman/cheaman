# -*- coding: utf-8 -*-
"""
계산서글.py — ④ 계산서 : 서버 /api/검토 결과(표 넷 · 식 줄)를 20번 짜임(㉮ 식 → 대입 → 답 · ∴ 판정 · [조문])의 계산서 HTML · 글(md)로 묶는다.
  셈은 없다 — 숫자는 전부 검토 결과(stm_풀이 · 정착)와 조합셈에서 온 것 그대로 · [조문] 은 _계획\\03_조문표.md
  HTML 은 A4 세로 · 흰 바탕 · 인쇄(PDF) 용 · hwp 는 다음 걸음 (한글 COM · 2_프로그램\\출력\\hwp쓰기.py 예정)
2026-10-26 새벽 · v0.4.0
"""
import html as _h
import time

import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import 형상                                   # noqa: E402  2_프로그램\형상.py (형식 이름 · 치수 칸)


def _f(x, n=1):
    try:
        return format(float(x), ',.%df' % n)
    except (TypeError, ValueError):
        return '—'


def _e(s):
    return _h.escape(str(s))


def _AI까닭(m):
    """4절 끝 «모델 정한 까닭» — ② 2-5 AI 짚어 보기를 썼을 때만 · AI 의견은 참고 · 처리는 설계자가 누른 것 (10-28 단계 ③)"""
    a = m.get('AI') or {}
    답 = a.get('답') or {}
    if not 답:
        return [], []
    try:
        import AI다리
        옛 = bool(a.get('지문')) and a['지문'] != AI다리.모델지문(m)
    except ImportError:
        옛 = False
    안 = m.get('기본안')
    줄 = ['모델 : ' + ('기본안 %s (프로그램 규칙으로 작성 → 설계자 확정)' % 안 if 안 in ('A', 'B') else '설계자 직접 입력')]
    권 = 답.get('권함') or {}
    이름 = {'claude': '클로드', 'lmstudio': 'LM 스튜디오'}.get(a.get('AI'), a.get('AI') or 'AI')
    권글 = (' · 권함 %s — %s' % ('기본안 ' + 권['안'] if 권.get('안') in ('A', 'B') else '지금 모델 그대로', 권.get('까닭', ''))) if 권.get('안') else ''
    줄.append('AI 짚어 보기 : %s · %s%s' % (이름, a.get('때', ''), 권글))
    if 옛:
        줄.append('답 받은 뒤 모델이 변경됨 — 아래 짚음은 앞 모델 기준')
    처 = a.get('처리') or {}
    for i, x in enumerate(답.get('짚음') or []):
        줄.append('%d) %s · %s — %s → %s' % (i + 1, x.get('등급', ''), x.get('어디', ''), x.get('무엇', ''), 처.get(str(i)) or '미처리'))
    줄.append('AI 의견은 참고 — 좌표 · 부재력 · 판정은 프로그램 셈 · 채택은 설계자')
    return (['<p><b>모델 정한 까닭</b></p><ul>' + ''.join('<li>%s</li>' % _e(s) for s in 줄) + '</ul>'],
            ['', '**모델 정한 까닭**', ''] + ['- ' + s for s in 줄])


def 만들기(m, 검, 조합=None, 서버판='', 화면판=''):
    """m = 과업 json · 검 = /api/검토 결과 · 조합 = 조합셈 결과(없으면 None) → {'절': [...], 'HTML': 문서, '글': md}"""
    f = m.get('형상') or {}; 재 = m.get('재료') or {}; φ = 검['φ']
    이름 = m.get('이름', '과업'); 꼴키 = f.get('꼴') or '깊은보'; 꼴 = 형상.이름.get(꼴키, 꼴키)
    오늘 = time.strftime('%Y-%m-%d')
    절 = []
    _판 = lambda v: '미입력' if v == '미정' else ('부재력 0 · 생략' if v == '생략' else v)      # 판정 값 «미정»(서버 값)은 계산서에 «미입력» 으로 (용어 사전 10-26 · 식 줄 «∴ 미정» 은 그대로)
    def _비(있는, 필요, 판):   # 검토비 — N.G 인데 둘째 자리에서 1.00 이 되면 셋째 자리까지 (10-29 검정)
        try:
            v = float(있는) / float(필요)
        except (TypeError, ValueError, ZeroDivisionError):
            return '—'
        return format(v, ',.3f') if 판 == 'N.G' and round(v, 2) >= 1 else format(v, ',.2f')
    기준 = 검.get('기준') or 'KDS'
    기준글 = {'KDS': 'KDS 14 20 24 (2021)', 'ACI318-11': 'ACI 318-11 (정답지 대조용 · φ 모두 0.75)', '없음': 'φ 없음 (실험 극한 평가 · 대조용)'}.get(기준, 기준)

    def 넣기(번호, 제목, 조각들, md줄):
        절.append({'번호': 번호, '제목': 제목, 'HTML': '\n'.join(조각들), '글': '\n'.join(md줄)})

    import re as _re
    def _칸(c):      # 숫자 칸만 오른쪽 · 글 칸(근거 · 이름)은 왼쪽
        return '<td class="n">%s</td>' % _e(c) if _re.match(r'^[-−+]?[\d,.]+( mm| MPa| × [\d,]+ mm)?$', str(c).strip()) else '<td>%s</td>' % _e(c)
    def 표(머리, 줄들):
        return '<table><tr>' + ''.join('<th>%s</th>' % _e(h) for h in 머리) + '</tr>' + ''.join('<tr>' + ''.join(_칸(c) for c in r) + '</tr>' for r in 줄들) + '</table>'

    def md표(머리, 줄들):
        return ['| ' + ' | '.join(머리) + ' |', '|' + '---|' * len(머리)] + ['| ' + ' | '.join(str(c) for c in r) + ' |' for r in 줄들]

    def 식(줄):
        s = _e(줄)
        for a, b in (('∴ O.K', '∴ <b class="ok">O.K</b>'), ('∴ N.G', '∴ <b class="ng">N.G</b>'), ('∴ 주의', '∴ <b class="mid">주의</b>'), ('∴ 미정', '∴ <b class="mid">미정</b>')):
            s = s.replace(a, b)
        import re
        s = re.sub(r'\[([^\]]+)\]', r'<span class="cite">[\1]</span>', s)
        return '<div class="eq">%s</div>' % s

    # 1 개요
    치수 = 형상.칸.get(꼴키, [])
    치수줄 = [(k, _f(f.get(k), 0) + (' 개' if k.endswith('수') else ' mm')) for k in 치수 if f.get(k) is not None]
    if f.get('받침판'):
        치수줄.append(('받침판', '%s × %s mm' % tuple(f['받침판'])))
    넣기(1, '개요 · 설계 조건', [
        '<p>과업 <b>%s</b> · 부재 형식 <b>%s</b> · 검토 방법 스트럿-타이 모델 · 기준 <b>%s</b> · 단위 %s</p>' % (_e(이름), _e(꼴), _e(기준글), 'kN · mm · MPa' if (m.get('단위') or 'kN-mm-MPa') == 'kN-mm-MPa' else _e(m.get('단위'))),
        표(['치수', '값'], 치수줄),
        '<p class="dim">절점 · 부재는 설계자가 확정한 모델 · 프로그램은 평형 · 정정을 검사 (사재 각도는 표시만) · 강도 · 정착을 검토</p>',
        '<p class="dim">이 계산서는 STM(스트럿 · 타이 · 절점영역 · 정착) 검토만 수록 — 부재 자중 · 깊은보 전단 상한 · 최소 분포철근 · 스트럿 횡철근(KDS 14 20 24 4.2.3) 검토는 별도</p>'],
        ['# STM 검토 계산서 — %s' % 이름, '', '## 1. 개요 · 설계 조건', '- 부재 형식 %s · 기준 %s · 단위 %s' % (꼴, 기준글, 'kN · mm · MPa' if (m.get('단위') or 'kN-mm-MPa') == 'kN-mm-MPa' else m.get('단위'))] + md표(['치수', '값'], 치수줄)
        + ['- 이 계산서는 STM(스트럿 · 타이 · 절점영역 · 정착) 검토만 수록 — 부재 자중 · 깊은보 전단 상한 · 최소 분포철근 · 스트럿 횡철근(4.2.3) 검토는 별도'])

    # 2 재료 · 계수
    βs = m.get('βs') or {}; βn = m.get('βn') or {}
    계수줄 = [('fck', '%s MPa' % _f(재.get('fck', 재.get('fc')), 0), '설계 조건'), ('fy', '%s MPa' % _f(재.get('fy'), 0), '설계 조건'),
           ('φ 스트럿', φ['스트럿'], 'KDS 14 20 10 4.2.3(2)⑥ · KDS 14 20 24 4.1.3(1)'), ('φ 타이', φ['타이'], 'KDS 14 20 24 4.1.3(1)'), ('φ 절점영역', φ['절점'], 'KDS 14 20 10 4.2.3(2)⑥')]
    for k, v in βs.items():
        계수줄.append(('βs ' + k, v, 'KDS 14 20 24 4.2.2(2)'))
    for k, v in βn.items():
        계수줄.append(('βn ' + k, v, 'KDS 14 20 24 4.4.3(2)'))
    βs주 = 'βs · βn 은 설계자 확인 값 (βn 미입력 절점은 연결 타이 수로 지정) · 유효압축강도 fce = 0.85 βs fck (4.2-2) · 0.85 βn fck (4.4-2) · βs 0.75 는 병모양 스트럿의 횡철근 조건 KDS 14 20 24 4.2.3 식 (4.2-3) 만족을 전제 (이 계산서에서 검토하지 않음 — 설계자 확인)'
    넣기(2, '재료 · 강도감소계수', [표(['항목', '값', '근거'], 계수줄), '<p class="dim">%s</p>' % βs주],
        ['', '## 2. 재료 · 강도감소계수'] + md표(['항목', '값', '근거'], 계수줄) + ['- ' + βs주])

    # 3 하중 · 조합
    조각 = []; md = ['', '## 3. 하중 · 하중조합']
    if 조합:
        줄들 = [(r['번호'], _f(r['x'], 0), _f(r['D'], 0), _f(r['L'], 0), _f(r['H'], 0), _f(r['Vu']), _f(r['Hu'])) for r in 조합['줄']]
        조각 += ['<p>하중조합 <b>%s</b> · 하중계수 D %s · L %s <span class="cite">[%s]</span> · 수평력 H 는 고정하중 계수 적용 (확인 필요)</p>' % (_e(조합['조합']), 조합['계수']['D'], 조합['계수']['L'], _e(조합['조문'])),
               표(['받침', 'x', 'D', 'L', 'H', 'Vu', 'Hu'], 줄들), '<p>연직 합 Σ Vu = <b>%s kN</b> · 수평 합 Σ Hu = %s kN</p>' % (_f(조합['연직합']), _f(조합['수평합']))]
        md += ['- 하중조합 %s · 하중계수 D %s · L %s [%s]' % (조합['조합'], 조합['계수']['D'], 조합['계수']['L'], 조합['조문'])] + md표(['받침', 'x', 'D', 'L', 'H', 'Vu', 'Hu'], 줄들) + ['- 연직 합 %s kN' % _f(조합['연직합'])]
        for g in 조합.get('경고') or []:          # 10-29 검정 : 다른 조합(1.4D)이 더 크면 계산서에도
            조각.append('<p class="ng">★ %s</p>' % _e(g)); md.append('- ★ ' + g)
        자중주 = '하중은 받침표 값만 — 부재 자중은 포함하지 않음 (자중을 넣으려면 받침표 D 에 더함 · 설계자 확인)'
        조각.append('<p class="dim">%s</p>' % 자중주); md.append('- ' + 자중주)
    하 = m.get('하중') or {}
    하줄 = [(n, _f(v[0]), _f(v[1])) for n, v in 하.items()]
    조각 += ['<p>절점 하중 (kN · 아래 −)</p>', 표(['절점', 'Fx', 'Fy'], 하줄)]; md += md표(['절점', 'Fx', 'Fy'], 하줄)
    넣기(3, '하중 · 하중조합', 조각, md)

    # 4 모델
    점 = m.get('절점') or {}; 받 = m.get('받침') or {}; 힘 = 검['힘']
    절점줄 = [(n, _f(p[0], 0), _f(p[1], 0), {'xy': '핀', 'y': '롤러', 'x': 'x 만 고정'}.get(''.join(sorted(받.get(n, []))), '—')) for n, p in 점.items()]
    부재줄 = [(p[0], p[1], p[2], p[3], _f(힘.get(p[0]))) for p in m['부재']]
    반력줄 = [(k, _f(v)) for k, v in 힘.items() if k.startswith('R')]
    까닭조각, 까닭md = _AI까닭(m)
    넣기(4, 'STM 모델 (절점 · 부재 · 부재력)', [
        '<p>좌표 원점 = 왼 끝 · 하면 (y 위 +) · 부재력 + 인장 · − 압축 · 정정 트러스를 절점 평형으로 해석</p>',
        표(['절점', 'x', 'y', '지점'], 절점줄), 표(['부재', 'i', 'j', '종류', 'F (kN)'], 부재줄), 표(['반력', 'kN'], 반력줄)] + 까닭조각,
        ['', '## 4. STM 모델'] + md표(['절점', 'x', 'y', '지점'], 절점줄) + [''] + md표(['부재', 'i', 'j', '종류', 'F (kN)'], 부재줄) + [''] + md표(['반력', 'kN'], 반력줄) + 까닭md)

    # 5 스트럿 · 타이
    조각 = []; md = ['', '## 5. 스트럿 · 타이 검토']
    for i, t in enumerate(검['타이']):
        조각.append('<h4>5.%d 타이 %s</h4>' % (i + 1, _e(t['이름']))); md.append('### 5.%d 타이 %s' % (i + 1, t['이름']))
        for 줄 in 검['식줄'].get(t['이름'], []):
            조각.append(식(줄)); md.append('- ' + 줄)
    타이표 = [(t['이름'], _f(t['Fu']), φ['타이'], _f(t['필요As']), ('D%s×%s' % (t['지름'], _f(t['개수'], 0))) if t['지름'] else '—', _f(t['제공As']), _비(t['제공As'], t['필요As'], t['판정']) if t['비'] is not None else '—', _판(t['판정'])) for t in 검['타이']]
    조각 += ['<h4>5.%d 타이 전체</h4>' % (len(검['타이']) + 1), 표(['부재', 'Fu', 'φ', 'As,req', '배근', 'As', '검토비', '판정'], 타이표)]; md += md표(['부재', 'Fu', 'φ', 'As,req', '배근', 'As', '검토비', '판정'], 타이표)
    n0 = len(검['타이']) + 1
    for i, s in enumerate(검['스트럿']):
        조각.append('<h4>5.%d 스트럿 %s</h4>' % (n0 + i + 1, _e(s['이름']))); md.append('### 5.%d 스트럿 %s' % (n0 + i + 1, s['이름']))
        for 줄 in 검['식줄'].get(s['이름'], []):
            조각.append(식(줄)); md.append('- ' + 줄)
    스표 = [(s['이름'], _f(s['Fu']), ('%s (미입력 · 가정)' % s['βs']) if s.get('βs미입력') else s['βs'], _f(s['fce'], 2), _f(s['필요폭']), _f(s['있는폭']) if s['있는폭'] is not None else '—', _비(s['있는폭'], s['필요폭'], s['판정']) if s['비'] is not None else '—', _판(s['판정'])) for s in 검['스트럿']]
    조각 += ['<h4>스트럿 전체</h4>', 표(['부재', 'Fu', 'βs', 'fce', 'w,req', '제공 폭', '검토비', '판정'], 스표)]; md += md표(['부재', 'Fu', 'βs', 'fce', 'w,req', '제공 폭', '검토비', '판정'], 스표)
    넣기(5, '스트럿 · 타이 검토 (식 → 대입 → 답)', 조각, md)

    # 6 절점
    조각 = []; md = ['', '## 6. 절점영역 검토']
    if 검['절점']:
        for n, 줄들 in 검['식줄'].items():
            if n.startswith('절점 '):
                조각.append('<h4>%s</h4>' % _e(n)); md.append('### ' + n)
                for 줄 in 줄들:
                    조각.append(식(줄)); md.append('- ' + 줄)
        절표 = [(x['절점'], x['면'], x['βn'], _f(x['fce'], 2), _f(x.get('두께'), 0), _f(x['필요폭']), _f(x['있는폭']) if x['있는폭'] is not None else '—', _비(x['있는폭'], x['필요폭'], x['판정']) if x['비'] is not None else '—', _판(x['판정'])) for x in 검['절점']]
        머리6 = ['절점', '경계면', 'βn', '유효압축강도 fce', '면 두께 b', 'w,req', '제공 폭', '검토비', '판정']
        조각.append(표(머리6, 절표)); md += md표(머리6, 절표)
        if 검.get('절점두께'):
            두께주 = '면 두께 b = 힘이 닿는 면의 가로폭 (받침판 가로 · 말뚝 π/4·D 등가 · 그 밖은 부재 두께) — KDS 14 20 24 4.4.2(1) An 은 면의 면적'
            조각.append('<p class="dim">%s</p>' % 두께주); md.append('- ' + 두께주)
    else:
        조각.append('<p class="dim">경계면 미입력 — 절점영역 미검토 (경계면 · 작용력을 입력하면 KDS 14 20 24 4.4 로 검토)</p>'); md.append('- 경계면 미입력 — 절점영역 미검토')
    넣기(6, '절점영역 검토', 조각, md)

    # 7 정착
    조각 = []; md = ['', '## 7. 정착 검토']
    if 검['정착표']:
        정표 = [(d['이름'], {'갈고리90': '갈고리 90°', '갈고리180': '갈고리 180°'}.get(d.get('꼴'), d.get('꼴') or '—'), _f(d.get('있는'), 0), _f(d.get('필요'), 0), _비(d.get('있는'), d.get('필요'), d['판정']) if d.get('비') is not None else '—', _판(d['판정']), d.get('고칠길') or (d.get('오류') or '—')) for d in 검['정착표']]
        머리7 = ['타이', '정착 형태', 'ℓanc', 'ℓd (갈고리는 ℓdh)', '검토비', '판정', '조치 방안']
        조각.append(표(머리7, 정표)); md += md표(머리7, 정표)
        조각.append('<p class="dim">식 · 대입은 5절 각 타이의 ㉯ 줄 · 기준 KDS 14 20 52 (2024-12-30) 4.1.2 · 4.1.5</p>')
    else:
        조각.append('<p class="dim">정착 검토 대상 없음 — 정착 형태 · ℓanc 미입력</p>'); md.append('- 정착 검토 대상 없음 (미입력)')
    넣기(7, '정착 검토', 조각, md)

    # 8 판정
    요 = 검['요약']
    요표 = [(k, 요[k]['수'], 요[k]['OK'], 요[k]['NG'], 요[k]['미정'], 요[k].get('생략', 0), _f(요[k]['최소비'], 2) if 요[k]['최소비'] is not None else '—', 요[k]['최소이름'] or '—') for k in ('스트럿', '타이', '절점', '정착')]
    요표 = [({'절점': '절점영역'}.get(x[0], x[0]),) + x[1:] for x in 요표]
    색 = {'O.K': 'ok', 'N.G': 'ng'}.get(검['판정'], 'mid')
    넣기(8, '판정 요약', ['<p class="verdict %s">판정 : %s</p><p>%s</p>' % (색, _e(_판(검['판정'])), _e(검['왜'])), 표(['항목', '수', 'O.K', 'N.G', '미입력', '부재력 0 생략', '최소 검토비', '지배 부재'], 요표),
                      '<p class="dim">검토비 = 제공 ÷ 소요 · 1.00 미만 N.G · 1.11 미만 주의 · «미입력» 은 설계자가 아직 입력하지 않은 값(제공 폭 · 철근)이 있어 판정을 보류한 것</p>']
                  + (['<p>부재력 0 부재 : %s — 부재력이 0 (가장 큰 부재력의 0.01 %% 이하) 이라 강도 · 폭 · 정착 검토를 생략함 (하중이 대칭이면 생기는 부재 · 하중이 변경되면 다시 검토)</p>' % _e(' · '.join(검['힘0']))] if 검.get('힘0') else []),
        ['', '## 8. 판정 요약', '- 판정 **%s** — %s' % (_판(검['판정']), 검['왜'])] + md표(['항목', '수', 'O.K', 'N.G', '미입력', '부재력 0 생략', '최소 검토비', '지배 부재'], 요표)
        + (['', '- 부재력 0 부재 : %s — 부재력이 0 (가장 큰 부재력의 0.01 %% 이하) 이라 강도 · 폭 · 정착 검토를 생략함 (하중이 대칭이면 생기는 부재 · 하중이 변경되면 다시 검토)' % ' · '.join(검['힘0'])] if 검.get('힘0') else []))

    머리 = ('<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>STM 검토 계산서 — %s</title><style>'
          '@page{size:A4;margin:18mm 16mm}body{font-family:Pretendard,"Malgun Gothic",sans-serif;font-size:11.5pt;color:#111;background:#fff;margin:0;padding:18px 22px;line-height:1.5}'
          'h1{font-size:17pt;margin:0 0 4px}h2{font-size:13.5pt;margin:18px 0 6px;padding-bottom:3px;border-bottom:1.5px solid #333;page-break-after:avoid}h4{font-size:11.5pt;margin:10px 0 3px}'
          'table{border-collapse:collapse;margin:4px 0 8px;font-size:10.5pt}th,td{border:1px solid #999;padding:2px 7px;text-align:left}th{background:#eee;font-weight:600}td.n{text-align:right}'
          '.eq{margin:2px 0 2px 8px;font-size:10.8pt}.cite{color:#666;font-size:9.5pt}.dim{color:#666;font-size:10pt}.ok{color:#1a7f37}.ng{color:#c00}.mid{color:#b25000}'
          '.verdict{font-size:15pt;font-weight:800}.verdict.ok{color:#1a7f37}.verdict.ng{color:#c00}.verdict.mid{color:#b25000}.sign{margin-top:16px;color:#777;font-size:9.5pt;border-top:1px solid #ccc;padding-top:4px}'
          '.cover{page-break-after:always;break-after:page;box-sizing:border-box;height:240mm;display:flex;flex-direction:column;align-items:center;padding-top:22mm;overflow:hidden}'
          '.c-top{font-size:12pt;color:#444;min-height:18px}.c-title{font-size:30pt;font-weight:800;letter-spacing:4px;margin:18mm 0 4mm}.c-sub{font-size:14pt;color:#333;margin-bottom:16mm}'
          '.c-tab{width:120mm;font-size:11.5pt}.c-tab th{width:32mm;background:#f2f2f2}.c-tab td{padding:5px 9px}'
          '.c-sign{width:120mm;margin-top:14mm;font-size:11pt;table-layout:fixed}.c-sign th{text-align:center}.c-sign td{height:12mm}'
          '.c-foot{margin-top:auto;font-size:13pt;font-weight:700;min-height:20px}'
          '</style></head><body>') % _e(이름)
    # 표지 (잠정 꼴 · 10-26 — 회사 머리 · 날인 꼴은 전무님 확인 뒤) · 과업 json «표지» 칸이 있으면 그 값 · 없으면 빈칸
    표지 = m.get('표지') or {}
    표지줄 = [('과업명', 표지.get('과업명') or 이름), ('대상 부재', 표지.get('대상') or 꼴 or '—'),
            ('검토 방법', '스트럿-타이 모델 (KDS 14 20 24 (2021))'), ('하중조합', m.get('조합') or '—'),
            ('재료', 'fck %s MPa · fy %s MPa' % (_f(재.get('fck'), 0), _f(재.get('fy'), 0))), ('판정', _판(검['판정'])), ('작성일', 표지.get('날짜') or 오늘)]
    사람 = 표지.get('사람') or {}
    표지HTML = ('<section class="cover"><div class="c-top">%s</div><div class="c-title">구 조 계 산 서</div><div class="c-sub">STM (스트럿-타이 모델) 검토</div>'
              '<table class="c-tab">%s</table>'
              '<table class="c-sign"><tr><th>구분</th><th>작성</th><th>검토</th><th>승인</th></tr>%s</table>'
              '<div class="c-foot">%s</div></section>') % (
        _e(표지.get('발주') or ''),
        ''.join('<tr><th>%s</th><td class="%s">%s</td></tr>' % (_e(k), ({'O.K': 'ok', 'N.G': 'ng'}.get(v, 'mid') if k == '판정' else ''), _e(v)) for k, v in 표지줄),
        ''.join('<tr><th>%s</th>%s</tr>' % (줄, ''.join('<td>%s</td>' % _e((사람.get(누) or {}).get(키, '')) for 누 in ('작성', '검토', '승인')))
                for 줄, 키 in (('성명', '성명'), ('서명', '서명'), ('날짜', '날짜'))),
        _e(표지.get('회사') or ''))
    본문 = 표지HTML + '<h1>STM 검토 계산서 — %s</h1><div class="dim">%s · KDS 14 20 24 (2021) · 하중조합 %s · %s</div>' % (_e(이름), _e(꼴), _e(m.get('조합', '')), 오늘)
    for s in 절:
        본문 += '<h2 id="절%d">%d. %s</h2>%s' % (s['번호'], s['번호'], _e(s['제목']), s['HTML'])
    꼬리 = '<div class="sign">DSM · 64 STM 검토기 · 서버 %s · 화면 %s · %s</div></body></html>' % (_e(서버판), _e(화면판), 오늘)
    글 = '# 구조계산서 — STM 검토\n\n' + '\n'.join('- %s : %s' % kv for kv in 표지줄) + '\n\n| 구분 | 작성 | 검토 | 승인 |\n|---|---|---|---|\n| 성명 | | | |\n| 서명 | | | |\n| 날짜 | | | |\n\n' + '\n'.join(s['글'] for s in 절) + '\n\n---\nDSM · 64 STM 검토기 · 서버 %s · %s\n' % (서버판, 오늘)
    return {'절': [{'번호': s['번호'], '제목': s['제목']} for s in 절], 'HTML': 머리 + 본문 + 꼬리, '글': 글}
