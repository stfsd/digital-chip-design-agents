# Future Work

Items deferred from the two-tier agent memory system implementation (see `memory/README.md`).
Track these as follow-up issues after the initial memory system ships.

## 1. Memory-Keeper Skill ✓ IMPLEMENTED

**Status:** Shipped — `plugins/infrastructure/skills/memory-keeper/`

A skill that periodically distils `memory/<domain>/experiences.jsonl`
into an updated `memory/<domain>/knowledge.md` summary. Implementation includes:

- `SKILL.md` — three-stage agent skill (load_experiences → distil_knowledge → report)
- `distill.py` — CLI helper: parses JSONL, computes issue/fix pairs, metric ranges, and
  tool-flag candidates; emits a structured JSON summary for the agent to use
- Invocable via `/chip-design-infrastructure:memory-keeper --domain <name>` or `--all`
- Threshold guard: skips domains with fewer than N records (default: 5)

## 2. Semantic Search Over Experiences

An MCP memory server that embeds experience records and allows orchestrators to query by similarity
(e.g., "what fixed WNS issues on sky130 before?") rather than full-file read.

**Prerequisite**: Experience log must be large enough to justify the infrastructure overhead —
target threshold is ~50 records per domain before semantic search adds value over keyword grep.

Implementation options:
- SQLite + sqlite-vec extension (zero-dependency, file-based)
- Chroma or Qdrant (local Docker container)
- Hosted: Pinecone, Weaviate Cloud

## 3. Cross-Design Metric Trending ✓ IMPLEMENTED

**Status:** Shipped — `tools/qor_trends.py`

A reporting utility that reads all `memory/<domain>/experiences.jsonl` files and
produces QoR trend tables and optional matplotlib charts for a named design. Use cases:

- Regression detection: flags when a metric degrades across runs (⚠ alert column)
- PDK comparison: compare WNS/area across sky130 vs GF180 for the same RTL _(not yet implemented — requires `--pdk` filter and grouping by the `pdk` field in experiences.jsonl)_
- Tool comparison: compare Yosys vs DC synthesis area for the same design _(not yet implemented — requires `--tool` filter and grouping by the `tool_used` field in experiences.jsonl)_

Usage:
```bash
# Text table for all domains where design "aes_core" appears
python3 tools/qor_trends.py --design aes_core

# WNS trend for synthesis only
python3 tools/qor_trends.py --design aes_core --domain synthesis --metric wns_ns

# Save a matplotlib chart
python3 tools/qor_trends.py --design aes_core --plot --output aes_core_qor.png
```

## 4. Infrastructure Orchestrator Memory

Track tool versions, install paths, and MCP configuration choices across setups in
`memory/infrastructure/`. Deferred because:

- Infrastructure state is environment-specific (machine A ≠ machine B)
- The value is lower than domain memory — tool version is better tracked in a lockfile
- MCP configuration is already stored in `.claude/settings.json`

Revisit if tool version mismatches cause repeated debugging across sessions.

## 5. Central "Design" State

Provide a structured object that all agents read/write to enable iterations instead of a linear flow
and make agents context-aware

### Minimum fields

- Spec (natural langauge + structured interpretation)
- Interfaces (e.g., AXI3-lite definition)
- Constraints (timing, area if available)
- RTL (current version)
- Verification status
- Tool feedback (if any)
- History (decisions, iterations)

## 6. Continuous Verification Loop

Generate testbenches from spec and run simulation (even basic), and detect 
functional mismatches and interface violations (e.g., AXI behavior), and feed 
failures back to the RTL agent

The flow changes from:

Architecture --> RTL --> Verifcation

To:

RTL --> Verify --> Fix --> Verify --> (Repeat until pass)

## 7. Agent Contract Standardization

**Feature**: Unified agent I/O contract

- Input
  - design_state
  - Task definition
- Output
  - Updated design_state fields
  - Artifacts (RTL, reports, etc)
  - Status (success/fail/needs clarification)
  - Confidence level
  - Suggested next step

This is important to prevent agent drift, make orchestration predictable and 
enable retry logic later

## 8. Constraint Awareness

Agents should handle clock assumptions, interface requirements and basic performance expectations

**Agent Behavior Changes**:

- Query constraints before generating output
- Justify decisions relative to constraints

## 9. Architecture Exploration Improvement

Architecture agent should:

- Generate multiple candidate designs
- Compare them on:
  - Complexity
  - Expected performance
- Select or refine

This is an important step as it helps to reduce early bad decisions and makes
the system more robust without needing perfect prompts

## 10. Structured Failure Handling

Define failure classes:

- Invalid RTL
- Verification failure
- Interface mismatch
- Incomplete spec

Each agent should tag failures and suggest retry strategies, such as regenerate,
refine, escalate, etc

## 11. Human-in-the-loop Control Points + Observability

Insert checkpoints after architecture generation, before final RTL freeze, etc
Agents can ask for clarification if spec is ambigious and/or request for approval
before proceeding
This can help to ensure that there are always checkpoints where humans can review
the agents work before moving on to the next stage

Add execution trace to track which agent did what, why decisions are made and how
design evolved
This is to make sure there is a clear relationship between decision and output
