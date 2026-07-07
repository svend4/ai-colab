# Чек-лист применения (когда среда разгрузится) — 2026-07-07

Единая точка возобновления после насыщения машины (фоновый gc/repack + многоагентный
validate). Всё ниже подготовлено на диске БЕЗ git; применять по порядку, когда
`git rev-parse HEAD` отвечает за секунды.

## 0. Проверка, что среда свободна

```
git rev-parse --short HEAD     # должно ответить мгновенно
git count-objects -v           # loose count должен быть небольшим (gc доработал)
git config --get gc.auto       # 20000 (исправлено прямой правкой .git/config)
```

## 1. Докоммитить зависшее (на диске, tracked-modified)

- `docs/beta0-acceptance-checklist-2026-07-06.md` — правка «7/10 зелёных» + cross-link отчёта
  Novax (reconcile). Коммит через сериализацию:
  ```
  python tools/commit_lock.py acquire claude --ttl 500 --wait 60
  python tools/generate.py
  python tools/commit.py docs/beta0-acceptance-checklist-2026-07-06.md STATUS.md board.md TASKS.md index.json indexes/*.md drivers/index.json -m "docs(beta0): 7/10 зелёных + cross-link Novax" --agent claude
  python tools/commit_lock.py release claude
  ```

## 2. Прогнать подготовленные тесты (новые инструменты)

```
py -3 tools/tests/test_validate_staged.py     # ожидается: TESTS OK validate_staged
py -3 tools/validate_staged.py                # на реальном staged (или пусто → OK)
py -3 tools/tests/test_commit.py              # уже зелёный (5 кейсов)
py -3 tools/tests/test_reconcile.py           # уже зелёный (2 ступени)
```
Закоммитить `tools/validate_staged.py` + тест через `tools/commit.py`.

## 3. Облегчить pre-commit (главный фикс коммит-медленности)

Дизайн/риски/swap — `docs/pre-commit-lightening-proposal-2026-07-07.md`. Шаги:
1. CI-полнота: в `.github/workflows/bulk-guard.yml` добавить шаг `python tools/generate.py --check`
   (после validate). Когда T-294 (Codex, `bulk_guard --range`) сядет — заменить inline-подсчёт
   диапазона в CI на `python tools/bulk_guard.py --range "$BASE" "$HEAD"`.
2. Активировать через reconcile (НЕ удалять старый):
   ```
   copy tools/githooks/pre-commit tools/githooks/pre-commit.full.bak   # снапшот (reconcile §E)
   copy tools/githooks/pre-commit.fast tools/githooks/pre-commit       # swap
   ```
3. Проверить: обычный коммит теперь секундный; массовое удаление всё ещё блокируется
   (bulk_guard локально + CI).

## 3b. Пакет worktree/admission enforcement (Гейты A+B; корневой фикс насыщения)

Дизайн: `docs/worktree-isolation-enforcement-2026-07-07.md`. Решение принято Stefan
(котёл 2026-07-07): worktree обязателен при N≥3, <3 — рекомендуется; CAP слотов ≈ ядра−запас,
лишние в очередь. Теоретически — субстрат independent-first (D-028): каждый пишет свою версию
независимо, потом reconcile (D-029).

Артефакты на диске:
- ✅ `tools/worktree_gate.py` (Гейт A) — детектор «общий main + N≥3»; `--hook` условная строгость.
- ✅ `tools/work_admission.py` (Гейт B) — семафор слотов + очередь; авто-слоты = max(1, ядра−reserve);
  fencing/TTL/атомарность (уроки commit_lock из аудита).
- ✅ `tools/tests/test_worktree_gate.py`, `tools/tests/test_work_admission.py`.
- ✅ `commit.py` — вызов `worktree_gate --hook` (advisory, блок после ратификации).

Применить (когда git отзывчив):
1. Тесты: `py -3 tools/tests/test_work_admission.py` + `py -3 tools/tests/test_worktree_gate.py`
   (ожидается TESTS OK; git не требуется — тесты изолированы). Прогнать `worktree_gate check` и
   `work_admission status` на репо.
2. **Записать решение** через `next_id decision`: «worktree обязателен при N≥3 + CAP слотов»
   (id избежит коллизии). Обновить `worktree_gate.RATIFY_DECISION = "<новый id>"` → это переключит
   Гейт A из advisory в BLOCK.
3. **Гейт B в точку старта:** в `top.py take` / `pipeline claim` вызывать
   `work_admission acquire <agent> --wait <s>`; при QUEUE (exit 1) — агент откладывает тяжёлую
   работу/встаёт в очередь. `release` — по завершении задачи. (Правка контендящихся core-файлов —
   через эстафету/worktree, не форсировать.)
4. `logs/slots/` — добавить в `.gitignore` (runtime-лизинги слотов, как logs/heartbeat).

## 4. gc-восстановление (проверить)

- `gc.auto = 20000` уже в `.git/config` (прямая правка). Если машина всё ещё тормозит после
  завершения текущего gc — разово `git gc` вручную в тихий момент.

## 5. Открытые human-gate (за Stefan, не агентские)

- **B2:** `rm z`, `rm test_guard.md`, worktree/ветка T-162.
- **Branch protection** на GitHub: чтобы CI `bulk-guard.yml` реально блокировал merge при провале.
- **Reconcile-коллизии** (`python tools/reconcile.py plan`, 16 шт.): флип primary в 3 дублях,
  стратегия переполнения dialog.md/audit-2026-07-02 (снапшот vs папочный режим) — решение человека.
- **Q16:** инцидент antigravity, дедлайн 2026-07-13.
- **Котёл-вопросы (proposed):** облегчение pre-commit (§7 предложения), reconcile-документ →
  accepted, package/agenda-слой пилот-решение.

## 6. Экосистема (идёт у других агентов — не дублировать)

- **Codex:** T-294 `bulk_guard --range` (doing, дополнит мой CI), T-295 materializer, T-296
  additive-shortlist.
- **Novax:** T-293 переверификация 4 драйверов по D-038 (1/2), Beta-0 acceptance report (T-292).
- **Пул:** T-291 done (правило коммита в PROTOCOL), maturity-индекс.

## 7. Что ещё prep-able (следующий заход)

- Оценка удобства портала (Beta-0 критерий 9) — read-only + отчёт (broad-scan сейчас таймаутит).
- Интеграция CI ↔ Codex `bulk_guard --range` (после T-294).

---
*Составлено при насыщенной машине (только Write). Ничего не удалено, ничего не форсировано
в занятый git. Порядок применения — сверху вниз.*
