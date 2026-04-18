---
name: logic-synthesis
description: >
  Logic synthesis from RTL to gate-level netlist — SDC constraint validation,
  compile and optimisation strategy, netlist quality check, and LEC equivalence
  verification. Use when synthesising RTL for ASIC, setting up timing constraints,
  optimising for timing/area/power, or verifying a post-synthesis netlist.
version: 1.0.0
author: chuanseng-ng
license: MIT
allowed-tools: Read, Write, Bash
---

# Skill: Logic Synthesis

## Invocation

- **If invoked by a user** presenting a synthesis task: immediately spawn the
  `digital-chip-design-agents:synthesis-orchestrator` agent and pass the full
  user request and any available context. Do not execute stages directly.
- **If invoked by the `synthesis-orchestrator` mid-flow**: do not spawn a new
  agent. Treat this file as read-only — return the requested stage rules,
  sign-off criteria, or loop-back guidance to the calling orchestrator.

Spawning the orchestrator from within an active orchestrator run causes recursive
delegation and must never happen.

## Purpose
Produce a timing-clean, area-efficient, LEC-verified gate-level netlist
from RTL. Covers constraint setup, synthesis compilation strategy, and
quality checks before PD handoff.

---

## Supported EDA Tools

### Open-Source
- **Yosys** (`yosys`) — open-source synthesis suite; runs as a sequential pass pipeline (see sequential flow note below)
- **Surelog** (`surelog`) — SystemVerilog front-end for Yosys
- **ABC** — logic optimisation and technology mapping (invoked automatically by Yosys)

### Proprietary
- **Synopsys Design Compiler** (`dc_shell`) — industry-standard logic synthesis
- **Cadence Genus** (`genus`) — RTL-to-netlist with concurrent optimisation
- **Synopsys Fusion Compiler** (`fc_shell`) — combined synthesis and physical guidance

### Sequential Flow Log Review (Yosys)

Yosys runs its synthesis script (`yosys -c synth.ys` or `yosys -p "synth_*"`) as a
sequential pass pipeline. Each pass (read_verilog → synth → opt → techmap → abc →
write_verilog) executes in order; errors or warnings in early passes propagate forward.

**After a Yosys run the agent must:**
1. Read the Yosys log (stdout or redirected `yosys.log`) for:
   - `Warning:` / `Error:` lines per pass
   - Final statistics block: number of cells, wires, and logic depth
   - Unmapped cells (search for `$`-prefixed cell names in the output netlist)
2. Verify that the output netlist (`synth_netlist.v`) exists and is non-empty
3. Parse `report_area` / `report_timing` output if ABC timing mode (`abc -constr`) was used

When used inside OpenROAD Flow Scripts (ORFS) or LibreLane, the Yosys log appears at:
`logs/<platform>/<design>/1_1_yosys.log`

---

## Stage: constraint_setup

### Domain Rules
1. `create_clock`: all primary clocks with period, waveform, source pin, name
2. `create_generated_clock`: all derived/divided clocks with correct source
3. `set_clock_uncertainty`: setup = skew + jitter (typically 200–500 ps pre-CTS)
4. `set_input_delay` / `set_output_delay`: all primary IOs constrained
5. `set_false_path`: multi-clock crossings, test modes, async resets
6. `set_multicycle_path`: both setup (-setup N) and hold (-hold 1) must be set
7. `set_dont_touch`: IPs, memory macros, hand-crafted cells
8. `set_max_fanout`: per library recommendation (typically 32)
9. `set_max_transition`: per technology DRC rule
10. Operating conditions: explicitly set (never rely on tool defaults)

### Common SDC Mistakes
| Mistake | Consequence |
|---------|------------|
| Missing generated clock | Path unconstrained — may miss timing |
| MCP without hold correction | Hold violations introduced |
| False path too broad | Real timing issues masked |
| No operating conditions set | Wrong library corner used |

### QoR Metrics to Evaluate
- All clocks defined (verify with `report_clocks`)
- All IOs constrained (verify with `report_port -verbose`)
- No unconstrained paths (`report_timing -unconstrained`)

### Output Required
- Validated SDC file
- Clock summary
- Constraint QA report

---

## Stage: compile_explore

### Domain Rules
1. Run at worst-case timing corner (SS, low voltage, high temperature)
2. Compile explore: faster run to find best logic structure
3. Try multiple architectures: retiming on/off, datapath options
4. Identify critical paths for human review before final compile
5. Check area estimate vs microarch estimate

### Optimisation Strategy by Priority
| Priority | Approach |
|----------|---------|
| Timing | compile_ultra, path_group weighting, retiming |
| Area | High area_effort, resource sharing |
| Power | Clock gating insertion, power-aware compile |
| Balanced | compile_ultra -no_autoungroup + incremental |

### Output Required
- Exploration report (timing, area, power summary)
- Critical path list for architect review
- Recommended compile strategy for final compile

---

## Stage: compile_final

### Domain Rules
1. Run multi-scenario if available (setup + hold simultaneously)
2. Enable clock gating synthesis for sequential power reduction
3. Preserve hierarchy for blocks with existing placement intent
4. Ungroup small modules for better cross-boundary optimisation
5. Review critical paths manually — restructure RTL if path cannot close
6. Run incremental compile after initial compile to address remaining violations

### QoR Metrics to Evaluate
- WNS: ≥ 0 at worst-case corner for sign-off
- TNS: = 0 for clean sign-off
- Area: within budget
- Power: within budget
- No unmapped cells

### Output Required
- Gate-level netlist (.v)
- Timing report (setup and hold, all path groups)
- Area report
- Power report
- Synthesis run log

---

## Stage: netlist_qc

### Checks Required
1. No black boxes (undefined modules) in netlist
2. No combinational loops (`report_loop`)
3. Scan chains intact (if DFT-enabled compile)
4. Power/ground connections correct (tie cells, well ties)
5. Formal equivalence check (RTL vs netlist): PASS required

### LEC Requirements
- Golden: RTL (post-lint, post-CDC-clean)
- Revised: gate-level netlist
- Result: all points EQUIVALENT
- Any UNMATCHED point: must be resolved before PD

### QoR Metrics to Evaluate
- LEC: 100% EQUIVALENT
- No black boxes
- No combinational loops
- Scan chain integrity: verified

### Output Required
- LEC report (pass/fail)
- Netlist QC checklist
- Final gate netlist (ready for PD)
- Back-annotated SDC for PD

---

## Stage: synthesis_signoff

### Sign-off Checklist
- [ ] WNS ≥ 0 at all required corners
- [ ] TNS = 0
- [ ] Area within budget
- [ ] Power within budget
- [ ] LEC: EQUIVALENT
- [ ] No black boxes
- [ ] No combinational loops
- [ ] Scan chains verified (if DFT)

### Output Required
- PD handoff package: netlist, SDC, timing reports, area/power reports

---

## Memory

### Write on stage completion
After each stage completes (regardless of whether an orchestrator session is active),
upsert one JSON record in `memory/synthesis/experiences.jsonl` keyed by `run_id`.
Implement the upsert by rewriting the file: read all existing lines, filter out any
record(s) with the same `run_id`, append the updated record, write the full content
back atomically (replace the file). Every record must include a top-level `"run_id"`
field with format `synthesis_<YYYYMMDD>_<HHMMSS>` (set once at flow start; reuse on
each stage update). Set `signoff_achieved: false` until the final sign-off stage
completes.
