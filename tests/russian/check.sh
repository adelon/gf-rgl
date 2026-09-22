#!/bin/sh
set -eu
: "${GF:?Set GF to your GF executable}"
cd "$(dirname "$0")/../.."
work=$(mktemp -d "${TMPDIR:-/tmp}/russian-rgl-tests.XXXXXX")
trap 'rm -rf "$work"' EXIT HUP INT TERM
"$GF" -run -path=src/api:src/russian:src/common:src/abstract:src/prelude \
  -gfo-dir="$work" < tests/russian/prodrop.gfs > "$work/prodrop.out"
diff -u tests/russian/prodrop.out "$work/prodrop.out"
printf 'Russian subject omission, agreement, oblique and possessive forms passed.\n'
