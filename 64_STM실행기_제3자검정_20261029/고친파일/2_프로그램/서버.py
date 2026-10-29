# -*- coding: utf-8 -*-
r"""
64 STM 검토기 — 화면 뒤 서버                    v0.1.0 · 만든 날 2026-10-25 밤 · 64번 폴더

  화면(1_화면\STM검토기.html)이 부르는 창구. 이 PC 에서만, 이 실행기 화면에서만 받는다.
  셈은 전부 파이썬 (2_프로그램\셈\) · 화면 JS 는 그리기만 — 02_짜임.md 틀 B

  가져온 곳 : 53 구조도 3_실행기\서버.py v0.15 뼈대 (살아있나 · 숨 · 지킴이 30분 · 열쇠 X-Tool · 끄기)

  주소 : http://127.0.0.1:38775/        (도구지도 포트 표에 적을 것 · 시험은 38776)
  기록 : _기록\서버기록.txt
  시험 : python 서버.py --포트 38776 --기록 <임시폴더> --과업 <임시폴더>

  창구 (02_짜임 3-1)
    GET  /api/살아있나          도구 이름 · 판
    GET  /api/예제              3_자료\예제\*.stm.json 목록
    GET  /api/열기?이름=        예제 · 과업 파일 하나 (이름 없으면 마지막 과업)
    GET  /api/과업목록          3_자료\과업\*.stm.json 목록 · 최근 고친 순 (화면 «과업 열기 ▾»)
    POST /api/조합              받침 표 → 조합 계수 곱 (1.2D + 1.6L) · 합 · 기둥 반력      [KDS 14 20 10 4.2.2 식 (4.2-2)]
    POST /api/기본안            형상 · 받침표 → 기본안 A 삼각 · B 사다리꼴 (절점 · 부재 · 받침 · 하중 · βs · βn 제안 · 힘) — 확정은 사람
    POST /api/풀기              과업 json → 트러스 풀기 + 스트럿 · 타이 · 절점 폭 + 정착 (절점 · 부재가 있을 때)
    POST /api/저장              과업 json → 3_자료\과업\<이름>.stm.json (저절로 저장) · 마지막 과업 기억
    POST /api/폴더열기          과업 폴더를 탐색기로
    POST /api/숨 · /api/끄기    화면 숨 · 끄기 (open_app.ps1 이 새 판으로 바꿀 때)
"""
import argparse
import json
import os
import re
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, unquote, urlparse

if sys.stdout is None:                       # pythonw 로 켜면 출력 자리가 없다 (기억 pythonw-stdout-none)
    sys.stdout = open(os.devnull, 'w', encoding='utf-8')
if sys.stderr is None:
    sys.stderr = open(os.devnull, 'w', encoding='utf-8')

도구 = '64 STM검토기'    # /api/살아있나 에 이 이름 — open_app.ps1 이 «내 서버인가» 를 가린다
판 = 'v0.6.2'            # 고치면 올린다 — 켜는 쪽이 옛 판이면 끄고 새로 켠다 (이 줄 꼴을 바꾸지 말 것 : ps1 이 정규식으로 읽음)
# v0.6.2 (10-29) 제3자 검정 (평가자 둘 · 겹친 지적 6) — 절점영역 면 두께(받침판 가로 · 말뚝 π/4·D · 전엔 늘 b) · 단위 정규화(키 없으면 kN-mm-MPa · 전엔 1000배) · 역부호 = N.G · 종류 미지정 멈춤 · βs 빈 칸 미정 · βs · βn 값 검사 · 1.4D 지배 경고 · 인장 반력 알림 · 경계면 일부만 입력이면 미정 · 정착 l_anc 0 = 검토 · 타이만 · 형태 검사 · 갈고리 β 1.2 · 검토비 1.00 N.G 는 소수 셋째 · 철근 지름 25.0 꼴 · 길이 0 부재 글 · 계산서 자중 · 전단상한 · 기준 이름
# v0.6.1 (10-28 밤) 용어 권고 — 보이는 글만 (부재력 0 · 하중조합 · 절점영역 · 미검토 · 갈고리 90° · 오류 글 꼴) · 계산 값 같음 (예제 · 과업 11벌 숫자 칸 대조 0)
# v0.6.0 (10-28) /api/AI검토 — 단계 ③ AI 칸 · AI다리.py (claude 명령줄 · LM 스튜디오 고르기 · 150초 + 한 번 더 · 같은 물음 기억 _기록\AI기억) · AI 는 짚기만 (등급 · 정해진 손질 이름 · 좌표 X)
# v0.5.8 (10-28) /api/과업목록 — 저절로 저장된 과업을 최근 고친 순으로 (화면 «과업 열기 ▾» · 전무님 «화일 저장기능 · 처음부터 실행?» → 목업 고르심)
# v0.5.9 (10-28) ③ 정착 칸이 빈 타이도 정착 «미정» 한 줄로 셈 — 타이 둘 가운데 하나만 정착을 넣어도 «정착 1 / 1 · 모두 O.K» 로 나오던 것 (걷기 10-27 진짜 1)
# v0.5.7 (10-26 밤) ③ 힘 0 부재 = «생략» 판정 (O.K 셈에서 빼고 계산서에 한 줄 · 전무님 지휘 고르심 «힘 0 — 검토 생략») — 대칭 하중이면 기본안에 힘 0 사재가 남아 판정이 «미입력» 에서 멈추던 것
# v0.5.6 (10-26 밤) ② 기본안 형식 전부 — 깊은보 밖 (코핑 1열 · 다열 · 말뚝캡 · 확대기초 · 코벨) 은 기본안.일반 (띠 삼각분할 · 형상.py 받는 점) · 판길이 → 폭제안 · 안 되는 안은 까닭과 함께 빼고 되는 것만
# v0.5.2 (10-26 아침) βn 이 빈 절점은 닿는 타이 수로 채워 풂 (0 → 1.00 · 1 → 0.80 · 2 이상 → 0.60 · 기본안.py 와 같은 규칙 · KDS 14 20 24 4.4.3(2)) — 전엔 1.00 (고칠거리 가)
# v0.5.1 (10-26 아침) ③ 검토 «폭제안» — 셈\폭제안.py (ACI 318 해설 꼴 · 전무님 고르심 · KDS 본문에 폭 규칙 없음) · 빈 절점면 · 있는 폭 제안만 (판정엔 안 씀) · SP 정답지 판 면 · 정수압 사면 대조
# v0.5.0 (10-26 아침) ② 모델 기본안 — /api/기본안 (기본안.py · 깊은보 A 삼각 · B 사다리꼴 · 하중은 조합셈 · 정답지 깊은보 셋과 같은 모델 · 시험\기본안대조.py) · CLAUDE.md 2절 «제안 → 사람 확정»
# v0.4.2 (10-26 아침) 계산서 표지 (잠정 꼴) — 과업명 · 대상 · 방법 · 조합 · 재료 · 판정 · 날짜 + 작성 · 검토 · 승인 × 성명 · 서명 · 날짜 빈칸 · 과업 json «표지» 칸이 있으면 채움
# v0.4.1 (10-26 아침) 절점면 — 닿는 것이 없어진 면은 빼고 풀고 «왜» 에 알림 · 화면 ③ 절점 탭 면 더하기 · 지우기 · 닿는 것 고르개
# v0.4.0 (10-26 새벽) ④ 계산서 · 도면 — /api/계산서 (출력\계산서글.py HTML · md · 출력\dxf쓰기.py ezdxf) · 저장은 과업폴더\<이름>_출력\ 판 번호 · hwp 는 다음
# v0.3.0 (10-26 새벽) ③ 검토 판 — /api/검토 (풀기 결과를 스트럿 · 타이 · 절점 · 정착 표로 · 비 = 있는/필요 · 식 줄 [조문]은 03_조문표) · 3_자료\철근표.json (대조 전)
# v0.2.0 (10-25 밤) ② 모델 판 — /api/모델검사 (이름 · 길이 · 각도 · 정정/부정정 · 정정이면 풀어 힘 부호로 종류 제안) · 각도 한계는 발췌에 없어 안 재고 각도만 돌려줌
# v0.1.0 (10-25 밤) 첫 판 — ① 형상 · 하중 판 · 조합 · 풀기(정답지 셈 그대로) · 저장 · 열기 · 예제
열쇠 = 'stm-64'          # 화면이 POST 에 붙이는 머리글 값 (ASCII)

