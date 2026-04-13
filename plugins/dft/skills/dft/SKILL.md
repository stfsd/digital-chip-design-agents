---
name: dft
description: >
  Design for Test — scan architecture planning, scan insertion, ATPG pattern
  generation, MBIST for embedded memories, and JTAG boundary scan. Use when
  planning a DFT strategy, inserting scan, generating test patterns, or
  verifying that a chip will be testable in manufacturing.
version: 1.0.0
author: chuanseng-ng
license: MIT
allowed-tools: Read, Write, Bash
---

# Skill: Design for Test (DFT)

## Invocation

- **If invoked by a user** presenting a DFT task: immediately spawn the
  `digital-chip-design-agents:dft-orchestrator` agent and pass the full user
  request and any available context. Do not execute stages directly.
- **If invoked by the `dft-orchestrator` mid-flow**: do not spawn a new agent.
  Treat this file as read-only — return the requested stage rules, sign-off
  criteria, or loop-back guidance to the calling orchestrator.

Spawning the orchestrator from within an active orchestrator run causes recursive
delegation and must never happen.

## Purpose
Guide the complete DFT flow from architecture planning through ATPG pattern
generation, BIST insertion, JTAG setup, and sign-off. Ensures the manufactured
chip meets quality targets (fault coverage and DPPM).

---

## Stage: dft_architecture

### Domain Rules
1. Scan architecture: full-scan preferred for ASIC; capture all sequential elements
2. Scan chain count: √(total flip-flops) as rule of thumb; balance test time vs routing
3. Chain length balance: ±5% of target length across all chains
4. Compression: EDT/OPMISR for designs > 1M FFs to reduce ATE test time
5. MBIST: one controller per memory group (same width/depth class)
6. JTAG: IEEE 1149.1 TAP controller; boundary scan for all IO pins
7. At-speed test: launch-on-capture (LOC) or launch-on-shift (LOS) — agree with test team
8. Test modes: scan_mode, mbist_mode, jtag_mode must be mutually exclusive
9. Power domains: scan must respect UPF power domain boundaries

### DFT IO Signals Required
- `scan_en` (SE): primary input, must be controllable from ATE
- `scan_in[]` (SDI): one per chain
- `scan_out[]` (SDO): one per chain
- `test_clk`: separate from functional clock or gated version

### QoR Metrics to Evaluate
- DFT spec completeness: all elements defined before insertion
- Estimated fault coverage: analytical pre-insertion estimate ≥ target
- Estimated test time: within ATE budget

### Output Required
- DFT architecture document
- Scan chain plan (count, estimated length, IOs)
- Test mode definitions

---

## Stage: scan_insertion

### Domain Rules
1. Replace all standard FFs with scan-equivalent cells (SDFF, SDFFRQ, etc.)
2. Exclude from scan: memory-mapped registers, MBIST controllers, JTAG cells
3. Do not place scan in: clock gating enables, async set/reset paths (without care cells)
4. EDT compression: insert compressor/decompressor for > 100K FFs
5. Lockup latches: insert between chains crossing clock domain boundaries
6. Scan re-ordering: minimise routing wirelength (use placement-aware reorder)
7. Test points: add controllability/observability points for low-coverage nets

### Scan DRC Rules (all must pass before ATPG)
- No clock signals feeding into scan data path
- No combinational feedback loops through scan
- Scan enable is glitch-free during functional mode
- All scan FFs: correct SI/SE connections

### QoR Metrics to Evaluate
- Scan FF count: 100% of sequential elements minus explicit exclusions
- Chain count and length: per architecture spec (±5%)
- Scan DRC: 0 errors

### Output Required
- Scan-inserted netlist
- Scan chain definition file (.scandef)
- Scan DRC report

---

## Stage: atpg

### Fault Model Targets
| Fault Model | Target Coverage |
|-------------|----------------|
| Stuck-at (SAF) | ≥ 99% |
| Transition Delay | ≥ 95% |
| Cell-Aware | ≥ 95% |
| Bridging | ≥ 90% |
| Path Delay | Critical paths only |

### Domain Rules
1. Run ATPG at multiple capture clocks (slow and fast for transition)
2. X-bounding: apply to improve pattern quality
3. Untestable faults: classify as Redundant or ATPG-Untestable; document all
4. Pattern compression: use compressed patterns for EDT designs
5. At-speed patterns: verify capture timing with STA before signing off
6. Good-machine simulation: run all patterns on RTL or gate sim — 0 failures allowed

### QoR Metrics to Evaluate
- SAF coverage: ≥ 99%
- Transition coverage: ≥ 95%
- Pattern count: minimised (ATE time = test cost)
- Good-machine simulation: 0 failures

### Output Required
- Test pattern file (STIL or WGL)
- Fault report (coverage per model)
- Untestable fault list with classification

---

## Stage: bist_insertion

### MBIST Rules
1. One MBIST controller per memory group (same width/depth class)
2. March algorithm: MATS+, March-C, or as required by quality spec
3. Memory isolation: memories disconnected from logic during BIST
4. Power: verify IR drop with all memories running BIST simultaneously
5. Access: via JTAG TAP or dedicated BIST port

### LBIST Rules (if required)
1. STUMPS architecture: PRPG + MISR + scan chains
2. Alias probability: target < 1e-10
3. LBIST clock: separate from functional clock (usually divided)

### QoR Metrics to Evaluate
- MBIST: all memory instances covered
- MBIST fault coverage: ≥ 99%
- BIST power: within IR drop budget during test
- LBIST alias probability: within target (if applicable)

### Output Required
- BIST-inserted netlist
- BIST controller connection report
- MBIST fault coverage report
- BIST power estimate

---

## Stage: jtag_setup

### Domain Rules
1. TAP pins: TCK, TMS, TDI, TDO, TRST_N — dedicated pads required
2. Boundary scan cells: all digital IO pins must have BSR cells
3. Mandatory instructions: BYPASS, IDCODE, SAMPLE/PRELOAD, EXTEST
4. IDCODE register: 32-bit, unique per device, per IEEE 1149.1
5. TAP: accessible when core is in reset
6. Security: JTAG lockout mechanism for production (OTP/fuse based)

### QoR Metrics to Evaluate
- TAP DRC: all required instructions implemented
- Boundary scan chain: all IOs included
- JTAG connectivity simulation: passes
- IDCODE: unique and correctly formatted

### Output Required
- JTAG-inserted netlist
- BSDL file
- TAP connectivity report

---

## Stage: dft_signoff

### Sign-off Checklist
- [ ] Scan DRC: 0 errors
- [ ] SAF coverage: ≥ 99% (or agreed target)
- [ ] Transition coverage: ≥ 95%
- [ ] Good-machine simulation: 0 failures
- [ ] MBIST: all memories covered
- [ ] JTAG: BSDL generated and verified
- [ ] DFT netlist: LEC vs pre-DFT netlist EQUIVALENT

### Output Required
- DFT sign-off report
- Final test pattern files
- BSDL file
- DFT netlist (input to PD)
