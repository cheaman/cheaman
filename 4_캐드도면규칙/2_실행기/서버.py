# -*- coding: utf-8 -*-
"""도면 규칙 가르치기 — 로컬 서버. 127.0.0.1:8947 · 화면.html 을 내고 API 를 받는다.
v0.1 · 만든 날 2026-10-29 · 고친 날 2026-10-29 · 4_캐드도면규칙 / 2_실행기
돌리기 : python 서버.py [포트] [--열지않음]      (실행.bat 이 부른다)

[ 구역 지도 ]
  1. 준비 · 공통             경로 · 창고 · 다리 · JSON 답
  2. 자료 넣기               /api/자료/넣기 (파일 base64) · /api/말 · 종류 가르기 · DXF 숫자 · 겹침 · 그림 · AI 부름
  3. 자료 · 이해 보기        /api/자료 (파악한것 파일을 보고 이해를 채움) · /api/그림/<번호>/<k>
  4. 판정                    /api/이해/판정 (○ · × · 고쳐서 ○ · 물음 답 · 건너뜀)
  5. 규칙 · 지적 · 설정      /api/규칙 · /api/규칙/올리기 · /api/설정
  6. 시험                    /api/시험/정답지 (받은판 ↔ 고친판 짝 대조)
  7. 요청 가르기             do_GET · do_POST
원칙 : 원본은 3_자료 에 읽기만 · 결과는 4_결과 · AI 와는 _주고받기 · 말없이 멈추지 않음 (오류는 글로 돌려줌)"""
import os, sys, io, json, base64, re, threading, webbrowser, datetime, traceback, shutil
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, unquote
여기 = os.path.dirname(os.path.abspath(__file__)); 뿌리 = os.path.dirname(여기)
sys.path.insert(0, 여기)
from 엔진 import 도면읽기, 규칙 as 규칙모듈, AI다리

판 = "v0.3"; 고친날 = "2026-10-29"
창고 = 규칙모듈.창고(뿌리); 다리 = AI다리.다리(창고)
잠금 = threading.Lock(); 그림잠금 = threading.Lock()   # SVG 그리기는 한 번에 하나 (글꼴 부품이 동시 실행에 깨짐 · 10-29 겪음)

def 종류가르기(이름):
    e = os.path.splitext(이름)[1].lower()
    if e in (".dxf", ".dwg"): return "도면"
    if e in (".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"): return "캡처 그림"
    if e in (".m4a", ".mp3", ".wav", ".ogg"): return "녹음"
    if e in (".dwt",): return "틀"
    if e in (".md", ".txt"): return "지적" if "지적" in 이름 else "말"
    if e in (".pdf",): return "기준"
    return "기타"

def AI끝(번호, 답, 오류, 초):
    """AI 가 답하면 자료에 이해를 채운다 (파일로 온 답도 같은 길)."""
    with 잠금:
        a = 창고.자료찾기(번호)
        if not a: return
        if 답 and "이해" in 답:
            이해 = []
            for i, u in enumerate(답["이해"]):
                u = {k: u.get(k, "") for k in ("한줄", "어디", "무엇이", "어떻게", "안건드림", "출처", "상태", "물음", "답")}
                u["id"] = "%d-%d" % (번호, i + 1); u["상태"] = u["상태"] if u["상태"] in ("wait", "ask", "unknown") else "wait"
                이해.append(u)
            이해 = 다리.되받아검사(a, 이해)
            창고.자료고치기(번호, {"이해": 이해, "상태": "AI 가 봄 · %d초" % 초, "AI오류": ""})
        else:
            창고.자료고치기(번호, {"상태": "AI 답 없음", "AI오류": 오류 or (답 or {}).get("오류", "답 모양이 다름")})

