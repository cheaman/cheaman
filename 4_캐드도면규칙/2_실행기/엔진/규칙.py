# -*- coding: utf-8 -*-
"""규칙 — 규칙.json(규칙 목록) · 지적기록.md · 설정.json · 자료.json 을 읽고 쓴다.
v0.1 · 2026-10-29 · 4_캐드도면규칙 / 2_실행기 / 엔진
원칙 : 쓰기 전 예비본(.bak) · 다시 읽혀야 씀 · 지운 번호는 다시 안 씀"""
import os, json, io, shutil, datetime, threading

def _잠금(f):
    """창고 메서드를 잠금 안에서 돌린다."""
    def g(self, *a, **k):
        with self.잠금: return f(self, *a, **k)
    return g

def 지금(): return datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

class 창고:
    """과업 폴더 하나의 기억. 뿌리 = 4_캐드도면규칙 (3_자료 · 4_결과 · _주고받기 가 그 밑)"""
    def __init__(self, 뿌리):
        self.잠금 = threading.RLock()        # 읽고 고쳐 쓰는 일은 한 번에 하나
        self.뿌리 = 뿌리
        self.결과 = os.path.join(뿌리, "4_결과"); os.makedirs(self.결과, exist_ok=True)
        os.makedirs(os.path.join(self.결과, "그림"), exist_ok=True)
        self.주고받기 = os.path.join(뿌리, "_주고받기"); os.makedirs(self.주고받기, exist_ok=True)
        self.자료폴더 = os.path.join(뿌리, "3_자료"); 
        for d in ("원본", "캡처", "변환"): os.makedirs(os.path.join(self.자료폴더, d), exist_ok=True)
        self.설정경로 = os.path.join(self.결과, "설정.json")
        self.규칙경로 = os.path.join(self.결과, "규칙.json")
        self.자료경로 = os.path.join(self.결과, "자료.json")
        self.지적경로 = os.path.join(self.결과, "지적기록.md")

    # ── 공통 읽고 쓰기 ──
    def _읽기(self, 경로, 기본):
        if not os.path.exists(경로): return 기본
        try: return json.load(io.open(경로, encoding="utf-8"))
        except Exception: return 기본
    def _쓰기(self, 경로, 값):
        if os.path.exists(경로): shutil.copy2(경로, 경로 + ".bak")
        글 = json.dumps(값, ensure_ascii=False, indent=1)
        json.loads(글)                                     # 다시 읽혀야 씀
        with io.open(경로, "w", encoding="utf-8") as f: f.write(글)

    # ── 설정 ──
    기본설정 = {"도면종류": "횡단면도", "출력배율": 50, "회사틀": "", "블록폴더": "",
               "시험잣대": {"적정_벌수": 7, "전체_벌수": 8, "겹침": 0, "자리차이_mm": 1, "새시킴_x": 2},
               "규칙글_줄한도": 30, "AI": "클로드", "AI모델": "", "AI늘한줄": "", "스킬경로": "", "판": "v0.3"}
    def 설정(self):
        s = dict(self.기본설정); s.update(self._읽기(self.설정경로, {})); return s
    @_잠금
    def 설정쓰기(self, 새): s = self.설정(); s.update(새); self._쓰기(self.설정경로, s); return s

    # ── 자료 ──
    def 자료(self): return self._읽기(self.자료경로, {"다음번호": 1, "목록": []})
    def 자료쓰기(self, v): self._쓰기(self.자료경로, v)
    @_잠금
    def 자료더하기(self, 항목):
        v = self.자료(); 항목["번호"] = v["다음번호"]; 항목["넣은때"] = 지금(); 항목.setdefault("이해", []); 항목.setdefault("상태", "")
        v["다음번호"] += 1; v["목록"].append(항목); self.자료쓰기(v); return 항목
    def 자료찾기(self, 번호):
        for a in self.자료()["목록"]:
            if a["번호"] == 번호: return a
        return None
    @_잠금
    def 자료고치기(self, 번호, 고침):
        v = self.자료()
        for a in v["목록"]:
            if a["번호"] == 번호: a.update(고침); self.자료쓰기(v); return a
        return None

    # ── 규칙 ──
    def 규칙(self): return self._읽기(self.규칙경로, {"판": "v0", "다음번호": 1, "목록": []})
    @_잠금
    def 규칙더하기(self, 글, 출처, 자료번호=None, 이해id=None, 상태="○ 받음"):
        v = self.규칙(); r = {"번호": v["다음번호"], "글": 글, "출처": 출처, "상태": 상태, "판": "다음 판", "자료번호": 자료번호, "이해id": 이해id, "때": 지금(), "단원": self.교육()["지금"]}
        v["다음번호"] += 1; v["목록"].append(r); self._쓰기(self.규칙경로, v); return r
    @_잠금
    def 규칙올리기(self):
        """○ 받음 → 올림 · 판 번호 하나 올림. 규칙 글(md) · 숫자 표(json) 를 같이 써 낸다."""
        v = self.규칙(); n = 0
        옛 = v.get("판", "v0"); 새 = "v0.%d" % (int(옛.split(".")[-1]) + 1 if "." in 옛 else 1)
        for r in v["목록"]:
            if r["상태"] == "○ 받음": r["상태"] = "올림"; r["판"] = 새; n += 1
        if n: v["판"] = 새; self._쓰기(self.규칙경로, v); self.규칙글쓰기(v)
        return n, 새
    def 규칙글쓰기(self, v):
        """규칙 글 — 스킬 13장에 붙일 글. 30줄 안. 숫자는 json 으로."""
        줄 = ["## 13. 치수선 · 지시선 · 기호 자리 규칙 (규칙 판 %s · %s · 도면 규칙 가르치기가 씀)" % (v["판"], 지금()[:10]), ""]
        글들 = [r for r in v["목록"] if r["상태"] == "올림"]
        이름 = {d["번호"]: d["이름"] for d in self.교육()["단원"]}
        for i, r in enumerate(글들, 1): 줄.append("13-%d [%s] %s (%s · %s)" % (i, 이름.get(r.get("단원"), "-"), r["글"], r["출처"], r["때"][:10]))
        with io.open(os.path.join(self.결과, "규칙글_13장.md"), "w", encoding="utf-8") as f: f.write("\n".join(줄) + "\n")

    # ── 교육 계획 ──
    기본교육 = {"주제": "횡단면도 치수선 · 지시선 · 기호 자리 규칙", "바라는것": "", "페이지": "계획", "확정": False, "목표": "횡단면도 한 종류에서 다섯 단원의 규칙을 ○ 로 확정해 규칙 글 30줄 안 + 숫자 표 → 정답지 8벌 중 7 적정 · 겹침 0 → 스킬에 붙임", "기": "1기 횡단면도", "지금": 0, "단원": [
        {"번호": 0, "이름": "바탕", "가르침": "출력 배율 · 글자 높이 · 치수 스타일 · 레이어 · EL 블록 이름", "자료": "회사 틀 1 · 고친 판 1 · 설정", "초점": "숫자만 (배율 · 글자 높이 · 레이어 · 블록) · 판단 없음", "끝": "숫자 표 6칸 ○ · 물음 0", "규칙수": 1, "짐작": "30분"},
        {"번호": 1, "이름": "치수선", "가르침": "단 수 · 단 사이 간격 · 첫 단 띄움 · 글자 겹칠 때 비키는 차례 · 같은 선상 합침", "자료": "고친 판 3 · 질문지 1 ~ 8 답", "초점": "치수선만 — 지시선 · 기호는 적지 않음", "끝": "○ 규칙 4 이상 · 물음 0", "규칙수": 4, "짐작": "1시간"},
        {"번호": 2, "이름": "지시선", "가르침": "각 · 글 자리 · 머리 · 모을 때 차례 · 치수선과 겹칠 때 누가 비키나", "자료": "고친 판 3 (지시선 많은 판) · 질문지 9 ~ 15 답", "초점": "지시선만", "끝": "○ 규칙 4 이상 · 물음 0", "규칙수": 4, "짐작": "1시간"},
        {"번호": 3, "이름": "EL · 기호", "가르침": "EL 꼴 · 자리 · 둘이 가까울 때 · 측점 · 경사", "자료": "고친 판 2 · 질문지 16 ~ 19 답 · 캡처 2", "초점": "EL · 측점 · 경사 기호만", "끝": "○ 규칙 3 이상 · 물음 0", "규칙수": 3, "짐작": "40분"},
        {"번호": 4, "이름": "변경 · 틀", "가르침": "받은 판 → 고친 판에서 무엇이 움직이고 무엇이 안 움직이나 · 틀을 깨도 되는 때 · 구름", "자료": "받은판 ↔ 고친판 짝 4 · 질문지 20 ~ 23 답 · 지적기록", "초점": "바뀐 객체 · 안 바뀐 것 · 구름 · 틀", "끝": "○ 규칙 4 이상 · 「절대 안 움직이는 것」 1줄", "규칙수": 4, "짐작": "1시간 30분"},
        {"번호": 5, "이름": "종합", "가르침": "다섯 단원을 한 판에", "자료": "남은 짝 4 (가린 시험용)", "초점": "전부", "끝": "정답지 8벌 중 7 적정 · 겹침 0 · 되풀이 3/3 · 규칙 글 30줄 안 → 스킬에 붙임", "규칙수": 0, "짐작": "1시간"}]}
    def 교육(self):
        v = self._읽기(os.path.join(self.결과, "교육계획.json"), None)
        if not v: v = json.loads(json.dumps(self.기본교육)); self._쓰기(os.path.join(self.결과, "교육계획.json"), v)
        return v
    @_잠금
    def 교육쓰기(self, v): self._쓰기(os.path.join(self.결과, "교육계획.json"), v); return v
    def 지금단원(self):
        v = self.교육(); return v["단원"][min(v["지금"], len(v["단원"]) - 1)]
    def 단원현황(self):
        """지금 단원의 끝 조건 셈 — ○ 규칙 수(이 단원 꼬리표) · 남은 물음 수."""
        v = self.교육(); d = self.지금단원(); 규 = self.규칙()["목록"]
        받은 = sum(1 for r in 규 if r.get("단원") == d["번호"] and r["상태"] in ("○ 받음", "올림"))
        물음 = 0
        for a in self.자료()["목록"]:
            if a.get("단원") == d["번호"]: 물음 += sum(1 for u in a.get("이해", []) if u["상태"] == "ask")
        됨 = 받은 >= d["규칙수"] and 물음 == 0 and (d["규칙수"] > 0 or 받은 > 0)
        return {"단원": d, "받은": 받은, "물음": 물음, "됨": 됨, "지금": v["지금"], "전체": len(v["단원"]), "기": v["기"]}
    @_잠금
    def 다음단원(self):
        v = self.교육(); v["지금"] = min(v["지금"] + 1, len(v["단원"]) - 1); v["단원"][max(v["지금"] - 1, 0)]["끝낸때"] = 지금(); self._쓰기(os.path.join(self.결과, "교육계획.json"), v); return v

    # ── 지적기록 ──
    @_잠금
    def 지적더하기(self, 어디, 무엇, 까닭):
        줄 = "- %s · %s · %s · 까닭 : %s\n" % (지금(), 어디, 무엇, 까닭)
        with io.open(self.지적경로, "a", encoding="utf-8") as f: f.write(줄)
        return self.지적수()
    def 지적수(self):
        if not os.path.exists(self.지적경로): return 0
        return sum(1 for l in io.open(self.지적경로, encoding="utf-8") if l.startswith("- "))
