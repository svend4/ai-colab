# Кристаллизация: new-problems-2026-06-23 и session-state-2026-06-23
> [!NOTE]
> Этот файл был сгенерирован алгоритмом Entropic Decay Monitor.
> Оригинальные файлы сохранены в неприкосновенности.

## Общие смысловые тезисы (пересечение)
- Md:52`), or (b) keep the sync subprocess client as the in-repo check (`docs/mcp-stdio-windows-pipe-diagnostics-2026-06-21.
- ---

## рекомендованные назначения

| problem | кому / как | mode | effort |
| --- | --- | --- | --- |
| **f-020 gate-poison** — wire the missing `friction.
- Py:279-307` (`section_flow` — substring scan that already flags ungrounded accepted decisions), `:295-296` (the `did not in surface_text` test to replace with the key join).
- ",
    ],
    "docs": ["topics/gate-poison-situation-2026-06-22.
- Environment note (verified read-only on this machine, 2026-06-23): the runtime here is python 3.
- Py:47-52` (`levels`, `l3_dirs`), `:59-72` (`level_of` — dir-derived, returns l3 for any `decisions/` file), `:92-101` (`_has_decision_ref` — runtime gate arg, not a registry link), `:261` (`decision_ref` stamp).
- Py:52` — which is prose, not a structured key (confirmed by grep: the sole hits are the `why` literal, the `evidence` literal at `:123`, and `"decisions"` as a directory name at `:389`).
- Py reports error=n>0 (often a foreign half-done task: done card with a missing deliverable, broken topic link, bad front-matter, or duplicate id) so the pre-commit hook blocks commits for everyone.
- The only **ratify** sub-option is the inverse `surfaced_by` key on decision front-matter — leave it out of the first ship; one direction is enough for traceability.
- Py recipe gate-poison` resolves to `none` → `cmd_recipe` prints `"unknown friction id/alias: gate-poison"` and returns 1 (`:660-666`).
- Create_subprocess_exec` with pipes succeeds — confirmed working on this host today and listed as a workaround in the diagnostics (`docs/mcp-stdio-windows-pipe-diagnostics-2026-06-21.
- Md:109-111`, `:114`): only the **read-only detector** is in scope and pre-approved (it is already live in `cohort guard`).
- Md:24`, and item #4 at `:73`) records these as "flow-сироты" (d-008/d-004/d-009/d-002) and the fix today is manual: hand-weave each decision's text into `agents.
- Py`) is already shipped and verified green here, so the remaining work is the one read-only documentation edit: update the gateway doc's runtime caveat (`drivers/gateway.
- (optionally add the inverse key `surfaced_by: [collab-protocol]` to decision front-matter for a two-way check, but one direction is enough to make the path traceable and avoids editing the ratify-gated decision registry.
- The half-done quarantine that distinguishes warn vs error lives at `tools/validate.
- ",
        "merge back only once the shared gate is green again.
- No mutator boundary is crossed and the ratify-gated `decisions/` registry is **not** touched (the join key lives on the instruction side by design).
- Py:15`) for the decision's `status` — no new parser/index, matching the stated reuse discipline of `assurance.
- " the `q016-assurance-state` topic (`topics/q016-assurance-state-2026-06-23.
- "
```

### governance note (do not over-reach in this change)

the synthesis is explicit (`topics/friction-subsystems-synthesis-2026-06-22.
- (decision front-matter: `id/type/title/status/date/participants` only — no surface/level key; cross-links only in prose, e.
- ### design: a shared key + a small read-only tracer

two additive pieces, no behavior change to existing contracts:

**(1) shared key `surfaces` on instruction entries.
- 15 with the default `windowsproactoreventlooppolicy`, and on this box `asyncio.
- Append({"trigger": "gate-poison", "files": poison_errs or ["validate error>0"], "recipe": "gate-poison"})`.
- ### the fix / workaround (already designed, verified here)

the chosen design is a **synchronous, transport-independent `tools/call` acceptance** that bypasses the async overlapped-pipe path entirely, staying fully read-only:

1.
- Py:298-302`) from a fuzzy text match into an exact join, and lets the apex dashboard report, per decision, *which* instruction and *which* level grounds it — i.
- - `c:/users/stefan/documents/new project ai colab/topics/gate-poison-situation-2026-06-22.
- Py:262-271`); there is no f-020 and no `gate-poison` alias.
- Crucially the gap is *not* in gateway logic — `initialize` and `tools/list` (handshake) pass; what was blocked is the vertical `tools/call` acceptance over the official async stdio transport.
- |
| **gateway windows async-stdio `call_tool` blocker** — adopt portable sync `tools/call` acceptance as canonical gate | code fix already landed and verified green (`mcp_sync_acceptance.
- Py` per-agent/per-zone so one foreign error does not block all — changes the shared gate contract, is owned by integrator/stefan (d-021), and must go through d-017/d-018 collective acceptance.
- ) |
| **base↛apex shared key + tracer** — `surfaces` join key on instruction entries + read-only `trace(d-nnn)` + tighten `section_flow` | any agent touching the assurance/instructions surface: edits live **only** on the instruction side (`instructions.
- Py:164-171` (questions) and `:194-202` (tasks): an open/doing task whose topic file is missing = warn (carantine), a **done** task with missing deliverable = error (poison).
- Md:53`), there is no in-loop policy swap that fixes it; the only ways to get the *official async* client green are (a) run acceptance in an environment where `asyncio.
- Py is blind to the single most dangerous shared-tree state, exactly as the synthesis docs note (`topics/friction-subsystems-synthesis-2026-06-22.
- Py"],
    "aliases": ["gate-poison", "poison", "validate-error"],
},
```

the `"gate-poison"` alias is the load-bearing fix: it makes the cross-link emitted at `tools/cohort.
- ",
        "if the offending source maps to your claim, fix it; if it is foreign/unknown, do not wait — escalate to a level 1 worktree from a clean base (python tools/cohort.
