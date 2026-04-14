---
name: sta
description: >
  Static timing analysis — multi-corner constraint validation, setup and hold
  analysis, timing exception review, and ECO guidance for closure. Use when
  running timing analysis on a design, reviewing timing violations, guiding
  ECO fixes, or performing timing sign-off for tape-out.
version: 1.0.0
author: chuanseng-ng
license: MIT
allowed-tools: Read, Write, Bash
---

# Skill: Static Timing Analysis (STA)

## Invocation

When this skill is loaded and a user presents a timing analysis task, **do not
execute stages directly**. Immediately spawn the
`digital-chip-design-agents:sta-orchestrator` agent and pass the full user
request and any available context to it. The orchestrator enforces the stage
sequence, loop-back rules, and sign-off criteria defined below.

Use the domain rules in this file only when the orchestrator reads this skill
mid-flow for stage-specific guidance, or when the user asks a targeted reference
question rather than requesting a full flow execution.

## Purpose
Multi-corner, multi-mode timing analysis, exception review, ECO-guided closure,
and timing sign-off. WNS ≥ 0 and TNS = 0 at all corners required for tape-out.

---

## Supported EDA Tools

### Open-Source
- **OpenSTA** (`sta`) — standalone open-source STA; runs tcl scripts in batch mode (see sequential flow note below)
- **OpenROAD STA subsystem** (`openroad -no_init`) — STA within the OpenROAD PD flow; runs sequentially via tcl script

### Proprietary
- **Synopsys PrimeTime** (`pt_shell`) — gold-standard multi-corner STA and power analysis
- **Cadence Tempus** (`tempus`) — concurrent multi-mode multi-corner STA with ECO guidance

### Sequential Flow Log Review (OpenSTA / OpenROAD STA)

OpenSTA (`sta`) and the OpenROAD STA subsystem (`openroad -no_init`) execute tcl script
commands sequentially. When run in batch mode the agent must parse the output log to
extract timing results — there is no interactive prompt to query mid-run.

**Key log patterns to parse after run completion:**
- `report_timing` output → extract WNS (worst negative slack) and critical path
- `report_tns` output → extract TNS (total negative slack) per corner
- `report_clock_skew` output → global skew and insertion delay per clock group
- `check_timing` → missing constraints, unconstrained endpoints, loops

**Batch invocation:**
```
opensta -no_splash -exit timing_check.tcl > sta.log 2>&1
# or via OpenROAD:
openroad -no_init -exit sta.tcl > sta.log 2>&1
```

Parse `sta.log` after completion. Apply loop-back rules (ECO guidance stage) if
setup/hold violations are found.

---

## Stage: constraint_validation

### Validation Checks
1. All clocks defined with correct period and waveform
2. All generated clocks: correct source and division/multiplication
3. No unconstrained paths: verify with `report_timing -unconstrained`
4. CDCs: correct false_path or max_delay applied
5. Multicycle paths: both `–setup N` and `–hold 1` specified
6. Input/output delays: match system-level timing budget
7. Timing exceptions: not overly broad (masking real violations)
8. Propagated vs ideal clocks: correct mode (ideal pre-CTS, propagated post-CTS)

### Common Constraint Errors
| Error | Consequence |
|-------|------------|
| MCP without hold correction | Hold violations introduced |
| False path too broad | Real timing issues masked |
| Generated clock missing | Path unconstrained |
| Wrong clock period | Over/under-constraining |

### QoR Metrics to Evaluate
- 0 unconstrained paths
- 0 clock definition errors
- All exceptions reviewed and documented

### Output Required
- Constraint QA report
- Clock summary (all clocks, sources, periods)
- Exception list with justifications

---

## Stage: multi_corner_analysis

### Required Corner Matrix
| Mode | Setup Corner | Hold Corner |
|------|-------------|-------------|
| Functional | SS/0.9V/125°C | FF/1.1V/−40°C |
| Test (at-speed) | SS/0.9V/125°C | FF/1.1V/25°C |
| Low Power | SS/0.9V/125°C | FF/1.1V/25°C |

### POCV/AOCV Application
1. AOCV: apply depth and location-based derating (pre-POCV designs)
2. POCV: apply parametric variation (sigma-based, per foundry agreement)
3. Clock uncertainty: pre-CTS ideal values → post-CTS propagated

