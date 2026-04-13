---
name: physical-design
description: >
  Full physical design flow — floorplan, placement, clock tree synthesis, routing,
  timing optimisation, power optimisation, area optimisation, and tape-out sign-off.
  Use when implementing a gate-level netlist through to GDS-II, closing timing and
  power, or performing any individual PD stage analysis.
version: 1.0.0
author: chuanseng-ng
license: MIT
allowed-tools: Read, Write, Bash
---

# Skill: Physical Design

## Invocation

- **If invoked by a user** presenting a physical design task: immediately spawn
  the `digital-chip-design-agents:physical-design-orchestrator` agent and pass
  the full user request and any available context. Do not execute stages directly.
- **If invoked by the `physical-design-orchestrator` mid-flow**: do not spawn a
  new agent. Treat this file as read-only — return the requested stage rules,
  sign-off criteria, or loop-back guidance to the calling orchestrator.

Spawning the orchestrator from within an active orchestrator run causes recursive
delegation and must never happen.

## Purpose
Guide the complete physical implementation flow from gate-level netlist to
tape-out-ready GDS-II. Eight stages with explicit QoR gates and loop-back
criteria enforced by the physical-design orchestrator.

---

## Stage: floorplan

### Domain Rules
1. Core utilisation target: 70–80% — leave margin for routing congestion
2. Macros: place at die edges or corners with halos (typically 5–10 μm)
3. IO pads: distribute evenly; match package pin assignment
4. Power grid: VDD/VSS straps every N rows (technology-node specific)
5. Blockages: hard blockages around analog/RF macros
6. Aspect ratio: keep close to 1:1 unless package constrains otherwise
7. Voltage island boundaries must align to row boundaries

### QoR Metrics to Evaluate
- Estimated congestion (H and V): flag if > 80%
- Estimated WNS from floorplan-stage STA: flag if < −2 ns
- IR drop estimate: flag if > 10% of VDD

### Output Required
- Floorplan DEF (floorplan.def)
- Power grid DEF or script
- Macro placement report
- Estimated congestion map

---

## Stage: placement

### Domain Rules
1. Sequence: global → legalise → detailed → pre-CTS optimisation
2. Pre-CTS timing: ideal clocks; uncertainty = skew + jitter estimate
3. Max utilisation per partition: 80%
4. High-fanout nets: buffer before placement or apply constraints
5. Timing-critical paths: co-locate related cells with placement constraints
6. Scan chains: re-order after placement for minimum wirelength

### QoR Metrics to Evaluate
- Pre-CTS WNS: > −0.3 ns
- Cell density hotspots: flag if any region > 90%
- Estimated routing congestion overflow: flag if > 1%

### Output Required
- Placed DEF
- Pre-CTS timing report (setup and hold)
- Cell density and congestion report

---

## Stage: cts

### Domain Rules
1. Target skew: < 100 ps (or per SDC set_clock_uncertainty)
2. Max transition on clock nets: per technology DRC rule (150–200 ps)
3. Max fanout per clock buffer: per library (16–32)
4. Useful skew: only with explicit sign-off approval
5. Clock gating: integrate into CTS; verify enable pin timing
6. Multi-clock: handle each domain independently; check CDC after CTS

### QoR Metrics to Evaluate
- Global skew per domain: flag if > 150 ps
- Max insertion delay: flag if > 500 ps
- Post-CTS WNS (setup): flag if < −0.2 ns
- Post-CTS hold slack: must be ≥ 0 before routing

### Output Required
- Post-CTS DEF
- Clock tree report (skew, insertion delay per domain)
- Post-CTS timing report (setup and hold)

---

## Stage: routing

### Domain Rules
1. Sequence: global → track assignment → detailed → search-and-repair
2. Follow foundry DRC deck (spacing, width, via enclosure)
3. Shield critical clock and analog nets
4. Upper metals for power, lower metals for signals
5. Antenna rules: insert diodes or use jump-via strategy
6. Double/multi-patterning (7 nm and below): resolve same-colour violations

### QoR Metrics to Evaluate
- DRC violations: 0 at sign-off
- LVS errors: 0 at sign-off
- Post-route WNS: flag if < 0
- Routing overflow: 0

### Output Required
- Routed DEF
- DRC report
- LVS report
- Post-route timing report

---

## Stage: timing_optimization

### Domain Rules
1. Multi-corner: SS (setup), FF (hold), TT (typical)
2. Setup: upsize drivers, insert repeaters, retime registers
3. Hold: insert HVT delay buffers
4. Vt swapping: SVT/LVT for speed-critical; HVT for power-insensitive paths
5. ECO: formal ECO → place in reserved sites → re-route ECO nets
6. Do not modify scan chain order without DFT approval
7. Apply POCV/AOCV per foundry sign-off agreement

### QoR Metrics to Evaluate
- WNS: ≥ 0 all corners
- TNS: = 0 all corners
- Hold slack: ≥ 0 after fixing
- ECO cell count: flag if > 2% of total cells

### Output Required
- Timing closure report (all corners)
- ECO change list
- SPEF
- Updated routed DEF (post-ECO)

---

## Stage: power_optimization

### Domain Rules
1. Dynamic: clock gating insertion, operand isolation, multi-Vt swapping
2. Leakage: swap non-critical cells to HVT; verify timing after each batch
3. Power domains: validate UPF (isolation, level-shifters, retention regs)
4. Voltage islands: verify IR drop per domain
5. Always-on logic: verify correct library cells
6. Power gating: verify wakeup/shutdown sequences before routing changes

### QoR Metrics to Evaluate
- Total power: within spec budget
- Leakage: flag if > 15% of total at TT corner
- IR drop: < 5% VDD across all domains
- Post-power-opt WNS: must remain ≥ 0

### Output Required
- Power analysis report (dynamic + static, per domain)
- IR drop report
- Updated DEF (post-power-opt)
- UPF compliance report

---

## Stage: area_optimization

### Domain Rules
1. Remove redundant buffers and inverter pairs
2. Downsize non-timing-critical cells to minimum drive strength
3. Reclaim unused standard cell sites
4. Do not drop WNS margin below 50 ps buffer
5. Re-run DRC after any area ECO

### QoR Metrics to Evaluate
- Core utilisation: target 70–80%; hard limit 85%
- WNS: must remain ≥ 0
- DRC: must remain clean

### Output Required
- Area utilisation report (pre vs post)
- Updated DEF
- Cell count breakdown

---

## Stage: signoff

### Sign-off Pass Criteria (all must pass)
| Check | Criterion |
|-------|-----------|
| Setup WNS | ≥ 0 all corners |
| Setup TNS | = 0 all corners |
| Hold WNS | ≥ 0 all corners |
| DRC violations | = 0 |
| LVS errors | = 0 |
| Antenna violations | = 0 |
| IR drop | < 5% VDD |
| Metal density | Within foundry window |

### Domain Rules
1. STA sign-off: run all required PVT corners with POCV/AOCV
2. DRC: foundry-approved deck — zero violations
3. LVS: netlist vs layout — zero errors
4. ERC: electromigration and IR drop sign-off
5. Final GDS: merge all layers, add seal ring, chip-level DRC

### Failure Escalation
- Timing fail → timing_optimization
- DRC/LVS fail → routing
- Power/EM fail → power_optimization

### Output Required
- Sign-off STA report (all corners)
- DRC clean report
- LVS clean report
- Final GDS-II
- Completed tape-out checklist
