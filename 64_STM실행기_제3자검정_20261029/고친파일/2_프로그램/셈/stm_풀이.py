# STM 풀이 대본 (시험판) — 정정 2차원 트러스를 절점 평형으로 풀고 스트럿 · 타이 · 절점 폭을 잰다
# 2026-10-25 · 20번 창 · 실행기 아님 (05_STM_만들까판정 «스킬 + 대화로 2주» 의 셈 몫)
#
# 돌리는 법 :  python stm_풀이.py  예제.json  [기준]
#   기준 = KDS (φ 스트럿 0.75 · 타이 0.85 [KDS 14 20 24 4.1.3] · 절점 0.75 [KDS 14 20 10 4.2.3(2)⑥] — 10-25 뷰어 원문 대조)
#          ACI318-11 (φ 모두 0.75 — StructurePoint 정답지 대조용)
#          없음 (φ = 1 — 실험 극한 평가 논문 대조용)
# 단위는 예제 파일 것 그대로 (kN · mm · MPa 또는 kip · in · ksi) — 섞지 않음
import json, math, sys

φ표 = {"KDS": (0.75, 0.85, 0.75), "ACI318-11": (0.75, 0.75, 0.75), "없음": (1.0, 1.0, 1.0)}

def 풀기(m):
    점 = m["절점"]                      # {"A": [x, y], ...}
    부 = m["부재"]                      # [["AB", "A", "B", "스트럿"|"타이"], ...]
    받 = m["받침"]                      # {"A": ["x", "y"], "D": ["y"]}
    하 = m.get("하중", {})              # {"B": [Fx, Fy]}  (y 는 위가 +)
    모름 = [p[0] for p in 부] + [f"R{n}{d}" for n, ds in 받.items() for d in ds]
    줄 = []; 오른 = []
    for n, (x, y) in 점.items():
        for 축 in (0, 1):
            r = [0.0] * len(모름)
            for k, (이름, a, b, _) in enumerate(부):
                if n not in (a, b): continue
                o = b if n == a else a
                dx, dy = 점[o][0] - x, 점[o][1] - y
                L = math.hypot(dx, dy)
                if L < 1e-9: raise SystemExit(f"부재 {이름} 길이 0 — 절점 {a} · {b} 좌표가 같음 (② 모델에서 좌표 확인)")   # 10-29 검정 : 전엔 «float division by zero»
                r[k] = (dx, dy)[축] / L          # 인장 + : 절점에서 상대 절점 쪽으로 당김
            for d in 받.get(n, []):
                if (d == "x") == (축 == 0): r[모름.index(f"R{n}{d}")] = 1.0
            줄.append(r); 오른.append(-하.get(n, [0, 0])[축])
    if len(줄) < len(모름): raise SystemExit(f"부정정 — 방정식 수 {len(줄)} · 미지수 {len(모름)} (강성법은 아직 없음)")
    원줄, 원오른 = 줄, 오른
    if len(줄) > len(모름):
        # 식이 많음 = 대칭 4점 재하 같은 «하중이 맞아야만 서는» 모델 — 정규방정식으로 풀고 남는 힘을 잰다
        n = len(모름)
        줄 = [[sum(r[i] * r[j] for r in 원줄) for j in range(n)] for i in range(n)]
        오른 = [sum(r[i] * b for r, b in zip(원줄, 원오른)) for i in range(n)]
    # 가우스 소거
    A = [r[:] + [b] for r, b in zip(줄, 오른)]; N = len(A)
    for c in range(N):
        p = max(range(c, N), key=lambda i: abs(A[i][c]))
        if abs(A[p][c]) < 1e-12: raise SystemExit("해석 실패 (불안정 트러스)")
        A[c], A[p] = A[p], A[c]
        for i in range(N):
            if i != c and A[i][c]:
                f = A[i][c] / A[c][c]
                A[i] = [a - f * b for a, b in zip(A[i], A[c])]
    답 = {모름[i]: A[i][N] / A[i][i] for i in range(N)}
    남 = max(abs(sum(r[k] * 답[모름[k]] for k in range(N)) - b) for r, b in zip(원줄, 원오른))
    if 남 > 1e-6 * max(1.0, max(abs(b) for b in 원오른)):
        raise SystemExit(f"평형 불만족 (잔차 {남:.3g}) — 불안정 구조 (사재 추가 필요)")
    return 답

