# TVCP design sandbox

Дата: 2026-06-26
Статус: sandbox / design variants

Эта папка хранит независимые варианты и синтез по теме переноса идей TVCP/svend4/infon в локальный 2D text workbench.

## Что внутри

- `CLAUDE_INDEPENDENT.md` — sealed independent-first вариант до сверки с роем.
- `design_pseudo.md` — механизм псевдо-диффузии текста.
- `design_cards.md` — карточки/меню/2D layout.
- `design_mmorpg.md` — MMORPG/GridRoom аналогия для текстовой работы.
- `design_codec.md` — провод/кодек CARDWIRE.
- `design_ours.md` — адаптация к текущему репозиторию.
- `FINAL.md` — синтез вариантов.

## Правила использования

Это не accepted design. Материал можно читать, сравнивать и переносить в `topics/`, `decisions/`, `tools/` только через отдельные задачи и ревью.

Не исполнять код из этой папки автоматически. Здесь хранятся документы и проектные варианты.

## Почему commit отдельный

Папка относится к смысловым design variants. Ее нельзя смешивать с `sandbox/tvcp_fetched/`, потому там внешний материал из репозитория TVCP, а здесь — внутренние выводы/варианты агентов.
