#!/usr/bin/env bash
# wrap-klayout.sh — run KLayout DRC and emit a compact JSON summary
set -euo pipefail

TOOL="klayout"

if ! command -v "$TOOL" &>/dev/null; then
  python3 - <<'PYEOF'
import json
print(json.dumps({"tool":"klayout","exit_code":1,"status":"FAIL","summary":{},"errors":["tool not found: klayout"],"warnings":[],"raw_log":""}))
PYEOF
  exit 1
fi

LOG=$(mktemp /tmp/klayout-XXXXXX.log)
set +e
"$TOOL" "$@" >"$LOG" 2>&1
EXIT_CODE=$?
set -e

python3 - "$LOG" "$EXIT_CODE" <<'PYEOF'
import json, re, sys, os, glob

log_path = sys.argv[1]
exit_code = int(sys.argv[2])

with open(log_path) as f:
    text = f.read()

errors   = [l.strip() for l in text.splitlines() if re.search(r'\bERROR\b', l, re.I)]
warnings = [l.strip() for l in text.splitlines() if re.search(r'\bWARN\b',  l, re.I)]

# Parse KLayout DRC report XML (*.lyrdb or *.xml) if present
drc_categories = {}
total_drc = 0

for report_file in glob.glob('*.lyrdb') + glob.glob('*drc*.xml'):
    try:
        import xml.etree.ElementTree as ET
        tree = ET.parse(report_file)
        root = tree.getroot()
        for cat in root.findall('.//category'):
            name_el = cat.find('name')
            items   = cat.findall('.//item')
            if name_el is not None:
                cat_name  = name_el.text or "unknown"
                cat_count = len(items)
                drc_categories[cat_name] = cat_count
                total_drc += cat_count
    except Exception:
        pass

# Fallback: parse text log for DRC count
if not drc_categories:
    drc_m = re.search(r'(\d+)\s+(?:DRC\s+)?(?:error|violation)', text, re.I)
    if drc_m:
        total_drc = int(drc_m.group(1))

summary = {
    "drc_total":      total_drc,
    "drc_categories": drc_categories,
    "error_count":    len(errors),
    "warning_count":  len(warnings),
}

if exit_code != 0 or errors:
    status = "FAIL"
elif total_drc > 0:
    status = "WARN"
else:
    status = "PASS"

print(json.dumps({
    "tool":      "klayout",
    "exit_code": exit_code,
    "status":    status,
    "summary":   summary,
    "errors":    errors[:10],
    "warnings":  warnings[:10],
    "raw_log":   log_path
}, indent=2))
PYEOF

exit $EXIT_CODE
