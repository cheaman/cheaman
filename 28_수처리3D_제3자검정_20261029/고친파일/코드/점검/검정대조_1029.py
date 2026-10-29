# -*- coding: utf-8 -*-
r"""제3자 검정 (2026-10-29 · 1_기록 206) 회귀 시험 — 평가자 둘이 짚고 재현한 지적이 고쳐졌는지 같은 입력으로 다시 잼
  PYTHONUTF8=1 python 코드\점검\검정대조_1029.py        → 끝 줄 «검정 대조 N/N ✔»
  자료 : _시험자료\스크린실\모델링\전채만 테스트\2_해석\그물_모델링.json (저장된 면하중 = 되돌이 기준) · 읽기만 · 임시 폴더에만 씀
"""
import copy
import io
import json
import os
import sys
import tempfile

여기 = os.path.dirname(os.path.abspath(__file__))
뿌리 = os.path.dirname(os.path.dirname(여기))
sys.path.insert(0, os.path.dirname(여기))
sys.stdout.reconfigure(encoding='utf-8')
import 하중계산 as 하      # noqa: E402
import MCT쓰기             # noqa: E402

그물자리 = os.path.join(뿌리, '_시험자료', '스크린실', '모델링', '전채만 테스트', '2_해석', '그물_모델링.json')
줄 = []


def 잼(이름, 됨, 글=''):
    줄.append(bool(됨))
    print('%s %-62s %s' % ('✔' if 됨 else '✘', 이름, 글))


def 그물():
    return json.load(io.open(그물자리, encoding='utf-8'))


def 설(g, **덮을):
    d = dict(하.기본설계값); d.update(g.get('설계값') or {}); d.update(덮을)
    return d


def 면(g, **덮을):
    return 하.면하중만들기(g, 설(g, **덮을))


def 판표(g):
    return {int(p['번']): p for p in g['판요소']}


def MCT(g, **덮을):
    g2 = copy.deepcopy(g); g2['설계값'] = 설(g2, **덮을)
    d = tempfile.mkdtemp(prefix='stm28검정_'); src = os.path.join(d, '그물.json')
    json.dump(g2, io.open(src, 'w', encoding='utf-8'), ensure_ascii=False)
    out = os.path.join(d, '낸.mct'); _, 말 = MCT쓰기.쓰기(src, out)
    return io.open(out, encoding='cp949', errors='replace').read(), 말


# 0 되돌이 — 저장된 면하중과 같은가 (바뀌어야 할 곳 = 바닥 모서리 띠 8 장 내부수압만)
g = 그물(); 저장 = g['면하중']; 지금 = 면(g)
다른 = {}
for k in set(저장) | set(지금):
    a = {(q['요소'], q['방향']): q['값'] for q in 저장.get(k, [])}; b = {(q['요소'], q['방향']): q['값'] for q in 지금.get(k, [])}
    다른[k] = sorted(k2 for k2 in set(a) | set(b) if a.get(k2) != b.get(k2))
잼('0 되돌이 : 횡토압 · 지하수압 · 양압력 · 활하중 저장값과 같음', all(not 다른[k] for k in 다른 if k != '내부수압'))
잼('0 되돌이 : 내부수압은 바닥 모서리 띠 8 장만 더해짐 (A10)', len(다른['내부수압']) == 8 and all(q['값'] == -15.0 for q in 지금['내부수압'] if (q['요소'], q['방향']) in set(다른['내부수압'])), str([e for e, _ in 다른['내부수압']]))
잼('0 되돌이 : 알림 없음', not g['하중알림'], str(g['하중알림'])[:80])

# 1 상판 내부수압 — 수위가 상판 밑면보다 높으면 «위로» (A2 · B1)
g = 그물(); f = 면(g, 내부수위EL=5.0)
위 = [q for q in f['내부수압'] if q['방향'] == 'GZ' and q['값'] > 0]
잼('1 내부수위 5.0 → 상판 152 장 +9.0 (위로 · 전엔 −5.0)', len(위) == 152 and all(abs(q['값'] - 9.0) < 1e-6 for q in 위), '%d 장 %s' % (len(위), sorted({q['값'] for q in 위})))
잼('1 알림 «상판에 내부수압을 위로»', any('위로' in a for a in g['하중알림']))
g = 그물(); f = 면(g, 내부수위EL=1.75)
잼('1 수위 1.75 (상판 아래) 면 상판에 아무것도 없음', not any(q['값'] > 0 for q in f['내부수압'] if q['방향'] == 'GZ'))

