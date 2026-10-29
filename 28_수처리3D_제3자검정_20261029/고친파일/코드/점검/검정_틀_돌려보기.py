# -*- coding: utf-8 -*-
"""28 수처리 3D 검정 — 평가자용 «돌려 보는 틀» (읽기만 · 원본 안 고침 · 1_기록 206)
   PYTHONUTF8=1 python 코드\점검\검정_틀_돌려보기.py            → 스크린실 그물로 면하중 · MCT 한 벌 요약
   파이썬 안에서 :  from 틀_돌려보기 import 그물, 설계값, 면하중, 요약, MCT글
"""
import io, json, os, sys, tempfile, copy
뿌리 = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(뿌리, '코드'))
import 하중계산, MCT쓰기                                   # noqa: E402

그물자리 = os.path.join(뿌리, '_시험자료/스크린실/모델링/전채만 테스트/2_해석/그물_모델링.json')


def 그물():
    """스크린실 그물 (절점 1107 · 판 1135 · 설계값 들어 있음) — 매번 새 사본"""
    return json.load(open(그물자리, encoding='utf-8'))


def 설계값(g, **덮을):
    설 = dict(하중계산.기본설계값); 설.update(g.get('설계값') or {}); 설.update(덮을)
    return 설


def 면하중(g, 설):
    """하중계산.면하중만들기 그대로 → {케이스: [{'요소','값','방향'}]} (g['하중알림'] · g['하중근거'] 도 채워짐)"""
    return 하중계산.면하중만들기(g, 설)


def 요약(면):
    """케이스마다 장수 · 방향별 합 (kN/m² · 값은 절점값이면 평균) · 최소 · 최대"""
    out = {}
    for k, v in 면.items():
        d = {}
        for q in v:
            x = q['값']; m = (sum(x) / len(x)) if isinstance(x, list) else x
            r = d.setdefault(q['방향'], {'장': 0, '합': 0.0, '최소': 1e18, '최대': -1e18})
            r['장'] += 1; r['합'] += m; r['최소'] = min(r['최소'], min(x) if isinstance(x, list) else x); r['최대'] = max(r['최대'], max(x) if isinstance(x, list) else x)
        out[k] = {kk: {a: round(b, 3) for a, b in vv.items()} for kk, vv in d.items()}
    return out


def MCT글(g, 설=None):
    """그물 사본 + 설계값 → MCT 글 (임시 파일 · MCT쓰기.쓰기 그대로)"""
    g2 = copy.deepcopy(g)
    if 설 is not None:
        g2['설계값'] = 설
    d = tempfile.mkdtemp(prefix='stm28_')
    src = os.path.join(d, '그물.json'); json.dump(g2, open(src, 'w', encoding='utf-8'), ensure_ascii=False)
    out = os.path.join(d, '낸.mct')
    MCT쓰기.쓰기(src, out)
    return open(out, encoding='cp949', errors='replace').read()


if __name__ == '__main__':
    g = 그물(); 설 = 설계값(g)
    면 = 면하중(g, 설)
    for k, v in 요약(면).items():
        print(k, v)
    print('하중알림', g.get('하중알림'))
    print('하중근거', json.dumps(g.get('하중근거'), ensure_ascii=False)[:400])
    t = MCT글(g, 설)
    print('MCT 줄', t.count('\n'), '| 블록', [b for b in ('*LOADCOMB', '*SPRING', '*CONSTRAINT', '*PRESSURE', '*BNDR-GROUP') if b in t])
