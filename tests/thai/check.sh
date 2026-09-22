#!/bin/sh
set -eu
: "${GF:?Set GF to your GF executable}"
cd "$(dirname "$0")/../.."
work=$(mktemp -d "${TMPDIR:-/tmp}/thai-rgl-tests.XXXXXX")
trap 'rm -rf "$work"' EXIT HUP INT TERM
# Linking NumeralTha by itself catches missing category imports that are masked
# when the full GrammarTha also supplies CatTha.
"$GF" -make -path=src/thai:src/common:src/abstract:src/prelude \
  -gfo-dir="$work" -output-dir="$work" src/thai/NumeralTha.gf \
  > "$work/build.log" 2>&1 || { cat "$work/build.log"; exit 1; }
"$GF" -run "$work/Numeral.pgf" < tests/thai/numeral.gfs > "$work/numeral.out"
diff -u tests/thai/numeral.out "$work/numeral.out"
printf 'Thai standalone numeral linking and Decimal/Digits round trips passed.\n'
