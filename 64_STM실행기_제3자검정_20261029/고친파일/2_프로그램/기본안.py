# ② 모델 기본안 — 형상 · 하중 자리에서 정해진 규칙으로 STM 모델을 그려 «제안» 한다 (확정은 사람)
# 2026-10-26 · CLAUDE.md 2절 (전무님 «기본 제안을 해주는거 아인가») · AI 는 안 고름 — 좌표는 이 규칙이 셈
#
# 깊은보 규칙 (정답지 셋 SP · DB-1 · 2010 논문과 같은 모델이 나오는지 대조함 — 기본안대조.py)
#   받침 절점 x = (TL ∓ 지간) / 2 · 아래 절점 y = 피복하 (타이 높이) · 위 절점 y = H − 피복상
#   A 삼각   : 위 절점 = 하중 자리 · 아래 절점 = 받침 + 하중 자리 아래 · 세로재 · 칸마다 사재 하나
#   B 사다리꼴 : A 에 더해 끝 전단경간 가운데에 세로 타이 하나씩 (사재 각도를 세움)
#   사재가 안 닿는 아래 절점(세로재 힘 0)은 뺀다 → 하중 하나인 A 는 삼각형 (절점 3 · 부재 3)
#   부재 종류는 풀어서 힘 부호로 (인장 = 타이) · βs · βn 은 KDS 14 20 24 발췌 값에서 «제안» (사람 확인)
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '셈'))
import stm_풀이
import 형상                                                 # noqa: E402  2_프로그램\형상.py (형식별 외곽 · 받는 점)


class 안됨(Exception):
    pass


def _이름(i):
    s = ''
    while True:
        s = chr(65 + i % 26) + s
        i = i // 26 - 1
        if i < 0:
            return s


