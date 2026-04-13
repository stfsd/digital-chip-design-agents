# digital-chip-design-agents

> Claude Code marketplace plugin — full digital chip design pipeline.  
> 13 domains · 13 orchestrators · 13 skill files · architecture through firmware.

[![Validate](https://github.com/chuanseng-ng/digital-chip-design-agents/actions/workflows/validate.yml/badge.svg)](https://github.com/chuanseng-ng/digital-chip-design-agents/actions/workflows/validate.yml)

---

## Install

### Option A — Marketplace (recommended)

Each plugin lives in its own isolated directory, so parallel installs have no
file-lock conflicts on any platform:

```text
/plugin marketplace add github:chuanseng-ng/digital-chip-design-agents
/plugin install chip-design-architecture@digital-chip-design-agents
/plugin install chip-design-rtl@digital-chip-design-agents
/plugin install chip-design-verification@digital-chip-design-agents
/plugin install chip-design-formal@digital-chip-design-agents
/plugin install chip-design-synthesis@digital-chip-design-agents
/plugin install chip-design-dft@digital-chip-design-agents
/plugin install chip-design-sta@digital-chip-design-agents
/plugin install chip-design-hls@digital-chip-design-agents
/plugin install chip-design-pd@digital-chip-design-agents
/plugin install chip-design-soc@digital-chip-design-agents
/plugin install chip-design-compiler@digital-chip-design-agents
/plugin install chip-design-firmware@digital-chip-design-agents
/plugin install chip-design-fpga@digital-chip-design-agents
```

### Option B — Install script (local clone)

**macOS / Linux / Git Bash:**
```bash
git clone https://github.com/chuanseng-ng/digital-chip-design-agents.git
cd digital-chip-design-agents
bash install.sh
```

**Windows (PowerShell):**
```powershell
git clone https://github.com/chuanseng-ng/digital-chip-design-agents.git
cd digital-chip-design-agents
.\install.ps1
```

Restart Claude Code after running — all 13 skills and agents will be active.

### Usage — describe your task in natural language

```
Run the RTL design flow for my AXI DMA controller block
Analyse timing violations on this routed DEF and suggest ECOs
Generate ATPG patterns for this DFT-inserted netlist
Build a UVM testbench for my FIFO block
```

Claude automatically loads the correct skill before executing.

---

## Available Plugins

| Plugin Name | Domain | Invoke When You Want To... |
|-------------|--------|---------------------------|
| `chip-design-architecture` | Architecture Evaluation | Explore microarch candidates, estimate PPA, assess risk |
| `chip-design-rtl` | RTL Design (SystemVerilog) | Write, lint, CDC-check, or synthesis-check RTL |
| `chip-design-verification` | Functional Verification (UVM) | Build testbench, write tests, close coverage, run regression |
| `chip-design-formal` | Formal Verification (FPV/LEC) | Prove properties, check equivalence, close formal gaps |
| `chip-design-synthesis` | Logic Synthesis | Set up SDC, run synthesis, verify netlist with LEC |
| `chip-design-dft` | Design for Test | Plan DFT, insert scan, run ATPG, set up JTAG |
| `chip-design-sta` | Static Timing Analysis | Analyse timing, guide ECO closure, sign off timing |
| `chip-design-hls` | High-Level Synthesis | Convert C/C++ to RTL, optimise directives, co-simulate |
| `chip-design-pd` | Physical Design | Full PD flow: floorplan → placement → CTS → routing → sign-off |
| `chip-design-soc` | SoC IP Integration | Qualify IPs, configure bus fabric, run chip-level sim |
| `chip-design-compiler` | Compiler Toolchain | Build LLVM/GCC backend, assembler, linker, runtime for custom ISA |
| `chip-design-firmware` | Embedded Firmware | BSP, HAL drivers, RTOS integration, firmware validation |
| `chip-design-fpga` | FPGA Emulation | Port ASIC to FPGA, bring up hardware, validate SW on prototype |

---

## How It Works

Each plugin installs two things:

1. **A Skill** (`plugins/<domain>/skills/<domain>/SKILL.md`) — domain knowledge Claude reads
   before executing. Contains stage-by-stage rules, QoR metrics, common fixes, and output
   requirements.

2. **An Orchestrator Agent** (`plugins/<domain>/agents/<domain>-orchestrator.md`) — a subagent
   that manages the full multi-stage flow. It sequences stages, enforces pass/fail criteria,
   applies loop-back rules when a stage fails, and escalates clearly when human input is needed.

Skills are loaded autonomously by Claude when you describe a task. Orchestrators are
invoked explicitly when you want to run a complete flow end-to-end.

---

## Orchestrator Flows

Each orchestrator enforces a strict stage sequence with loop-back rules:

**Physical Design** (example):
```
floorplan → placement → CTS → routing →
timing_opt → power_opt → area_opt → signoff
```
If routing DRC fails → retry routing (max 3×).  
If signoff timing fails → loop back to timing_opt (max 2×).  
If any loop exceeds its limit → escalate to you with full state + recommendations.

All 13 orchestrators follow the same pattern with domain-specific stages and criteria.

---

## Repo Structure

```
digital-chip-design-agents/
│
├── .claude-plugin/
│   └── marketplace.json         ← Marketplace registry (all 13 plugins)
│
├── plugins/                     ← One isolated directory per plugin
│   ├── architecture/
│   │   ├── .claude-plugin/
│   │   │   └── plugin.json      ← Per-plugin manifest
│   │   ├── agents/
│   │   │   └── architecture-orchestrator.md
│   │   └── skills/
│   │       └── architecture/
│   │           └── SKILL.md
│   ├── rtl-design/
│   │   ├── .claude-plugin/plugin.json
│   │   ├── agents/rtl-design-orchestrator.md
│   │   └── skills/rtl-design/SKILL.md
│   └── ... (13 total, same layout each)
│
└── .github/
    └── workflows/
        ├── validate.yml         ← CI: validates all files on every PR
        └── release.yml          ← CD: tags and publishes releases
```

---

## End-to-End Pipeline

The 13 domains map to a complete chip design pipeline:

```
[Specification]
      │
      ▼
[1. Architecture Evaluation] ──► microarch doc
      │
      ├──► [2. RTL Design]  ──► [3. HLS] (algorithm blocks)
      │           │
      │           ├──► [4. Functional Verification]
      │           └──► [5. Formal Verification]
      │                       │
      │                       ▼
      │              [6. Logic Synthesis]
      │                       │
      │           ┌───────────┼───────────┐
      │           ▼           ▼           ▼
      │      [7. DFT]  [8. Physical  [9. STA]
      │                   Design]
      │                       │
      │                   [Tape-out]
      │
      ├──► [10. SoC IP Integration]  (if SoC-level work)
      ├──► [11. Compiler Toolchain]  (if custom CPU)
      ├──► [12. Embedded Firmware]
      └──► [13. FPGA Emulation]      (pre-silicon SW dev)
```

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). PRs welcome for:
- Improved domain rules or QoR metrics in any SKILL.md
- New loop-back rules in orchestrators
- New skill domains (e.g., package/assembly, analog integration)

CI validates all files on every PR — the validate workflow must pass before merge.

### Shared metadata in plugin.json

Each `plugins/<domain>/.claude-plugin/plugin.json` repeats the same `author`,
`homepage`, `repository`, and `license` fields. These are intentional — the
plugin installer reads each manifest in isolation and requires these fields to
be present. The canonical values are:

```json
"author":     { "name": "chuanseng-ng", "url": "https://github.com/chuanseng-ng" },
"homepage":   "https://github.com/chuanseng-ng/digital-chip-design-agents",
"repository": "https://github.com/chuanseng-ng/digital-chip-design-agents",
"license":    "MIT"
```

When updating these fields, change all 13 `plugin.json` files and
`.claude-plugin/marketplace.json` together.

---

## License

MIT — see [LICENSE](LICENSE).
