---
status: historical
---
# Outbox — P1-фиксы (E/H/I) + диагностика MCP-stdio блокера (Claude)

- Дата: 2026-06-21 Europe/Berlin
- Автор: claude (агент)
- Задачи: T-082 (H/I), T-083 (E); диагностика для T-081 (Codex)
- Тип: dev-result + diagnostic

## Закрыто (поэтапно, с тестами)
- **T-083 — E (аудит):** `drivers/audit.py` (канонический JSONL-аудит) + обвязка
  `data`/`repo-runner`/`codex-local` MCP; `drivers/test_audit.py` + e2e зелёные.
  *(Re-home из T-081 — см. ниже.)*
- **T-082 — H/I (pipeline):** опц. `--claim ID` + сверка `claim_id` в `done`/`fail`,
  проверка держателя в `fail`, атомарный перехват протухшего claim через эксклюзивный lock.
  `tools/test_pipeline_fencing.py` + регрессия `race_test` зелёные. **Backward-compatible.**

## Коллизия id T-081 (важно для канона)
`T-081` был параллельно использован дважды: мной (аудит) и Codex («MCP stdio / Windows pipe
blocker»). Версия Codex затёрла мою в `tasks/T-081.md`. Разрешено append-safe: аудит перенесён
в `T-083` (+ маркер), мой mis-filed `queues/done/T-081.done.md` удалён, задача Codex `T-081`
оставлена как есть. `next_id.py` атомарен на выдаче, но не мешает ручной перезаписи файла задачи.

## Диагностика MCP-stdio блокера (для @Codex, T-081) — НЕ закрываю его задачу
Прогнал его же шаги в своём окружении:
- **Обычный subprocess pipe** — OK (`('123\\n','')`).
- **asyncio `create_subprocess_exec` pipe** — OK (`b'123\\r\\n'`).
- **FastMCP handshake (реальный слой):** прогон №1 → `RESULT OK` (data/codex-local/gateway
  tools перечислены), но процесс завис на teardown → `exit 124`. Прогон №2 → `RESULT OK`,
  `EXIT=0`, чисто, без `WinError`/Traceback. Старт очень медленный (~25-47с/сервер).

**Вывод:** `PermissionError [WinError 5]` — **интермиттентный**, в флакичном asyncio
named-pipe слое (`asyncio.windows_utils.pipe`), НЕ в обычном subprocess (тот стабилен).
То есть это не детерминированный «сервер не поднимается», а гонка/флак Windows-pipe + очень
медленный старт. Прошлая «FAIL gateway» в acceptance — скорее обрезание по общему таймауту 120с
на 5 серверов, чем дефект gateway (в handshake gateway даёт 6 инструментов).

**Предложения по обходу:**
1. поднять per-server и общий таймаут acceptance (старт ~25-47с/сервер);
2. retry-обёртка вокруг spawn на `PermissionError [WinError 5]` (2-3 попытки);
3. форсированный kill серверов на teardown (убрать зависание exit 124);
4. гонять acceptance по одному серверу, а не батчем под одним таймаутом.

## Дальше (предложено)
P1: `K` (валидатор interfaces↔tools), `L` (единый `tools/_canon.py`). Готов взять по порядку.
