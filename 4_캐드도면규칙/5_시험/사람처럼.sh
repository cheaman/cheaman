#!/bin/bash
# 복사본 서버에서 사람처럼 누르기 · 결과 → 5_시험/사람처럼_결과.md + 5_시험/사람처럼_그림/
pkill -f "[8]951 --" 2>/dev/null; sleep 0.5
ROOT=$(cd "$(dirname "$0")/.." && pwd); COPY=$(mktemp -d /tmp/dsm_rule_human_XXXX)
cp -r "$ROOT"/2_실행기 "$COPY"/; mkdir -p "$COPY"/3_자료/원본 "$COPY"/4_결과 "$COPY"/_주고받기
python3 "$ROOT"/5_시험/가짜도면.py "$COPY"/_가짜 >/dev/null
python3 "$COPY"/2_실행기/서버.py 8951 --열지않음 >"$COPY"/서버.log 2>&1 & SRV=$!
sleep 1.5
rm -rf "$ROOT"/5_시험/사람처럼_그림; node "$ROOT"/5_시험/사람처럼.js http://127.0.0.1:8951 "$COPY"/_가짜 "$ROOT"/5_시험/사람처럼_그림 "$ROOT"/5_시험/사람처럼_결과.md; RC=$?
kill $SRV 2>/dev/null; pkill -f "[8]951 --" 2>/dev/null; echo "복사본 $COPY"; exit $RC
