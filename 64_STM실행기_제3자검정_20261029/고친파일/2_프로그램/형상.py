# 부재 형식별 형상 — 외곽 · 절점 줄 높이 · 아래 줄 «받는 점» (기둥 · 말뚝 · 지반 반력 합력)
# 2026-10-26 밤 · 전무님 «전체 유형별 계산 되도록» · 기본안.py · 출력\dxf쓰기.py 가 같이 씀
# 화면 1_화면\STM검토기.html 의 꼴표 · 외곽점() 과 같은 꼴 — 한쪽을 고치면 다른 쪽도
#
# 좌표 : x 왼 끝 0 · y 하면 0 (위 +) · mm · 코핑은 기둥 위 면이 y 0 · 코벨은 기둥 면의 코벨 밑이 y 0
# 받는 점 (기본안이 쓰는 반력 나눔 — 사람 확인 · 손계산 대조 시험\형식별대조.py)
#   코핑 (1열) · 코벨 : 기둥 절점 둘 (기둥 폭 1/4 · 3/4 자리) — 정정이라 반력은 트러스가 셈
#   코핑 (다열)      : 기둥 가운데마다 한 절점 · 기둥 셋 이상이면 연속보 (EI 일정 · 기둥 강체 받침) 반력으로 나눔
#   말뚝캡           : 말뚝마다 한 절점 · 셋 이상이면 강체 캡 R = P/n ± M·x/Σx²
#   확대기초         : 지반 반력 직선 분포 (편심 B/6 넘으면 삼각 · 들뜸) → 토막 합력 (A 둘 · B 넷)

이름 = {'깊은보': '깊은보', '코핑': '교각 코핑 (1열)', '코핑다열': '교각 코핑 (다열)', '말뚝캡': '말뚝캡', '확대기초': '확대기초', '코벨': '코벨'}
칸 = {
    '깊은보': ['TL', 'H', 'b', '지간', '피복상', '피복하'],
    '코핑': ['TL', 'b', 'H1', 'H2', 'L1', 'L4', 'CW', '피복상', '피복하'],
    '코핑다열': ['TL', 'H', 'b', 'CW', '기둥수', '기둥간격', '피복상', '피복하'],
    '말뚝캡': ['TL', 'H', 'b', 'CW', '말뚝수', '말뚝간격', '말뚝지름', '피복상', '피복하'],
    '확대기초': ['TL', 'H', 'b', 'CW', '피복상', '피복하'],
    '코벨': ['TL', 'CW', 'H', 'H1', 'b', '피복상', '피복하'],
}


class 안됨(Exception):
    pass


def _수(f, k, 기본=None):
    v = f.get(k, 기본)
    try:
        return float(str(v).replace(',', ''))
    except (TypeError, ValueError):
        if 기본 is None:
            raise 안됨('형상 «%s» 값이 없음' % k)
        return float(기본)


def 줄자리(TL, n, 간격):
    """가운데 맞춘 같은 간격 n 개 자리"""
    n = int(round(n))
    if n < 1:
        raise 안됨('수가 1 이상이어야 함')
    return [TL / 2 + (k - (n - 1) / 2) * 간격 for k in range(n)]


def 높이(f):
    """몸 윗면 y (모델 좌표)"""
    return _수(f, 'H2') if (f.get('꼴') or '깊은보') == '코핑' else _수(f, 'H')


def 밑면(f, x):
    """그 x 의 몸 밑면 y (코핑 헌치 · 코벨 기울기 · 나머지 0)"""
    꼴 = f.get('꼴') or '깊은보'
    if 꼴 == '코핑':
        TL, H1, H2, CW = _수(f, 'TL'), _수(f, 'H1'), _수(f, 'H2'), _수(f, 'CW')
        cx = TL / 2; 면1 = cx - CW / 2; 면2 = cx + CW / 2
        꺾1 = min(_수(f, 'L1', 면1), 면1); 꺾2 = max(TL - _수(f, 'L4', TL - 면2), 면2)
        끝 = H2 - H1
        if x < 꺾1:
            return 끝 * (1 - x / 꺾1) if 꺾1 > 0 else 0.0
        if x > 꺾2:
            return 끝 * (x - 꺾2) / (TL - 꺾2) if TL > 꺾2 else 0.0
        return 0.0
    if 꼴 == '코벨':
        TL, CW, H, H1 = _수(f, 'TL'), _수(f, 'CW'), _수(f, 'H'), _수(f, 'H1')
        if x <= CW or TL <= CW:
            return 0.0
        return (H - H1) * (x - CW) / (TL - CW)
    return 0.0


