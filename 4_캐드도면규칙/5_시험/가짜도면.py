# -*- coding: utf-8 -*-
"""가짜 횡단면도 짝을 만든다 — 받은 판(치수 3단 · 지시선 글 겹침) 과 고친 판(2단 + 셋째 치수를 지시선으로 · 겹침 없음).
v0.1 · 2026-10-29 · 서대전 짝이 오기 전까지 시험 정답지. 단위 mm · 실제 치수 비슷하게."""
import os, sys, ezdxf
from ezdxf.enums import TextEntityAlignment

def 그리기(경로, 판="받은판", 벽=350, 단=3, 지시선쪽="R", 겹침=True):
    doc = ezdxf.new("R2018", setup=True); msp = doc.modelspace()
    for 이름 in ("STR-OUTLINE", "STR-SECTION", "DIM-MAIN", "TXT-NOTE", "SYM-EL", "REV-CLOUD"): doc.layers.add(이름)
    st = doc.dimstyles.get("EZDXF"); st.dxf.dimtxt = 2.5; st.dxf.dimasz = 2.5; st.dxf.dimdec = 0; st.dxf.dimscale = 50; st.dxf.dimexe = 1.5; st.dxf.dimexo = 1.0
    x0, yB, yT = 1000.0, 1000.0, 1000.0 + 3500.0                      # 벽 : x0 ~ x0+벽 · 바닥 yB · 꼭대기 yT
    기초w, 기초h = 벽 + 2 * 400, 600
    msp.add_lwpolyline([(x0, yB), (x0 + 벽, yB), (x0 + 벽, yT), (x0, yT)], close=True, dxfattribs={"layer": "STR-OUTLINE"})
    msp.add_lwpolyline([(x0 - 400, yB - 기초h), (x0 + 벽 + 400, yB - 기초h), (x0 + 벽 + 400, yB), (x0 - 400, yB)], close=True, dxfattribs={"layer": "STR-OUTLINE"})
    h = msp.add_hatch(color=8, dxfattribs={"layer": "STR-SECTION"}); h.set_pattern_fill("ANSI31", scale=20); h.paths.add_polyline_path([(x0, yB), (x0 + 벽, yB), (x0 + 벽, yT), (x0, yT)], is_closed=True)
    # 치수 (아래쪽) : 1단 벽 두께 · 2단 기초 폭 · 3단 전체 (받은 판) / 2단 + 지시선 (고친 판)   · 출력 1:50 이라 치면 8 mm = 400
    간격 = 400; 첫단 = 500; y1 = yB - 기초h - 첫단
    msp.add_linear_dim(base=(x0, y1), p1=(x0, yB - 기초h), p2=(x0 + 벽, yB - 기초h), dimstyle="EZDXF", dxfattribs={"layer": "DIM-MAIN"}).render()
    msp.add_linear_dim(base=(x0, y1 - 간격), p1=(x0 - 400, yB - 기초h), p2=(x0 + 벽 + 400, yB - 기초h), dimstyle="EZDXF", dxfattribs={"layer": "DIM-MAIN"}).render()
    if 단 >= 3:
        msp.add_linear_dim(base=(x0, y1 - 2 * 간격), p1=(x0 - 1000, yB - 기초h), p2=(x0 + 벽 + 1000, yB - 기초h), dimstyle="EZDXF", dxfattribs={"layer": "DIM-MAIN"}).render()
    else:   # 셋째 치수를 지시선으로
        lx = x0 + 벽 + 1000; msp.add_leader([(lx, yB - 기초h), (lx + 300, yB - 기초h + 300), (lx + 800, yB - 기초h + 300)], dxfattribs={"layer": "DIM-MAIN"})
        msp.add_text("W=%d" % (벽 + 2000), height=125, dxfattribs={"layer": "DIM-MAIN"}).set_placement((lx + 320, yB - 기초h + 330), align=TextEntityAlignment.LEFT)
    # 지시선 「앵커 M24」 — 받은 판은 오른쪽 위 치수 글(세로 치수) 과 겹치게
    ax, ay = x0 + 벽, yT - 800
    if 지시선쪽 == "R":
        msp.add_leader([(ax, ay), (ax + 600, ay + 600), (ax + 1400, ay + 600)], dxfattribs={"layer": "TXT-NOTE"})
        msp.add_text("앵커 M24", height=125, dxfattribs={"layer": "TXT-NOTE"}).set_placement((ax + 620, ay + 630), align=TextEntityAlignment.LEFT)
        if 겹침:   # 세로 치수 글이 같은 자리에 오게 — 겹침 1
            msp.add_linear_dim(base=(ax + 900, ay), p1=(ax, ay), p2=(ax, ay + 1200), angle=90, dimstyle="EZDXF", dxfattribs={"layer": "DIM-MAIN"}).render()
    else:
        msp.add_leader([(ax - 벽, ay), (ax - 벽 - 600, ay + 600), (ax - 벽 - 1400, ay + 600)], dxfattribs={"layer": "TXT-NOTE"})
        msp.add_text("앵커 M24", height=125, dxfattribs={"layer": "TXT-NOTE"}).set_placement((ax - 벽 - 1400, ay + 630), align=TextEntityAlignment.LEFT)
        msp.add_linear_dim(base=(ax + 900, ay), p1=(ax, ay), p2=(ax, ay + 1200), angle=90, dimstyle="EZDXF", dxfattribs={"layer": "DIM-MAIN"}).render()
    # EL 기호 블록
    if "EL-TRI" not in doc.blocks:
        b = doc.blocks.new("EL-TRI"); b.add_lwpolyline([(0, 0), (-125, 200), (125, 200)], close=True); b.add_line((-1000, 200), (1000, 200))
    msp.add_blockref("EL-TRI", (x0 - 400, yB), dxfattribs={"layer": "SYM-EL"})
    msp.add_text("EL +12.350", height=125, dxfattribs={"layer": "SYM-EL"}).set_placement((x0 - 1400, yB + 250), align=TextEntityAlignment.LEFT)
    msp.add_text("%s · 가짜 횡단면도 · 벽 %d" % (판, 벽), height=200, dxfattribs={"layer": "TXT-NOTE"}).set_placement((x0 - 1500, yT + 800))
    doc.saveas(경로); return 경로

def 짝만들기(폴더):
    os.makedirs(폴더, exist_ok=True)
    a = 그리기(os.path.join(폴더, "가짜_횡단면도_받은판_01.dxf"), "받은판", 350, 3, "R", True)
    b = 그리기(os.path.join(폴더, "가짜_횡단면도_고친판_01.dxf"), "고친판", 350, 2, "L", False)
    return a, b

if __name__ == "__main__":
    print(짝만들기(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "_가짜")))
