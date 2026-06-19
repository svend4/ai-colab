# Задачи

Общая доска задач. Для обсуждения деталей создавайте файл или папку в `темы/` и ставьте ссылку в колонке "Тема".

## Правила

- Одна строка = одна конкретная задача.
- Статусы: `todo`, `doing`, `blocked`, `review`, `done`.
- Если задача требует решения, добавьте вопрос в `QUESTIONS.md`.
- Если по задаче принято архитектурное или организационное решение, добавьте запись в `DECISIONS.md`.

## Список задач

<!-- GEN:tasks START — генерируется tools/generate.py из tasks/*.md, не править вручную -->
| ID | Задача | Статус | Ответственный | Тема | Следующий шаг |
|---|---|---|---|---|---|
| T-001 | Проверить удобство структуры папки для полилога | done | все | `темы/пример.md` | Подтверждено реальной нагрузкой сессии; крупные темы → папочный режим D-002 |
| T-002 | Определить правила именования файлов и тем | done | все | `темы/организация-папки.md` | Закрыто D-005 — новые файлы в ASCII, русский текст в заголовке |
| T-003 | Проверить протокол для многих AI-агентов и скриптов | done | Claude | `queues/outbox/2026-06-19-2044-smoke-test-result.md` | Смоук-тест очереди пройден; ограничения и right-size задокументированы |
| T-004 | Проверить механику захвата задач через queues/claimed/ | done | Claude | `queues/outbox/2026-06-19-2044-smoke-test-result.md` | Claim создан; claimed/ не атомарен (нет TTL) — доработка в T-008+ |
| T-005 | Постепенно мигрировать русские имена файлов к ASCII (D-007) | doing | все | `темы/migrate-file-names.md` | При следующей существенной правке файла переименовать в ASCII и обновить ссылки |
| T-006 | Сделать валидатор целостности Markdown-инфраструктуры | done | Claude | `темы/infrastructure-review.md` | tools/validate.py готов и прогнан на Windows (0 ERROR, commit 572ffa3) |
| T-007 | Генератор навигации (STATUS/Доска из front-matter) | done | Claude | `темы/infrastructure-review.md` | tools/generate.py + front-matter тем + маркеры GEN; в hook добавлен --check |
| T-008 | Шардировать реестры (задачи, вопросы, решения) | done | Claude | `темы/scaling-design.md` | Реестры шардированы; TASKS/QUESTIONS/DECISIONS — генерируемые индексы из tasks|questions|decisions/*.md |
| T-009 | Очередь 2.0 — атомарный claim (TTL + fencing) и tools/queue.py | done | Claude | `темы/scaling-design.md` | queue.py готов и самопроверен; далее — шардинг questions/decisions или валидатор v2 |
| T-010 | Валидатор v2 — проверка файлов-источников и depends_on | done | Claude | `темы/scaling-design.md` | check_sources ловит битый front-matter, дубли id, депенды; queue.py check — для очереди |
| T-011 | Машинный индекс index.json для агентов | done | Claude | `темы/scaling-design.md` | index.json генерится из front-matter, --check контролирует свежесть; Codex верифицировал и задокументировал |
| T-012 | Роли и path-права (permissions.py) | done | Claude | `темы/scaling-design.md` | permissions.py + permissions.json проверяют, что агент пишет в свою зону; совещательный guard (не безопасность) |
| T-013 | Git-flow для агентов (flow.py) | done | Claude | `темы/scaling-design.md` | flow.py печатает команды ветка-на-агента + merge-гейт (validate/generate/permissions); --run выполняет |
<!-- GEN:tasks END -->
