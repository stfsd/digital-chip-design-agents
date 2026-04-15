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

## Execution Hierarchy

When running tools, prefer in this order:
1. **MCP server** (lowest overhead, structured output directly in Claude context)
2. **Wrapper script** (structured JSON output, tool not configured as MCP)
3. **Direct execution** (last resort — raw log, no structured output)

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
1. Emit MCP config snippets for OpenROAD, Yosys, and OpenSTA pointing to their wrappers
2. Config must use `"type": "stdio"` and an absolute path to the wrapper as `command`
3. Print each snippet with explicit instruction:
   "Paste the `mcpServers` block into your `.claude/settings.json`"
4. Write the snippet files to `plugins/infrastructure/mcp/`
5. Do not modify `.claude/settings.json` automatically — user must do this manually

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
- `mcp_servers_configured`: count of MCP snippet files written (target: 3)

### Output Required
- `plugins/infrastructure/mcp/mcp-yosys.json`
- `plugins/infrastructure/mcp/mcp-openroad.json`
- `plugins/infrastructure/mcp/mcp-opensta.json`
- Printed MCP config snippets for each tool

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
- [ ] MCP config snippets written and printed
- [ ] No critical-path tools missing

### Output Required
- Printed environment validation report
- Updated `tool-manifest.json` with final confirmed state
