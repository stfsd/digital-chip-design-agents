---
name: infrastructure
description: >
  EDA tool detection, wrapper deployment, and MCP configuration for digital chip
  design environments. Use when setting up a new workstation, verifying tool
  availability before a domain flow, or generating install-missing-tools.sh.
version: 1.0.0
author: chuanseng-ng
license: MIT
allowed-tools: Read, Write, Bash
---

# Skill: Infrastructure Setup

## Invocation

- **If invoked by a user** presenting a setup task: immediately spawn the
  `digital-chip-design-agents:infrastructure-orchestrator` agent and pass the full
  user request and any available context. Do not execute stages directly.
- **If invoked by the `infrastructure-orchestrator` mid-flow**: do not spawn a new
  agent. Treat this file as read-only — return the requested stage rules,
  sign-off criteria, or loop-back guidance to the calling orchestrator.

Spawning the orchestrator from within an active orchestrator run causes recursive
delegation and must never happen.

## Purpose
Detect open-source and proprietary EDA tools, generate an installation script for
missing tools, deploy output-filtering shell wrappers that emit compact JSON instead
of raw 10,000–50,000-line logs, configure MCP server templates, and validate the
complete environment before any domain orchestrator begins work.

---

## Supported EDA Tools

### Open-Source
- **Verilator** (`verilator`) — fast RTL simulator and linter
- **Slang** (`slang`) — SystemVerilog compiler and language server
- **Surelog** (`surelog`) — SystemVerilog pre-processor and parser
- **sv2v** (`sv2v`) — SystemVerilog to Verilog converter
- **Icarus Verilog** (`iverilog`) — Verilog simulator
- **Yosys** (`yosys`) — open synthesis framework
- **ABC** (`abc`) — logic synthesis and verification tool
- **OpenROAD** (`openroad`) — RTL-to-GDS flow
- **LibreLane / OpenLane2** (`openlane`) — open-source ASIC flow
- **KLayout** (`klayout`) — GDS/OASIS viewer and DRC engine
- **OpenSTA** (`sta`) — gate-level static timing analysis
- **SymbiYosys** (`sby`) — formal hardware verification
- **gem5** (`gem5`) — full-system micro-architectural simulator
- **Bambu HLS** (`bambu-hls`) — high-level synthesis from C/C++
- **nextpnr** (`nextpnr`) — FPGA place-and-route
- **openFPGALoader** (`openFPGALoader`) — FPGA programming tool
- **cocotb** (Python package `cocotb`) — Python-based RTL co-simulation
- **LLVM** (`llvm-config`) — compiler infrastructure
- **GCC** (`gcc`) — GNU compiler collection
- **OpenOCD** (`openocd`) — on-chip debugger

### Proprietary (detect only — never install)
- **Synopsys VCS** (`vcs`) — industry-standard RTL simulator
- **Cadence Xcelium** (`xrun`, alt: `xmsim`) — next-generation simulation platform
- **Synopsys Design Compiler** (`dc_shell`, alt: `dc_shell-t`) — logic synthesis
- **Cadence Innovus** (`innovus`) — physical implementation
- **Mentor QuestaSim** (`vsim`, alt: `questa`, `questasim`) — advanced simulation and verification
- **Synopsys PrimeTime** (`pt_shell`, alt: `pt_shell64`) — sign-off static timing analysis
- **Synopsys Formality** (`formality`, alt: `fm_shell`) — formal equivalence checking

---

## MCP Architecture — Two Tiers

### Tier 1: Batch MCP servers (short, self-contained runs)
Use these for tools whose output fits inside a single request/response cycle (seconds to
a few minutes).  Each call spawns the wrapper script, captures its compact JSON output,
and returns it.

| MCP config | Tool | Typical duration |
|------------|------|-----------------|
| `mcp-yosys.json` | Yosys synthesis | seconds–minutes |
| `mcp-openroad.json` | Single OpenROAD stage | minutes |
| `mcp-opensta.json` | OpenSTA batch report | seconds–minutes |
| `mcp-klayout.json` | KLayout DRC/LVS | minutes |
| `mcp-verilator.json` | Verilator lint or sim | seconds–minutes |
| `mcp-bambu.json` | Bambu HLS synthesis | minutes |
| `mcp-gem5.json` | gem5 short benchmark run | minutes (set TOOL_TIMEOUT_S) |
| `mcp-symbiflow.json` | SymbiYosys bounded proof | minutes–hours (set TOOL_TIMEOUT_S) |

