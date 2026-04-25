# Changelog

## [Unreleased] — agent-scope-review branch

### Added
- **Pre-run context** (`## Pre-run Context`) section added to all 13 domain SKILL.md files:
  agents now read `knowledge.md` and `run_state.md` at every invocation point, not only
  at orchestrator session start.
- **Run-state tracking**: all 13 domain SKILL.md files and the PD orchestrator now write
  `memory/<domain>/run_state.md` as the first action before any tool invocation; `last_stage`
  is updated after each stage so wakeup-loop prompts can resume correctly.
- **Per-stage experience writes**: PD orchestrator (and all domain skills) now upsert to
  `experiences.jsonl` after each stage rather than only on session end; partial runs are
  persisted even if the session is interrupted.
- **Optional claude-mem integration**: all 13 domain skills and the memory-keeper skill now
  emit applied fixes to `mcp__plugin_ecc_memory__add_observations` when the MCP tool is
  present; guard clause skips silently when absent so JSONL remains the canonical record.
- **Clock gating opportunity analysis** added to `architecture` SKILL.md
  (`power_area_estimation` stage): classifies each clock domain by activity factor α,
  produces a `clock_power_budget` hand-off table (domain → frequency, α, est. clock power,
  gating class), and enforces a new QoR gate (≥ 70% of register bits in gateable domains).
- **Power intent / ICG insertion rules** added to `rtl-design` SKILL.md (`rtl_coding` stage):
  RTL agent reads `clock_power_budget` from architecture hand-off and inserts ICG cells for
  high/moderate gating domains; enforces `clock_gating_coverage` ≥ 60% QoR gate.
- **Architecture → RTL handoff contract** updated in `docs/MASTER_INDEX.md` to include
  `clock_power_budget` artifact.
- `memory/README.md` updated to document run_state.md, per-stage write semantics, `run_id`
  schema field, and the optional claude-mem index pattern.
- `docs/Architecture_Evaluation_Flow.md` and `docs/RTL_Design_Flow.md` updated to match
  the new clock gating analysis and ICG insertion rules added to the live SKILL.md files.
- OpenROAD MCP config (`mcp-openroad.json`) comment improved to call out the two placeholder
  values that require substitution during installation.

---

## [1.2.0] — 2026-04-14

### Added
- Multiple IDE support: GitHub Copilot, Google Gemini Code Assist, and OpenCode
- `ides/copilot/` — Copilot workspace instructions and per-domain file-glob mapping (`applyto-map.json`)
- `ides/gemini/` — preamble header injected into a generated `GEMINI.md`
- `ides/opencode/` — base OpenCode config template with all 13 chip-design modes
- `install.sh --ide <copilot|gemini|opencode|all>` flag to deploy IDE-specific config into the target project
- `install.ps1 -IDE <copilot|gemini|opencode|all>` equivalent for Windows PowerShell
- CI/CD validation extended to lint IDE config files on every PR

### Changed
- Agents and skills updated with explicit EDA tool usage annotations
- AgentShield CI step removed (no `.claude` directory present in repo)

---

## [1.1.1] — 2026-04-13

### Added
- AgentShield CI check to validate Claude agent files on every PR

### Fixed
- Issues reported after CodeRabbit review pass on the AgentShield integration

---

## [1.1.0] — 2026-04-13

### Added
- Install scripts for all OS: `install.sh` (macOS / Linux / Git Bash) and `install.ps1` (Windows PowerShell)
- `strict: true` set in `marketplace.json` to enforce exact plugin paths

### Changed
- **Breaking restructure:** all 13 agents and skills split from a shared flat directory into isolated per-plugin subdirectories (`plugins/<domain>/agents/` and `plugins/<domain>/skills/`) to eliminate file-system racing conditions when multiple plugins load concurrently
- Each plugin now has its own `.claude-plugin/plugin.json` manifest
- CI/CD updated for the new directory layout
- README updated to document the new structure and remove the prior racing-issue caveat

### Fixed
- Recursion guard added to agent and skill invocation chains
- Agents now read their skill file before executing; skills now spawn the corresponding orchestrator before executing

---

## [1.0.3] — 2026-04-12

### Fixed
- Marketplace recursive-directory bug: strengthened schema checks to enforce path typing and prevent the marketplace registry from resolving into subdirectories recursively

---

## [1.0.2] — 2026-04-12

### Fixed
- Validate CI and `plugin.json` incorrect formatting (follow-up to v1.0.1)

---

## [1.0.1] — 2026-04-12

### Fixed
- Validate CI pipeline failures on initial setup
- `plugin.json` formatting errors flagged by the CI linter
- Minor environment file corrections reported by CodeRabbit
- Removed stray `.claude` settings file from repo root

---

## [1.0.0] — 2026-04-12 — Initial Release

### Added
- 13 Claude Code marketplace plugins covering the complete digital chip design pipeline
- 13 skill files with YAML frontmatter, staged domain rules, QoR metrics, and fix guidance
- 13 orchestrator agent markdown files with stage sequences, loop-back rules, and sign-off criteria
- `.claude-plugin/plugin.json` — Claude Code plugin manifest
- `.claude-plugin/marketplace.json` — marketplace registry for all 13 plugins
- CI validation workflow (GitHub Actions) — validates every PR
- Automated release workflow with tar.gz archive generation

### Domains in v1.0.0
Architecture Evaluation · RTL Design (SystemVerilog) · Functional Verification (UVM) ·
Formal Verification (FPV/LEC) · Logic Synthesis · Design for Test (DFT) ·
Static Timing Analysis (STA) · High-Level Synthesis (HLS) · Physical Design ·
SoC IP Integration · Compiler Toolchain (LLVM) · Embedded Firmware · FPGA Emulation
