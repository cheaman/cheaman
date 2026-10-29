# 스트럿 · 절점 «있는 폭» 제안 — ACI 318 해설 꼴 (R23 절점영역 그림 · StructurePoint 전이보 예제 꼴)
# 2026-10-26 · KDS 14 20 24 본문에는 폭 수치 규칙이 없음 (_계획\발췌_KDS 14 20 24_4.1.1-4.1.2 …) → 전무님 고르심 «ACI 318 해설 꼴»
#
#   판 면 (반력 · 하중이 닿는 수평면) = 판 길이 lb   받침 = 형상.받침판[0] · 하중 = 형상.하중판 (없으면 받침판[0])
#   타이 면 (연직면) = wt = 2 × 타이 중심 높이       아래 절점 = 2 × 피복하 · 위 절점 = 2 × 피복상
#   사면 = lb'·sinθ + wt·cosθ                       θ = 사재 각 (수평에서) · lb' = 판을 닿는 사재 연직 힘 비로 나눈 몫 (사재 둘이면 반씩)
#   다만 가로 부재가 없는 판 절점 (하중 아래 CCC) 은 정수압 절점 — 사면 = lb × 스트럿 힘 / 판 힘 (SP C 사면 15.7 = 16.7 × 603/640 in)
#   스트럿 있는 폭 = 양 끝 경계면 중 작은 값 · 수평 스트럿 (위 현) 은 두 끝 wt 가운데 작은 값
# 제안만 — 화면은 빈 칸에만 넣고 사람이 고친 칸은 안 덮음 · 강도식 · 기준값은 새로 만들지 않음
import math

근거 = 'ACI 318 해설 꼴 (KDS 14 20 24 본문에 폭 규칙 없음 · 10-26 고르심)'


