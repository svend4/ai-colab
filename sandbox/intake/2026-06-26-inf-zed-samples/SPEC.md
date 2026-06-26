# The `.inf` format — specification (draft 0.1)

A thin **plaintext envelope over an infon graph**. Each block is a typed unit
of information (an *infon*: relation + arguments + polarity) that carries a
**Q6 semantic address** in `{-1,+1}⁶` and **typed links** to other blocks.

`.inf` is optimised for **machine clustering and traversal**, not for human
prettiness. The human-facing layer is a *render target* (terminal or HTML),
not the source.

---

## 0. Why this exists (design rationale)

Three forces explain why no "richer-than-Markdown, lighter-than-HTML" format
has stuck, and how `.inf` sidesteps them:

1. **Training-data lock-in.** Models are fluent in Markdown/HTML/JSON because
   they were trained on oceans of it. A brand-new syntax starts with no corpus,
   so the model is *worse* at it — regardless of how well it is designed.
2. **Tokenizer effects.** Novel delimiters fragment into extra BPE tokens.
3. **The frontier moved to protocols, not document languages** (content
   negotiation, `llms.txt`, `CLAUDE.md`/`AGENTS.md`, MCP, generative UI).

`.inf`'s response: **confine all novelty to the envelope.** The block *body*
stays Markdown-ish, so the model still writes in its native register. The new
part is only a small, classically-parseable header + metadata + link layer that
makes the document **addressable, clusterable, and graph-walkable** by machine.

`.inf` therefore optimises a different axis than `llms.txt` (which optimises
human-readable *token efficiency*). It optimises **cluster-based work**:
predictable blocks + heavy metadata + a link graph an agent walks ("domino")
instead of full-scanning prose.

---

## 1. File and block structure

A file is a sequence of **blocks**. A block is:

```
<sigil> <id> [k:v ...]          ← header line (column 0)
  <key>: <value>                ← metadata lines (space after the colon)
  links: <edge> <edge> ...
  ──                            ← body separator
  <body...>                     ← verbatim body, dedented, until the next block
```

- A block **starts at column 0** with a sigil, so `grep '^∞'` lists every block.
- Everything from one header line until the next header line (or EOF) is one
  block.
- Lines beginning with `#` (before the body) are comments.

### Sigils and separators

| Role          | Canonical | ASCII alias |
|---------------|-----------|-------------|
| Block start   | `∞`       | `@@`        |
| Body separator| `──`      | `---`       |

The canonical glyphs are UTF-8; the ASCII aliases exist for environments where
typing `∞`/`──` is awkward. A parser MUST accept both.

---

## 2. Header line

```
∞ A1  type:decision  q6:-+--+-
```

- The **first token** after the sigil is the block **id** (unique within the
  file).
- Remaining whitespace-separated `key:value` tokens (**no space** after the
  colon) are **inline attributes**. By convention `type` and `q6` live here so
  the most-used metadata stays greppable on one line.

---

## 3. Metadata

Metadata lines inside a block use `key: value` (**a space after the colon**,
which is what distinguishes them from inline header attributes). Keys are
free-form; the following are **reserved**:

| Key     | Meaning                                                        | Example                          |
|---------|----------------------------------------------------------------|----------------------------------|
| `type`  | Block type (free vocabulary)                                   | `type:claim`                     |
| `q6`    | Semantic address, 6 chars of `+`/`-` (see §4)                  | `q6:-+--+-`                       |
| `rel`   | Infon relation name (the `R` in `⟪R, args, pol⟫`)              | `rel: zustaendig`                |
| `args`  | Infon arguments, comma list, optional `[ ]`                    | `args: [Träger, §10-II]`         |
| `pol`   | Polarity: `+` (holds) / `-` (does not hold). Default `+`       | `pol: -`                         |
| `links` | Typed edges to other blocks (see §5)                           | `links: →A2(begründet) ⇒A3(exc)` |

Any non-reserved key (`src`, `date`, `confidence`, …) is preserved verbatim in
the block's `attrs` and is available to tools but has no built-in semantics.

A suggested `type` vocabulary: `claim`, `evidence`, `definition`, `context`,
`question`, `decision`. Tools that don't recognise a type MUST still parse it.

---

## 4. The Q6 semantic address

`q6` is a 6-character string, each character `+` or `-`, interpreted as a point
in `{-1,+1}⁶`:

```
"-+--+-"  →  (-1, +1, -1, -1, +1, -1)
```

This is the bridge between the document and a routing/embedding scheme (e.g. a
`{-1,+1}⁶` sparse router). It is **not** part of classical situation theory; it
is an extra-logical *address* that makes clustering cheap.

- **Distance** between two addresses is the **Hamming distance** (number of
  differing positions), an integer in `0..6`.
- **Clustering** (§7) groups blocks by Hamming proximity — an O(differing-bits)
  operation that needs **no re-embedding** of the document.

`q6` is optional. Blocks without it are simply excluded from clustering.

> A 6-bit address gives 64 cells. It is deliberately coarse: it is a *bucket*
> for first-pass clustering and routing, not a full embedding. Finer addresses
> (`q8`, `q12`, …) are a forward-compatible extension; tools key off the prefix
> length, so `hamming` generalises unchanged.

---

## 5. Links — the "domino" graph

Each link is `<arrow><target>(<label>)`:

```
links: →A2(begründet)  ⇒A3(rückausnahme)  ·C1(frist)
```

- `<target>` is the id of another block.
- `(<label>)` is an optional relation label for that specific edge.
- `<arrow>` encodes the **edge kind**:

| Glyph | ASCII | Kind        | Intended meaning                          |
|-------|-------|-------------|-------------------------------------------|
| `→`   | `->`  | `elaborate` | forward / detail / "the next step"        |
| `⇒`   | `=>`  | `exception` | override / supersedes / carve-out         |
| `·`   | `..`  | `context`   | weak association / "see also"             |
| `⊢`   | `\|-` | `entails`   | logical entailment                        |

