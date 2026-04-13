#!/usr/bin/env bash
# install.sh — sets up all 13 digital-chip-design-agents plugins for Claude Code
# Works on macOS, Linux, and Git Bash / MSYS2 on Windows.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MARKETPLACE="digital-chip-design-agents"
VERSION="1.0.0"

# ── Locate Claude config dir ──────────────────────────────────────────────────
if [[ -n "${CLAUDE_CONFIG_DIR:-}" ]]; then
  CLAUDE_DIR="$CLAUDE_CONFIG_DIR"
elif [[ "$OSTYPE" == msys* || "$OSTYPE" == cygwin* || "$OSTYPE" == win32* ]]; then
  CLAUDE_DIR="${USERPROFILE}/.claude"
else
  CLAUDE_DIR="${HOME}/.claude"
fi

CACHE_DIR="$CLAUDE_DIR/plugins/cache/$MARKETPLACE"
SETTINGS="$CLAUDE_DIR/settings.json"

echo "Claude config : $CLAUDE_DIR"
echo "Plugin cache  : $CACHE_DIR"
echo ""

# ── Sanity checks ─────────────────────────────────────────────────────────────
if [[ ! -d "$CLAUDE_DIR" ]]; then
  echo "ERROR: Claude config directory not found at $CLAUDE_DIR"
  echo "  Make sure Claude Code is installed and has been run at least once."
  exit 1
fi

if [[ ! -f "$REPO_DIR/.claude-plugin/marketplace.json" ]]; then
  echo "ERROR: Run this script from the repo root."
  exit 1
fi

# ── Plugin list ───────────────────────────────────────────────────────────────
PLUGINS=(
  "chip-design-architecture"
  "chip-design-rtl"
  "chip-design-verification"
  "chip-design-formal"
  "chip-design-synthesis"
  "chip-design-dft"
  "chip-design-sta"
  "chip-design-hls"
  "chip-design-pd"
  "chip-design-soc"
  "chip-design-compiler"
  "chip-design-firmware"
  "chip-design-fpga"
)

# ── Populate plugin cache ─────────────────────────────────────────────────────
echo "Installing plugin cache..."
for plugin in "${PLUGINS[@]}"; do
  dest="$CACHE_DIR/$plugin/$VERSION"
  rm -rf "$dest"
  mkdir -p "$dest"
  cp -r "$REPO_DIR/agents" "$dest/"
  cp -r "$REPO_DIR/skills" "$dest/"
  [[ -d "$REPO_DIR/docs" ]]      && cp -r "$REPO_DIR/docs"      "$dest/"
  [[ -f "$REPO_DIR/README.md" ]] && cp    "$REPO_DIR/README.md" "$dest/"
  [[ -f "$REPO_DIR/LICENSE" ]]   && cp    "$REPO_DIR/LICENSE"   "$dest/"
  echo "  [OK] $plugin"
done

# ── Update settings.json ──────────────────────────────────────────────────────
echo ""
echo "Updating $SETTINGS ..."

# Build the enabled-plugins JSON block
ENABLED_JSON=""
for plugin in "${PLUGINS[@]}"; do
  ENABLED_JSON+="    \"${plugin}@${MARKETPLACE}\": true,"$'\n'
done
ENABLED_JSON="${ENABLED_JSON%,$'\n'}"  # strip trailing comma

# Preflight: python3 required for JSON merge
if ! command -v python3 &>/dev/null; then
  echo "ERROR: python3 is required but not found in PATH."
  echo "  Install Python 3 and re-run this script."
  exit 1
fi

# Use Python for safe JSON merge (handles missing/existing settings)
python3 - "$SETTINGS" "$MARKETPLACE" "$REPO_DIR" <<PYEOF
import json, sys, os

settings_path = sys.argv[1]
marketplace   = sys.argv[2]

plugins = [
  "chip-design-architecture", "chip-design-rtl", "chip-design-verification",
  "chip-design-formal",       "chip-design-synthesis", "chip-design-dft",
  "chip-design-sta",          "chip-design-hls",       "chip-design-pd",
  "chip-design-soc",          "chip-design-compiler",  "chip-design-firmware",
  "chip-design-fpga",
]

cfg = {}
if os.path.exists(settings_path):
    with open(settings_path) as f:
        cfg = json.load(f)

enabled = cfg.setdefault("enabledPlugins", {})
for p in plugins:
    enabled[f"{p}@{marketplace}"] = True

mp = cfg.setdefault("extraKnownMarketplaces", {})
mp[marketplace] = {
    "source": {"source": "directory", "path": sys.argv[3]}
}

with open(settings_path, "w") as f:
    json.dump(cfg, f, indent=2)
    f.write("\n")

print(f"  [OK] {len(plugins)} plugins enabled in settings.json")
PYEOF

echo ""
echo "Done! Restart Claude Code to activate all 13 plugins."