def 깊은보(형, 하중들, 안='A'):
    """형 = 형상 {TL, H, 지간, 피복상, 피복하} · 하중들 = [{x, Vu, Hu}] (계수하중 · 조합셈 결과) → 모델 조각"""
    try:
        TL, H, 지간 = float(형['TL']), float(형['H']), float(형['지간'])
    except (KeyError, TypeError, ValueError):
        raise 안됨('기본안 작성 실패 — TL · H · 지간 입력 필요')
    yb = float(형.get('피복하') or 0); yt = H - float(형.get('피복상') or 0)
    x1, x2 = (TL - 지간) / 2, (TL + 지간) / 2
    if not 하중들:
        raise 안됨('하중 위치 없음 — ① 하중 표에 1줄 이상 입력')
    if yt <= yb:
        raise 안됨('위 절점이 아래 절점보다 낮음 — H · 피복을 확인')
    합 = {}                                                   # 같은 x 하중 줄은 합침 (10-29 검정 : 전엔 위 절점이 겹쳐 길이 0 부재 → 서버 오류) · 일반() 157~160줄과 같은 규칙
    for r in 하중들:
        x = round(float(r['x']), 1); h = 합.setdefault(x, {'x': x, 'Vu': 0.0, 'Hu': 0.0})
        h['Vu'] += float(r['Vu']); h['Hu'] += float(r.get('Hu') or 0)
    하 = sorted(합.values(), key=lambda r: float(r['x']))
    for r in 하:
        if not (x1 < float(r['x']) < x2):
            raise 안됨('하중 위치 x %s 가 두 받침 사이 (%s ~ %s) 밖' % (r['x'], round(x1), round(x2)))
    위x = [float(r['x']) for r in 하]
    if 안 == 'B':
        위x = [(x1 + 위x[0]) / 2] + 위x + [(위x[-1] + x2) / 2]
    elif 안 != 'A':
        raise 안됨('지원하지 않는 기본안 «%s»' % 안)
    # 칸마다 전단 부호 → 사재 방향 (압축이 받침 쪽으로 내려가게)
    R1 = sum(float(r['Vu']) * (x2 - float(r['x'])) for r in 하) / (x2 - x1)
    def 전단(xa):
        return R1 - sum(float(r['Vu']) for r in 하 if float(r['x']) <= xa + 1e-6)
    아래x = [x1] + 위x + [x2]
    선 = []                                                   # (('아래'|'위', 번호), (…))
    선.append((('아래', 0), ('위', 0)))
    선.append((('위', len(위x) - 1), ('아래', len(아래x) - 1)))
    for k in range(len(위x) - 1):
        선.append((('위', k), ('위', k + 1)))
        if 전단(위x[k]) >= 0:
            선.append((('아래', k + 1), ('위', k + 1)))
        else:
            선.append((('위', k), ('아래', k + 2)))
    쓰는아래 = {0, len(아래x) - 1} | {b[1] for 줄 in 선 for b in 줄 if b[0] == '아래'}
    아래번호 = sorted(쓰는아래)
    for a, b in zip(아래번호, 아래번호[1:]):
        선.append((('아래', a), ('아래', b)))
    for k in range(len(위x)):
        if (k + 1) in 쓰는아래:
            선.append((('아래', k + 1), ('위', k)))
    # 이름 : 아래 왼쪽부터 → 위 왼쪽부터 (정답지 SP 와 같은 꼴 A · B 아래 · C 위)
    이름표 = {}
    for i, k in enumerate(아래번호):
        이름표[('아래', k)] = _이름(i)
    for k in range(len(위x)):
        이름표[('위', k)] = _이름(len(아래번호) + k)
    점 = {}
    for (쪽, k), n in 이름표.items():
        점[n] = [round(아래x[k] if 쪽 == '아래' else 위x[k], 1), round(yb if 쪽 == '아래' else yt, 1)]
    부 = []
    for a, b in 선:
        na, nb = sorted((이름표[a], 이름표[b]), key=lambda s: (len(s), s))
        부.append([na + nb, na, nb, '스트럿'])
    받 = {이름표[('아래', 0)]: ['x', 'y'], 이름표[('아래', len(아래x) - 1)]: ['y']}
    하중 = {}
    for r in 하:
        k = 위x.index(float(r['x']))
        하중[이름표[('위', k)]] = [round(float(r.get('Hu') or 0), 1), -round(float(r['Vu']), 1)]
    힘 = stm_풀이.풀기({'절점': 점, '부재': 부, '받침': 받, '하중': 하중})
    for p in 부:
        if 힘[p[0]] > 1e-6:
            p[3] = '타이'
    # βs · βn 제안 [KDS 14 20 24 4.2.2 · 4.4.3 발췌] — 사재 = 병모양 0.75 (4.2.3 철근 조건 만족 가정) · 수평 스트럿 = 단면 일정 1.0
    βs = {}
    for p in 부:
        if p[3] == '스트럿':
            βs[p[0]] = 1.0 if abs(점[p[1]][1] - 점[p[2]][1]) < 1e-6 else 0.75
    βn = {}
    for n in 점:
        타이수 = sum(1 for p in 부 if p[3] == '타이' and n in (p[1], p[2]) and abs(힘[p[0]]) > 1e-6)
        βn[n] = 1.0 if 타이수 == 0 else 0.8 if 타이수 == 1 else 0.6
    사재각 = [round(math.degrees(math.atan2(abs(점[p[2]][1] - 점[p[1]][1]), abs(점[p[2]][0] - 점[p[1]][0]))), 1)
              for p in 부 if p[3] == '스트럿' and abs(점[p[1]][1] - 점[p[2]][1]) > 1e-6]
    return {'안': 안, '이름': {'A': '기본안 A · 삼각', 'B': '기본안 B · 사다리꼴'}[안],
            '절점': 점, '부재': 부, '받침': 받, '하중': 하중, 'βs': βs, 'βn': βn,
            '힘': {k: round(v, 1) for k, v in 힘.items()},
            '절점수': len(점), '부재수': len(부), '사재최소각': min(사재각) if 사재각 else None,
            '메모': 'βs · βn 은 발췌 값에서 제안 (사재 병모양 0.75 = 4.2.3 철근 조건 만족 가정) · 사재 각도 한계는 KDS 14 20 24 · 24 14 21 에 조항이 없어 각도만 보임'}


