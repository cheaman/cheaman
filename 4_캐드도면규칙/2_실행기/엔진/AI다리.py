# -*- coding: utf-8 -*-
"""AI 다리 — 봐주세요_NNN.md 를 쓰고, 파악한것_NNN.json 을 읽고, 이 PC 에 claude 가 있으면 바로 부른다.
v0.1 · 2026-10-29 · 4_캐드도면규칙 / 2_실행기 / 엔진
약속 : 스킬 tool-ai-bridge 3 · 4 · 5-5 장. 파일로 주고받는 길은 늘 남긴다 (클로드 대화창에서 「봐주세요 봐 줘」).
되받아 검사 : AI 가 적은 숫자가 프로그램이 센 숫자에 없으면 「확인 필요」."""
import os, io, re, json, shutil, subprocess, tempfile, datetime, threading, queue

답하는모양 = {
  "이해": [{"한줄": "우리 업 말로 · 숫자를 박아 · 한 줄에 규칙 하나", "어디": "도면 어디 · 어느 객체", "무엇이": "무엇이 보이나 · 수", "어떻게": "규칙으로 어떻게 쓰나",
            "안건드림": "이 규칙이 안 건드리는 것", "출처": "파일 이름 · 객체 수 · 녹음 분:초 · 캡처 번호", "상태": "wait | ask | unknown",
            "물음": "상태가 ask 일 때만 · 전무님께 묻는 한 문장", "답": ["보기 1", "보기 2"]}]
}

규칙글 = """당신은 토목 · 구조 도면(횡단면도 · 일반도 · 구조도)의 치수선 · 지시선 · 기호 자리 규칙을 읽어 내는 보조자입니다.
읽는 사람은 토목 · 구조 기술사(전무)이고 코드를 읽지 않습니다. 우리 업에서 쓰는 말로, 숫자를 박아서, 한 줄에 규칙 하나로 씁니다.
지켜야 할 것 :
1. 자료에 없는 숫자를 지어내지 않는다. 프로그램이 센 숫자 표가 있으면 그 숫자만 쓴다.
2. 캡처 그림은 벡터가 없어 숫자를 눈으로 읽는 것이다 — 그 경우 한줄 끝에 「(눈으로 읽음 · ±)」 를 붙인다.
3. 못 알아들은 것은 상태 unknown 으로 두고 어디를 다시 말해 달라는지 적는다. 이해한 척하지 않는다.
4. 도면과 말이 어긋나면 상태 ask 로 두고 물음 한 문장과 보기 2 ~ 4 를 적는다.
5. 코드 이름 · 영어 용어를 쓰지 않는다. 「치수선 · 지시선 · 단 · 간격 · 글자 높이 · EL 기호 · 구름」 같은 우리 말로.
6. 답은 JSON 만. 앞뒤에 설명 · 인사 · 코드블록 표시를 넣지 않는다. 빈 칸은 "" (null 금지).
7. 파일을 쓰거나 저장하지 않는다. 그림은 Read 로 보기만 한다. 답은 그대로 출력하면 도구가 받는다. 허가를 묻지 않는다.
답하는 모양 :
""" + json.dumps(답하는모양, ensure_ascii=False, indent=1)

def JSON뽑기(본문):
    """답 글에서 첫 { 부터 JSON 하나를 뽑는다. 코드블록 표시 · 뒤에 붙은 말이 있어도 된다."""
    i = 본문.find("{")
    while i >= 0:
        try:
            v, _ = json.JSONDecoder().raw_decode(본문[i:])
            if isinstance(v, dict) and "이해" in v: return v
        except Exception: pass
        i = 본문.find("{", i + 1)
    return None

def 클로드있나():
    return shutil.which("claude") is not None

