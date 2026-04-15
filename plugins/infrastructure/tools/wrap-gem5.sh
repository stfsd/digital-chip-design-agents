#!/usr/bin/env bash
# wrap-gem5.sh — run gem5 and emit a compact JSON summary
set -euo pipefail

TOOL="gem5"

if ! command -v "$TOOL" &>/dev/null; then
  _LOG=$(mktemp /tmp/gem5-notfound-XXXXXX.log)
  echo "tool not found: gem5" > "$_LOG"
  python3 - "$_LOG" <<'PYEOF'
import json, sys
log_path = sys.argv[1]
print(json.dumps({"tool":"gem5","exit_code":1,"status":"FAIL","summary":{},"errors":["tool not found: gem5"],"warnings":[],"raw_log":log_path}))
PYEOF
  exit 1
fi

LOG=$(mktemp /tmp/gem5-XXXXXX.log)
set +e
"$TOOL" "$@" >"$LOG" 2>&1
EXIT_CODE=$?
set -e

python3 - "$LOG" "$EXIT_CODE" <<'PYEOF'
import json, re, sys

log_path = sys.argv[1]
exit_code = int(sys.argv[2])

with open(log_path, encoding='utf-8', errors='replace') as f:
    text = f.read()

errors   = [l.strip() for l in text.splitlines() if re.search(r'\bERROR\b|panic|fatal', l, re.I)]
warnings = [l.strip() for l in text.splitlines() if re.search(r'\bWARN\b', l, re.I)]

sim_insts_m   = re.search(r'simInsts\s+(\d+)', text)
host_secs_m   = re.search(r'hostSeconds\s+([\d.]+)', text)
ipc_m         = re.search(r'\bipc\b\s+([\d.]+)', text, re.I)

summary = {}
if sim_insts_m: summary["sim_insts"]    = int(sim_insts_m.group(1))
if host_secs_m: summary["host_seconds"] = float(host_secs_m.group(1))
if ipc_m:       summary["ipc"]          = float(ipc_m.group(1))
summary["error_count"]   = len(errors)
summary["warning_count"] = len(warnings)

status = "FAIL" if exit_code != 0 or errors else ("WARN" if warnings else "PASS")

print(json.dumps({
    "tool":      "gem5",
    "exit_code": exit_code,
    "status":    status,
    "summary":   summary,
    "errors":    errors[:10],
    "warnings":  warnings[:10],
    "raw_log":   log_path
}, indent=2))
PYEOF

exit $EXIT_CODE