여기 = os.path.dirname(os.path.abspath(__file__))          # 2_프로그램
폴더 = os.path.dirname(여기)                                # 64번 폴더
셈폴더 = os.path.join(여기, '셈')
화면폴더 = os.path.join(폴더, '1_화면')
예제폴더 = os.path.join(폴더, '3_자료', '예제')

가 = argparse.ArgumentParser()
가.add_argument('--포트', type=int, default=38775)
가.add_argument('--기록', default=os.path.join(폴더, '_기록'))
가.add_argument('--과업', default=os.path.join(폴더, '3_자료', '과업'))     # 시험은 임시 폴더로
인자 = 가.parse_args()
포트 = 인자.포트
기록파일 = os.path.join(인자.기록, '서버기록.txt')
과업폴더 = 인자.과업
마지막파일 = os.path.join(과업폴더, '_마지막.txt')

sys.path.insert(0, 셈폴더)
import stm_풀이                                              # noqa: E402  셈\stm_풀이.py (정답지 4벌 24/24)
import 기본안                                                # noqa: E402  2_프로그램\기본안.py (규칙으로 모델 제안)
import 정착                                                  # noqa: E402  셈\정착.py   (정답지 8건 19/19)
import 폭제안                                                # noqa: E402  셈\폭제안.py (ACI 318 해설 꼴 · 제안만)
import AI다리                                               # noqa: E402  2_프로그램\AI다리.py (② 모델 짚기 · claude 명령줄)

상태 = {'마지막숨': time.time()}
조합표 = {'1.2D+1.6L': {'D': 1.2, 'L': 1.6, '조문': 'KDS 14 20 10 4.2.2 식 (4.2-2)'},   # 14 발췌 KDS 14 20 10_4.2.2 소요강도(하중조합).md
       '1.4D': {'D': 1.4, 'L': 0.0, '조문': 'KDS 14 20 10 4.2.2 식 (4.2-1)'}}           # 03_조문표 «1.4D 도 검사» — 10-29 검정 : L ≤ D/8 이면 1.4D 가 지배 · 고른 조합보다 큰 받침이 있으면 «경고»
정착열쇠 = ('꼴', '조건', '상부철근', '도막', '피복얇음', 'λ', '소요배근', '피복보정', '띠철근보정', '방법', 'c', 'K_tr')


class 멈춤(Exception):
    """화면에 그대로 보여 줄 말"""


def 적기(s):
    os.makedirs(os.path.dirname(기록파일), exist_ok=True)
    줄 = '%s  %s' % (time.strftime('%Y-%m-%d %H:%M:%S'), s)
    try:
        with open(기록파일, 'a', encoding='utf-8') as f:
            f.write(줄 + '\n')
    except Exception:
        pass
    try:
        print(줄)
    except Exception:
        pass


def _수(v, 기본=0.0):
    try:
        return float(str(v).replace(',', '').strip())
    except (ValueError, TypeError):
        return 기본


def 조합셈(인):
    """받침 표 [{x, D, L, H}] + 조합 이름 → 받침마다 Vu · Hu · 합 · 기둥 반력. 셈은 여기서만 (화면은 뿌리기만)"""
    이름 = 인.get('조합') or '1.2D+1.6L'
    if 이름 not in 조합표:
        raise 멈춤('지원하지 않는 하중조합 «%s» — 지금은 1.2D+1.6L 만' % 이름)
    계수 = 조합표[이름]
    줄 = []
    for i, r in enumerate(인.get('받침') or []):
        D, L, H = _수(r.get('D')), _수(r.get('L')), _수(r.get('H'))
        Vu = 계수['D'] * D + 계수['L'] * L
        Hu = 계수['D'] * H          # 수평력은 고정하중 계수로 (잠정 · 화면에 «잠정» 표시) — 아침에 여쭐 것
        줄.append({'번호': i + 1, 'x': _수(r.get('x')), 'D': D, 'L': L, 'H': H, 'Vu': round(Vu, 1), 'Hu': round(Hu, 1)})
    # 10-29 검정 : 다른 조합이 어느 받침에서든 더 크면 경고 (조합마다 따로 풀어 부재별 최댓값을 쓰는 것은 다음 걸음 — 지금은 고른 조합 하나로 풀고 경고만)
    경고 = []
    for 다른, k in 조합표.items():
        if 다른 == 이름:
            continue
        큰 = [(r['번호'], k['D'] * r['D'] + k['L'] * r['L'], r['Vu']) for r in 줄 if k['D'] * r['D'] + k['L'] * r['L'] > r['Vu'] * 1.005 + 1e-9]
        if 큰:
            경고.append('%s 가 더 큼 — 받침 %s (%s) · 하중조합을 바꿔 다시 검토 [%s]' % (다른, ' · '.join(str(n) for n, _, _ in 큰), ' · '.join('%.1f > %.1f kN' % (a, b) for _, a, b in 큰), k['조문']))
    return {'됨': True, '조합': 이름, '계수': {'D': 계수['D'], 'L': 계수['L']}, '조문': 계수['조문'], '줄': 줄,
            '연직합': round(sum(r['Vu'] for r in 줄), 1), '수평합': round(sum(r['Hu'] for r in 줄), 1),
            '기둥반력': round(sum(r['Vu'] for r in 줄), 1), '경고': 경고}


