# Changelog

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
