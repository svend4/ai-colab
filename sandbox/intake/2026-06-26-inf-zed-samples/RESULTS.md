# Falsification: does the `.inf` substrate reduce LLM coordination work?

A measured answer to the claim threaded through this whole build — that
**territory reads + reference-not-repeat + verify-once + CRDT merge** cut the
work an LLM (or a team of agents) spends coordinating over shared knowledge.

Run it yourself: `python inf_falsify.py --source normenkg_slice.json --rounds 6`

## Method

Two protocols, N=2 agents, R=6 rounds, on a NormenKG slice (node-link → `.inf`):

- **Naive** — every agent reads the whole corpus every round; concurrent edits
  to one block are a manual merge conflict (git / "paste it all in").
- **Substrate** — every agent reads only its Q6 territory (Hamming ≤ radius),
  follows **one reference** into the shared block instead of re-reading the
  other side, **skips** blocks already in the trust registry (verify-once), and
  concurrent edits **auto-merge** (the CRDT in `inf_crdt.py`).

"Context fed" is an estimate (~chars/4, the usual rough token heuristic) summed
over every block read in every round — the quantity that drives both cost and
attention dilution.

A **radius sweep** is the point of the experiment: at radius 6 every block sits
in every territory, so the territory saving must vanish and only verify-once can
remain. An honest test has to be able to show its own failure mode.

## Result

| radius | naive ctx | substrate ctx | reduction | manual conflicts | re-reads saved |
|-------:|----------:|--------------:|----------:|:-----------------|---------------:|
| ≤ 1    | 3714      | 871           | **76.5%** | 6 → 0 (CRDT)     | 20             |
| ≤ 2    | 3714      | 1049          | 71.8%     | 6 → 0            | 36             |
| ≤ 3    | 3714      | 1379          | 62.9%     | 6 → 0            | 36             |
| ≤ 6    | 3714      | 2114          | 43.1%     | 6 → 0            | 45             |

(Token figures are estimates; the *shape* is what matters, and it depends on the
data, not on tuning.)

## Verdict

The claim **holds conditionally**. When the work partitions into disjoint Q6
territories and blocks get verified, the substrate feeds ~76% less context and
turns every manual merge conflict into zero (auto-resolved). As territories
overlap (rising radius) the territory saving decays; at radius 6 — a fully
shared corpus — it collapses to **verify-once only** (~43%, purely from skipped
re-reads).

So the substrate pays off **exactly to the degree the knowledge is partitionable
and reused.** That is the real design constraint, and it is falsifiable: a body
of knowledge that is genuinely entangled (no clean territories) and never
re-touched would show little gain. The two mechanisms separate cleanly — the
radius sweep isolates *territory + reference* (the part that decays) from
*verify-once* (the part that survives even when everything is shared).

## What this does and does not show

- **Shown (mechanical):** context volume fed, manual conflicts avoided,
  re-reads saved — measured deterministically, no model needed.
- **Not shown (accuracy):** whether the slimmer context yields *as good* an
  answer. That needs a model. `python inf_falsify.py --llama --endpoint
  http://localhost:8080/v1 --model <your-gguf>` runs the actual Stellungnahme
  task under both context sets on a local `llama-server` so you can judge output
  quality side by side. If the substrate's slim context loses an argument that
  was in a skipped block, the partition was wrong — and that is the next thing
  to measure on real case data.

## Where this sits

This closes the loop on the build: format (`.inf`) → tooling (`infon.py`) →
collaborative board (`board.jsx`) → offline CRDT substrate (`inf_crdt.py`,
`inf_collab.py`) → and now a measured check that the substrate earns its keep.
The honest takeaway is not "it always wins" but "it wins where knowledge is
partitionable and reused, and the harness tells you when it doesn't."