def _수(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return 0.0


def _끝(m, n, a, b):
    점 = m['절점']; o = b if a == n else a
    dx, dy = 점[o][0] - 점[n][0], 점[o][1] - 점[n][1]
    return dx, dy, math.hypot(dx, dy)


def 절점면(m, 힘):
    """절점마다 면 제안 — 수평면 (받침 반력 y · 없으면 하중) · 연직면 (수평 부재) · 사면 (기운 부재, 셋까지). 힘 0 부재는 뺌"""
    받 = m.get('받침') or {}; 하 = m.get('하중') or {}; 표 = {}
    for n in m['절점']:
        면 = {}
        if 'y' in (받.get(n) or []):
            if _수(힘.get('R%sy' % n)) >= -1e-6:              # 10-29 검정 : 인장(음) 반력이면 지압면이 아님 — 제안하지 않음 (서버.검토 가 알림)
                면['수평면'] = 'R%sy' % n
        elif n in 하 and abs(_수((list(하[n]) + [0, 0])[1])) > 1e-9:
            면['수평면'] = 'P:' + n
        사 = []; 가로들 = []
        for 이름, a, b, 종 in m['부재']:
            if n not in (a, b) or abs(힘.get(이름, 0)) < 1e-6:
                continue
            dx, dy, L = _끝(m, n, a, b)
            if abs(dy) < 1e-6 * max(L, 1):
                가로들.append(이름)
            elif abs(dx) > 1e-6 * max(L, 1):
                사.append(이름)
        if 가로들:                                            # 10-29 검정 : 수평 부재가 둘(이어지는 타이 AB · BC)이면 힘이 큰 쪽 — 전엔 먼저 나온 것
            면['연직면'] = max(가로들, key=lambda k: abs(힘.get(k, 0)))
        for 면이름, 이름 in zip(('사면', '사면2', '사면3'), 사):
            면[면이름] = 이름
        if 면:
            표[n] = 면
    return 표


def 폭들(m, 힘, 면표=None):
    """→ {'스트럿': {이름: 폭}, '절점': {'n 면': 폭}, '절점면': 면표, '식': {열쇠: 글}} · 형상(피복 · 받침판)이 없으면 빈 것"""
    형 = m.get('형상') or {}; 점 = m.get('절점') or {}
    판 = 형.get('받침판') or []
    lb받 = _수(판[0]) if 판 else 0.0
    lb하 = _수(형.get('하중판')) or lb받
    판표 = m.get('판길이') or {}   # 기본안 (일반 형식) 이 준 절점별 판 길이 {n: [길이, 말]} — 기둥 · 말뚝 · 지반 토막 · 받침판 (있으면 위 둘보다 먼저)
    상, 하c = _수(형.get('피복상')), _수(형.get('피복하'))
    빈 = {'스트럿': {}, '절점': {}, '절점면': {}, '식': {}, '근거': 근거}
    if not ((lb받 or 판표) and (상 or 하c)) or not 점:
        return 빈
    면표 = 면표 if 면표 is not None else 절점면(m, 힘)
    ys = [p[1] for p in 점.values()]; 가운데 = (min(ys) + max(ys)) / 2
    def wt(n): return 2 * (하c if 점[n][1] <= 가운데 else 상)
    받 = m.get('받침') or {}; 하 = m.get('하중') or {}
    def lb(n):            # 면 표가 비어도 받침 · 하중에서 바로
        if n in 판표:
            return _수(판표[n][0])
        if 'y' in (받.get(n) or []):
            return lb받
        return lb하 if n in 하 and abs(_수((list(하[n]) + [0, 0])[1])) > 1e-9 else 0.0
    def 가로(n):          # 그 절점에 수평 부재 (힘 있음) 가 있나
        return any(n in (a, b) and abs(힘.get(이름, 0)) > 1e-6 and abs(_끝(m, n, a, b)[1]) < 1e-6 * max(_끝(m, n, a, b)[2], 1) for 이름, a, b, 종 in m['부재'])
    def 사재(n):          # 그 절점의 기운 부재 (힘 있음) → [(이름, sinθ, cosθ, 연직 힘)]
        줄 = []
        for 이름, a, b, 종 in m['부재']:
            if n not in (a, b) or abs(힘.get(이름, 0)) < 1e-6:
                continue
            dx, dy, L = _끝(m, n, a, b)
            if abs(dx) > 1e-6 * L and abs(dy) > 1e-6 * L:
                s, c = abs(dy) / L, abs(dx) / L
                줄.append((이름, s, c, abs(힘[이름]) * s))
        return 줄
    out = dict(빈, 절점면=면표)
    사면폭 = {}; 식 = {}
    for n in 점:
        줄 = 사재(n); 합 = sum(x[3] for x in 줄) or 1.0
        if lb(n) <= 0:                                        # 10-29 검정 : 판(받침판 · 하중판 · 기둥 · 말뚝)이 없는 절점은 ACI 해설 식 (lb'·sinθ + wt·cosθ) 의 적용 밖 — 제안하지 않음 (전엔 wt·cosθ 만 남아 36 ~ 94 mm 거짓 폭)
            continue
        정수압 = not 가로(n)
        for 이름, s, c, V in 줄:
            if 정수압:
                w = lb(n) * abs(힘[이름]) / 합      # 합 = 판 힘 (사재 연직 힘 합)
                식[(n, 이름)] = '정수압 절점 : lb × F / P = %.0f × %.1f / %.1f = %.0f mm' % (lb(n), abs(힘[이름]), 합, w)
            else:
                l = lb(n) * V / 합; w = l * s + wt(n) * c
                식[(n, 이름)] = "lb'·sinθ + wt·cosθ = %.0f × %.3f + %.0f × %.3f = %.0f mm" % (l, s, wt(n), c, w)
            사면폭[(n, 이름)] = w
    for n, 면들 in 면표.items():
        for 면, 키 in 면들.items():
            열쇠 = '%s %s' % (n, 면)
            if 면 == '수평면' and lb(n):
                out['절점'][열쇠] = round(lb(n)); out['식'][열쇠] = (판표[n][1] if n in 판표 else '받침판' if 'y' in (받.get(n) or []) else '하중판') + ' 길이 %.0f mm' % lb(n)
            elif 면 == '연직면' and wt(n):
                out['절점'][열쇠] = round(wt(n)); out['식'][열쇠] = 'wt = 2 × 타이 중심 높이 = 2 × %.0f = %.0f mm' % (wt(n) / 2, wt(n))
            elif (n, 키) in 사면폭:
                out['절점'][열쇠] = round(사면폭[(n, 키)]); out['식'][열쇠] = 식[(n, 키)]
    for 이름, a, b, 종 in m['부재']:
        if 종 != '스트럿':
            continue
        끝 = [사면폭[(n, 이름)] for n in (a, b) if (n, 이름) in 사면폭]
        끝식 = ['절점 %s : %s' % (n, 식[(n, 이름)]) for n in (a, b) if (n, 이름) in 식]
        if not 끝 and abs(힘.get(이름, 0)) > 1e-6 and abs(_끝(m, a, a, b)[1]) < 1e-6 * max(_끝(m, a, a, b)[2], 1):
            끝 = [wt(a), wt(b)]
            끝식 = ['절점 %s : wt = %.0f mm' % (n, wt(n)) for n in (a, b)]
        if 끝:
            out['스트럿'][이름] = round(min(끝))
            판없는 = [n for n in (a, b) if (n, 이름) not in 사면폭 and abs(_끝(m, a, a, b)[1]) >= 1e-6 * max(_끝(m, a, a, b)[2], 1)]
            out['식'][이름] = ('양 끝 경계면 중 작은 값 = min(%s) = %.0f mm' if len(끝) > 1 else '판 있는 끝의 경계면 = %s = %.0f mm') % (' , '.join('%.0f' % x for x in 끝), min(끝)) + (' (%s)' % ' / '.join(끝식) if 끝식 else '') + (' · 절점 %s 는 판이 없어 제안 없음 (설계자 확인)' % ' · '.join(판없는) if 판없는 else '')
    return out