# 2 상판 위 벽 토막 — 상재 · 활하중이 사라지던 것 (A3)
def 토막(g):
    nmax = max(int(n['번']) for n in g['절점']); pmax = max(int(p['번']) for p in g['판요소'])
    top = [n for n in g['절점'] if abs(float(n['X'])) < 1e-6 and abs(float(n['Z']) - 4.3) < 1e-6][:2]
    n1 = {'번': nmax + 1, 'X': 0.0, 'Y': top[0]['Y'], 'Z': 4.8}; n2 = {'번': nmax + 2, 'X': 0.0, 'Y': top[1]['Y'], 'Z': 4.8}
    g['절점'] += [n1, n2]
    g['판요소'].append({'번': pmax + 1, '절점': [int(top[0]['번']), int(top[1]['번']), n2['번'], n1['번']], '두께': 0.4, '무엇': '벽', '구분': '외부', '묶음': '외부벽체1'})
    return g
g = 토막(그물()); f = 면(g, 토피=1.0, 지표EL=None)          # 저장 설계값의 지표EL 4.5 (화면 값) 를 비워야 «상판 윗면 + 토피» 규칙이 보임
잼('2 벽 토막 + 토피 1 → 상재토압 160 장 · 활하중 160 장 (전엔 0)', len(f.get('상재토압(지하수무)', [])) == 160 and len(f.get('활하중', [])) == 160)
잼('2 흙 표면 = 상판 윗면 4.5 + 토피 1 = 5.5 (전엔 벽 윗끝 4.8 + 1)', abs(g['하중근거']['지표EL'] - 5.5) < 1e-6, '%s' % g['하중근거']['지표EL'])
잼('2 알림 «상판보다 높은 벽 1 장»', any('높은 벽 1 장' in a for a in g['하중알림']))

# 3 지진 값 일부 → 알림 (A4 · B2)
g = 그물(); f = 면(g, 지진KH=0.2156)
잼('3 KH 만 → 관성 · 동수압만 나가고 알림 «지진 값이 일부 비어»', set(k for k in f if '방향' in k) == {'구체관성력(X방향)', '구체관성력(Y방향)', '동수압(X방향)', '동수압(Y방향)'} and any('일부 비어' in a for a in g['하중알림']))
g = 그물(); f = 면(g, 지진KH='', 지진Sv=0.0118, 지진TG=0.17, 지진H=11.7, 지진KhX=204646, 지진KhY=187481)
잼("3 KH '' → 측벽변위만 · 알림에 «KH (동수압 · 구체관성력)»", any('KH (동수압' in a for a in g['하중알림']) and '측벽변위하중(X방향)' in f)
g = 그물(); f = 면(g, 지진KH=0.2156, 지진Sv=0.0118, 지진TG=0.17, 지진H=11.7, 지진KhX=204646, 지진KhY=187481, 지진Vs=0, 지진Vu=0.5, 지진Vb=4.0)
잼('3 Vs 0 · Vu 0.5 · Vb 4 → 주면전단 나감 (B10 · 전엔 Vs > 0 문지기)', '주면전단력(X방향)' in f and any(q['값'] == 0.5 for q in f['주면전단력(X방향)']))
g = 그물(); f = 면(g, 지진KH=0.2156, 지진Sv=0.0118, 지진TG=0.17, 지진H=11.7, 지진KhX=204646, 지진KhY=187481, 지진Vs=2.24)
잼('3 다 넣으면 8 케이스 · «일부 비어» 알림 없음', len([k for k in f if '방향' in k]) == 8 and not any('일부 비어' in a for a in g['하중알림']))
잼('3 중간슬래브 주면전단 알림 (A7 · 값은 그대로)', any('중간슬래브' in a and '주면전단' in a for a in g['하중알림']))

# 4 재하표 · 0 장 · 물칸 밖 알림 (A12 · B3 · B11)
g = 그물(); f = 면(g, 재하표={'활하중': ['없는묶음']})
잼('4 재하표 없는 묶음 → 알림 둘 (묶음 없음 · 활하중 0 장)', any('없는묶음' in a for a in g['하중알림']) and any('«활하중» 케이스가 0 장' in a for a in g['하중알림']))
g = 그물(); f = 면(g, 물담는칸=[{'x0': 10, 'x1': 12, 'y0': 0, 'y1': 7.1}])
잼('4 물칸이 모델 밖 → 알림', any('모델 밖' in a for a in g['하중알림']) and '내부수압' not in f)

# 5 입력 어긋남 알림 (B4 · A12② · B9 · A11)
g = 그물(); f = 면(g, 토피=1.0, 지표EL=3.0)
잼('5 지표 3.0 < 상판 윗면 4.5 · 토피 1 → 알림', any('상판 윗면' in a and '토피' in a for a in g['하중알림']))
g = 그물(); f = 면(g, 지하수위EL=6.0, 지표EL=4.5)
잼('5 지하수 6.0 > 흙 표면 4.5 → 알림', any('지하수위 EL' in a and '높음' in a for a in g['하중알림']))
g = 그물(); f = 면(g, 차량통행=True)
잼('5 차량 통행 + 군중 → 알림', any('차량 통행' in a for a in g['하중알림']))
g = 그물(); f = 면(g, 조합틀='옛틀', 토피=3.0, aH계산h=None)
잼('5 옛틀 · αH h 비움 · 토피 3 → 알림', any('αH' in a for a in g['하중알림']))