def 자료처리(항목):
    """넣은 자료 하나를 읽어 숫자 · 겹침 · 그림을 붙이고 AI 에게 보낸다."""
    try:
        if 항목["종류"] == "도면":
            경로 = 항목["경로"]
            if 경로.lower().endswith(".dwg"):
                dxf, 까닭 = 도면읽기.dwg를dxf로(경로, os.path.join(창고.자료폴더, "변환"))
                if not dxf: 창고.자료고치기(항목["번호"], {"상태": 까닭}); return
                경로 = dxf; 창고.자료고치기(항목["번호"], {"dxf경로": dxf})
            doc = 도면읽기.dxf열기(경로)
            n = 도면읽기.숫자세기(doc); g = 도면읽기.겹침세기(doc)
            항목.update({"숫자": n["숫자"], "못읽음": n["못읽음"], "객체수": n["객체수"], "겹침": g,
                         "상태": "셈 끝 · 객체 %d · 겹침 %d" % (n["객체수"], g["겹침수"])})
            창고.자료고치기(항목["번호"], 항목)           # 숫자는 먼저 저장 — 그림이 실패해도 남게
            그림 = os.path.join(창고.결과, "그림", "%03d.svg" % 항목["번호"])
            try:
                with 그림잠금: svg = 도면읽기.svg로(doc)
                io.open(그림, "w", encoding="utf-8").write(svg); 항목["그림경로"] = 그림
            except Exception as e:
                항목["못읽음"] = 항목["못읽음"] + ["그림(SVG) 을 못 그림 : %s" % e]
            창고.자료고치기(항목["번호"], 항목)
        elif 항목["종류"] == "캡처 그림":
            항목["상태"] = "그림 %d장" % len(항목.get("그림들", [])); 창고.자료고치기(항목["번호"], 항목)
        elif 항목["종류"] in ("말", "지적", "기타"):
            if 항목.get("경로") and not 항목.get("글"):
                try: 항목["글"] = io.open(항목["경로"], encoding="utf-8").read()[:20000]
                except Exception: 항목["글"] = ""
            항목["상태"] = "글 %d자" % len(항목.get("글", "")); 창고.자료고치기(항목["번호"], 항목)
        elif 항목["종류"] == "녹음":
            창고.자료고치기(항목["번호"], {"상태": "받아쓰기는 다음 판 — 지금은 질문지 답 · 말로 적기로 넣어 주십시오"}); return
        elif 항목["종류"] == "틀":
            창고.자료고치기(항목["번호"], {"상태": "틀 읽기는 다음 판 (dwt 는 ezdxf 가 못 엶) — 치수 스타일은 DXF 로 저장해 넣으면 셈"}); return
        else:
            창고.자료고치기(항목["번호"], {"상태": "아직 아무도 못 읽음 · 이름만 남김"}); return
        def 상태갱신(번호, 글):
            with 잠금:
                a = 창고.자료찾기(번호)
                if a and not a.get("이해"): 창고.자료고치기(번호, {"상태": re.sub(r" · AI .*$", "", a["상태"]) + " · " + 글, "AI시작": datetime.datetime.now().strftime("%H:%M:%S")})
        길 = 다리.부르기(항목, AI끝, 상태갱신)
        앞 = 다리.앞에몇건(항목["번호"])
        창고.자료고치기(항목["번호"], {"AI길": 길, "AI시작": datetime.datetime.now().strftime("%H:%M:%S"), "상태": 항목["상태"] + ((" · AI 차례 기다림 (앞에 %d건)" % 앞) if 길 == "클로드" and 앞 else " · AI 가 보는 중" if 길 == "클로드" else " · 봐주세요 파일 씀 → 대화창에 「봐주세요 봐 줘」")})
    except Exception as e:
        창고.자료고치기(항목["번호"], {"상태": "읽다가 멈춤 : %s" % e, "AI오류": traceback.format_exc()[-600:]})

