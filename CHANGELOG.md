# Changelog

## [1.0.0] — Initial Release

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

## [Unreleased]
- Analog/mixed-signal domain (planning)
- Package and assembly domain (planning)
- Additional handoff contract templates