# 6 설계값 문자열 (B12)
g = 그물(); f = 면(g, 지하수위EL='0.45', 내부수위EL='', 토피='1.2', 지진KH='abc')
잼("6 '0.45' · '' · '1.2' · 'abc' → 터지지 않고 셈 · 'abc' 알림", len(f.get('양압력', [])) == 168 and '내부수압' not in f and len(f.get('상재토압(지하수무)', [])) == 160 and any('못 읽은 설계값' in a for a in g['하중알림']))

# 7 동수압 — 격벽 양쪽 · 개구부 줄 (A6)
g = 그물(); f = 면(g, 지진KH=0.2156, 지진Sv=0.01183, 지진TG=0.1724, 지진H=11.7, 지진KhX=204646, 지진KhY=187481, 지진Vs=2.24)
판 = 판표(g); 가 = {e: 하.판가운데(g, p) for e, p in 판.items()}
d = {}
for q in f['동수압(X방향)']:
    d.setdefault((판[q['요소']]['묶음'], round(가[q['요소']][2], 3)), set()).add(round(max(q['값']), 3))
잼('7 바깥벽 X 동수압 : 같은 벽 · 같은 높이 줄은 한 값 (B 들쭉날쭉 없음)', all(len(v) == 1 for v in d.values()), str({k: sorted(v) for k, v in d.items() if len(v) > 1})[:80])
내 = [q for q in f['동수압(Y방향)'] if 판[q['요소']]['구분'] == '내부']
잼('7 격벽 (y 1.75 · 양옆 물) 동수압 = 양쪽 합 (알림)', len(내) > 0 and any('격벽' in a for a in g['하중알림']), '%d 장 최대 %.3f' % (len(내), max(max(q['값']) for q in 내) if 내 else 0))

# 8 단차 지붕 (B5) — 상부슬래브2 를 낮게 만들어 봄 : 상판 일부를 EL 3.0 으로 내리고 묶음 상부슬래브2
g = 그물(); 점 = {int(n['번']): n for n in g['절점']}
위판 = [p for p in g['판요소'] if p['무엇'] == '슬래브' and abs(하.판가운데(g, p, 점)[2] - 4.3) < 1e-6 and 하.판가운데(g, p, 점)[1] > 5.0]
내린 = set()
for p in 위판:
    p['묶음'] = '상부슬래브2'
    for b in p['절점']:
        내린.add(int(b))
for b in 내린:
    점[b]['Z'] = 3.0
f = 면(g, 토피=1.0, 지표EL=None)
낮 = [q for q in f.get('상재토압(지하수무)', []) if abs(하.판가운데(g, 판표(g)[q['요소']], 점)[2] - 3.0) < 1e-6]
잼('8 단차 지붕 (EL 3.0 · %d 장) 에 흙 무게 19 × (5.5 − 3.2) = 43.7 (전엔 0)' % len(위판), len(낮) == len(위판) and all(abs(q['값'] + 43.7) < 0.01 for q in 낮), str(sorted({q['값'] for q in 낮})))
잼('8 단차 지붕 알림', any('단차 지붕' in a for a in g['하중알림']))

# 9 MCT — 지진 조합 내부수압 (A1 · 선택) · 두께 0 알림 (B13)
g = 그물(); t, 말 = MCT(g)
잼('9 기본 : ECase 에 내부수압 없음 + 주석 알림', '지진 조합 (ECase) 에 내부수압 F 없음' in t and 'NAME=ECase1,' in t and 'ST, 내부수압' not in t.split('NAME=ECase1,')[1].split('NAME=ECase2,')[0])
g = 그물(); t2, _ = MCT(g, 지진내부수압=True)
첫 = t2.split('NAME=ECase1,')[1].split('NAME=ECase2,')[0]; 다섯 = t2.split('NAME=ECase17,')[1].split('NAME=ECase18,')[0]
잼('9 지진내부수압 켬 : ECase1 내부수압 1.2 · ECase17 (0.9D) 0.9', 'ST, 내부수압, 1.2' in 첫 and 'ST, 내부수압, 0.9' in 다섯 and '내부수압 F 없음' not in t2)
g = 그물(); g['판요소'][0]['두께'] = 0
t3, 말3 = MCT(g)
잼('9 두께 0 판 → MCT 알림 «두께가 0 인 판요소 1 장»', any('두께가 0' in m for m in 말3), str(말3)[-90:])

print('검정 대조 %d/%d %s' % (sum(줄), len(줄), '✔' if all(줄) else '✘'))
sys.exit(0 if all(줄) else 1)