The adapter is `plugins/infrastructure/tools/mcp-adapter.py`.

### Tier 2: Interactive session MCP servers (stateful, query-based)
Use these when an agent iterates many times over an already-loaded design (e.g. ECO timing
loops).  The process stays alive between calls — no re-loading per query.

| MCP config | Tool | Exposed tools |
|------------|------|---------------|
| `mcp-openroad-session.json` | OpenROAD Tcl session | `load_design`, `query_timing`, `query_drc`, `get_design_area`, `get_power`, `run_tcl`, `close_design` |
| `mcp-opensta-session.json` | OpenSTA Tcl session | `load_design`, `report_timing`, `report_slack_histogram`, `check_timing`, `run_tcl`, `close_design` |

The adapter is `plugins/infrastructure/tools/mcp-session-adapter.py`.

### Full-flow tools — do NOT use MCP
These tools run for 30 min–2+ hours and produce structured output files on disk.
Agents must launch them via Bash and read the output files directly.

| Tool | Launch command | Read these files |
|------|---------------|-----------------|
| LibreLane / OpenLane 2 | `openlane config.json` | `runs/<design>/<tag>/metrics.json` |
| ORFS / OpenROAD Flow Scripts | `make DESIGN_CONFIG=... finish` | `reports/<platform>/<design>/metrics.json` |
| gem5 full-system simulation | `gem5 config.py ...` | `m5out/stats.txt`, `m5out/simout` |

### Execution Hierarchy (per domain agent)
1. **Tier 2 session MCP** — if the tool supports a session and the design is already loaded
2. **Tier 1 batch MCP** — if the tool has a batch MCP server configured
3. **Wrapper script** — if MCP is not configured; wrapper emits compact JSON
4. **Direct execution** — last resort; raw logs consume significant context

Domain agents must check whether the relevant MCP server is active in `.claude/settings.json`
before falling back to the wrapper or direct execution.

---

## Stage: tool_discovery

### Domain Rules
1. Run `which <command>` and `<command> --version` (or `-version`) for every open-source tool
2. **Exception — Python packages**: for `cocotb`, use `cocotb-config --version` (not `which cocotb`) to determine FOUND and capture the version string; report MISSING if `cocotb-config` is absent or returns non-zero
3. For proprietary tools: check PATH using `which <primary-executable>` only (see executable names in the Proprietary section above); never attempt install; record as `PROPRIETARY_ONLY` if found, `MISSING` otherwise
4. Record each tool as one of: `FOUND`, `MISSING`, or `PROPRIETARY_ONLY`
5. Capture exact version string for each `FOUND` tool
6. Never attempt installation in this stage
7. Write results to `tool-status.json` before advancing

### QoR Metrics to Evaluate
- `tools_detected`: count of FOUND tools (target ≥ 10 for a functional open-source flow)
- `tools_missing`: count of MISSING open-source tools
- `proprietary_found`: count of PROPRIETARY_ONLY tools detected in PATH

### Output Required
- `tool-status.json` — array of `{ "tool": "", "command": "", "status": "FOUND|MISSING|PROPRIETARY_ONLY", "version": "", "path": "" }`

---

## Stage: tool_installation

### Domain Rules
1. **Never auto-run installs** — only generate `install-missing-tools.sh`
2. Script must include package-manager commands for each missing tool:
   - apt-get (Ubuntu/Debian), brew (macOS), pacman (Arch) where available
   - fall back to build-from-source instructions when no package exists
3. Mark proprietary tools as "# manual install required — see vendor docs"
4. If `python3` is missing: FAIL immediately and escalate — required for wrappers
5. Include `chmod +x` calls for all wrapper scripts at the end of the install script
6. Write `tool-manifest.json` reflecting confirmed tool state after user runs the script

### Common Issues & Fixes

| Issue | Fix |
|-------|-----|
| `python3` not found | Escalate immediately — all wrapper scripts depend on it |
| OpenROAD build required | Refer to https://github.com/The-OpenROAD-Project/OpenROAD |
| Bambu HLS Linux only | Wrap with `status: WARN` on macOS/Windows |

### Output Required
- `install-missing-tools.sh` — executable install script for all MISSING tools
- `tool-manifest.json` — final confirmed tool list after installation

---

## Stage: wrapper_deployment

### Domain Rules
1. Deploy all 8 wrapper scripts to `plugins/infrastructure/tools/`
2. Run `chmod +x` on every wrapper; if permission denied: FAIL and escalate with
   `sudo chmod +x` instructions