- ",
        )
    return make_check("f-020", "ok", "shared validate gate is green")
```

`import re` must be added to the import block at `tools/friction.
- Py:261`), but that is a runtime gate argument, not a persistent registry link, and it is keyed on the *artifact being promoted*, not on the base decision.
- All of the above stays inside the safety envelope: the gateway is `mode: read-only` / `sandbox: not-required-for-read-only` (`drivers/gateway.
- Py:59-72`) deriving a level **purely from the artifact's top-level directory** (`core`→l1, `portals`→l2, `tasks/decisions/questions/streams/topics/collab`→l3, `sandbox`→l4).
- | inline (doc) | xs — single doc-caveat edit; the code is already shipped and verified.
- ---

## diagnosing and fixing the gateway's windows async-stdio `call_tool` blocker

### what "ready-except-mcp-stdio-call-acceptance" actually means

the `gateway` driver composes three ready leaf drivers (`files`, `repo-runner`, `workbench`) into one mcp server named `ai-os-bridge` (`drivers/gateway/mcp_server.
- F-020 is whole-tree commit-blocking (highest severity per the automation ladder `docs/friction-ledger.
- Py`), not the ratify-gated `decisions/` registry.
- ---

## base↛apex: the missing shared key between the instruction registry and the promotion pyramid

### the break, confirmed in the live repo

there are three independent namespaces that never share a key, so no single lookup walks a base decision up to the apex:

1.
- ---