def 위y(f):
    return 높이(f) - _수(f, '피복상', 0)


def 아래y(f, x):
    return 밑면(f, x) + _수(f, '피복하', 0)


def 외곽점(f):
    """→ (몸 다각형 [(x, y)], 덧 다각형들 (기둥 · 말뚝), 몸 윗면 y)"""
    꼴 = f.get('꼴') or '깊은보'
    TL = _수(f, 'TL')
    if 꼴 == '코핑':
        H1, H2, CW = _수(f, 'H1'), _수(f, 'H2'), _수(f, 'CW')
        cx = TL / 2; 면1 = cx - CW / 2; 면2 = cx + CW / 2
        꺾1 = min(_수(f, 'L1', 면1), 면1); 꺾2 = max(TL - _수(f, 'L4', TL - 면2), 면2)
        return [(0, H2), (TL, H2), (TL, H2 - H1), (꺾2, 0), (꺾1, 0), (0, H2 - H1)], [[(면1, 0), (면2, 0), (면2, -1000), (면1, -1000)]], H2
    if 꼴 == '코벨':
        CW, H, H1 = _수(f, 'CW'), _수(f, 'H'), _수(f, 'H1')
        return [(CW, 0), (TL, H - H1), (TL, H), (CW, H)], [[(0, -300), (CW, -300), (CW, H + 300), (0, H + 300)]], H
    H = _수(f, 'H')
    몸 = [(0, 0), (TL, 0), (TL, H), (0, H)]
    덧 = []
    if 꼴 == '코핑다열':
        CW = _수(f, 'CW')
        for x in 줄자리(TL, _수(f, '기둥수', 2), _수(f, '기둥간격')):
            덧.append([(x - CW / 2, 0), (x + CW / 2, 0), (x + CW / 2, -800), (x - CW / 2, -800)])
    elif 꼴 in ('말뚝캡', '확대기초'):
        CW = _수(f, 'CW')
        덧.append([(TL / 2 - CW / 2, H), (TL / 2 + CW / 2, H), (TL / 2 + CW / 2, H + 500), (TL / 2 - CW / 2, H + 500)])
        if 꼴 == '말뚝캡':
            D = _수(f, '말뚝지름', 600)
            for x in 줄자리(TL, _수(f, '말뚝수', 2), _수(f, '말뚝간격')):
                덧.append([(x - D / 2, 0), (x + D / 2, 0), (x + D / 2, -800), (x - D / 2, -800)])
    return 몸, 덧, H


def _풀이(A, b):
    """작은 연립방정식 (가우스) — 연속보 반력용"""
    n = len(b); M = [r[:] + [v] for r, v in zip(A, b)]
    for c in range(n):
        p = max(range(c, n), key=lambda i: abs(M[i][c]))
        if abs(M[p][c]) < 1e-14:
            raise 안됨('연속보 반력 셈 실패 (받침 부족)')
        M[c], M[p] = M[p], M[c]
        for i in range(n):
            if i != c and M[i][c]:
                k = M[i][c] / M[c][c]
                M[i] = [a - k * q for a, q in zip(M[i], M[c])]
    return [M[i][n] / M[i][i] for i in range(n)]


