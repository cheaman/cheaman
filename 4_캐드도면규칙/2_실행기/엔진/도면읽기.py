# -*- coding: utf-8 -*-
"""도면읽기 — DXF 를 읽어 숫자를 세고, 겹침을 세고, 그림(SVG)으로 바꾸고, 두 판을 대조한다.
v0.1 · 만든 날 2026-10-29 · 고친 날 2026-10-29 · 4_캐드도면규칙 / 2_실행기 / 엔진

[ 구역 지도 ]
  1. 열기 · DWG → DXF            dxf열기 · dwg를dxf로
  2. 숫자 세기                     숫자세기   — 치수 단 수 · 단 간격 · 글자 높이 · 지시선 각 · 블록
  3. 겹침 세기                     겹침세기   — 글 · 치수 글 · 지시선 글 상자가 서로 겹친 수
  4. 그림                          svg로      — ezdxf 의 SVG 그리기 (matplotlib 없이)
  5. 두 판 대조                    대조       — 옛 판 ↔ 새 판 · 바뀐 객체 수
원칙 : 원본은 읽기만 · 숫자마다 출처(객체 수) 를 붙인다 · 못 읽은 것은 목록으로
"""
import os, sys, math, json, tempfile, subprocess, shutil
import ezdxf
from ezdxf import bbox as _bbox
from ezdxf.math import Vec2

# ───────────────────────── 1. 열기 ─────────────────────────
콘솔후보 = [r"C:\Program Files\Autodesk\AutoCAD LT 2027\accoreconsole.exe",
            r"C:\Program Files\Autodesk\AutoCAD 2027\accoreconsole.exe"]

def dwg를dxf로(dwg경로, 출력폴더):
    """DWG 를 오토캐드 콘솔로 DXF 로 바꾼다 (스킬 cad-drawing-work 2장). 콘솔이 없으면 None 과 까닭."""
    콘솔 = next((c for c in 콘솔후보 if os.path.exists(c)), None)
    if not 콘솔:
        return None, "오토캐드 콘솔(accoreconsole)이 없습니다 — 캐드에서 「다른 이름으로 저장 → DXF」 로 받아 넣으십시오"
    임시 = os.path.join(tempfile.gettempdir(), "dsm_rule_dxf")   # 영문 임시 폴더 (scr 안 한글 경로 함정)
    os.makedirs(임시, exist_ok=True)
    out = os.path.join(임시, "out.dxf")
    scr = os.path.join(임시, "conv.scr")
    with open(scr, "w", encoding="ascii", newline="\r\n") as f:
        f.write('(setvar "FILEDIA" 0)\n(command "_.DXFOUT" "%s" "_V" "_2018" "16")\n' % out.replace("\\", "\\\\"))
    try:
        subprocess.run([콘솔, "/i", dwg경로, "/s", scr, "/l", "en-US"], timeout=180,
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0), capture_output=True)
    except subprocess.TimeoutExpired:
        return None, "콘솔이 3분 안에 끝나지 않았습니다 — DXF 로 저장해 넣으십시오"
    if not os.path.exists(out):
        return None, "콘솔이 DXF 를 만들지 못했습니다 — DXF 로 저장해 넣으십시오"
    목적 = os.path.join(출력폴더, os.path.splitext(os.path.basename(dwg경로))[0] + ".dxf")
    os.makedirs(출력폴더, exist_ok=True); shutil.move(out, 목적)
    return 목적, ""

def dxf열기(경로):
    """DXF 를 연다. 캐드보다 너그럽게 읽으므로 「캐드에서 열리나」 는 따로 본다 (스킬 2장)."""
    return ezdxf.readfile(경로)