def 자료넣기(파일들, 묶음이름=None):
    """파일들 = [{이름, base64}] · 그림은 한 묶음으로 · 나머지는 하나씩."""
    그림 = [f for f in 파일들 if 종류가르기(f["이름"]) == "캡처 그림"]; 나머지 = [f for f in 파일들 if 종류가르기(f["이름"]) != "캡처 그림"]
    만든 = []
    if 그림:
        n = len([a for a in 창고.자료()["목록"] if a["종류"] == "캡처 그림"]) + 1
        경로들 = []
        for i, f in enumerate(그림, 1):
            p = os.path.join(창고.자료폴더, "캡처", "캡처%03d_%d%s" % (n, i, os.path.splitext(f["이름"])[1].lower() or ".png"))
            io.open(p, "wb").write(base64.b64decode(f["base64"])); 경로들.append(p)
        a = 창고.자료더하기({"단원": 창고.교육()["지금"], "이름": 묶음이름 or ("캡처 %d · %s" % (n, datetime.datetime.now().strftime("%H:%M")) + (" · %d장 묶음" % len(그림) if len(그림) > 1 else "")), "종류": "캡처 그림", "그림들": 경로들})
        만든.append(a); threading.Thread(target=자료처리, args=(a,), daemon=True).start()
    for f in 나머지:
        p = os.path.join(창고.자료폴더, "원본", os.path.basename(f["이름"]))
        if os.path.exists(p):   # 같은 이름 → 번호 붙임 (원본은 덮지 않음)
            b, e = os.path.splitext(p); k = 2
            while os.path.exists("%s_%d%s" % (b, k, e)): k += 1
            p = "%s_%d%s" % (b, k, e)
        io.open(p, "wb").write(base64.b64decode(f["base64"]))
        a = 창고.자료더하기({"단원": 창고.교육()["지금"], "이름": os.path.basename(p), "종류": 종류가르기(f["이름"]), "경로": p})
        만든.append(a); threading.Thread(target=자료처리, args=(a,), daemon=True).start()
    return 만든

def 자료목록():
    """파악한것 파일이 새로 왔으면 이해를 채운 뒤 돌려준다 (파일 길)."""
    v = 창고.자료()
    for a in v["목록"]:
        if not a.get("이해") and a.get("AI길") == "파일":
            답 = 다리.파악한것읽기(a["번호"])
            if 답: AI끝(a["번호"], 답, "", 0)
    v = 창고.자료()
    for a in v["목록"]:
        a["이해수"] = len(a.get("이해", [])); a["남은"] = sum(1 for u in a.get("이해", []) if u["상태"] in ("wait", "ask", "unknown"))
        a["그림"] = ["/api/그림/%d/%d" % (a["번호"], i) for i in range(len(a.get("그림들", [])))] + (["/api/그림/%d/svg" % a["번호"]] if a.get("그림경로") else [])
    return v

def 판정(번호, id, 어떻게, 글="", 까닭=""):
    a = 창고.자료찾기(번호)
    if not a: return {"오류": "자료 %d 없음" % 번호}
    for u in a.get("이해", []):
        if u["id"] != id: continue
        if 어떻게 == "ok":
            u["상태"] = "ok"; r = 창고.규칙더하기(글 or u["한줄"], u.get("출처", ""), 번호, id)
        elif 어떻게 == "edit":
            u["한줄"] = 글; u["상태"] = "ok"; r = 창고.규칙더하기(글, u.get("출처", "") + " · 전무님이 고침", 번호, id)
        elif 어떻게 == "answer":
            u["답한것"] = 글; u["한줄"] = u["한줄"] + " → 답 : " + 글; u["상태"] = "ok"; r = 창고.규칙더하기(u["한줄"], u.get("출처", "") + " · 물음에 답", 번호, id)
        elif 어떻게 == "no":
            u["상태"] = "no"; u["까닭"] = 까닭; n = 창고.지적더하기(u.get("어디", ""), u["한줄"][:60], 까닭); r = {"지적수": n}
        elif 어떻게 == "skip":
            u["상태"] = "skip"; r = {}
        else: return {"오류": "모르는 판정 " + 어떻게}
        창고.자료고치기(번호, {"이해": a["이해"]}); return {"됨": True, "결과": r}
    return {"오류": "이해 %s 없음" % id}