def 연속보반력(TL, 받침x, 하중들):
    """EI 일정 연속보 · 받침 연직 고정 · 하중 [(x, Vu 아래 +)] → 받침마다 반력 (위 +)"""
    점 = sorted(set([0.0, float(TL)] + [float(x) for x in 받침x] + [float(x) for x, _ in 하중들]))
    자 = {x: i for i, x in enumerate(점)}; N = 2 * len(점)
    K = [[0.0] * N for _ in range(N)]; F = [0.0] * N
    for a, b in zip(점, 점[1:]):
        L = b - a; i = 자[a] * 2; j = 자[b] * 2
        k = [[12, 6 * L, -12, 6 * L], [6 * L, 4 * L * L, -6 * L, 2 * L * L], [-12, -6 * L, 12, -6 * L], [6 * L, 2 * L * L, -6 * L, 4 * L * L]]
        d = [i, i + 1, j, j + 1]
        for r in range(4):
            for c in range(4):
                K[d[r]][d[c]] += k[r][c] / L ** 3
    for x, V in 하중들:
        F[자[float(x)] * 2] -= float(V)
    묶 = {자[float(x)] * 2 for x in 받침x}
    남 = [i for i in range(N) if i not in 묶]
    u = [0.0] * N
    for i, v in zip(남, _풀이([[K[r][c] for c in 남] for r in 남], [F[r] for r in 남])):
        u[i] = v
    return [sum(K[자[float(x)] * 2][c] * u[c] for c in range(N)) - F[자[float(x)] * 2] for x in 받침x]


def 지반세기(TL, P, e):
    """지반 반력 세기 q(x) (kN/mm · 위 +) — 직선 · 편심 B/6 넘으면 삼각 (들뜸)"""
    B = TL; cx = TL / 2
    if abs(e) >= B / 2:
        raise 안됨('편심 %.0f mm 가 기초 폭 반 (%.0f) 을 넘음 — 전도' % (e, B / 2))
    if abs(e) <= B / 6:
        return (lambda x: P / B + 12 * P * e * (x - cx) / B ** 3), '직선 분포 (e = %.0f ≤ B/6)' % e
    a = 3 * (B / 2 - abs(e)); qm = 2 * P / a
    if e > 0:
        return (lambda x: max(0.0, qm * (1 - (TL - x) / a))), '삼각 분포 · 들뜸 (e = %.0f > B/6 · 닿는 길이 %.0f)' % (e, a)
    return (lambda x: max(0.0, qm * (1 - x / a))), '삼각 분포 · 들뜸 (e = %.0f > B/6 · 닿는 길이 %.0f)' % (e, a)


def 토막합력(q, a, b, n=600):
    """[a, b] 토막의 합력 · 합력 자리 (가운데 점 적분)"""
    h = (b - a) / n; R = 0.0; Rx = 0.0
    for k in range(n):
        x = a + (k + 0.5) * h; w = q(x) * h
        R += w; Rx += w * x
    return R, (Rx / R if R > 1e-12 else (a + b) / 2)