A bare target with **no arrow** defaults to `context`.

These edges are what an agent (or a TUI) **walks** instead of reading linearly:
read one block, follow its `elaborate` edges to drill in, its `exception` edges
to find overrides, its `context` edges to surface neighbours. The metadata of
one block pulls in the next — the domino chain.

---

## 6. Body

Everything after the `──` separator, until the next block, is the **body**:

- It is **verbatim**, except that **common leading indentation is stripped**
  (dedented), so authors may visually nest the body under the block while
  consumers receive clean text. *Relative* indentation inside the body is
  preserved (lists, code, etc.).
- The body is intended to be **Markdown-ish** — this is where the model writes
  in its native register, which is the whole point of the design.
- A body line MUST NOT begin (at column 0) with a sigil (`∞`/`@@`), since that
  starts a new block.

---

## 7. Semantics

### 7.1 Traversal (the walk)

A **walk** from a start block is a depth-first traversal that follows `links`:

- optionally filtered to a single edge kind (e.g. only `exception`),
- **cycle-safe** (a block is expanded once; back-edges are shown but not
  re-expanded),
- bounded by a maximum depth.

This turns retrieval into a **graph walk** rather than a full document scan.

### 7.2 Clustering

Given a Hamming **radius** `r`, blocks are grouped by **single-linkage
connected components**: two blocks join the same cluster when
`hamming(q6_a, q6_b) ≤ r`. At `r = 0`, only identical addresses cluster.
Blocks without `q6` are returned as singletons.

Because the address is fixed per block, clustering across *many* documents is
the same operation — which is what makes the format **federation-friendly**: a
block from document A and a block from document B with the same address cluster
automatically.

### 7.3 Validation

A conforming validator reports:

- **errors**: duplicate block ids; dangling links (target id absent);
  malformed `q6` (not exactly 6 chars of `+`/`-`).
- **warnings**: blocks with no `q6` (excluded from clustering); empty bodies;
  text outside any block.

---

## 8. Stated advantages (machine-first framing)

For a repo description / pitch, the benefits are framed around machine work,
not readability:

- **Block addressability** — every block has a semantic address; clustering is
  Hamming on metadata, no document re-embedding.
- **Graph navigation (domino)** — typed links let an agent step to the next
  relevant block instead of scanning; retrieval is a walk, not a full scan.
- **Cheap context selection** — pull only blocks whose address is within
  Hamming-`r` of the query; the context window becomes a working set, not a
  dump.
- **Compositionality / federation** — self-describing units deduplicate,
  recombine, and federate across sources; same-address blocks cluster across
  documents.
- **Deterministic parsing** — a fixed block schema is parseable by classical
  tools (`grep`, `jq`-like) *and* by the model, both deterministically.
- **Split reading load** — humans read the rendered view (terminal/HTML compile
  target); machines read the metadata layer. The source stays plaintext, so it
  is reviewable and `git diff`-able — which removes the usual objections to
  HTML-as-output (noisy diffs, unreviewable source, hosting/security tax).

---

## 9. Relation to other models (non-goals)

- **vs Markdown** — `.inf` *contains* Markdown (in bodies). It adds an
  addressable, linkable block envelope MD lacks. It is not a prettier MD.
- **vs HTML** — `.inf` is not a presentation format. Render to terminal
  (ANSI/Rich/Textual) or compile to HTML when a visual surface is wanted.
- **vs RDF / situation theory** — a block *is* an infon `⟪rel, args, pol⟫`,
  i.e. a reified n-ary statement; `links` are typed predicates between blocks.
  The classical situation-theory line (Barwise/Perry; infons assembled into
  ontology graphs) is the formal ancestor. `q6` is the one non-classical
  addition: an extra-logical address for cheap clustering/routing. A block graph
  maps cleanly onto RDF triples / an OWL n-ary pattern if a formal backend is
  wanted.
- **Not a programming language.** It is a *file format* — a parseable envelope.

---

## 10. Reference tooling

`infon.py` (zero dependencies, Python 3.8+, stdlib only):

```
python infon.py view        FILE.inf              # render every block
python infon.py tree        FILE.inf ID [--kind elaborate] [--depth N]
python infon.py clusters    FILE.inf [--r N]      # Q6 Hamming clusters
python infon.py validate    FILE.inf              # structural issues
python infon.py stats       FILE.inf              # summary counts
python infon.py from-nodelink FILE.json [-o OUT]  # networkx node-link → .inf
```

`from-nodelink` converts a networkx node-link JSON graph (e.g. a NormenKG
export) into `.inf`. If a node lacks a real `q6`, a **placeholder** address is
derived from its `type` so clustering has signal in demos — in production this
MUST be replaced with the real routing output.

Terminal rendering uses pure ANSI escape codes and auto-disables when output is
not a TTY (or with `--no-color`). A richer TUI (Textual) is an optional upgrade,
not a dependency.

---

## 11. Minimal example

```
∞ A1  type:decision  q6:-+--+-
  rel:   zustaendig
  args:  [Träger-örtlich, §10-II-SächsAGSGB]
  links: →A2(begründet)  ⇒A3(rückausnahme)  ·C1(frist)
  ──
  Örtliche Zuständigkeit liegt beim örtlichen Träger nach §10 Abs. 2 SächsAGSGB.
```

See `example.inf` for a 10-block graph that forms three clean Hamming-radius-1
clusters (jurisdiction / rate-calculation / deadline) plus one outlier.

---

*Draft 0.1. The envelope is intentionally small; extend the `type`, edge-kind,
and address-length vocabularies rather than the core grammar.*