def 시험_정답지():
    """3_자료\\원본 의 받은판 ↔ 고친판 짝(이름에 받은판 · 고친판 · 같은 번호)을 대조. 규칙을 돌리는 것(자리 다시 잡기)은 다음 판이라, 지금은 고친 판을 규칙 판 대신 둔다."""
    폴더 = os.path.join(창고.자료폴더, "원본"); 잣대 = 창고.설정()["시험잣대"]; 줄 = []
    for f in sorted(os.listdir(폴더)):
        if "받은판" not in f or not f.lower().endswith(".dxf"): continue
        g = f.replace("받은판", "고친판")
        if not os.path.exists(os.path.join(폴더, g)):
            줄.append({"판": f, "판정": "자료 미비", "까닭": "고친 판 없음"}); continue
        try:
            da = 도면읽기.dxf열기(os.path.join(폴더, f)); db = 도면읽기.dxf열기(os.path.join(폴더, g))
            ga = 도면읽기.겹침세기(da)["겹침수"]; gb = 도면읽기.겹침세기(db)["겹침수"]; dj = 도면읽기.대조(da, db)
            판정 = "적정" if gb <= 잣대["겹침"] else "보완 필요"
            줄.append({"판": f, "겹침_받은판": ga, "겹침_고친판": gb, "다른객체": dj["다른객체"], "종류별": dj["종류별"], "판정": 판정})
        except Exception as e:
            줄.append({"판": f, "판정": "자료 미비", "까닭": str(e)})
    적정 = sum(1 for r in 줄 if r["판정"] == "적정")
    통과 = bool(줄) and 적정 >= min(잣대["적정_벌수"], len(줄)) and all(r.get("겹침_고친판", 0) <= 잣대["겹침"] for r in 줄 if r["판정"] != "자료 미비")
    결과 = {"때": 규칙모듈.지금(), "규칙판": 창고.규칙()["판"], "줄": 줄, "적정": 적정, "벌수": len(줄), "통과": 통과, "잣대": 잣대}
    기록 = os.path.join(창고.결과, "시험기록.json"); 옛 = 창고._읽기(기록, []); 옛.append(결과); 창고._쓰기(기록, 옛[-50:])
    return 결과

def 시험_검사도구():
    """시험 4 — 고친 판에 겹침 12곳을 일부러 심어 겹침 세기가 다 잡나 · 깨끗한 판에서 헛잡음 0 인가."""
    sys.path.insert(0, os.path.join(뿌리, "5_시험")); import 가짜도면
    임시 = os.path.join(창고.결과, "_시험"); os.makedirs(임시, exist_ok=True)
    심음 = 가짜도면.틀린도면(os.path.join(임시, "틀린판.dxf"), 12)
    깨끗 = 가짜도면.그리기(os.path.join(임시, "깨끗한판.dxf"), "고친판", 350, 2, "L", False)
    잡음 = 도면읽기.겹침세기(도면읽기.dxf열기(os.path.join(임시, "틀린판.dxf")))["겹침수"]
    헛 = 도면읽기.겹침세기(도면읽기.dxf열기(깨끗))["겹침수"]
    결과 = {"종류": "검사도구", "때": 규칙모듈.지금(), "규칙판": 창고.규칙()["판"], "심음": 심음, "잡음": 잡음, "헛잡음": 헛, "통과": 잡음 >= 심음 and 헛 == 0}
    기록 = os.path.join(창고.결과, "시험기록.json"); 옛 = 창고._읽기(기록, []); 옛.append(결과); 창고._쓰기(기록, 옛[-50:]); return 결과

def 시험_되풀이():
    """시험 5 — 같은 도면을 세 번 세어 숫자 · 겹침이 똑같은가 (프로그램 몫 · AI 판단은 ○ 받은 규칙만 쓰므로 여기선 안 셈)."""
    폴더 = os.path.join(창고.자료폴더, "원본"); 후보 = [f for f in sorted(os.listdir(폴더)) if f.lower().endswith(".dxf")]
    if not 후보:
        sys.path.insert(0, os.path.join(뿌리, "5_시험")); import 가짜도면
        임시 = os.path.join(창고.결과, "_시험"); os.makedirs(임시, exist_ok=True); 파일 = 가짜도면.짝만들기(임시)[0]; 이름 = "가짜 (원본에 DXF 없음)"
    else: 파일 = os.path.join(폴더, 후보[0]); 이름 = 후보[0]
    답 = []
    for i in range(3):
        d = 도면읽기.dxf열기(파일); 답.append(json.dumps({"n": 도면읽기.숫자세기(d)["숫자"], "g": 도면읽기.겹침세기(d)["겹침수"]}, ensure_ascii=False, sort_keys=True))
    같음 = sum(1 for x in 답 if x == 답[0])
    결과 = {"종류": "되풀이", "때": 규칙모듈.지금(), "규칙판": 창고.규칙()["판"], "도면": 이름, "같음": 같음, "번": 3, "통과": 같음 == 3}
    기록 = os.path.join(창고.결과, "시험기록.json"); 옛 = 창고._읽기(기록, []); 옛.append(결과); 창고._쓰기(기록, 옛[-50:]); return 결과