def 받는점(f, 하중들, 안='A'):
    """아래 줄 점 → ([{'x', 'y', 'R' (None = 트러스가 셈 · 수 = 미리 나눈 반력 위 +), '판', '판말'}], 메모 글, 위 덧 절점 x (코벨 정착))"""
    꼴 = f.get('꼴') or '깊은보'
    TL = _수(f, 'TL')
    P = sum(float(r['Vu']) for r in 하중들)
    # 수평력 Hu 의 모멘트 (10-29 검정 : 전엔 빠짐) — 팔 길이 = 위 절점(하중) y − 아래 절점(받는 점) y · 트러스가 보는 것과 같은 팔 · +x 힘이면 오른쪽 받는 점이 더 눌림
    MH = sum(float(r.get('Hu') or 0) * (위y(f) - 아래y(f, float(r['x']))) for r in 하중들)
    점 = []; 메모 = ''; 위덧 = []
    if 꼴 == '코핑':
        CW = _수(f, 'CW')
        for x in (TL / 2 - CW / 4, TL / 2 + CW / 4):
            점.append({'x': x, 'R': None, '판': CW / 2, '판말': '기둥 폭/2'})
        메모 = '기둥 = 받침 절점 둘 (기둥 폭 1/4 · 3/4 자리)'
    elif 꼴 == '코벨':
        CW = _수(f, 'CW')
        for x in (CW / 4, CW * 3 / 4):
            점.append({'x': x, 'R': None, '판': CW / 2, '판말': '기둥 폭/2'})
        위덧 = [CW / 4]
        메모 = '기둥 = 받침 절점 둘 (기둥 폭 1/4 · 3/4) · 위 타이는 기둥 바깥 철근 자리까지 (정착 절점) · 기둥 축력은 모델에 안 넣음'
    elif 꼴 == '코핑다열':
        CW = _수(f, 'CW'); xs = 줄자리(TL, _수(f, '기둥수', 2), _수(f, '기둥간격'))
        if len(xs) < 2:
            raise 안됨('코핑 (다열) 은 기둥 2개 이상')
        R = [None] * len(xs)
        if len(xs) >= 3:
            R = 연속보반력(TL, xs, [(float(r['x']), float(r['Vu'])) for r in 하중들])
            메모 = '기둥 %d 개 — 반력은 연속보 (EI 일정 · 기둥 강체 받침) 로 나눔 : %s kN · 바깥 둘은 받침 · 안쪽은 위로 하중' % (len(xs), ' · '.join('%.0f' % v for v in R))
        else:
            메모 = '기둥 2 개 = 받침 절점 둘 (기둥 가운데)'
        for x, r in zip(xs, R):
            점.append({'x': x, 'R': r, '판': CW, '판말': '기둥 폭'})
    elif 꼴 == '말뚝캡':
        D = _수(f, '말뚝지름', 600); xs = 줄자리(TL, _수(f, '말뚝수', 2), _수(f, '말뚝간격'))
        if len(xs) < 2:
            raise 안됨('말뚝캡 은 단면 방향 말뚝 2개 이상')
        R = [None] * len(xs)
        if len(xs) >= 3:
            가 = sum(xs) / len(xs); M = sum(float(r['Vu']) * (float(r['x']) - 가) for r in 하중들) + MH; Σ = sum((x - 가) ** 2 for x in xs)
            R = [P / len(xs) + M * (x - 가) / Σ for x in xs]
            메모 = '말뚝 %d 개 — 반력은 강체 캡 R = P/n ± M·x/Σx² (M 에 수평력 Hu × 팔 %s kN·m 포함) : %s kN · 바깥 둘은 받침 · 안쪽은 위로 하중' % (len(xs), '%.0f' % (MH / 1000), ' · '.join('%.0f' % v for v in R))
        else:
            메모 = '말뚝 2 개 = 받침 절점 둘 (말뚝 가운데)'
        for x, r in zip(xs, R):
            점.append({'x': x, 'R': r, '판': D, '판말': '말뚝 지름'})
        메모 += ' · 수평력은 왼쪽 말뚝 x 반력으로 (말뚝머리 전단 — 사람 확인)'
    elif 꼴 == '확대기초':
        if P <= 0:
            raise 안됨('기둥 하중 합이 0 이하 — 지반 반력을 못 나눔')
        cx = TL / 2; e = (sum(float(r['Vu']) * (float(r['x']) - cx) for r in 하중들) + MH) / P      # 편심에 수평력 모멘트 포함 (10-29 검정)
        q, 말 = 지반세기(TL, P, e)
        if abs(MH) > 1e-9:
            말 += ' · 편심에 수평력 Hu × 팔 %.0f kN·m 포함' % (MH / 1000)
        끊 = [0, cx, TL] if 안 == 'A' else [0, cx / 2, cx, (cx + TL) / 2, TL]
        합들 = []
        for a, b in zip(끊, 끊[1:]):
            R, xr = 토막합력(q, a, b)
            if R > 1e-6 * P:
                점.append({'x': xr, 'R': R, '판': b - a, '판말': '지반 토막 길이'}); 합들.append(R)
        if len(점) < 2:
            raise 안됨('지반 반력이 한 토막에만 — 편심이 큼 (전도 검토 먼저)')
        if len(점) == 2:
            for p in 점:
                p['R'] = None
        메모 = '지반 반력 %s → 토막 %d 개 합력 (%s kN) · 바깥 둘은 받침 · 안쪽은 위로 하중 · 수평력은 왼쪽 받침 x 반력으로 (저면 마찰 — 사람 확인)' % (말, len(점), ' · '.join('%.0f' % v for v in 합들))
    else:
        raise 안됨('형식 «%s» 의 받는 점 규칙 없음' % 꼴)
    for p in 점:
        p['y'] = 아래y(f, p['x'])
    return 점, 메모, 위덧
