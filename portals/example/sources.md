---
id: portal-example-sources
portal: portal-example-l2
updated: 2026-06-21
---

# Источники — портал «пример»

## Curated corpus

| Источник | Назначение | Статус |
|---|---|---|
| `data/portals/example/portal.md` | операционный manifest для текущего `tools/portal.py` | active |
| `data/portals/example/corpus/note-alpha.md` | демонстрационный Markdown-документ | active |
| `data/portals/example/corpus/note-beta.txt` | демонстрационный text-документ | active |

## Граница L2/L4

`portals/example/` хранит чистовое состояние и ссылки. Операционный корпус пока остаётся в
`data/portals/example/corpus/`, потому что `tools/portal.py` уже работает с этой структурой.

Непроверенный внешний источник нельзя класть сюда напрямую. Сначала: `sandbox/` intake → read-only
inventory report → decision/review → только затем curated добавление в corpus.

## Открытый вопрос

Stream `streams/portal-location/20260621-1931-claude/STREAM.md` предлагает оставить split-модель:
`portals/<name>/` как clean L2, `data/portals/<name>/` как операционный corpus/runtime. До синтеза
этот портал использует split-модель без изменения `portal.py`.