# ───────────────────────── 2. 숫자 세기 ─────────────────────────
def _중앙(값들):
    """중앙값 — 짝수면 아래쪽 가운데 (둘이면 작은 쪽)."""
    if not 값들: return 0
    v = sorted(값들); return v[(len(v) - 1) // 2]

def _묶기(값들, 틈):
    """가까운 값끼리 묶어 대표값 목록으로. 틈 안이면 같은 묶음."""
    값들 = sorted(값들); 묶음 = []
    for v in 값들:
        if 묶음 and v - 묶음[-1][-1] <= 틈: 묶음[-1].append(v)
        else: 묶음.append([v])
    return [sum(g) / len(g) for g in 묶음]

def 숫자세기(doc, 틈=0.5):
    """치수 단 수 · 단 사이 간격 · 첫 단 띄움 · 글자 높이 · 지시선 각 · 블록 수를 센다.
    돌려주는 것 : {항목: {값, 출처, 어떻게}} + 못읽음 목록. 단위는 도면 단위(보통 mm · 출력 배율은 설정에서)."""
    msp = doc.modelspace(); r = {}; 못읽음 = []
    # 2-1 치수 : 같은 방향 · 같은 기준선(측정점) 을 가진 치수들의 치수선 띄움을 묶어 단으로
    가로 = {}; 세로 = {}; 글자높이 = []; n치수 = 0
    for d in msp.query("DIMENSION"):
        try:
            if d.dimtype not in (0, 1): continue                     # 선형 치수만
            p2, p3, pl = Vec2(d.dxf.defpoint2), Vec2(d.dxf.defpoint3), Vec2(d.dxf.defpoint)
            n치수 += 1
            if abs(p2.y - p3.y) <= 틈:          # 가로 치수 → 기준 y, 치수선 y
                키 = round(p2.y / (틈 * 4)); 가로.setdefault(키, []).append(abs(pl.y - p2.y))
            elif abs(p2.x - p3.x) <= 틈:        # 세로 치수
                키 = round(p2.x / (틈 * 4)); 세로.setdefault(키, []).append(abs(pl.x - p2.x))
            st = doc.dimstyles.get(d.dxf.dimstyle)
            if st is not None: 글자높이.append(round(st.dxf.dimtxt * (st.dxf.get("dimscale", 1) or 1), 2))
        except Exception as e:
            못읽음.append("치수 %s : %s" % (d.dxf.handle, e))
    단수들 = []; 간격들 = []; 첫단들 = []
    for 기준 in list(가로.values()) + list(세로.values()):
        단 = _묶기(기준, 틈 * 2)
        단수들.append(len(단)); 첫단들.append(round(단[0], 1))
        간격들 += [round(b - a, 1) for a, b in zip(단, 단[1:])]
    r["치수선.단수_최대"] = {"값": max(단수들) if 단수들 else 0, "출처": "선형 치수 %d개 · 기준선 %d곳" % (n치수, len(단수들)), "어떻게": "같은 방향 · 같은 기준선 치수의 치수선 띄움을 묶음"}
    r["치수선.단수_보통"] = {"값": _중앙(단수들), "출처": "기준선 %d곳의 가운데 값" % len(단수들), "어떻게": "중앙값"}
    r["치수선.단_간격"] = {"값": _중앙(간격들), "출처": "단 사이 %d쌍 · 최소 %s · 최대 %s" % (len(간격들), min(간격들) if 간격들 else "-", max(간격들) if 간격들 else "-"), "어떻게": "이웃한 단의 띄움 차이 · 중앙값"}
    r["치수선.첫단_띄움"] = {"값": _중앙(첫단들), "출처": "기준선 %d곳" % len(첫단들), "어떻게": "기준선에서 첫 치수선까지"}
    r["글자.치수_높이"] = {"값": _중앙(글자높이), "출처": "치수 스타일 %d개" % len(set(글자높이)), "어떻게": "dimtxt × dimscale"}
    # 2-2 글자 높이 (TEXT · MTEXT)
    h = [round(t.dxf.height, 2) for t in msp.query("TEXT")] + [round(t.dxf.char_height, 2) for t in msp.query("MTEXT")]
    r["글자.높이"] = {"값": _중앙(h), "출처": "글 %d개" % len(h), "어떻게": "중앙값"}
    # 2-3 지시선 각 · 글 자리 (LEADER · MLEADER)
    각들 = []; 오른쪽 = 0; n지시 = 0
    for ld in msp.query("LEADER"):
        v = [Vec2(p) for p in ld.vertices]
        if len(v) >= 2:
            a = math.degrees(math.atan2(v[1].y - v[0].y, v[1].x - v[0].x)) % 180
            각들.append(round(min(a, 180 - a))); n지시 += 1
            if v[-1].x >= v[0].x: 오른쪽 += 1
    for ml in msp.query("MLEADER"):
        try:
            v = [Vec2(p) for p in ml.context.leaders[0].lines[0].vertices]
            if len(v) >= 2:
                a = math.degrees(math.atan2(v[1].y - v[0].y, v[1].x - v[0].x)) % 180
                각들.append(round(min(a, 180 - a))); n지시 += 1
                if v[-1].x >= v[0].x: 오른쪽 += 1
        except Exception as e:
            못읽음.append("다중지시선 %s : %s" % (ml.dxf.handle, e))
    셈 = {}
    for a in 각들: 셈[a] = 셈.get(a, 0) + 1
    r["지시선.각"] = {"값": (max(셈, key=셈.get) if 셈 else 0), "출처": "지시선 %d개 · " % n지시 + " · ".join("%d° %d" % (k, v) for k, v in sorted(셈.items(), key=lambda x: -x[1])), "어떻게": "첫 마디 각도"}
    r["지시선.글_오른쪽_비율"] = {"값": (round(100 * 오른쪽 / n지시) if n지시 else 0), "출처": "지시선 %d개" % n지시, "어떻게": "끝점이 시작점보다 오른쪽"}
    # 2-4 블록
    블록 = {}
    for i in msp.query("INSERT"): 블록[i.dxf.name] = 블록.get(i.dxf.name, 0) + 1
    r["블록"] = {"값": " · ".join("%s %d" % kv for kv in sorted(블록.items(), key=lambda x: -x[1])[:6]) or "없음", "출처": "삽입 %d개" % sum(블록.values()), "어떻게": "블록 이름별 수"}
    r["레이어"] = {"값": len(doc.layers), "출처": " · ".join(l.dxf.name for l in list(doc.layers)[:8]), "어떻게": "레이어 표"}
    return {"숫자": r, "못읽음": 못읽음, "객체수": len(msp)}

# ───────────────────────── 3. 겹침 세기 ─────────────────────────
def _글상자들(doc):
    """글 · 치수 글 · 지시선 글의 상자(bbox) 목록. (종류 · 핸들 · 글 · (x0,y0,x1,y1))"""
    msp = doc.modelspace(); 상자 = []
    def 넣기(종류, 핸들, 글, 개체들):
        try:
            ex = _bbox.extents(개체들, fast=True)
            if ex.has_data:
                상자.append((종류, 핸들, 글, (ex.extmin.x, ex.extmin.y, ex.extmax.x, ex.extmax.y)))
        except Exception: pass
    for t in msp.query("TEXT"): 넣기("글", t.dxf.handle, t.dxf.text, [t])
    for t in msp.query("MTEXT"): 넣기("글", t.dxf.handle, t.text, [t])
    for d in msp.query("DIMENSION"):
        try:
            글들 = [e for e in d.virtual_entities() if e.dxftype() in ("TEXT", "MTEXT")]
            if 글들: 넣기("치수글", d.dxf.handle, getattr(글들[0].dxf, "text", "") or d.dxf.get("text", ""), 글들)
        except Exception: pass
    for ml in msp.query("MLEADER"):
        try:
            글들 = [e for e in ml.virtual_entities() if e.dxftype() in ("TEXT", "MTEXT")]
            if 글들: 넣기("지시선글", ml.dxf.handle, ml.context.mtext.default_content if ml.context.mtext else "", 글들)
        except Exception: pass
    return 상자

def 겹침세기(doc, 여유=0.0):
    """글 상자끼리 겹친 쌍을 센다. 돌려주는 것 : {겹침수, 목록:[(글a, 글b, 겹친 넓이)]}"""
    상자 = _글상자들(doc); 목록 = []
    for i in range(len(상자)):
        for j in range(i + 1, len(상자)):
            a, b = 상자[i][3], 상자[j][3]
            w = min(a[2], b[2]) - max(a[0], b[0]) + 여유; h = min(a[3], b[3]) - max(a[1], b[1]) + 여유
            if w > 0 and h > 0:
                목록.append({"a": "%s 「%s」" % (상자[i][0], 상자[i][2]), "b": "%s 「%s」" % (상자[j][0], 상자[j][2]),
                             "넓이": round(w * h, 2), "자리": [round((a[0] + b[0]) / 2, 1), round((a[1] + b[1]) / 2, 1)]})
    return {"겹침수": len(목록), "글상자수": len(상자), "목록": 목록}

# ───────────────────────── 4. 그림 ─────────────────────────
def svg로(doc, 폭=1200, 높이=800):
    """모델 공간을 SVG 글자열로. SHX 한글 글꼴은 깨질 수 있다 (스킬 6장) — 그림은 보는 용도."""
    from ezdxf.addons.drawing import Frontend, RenderContext, layout
    from ezdxf.addons.drawing import svg as _svg
    ctx = RenderContext(doc); be = _svg.SVGBackend()
    Frontend(ctx, be).draw_layout(doc.modelspace())
    page = layout.Page(폭, 높이, layout.Units.px, margins=layout.Margins.all(10))
    return be.get_string(page)

# ───────────────────────── 5. 두 판 대조 ─────────────────────────
def _열쇠(e, 자리):
    """객체를 견주는 열쇠 — 종류 · 층 · 좌표(반올림) · 글. 핸들은 안 본다 (스킬 12장 5번)."""
    t = e.dxftype(); 층 = e.dxf.layer; 글 = ""
    try:
        if t in ("TEXT",): 글 = e.dxf.text; p = (e.dxf.insert.x, e.dxf.insert.y)
        elif t == "MTEXT": 글 = e.text; p = (e.dxf.insert.x, e.dxf.insert.y)
        elif t == "LINE": p = (e.dxf.start.x, e.dxf.start.y, e.dxf.end.x, e.dxf.end.y)
        elif t == "LWPOLYLINE": p = tuple(round(c, 자리) for v in e.get_points("xy") for c in v)
        elif t == "DIMENSION": 글 = str(e.dxf.get("text", "")); p = (e.dxf.defpoint.x, e.dxf.defpoint.y, e.dxf.defpoint2.x, e.dxf.defpoint2.y, e.dxf.defpoint3.x, e.dxf.defpoint3.y)
        elif t == "INSERT": 글 = e.dxf.name; p = (e.dxf.insert.x, e.dxf.insert.y)
        elif t == "HATCH": p = (len(e.paths),)
        elif t == "LEADER": p = tuple(round(c, 자리) for v in e.vertices for c in (Vec2(v).x, Vec2(v).y))
        elif t == "MLEADER": p = tuple(round(c, 자리) for v in e.context.leaders[0].lines[0].vertices for c in (v[0], v[1])); 글 = e.context.mtext.default_content if e.context.mtext else ""
        else: p = ()
    except Exception: p = ()
    return (t, 층, tuple(round(c, 자리) for c in p), 글)

def 대조(옛doc, 새doc, 자리=1, 빼는글=("DATE", "날짜", "도면번호")):
    """옛 판 ↔ 새 판. 돌려주는 것 : 바뀐 수 · 지운 수 · 더한 수 · 종류별."""
    def 모으기(doc):
        셈 = {}
        for e in doc.modelspace():
            k = _열쇠(e, 자리)
            if any(x in (k[3] or "") for x in 빼는글): continue
            셈[k] = 셈.get(k, 0) + 1
        return 셈
    a, b = 모으기(옛doc), 모으기(새doc)
    지움 = [k for k in a if a[k] > b.get(k, 0)]; 더함 = [k for k in b if b[k] > a.get(k, 0)]
    종류 = {}
    for k in 지움: 종류[k[0]] = 종류.get(k[0], 0) + 1
    for k in 더함: 종류[k[0]] = 종류.get(k[0], 0) + 1
    return {"지움": len(지움), "더함": len(더함), "다른객체": len(지움) + len(더함), "종류별": 종류,
            "지운것": [list(k)[:2] + [k[3]] for k in 지움[:30]], "더한것": [list(k)[:2] + [k[3]] for k in 더함[:30]]}

if __name__ == "__main__":
    print("도면읽기 v0.1 · 2026-10-29")
    if len(sys.argv) > 1:
        d = dxf열기(sys.argv[1]); print(json.dumps(숫자세기(d), ensure_ascii=False, indent=1)); print(json.dumps(겹침세기(d), ensure_ascii=False)[:500])