def 검토(m, 기준):
    φs, φt, φn = φ표[기준]
    힘 = 풀기(m); fc = m["재료"]["fc"]; fy = m["재료"]["fy"]; b = m["폭b"]
    βs = m.get("βs", {}); βn = m.get("βn", {})
    배 = 1000.0 if m.get("단위") == "kN-mm-MPa" else 1.0   # kN → N (폭 mm · As mm²) · 단위 키가 없으면 ×1 (정답지 kip-in-ksi 꼴) — 서버.풀기 가 과업의 단위를 먼저 정규화해 넘김 (10-29 검정)
    절점두께 = m.get("절점두께") or {}                     # 절점영역 면의 두께 {절점: mm} — 받침판 가로 · 말뚝 π/4·D 등가 · 없으면 부재 두께 b (10-29 검정 : 전엔 늘 b → 좁은 판 · 말뚝에서 위험 쪽)
    나 = []; 폭 = {}
    for 이름, a, c, 종 in m["부재"]:
        F = 힘[이름]
        if 종 == "스트럿":
            if F > 1e-9: 나.append(f"  ★ {이름} 스트럿인데 인장 {F:.1f}")
            bs = βs.get(이름, 0.75); fce = 0.85 * bs * fc      # (4.2-2) · 병모양 횡철근 못 채우면 0.60λ
            w = -F * 배 / (φs * fce * b)
            나.append(f"  {이름:4} 스트럿 {F:10.1f} · βs {bs:.2f} · fce {fce:.3f} · 필요 폭 {w:.2f}")
        else:
            if F < -1e-9: 나.append(f"  ★ {이름} 타이인데 압축 {F:.1f}")
            As = F * 배 / (φt * fy); 폭[이름 + " As"] = As
            나.append(f"  {이름:4} 타이   {F:10.1f} · 필요 As {As:.1f}")
    for n, 면들 in m.get("절점면", {}).items():
        bn = βn.get(n, 1.0); fce = 0.85 * bn * fc          # (4.4-2)
        for 면, 키 in 면들.items():
            # 키 = 부재 이름 · 받침 반력 «RAy» · 하중 «P:B» (그 절점 하중 크기)
            F = math.hypot(*m["하중"][키[2:]]) if 키.startswith("P:") else abs(힘[키])
            # 면 강도 = 절점 유효강도와 그 절점에 닿는 스트럿 유효강도 중 가장 작은 값 (StructurePoint 꼴 · 보수적)
            닿는 = [βs.get(p[0], 0.75) for p in m["부재"] if p[3] == "스트럿" and n in (p[1], p[2])]
            bs면 = min(닿는) if 닿는 else 1.0
            f면 = min(fce, 0.85 * bs면 * fc) if m.get("면은작은값", True) else fce
            b면 = float(절점두께.get(n) or b)
            w = F * 배 / (φn * f면 * b면); 폭[f"{n} {면}"] = w
            나.append(f"  절점 {n} {면:6} 힘 {F:9.1f} · 필요 폭 {w:.2f}")
    return 힘, 나, 폭

if __name__ == "__main__":
    m = json.load(open(sys.argv[1], encoding="utf-8"))
    기준 = sys.argv[2] if len(sys.argv) > 2 else m.get("기준", "KDS")
    힘, 나, 폭 = 검토(m, 기준)
    print(f"== {m['이름']} · 기준 {기준} ==")
    print("  " + " · ".join(f"{k} {v:.1f}" for k, v in 힘.items()))
    print("\n".join(나))
    for 키, 값 in m.get("기대", {}).items():
        try: 얻 = abs(힘[키]) if 키 in 힘 else None
        except Exception: 얻 = None
        if 얻 is None: continue
        틀 = abs(얻 - 값) / 값
        print(f"  대조 {키:5} 얻 {얻:9.1f} · 정답 {값:9.1f} · 차 {틀*100:.2f} % {'✔' if 틀 <= 0.005 else '★'}")
    if 기준 == m.get("기준"):
        for 키, 값 in m.get("기대_폭", {}).items():
            얻 = 폭.get(키)
            if 얻 is None: print(f"  대조 {키} — 얻은 값 없음 ★"); continue
            틀 = abs(얻 - 값) / 값
            print(f"  대조 {키:9} 얻 {얻:8.2f} · 정답 {값:8.2f} · 차 {틀*100:.2f} % {'✔' if 틀 <= 0.01 else '★'}")