def 풀기(인):
    """과업 json → 트러스 힘 · 폭 · 정착. 셈은 stm_풀이 · 정착 (정답지와 맞춘 그 코드) — 여기선 부르기만"""
    m = 인.get('과업') or 인
    if not m.get('절점') or not m.get('부재'):
        raise 멈춤('절점 · 부재 없음 — ② 모델에서 입력한 뒤 해석')
    기준 = m.get('기준') or 'KDS'
    if 기준 not in stm_풀이.φ표:
        raise 멈춤('지원하지 않는 기준 «%s»' % 기준)
    # 10-29 검정 — 풀기 앞 입력 검사 한 층 (단위 · 종류 · 재료 · β) : 전엔 단위 키가 없으면 stm_풀이 ×1 · 서버 ×1000 으로 갈려 타이 As · 절점 폭이 1000배 작게 나감
    단위 = m.get('단위') or 'kN-mm-MPa'
    if 단위 not in ('kN-mm-MPa', 'kip-in-ksi'):
        raise 멈춤('지원하지 않는 단위 «%s» — kN-mm-MPa 또는 kip-in-ksi' % 단위)
    m['단위'] = 단위
    미지정 = [p[0] for p in m['부재'] if len(p) < 4 or p[3] not in ('스트럿', '타이')]
    if 미지정:
        raise 멈춤('부재 종류 미지정 : %s — ② 모델에서 스트럿 · 타이 선택' % ' · '.join(str(x) for x in 미지정))
    if '재료' in m and 'fc' not in m['재료'] and 'fck' in m['재료']:
        m['재료'] = dict(m['재료'], fc=m['재료']['fck'])          # .stm.json 은 fck · 옛 예제는 fc
    if not (_수((m.get('재료') or {}).get('fc')) > 0 and _수((m.get('재료') or {}).get('fy')) > 0 and _수(m.get('폭b')) > 0):
        raise 멈춤('재료 fck · fy · 부재 두께 b 는 0 보다 커야 함 — ① 재료 · 치수 확인')
    βs = {}
    for k, v in (m.get('βs') or {}).items():
        if v in (None, ''):
            continue                                          # 빈 칸은 두지 않음 → 셈은 0.75 가정 · 검토는 «미정» (βs 미입력)
        if not (0 < _수(v) <= 1):
            raise 멈춤('βs %s 값 이상 «%s» — 0 초과 1 이하' % (k, v))
        βs[k] = _수(v)
    m['βs'] = βs
    # βn 이 빈 절점 — 닿는 타이 수로 (사람이 고른 값은 그대로 · 검토 · 계산서도 같은 값을 보게 과업에 채움)
    βn = dict(m.get('βn') or {})
    for n in m['절점']:
        if βn.get(n) in (None, ''):
            타이수 = sum(1 for p in m['부재'] if len(p) > 3 and p[3] == '타이' and n in (p[1], p[2]))
            βn[n] = 1.0 if 타이수 == 0 else 0.8 if 타이수 == 1 else 0.6
        elif not (0 < _수(βn[n]) <= 1):
            raise 멈춤('βn %s 값 이상 «%s» — 0 초과 1 이하' % (n, βn[n]))
        else:
            βn[n] = _수(βn[n])
    m['βn'] = βn
    # 절점영역 면 두께 (10-29 검정 : 전엔 늘 부재 두께 b → 받침판 · 말뚝이 b 보다 좁으면 위험 쪽) — 과업에 «절점두께» 가 있으면 그 값 · 없으면 형상에서
    if not m.get('절점두께'):
        m['절점두께'], m['절점두께말'] = 절점두께들(m)
    뺀면 = []
    if m.get('절점면'):
        def 닿음(n, 키):      # 그 절점에 닿는 것만 : 그 절점의 부재 · 그 절점 반력 «R+n+x/y» · 그 절점 하중 «P:n»
            if any(p[0] == 키 and n in (p[1], p[2]) for p in m['부재']):
                return True
            if 키 == 'P:' + n:
                return n in (m.get('하중') or {})
            return 키 in ('R%sx' % n, 'R%sy' % n) and 키[-1] in ((m.get('받침') or {}).get(n) or [])
        남 = {}
        for n, 면들 in m['절점면'].items():
            for 면, 키 in (면들 or {}).items():
                if n in m['절점'] and 닿음(n, str(키)):
                    남.setdefault(n, {})[면] = 키
                else:
                    뺀면.append('%s %s (%s)' % (n, 면, 키))
        m = dict(m, 절점면=남)
    t = time.time()
    try:
        힘, 줄, 폭 = stm_풀이.검토(m, 기준)
    except SystemExit as e:                                   # 부정정 · 불안정 — 대본이 멈춤으로 알림
        raise 멈춤(str(e))
    except (KeyError, ZeroDivisionError, ValueError) as e:
        raise 멈춤('해석 실패 — %s' % e)
    정착들 = {}
    fck = _수((m.get('재료') or {}).get('fc')); fy = _수((m.get('재료') or {}).get('fy'))
    타이들 = {p[0] for p in m['부재'] if p[3] == '타이'}
    for 이름, 설정 in (m.get('정착') or {}).items():
        if 이름 not in 타이들:                                   # 10-29 검정 : 스트럿 이름의 정착은 보지 않음 (전엔 정착표에 줄이 생김)
            continue
        철 = (m.get('철근') or {}).get(이름) or {}
        d_b = _수(철.get('지름'))
        if not d_b or (설정 or {}).get('l_anc') in (None, ''):   # l_anc 0 은 «0 mm 정착» 으로 검토 (전엔 조용히 건너뜀)
            continue
        인자들 = {k: 설정[k] for k in 정착열쇠 if k in 설정}
        try:
            정착들[이름] = 정착.검토(d_b, fy, fck, _수(설정['l_anc']), **인자들)
        except (KeyError, ValueError, TypeError) as e:
            정착들[이름] = {'오류': '정착 검토 실패 — %s' % e}
    큰힘 = max([abs(v) for v in 힘.values()] or [0.0])
    음반력 = {k: round(v, 1) for k, v in 힘.items() if k.startswith('R') and k.endswith('y') and v < -(큰힘 * 1e-4 + 1e-9)}   # 10-29 검정 : 받침 연직 반력이 인장 — 지압 아님
    적기('풀기 %s · 부재 %d · %.2f초' % (m.get('이름', ''), len(m['부재']), time.time() - t))
    return {'됨': True, '기준': 기준, 'φ': dict(zip(('스트럿', '타이', '절점'), stm_풀이.φ표[기준])),
            '힘': {k: round(v, 2) for k, v in 힘.items()}, '줄': 줄, '폭': {k: round(v, 2) for k, v in 폭.items()},
            '정착': 정착들, '뺀면': 뺀면, '음반력': 음반력, '절점두께': m.get('절점두께') or {}, '절점두께말': m.get('절점두께말') or {}, '초': round(time.time() - t, 2)}


def 절점두께들(m):
    """절점영역 면의 두께 {절점: mm} 와 말 {절점: 글} — KDS 14 20 24 4.4.2(1) Fnn = fce·An 의 An 은 «힘이 닿는 면의 면적» (10-29 검정)
    받침판 = 받침판[1] (가로) · 말뚝 = π/4·D 등가 두께 (원형 면적을 지름 길이로 나눈 값) · 기둥 · 지반 토막 · 하중판 = 가로폭 칸이 없어 부재 두께 b (설계자 확인) · b 보다 크지 않게"""
    import math
    형 = m.get('형상') or {}; b = _수(m.get('폭b')); 판표 = m.get('판길이') or {}
    받침판 = 형.get('받침판') or []; 가로 = _수(받침판[1]) if len(받침판) > 1 else 0.0
    하중판가로 = _수(형.get('하중판가로'))
    받 = m.get('받침') or {}; 하 = m.get('하중') or {}
    두께 = {}; 말 = {}
    for n in m['절점']:
        t = None
        if n in 판표:
            판말 = str((list(판표[n]) + [''])[1])
            if '말뚝' in 판말:
                D = _수(판표[n][0]); t = math.pi / 4 * D; 말[n] = '말뚝 원형 단면 π/4·D² ÷ D = %.0f mm 등가 두께' % t
            elif '받침판' in 판말 and 가로:
                t = 가로; 말[n] = '받침판 가로 %.0f mm' % 가로
            else:
                t = b; 말[n] = '%s 가로폭 칸 없음 → 부재 두께 b (설계자 확인)' % (판말 or '판')
        elif 'y' in (받.get(n) or []):
            t = 가로 or b; 말[n] = ('받침판 가로 %.0f mm' % 가로) if 가로 else '받침판 가로 없음 → 부재 두께 b'
        elif n in 하:
            t = 하중판가로 or b; 말[n] = ('하중판 가로 %.0f mm' % 하중판가로) if 하중판가로 else '하중판 가로 없음 → 부재 두께 b (설계자 확인)'
        if t:
            두께[n] = round(min(t, b) if b else t, 1)
    return 두께, 말


def 철근표():
    p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '3_자료', '철근표.json')
    with open(p, encoding='utf-8') as f:
        표 = json.load(f)
    return {k: v for k, v in 표.items() if not k.startswith('_')}, 표.get('_대조', '아직')