시작표 = "<!-- 도면규칙가르치기 13장 시작 -->"; 끝표 = "<!-- 도면규칙가르치기 13장 끝 -->"
def 스킬에붙이기():
    """규칙글_13장.md 를 설정의 스킬 파일(SKILL.md) 에 표 사이로 붙인다. 예비본 · 다시 읽혀야 씀 · 줄 한도 넘으면 안 붙임."""
    설 = 창고.설정(); 경로 = 설.get("스킬경로") or ""
    if not 경로: return {"오류": "설정 「스킬 파일 경로」 가 비었습니다 — cad-drawing-work 의 SKILL.md 경로를 넣어 주십시오"}
    if not os.path.exists(경로): return {"오류": "스킬 파일이 없습니다 : " + 경로}
    글경로 = os.path.join(창고.결과, "규칙글_13장.md")
    if not os.path.exists(글경로): return {"오류": "아직 올린 규칙이 없습니다 — 먼저 ○ 받은 규칙을 올리십시오"}
    글 = io.open(글경로, encoding="utf-8").read().strip(); 줄수 = len([l for l in 글.splitlines() if l.strip()])
    if 줄수 > int(설.get("규칙글_줄한도") or 30): return {"오류": "규칙 글이 %d줄 — 한도 %s줄을 넘어 안 붙입니다. 긴 것은 숫자 표(json)로 빼십시오" % (줄수, 설.get("규칙글_줄한도"))}
    원 = io.open(경로, encoding="utf-8").read(); 덩이 = 시작표 + "\n" + 글 + "\n" + 끝표
    if 시작표 in 원 and 끝표 in 원: 새 = 원[:원.index(시작표)] + 덩이 + 원[원.index(끝표) + len(끝표):]
    else: 새 = 원.rstrip("\n") + "\n\n" + 덩이 + "\n"
    예비 = 경로 + "." + datetime.datetime.now().strftime("%Y%m%d_%H%M") + ".bak"; shutil.copy2(경로, 예비)
    io.open(경로, "w", encoding="utf-8", newline="").write(새)
    되읽 = io.open(경로, encoding="utf-8").read()
    if 시작표 not in 되읽 or 글[:40] not in 되읽: shutil.copy2(예비, 경로); return {"오류": "붙인 뒤 되읽기가 어긋나 되돌렸습니다"}
    창고.설정쓰기({"스킬붙인때": 규칙모듈.지금(), "스킬붙인줄": 줄수})
    return {"됨": True, "줄수": 줄수, "경로": 경로, "예비": 예비}