def _삼각(위, 아래, 좌표, V, 문턱):
    """위 · 아래 줄 (x 순 열쇠) 사이 띠 삼각분할 → 이음 [(a, b)] — 현 · 이음 모두"""
    선 = list(zip(위, 위[1:])) + list(zip(아래, 아래[1:]))
    i = j = 0
    선.append((위[0], 아래[0]))
    while i < len(위) - 1 or j < len(아래) - 1:
        if i == len(위) - 1:
            j += 1
        elif j == len(아래) - 1:
            i += 1
        else:
            t0, t1 = 좌표[위[i]][0], 좌표[위[i + 1]][0]
            b0, b1 = 좌표[아래[j]][0], 좌표[아래[j + 1]][0]
            if t0 < b1 - 1 and b0 < t1 - 1:                  # 두 사재 다 됨 → 전단 부호 (압축 쪽)
                올 = V((max(t0, b0) + min(t1, b1)) / 2) >= -문턱
            else:                                            # 한 쪽만 됨 → x 가 가까운 쪽
                올 = t1 <= b1
            if 올:
                i += 1
            else:
                j += 1
        선.append((위[i], 아래[j]))
    return 선


def 일반(형, 하중들, 안='A'):
    """깊은보 밖 형식 — 형 = 형상 (꼴 · 치수) · 하중들 = [{x, Vu, Hu}] (조합셈 계수하중) → 모델 조각 (깊은보() 와 같은 꼴)"""
    꼴 = 형.get('꼴') or ''
    if 안 not in ('A', 'B'):
        raise 안됨('지원하지 않는 기본안 «%s»' % 안)
    try:
        TL = float(형['TL']); yt = 형상.위y(형)
        받는, 메모, 위덧 = 형상.받는점(형, 하중들, 안)
    except (KeyError, TypeError, ValueError) as e:
        raise 안됨('형상 값이 모자람 (%s) — ① 1-2 치수를 확인' % e)
    except 형상.안됨 as e:
        raise 안됨(str(e))
    if not 하중들:
        raise 안됨('하중 위치 없음 — ① 하중 표에 1줄 이상 입력')
    for r in 하중들:
        if not (0 <= float(r['x']) <= TL):
            raise 안됨('하중 위치 x %s 가 부재 밖 (0 ~ %s)' % (r['x'], round(TL)))
    # 위 줄 (같은 x 는 합침) · 아래 줄
    위하 = {}
    for r in 하중들:
        x = round(float(r['x']), 1); h = 위하.setdefault(x, [0.0, 0.0])
        h[0] += float(r.get('Hu') or 0); h[1] += float(r['Vu'])
    위덧 = [round(x, 1) for x in 위덧 if round(x, 1) not in 위하]
    아래점 = {}
    for p in 받는:
        아래점[round(p['x'], 1)] = p
    if yt <= max(p['y'] for p in 받는) + 1:
        raise 안됨('위 절점이 아래 절점보다 낮음 — 높이 · 피복을 확인')
    xs = sorted(아래점); 왼, 오 = xs[0], xs[-1]
    # 전단 부호용 연직 힘 — 하중 · 안쪽 받는 점 (미리 나눈 반력) · 바깥 두 받침 반력 (힘 · 모멘트 평형)
    힘들 = [(x, yt, h[0], -h[1]) for x, h in 위하.items()]
    힘들 += [(x, 아래점[x]['y'], 0.0, float(아래점[x]['R'])) for x in xs[1:-1] if 아래점[x]['R'] is not None]
    ya = 아래점[왼]['y']; yb = 아래점[오]['y']
    if 오 - 왼 < 1:
        raise 안됨('받는 점이 한 위치 — 받침 2개 필요')
    M = sum(Fy * (x - 왼) - Fx * (y - ya) for x, y, Fx, Fy in 힘들)
    R오 = -M / (오 - 왼); R왼 = -sum(f[3] for f in 힘들) - R오
    연직 = [(x, Fy) for x, y, Fx, Fy in 힘들] + [(왼, R왼), (오, R오)]
    문턱 = 1e-6 * max([abs(v) for _, v in 연직] + [1.0])
    def V(x):
        return sum(v for xi, v in 연직 if xi < x)
    def 짓기(위x, 아래x):
        좌표 = {('위', x): (x, yt) for x in 위x}
        좌표.update({('아래', x): (x, 형상.아래y(형, x)) for x in 아래x})
        return 좌표, _삼각([('위', x) for x in sorted(위x)], [('아래', x) for x in sorted(아래x)], 좌표, V, 문턱)
    위x = sorted(set(위하) | set(위덧)); 아래x = list(xs)
    좌표, 선 = 짓기(위x, 아래x)
    if 안 == 'B':
        더 = set()
        for a, b in 선:
            if a[0] != b[0]:
                xa, xb = 좌표[a][0], 좌표[b][0]; xm = round((xa + xb) / 2, 1)
                if abs(xa - xb) > 0.75 * (yt - 형상.아래y(형, xm)):
                    더.add(xm)
        if not 더:
            raise 안됨('B 는 A 와 같음 (긴 사재 없음)')
        좌표, 선 = 짓기(sorted(set(위x) | 더), sorted(set(아래x) | 더))
    # 받침 · 하중 (열쇠로)
    받 = {('아래', 왼): ['x', 'y'], ('아래', 오): ['y']}
    하 = {('위', x): [round(h[0], 1), -round(h[1], 1)] for x, h in 위하.items()}
    for x in xs[1:-1]:
        if 아래점[x]['R'] is not None:
            하[('아래', x)] = [0.0, round(float(아래점[x]['R']), 1)]
    # 하중 없는 2부재 절점 (꺾인 두 부재 = 힘 0) 은 걷음 — 정정은 그대로 (절점 1 · 부재 2)
    while True:
        걷음 = None
        for n in 좌표:
            if n in 받 or n in 하:
                continue
            닿 = [k for k, (a, b) in enumerate(선) if n in (a, b)]
            if len(닿) == 2:
                o = [선[k][1] if 선[k][0] == n else 선[k][0] for k in 닿]
                d = [(좌표[q][0] - 좌표[n][0], 좌표[q][1] - 좌표[n][1]) for q in o]
                if abs(d[0][0] * d[1][1] - d[0][1] * d[1][0]) > 1e-6 * math.hypot(*d[0]) * math.hypot(*d[1]):
                    걷음 = (n, 닿); break
        if not 걷음:
            break
        선 = [l for k, l in enumerate(선) if k not in 걷음[1]]
        del 좌표[걷음[0]]
    # 이름 : 아래 왼쪽부터 → 위 왼쪽부터
    이름표 = {}
    for k, n in enumerate(sorted([n for n in 좌표 if n[0] == '아래'], key=lambda n: n[1]) + sorted([n for n in 좌표 if n[0] == '위'], key=lambda n: n[1])):
        이름표[n] = _이름(k)
    점 = {이름표[n]: [round(xy[0], 1), round(xy[1], 1)] for n, xy in 좌표.items()}
    부 = []
    for a, b in 선:
        na, nb = sorted((이름표[a], 이름표[b]), key=lambda s: (len(s), s))
        부.append([na + nb, na, nb, '스트럿'])
    받n = {이름표[n]: v for n, v in 받.items()}
    하n = {이름표[n]: v for n, v in 하.items()}
    if 2 * len(점) != len(부) + 3:
        raise 안됨('정정 아님 (절점 %d · 부재 %d) — 규칙 확인 필요' % (len(점), len(부)))
    try:
        힘 = stm_풀이.풀기({'절점': 점, '부재': 부, '받침': 받n, '하중': 하n})
    except SystemExit as e:
        raise 안됨('기본안 해석 실패 — %s' % e)
    for p in 부:
        if 힘[p[0]] > 1e-6:
            p[3] = '타이'
    음반력 = [n for n in 받n if 힘.get('R%sy' % n, 0.0) < -1e-6]
    if 음반력:                                                # 10-29 검정 : 기둥 절점의 인장 반력 = 기둥 철근이 받는 힘 (코벨 · 치우친 코핑) — 모델은 내되 메모 · 검토는 그 절점 지압면을 보지 않음 (서버.검토)
        메모 += ' · ★ 받침 절점 %s 연직 반력 인장 (%s kN) = 기둥 철근(연직 타이)이 받는 힘 — 지압 아님 · 기둥 철근 정착은 설계자 확인' % (' · '.join(음반력), ' · '.join('%.0f' % 힘['R%sy' % n] for n in 음반력))
    βs = {p[0]: (1.0 if abs(점[p[1]][1] - 점[p[2]][1]) < 1e-6 else 0.75) for p in 부 if p[3] == '스트럿'}
    βn = {}
    for n in 점:
        타이수 = sum(1 for p in 부 if p[3] == '타이' and n in (p[1], p[2]) and abs(힘[p[0]]) > 1e-6)
        βn[n] = 1.0 if 타이수 == 0 else 0.8 if 타이수 == 1 else 0.6
    # 판 길이 (폭 제안이 씀) — 받는 점 = 기둥 · 말뚝 · 지반 토막 / 위 하중 = 받침판 (코핑 · 코벨) · 기둥 (말뚝캡 · 확대기초)
    판 = {}
    for x, p in 아래점.items():
        if ('아래', x) in 이름표:
            판[이름표[('아래', x)]] = [round(p['판']), p['판말']]
    받침판 = (형.get('받침판') or [0])[0]
    for x in 위하:
        if 꼴 in ('말뚝캡', '확대기초'):
            l = float(형.get('하중판') or 0) or float(형.get('CW') or 0) / 2
            판[이름표[('위', x)]] = [round(l), '하중판' if 형.get('하중판') else '기둥 폭/2']
        elif 받침판:
            판[이름표[('위', x)]] = [round(float(받침판)), '받침판']
    사재각 = [round(math.degrees(math.atan2(abs(점[p[2]][1] - 점[p[1]][1]), abs(점[p[2]][0] - 점[p[1]][0]))), 1)
              for p in 부 if p[3] == '스트럿' and abs(점[p[1]][1] - 점[p[2]][1]) > 1e-6 and abs(힘[p[0]]) > 1e-6]
    if 안 == 'B' and 사재각:                                  # B 는 사재를 세우려고 더함 — A 보다 눕으면 내지 않음 (코벨 기울어진 밑면 등)
        a각 = 일반(형, 하중들, 'A')['사재최소각']
        if a각 and min(사재각) < a각:
            raise 안됨('B 는 사재 각도 %.1f° 로 A (%.1f°) 보다 낮아짐 — A 를 씀' % (min(사재각), a각))
    return {'안': 안, '이름': {'A': '기본안 A · 최소 트러스', 'B': '기본안 B · 세로재 추가'}[안],
            '절점': 점, '부재': 부, '받침': 받n, '하중': 하n, 'βs': βs, 'βn': βn, '판길이': 판,
            '힘': {k: round(v, 1) for k, v in 힘.items()},
            '절점수': len(점), '부재수': len(부), '사재최소각': min(사재각) if 사재각 else None,
            '메모': 메모 + ' · βs · βn 은 발췌 값에서 제안 (사재 병모양 0.75 = 4.2.3 철근 조건 만족 가정) · 사재 각도 한계는 KDS 14 20 24 · 24 14 21 에 조항이 없어 각도만 보임'}
