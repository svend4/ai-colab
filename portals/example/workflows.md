---
id: portal-example-workflows
portal: portal-example-l2
---

# Рабочие процессы портала «пример»

| Действие | Команда |
|---|---|
| Список порталов | `python tools/portal.py list` |
| Собрать индекс корпуса | `python tools/portal.py build example` |
| Отчёт + покрытие тем | `python tools/portal.py report example --query alpha` |
| Поиск по содержимому | `python tools/knowledge.py search <db> "<текст>"` |

**Добавить материал:** положить файл в `data/portals/example/corpus/`, пересобрать `build`.

**Внешний непроверенный источник:** сначала через L4 `sandbox/` (`python tools/sandbox.py intake ...`
или демо `python tools/sandbox_intake_demo.py`), затем `report → decision → портал` — не класть сырой
вход напрямую в корпус.

**Граница безопасности:** всё read-only; execute закрыт; секреты маскируются redaction'ом ядра.