def 검토(인):
    """③ 검토 판 — 풀기(stm_풀이 · 정착 그대로) 결과를 표 넷(스트럿 · 타이 · 절점 · 정착)으로 묶고 비 · 판정을 붙인다.
    비 = 있는 / 필요 (1.00 이상 O.K · 1.11 미만 주의) · 있는 폭을 사람이 안 넣은 스트럿 · 절점은 «미정» (KDS 14 20 24 본문에 폭 규칙 없음 → 폭 제안은 ACI 318 해설 꼴 · 셈\폭제안.py)
    제공 폭이 폭 제안 값과 같으면 식 줄에 그 식 · 근거를 한 줄 더함 (사람이 다른 값을 넣으면 안 붙임)
    식 줄의 [조문] 은 _계획\\03_조문표.md 에서 옮김 · 새 강도식 없음"""
    m = 인.get('과업') or 인
    r = 풀기(인)
    힘, 폭, φ, 정착들 = r['힘'], r['폭'], r['φ'], r['정착']
    표, 대조 = 철근표()
    재 = m.get('재료') or {}; fck = _수(재.get('fck', 재.get('fc'))); fy = _수(재.get('fy')); b = _수(m.get('폭b'))
    배 = 1000.0 if m.get('단위', 'kN-mm-MPa') == 'kN-mm-MPa' else 1.0
    βs = m.get('βs') or {}; βn = m.get('βn') or {}; 철근 = m.get('철근') or {}; 스폭 = m.get('스트럿폭') or {}; 절폭 = m.get('절점폭') or {}
    # 힘 0 부재 (10-26 밤 · 전무님 «힘 0 — 검토 생략») : |Fu| ≤ 가장 큰 부재력의 0.01 % → 강도 · 폭 · 정착 검토 대상 아님 · 판정 «생략» · 계산서에 한 줄
    큰힘 = max([abs(v) for v in 힘.values()] or [0.0])
    문턱 = 큰힘 * 1e-4 + 1e-9
    힘0 = [q[0] for q in m['부재'] if abs(힘.get(q[0], 0.0)) <= 문턱]
    생략글 = ' · |Fu| ≈ 0 (가장 큰 부재력의 0.01 % 이하) ∴ 부재력 0 — 검토 생략'
    def 비판정(있는, 필요):
        if 있는 is None or 필요 <= 0:
            return None, '미정'
        비 = 있는 / 필요
        return round(비, 2), 'N.G' if 비 < 1 - 1e-9 else ('주의' if 비 < 1.11 else 'O.K')
    def 비글(있는, 필요, 판):   # 식 줄 · 계산서용 — N.G 인데 둘째 자리에서 1.00 이 되면 셋째 자리까지 (10-29 검정 : «검토비 1.00 ∴ N.G» 로 찍히던 것)
        if 있는 is None or 필요 <= 0:
            return '—'
        비 = 있는 / 필요
        return format(비, ',.3f') if 판 == 'N.G' and round(비, 2) >= 1 else format(비, ',.2f')
    def f1(x, n=1): return format(x, ',.%df' % n)
    두께 = r.get('절점두께') or {}; 두께말 = r.get('절점두께말') or {}; 음반력 = r.get('음반력') or {}
    역부호글 = ' ★ 부재 종류와 부재력 부호가 어긋남 (%s) — ② 모델에서 종류 · 모델 확인 ∴ N.G'
    # 폭 제안 (판정엔 안 씀 · 화면 «빈 칸 제안» 이 빈 칸에만 넣음) — 면 표 = 사람이 넣은 절점면 + 면이 없는 절점은 제안 면
    try:
        제안면 = 폭제안.절점면(m, r['힘'])
        있는면 = {n: f for n, f in (m.get('절점면') or {}).items() if f}
        제안 = 폭제안.폭들(m, r['힘'], dict(제안면, **있는면))
        제안['절점면'] = {n: f for n, f in 제안면.items() if n not in 있는면}
    except Exception as e:      # 제안이 못 돼도 검토는 그대로
        제안 = {'스트럿': {}, '절점': {}, '절점면': {}, '식': {}, '오류': '%s' % e}
    def 폭근거(있는, 열쇠):     # 제공 폭 = 제안 값이면 그 식 (제안 값은 mm 정수로 반올림)
        제 = (제안.get('스트럿') or {}).get(열쇠, (제안.get('절점') or {}).get(열쇠))
        if 있는 is None or 제 is None or abs(있는 - 제) > 0.5 or 열쇠 not in (제안.get('식') or {}):
            return None
        return '  → 제공 폭 %s mm 산정 : %s [ACI 318 해설 방법 · KDS 14 20 24 본문에 제공 폭 규칙 없음]' % (f1(있는), 제안['식'][열쇠])
    스트럿 = []; 타이 = []; 절점 = []; 식줄 = {}
    for 이름, a, c, 종 in m['부재']:
        F = 힘[이름]
        if 종 == '스트럿':
            βs빈 = βs.get(이름) in (None, '')                   # 10-29 검정 : βs 를 안 고르면 «미정» (셈은 0.75 가정값 · 전엔 말없이 0.75)
            bs = 0.75 if βs빈 else _수(βs.get(이름)); fce = 0.85 * bs * fck
            w = -F * 배 / (φ['스트럿'] * fce * b) if fce > 0 and b > 0 else 0.0
            있는 = _수(스폭.get(이름)) if 스폭.get(이름) not in (None, '') else None
            비, 판 = 비판정(있는, w)
            역 = F > 1e-9 and 이름 not in 힘0
            if 이름 in 힘0:
                비, 판 = None, '생략'
            elif 역:                                          # 10-29 검정 : 스트럿인데 인장 → N.G (전엔 소요 폭이 음수라 «미정 · 제공 폭 비어 있음»)
                비, 판 = None, 'N.G'
            elif βs빈 and 판 in ('O.K', '주의'):
                판 = '미정'
            스트럿.append({'이름': 이름, 'Fu': round(-F, 1), 'βs': bs, 'βs미입력': βs빈, 'fce': round(fce, 3), '필요폭': round(w, 1), '있는폭': 있는, '비': 비, '판정': 판, '역부호': F > 1e-9})
            식줄[이름] = [
                '㉮ 유효압축강도 : fce = 0.85·βs·fck = 0.85 × %s × %s = %s MPa [KDS 14 20 24 4.2.2(1) 식 (4.2-2) · βs 4.2.2(2)]' % (bs, f1(fck, 0), f1(fce, 2))
                + (' · βs 미입력 — 0.75 (병모양 · 4.2.3 횡철근 만족) 가정값 · 설계자 선택 필요' if βs빈 else ''),
                ('㉯ 소요 폭 : w = Fu / (φ·fce·b) = %s × 10³ / (%s × %s × %s) = %s mm [KDS 14 20 24 4.2.1(1) 식 (4.2-1) · φ 4.1.3(1)]' % (f1(-F), φ['스트럿'], f1(fce, 2), f1(b, 0), f1(w)) if not 역 else '㉯ 부재력 Fu = %s kN (인장)' % f1(F))
                + (생략글 if 판 == '생략' else 역부호글 % '스트럿인데 인장' if 역 else (' · 제공 폭 %s mm → 검토비 %s ∴ %s' % (f1(있는), 비글(있는, w, 판), 판)) if 있는 is not None else ' · 제공 폭 미입력 ∴ 미정')]
            if 판 != '생략' and not 역 and 폭근거(있는, 이름):
                식줄[이름].append(폭근거(있는, 이름))
        else:
            As필 = 폭.get(이름 + ' As', 0.0)
            철 = 철근.get(이름) or {}; d = 철.get('지름'); n = _수(철.get('개수'))
            try:                                              # 10-29 검정 : 지름 25.0 (float) 도 D25 로 · 표에 없는 지름은 그렇게 적음 (전엔 «미입력» 이라 적음)
                d = int(round(float(str(d).replace('D', '')))) if d not in (None, '') else None
            except (TypeError, ValueError):
                pass
            단면 = 표.get('D%s' % d) if d is not None else None
            As제 = (단면 * n) if 단면 and n else None
            비, 판 = 비판정(As제, As필)
            역 = F < -1e-9 and 이름 not in 힘0
            if 이름 in 힘0:
                비, 판 = None, '생략'
            elif 역:                                          # 타이인데 압축 → N.G
                비, 판 = None, 'N.G'
            정 = 정착들.get(이름)
            타이.append({'이름': 이름, 'Fu': round(F, 1), '지름': d, '개수': n, '제공As': round(As제, 1) if As제 else None, '필요As': round(As필, 1), '비': 비, '판정': 판, '역부호': F < -1e-9,
                        '정착꼴': ((m.get('정착') or {}).get(이름) or {}).get('꼴'), 'l_anc': ((m.get('정착') or {}).get(이름) or {}).get('l_anc'), '정착': 정})
            줄 = [('㉮ 타이 강도 : As,req = Fu / (φ·fy) = %s × 10³ / (%s × %s) = %s mm² [KDS 14 20 24 4.3.1 식 (4.3-1) · φ 4.1.3(1)]' % (f1(F), φ['타이'], f1(fy, 0), f1(As필)) if not 역 else '㉮ 부재력 Fu = %s kN (압축)' % f1(F))
                  + (생략글 if 판 == '생략' else 역부호글 % '타이인데 압축' if 역 else (' · 제공 D%s × %s = %s mm² → 검토비 %s ∴ %s' % (d, f1(n, 0), f1(As제), 비글(As제, As필, 판), 판)) if As제 else (' · 철근표에 없는 규격 D%s ∴ 미정' % d if d is not None and 단면 is None else ' · 철근 규격 · 본수 미입력 ∴ 미정'))]
            if 판 != '생략' and not 역 and 정 and '식줄' in 정:
                줄.append('㉯ 정착 (%s) : ' % {'갈고리90': '갈고리 90°', '갈고리180': '갈고리 180°'}.get(정.get('꼴'), 정.get('꼴') or '') + ' / '.join(정['식줄']) + ' [KDS 14 20 52 (2024-12-30) 4.1.2 · 4.1.5]')
                if 정.get('고칠길'):
                    g = 정['고칠길']; 줄.append('  → 조치 방안 갈고리 90° : ' + ' / '.join(g.get('식줄', [])) + ' ∴ ' + g.get('판정', '') + ' [KDS 14 20 52 4.1.5(2) 식 (4.1-4)]')
            식줄[이름] = 줄
    for 열쇠, w in 폭.items():
        if 열쇠.endswith(' As'):
            continue
        n, 면 = 열쇠.split(' ', 1)
        있는 = _수(절폭.get(열쇠)) if 절폭.get(열쇠) not in (None, '') else None
        비, 판 = 비판정(있는, w)
        bn = _수(βn.get(n, 1.0))
        면힘0 = False
        fce_n = 0.85 * bn * fck
        # 식 줄을 셈(stm_풀이 72~81줄)과 같은 순서로 드러냄 — 면 힘 · 면 강도 = min(절점 fce, 닿는 스트럿 중 작은 βs 의 fce) (StructurePoint 꼴 · 보수적)
        키 = ((m.get('절점면') or {}).get(n) or {}).get(면, '')
        try:
            Fu면 = (sum(_수(v) ** 2 for v in (m.get('하중') or {})[키[2:]]) ** 0.5) if 키.startswith('P:') else abs(힘[키])
        except (KeyError, TypeError):
            Fu면 = None
        if 키 in 힘0 or (Fu면 is not None and Fu면 <= 문턱):
            비, 판 = None, '생략'; 면힘0 = True
        인장면 = 키 in 음반력                                  # 10-29 검정 : 인장 반력 면은 지압 검토 대상이 아님 (전엔 abs 로 O.K)
        if 인장면:
            비, 판 = None, '미정'
        닿는 = [_수(βs.get(q[0], 0.75)) for q in m['부재'] if q[3] == '스트럿' and n in (q[1], q[2])]
        bs면 = min(닿는) if 닿는 else 1.0
        f면 = min(fce_n, 0.85 * bs면 * fck) if m.get('면은작은값', True) else fce_n
        b면 = _수(두께.get(n)) or b
        타이수 = sum(1 for q in m['부재'] if q[3] == '타이' and n in (q[1], q[2]) and q[0] not in 힘0)
        절점.append({'절점': n, '면': 면, '열쇠': 열쇠, 'βn': bn, 'fce': round(f면, 3), 'fce절점': round(fce_n, 3), '면힘': 키, 'Fu': round(Fu면, 1) if Fu면 is not None else None, '필요폭': round(w, 1), '있는폭': 있는, '비': 비, '판정': 판, '두께': b면})
        식 = '㉮ 절점 %s %s (%s) : fce = 0.85·βn·fck = 0.85 × %s × %s = %s MPa [KDS 14 20 24 4.4.3(1) 식 (4.4-2) · βn 4.4.3(2) · 연결 타이 %d개 → %s]' % (n, 면, 키 or '—', bn, f1(fck, 0), f1(fce_n, 2), 타이수, 'C-C-C' if 타이수 == 0 else 'C-C-T' if 타이수 == 1 else 'C-T-T')
        if f면 < fce_n - 1e-9:
            식 += ' · 연결 스트럿 βs %s → 0.85 × %s × %s = %s MPa 가 작아 이 값을 적용 (보수적 · KDS 조문 아님)' % (bs면, bs면, f1(fck, 0), f1(f면, 2))
        if 인장면:
            식 += ' · 반력 %s kN 이 인장 — 받침은 인장을 못 받음 · 기둥 철근(연직 타이)으로 받고 정착 검토 · 지압면 검토 생략 ∴ 미정' % f1(음반력[키])
        else:
            식 += ' · 소요 폭 = Fu / (φ·fce·b면) = %s × 10³ / (%s × %s × %s) = %s mm [4.4.2(1) 식 (4.4-1) · φ 4.1.3(1)%s]' % (f1(Fu면) if Fu면 is not None else '—', φ['절점'], f1(f면, 2), f1(b면, 0), f1(w), (' · 면 두께 b면 = %s' % 두께말[n]) if abs(b면 - b) > 0.5 and n in 두께말 else '')
            식 += (생략글 if 면힘0 else (' · 제공 폭 %s → 검토비 %s ∴ %s' % (f1(있는), 비글(있는, w, 판), 판)) if 있는 is not None else ' · 제공 폭 미입력 ∴ 미정')
        식줄.setdefault('절점 ' + n, []).append(식)
        if not 면힘0 and not 인장면 and 폭근거(있는, 열쇠):
            식줄['절점 ' + n].append(폭근거(있는, 열쇠))
    정착표 = []
    for 이름, 정 in 정착들.items():
        if 이름 in 힘0:
            정착표.append({'이름': 이름, '꼴': 정.get('꼴'), '판정': '생략'}); continue
        if '오류' in 정:
            정착표.append({'이름': 이름, '판정': '미정', '오류': 정['오류']}); continue
        g = 정.get('고칠길')
        정착표.append({'이름': 이름, '꼴': 정.get('꼴'), '있는': 정.get('있는'), '필요': 정.get('필요'), '비': 정.get('비'), '판정': 정.get('판정'),
                    '고칠길': ('갈고리 90° → l_dh %s %s' % (f1(g['필요'], 0), g['판정'])) if g else None})
    if 정착표:                                                # 정착을 하나라도 넣었으면 빈 타이도 한 줄 (미정) — 안 넣은 타이를 O.K 로 보이지 않게
        for t in 타이:
            if t['이름'] not in 정착들:
                정착표.append({'이름': t['이름'], '판정': '생략' if t['이름'] in 힘0 else '미정', '미입력': True})
    def 묶음(줄들):
        n = len(줄들); ng = sum(1 for x in 줄들 if x['판정'] == 'N.G'); 미 = sum(1 for x in 줄들 if x['판정'] == '미정'); 생 = sum(1 for x in 줄들 if x['판정'] == '생략')
        있 = [x for x in 줄들 if x.get('비') is not None]
        최소 = min(있, key=lambda x: x['비']) if 있 else None
        return {'수': n, 'NG': ng, '미정': 미, '생략': 생, 'OK': n - ng - 미 - 생, '최소비': 최소['비'] if 최소 else None, '최소이름': (최소.get('이름') or 최소.get('열쇠')) if 최소 else None}
    요약 = {'스트럿': 묶음(스트럿), '타이': 묶음(타이), '절점': 묶음(절점), '정착': 묶음(정착표)}
    NG = [k for k, v in 요약.items() if v['NG']]; 미정 = [k for k, v in 요약.items() if v['미정']]
    # v0.4.0 : 하나도 재지 않은 칸(절점면 없음 · 타이는 있는데 정착 없음)도 «미정» — 안 잰 것을 O.K 로 보이지 않게 (CLAUDE.md 3절 «강도 + 절점 + 정착 다»)
    안잼 = ([] if 요약['절점']['수'] else ['절점']) + (['정착'] if 요약['타이']['수'] and not 요약['정착']['수'] else [])
    # 10-29 검정 : 경계면을 일부만 입력한 절점 — 닿는 것(방향이 다른 부재 · 반력 · 하중) 수보다 입력한 면이 적으면 «미정» (전엔 넣은 면만 O.K 면 «모두 O.K»)
    import math as _m
    면빠짐 = []
    if 요약['절점']['수']:
        for n in m['절점']:
            방향 = []
            for q in m['부재']:
                if n not in (q[1], q[2]) or q[0] in 힘0:
                    continue
                o = q[2] if q[1] == n else q[1]
                dx, dy = m['절점'][o][0] - m['절점'][n][0], m['절점'][o][1] - m['절점'][n][1]
                L = _m.hypot(dx, dy) or 1.0; u = (abs(dx) / L, abs(dy) / L)
                if not any(abs(u[0] * v[1] - u[1] * v[0]) < 1e-6 for v in 방향):     # 한 줄로 이어지는 부재(AB · BC)는 한 방향
                    방향.append(u)
            닿는수 = len(방향) + (1 if 'y' in ((m.get('받침') or {}).get(n) or []) and abs(힘.get('R%sy' % n, 0)) > 문턱 else 0) + (1 if n in (m.get('하중') or {}) and any(abs(_수(v)) > 1e-9 for v in m['하중'][n]) else 0)
            입력 = len(((m.get('절점면') or {}).get(n) or {}))
            if 닿는수 and 입력 < 닿는수:
                면빠짐.append('절점 %s 경계면 %d/%d' % (n, 입력, 닿는수))
    판정 = 'N.G' if NG else ('미정' if (미정 or 안잼 or 면빠짐 or 음반력) else 'O.K')
    빈것 = {'스트럿': '제공 폭', '타이': '철근', '절점': '제공 폭', '정착': '정착 꼴 · ℓanc'}
    왜 = ('N.G — %s' % ' · '.join('%s %d개소' % ({'절점': '절점영역'}.get(k, k), 요약[k]['NG']) for k in NG)) if NG else (' · '.join(([(' · '.join('%s %d (%s)' % ({'절점': '절점영역'}.get(k, k), 요약[k]['미정'], 빈것[k]) for k in 미정) + ' 값이 비어 있음')] if 미정 else []) + ([('%s 은 미검토 (경계면 · 정착 입력 후 검토)' % ' · '.join({'절점': '절점영역'}.get(k, k) for k in 안잼))] if 안잼 else [])) or '스트럿 · 타이 · 절점영역 · 정착 4개 항목 모두 O.K')
    if 판정 != 'N.G' and 면빠짐:
        왜 = ('%s 은 경계면 일부만 입력 — 미검토 (닿는 것마다 경계면 입력 · 대칭 생략은 설계자 판단)' % ' · '.join(면빠짐)) + ((' · ' + 왜) if 미정 or 안잼 else '')
    if 음반력:
        왜 += ' · ★ 받침 %s 연직 반력 인장 (%s kN) — 받침은 인장을 못 받음 · 기둥 철근(연직 타이)으로 받고 정착 검토 (설계자 확인)' % (' · '.join(k[1:-1] for k in 음반력), ' · '.join('%.0f' % v for v in 음반력.values()))
    역들 = [x['이름'] for x in 스트럿 + 타이 if x.get('역부호') and x['판정'] == 'N.G']
    if 역들:
        왜 += ' · ★ 부재 %s 는 종류와 부재력 부호가 어긋남 — ② 모델 확인' % ' · '.join(역들)
    if 힘0:
        왜 += ' · 부재력 0 부재 %s 는 검토 생략' % ' · '.join(힘0)
    if r.get('뺀면'):
        왜 += ' · 그 절점과 연결되지 않은 경계면은 제외 : ' + ' / '.join(r['뺀면'])
    return {'됨': True, '판정': 판정, '왜': 왜, '요약': 요약, '폭제안': 제안, '스트럿': 스트럿, '타이': 타이, '절점': 절점, '정착표': 정착표, '식줄': 식줄, '힘0': 힘0,
            '힘': 힘, 'φ': φ, '기준': r['기준'], '철근표': 표, '철근표대조': 대조, '조합': m.get('조합'), '음반력': 음반력, '면빠짐': 면빠짐, '절점두께': 두께, '초': r['초']}


