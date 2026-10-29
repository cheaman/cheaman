# -*- coding: utf-8 -*-
"""자리잡기 — 숫자 표(주석규칙.json) 대로 치수선 단을 줄이고(셋째 → 지시선) 겹친 글을 비켜 「규칙 판」 을 만든다.
v0.1 · 2026-10-29 · 4_캐드도면규칙 / 2_실행기 / 엔진
원칙 : 원본은 읽기만 · 규칙 판은 새 파일 · 후보마다 까닭(규칙 이름) · 못 푼 것은 목록으로 남김 (지어서 옮기지 않음)
[ 구역 지도 ]  1. 숫자 표 만들기   2. 치수 단 줄이기   3. 겹친 글 비키기   4. 한 번에 (규칙판만들기)"""
import os, io, json, math
import ezdxf
from ezdxf.math import Vec2
from ezdxf.enums import TextEntityAlignment
from . import 도면읽기

기본표 = {"치수선.단수_최대": 2, "치수선.단_간격": 400, "치수선.첫단_띄움": 500, "글자.높이": 125, "지시선.각": 45, "지시선.글_쪽": "R", "비킴_차례": ["위", "옆", "지시선"], "출력배율": 50}

# ───────────────────────── 1. 숫자 표 ─────────────────────────
def 숫자표만들기(자료목록, 설정, 규칙목록):
    """○ 받은 규칙이 있는 도면 자료들의 센 숫자(중앙값)로 숫자 표를 만든다. 없으면 기본값. 출처를 같이 적는다."""
    표 = dict(기본표); 출처 = {}
    표["출력배율"] = 설정.get("출력배율", 50)
    값들 = {}
    for a in 자료목록:
        if not a.get("숫자"): continue
        for k in ("치수선.단_간격", "치수선.첫단_띄움", "글자.높이", "지시선.각"):
            v = a["숫자"].get(k, {}).get("값")
            if isinstance(v, (int, float)) and v: 값들.setdefault(k, []).append(v)
    for k, vs in 값들.items():
        표[k] = 도면읽기._중앙(vs); 출처[k] = "도면 %d벌 중앙값" % len(vs)
    for r in 규칙목록:                                    # ○ 받은 글 규칙에서 단 수를 읽음 (「2단」 「3단」)
        if r["상태"] not in ("○ 받음", "올림"): continue
        import re
        m = re.search(r"(\d)단까지", r["글"])
        if m: 표["치수선.단수_최대"] = int(m.group(1)); 출처["치수선.단수_최대"] = "규칙 %d" % r["번호"]
    표["_출처"] = 출처; return 표

# ───────────────────────── 2. 치수 단 줄이기 ─────────────────────────
def _기준묶음(doc, 틈=0.5):
    """같은 방향 · 같은 기준선 치수를 묶고, 묶음 안에서 띄움 순으로 (dim, 띄움) 목록."""
    묶 = {}
    for d in doc.modelspace().query("DIMENSION"):
        if d.dimtype not in (0, 1): continue
        p2, p3, pl = Vec2(d.dxf.defpoint2), Vec2(d.dxf.defpoint3), Vec2(d.dxf.defpoint)
        if abs(p2.y - p3.y) <= 틈: k = ("가로", round(p2.y / (틈 * 4))); 띄움 = abs(pl.y - p2.y); 쪽 = -1 if pl.y < p2.y else 1
        elif abs(p2.x - p3.x) <= 틈: k = ("세로", round(p2.x / (틈 * 4))); 띄움 = abs(pl.x - p2.x); 쪽 = -1 if pl.x < p2.x else 1
        else: continue
        묶.setdefault(k, []).append((d, 띄움, 쪽))
    for k in 묶: 묶[k].sort(key=lambda x: x[1])
    return 묶

