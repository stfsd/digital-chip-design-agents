---
name: fpga-emulation
description: >
  FPGA prototyping — ASIC-to-FPGA RTL adaptation, multi-FPGA partitioning,
  synthesis and timing closure on FPGA, hardware bring-up, and software
  validation on the prototype. Use when porting an ASIC design to Xilinx or
  Intel FPGA for pre-silicon software development and hardware validation.
version: 1.0.0
author: chuanseng-ng
license: MIT
allowed-tools: Read, Write, Bash
---

# Skill: FPGA Emulation & Prototyping

## Invocation

- **If invoked by a user** presenting an FPGA prototyping task: immediately spawn
  the `digital-chip-design-agents:fpga-orchestrator` agent and pass the full user
  request and any available context. Do not execute stages directly.
- **If invoked by the `fpga-orchestrator` mid-flow**: do not spawn a new agent.
  Treat this file as read-only — return the requested stage rules, sign-off
  criteria, or loop-back guidance to the calling orchestrator.

Spawning the orchestrator from within an active orchestrator run causes recursive
delegation and must never happen.

## Purpose
Port an ASIC design to an FPGA prototype platform for pre-silicon hardware/
software co-development. The FPGA prototype is not cycle-accurate but
provides functional and architectural validation months before silicon.

---

## Supported EDA Tools

### Open-Source
- **Yosys** (`yosys`) — open-source synthesis for Xilinx/Intel/Lattice FPGA targets
- **nextpnr** (`nextpnr-xilinx`, `nextpnr-ice40`, `nextpnr-ecp5`) — place-and-route for open-source flows
- **OpenFPGALoader** (`openFPGALoader`) — universal FPGA programmer
- **Project IceStorm** — iCE40 FPGA toolchain (icepack, iceprog, icetime)
- **Project X-Ray** — Xilinx 7-series bitstream documentation

### Proprietary
- **Xilinx Vivado** (`vivado`) — synthesis, implementation, and bitstream generation for AMD/Xilinx
- **Intel Quartus** (`quartus_sh`) — synthesis and programming for Intel/Altera FPGAs
- **Microchip Libero** (`libero`) — synthesis and programming for PolarFire/SmartFusion FPGAs
- **Synopsys Synplify** — FPGA synthesis front-end targeting multiple device families

---

## Stage: rtl_adaptation

### ASIC → FPGA Substitutions
| ASIC Element | FPGA Replacement |
|---|---|
| SRAM macros | BRAM/URAM (Xilinx) or M20K (Intel) |
| Analog PLLs | MMCM (Xilinx) or ALTPLL (Intel) |
| IO pad cells | FPGA IOB + IOBUF primitives |
| Analog/mixed-signal | Stub model or remove |
| DFT scan logic | Remove — not needed on prototype |
| Power management cells | Remove — FPGA handles internally |

### Memory Replacement Rules
1. Match port configuration (single-port vs dual-port)
2. BRAM has 1-cycle read latency — verify RTL handles this
3. Memories > available BRAM: use external DDR via MIG/HBM controller
4. Use `XPM_MEMORY` (Xilinx) or equivalent portable macros

### Clock Replacement Rules
1. Replace ASIC PLL with MMCM (Xilinx) or ALTPLL (Intel)
2. Scale all clocks to FPGA prototype frequency (typically 50–100 MHz from ≥ 1 GHz ASIC)
3. Maintain same ratio between clock domains
4. Use BUFG for all global clocks — never route clocks on data fabric

### QoR Metrics to Evaluate
- No ASIC-specific primitives remain in adapted RTL
- All memories mapped to BRAM or external DDR
- Adapted RTL: lint clean, 0 errors
- Functional sim: adapted RTL produces same outputs as ASIC RTL

### Output Required
- Adapted RTL file set
- Substitution log (what was replaced and why)
- BRAM and MMCM resource estimate

---

## Stage: partitioning

### Domain Rules
1. Target utilisation per FPGA: < 70% LUT (leave room for ILA debug cores)
2. Minimise inter-FPGA signal count — each signal uses a physical connector pin
3. Never cut timing-critical paths at partition boundaries
4. Keep complete clock domains within a single FPGA wherever possible
5. Inter-FPGA: Aurora or GTH SERDES for high-speed; GPIO for slow control

### QoR Metrics to Evaluate
- Per-FPGA: LUT < 70%, BRAM < 80%, DSP < 80%
- Inter-FPGA signal count: within connector pin budget
- No clock domain split without explicit bridge

### Output Required
- Partition plan (block → FPGA mapping)
- Inter-FPGA signal list
- Physical connector pin assignment

---

## Stage: fpga_synthesis

### Domain Rules
1. Full Vivado (Xilinx) or Quartus (Intel) flow:
   synth → opt → place → route → phys_opt → bitstream