3. Every wrapper must emit JSON conforming to the schema below regardless of exit code
4. Test each wrapper with `--version` or `--help` after deploy; tolerate MISSING tools
   (wrappers must handle tool-not-found gracefully with `status: "FAIL"`)
5. Never suppress the tool's original exit code

### Wrapper JSON Output Schema
Every wrapper script must print exactly this JSON structure to stdout:
```json
{
  "tool": "<tool-name>",
  "exit_code": 0,
  "status": "PASS|FAIL|WARN",
  "summary": {},
  "errors": [],
  "warnings": [],
  "raw_log": "/tmp/<tool>-XXXXXX.log"
}
```

Fields:
- `status`: `PASS` if exit_code == 0 and no errors; `FAIL` if exit_code != 0 or tool not found; `WARN` if exit_code == 0 with warnings
- `summary`: tool-specific metrics (cells, timing, coverage, etc.)
- `raw_log`: absolute path to temp file containing full unfiltered output

### QoR Metrics to Evaluate
- `wrappers_deployed`: count of wrapper scripts with executable bit set (target: 8)

### Output Required
- 8 executable wrapper scripts in `plugins/infrastructure/tools/`

---

## Stage: mcp_configuration

### Domain Rules
1. Emit MCP config snippets for all 10 MCP configs (8 batch + 2 session)
2. All batch configs use `"command": "python3"` with `mcp-adapter.py` — never point
   directly to the wrapper script as the command; wrapper scripts are not MCP servers
3. Session configs use `mcp-session-adapter.py` with `--tool openroad` or `--tool opensta`
4. Resolve the absolute adapter and wrapper paths at runtime using `realpath` or `pwd` —
   never leave the placeholder `/absolute/path/to/` in the emitted snippets
5. Print each snippet with explicit instruction:
   "Paste the `mcpServers` block into your `.claude/settings.json`"
6. Write the snippet files to `plugins/infrastructure/mcp/`
7. Do not modify `.claude/settings.json` automatically — user must do this manually

### MCP Config Template
```json
{
  "mcpServers": {
    "<tool>": {
      "type": "stdio",
      "command": "/absolute/path/to/plugins/infrastructure/tools/wrap-<tool>.sh",
      "args": []
    }
  }
}
```

### QoR Metrics to Evaluate
- `mcp_servers_configured`: count of MCP snippet files written (target: 10)

### Output Required
Batch MCP configs (Tier 1):
- `plugins/infrastructure/mcp/mcp-yosys.json`
- `plugins/infrastructure/mcp/mcp-openroad.json`
- `plugins/infrastructure/mcp/mcp-opensta.json`
- `plugins/infrastructure/mcp/mcp-klayout.json`
- `plugins/infrastructure/mcp/mcp-verilator.json`
- `plugins/infrastructure/mcp/mcp-bambu.json`
- `plugins/infrastructure/mcp/mcp-gem5.json`
- `plugins/infrastructure/mcp/mcp-symbiflow.json`

Session MCP configs (Tier 2):
- `plugins/infrastructure/mcp/mcp-openroad-session.json`
- `plugins/infrastructure/mcp/mcp-opensta-session.json`

Adapter scripts (required — MCP servers will not start without these):
- `plugins/infrastructure/tools/mcp-adapter.py`
- `plugins/infrastructure/tools/mcp-session-adapter.py`

Printed MCP config snippets for each tool with resolved absolute paths

---

## Stage: environment_validation

### Domain Rules
1. Re-run tool presence checks against `tool-manifest.json`
2. Verify all 8 wrapper scripts exist and have executable bit set
3. Verify MCP snippet files are present in `plugins/infrastructure/mcp/`
4. FAIL if any critical-path tool (Yosys, Verilator, OpenROAD, OpenSTA) is still missing
5. Print final sign-off summary: tools detected, wrappers deployed, MCP servers configured

### Sign-off Checklist
- [ ] `tool-status.json` written with all tools surveyed
- [ ] `install-missing-tools.sh` generated (auto-run is user's choice)
- [ ] `tool-manifest.json` written
- [ ] All 8 wrappers deployed and executable
- [ ] `mcp-adapter.py` and `mcp-session-adapter.py` present in `plugins/infrastructure/tools/`
- [ ] All 10 MCP config snippets written with resolved absolute paths and printed
- [ ] No critical-path tools missing

### Output Required
- Printed environment validation report
- Updated `tool-manifest.json` with final confirmed state
