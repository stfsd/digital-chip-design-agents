# Agent Memory System

This directory holds persistent, file-based memory for the digital chip design orchestrators.
Agents read it at session start and write to it at session end — no new infrastructure required.

## Two-Tier Design

### Tier 1 — `experiences.jsonl`
Append-only JSONL file. One record per completed (or abandoned) orchestrator run.
Machine-parseable; grows over time; never edited manually.

### Tier 2 — `knowledge.md`
Human- and agent-readable distilled summary. Seeded with known failure patterns, successful
tool flags, and PDK/tool quirks. Intended to be periodically updated by a memory-keeper skill
(see `FUTURE_WORK.md`) as experience records accumulate.

## Experience Record Schema

```json
{
  "timestamp": "<ISO-8601>",
  "domain": "<domain>",
  "design_name": "<from state>",
  "pdk": "<from state if known, else null>",
  "tool_used": "<primary tool>",
  "stages_completed": ["<stage>", "..."],
  "loop_backs": {"<stage>": "<count>", "..."},
  "key_metrics": { "<domain-specific fields — see table below>" },
  "issues_encountered": ["<description>", "..."],
  "fixes_applied": ["<description>", "..."],
  "signoff_achieved": true,
  "notes": "<free-text observations>"
}
```

## Domain key_metrics Fields

| Domain       | key_metrics fields                                                    |
|--------------|-----------------------------------------------------------------------|
| architecture | `selected_arch`, `estimated_mhz`, `estimated_area_um2`              |
| compiler     | `isa_tests_passed`, `abi_compliant`, `regression_pass_rate`          |
| dft          | `scan_coverage_pct`, `atpg_fault_coverage_pct`                       |
| firmware     | `build_pass`, `flash_size_kb`, `bsp_tests_passed`                    |
| formal       | `proved`, `failed`, `unknown`                                         |
| fpga         | `lut_count`, `fmax_mhz`, `timing_met`                                |
| hls          | `latency_cycles`, `dsp_count`, `ii_achieved`                         |
| pd           | `wns_ns`, `drc_violations`, `lvs_errors`, `gds_area_um2`            |
| rtl-design   | `lint_errors`, `cdc_violations`, `synth_check_pass`                  |
| soc          | `ip_blocks_integrated`, `simulation_pass`, `memory_map_conflicts`    |
| sta          | `setup_wns_ns`, `hold_wns_ns`, `tns_ns`, `failing_paths`            |
| synthesis    | `wns_ns`, `cells`, `area_um2`, `lec_unmatched`                       |
| verification | `functional_coverage_pct`, `regression_failures`, `assertions_triggered` |

## Directory Layout

```
memory/
├── README.md                    ← this file
├── designs/                     ← per-design metric history (future use)
│   └── .gitkeep
├── architecture/
│   ├── knowledge.md             ← Tier 2: seeded domain knowledge
│   └── experiences.jsonl        ← Tier 1: created on first run
├── compiler/
├── dft/
├── firmware/
├── formal/
├── fpga/
├── hls/
├── pd/
├── rtl-design/
├── soc/
├── sta/
├── synthesis/
└── verification/
```

## How Orchestrators Use This

**Session start**: Read `memory/<domain>/knowledge.md` before the first stage.
Incorporate guidance into stage decisions — especially known failure patterns,
successful tool flags, and PDK-specific notes.

**Session end**: After signoff (or on escalation/abandon), append one JSON line to
`memory/<domain>/experiences.jsonl`. Create the file and parent directories if they
do not exist.