class 다리:
    def __init__(self, 창고):
        self.창고 = 창고; self.줄 = queue.Queue(); self.줄에 = []; self.일꾼 = None   # AI 는 한 번에 하나 (넷을 같이 보내니 셋이 150초를 넘김 · 10-29)
    def 경로(self, 번호, 어느):
        return os.path.join(self.창고.주고받기, "%s_%03d.%s" % (어느, 번호, "md" if 어느 == "봐주세요" else "json"))

    def 봐주세요쓰기(self, 자료):
        """자료 하나에 대한 물음 파일. 숫자 표 · 글 · 그림 경로를 담는다."""
        줄 = ["# 봐주세요 · 자료 %d · %s" % (자료["번호"], 자료["이름"]), "", "종류 : %s · 넣은 때 : %s" % (자료["종류"], 자료["넣은때"]), ""]
        if 자료.get("숫자"):
            줄 += ["## 프로그램이 센 숫자 (이 숫자만 쓰십시오 · 단위 도면 mm · 출력 배율 1:%s)" % self.창고.설정()["출력배율"], "", "| 항목 | 값 | 출처 | 어떻게 셌나 |", "|---|---|---|---|"]
            for k, v in 자료["숫자"].items(): 줄.append("| %s | %s | %s | %s |" % (k, v["값"], v["출처"], v["어떻게"]))
            줄.append("")
        if 자료.get("겹침") is not None:
            줄 += ["## 겹침 : %d곳 (글 상자 %d개)" % (자료["겹침"]["겹침수"], 자료["겹침"]["글상자수"])] + ["- %s ↔ %s" % (x["a"], x["b"]) for x in 자료["겹침"]["목록"][:10]] + [""]
        if 자료.get("글"):
            줄 += ["## 말 · 글 (전무님이 적거나 녹음을 받아쓴 것)", "", 자료["글"], ""]
        if 자료.get("그림들"):
            줄 += ["## 그림 (캡처 · 직접 보십시오 — Read 로 열기 · 벡터가 없어 숫자는 눈으로)", ""] + ["- %s" % p for p in 자료["그림들"]] + [""]
        if 클로드있나(): 줄 += ["## 답하는 모양 — 아래 JSON 을 그대로 출력 (파일로 쓰지 않음 · 앞뒤 말 없음)", ""]
        else: 줄 += ["## 답하는 모양 — `%s` 에 JSON 만" % os.path.basename(self.경로(자료["번호"], "파악한것")), ""]
        줄 += ["```json", json.dumps(답하는모양, ensure_ascii=False, indent=1), "```", ""]
        with io.open(self.경로(자료["번호"], "봐주세요"), "w", encoding="utf-8") as f: f.write("\n".join(줄))
        return self.경로(자료["번호"], "봐주세요")

    def 파악한것읽기(self, 번호):
        p = self.경로(번호, "파악한것")
        if not os.path.exists(p): return None
        try: return json.load(io.open(p, encoding="utf-8"))
        except Exception as e: return {"오류": "파악한것_%03d.json 을 읽지 못함 : %s" % (번호, e)}

    def 되받아검사(self, 자료, 이해):
        """AI 가 적은 숫자가 센 숫자(도면 mm · 종이 mm = ÷출력배율) 와 출처 글에 없으면 확인 필요. 캡처(눈으로)는 건너뜀."""
        if not 자료.get("숫자"): return 이해
        배율 = float(self.창고.설정().get("출력배율") or 50)
        풀 = " ".join(str(v["값"]) + " " + v["출처"] for v in 자료["숫자"].values()) + " " + json.dumps(자료.get("겹침", {}), ensure_ascii=False)
        있는수 = set()
        for t in re.findall(r"\d+(?:\.\d+)?", 풀):
            x = float(t); 있는수.add(round(x, 3)); 있는수.add(round(x / 배율, 3))      # 도면 mm 와 종이 mm 둘 다
        for u in 이해:
            if "눈으로" in (u.get("한줄") or ""): continue
            없음 = []
            for t in re.findall(r"\d+(?:\.\d+)?", u.get("한줄", "")):
                x = round(float(t), 3)
                if x in 있는수 or x <= 3 or x == 13: continue             # 작은 수(단 수 · 차례) 와 13장 번호는 안 봄
                없음.append(t)
            if 없음: u["확인필요"] = "센 숫자에 없는 수 : " + " · ".join(없음)
        return 이해

    def 부르기(self, 자료, 끝나면, 상태갱신=None):
        """이 PC 에 claude 가 있으면 줄에 세워 하나씩 부른다. 없으면 봐주세요 파일만 남긴다."""
        p = self.봐주세요쓰기(자료)
        if not 클로드있나(): return "파일"
        self.줄에.append(자료["번호"]); self.줄.put((자료, p, 끝나면, 상태갱신))
        if self.일꾼 is None or not self.일꾼.is_alive():
            self.일꾼 = threading.Thread(target=self._일꾼, daemon=True); self.일꾼.start()
        return "클로드"
    def 앞에몇건(self, 번호):
        return self.줄에.index(번호) if 번호 in self.줄에 else 0
    def _일꾼(self):
        while True:
            try: 자료, p, 끝나면, 상태갱신 = self.줄.get(timeout=2)
            except queue.Empty: return
            if 상태갱신: 상태갱신(자료["번호"], "AI 가 보는 중")
            self._돌기(자료, p, 끝나면)
            try: self.줄에.remove(자료["번호"])
            except ValueError: pass

    def _돌기(self, 자료, 물음경로, 끝나면):
        임시 = tempfile.mkdtemp(prefix="dsm_rule_ai_"); 규칙경로 = os.path.join(임시, "rules.txt")
        io.open(규칙경로, "w", encoding="utf-8").write(규칙글)
        글 = io.open(물음경로, encoding="utf-8").read()
        for g in 자료.get("그림들", []):      # 그림은 그 폴더에 사본 (AI 손발 : 그 폴더만 읽음)
            try: shutil.copy2(g, 임시)
            except Exception: pass
        글 = 글.replace(os.path.dirname(자료["그림들"][0]) if 자료.get("그림들") else "\x00", 임시)
        명령 = ["claude", "-p", "--output-format", "text", "--no-session-persistence", "--system-prompt-file", 규칙경로] + (["--allowedTools", "Read"] if 자료.get("그림들") else ["--tools", ""])
        모델 = self.창고.설정().get("AI모델")
        if 모델: 명령 += ["--model", 모델]
        t0 = datetime.datetime.now(); 답 = None; 오류 = ""
        try:
            r = subprocess.run(명령, input=글, capture_output=True, text=True, encoding="utf-8", cwd=임시, timeout=180, shell=(os.name == "nt"))
            본문 = r.stdout.strip(); 답 = JSON뽑기(본문)
            if 답 is None: 오류 = "답에서 JSON 을 못 찾음 : " + 본문[:200] + " " + r.stderr[:200]
        except subprocess.TimeoutExpired: 오류 = "180초 안에 답이 없음 — [AI 에게 다시] 를 누르거나 「봐주세요 봐 줘」 로 대화창에 부탁하십시오"
        except Exception as e: 오류 = "claude 부르기 실패 : %s" % e
        초 = (datetime.datetime.now() - t0).seconds
        if 답 is not None:
            io.open(self.경로(자료["번호"], "파악한것"), "w", encoding="utf-8").write(json.dumps(답, ensure_ascii=False, indent=1))
            io.open(os.path.join(self.창고.주고받기, "사용량_%03d.json" % 자료["번호"]), "w", encoding="utf-8").write(json.dumps({"답한곳": "Claude", "모델": 모델 or "", "소요초": 초, "답한때": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}, ensure_ascii=False))
        끝나면(자료["번호"], 답, 오류, 초)
