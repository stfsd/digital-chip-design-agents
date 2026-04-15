#!/usr/bin/env bash
# wrap-openroad.sh — run OpenROAD and emit a compact JSON summary
set -euo pipefail

TOOL="openroad"

if ! command -v "$TOOL" &>/dev/null; then
  python3 - <<'PYEOF'
import json
print(json.dumps({"tool":"openroad","exit_code":1,"status":"FAIL","summary":{},"errors":["tool not found: openroad"],"warnings":[],"raw_log":""}))
PYEOF
  exit 1
fi

LOG=$(mktemp /tmp/openroad-XXXXXX.log)
set +e
"$TOOL" "$@" >"$LOG" 2>&1
EXIT_CODE=$?
set -e

python3 - "$LOG" "$EXIT_CODE" <<'PYEOF'
import json, re, sys

log_path = sys.argv[1]
exit_code = int(sys.argv[2])

with open(log_path) as f:
    text = f.read()

errors   = [l.strip() for l in text.splitlines() if re.search(r'\bERROR\b', l, re.I)]
warnings = [l.strip() for l in text.splitlines() if re.search(r'\bWARN\b',  l, re.I)]

wns_m  = re.search(r'wns\s+([-\d.]+)', text)
tns_m  = re.search(r'tns\s+([-\d.]+)', text)
drc_m  = re.search(r'(\d+)\s+(?:DRC\s+)?violations?', text, re.I)

summary = {}
if wns_m:  summary["wns_ns"]       = float(wns_m.group(1))
if tns_m:  summary["tns_ns"]       = float(tns_m.group(1))
if drc_m:  summary["drc_violations"] = int(drc_m.group(1))

progress = re.findall(r'\[INFO\][^\n]+', text)
summary["progress_messages"] = progress[-5:] if progress else []
summary["error_count"]   = len(errors)
summary["warning_count"] = len(warnings)

status = "PASS" if exit_code == 0 and not errors else ("WARN" if exit_code == 0 else "FAIL")

print(json.dumps({
    "tool":      "openroad",
    "exit_code": exit_code,
    "status":    status,
    "summary":   summary,
    "errors":    errors[:10],
    "warnings":  warnings[:10],
    "raw_log":   log_path
}, indent=2))
PYEOF

exit $EXIT_CODE