## f-020 gate-poison: wire the missing friction.
- Cross-link the verdict (one canonical id, both directions):**
- cohort→friction is fixed automatically by step 1 (the `gate-poison` alias now resolves; `tools/cohort.
- Md:7-9`, risk ladder `:18-22`), and the acceptance path only reads fixtures within the allowed-root and routes every call through `drivers/audit.
- Py` reuses `syncmcpclient` and extends it from handshake to a real `tools/call` on **every** tool with fixture arguments (`drivers/mcp_sync_acceptance.
- Add the f-020 registry entry** — append one dict after the f-019 block at `tools/friction.
- Md:5`), but the doc qualifies this at runtime: it is *not* considered to have passed full `call_tool` mcp acceptance in the official async stdio client on windows until a separate runtime blocker is closed or a synchronous `tools/call` acceptance is added (`drivers/gateway.
- Py`), not the decision side, so it does **not** edit the ratify-gated `decisions/` registry (the `topics/q016-assurance-state` doc marks decision-registry edits as "ratify"/котёл d-018; instruction-surface edits are the lighter path).
- > **shipped 2026-06-23 — все три зашиплены, документ переведён в `status: resolved`:**
> - **f-020 gate-poison** (`67fa8b5`): f-020 registry-запись + `check_gate_poison()` + `collect_status`/`recommendation` в `friction.
- Py:282-288`), then for every `accepted` decision checks `if did not in surface_text` and reports "accepted-решения, не упомянутые в поверхности инструкций" (`assurance.
- This is the concrete, portable closure of the call-acceptance gap; the project-wide run reports 19→23 tools/call green across servers (`tasks/t-101.
- The detector half is **pre-approved** (already live in `cohort guard`); only the structural validate-scoping spinoff is **ratify** (d-021, gated by d-017/d-018).
- ---
id: new-problems-2026-06-23
type: topic
title: three newly-surfaced producer-workflow problems + designs (2026-06-23)
status: resolved
date: 2026-06-23
related: [friction-subsystems-synthesis-2026-06-22, q016-assurance-state-2026-06-23, drivers-subsystem-state-2026-06-23, d-018]
---

# three newly-surfaced producer-workflow problems + designs (2026-06-23)

этот документ собирает три проблемы, которые выделились **из решения по уже готовой документации** — то есть всплыли не как новые исследовательские вопросы, а как конкретные расхождения между тем, что наши синтез-доки уже описывают, и тем, что живёт в коде репозитория `c:/users/stefan/documents/new project ai colab` на 2026-06-23.
- - the tracer is read-only and reuses existing primitives, so it inherits the read/observe boundary that `assurance.
- Py`): a new optional front-matter-free list field on instruction dicts, a new read-only `trace()` function + subcommand, and one substring→join swap.
- Md:7,15`), the execute-gate stays closed (the safety policy forbids running unvetted code/writes without a separate decision and real sandbox — `docs/driver-safety-policy.
- F-020 stays a proposed shared archetype until ratified; this pr adds only the detector + the canonical id + the cross-link, nothing that alters `validate.
- For a given `d-nnn` it returns the one path:
```
base decision (decisions/d-nnn.
- Md` front-matter carries only `id, type, title, status, date, participants` (verified across d-001/d-002/d-004/d-008/d-009/d-023).
- Md", "docs/parallel-work-policy.
- Py detector + cohort↔friction cross-link

### problem, confirmed against source

the two collaboration-safety subsystems detect the **same** t-150-class incident (a foreign half-done task turns the shared `validate.
- Py`) as the canonical, environment-portable acceptance gate for the gateway, and update the gateway doc's operational caveat to "call-acceptance covered via portable sync path; official async stdio remains environment-dependent.
- This is a **substring scan over prose**, not a key join — it can only say "this `d-nnn` string does not appear anywhere in the instruction files.
- Py` gate red, blocking commits for everyone via the pre-commit hook) but they do not share one canonical id, and the cross-link they already advertise is **broken**.
- Py guard`:

```python
if warn_ids & {"f-006", "f-007", "f-011", "f-013", "f-015", "f-020"}:
    return "level 1 or selective-add: dirty/drift/stream/gate-poison signals; run `python tools/cohort.
- This is the only edit inside the shared `registry` literal and is purely additive:

```python
{
    "id": "f-020",
    "name": "gate-poison: shared validate gate is red",
    "symptom": "validate.
- " it cannot answer the structured question "which instruction surfaces decision d-008, and at which pyramid level does that surface sit.
- ,
  "surfaces": ["d-009"] },
```
this is the single shared join key the two namespaces lack: it points an instruction `id` at base `d-nnn`s.
- Base↛apex becomes one verifiable path that the `--strict` gate can enforce.
- Md:24` and item #4 `:73` (records d-008/d-004/d-009/d-002 as flow-orphans, current fix is manual hand-weaving).
- Group(1)) > 0) or rc not in (0, none):
        return make_check(
            "f-020", "warn", "shared validate gate is red (commits blocked for everyone)",
            evidence=errs or first_lines(text, 4),
            recipe_hint="foreign half-done.