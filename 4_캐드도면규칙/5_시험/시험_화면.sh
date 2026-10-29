#!/bin/bash
# 복사본 폴더에서 서버를 띄워 화면 시험 (진짜 3_자료 · 4_결과 는 안 건드림) · 변수 이름은 bash 라서 영문
pkill -f "[8]949 --" 2>/dev/null; sleep 0.5
ROOT=$(cd "$(dirname "$0")/.." && pwd); COPY=$(mktemp -d /tmp/dsm_rule_copy_XXXX)
cp -r "$ROOT"/2_실행기 "$COPY"/; mkdir -p "$COPY"/3_자료/원본 "$COPY"/4_결과 "$COPY"/_주고받기
python3 "$ROOT"/5_시험/가짜도면.py "$COPY"/_가짜 >/dev/null
python3 "$COPY"/2_실행기/서버.py 8949 --열지않음 >"$COPY"/서버.log 2>&1 & SRV=$!
sleep 1.5
node "$ROOT"/5_시험/시험_화면.js http://127.0.0.1:8949 "$COPY"/_가짜 "$COPY"/_그림; RC=$?
kill $SRV 2>/dev/null; pkill -f "[8]949 --" 2>/dev/null; echo "복사본 $COPY (그림 _그림 · 서버.log · _주고받기)"; exit $RC
