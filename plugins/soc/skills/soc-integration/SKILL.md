---
name: soc-integration
description: >
  SoC IP integration — IP procurement and qualification, IP configuration,
  bus fabric setup, top-level RTL integration, and chip-level simulation.
  Use when assembling a SoC from multiple IP blocks, configuring an AXI
  bus interconnect, integrating memory macros, or running chip-level tests.
version: 1.0.0
author: chuanseng-ng
license: MIT
allowed-tools: Read, Write, Bash
---

# Skill: SoC IP Integration

## Invocation

When this skill is loaded and a user presents a SoC integration task, **do not
execute stages directly**. Immediately spawn the
`digital-chip-design-agents:soc-integration-orchestrator` agent and pass the full
user request and any available context to it. The orchestrator enforces the stage
sequence, loop-back rules, and sign-off criteria defined below.

Use the domain rules in this file only when the orchestrator reads this skill
mid-flow for stage-specific guidance, or when the user asks a targeted reference
question rather than requesting a full flow execution.

## Purpose
Assemble a complete SoC from first-party RTL, licensed hard/soft IPs, and
memory macros. Covers IP procurement, bus fabric configuration, top-level
integration, and chip-level simulation sign-off.

---

## Stage: ip_procurement

### IP Qualification Checklist
- [ ] Deliverable format: RTL (.v/.sv), GDSII, or encrypted netlist?
- [ ] Technology node: certified for target process?
- [ ] Timing libraries: SS/TT/FF corners available?
- [ ] LEF/DEF: available for PD flow?
- [ ] Simulation models: behavioural/RTL for verification?
- [ ] UPF: power intent delivered?
- [ ] Databook: register map, timing diagrams, integration guide?
- [ ] DFT: scan-enabled? BIST available?
- [ ] Silicon proven: on which node?
- [ ] Support SLA: bug-fix and update commitment?

### Hard IP vs Soft IP
| Aspect | Hard IP (GDSII) | Soft IP (RTL) |
|--------|----------------|---------------|
| Area | Fixed | Synthesis-dependent |
| Timing | Characterised libs only | Optimisable |
| PD effort | Place as macro | Full PD flow |
| Customisation | None | Parameterisable |

### Memory Macro Qualification
1. Verify compiler-generated views: .lib, .lef, .v (behavioural)
2. Check access time vs target frequency
3. Verify retention/power-down modes (for UPF power domains)
4. Confirm MBIST ports available

### Output Required
- IP qualification report per IP
- IP deliverable checklist (all views received)
- IP risk register (gaps in deliverables)

---

## Stage: ip_configuration

### Domain Rules
1. Configure each IP per its databook for target use case
2. Parameterise data widths, FIFO depths, feature enables
3. Verify configured timing meets target frequency at worst-case corner
4. Verify interface widths match bus fabric port requirements
5. Generate integration wrapper if IP port names differ from system conventions

### Output Required
- Configured IP files and wrappers
- Timing verification report (configured corner)

---

## Stage: bus_fabric_setup

### Bus Fabric Selection
| Fabric Type | Use Case | Bandwidth |
|-------------|---------|-----------|
| AXI4 Crossbar | High-bandwidth data paths | High |
| AXI4-Lite | Low-bandwidth control registers | Low |
| APB3 | Peripheral register access | Low |
| NoC | Many-core topologies | Very High |

### Domain Rules
1. Non-overlapping address regions for all slaves
2. AXI width adapters for any width mismatches
3. Async bridges for all cross-clock-domain connections
4. QoS: assign traffic class for latency-sensitive masters
5. Error handling: out-of-range address → DECERR response defined

### Memory Map Validation
- No address region overlaps
- All peripherals accessible from all required masters
- Reserved regions return DECERR
- No unintended address aliasing

### QoR Metrics to Evaluate
- Address decode: complete, no gaps, no overlaps
- All IP blocks connected with correct port width
- CDC bridges in place for all clock crossings

### Output Required
- Bus fabric configuration file
- Memory map document (final, versioned)
- Address decoder verification report

---

## Stage: top_integration

### Domain Rules
1. Top module: wiring only — no logic at top level
2. All IPs instantiated once (no unintended duplicates)
3. All ports connected — lint check for unconnected active signals
4. Clock generation: PLL/mux module at or near top level
5. Reset generation: synchroniser per domain at top level
6. Tie cells: VDD/VSS tie-offs for all floating inputs
7. Scan chain: SI/SO routed through scan backbone
8. JTAG: TDI/TDO routed through JTAG chain

### Integration Checklist (per IP)
- [ ] Correct module name and parameters
- [ ] All active ports connected
- [ ] Clock: correct domain
- [ ] Reset: correct domain and polarity
- [ ] Power ports: correct UPF domain
- [ ] Scan: SI/SO connected

### Common Integration Bugs
| Bug | Consequence |
|-----|------------|
| Wrong clock domain | Metastability in silicon |
| Reset polarity inversion | Block never exits reset |
| Unconnected valid/enable | Block runs freely or never |
| AXI address offset wrong | Peripheral at wrong base address |

### Output Required
- Top-level RTL (soc_top.sv)
- Integration lint report
- IP connectivity summary

---

## Stage: chip_level_sim

### Required Tests
1. Boot test: CPU boots from reset vector, executes code
2. Peripheral access: read/write all peripheral registers
3. DMA: transfers between memory regions verified
4. Interrupt: each peripheral can interrupt CPU and ISR fires
5. Multi-master: concurrent bus access from multiple masters
6. Clock switching: clock mux operates correctly
7. Power modes: enter and exit sleep/deep-sleep
8. Reset: warm and cold reset; all blocks re-initialise

### QoR Metrics to Evaluate
- All peripheral register tests: PASS
- Boot test: CPU reaches application code
- DMA: correct data at correct address
- No AXI protocol violations (checker clean)
- No X propagation at key outputs after reset

### Output Required
- Chip-level simulation report
- Per-test pass/fail log
- Protocol checker clean report

---

## Stage: integration_signoff

### Sign-off Checklist
- [ ] All IP qualification issues resolved
- [ ] Memory map: final, agreed, no overlaps
- [ ] Top-level lint: 0 unconnected active ports
- [ ] CDC: 0 violations at chip level
- [ ] All chip-level simulation tests: PASS
- [ ] AXI protocol checker: clean

### Output Required
- Integration sign-off report
- Final memory map document
- Integrated SoC RTL package (ready for synthesis)
