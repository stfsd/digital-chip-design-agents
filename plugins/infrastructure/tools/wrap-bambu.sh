#!/usr/bin/env bash
# wrap-bambu.sh — run Bambu HLS and emit a compact JSON summary
set -euo pipefail

TOOL="bambu-hls"

if ! command -v "$TOOL" &>/dev/null; then
  python3 - <<'PYEOF'
import json
print(json.dumps({"tool":"bambu","exit_code":1,"status":"FAIL","summary":{},"errors":["tool not found: bambu-hls"],"warnings":[],"raw_log":""}))
PYEOF
  exit 1
fi

LOG=$(mktemp /tmp/bambu-XXXXXX.log)
set +e
"$TOOL" "$@" >"$LOG" 2>&1
EXIT_CODE=$?
set -e

python3 - "$LOG" "$EXIT_CODE" <<'PYEOF'
import json, re, sys, os

log_path = sys.argv[1]
exit_code = int(sys.argv[2])

with open(log_path) as f:
    text = f.read()

errors   = [l.strip() for l in text.splitlines() if re.search(r'\bERROR\b', l, re.I)]
warnings = [l.strip() for l in text.splitlines() if re.search(r'\bWARN\b',  l, re.I)]

# Bambu may write an XML report; try to parse it
latency_m = re.search(r'Total latency[^\d]*([\d.]+)\s*cycles?', text, re.I)
dsp_m     = re.search(r'DSP\s+(\d+)', text, re.I)
bram_m    = re.search(r'BRAM\s+(\d+)', text, re.I)

# Also try parsing HLS report XML if present
xml_candidates = [f for f in os.listdir('.') if f.endswith('_results.xml') or 'hls_report' in f]
for xf in xml_candidates:
    try:
        import xml.etree.ElementTree as ET
        tree = ET.parse(xf)
        root = tree.getroot()
        for tag, key in [('Latency', 'latency_cycles'), ('DSPs', 'dsp_count'), ('BRAMs', 'bram_count')]:
            el = root.find('.//' + tag)
            if el is not None and el.text:
                try:
                    summary_from_xml[key] = int(el.text)
                except ValueError:
                    pass
    except Exception:
        pass

summary = {}
if latency_m: summary["latency_cycles"] = float(latency_m.group(1))
if dsp_m:     summary["dsp_count"]      = int(dsp_m.group(1))
if bram_m:    summary["bram_count"]     = int(bram_m.group(1))
summary["error_count"]   = len(errors)
summary["warning_count"] = len(warnings)

status = "PASS" if exit_code == 0 and not errors else ("WARN" if exit_code == 0 else "FAIL")

print(json.dumps({
    "tool":      "bambu",
    "exit_code": exit_code,
    "status":    status,
    "summary":   summary,
    "errors":    errors[:10],
    "warnings":  warnings[:10],
    "raw_log":   log_path
}, indent=2))
PYEOF

exit $EXIT_CODE