def 단줄이기(doc, 표):
    """단수_최대를 넘는 바깥 단 치수를 지시선 + 글로 바꾼다. 돌려주는 것 : 후보 목록."""
    후보 = []; msp = doc.modelspace(); h = float(표["글자.높이"]); 각 = math.radians(float(표["지시선.각"]))
    for k, 줄 in _기준묶음(doc).items():
        단 = []
        for d, 띄움, 쪽 in 줄:
            if 단 and abs(띄움 - 단[-1][0]) <= 1.0: 단[-1][1].append(d)
            else: 단.append([띄움, [d]])
        while len(단) > int(표["치수선.단수_최대"]):
            띄움, dims = 단.pop()                           # 가장 바깥 단
            for d in dims:
                p2, p3 = Vec2(d.dxf.defpoint2), Vec2(d.dxf.defpoint3)
                try: 값 = d.get_measurement()
                except Exception: 값 = (p3 - p2).magnitude
                시작 = p3 if p3.x >= p2.x else p2             # 오른쪽 끝에서
                꺾 = 시작 + Vec2(math.cos(각), math.sin(각)) * (h * 4); 끝 = 꺾 + Vec2(h * 4, 0)
                msp.add_leader([(시작.x, 시작.y), (꺾.x, 꺾.y), (끝.x, 끝.y)], dxfattribs={"layer": d.dxf.layer})
                msp.add_text("W=%d" % round(값), height=h, dxfattribs={"layer": d.dxf.layer}).set_placement((꺾.x + h * 0.2, 꺾.y + h * 0.3), align=TextEntityAlignment.LEFT)
                후보.append({"종류": "3단 → 지시선", "핸들": d.dxf.handle, "값": round(값), "자리": [round(꺾.x), round(꺾.y)], "까닭": "치수선.단수_최대 %s 를 넘는 바깥 단" % 표["치수선.단수_최대"]})
                msp.delete_entity(d)
    return 후보

# ───────────────────────── 3. 겹친 글 비키기 ─────────────────────────
def _겹침쌍(doc):
    상자 = 도면읽기._글상자들(doc); 쌍 = []
    for i in range(len(상자)):
        for j in range(i + 1, len(상자)):
            a, b = 상자[i][3], 상자[j][3]
            if min(a[2], b[2]) > max(a[0], b[0]) and min(a[3], b[3]) > max(a[1], b[1]): 쌍.append((상자[i], 상자[j]))
    return 쌍

def 글비키기(doc, 표, 되풀이=4):
    """겹친 쌍마다 「글」(TEXT) 쪽을 비킴_차례(위 → 옆)로 옮겨 본다. 다 안 되면 「지시선 필요」 로 남긴다."""
    후보 = []; msp = doc.modelspace(); h = float(표["글자.높이"])
    for _ in range(되풀이):
        쌍 = _겹침쌍(doc)
        if not 쌍: break
        움직임 = False
        for a, b in 쌍:
            글 = a if a[0] == "글" else b if b[0] == "글" else None
            if 글 is None: continue
            e = msp.get_entity_by_handle(글[1]) if hasattr(msp, "get_entity_by_handle") else doc.entitydb.get(글[1])
            if e is None or e.dxftype() != "TEXT": continue
            원 = Vec2(e.dxf.insert); 됐나 = False
            for 차례 in 표["비킴_차례"]:
                if 차례 == "위": 새 = 원 + Vec2(0, h * 1.6)
                elif 차례 == "옆": 폭 = 글[3][2] - 글[3][0]; 새 = 원 + Vec2(폭 + h, 0)
                else: break
                e.dxf.insert = (새.x, 새.y, 0)
                if hasattr(e.dxf, "align_point") and e.dxf.hasattr("align_point"): e.dxf.align_point = (새.x, 새.y, 0)
                if not any(글[1] in (x[1], y[1]) for x, y in _겹침쌍(doc)):
                    후보.append({"종류": "글 비킴 (%s)" % 차례, "핸들": 글[1], "글": 글[2], "자리": [round(새.x), round(새.y)], "까닭": "「%s」 과 겹침 → 비킴_차례 %s" % ((b if 글 is a else a)[2], 차례)}); 됐나 = True; 움직임 = True; break
                e.dxf.insert = (원.x, 원.y, 0)
            if not 됐나: 후보.append({"종류": "못 비킴 · 지시선 필요", "핸들": 글[1], "글": 글[2], "자리": [round(원.x), round(원.y)], "까닭": "위 · 옆으로도 겹침이 남음 — 사람이 정함"})
        if not 움직임: break
    return 후보

# ───────────────────────── 4. 한 번에 ─────────────────────────
def 규칙판만들기(원본경로, 표, 출력경로):
    """원본 DXF 를 읽어 규칙 판을 새 파일로. 돌려주는 것 : 후보 목록 · 남은 겹침 수 · 단 수."""
    doc = ezdxf.readfile(원본경로)
    후보 = 단줄이기(doc, 표) + 글비키기(doc, 표)
    os.makedirs(os.path.dirname(출력경로), exist_ok=True); doc.saveas(출력경로)
    d2 = ezdxf.readfile(출력경로)
    return {"후보": 후보, "겹침": 도면읽기.겹침세기(d2)["겹침수"], "단수": 도면읽기.숫자세기(d2)["숫자"]["치수선.단수_최대"]["값"], "경로": 출력경로}
