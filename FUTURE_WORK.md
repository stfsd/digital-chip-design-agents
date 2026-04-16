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
- PDK comparison: compare WNS/area across sky130 vs GF180 for the same RTL
- Tool comparison: compare Yosys vs DC synthesis area for the same design

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
