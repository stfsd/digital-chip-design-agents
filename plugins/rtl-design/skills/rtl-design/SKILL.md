---
name: rtl-design
description: >
  SystemVerilog RTL design — module planning, coding standards enforcement, lint
  checking, CDC/RDC analysis, and synthesis readiness verification. Use when
  writing, reviewing, or debugging RTL for ASIC or FPGA targets, or when
  checking an existing RTL package for synthesis readiness.
version: 1.0.0
author: chuanseng-ng
license: MIT
allowed-tools: Read, Write, Bash
---

# Skill: RTL Design (SystemVerilog)

## Invocation

When this skill is loaded and a user presents an RTL design task, **do not
execute stages directly**. Immediately spawn the
`digital-chip-design-agents:rtl-design-orchestrator` agent and pass the full
user request and any available context to it. The orchestrator enforces the stage
sequence, loop-back rules, and sign-off criteria defined below.

Use the domain rules in this file only when the orchestrator reads this skill
mid-flow for stage-specific guidance, or when the user asks a targeted reference
question rather than requesting a full flow execution.

## Purpose
Guide RTL development from module hierarchy planning through lint-clean,
CDC-clean, synthesis-ready RTL. Enforces industry-standard SystemVerilog
coding practices and produces a signed-off RTL package ready for simulation
and synthesis handoff.

---

## Stage: module_planning

### Domain Rules
1. Top-down decomposition: start with top-level module, recurse to leaf cells
2. Each module: single clear responsibility (single responsibility principle)
3. Define all port lists before coding (direction, width, type)
4. Identify all clock domains per module; mark CDC crossings explicitly
5. Identify all reset domains; mark synchronous vs asynchronous
6. Parameterise widths and depths wherever possible
7. No logic in top-level integration modules — wiring only
8. Separate datapath and control into distinct sub-modules

### Output Required
- Module hierarchy tree
- Module descriptor (name, purpose, clock domain, ports, sub-modules) per module
- Interface/port list document

---

## Stage: rtl_coding

### Domain Rules — General
1. Always use `logic` type (not wire/reg distinction)
2. All ports: explicitly typed and directioned
3. `default_nettype none` at top of every file
4. No latches: all always_comb blocks must have complete case and assignment coverage
5. No blocking assignments (=) in always_ff blocks
6. No non-blocking assignments (<=) in always_comb blocks
7. One always block per register or coherent register group
8. Reset all registers explicitly; synchronous reset preferred for ASIC

### Domain Rules — Naming Conventions
- Clocks:       `clk_[domain]`
- Resets:       `rst_n_[domain]` (active-low) or `rst_[domain]`
- Active-low:   `signal_n` suffix
- Registered:   `signal_q` suffix
- Next-state:   `signal_d` suffix
- Parameters:   `UPPER_SNAKE_CASE`
- Modules/Signals: `lower_snake_case`

### Domain Rules — Synthesis Safety
1. No delays (#) in RTL — simulation only
2. No initial blocks in ASIC RTL
3. Use `unique case` with explicit don't-cares instead of casez/casex
4. Flag any net with fanout > 32 for buffering intent review
5. No combinational loops — will cause synthesis errors
6. Pipeline registers: clearly marked with `_q` suffix at each stage

### Domain Rules — CDC
1. Two-FF synchroniser for every single-bit CDC crossing
2. Async FIFO for multi-bit CDC data paths
3. Gray-coded pointers for async FIFO crossing
4. Never sample asynchronous data directly in synchronous logic

### Output Required
- RTL source files (.sv) per module
- SVA assertion files per module
- Inline comments on all non-obvious logic

---

## Stage: lint_check

### Domain Rules
1. ERROR level (must fix): latches, incomplete sensitivity lists,
   undriven outputs, multiply-driven signals, X-propagation sources
2. WARNING level (review): unused ports, truncated assignments,
   bit-width mismatches, constant conditions
3. All waivers: must include signal name, rule ID, justification, approver
4. No ERROR-level waivers without architect approval
5. All waivers logged in `lint_waivers.csv`

### QoR Metrics to Evaluate
- ERROR count: must be 0 before proceeding
- WARNING count: review all; waive with documented justification
- All RTL files checked (not just top-level)

### Output Required
- Lint report (per file, per rule)
- Waiver file
- Clean lint summary

---

## Stage: cdc_rdc_analysis

### CDC Rules
1. Every CDC crossing: approved synchroniser primitive
2. Single-bit control: 2-FF synchroniser minimum
3. Multi-bit data: async FIFO or handshake protocol
4. Pulse crossings: pulse stretcher + synchroniser
5. Zero CDC violations (unwaived) before proceeding

### RDC Rules
1. All reset domains explicitly defined in constraints
2. Reset de-assertion: synchronous to receiving clock domain
3. No combinational logic between reset sources
4. Retention registers: correct UPF annotation

### QoR Metrics to Evaluate
- CDC violations (unwaived): 0
- RDC violations (unwaived): 0
- All clock domains verified in tool constraints

### Output Required
- CDC/RDC report
- Synchroniser instance list
- Waiver file

---

## Stage: synth_check

### Domain Rules
1. Run synthesis at target frequency with typical corner
2. Check for unmapped cells (technology library gaps)
3. Identify critical paths — report to architect if WNS < −0.5 ns
4. Check area vs microarch estimate (< 120% acceptable)
5. Check for multi-driven nets or unresolved X
6. Flag high-fanout nets needing buffering strategy
7. Verify all clock definitions synthesise correctly

### QoR Metrics to Evaluate
- WNS at target frequency: > −0.5 ns acceptable at this stage
- Area: < 120% of microarch estimate
- No unmapped cells
- No multi-driven nets

### Output Required
- Synthesis area report
- Timing report (critical paths)
- Recommendations for RTL fixes if needed

---

## Stage: rtl_signoff

### Sign-off Checklist
- [ ] All modules from planning implemented
- [ ] Lint: 0 errors, all warnings reviewed
- [ ] CDC: 0 unwaived violations
- [ ] RDC: 0 unwaived violations
- [ ] Synthesis check: WNS within acceptable range
- [ ] All ports connected in integration
- [ ] SVA assertions in place for key properties
- [ ] Code review completed
- [ ] File list and compile order documented

### Output Required
- RTL file package (all .sv files)
- File list (filelist.f)
- Compile order document
- Assertion library (.sva files)
- RTL sign-off record