def PDF찍기(html, pdf):
    """이 PC 크롬(설치 없음)을 머리 없이 띄워 계산서 HTML 을 A4 PDF 로 — 크롬이 없으면 HTML 만 남기고 까닭을 돌려줌"""
    import pathlib, tempfile
    후보 = [os.path.join(os.environ.get(k, ''), r'Google\Chrome\Application\chrome.exe') for k in ('ProgramFiles', 'ProgramFiles(x86)', 'LOCALAPPDATA')]
    크롬 = next((c for c in 후보 if os.path.isfile(c)), None)
    if not 크롬:
        return {'pdf': None, 'pdf오류': '찾기 실패 — 크롬 없음 → 계산서 HTML 을 열어 인쇄(PDF)'}
    방 = tempfile.mkdtemp(prefix='stm64크롬_')
    try:
        subprocess.run([크롬, '--headless=new', '--disable-gpu', '--no-pdf-header-footer', '--user-data-dir=' + 방, '--print-to-pdf=' + pdf, pathlib.Path(html).as_uri()],
                       timeout=90, capture_output=True, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    except Exception as e:
        return {'pdf': None, 'pdf오류': '%s' % e}
    return {'pdf': pdf} if os.path.isfile(pdf) and os.path.getsize(pdf) > 1000 else {'pdf': None, 'pdf오류': 'PDF 저장 실패'}


def 계산서(인):
    """④ 계산서 · 도면 — 검토 결과를 2_프로그램\\출력\\계산서글.py 로 HTML · 글(md)로 · 저장이면 과업폴더\\<이름>_출력\\ 에 판 번호 붙여 html · md · dxf"""
    m = 인.get('과업') or 인
    출력폴더 = os.path.join(os.path.dirname(os.path.abspath(__file__)), '출력')
    if 출력폴더 not in sys.path:
        sys.path.insert(0, 출력폴더)
    import 계산서글
    검 = 검토(인)
    조합 = None
    if m.get('받침표'):
        try:
            조합 = 조합셈({'받침': m['받침표'], '조합': m.get('조합')})
        except 멈춤:
            조합 = None
    글 = 계산서글.만들기(m, 검, 조합, 판, 인.get('화면판', ''))
    대조 = []
    for k, v in (m.get('기대') or {}).items():
        있 = 검['힘'].get(k)
        if 있 is not None:
            차 = abs(abs(있) - abs(_수(v))) / max(abs(_수(v)), 1e-9) * 100
            대조.append({'무엇': k, '기대': v, '셈': 있, '차%': round(차, 2), '같음': 차 <= 0.6})
    for k, v in (m.get('기대_폭') or {}).items():
        t = next((x for x in 검['타이'] if k.startswith(x['이름'])), None)
        if t:
            차 = abs(t['필요As'] - _수(v)) / max(abs(_수(v)), 1e-9) * 100
            대조.append({'무엇': k, '기대': v, '셈': t['필요As'], '차%': round(차, 2), '같음': 차 <= 0.6})
    결과 = {'됨': True, '절': 글['절'], 'HTML': 글['HTML'], '글': 글['글'], '판정': 검['판정'], '왜': 검['왜'], '요약': 검['요약'], '힘': 검['힘'], '대조': 대조, '경로들': None}
    if 인.get('저장'):
        이름 = 안전이름(m.get('이름')); 방 = os.path.join(과업폴더, 이름 + '_출력'); os.makedirs(방, exist_ok=True)
        n = 1
        while os.path.exists(os.path.join(방, '계산서_v%d.html' % n)):
            n += 1
        낼것 = set(인.get('낼것') or ['html', 'pdf', 'md', 'dxf'])
        경로들 = {'폴더': 방, '판번호': n}
        html = os.path.join(방, '계산서_v%d.html' % n)
        with open(html, 'w', encoding='utf-8') as f:          # PDF 는 이 HTML 을 인쇄하므로 늘 씀
            f.write(글['HTML'])
        경로들['html'] = html
        if 'md' in 낼것:
            경로들['md'] = os.path.join(방, '계산서_v%d.md' % n)
            with open(경로들['md'], 'w', encoding='utf-8') as f:
                f.write(글['글'])
        if 'pdf' in 낼것:
            경로들.update(PDF찍기(html, os.path.join(방, '계산서_v%d.pdf' % n)))
        if 'dxf' in 낼것:
            try:
                import dxf쓰기
                경로들['dxf'] = os.path.join(방, '모델도_v%d.dxf' % n)
                경로들['dxf정보'] = dxf쓰기.쓰기(m, 검, 경로들['dxf'], 판)
            except Exception as e:                               # ezdxf 가 없거나 형상이 모자라도 계산서는 남긴다
                경로들['dxf'] = None; 경로들['dxf오류'] = '%s' % e
        적기('계산서 저장 %s v%d' % (이름, n))
        결과['경로들'] = 경로들
    return 결과


def 기본안받기(인):
    """② 모델 기본안 — 형상 · 받침표(하중 자리)에서 규칙으로 그린 모델 둘 (A 삼각 · B 사다리꼴) · 하중은 조합셈 계수하중"""
    m = 인.get('과업') or 인
    형 = m.get('형상') or {}
    조 = 조합셈({'받침': m.get('받침표') or [], '조합': m.get('조합')})
    하중들 = [{'x': r['x'], 'Vu': r['Vu'], 'Hu': r['Hu']} for r in 조['줄']]
    깊은 = (형.get('꼴') or '깊은보') == '깊은보'
    안들 = []; 빠짐 = []
    for 안 in ('A', 'B'):
        try:
            안들.append(기본안.깊은보(형, 하중들, 안) if 깊은 else 기본안.일반(형, 하중들, 안))
        except (기본안.안됨, SystemExit, ZeroDivisionError, ValueError, KeyError, TypeError) as e:     # 10-29 검정 : 전엔 ZeroDivisionError 가 «서버 오류» 로
            if 깊은 or 안 == 'A':
                return {'됨': False, '까닭': str(e)}
            빠짐.append('%s — %s' % (안, e))
    return {'됨': True, '안': 안들, '조합': 조['조합'], '권함': 'A', '빠짐': 빠짐}


def 모델검사(인):
    """② 모델 판 — 절점 · 부재 표를 검사만 한다 (모델을 만들지 않음 · tool-human-gives 규칙)
    이름 · 없는 절점 · 길이 0 · 각도 · 정정/부정정 (식 2n 과 모름 m+r) · 정정이면 stm_풀이.풀기 로 힘 → 부호로 종류 제안 · 종류와 어긋나면 ★
    사재 최소 각도 한계는 KDS 발췌에 아직 없어(03_조문표 «아직 없는 것») 재지 않고 각도만 돌려줌"""
    import math
    m = 인.get('과업') or 인
    점 = m.get('절점') or {}; 부 = m.get('부재') or []; 받 = m.get('받침') or {}; 하 = m.get('하중') or {}
    문제 = []; 부재들 = []; 이름들 = set()
    for p in 부:
        if not isinstance(p, (list, tuple)) or len(p) < 4:
            문제.append('부재 줄 형식 오류 — 4칸(이름 · i · j · 종류)이 아님 : %s' % (p,)); continue
        이름, a, b, 종 = p[:4]
        if 이름 in 이름들:
            문제.append('부재 이름 중복 %s' % 이름)
        이름들.add(이름)
        if a not in 점 or b not in 점:
            문제.append('부재 %s 의 절점 %s 이 없음' % (이름, a if a not in 점 else b)); continue
        if a == b:
            문제.append('부재 %s 의 두 끝이 같은 절점' % 이름); continue
        dx, dy = 점[b][0] - 점[a][0], 점[b][1] - 점[a][1]
        L = math.hypot(dx, dy)
        if L < 1e-9:
            문제.append('부재 %s 길이 0' % 이름); continue
        각 = abs(math.degrees(math.atan2(dy, dx))) % 180.0
        부재들.append({'이름': 이름, 'i': a, 'j': b, '종류': 종, '길이': round(L, 1), '각도': round(min(각, 180.0 - 각), 1)})
    for n in 받:
        if n not in 점:
            문제.append('받침 절점 %s 이 없음' % n)
    for n in 하:
        if n not in 점:
            문제.append('하중 절점 %s 이 없음' % n)
    n절 = len(점); m부 = len(부재들); r = sum(len(ds) for n, ds in 받.items() if n in 점)
    식 = 2 * n절; 모름 = m부 + r
    정정 = '정정' if 식 == 모름 else ('부정정 %d차 — 강성법 미지원 (다음 버전)' % (모름 - 식) if 모름 > 식 else '방정식 수 %d > 미지수 %d — 불안정 구조 (이 하중에서만 평형 · 해석으로 확인)' % (식, 모름))
    힘 = None; 평형 = None
    if not 문제 and 점 and 부재들 and 식 >= 모름:
        try:
            힘 = stm_풀이.풀기({'절점': 점, '부재': [[b['이름'], b['i'], b['j'], b['종류']] for b in 부재들], '받침': 받, '하중': 하})
            평형 = True
            for b in 부재들:
                F = 힘[b['이름']]; b['힘'] = round(F, 2)
                b['제안'] = '타이' if F > 1e-9 else '스트럿' if F < -1e-9 else '힘 0'
                b['검사'] = '' if b['종류'] == b['제안'] or b['제안'] == '힘 0' else ('★ %s 인데 %s' % (b['종류'], '인장' if F > 0 else '압축'))
        except SystemExit as e:
            평형 = False; 문제.append(str(e))
    return {'됨': True, '문제': 문제, '부재': 부재들, '절점수': n절, '부재수': m부, '반력수': r, '식': 식, '모름': 모름, '정정': 정정, '평형': 평형,
            '힘': {k: round(v, 2) for k, v in 힘.items()} if 힘 else None,
            '메모': '사재 최소 각도 한계는 KDS 발췌에 아직 없어 각도만 보임 (03_조문표 «아직 없는 것»)'}


def AI검토(인):
    """② 모델 AI 짚기 — 모델검사 결과 · 기본안 A · B 요약을 붙여 묻고 정해진 꼴로 거름 · 못 받으면 묻는 글을 돌려줌"""
    m = 인.get('과업') or 인
    if not m.get('절점') or not m.get('부재'):
        raise 멈춤('모델 없음 — ② 기본안을 고르거나 절점 · 부재를 입력한 뒤 묻기')
    if 인.get('답글'):                                       # 다른 창에 물어 받은 답을 붙여 넣음 — 같은 거르기
        try:
            답 = AI다리.json뽑기(인['답글'])
        except ValueError as e:
            raise 멈춤('붙여 넣은 답을 JSON 으로 못 읽음 — %s' % e)
        적기('AI검토 %s · 붙여 넣음' % m.get('이름', ''))
        return {'됨': True, 'AI': '붙여 넣음', '초': None, '때': time.strftime('%Y-%m-%d %H:%M'), '기억': False,
                '지문': AI다리.모델지문(m), '답': AI다리.답거르기(답, m)}
    검사 = 모델검사({'과업': m})
    안들 = {}
    try:
        b = 기본안받기({'과업': m})
        for a in b.get('안') or []:
            안들[a.get('안', '')] = {'이름': a.get('이름'), '절점수': a.get('절점수'), '부재수': a.get('부재수'), '사재최소각': a.get('사재최소각')}
    except Exception as e:                                   # 기본안을 못 그려도 묻기는 함
        안들 = {'못 그림': str(e)[:80]}
    물음 = AI다리.모델물음(m, 검사, 안들)
    r = AI다리.묻기(물음, AI=인.get('AI') or 'claude', 기억=os.path.join(인자.기록, 'AI기억'), 새로=bool(인.get('새로')))
    적기('AI검토 %s · %s · %s' % (m.get('이름', ''), r.get('AI'), ('%s초%s' % (r.get('초'), ' (기억)' if r.get('기억') else '')) if r.get('ok') else r.get('까닭')))
    if not r.get('ok'):
        return {'됨': False, '까닭': r.get('까닭'), '글': r.get('글'), 'AI': r.get('AI')}
    return {'됨': True, 'AI': r['AI'], '초': r.get('초'), '때': r.get('때'), '기억': r.get('기억'), '지문': AI다리.모델지문(m), '답': AI다리.답거르기(r['답'], m)}


def 안전이름(s):
    s = re.sub(r'[\\/:*?"<>|]+', ' ', str(s or '')).strip()
    return s[:80] or '이름없음'


def 저장(인):
    m = 인.get('과업')
    if not isinstance(m, dict):
        raise 멈춤('저장할 과업이 없음')
    이름 = 안전이름(인.get('이름') or m.get('이름'))
    os.makedirs(과업폴더, exist_ok=True)
    경로 = os.path.join(과업폴더, 이름 + '.stm.json')
    m.setdefault('판', {})
    m['판'].update({'저장판': 판, '마지막': time.strftime('%Y-%m-%d %H:%M')})
    with open(경로, 'w', encoding='utf-8') as f:
        json.dump(m, f, ensure_ascii=False, indent=1)
    with open(마지막파일, 'w', encoding='utf-8') as f:
        f.write(경로)
    return {'됨': True, '경로': 경로, '때': m['판']['마지막']}


def 예제목록():
    줄 = []
    if os.path.isdir(예제폴더):
        for n in sorted(os.listdir(예제폴더)):
            if n.endswith('.stm.json'):
                try:
                    with open(os.path.join(예제폴더, n), encoding='utf-8') as f:
                        m = json.load(f)
                    줄.append({'파일': n, '이름': m.get('이름', n), '꼴': (m.get('형상') or {}).get('꼴', '')})
                except Exception as e:
                    줄.append({'파일': n, '이름': n, '오류': str(e)})
    return {'됨': True, '예제': 줄}


def 과업목록():
    줄 = []
    if os.path.isdir(과업폴더):
        for n in os.listdir(과업폴더):
            if not n.endswith('.stm.json'):
                continue
            p = os.path.join(과업폴더, n)
            t = os.path.getmtime(p)
            try:
                with open(p, encoding='utf-8') as f:
                    m = json.load(f)
                줄.append({'파일': n, '이름': m.get('이름') or n[:-9], '꼴': (m.get('형상') or {}).get('꼴', ''), '때': time.strftime('%Y-%m-%d %H:%M', time.localtime(t)), '_t': t})
            except Exception as e:
                줄.append({'파일': n, '이름': n[:-9], '오류': str(e), '때': time.strftime('%Y-%m-%d %H:%M', time.localtime(t)), '_t': t})
    줄.sort(key=lambda x: -x['_t'])
    for x in 줄:
        del x['_t']
    지금 = ''
    if os.path.isfile(마지막파일):
        with open(마지막파일, encoding='utf-8') as f:
            지금 = os.path.basename(f.read().strip())
    return {'됨': True, '과업': 줄, '지금': 지금}


def 열기(이름):
    """이름 = 예제 파일 이름(.stm.json) · 과업 이름 · 빈칸 = 마지막 과업"""
    if 이름:
        후보 = [os.path.join(예제폴더, 이름), os.path.join(과업폴더, 이름),
              os.path.join(과업폴더, 이름 + '.stm.json'), os.path.join(예제폴더, 이름 + '.stm.json')]
    else:
        if not os.path.isfile(마지막파일):
            return {'됨': False, '까닭': '마지막 과업 없음'}
        with open(마지막파일, encoding='utf-8') as f:
            후보 = [f.read().strip()]
    for p in 후보:
        p = os.path.normpath(p)
        if os.path.isfile(p) and (p.startswith(os.path.normpath(예제폴더)) or p.startswith(os.path.normpath(과업폴더))):
            with open(p, encoding='utf-8') as f:
                return {'됨': True, '경로': p, '과업': json.load(f), '예제': p.startswith(os.path.normpath(예제폴더))}
    return {'됨': False, '까닭': '열기 실패 — 파일 없음 : %s' % 이름}


def 일하기(길, 인):
    if 길 == '/api/숨':
        return {'ok': True, '판': 판}
    if 길 == '/api/끄기':
        적기('끄기 (화면 단추 · 또는 새 판으로 바꿈)')
        threading.Timer(0.3, lambda: os._exit(0)).start()
        return {'ok': True}
    if 길 == '/api/조합':
        return 조합셈(인)
    if 길 == '/api/풀기':
        return 풀기(인)
    if 길 == '/api/기본안':
        return 기본안받기(인)
    if 길 == '/api/모델검사':
        return 모델검사(인)
    if 길 == '/api/검토':
        return 검토(인)
    if 길 == '/api/AI검토':
        return AI검토(인)
    if 길 == '/api/계산서':
        return 계산서(인)
    if 길 == '/api/출력폴더열기':
        방 = os.path.join(과업폴더, 안전이름((인.get('과업') or {}).get('이름')) + '_출력')
        os.makedirs(방, exist_ok=True)
        subprocess.Popen(['explorer', os.path.normpath(방)])
        return {'ok': True, '폴더': 방}
    if 길 == '/api/저장':
        return 저장(인)
    if 길 == '/api/폴더열기':
        os.makedirs(과업폴더, exist_ok=True)
        subprocess.Popen(['explorer', os.path.normpath(과업폴더)])
        return {'ok': True}
    raise 멈춤('없는 창구 : %s' % 길)


class 손님(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def 보내기(self, 코드, 몸, 종류='application/json; charset=utf-8'):
        if not isinstance(몸, (bytes, bytearray)):
            몸 = json.dumps(몸, ensure_ascii=False).encode('utf-8')
        self.send_response(코드)
        self.send_header('Content-Type', 종류)
        self.send_header('Content-Length', str(len(몸)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(몸)

    def 이PC인가(self):
        return self.client_address[0] in ('127.0.0.1', '::1')

    def do_GET(self):
        if not self.이PC인가():
            return self.보내기(403, {'오류': '이 PC 에서만 씀'})
        u = urlparse(self.path)
        길 = unquote(u.path)
        if 길 == '/api/살아있나':
            return self.보내기(200, {'ok': True, '도구': 도구, '판': 판})
        if 길 == '/api/예제':
            return self.보내기(200, 예제목록())
        if 길 == '/api/과업목록':
            return self.보내기(200, 과업목록())
        if 길 == '/api/열기':
            이름 = parse_qs(u.query).get('이름', [''])[0]
            try:
                return self.보내기(200, 열기(이름))
            except Exception as e:
                return self.보내기(200, {'됨': False, '까닭': str(e)})
        if 길 in ('/', ''):
            길 = '/STM검토기.html'
        p = os.path.normpath(os.path.join(화면폴더, 길.lstrip('/')))        # 화면 폴더 안의 파일만
        if not p.startswith(화면폴더) or not os.path.isfile(p):
            return self.보내기(404, {'오류': '없는 주소'})
        종류 = {'.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8',
              '.css': 'text/css; charset=utf-8', '.woff2': 'font/woff2', '.png': 'image/png',
              '.svg': 'image/svg+xml', '.ico': 'image/x-icon', '.json': 'application/json; charset=utf-8'
              }.get(os.path.splitext(p)[1].lower(), 'application/octet-stream')
        with open(p, 'rb') as f:
            self.보내기(200, f.read(), 종류)

    def do_POST(self):
        if not self.이PC인가() or self.headers.get('X-Tool') != 열쇠:
            return self.보내기(403, {'오류': '이 PC 의 프로그램 화면에서만 부를 수 있습니다'})
        길 = unquote(self.path.split('?')[0])
        상태['마지막숨'] = time.time()
        try:
            n = int(self.headers.get('Content-Length') or 0)
            인 = json.loads(self.rfile.read(n).decode('utf-8') or '{}') if n else {}
            self.보내기(200, 일하기(길, 인))
        except 멈춤 as e:
            self.보내기(200, {'오류': str(e)})
        except Exception as e:
            import traceback
            적기('오류 %s\n%s' % (길, traceback.format_exc()))
            self.보내기(200, {'오류': '서버 오류 → _기록\\서버기록.txt (%s)' % e})


class 혼자쓰는서버(ThreadingHTTPServer):
    allow_reuse_address = False          # 같은 포트에 둘이 뜨지 않게
    daemon_threads = True


def 지킴이():
    """화면이 30분 동안 숨을 안 쉬면(창을 닫음) 스스로 꺼진다"""
    while True:
        time.sleep(60)
        if time.time() - 상태['마지막숨'] > 1800:
            적기('30분 동안 화면이 없음 → 끔')
            os._exit(0)


if __name__ == '__main__':
    적기('켜짐 %s %s · 포트 %d' % (도구, 판, 포트))
    threading.Thread(target=지킴이, daemon=True).start()
    혼자쓰는서버(('127.0.0.1', 포트), 손님).serve_forever()