2. Timing target: WNS ≥ 0 at prototype frequency
3. If WNS < 0: reduce frequency first; add pipeline registers second
4. Utilisation targets: LUT < 70%, BRAM < 80%, DSP < 80%

### Debug Infrastructure (add before bitstream)
- ILA: up to 64 probes per core; trigger on errors or key FSM states
- VIO: drive and sample control/status signals from PC
- JTAG-to-AXI: register access from PC without re-synthesising

### Timing Closure Techniques
| Technique | When to Apply |
|-----------|--------------|
| Reduce clock frequency | First option — accept slower prototype |
| Add pipeline registers | When path identifiable and latency increase acceptable |
| Pblock constraints | Co-locate logic near BRAMs/DSPs |
| BUFG on high-fanout net | Break long high-fanout routes |
| phys_opt –directive AggressiveExplore | Last resort |

### QoR Metrics to Evaluate
- WNS ≥ 0 at prototype frequency
- LUT < 70%, BRAM < 80%, DSP < 80%
- Bitstream: no critical DRC errors
- ILA: configured on key debug signals

### Output Required
- Bitstream (.bit or .sof)
- Timing summary report
- Utilisation report
- ILA probe definition file

---

## Stage: bring_up

### Bring-up Sequence (follow in order)
1. Power-on: measure power rails; current within spec
2. FPGA configuration: load bitstream via JTAG or SPI flash
3. Clock verification: oscilloscope or ILA — verify frequency and stability
4. Reset: toggle reset; verify all status bits de-assert
5. Register access via JTAG-to-AXI: read chip-ID register — first functional test
6. Memory test: write and read-back BRAM and external DDR
7. UART console: CPU outputs boot messages — verify on serial terminal
8. Minimal firmware: bare-metal binary executes and prints PASS

### Common Failures
| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| MMCM lock never sets | PLL input freq out of range | Recheck MMCM config |
| CPU never outputs UART | Wrong reset vector or memory map | Check linker script |
| Register reads 0x00000000 | Base address wrong in SW | Compare memory_map.h vs HW |
| Register reads 0xDEADBEEF | Out-of-range access → DECERR | Fix address in driver |
| Intermittent data corruption | CDC issue in adapted RTL | Review clock crossings |

### QoR Metrics to Evaluate
- All clocks: correct frequency (measured)
- CPU: reaches UART prompt
- All peripheral registers: readable/writable via JTAG
- DDR memory test: passes (if present)

### Output Required
- Bring-up test results log
- ILA captures for any failures
- Known issues list for SW team

---

## Stage: sw_validation

### Domain Rules
1. Run embedded-firmware skill validation suite on FPGA prototype
2. Scale all timeouts by FPGA-to-ASIC frequency ratio (e.g., 20× for 50 MHz vs 1 GHz)
3. Record all performance measurements at FPGA frequency; note scale factor

### Hardware Bug vs Software Bug Triage
1. Reproducible deterministically? → likely HW bug
2. Same failure in RTL simulation? → RTL bug (fix RTL, not just firmware)
3. Different from RTL sim? → FPGA adaptation issue
4. Intermittent? → CDC or timing margin issue

### Validation Tiers on Prototype
| Test | Pass Criteria |
|------|--------------|
| BSP | All peripherals accessible |
| Driver unit | 100% per driver |
| System | Correct output vs golden |
| Long-run (4 hr) | 0 lockups, 0 unexpected resets |

### QoR Metrics to Evaluate
- All driver tests: PASS on prototype
- Application: correct output vs golden reference
- No lockups or unexpected resets in stress test
- Performance baseline: recorded at prototype frequency

### Output Required
- SW validation report
- Performance baseline (labelled as prototype-frequency values)
- Bug list (HW vs SW classification)
- Performance projection to silicon frequency

---

## Stage: proto_signoff

### Sign-off Checklist
- [ ] All clocks verified at correct frequency
- [ ] CPU boots and reaches application code
- [ ] All peripheral registers accessible
- [ ] All driver tests pass on prototype
- [ ] Application produces correct output
- [ ] 4-hour stress: clean
- [ ] All HW bugs filed to RTL team with ILA captures
- [ ] Performance baseline documented

### Output Required
- Prototype sign-off report
- Bug report for RTL team (HW bugs with ILA evidence)
- Performance baseline document
- Prototype user guide for SW development team

---

## Memory

### Write on stage completion
After each stage completes (regardless of whether an orchestrator session is active),
write or overwrite one JSON record in `memory/fpga/experiences.jsonl` keyed by
`run_id`. This ensures data is persisted even if the flow is interrupted or called
without full orchestrator context.

Use `run_id` = `fpga_<YYYYMMDD>_<HHMMSS>` (set once at flow start; reuse on each
stage update). Set `signoff_achieved: false` until the final sign-off stage completes.