# ───────────────────────── 7. 요청 가르기 ─────────────────────────
class 손(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def _json(self, 값, 코드=200):
        b = json.dumps(값, ensure_ascii=False).encode("utf-8")
        self.send_response(코드); self.send_header("Content-Type", "application/json; charset=utf-8"); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
    def _파일(self, 경로, 형):
        if not os.path.exists(경로): self.send_response(404); self.end_headers(); return
        b = open(경로, "rb").read(); self.send_response(200); self.send_header("Content-Type", 형); self.send_header("Content-Length", str(len(b))); self.send_header("Cache-Control", "no-store"); self.end_headers(); self.wfile.write(b)
    def _몸(self):
        n = int(self.headers.get("Content-Length") or 0); return json.loads(self.rfile.read(n).decode("utf-8")) if n else {}
    def do_GET(self):
        u = urlparse(self.path); p = unquote(u.path)
        try:
            if p in ("/", "/index.html"): return self._파일(os.path.join(여기, "화면.html"), "text/html; charset=utf-8")
            if p == "/api/살아있나": return self._json({"판": 판, "고친날": 고친날, "클로드": AI다리.클로드있나()})
            if p == "/api/자료": return self._json(자료목록())
            if p == "/api/규칙": return self._json(창고.규칙())
            if p == "/api/설정": return self._json(창고.설정())
            if p == "/api/교육": return self._json(dict(창고.교육(), 현황=창고.단원현황()))
            if p == "/api/지적": return self._json({"수": 창고.지적수(), "글": io.open(창고.지적경로, encoding="utf-8").read() if os.path.exists(창고.지적경로) else ""})
            if p == "/api/시험기록": return self._json(창고._읽기(os.path.join(창고.결과, "시험기록.json"), []))
            m = re.match(r"^/api/주고받기/(\d+)/(봐주세요|파악한것|사용량)$", p)
            if m:
                q = 다리.경로(int(m.group(1)), m.group(2)) if m.group(2) != "사용량" else os.path.join(창고.주고받기, "사용량_%03d.json" % int(m.group(1)))
                return self._json({"글": io.open(q, encoding="utf-8").read() if os.path.exists(q) else "", "있음": os.path.exists(q), "경로": q})
            m = re.match(r"^/api/그림/(\d+)/(\w+)$", p)
            if m:
                a = 창고.자료찾기(int(m.group(1)))
                if not a: return self._json({"오류": "없음"}, 404)
                if m.group(2) == "svg": return self._파일(a.get("그림경로", ""), "image/svg+xml; charset=utf-8")
                g = a.get("그림들", [])[int(m.group(2))]; e = os.path.splitext(g)[1].lower().strip(".")
                return self._파일(g, "image/" + ("jpeg" if e in ("jpg", "jpeg") else e))
            self._json({"오류": "모르는 주소 " + p}, 404)
        except Exception as e:
            self._json({"오류": str(e), "어디": traceback.format_exc()[-400:]}, 500)
    def do_POST(self):
        p = unquote(urlparse(self.path).path)
        try:
            몸 = self._몸()
            if p == "/api/자료/넣기":
                만든 = 자료넣기(몸.get("파일들", []), 몸.get("이름")); return self._json({"넣음": [a["번호"] for a in 만든], "자료": 자료목록()})
            if p == "/api/말":
                글 = (몸.get("글") or "").strip()
                if not 글: return self._json({"오류": "글이 비었습니다"}, 400)
                a = 창고.자료더하기({"단원": 창고.교육()["지금"], "이름": "말로 적음 · " + datetime.datetime.now().strftime("%H:%M"), "종류": "말", "글": 글})
                threading.Thread(target=자료처리, args=(a,), daemon=True).start(); return self._json({"넣음": [a["번호"]]})
            if p == "/api/이해/판정": return self._json(판정(int(몸["번호"]), 몸["id"], 몸["어떻게"], 몸.get("글", ""), 몸.get("까닭", "")))
            if p == "/api/규칙/올리기":
                n, 새 = 창고.규칙올리기(); 시험 = 시험_정답지() if n else None
                return self._json({"올림": n, "판": 새, "시험": 시험})
            if p == "/api/설정": return self._json(창고.설정쓰기(몸))
            if p == "/api/교육/다음단원": return self._json(dict(창고.다음단원(), 현황=창고.단원현황()))
            if p == "/api/교육/단원고르기": v = 창고.교육(); v["지금"] = max(0, min(int(몸["지금"]), len(v["단원"]) - 1)); 창고.교육쓰기(v); return self._json(dict(v, 현황=창고.단원현황()))
            if p == "/api/시험/정답지": return self._json(시험_정답지())
            if p == "/api/시험/검사도구": return self._json(시험_검사도구())
            if p == "/api/시험/되풀이": return self._json(시험_되풀이())
            if p == "/api/규칙/스킬에붙이기": return self._json(스킬에붙이기())
            if p == "/api/AI/다시":
                a = 창고.자료찾기(int(몸["번호"]))
                if not a: return self._json({"오류": "없음"}, 404)
                창고.자료고치기(a["번호"], {"이해": [], "AI오류": ""}); threading.Thread(target=자료처리, args=(a,), daemon=True).start(); return self._json({"됨": True})
            self._json({"오류": "모르는 주소 " + p}, 404)
        except Exception as e:
            self._json({"오류": str(e), "어디": traceback.format_exc()[-400:]}, 500)

if __name__ == "__main__":
    포트 = int(next((a for a in sys.argv[1:] if a.isdigit()), 8947))
    print("도면 규칙 가르치기 서버 %s · %s · http://127.0.0.1:%d · 클로드 %s" % (판, 고친날, 포트, "있음" if AI다리.클로드있나() else "없음 (파일로 주고받음)"))
    s = ThreadingHTTPServer(("127.0.0.1", 포트), 손)
    if "--열지않음" not in sys.argv: threading.Timer(0.7, lambda: webbrowser.open("http://127.0.0.1:%d" % 포트)).start()
    try: s.serve_forever()
    except KeyboardInterrupt: pass
