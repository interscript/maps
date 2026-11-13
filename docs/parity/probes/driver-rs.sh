#!/usr/bin/env bash
# Parity battery driver (rs leg).
# Usage: driver-rs.sh <maps_dir> <map_id> <input> [--stage S] [--lang L] [--reverse]
# Prints:  OK<TAB>result   or   ERR<TAB>Class<TAB>message
MAPS="$1"; MAPID="$2"; INPUT="$3"; shift 3
STAGE="main"; LANGSEL=""; REVERSE=0
while [ $# -gt 0 ]; do
  case "$1" in
    --stage) STAGE="$2"; shift 2 ;;
    --lang) LANGSEL="$2"; shift 2 ;;
    --reverse) REVERSE=1; shift ;;
    *) echo "unknown flag $1" >&2; exit 2 ;;
  esac
done

ISCRS=/Users/mulgogi/src/interscript/interscript-rs/target/release/iscrs
ARGS=(transliterate "$MAPID" "$INPUT" --stage "$STAGE" --maps "$MAPS")
[ -n "$LANGSEL" ] && ARGS+=(--language "$LANGSEL")
if [ "$REVERSE" = 1 ]; then
  ARGS=(reverse "$MAPID" "$INPUT" --maps "$MAPS")
fi

STDERR_FILE=$(mktemp /tmp/isc-parity-rs-stderr.XXXXXX)
OUT=$("$ISCRS" "${ARGS[@]}" 2>"$STDERR_FILE")
RC=$?
STDERR=$(head -1 "$STDERR_FILE")
rm -f "$STDERR_FILE"
if [ $RC -eq 0 ]; then
  printf 'OK\t%s\n' "$OUT"
else
  STDERR=${STDERR#error: }
  case "$STDERR" in
    "map logic error: "*) printf 'ERR\tMapLogicError\t%s\n' "${STDERR#map logic error: }" ;;
    "unsupported: "*)     printf 'ERR\tUnsupported\t%s\n' "${STDERR#unsupported: }" ;;
    "couldn't locate map"*) printf 'ERR\tMapNotFoundError\t%s\n' "${STDERR#couldn*t locate }" ;;
    "parse failed in"*)   printf 'ERR\tParseError\t%s\n' "$STDERR" ;;
    "dependency cycle: "*) printf 'ERR\tDependencyCycleError\t%s\n' "$STDERR" ;;
    "model error: "*)     printf 'ERR\tModelError\t%s\n' "${STDERR#model error: }" ;;
    *)                    printf 'ERR\tOther\t%s\n' "$STDERR" ;;
  esac
fi
