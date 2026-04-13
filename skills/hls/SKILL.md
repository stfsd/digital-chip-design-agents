---
name: hls
description: >
  High-Level Synthesis — C/C++ algorithm analysis, HLS directive optimisation,
  synthesis execution, and co-simulation verification. Use when converting C/C++
  to synthesisable RTL, optimising for latency/throughput/area targets using
  pragmas, or verifying that generated RTL matches the golden C model.
version: 1.0.0
author: chuanseng-ng
license: MIT
allowed-tools: Read, Write, Bash
---

# Skill: High-Level Synthesis (HLS)

## Invocation

When this skill is loaded and a user presents an HLS task, **do not execute
stages directly**. Immediately spawn the
`digital-chip-design-agents:hls-orchestrator` agent and pass the full user
request and any available context to it. The orchestrator enforces the stage
sequence, loop-back rules, and sign-off criteria defined below.

Use the domain rules in this file only when the orchestrator reads this skill
mid-flow for stage-specific guidance, or when the user asks a targeted reference
question rather than requesting a full flow execution.

## Purpose
Convert C/C++/SystemC algorithmic descriptions to synthesisable RTL.
Covers algorithm analysis for HLS compatibility, pragma/directive optimisation,
and co-simulation to verify RTL matches the golden C model.

---

## Stage: algorithm_analysis

### HLS-Hostile Patterns (must fix before synthesis)
1. Dynamic memory (malloc/new) → replace with fixed-size static arrays
2. Recursive functions → convert to iterative with explicit stack
3. Pointer aliasing → use `restrict` keyword or restructure accesses
4. System calls (printf, file I/O) → wrap in `#ifndef __SYNTHESIS__`
5. Function pointers → replace with switch/case dispatch
6. Data-dependent loop bounds → add maximum bound + early-exit flag
7. Floating-point → evaluate fixed-point (`ap_fixed<W,I>` for Vitis HLS)

### Analysis Steps
1. Identify innermost critical loop — the performance bottleneck
2. Analyse loop-carried dependencies — limit achievable II
3. Classify memory access: sequential (burst-able) vs random (expensive)
4. Calculate theoretical minimum latency: trip_count × body_latency

### QoR Metrics to Evaluate
- All HLS-hostile patterns resolved
- Critical loop identified with dependency graph
- Theoretical II lower bound computed

### Output Required
- Algorithm analysis report
- Fixed-point type recommendations (if applicable)
- Critical loop dependency graph

---

## Stage: directive_planning

### Pipelining and Throughput
```cpp
#pragma HLS PIPELINE II=1          // Pipeline loop, target II=1
#pragma HLS DATAFLOW                // Task-level pipelining
#pragma HLS LOOP_FLATTEN            // Flatten nested loops
#pragma HLS LOOP_MERGE              // Merge sequential loops
```

### Latency and Unrolling
```cpp
#pragma HLS UNROLL factor=4        // Partial unroll (4 parallel copies)
#pragma HLS UNROLL                  // Full unroll (small trip counts only)
```

### Memory and Interfaces
```cpp
#pragma HLS ARRAY_PARTITION variable=buf cyclic factor=4
#pragma HLS INTERFACE mode=axis port=data       // AXI4-Stream
#pragma HLS INTERFACE mode=m_axi port=mem       // AXI4 master
#pragma HLS INTERFACE mode=s_axilite port=ctrl  // AXI4-Lite registers
```

### Resource Binding
```cpp
#pragma HLS BIND_OP op=mul impl=dsp      // Force multiply to DSP
#pragma HLS ALLOCATION operation=mul limit=4   // Cap DSP count
```

### Strategy by Target
| Target | Primary Directives |
|--------|--------------------|
| Low latency | UNROLL + PIPELINE II=1 |
| High throughput | PIPELINE + DATAFLOW + ARRAY_PARTITION |
| Low area | ALLOCATION limits + no UNROLL |
| Balanced | PIPELINE II=1 inner loop + ARRAY_PARTITION |

### QoR Metrics to Evaluate
- Achieved II: ≤ target
- Latency: ≤ target cycles
- Area: within budget
- No directive synthesis errors

### Output Required
- Annotated source with all directives and justifications
- Directive justification table

---

## Stage: hls_synthesis

### Domain Rules
1. Synthesise at target clock period
2. Check HLS report: latency, II, resource usage
3. Compare achieved vs target — loop back to directives if miss
4. Flag any warnings: unresolved dependencies, failed II, inferred latches
5. Verify interface protocols match system integration requirements

### QoR Metrics to Evaluate
- II: matches or beats target
- Latency: within target cycles
- Area: within budget
- No latch inference warnings

### Output Required
- HLS synthesis report (latency, II, resource summary)
- Generated RTL files
- Unresolved warnings with justification

---

## Stage: rtl_qc

### Domain Rules
1. Run lint on HLS-generated RTL (same rules as rtl-design skill)
2. Verify no latches in generated RTL
3. Verify interface signal names match integration requirements
4. Check all registers reset correctly

### QoR Metrics to Evaluate
- Lint: 0 errors
- No latches inferred
- Interface ports match integration spec

### Output Required
- Lint report on HLS-generated RTL

---

## Stage: cosimulation

### Domain Rules
1. C testbench drives RTL through HLS wrapper
2. RTL outputs compared against C golden model automatically
3. Measure actual latency and II — must match HLS report ±5%
4. Exercise all code paths; test boundary conditions

### Common Failures
| Failure | Fix |
|---------|-----|
| Output mismatch | Check fixed-point overflow; increase bit widths |
| AXI handshake error | Fix INTERFACE pragma configuration |
| Latency differs | Verify loop bounds are static |
| X propagation | Initialise all variables in C source |

### QoR Metrics to Evaluate
- Co-simulation: 100% output match with C golden model
- Latency measured: within 5% of HLS report
- II measured: matches HLS report exactly
- No simulation errors or X propagation

### Output Required
- Co-simulation pass/fail report
- Latency and II measurement log

---

## Stage: hls_signoff

### Sign-off Checklist
- [ ] All HLS-hostile patterns resolved
- [ ] Latency and II targets met in synthesis
- [ ] Area within budget
- [ ] RTL QC: lint clean, no latches
- [ ] Co-simulation: 100% output match
- [ ] Interface ports match system integration spec

### Output Required
- HLS RTL package (generated .v/.sv files)
- Co-simulation pass report
- HLS QoR report (latency, II, area)
- Interface documentation
