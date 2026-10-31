#!/usr/bin/env bash
# check.sh deck.md|deck.html [shots-dir] — build (if .md), screenshot+audit, contact sheets, interaction test.
set -uo pipefail
D="$(cd "$(dirname "$0")" && pwd)"
in="$1"; html="$in"
if [[ "$in" == *.md ]]; then html="${in%.md}.html"; python3 "$D/build.py" "$in" -o "$html" --strict || { echo "CHECK FAIL (build warnings: fix copy budget first)"; exit 1; }; fi
out="${2:-$(dirname "$html")/shots}"
node "$D/shot.js" "$html" --out "$out"; s=$?
python3 "$D/sheet.py" "$out" --prefix d >/dev/null && python3 "$D/sheet.py" "$out" --prefix m --cols 6 --width 300 --per 18 >/dev/null
node "$D/key.js" "$html"; k=$?
echo "sheets: $(ls "$out"/sheet-*.png | tr '\n' ' ')"
[[ $s -eq 0 && $k -eq 0 ]] && echo "CHECK PASS" || { echo "CHECK FAIL (shot=$s key=$k)"; exit 1; }