### Path Analysis Priority
1. WNS path per corner (most critical single path)
2. TNS contribution (how many paths fail and by how much)
3. CDC paths with max_delay constraints
4. At-speed paths: launch/capture pair STA

### QoR Metrics — Sign-off Targets
| Metric | Target |
|--------|--------|
| Setup WNS | ≥ 0 all corners |
| Setup TNS | = 0 all corners |
| Hold WNS | ≥ 0 all corners |
| Hold TNS | = 0 all corners |

### Output Required
- Timing report per corner (setup and hold)
- WNS/TNS summary table across all corners
- Top 100 violating paths

---

## Stage: path_analysis

### Domain Rules
1. Group failing paths by root cause: long wire, weak driver, logic depth, high-Vt
2. Separate setup violations from hold violations — different fix strategies
3. At-speed violations: check launch/capture pair timing explicitly
4. False paths: verify every exception is still valid after PD changes
5. Reconvergent fanout: flag paths with reconvergence for careful ECO planning

### Output Required
- Failing path analysis (root cause per path group)
- Paths requiring ECO vs paths requiring SDC correction

---

## Stage: exception_review

### Domain Rules
1. Review every timing exception for correctness and scope:
   - `set_false_path`: verify the path is truly non-functional (not just inconvenient)
   - `set_multicycle_path`: verify both `-setup N` and `-hold 1` are set correctly
   - `set_max_delay`: verify value matches system-level timing budget
2. Overly broad exceptions: any exception matching > 1% of all paths requires architect approval
3. Exceptions masking real violations: revoke immediately and re-run path analysis
4. Every exception must have a documented justification (design intent, async crossing, test mode)
5. Post-ECO exceptions: verify any new exceptions added after ECO are still valid

### Common Exception Errors

| Error | Consequence |
|-------|------------|
| `set_false_path` on functional CDC | Real metastability risk hidden |
| MCP without hold correction | Hold violations introduced silently |
| Exception too broad (glob match) | Unintended paths unconstrained |
| Expired exception (removed logic) | Stale SDC — may mask other issues |

### QoR Metrics to Evaluate
- 0 exceptions without documented justification
- 0 overly broad exceptions (flagged for architect review)
- Exception list reviewed and signed off before ECO guidance begins

### Output Required
- Exception audit report (valid / revoked / needs-approval per exception)
- Revised SDC with invalid exceptions removed
- Exception sign-off record

---

## Stage: eco_guidance

### ECO Decision Tree
```
Setup violation:
  Logic depth > target?       → Retime / add pipeline stage
  Long wire (> 500μm)?        → Buffer insertion / reroute on upper metal
  Weak driver?                → Upsize driver cell
  High-Vt on critical path?   → Swap to SVT or LVT
  Reconvergent fanout?        → Clone cell / split net

Hold violation:
  Skew-induced (post-CTS)?    → Useful skew / targeted delay buffer
  Short path (< 1 cycle)?     → Insert HVT delay buffer
  New path from ECO?          → Targeted hold buffer at sink register
```

### ECO Rules
1. Minimum ECO footprint: fewest cell changes to fix the most violations
2. Prefer resize over add new cell (less routing impact)
3. ECO cells: place in pre-reserved ECO sites or free standard cell rows
4. Re-run STA after every ECO batch — never accumulate blind
5. LEC after every ECO: verify equivalence preserved
6. Never introduce new hold violations while fixing setup (and vice versa)

### QoR Metrics to Evaluate
- ECO efficiency: violations fixed per change
- ECO cell count: < 2% of total cells (flag if exceeded — upstream issue)
- Post-ECO LEC: EQUIVALENT

### Output Required
- ECO change list (cell, action, justification)
- Pre/post ECO timing comparison
- ECO LEC result

---

## Stage: sta_signoff

### Sign-off Checklist
- [ ] Setup WNS ≥ 0 at all corners
- [ ] Setup TNS = 0 at all corners
- [ ] Hold WNS ≥ 0 at all corners
- [ ] Hold TNS = 0 at all corners
- [ ] All exceptions valid and documented
- [ ] POCV/AOCV applied per foundry spec
- [ ] LEC clean post all ECOs

### Output Required
- Sign-off timing report (all corners, all modes)
- ECO change summary
- Timing sign-off record
