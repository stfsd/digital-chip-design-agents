#!/usr/bin/env bash
# wrap-yosys.sh — run Yosys and emit a compact JSON summary
set -euo pipefail

TOOL="yosys"

if ! command -v "$TOOL" &>/dev/null; then
  python3 - <<'PYEOF'
import json, sys
print(json.dumps({"tool":"yosys","exit_code":1,"status":"FAIL","summary":{},"errors":["tool not found: yosys"],"warnings":[],"raw_log":""}))
PYEOF
  exit 1
fi

LOG=$(mktemp /tmp/yosys-XXXXXX.log)
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
warnings = [l.strip() for l in text.splitlines() if re.search(r'\bWARNING\b', l, re.I)]

cells_m  = re.search(r'Number of cells:\s+(\d+)', text)
area_m   = re.search(r'Chip area for (?:top )?module[^:]*:\s+([\d.]+)', text)

summary = {}
if cells_m:
    summary["cells"] = int(cells_m.group(1))
if area_m:
    summary["chip_area_um2"] = float(area_m.group(1))
summary["error_count"]   = len(errors)
summary["warning_count"] = len(warnings)

status = "PASS" if exit_code == 0 and not errors else ("WARN" if exit_code == 0 else "FAIL")

print(json.dumps({
    "tool":      "yosys",
    "exit_code": exit_code,
    "status":    status,
    "summary":   summary,
    "errors":    errors[:10],
    "warnings":  warnings[:10],
    "raw_log":   log_path
}, indent=2))
PYEOF

exit $EXIT_CODE
