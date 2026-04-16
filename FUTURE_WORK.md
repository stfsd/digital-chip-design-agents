# Future Work

Items deferred from the two-tier agent memory system implementation (see `memory/README.md`).
Track these as follow-up issues after the initial memory system ships.

## 1. Memory-Keeper Skill

A skill (or infrastructure stage) that periodically distills `memory/<domain>/experiences.jsonl`
into an updated `memory/<domain>/knowledge.md` summary. Without this, the knowledge file stays at
its seeded content while experience records accumulate. The skill should:

- Read all records in `experiences.jsonl` for a domain
- Extract recurring issues, successful fixes, and tool flag patterns
- Update the `knowledge.md` with distilled learnings, preserving existing content that is still accurate
- Be invocable manually or on a schedule (e.g., after every 10 runs)

## 2. Semantic Search Over Experiences

An MCP memory server that embeds experience records and allows orchestrators to query by similarity
(e.g., "what fixed WNS issues on sky130 before?") rather than full-file read.

**Prerequisite**: Experience log must be large enough to justify the infrastructure overhead —
target threshold is ~50 records per domain before semantic search adds value over keyword grep.

Implementation options:
- SQLite + sqlite-vec extension (zero-dependency, file-based)
- Chroma or Qdrant (local Docker container)
- Hosted: Pinecone, Weaviate Cloud

## 3. Cross-Design Metric Trending

A reporting utility or dashboard that reads all `memory/<domain>/experiences.jsonl` files and
plots QoR trends (WNS, area, coverage) across runs for a named design. Use cases:

- Regression detection: alert when a metric degrades across runs
- PDK comparison: compare WNS/area across sky130 vs GF180 for the same RTL
- Tool comparison: compare Yosys vs DC synthesis area for the same design

Implementation: Python script + matplotlib, or a Jupyter notebook in `tools/qor_trends.ipynb`.

## 4. Infrastructure Orchestrator Memory

Track tool versions, install paths, and MCP configuration choices across setups in
`memory/infrastructure/`. Deferred because:

- Infrastructure state is environment-specific (machine A ≠ machine B)
- The value is lower than domain memory — tool version is better tracked in a lockfile
- MCP configuration is already stored in `.claude/settings.json`

Revisit if tool version mismatches cause repeated debugging across sessions.
