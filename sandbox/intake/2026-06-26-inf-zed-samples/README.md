# infon — `.inf` block format

A thin plaintext envelope over an **infon graph**: each block is a typed unit of
information (relation + args + polarity) carrying a **Q6 address** in `{-1,+1}⁶`
and **typed links** to other blocks. Optimised for **machine clustering and
graph traversal**, not human prettiness. The body stays Markdown-ish; only the
envelope is new.

- **Spec:** [`SPEC.md`](SPEC.md)
- **Tooling:** [`infon.py`](infon.py) — zero dependencies, stdlib only, Python 3.8+
- **Example:** [`example.inf`](example.inf)
- **Tests:** `python test_infon.py` (19 tests, stdlib `unittest`)

## Quickstart

```bash
python infon.py stats     example.inf      # summary
python infon.py clusters  example.inf --r 1  # Q6 Hamming clusters
python infon.py tree      example.inf A1     # walk the "domino" graph
python infon.py validate  example.inf
```

Run on your own knowledge graph (networkx node-link JSON, e.g. a NormenKG
export):

```bash
python infon.py from-nodelink yourgraph.json -o yourgraph.inf
python infon.py clusters yourgraph.inf --r 1
```

## The idea in one line

`llms.txt` optimises human-readable token efficiency; `.inf` optimises the other
axis — **predictable blocks + heavy metadata + a link graph an agent walks**
("domino") instead of full-scanning prose, with a Hamming-addressable Q6 cell
per block so clustering is cheap and federation-friendly.

License: Apache-2.0
