# TVCP fetched intake

Дата: 2026-06-26
Статус: external fetched snapshot / read-only intake
Источник: https://github.com/svend4/infon
Назначение: локальный материал для анализа TVCP, textscene, terminal-video, pseudo-image, scene DSL и tvcp-ai/1.

## Что это

Эта папка содержит плоский fetched-срез части внешнего репозитория `svend4/infon`. Имена файлов вида `docs__COMMANDS.md` или `pkg__scene__scene.go` сохраняют исходный путь через `__`.

GitHub-страница репозитория указывает MIT license и наличие `LICENSE`, но в текущий локальный fetched-срез файл `LICENSE` не включен. Поэтому этот intake нельзя считать полноценным redistributable vendor snapshot до отдельного provenance/license шага.

## Правила

- Читать и цитировать кратко для анализа можно.
- Автоматически исполнять код из этой папки нельзя.
- Переносить код в `tools/`, `drivers/`, `core/` нельзя без отдельного review, attribution и проверки лицензии.
- Коммитить весь внешний fetched-срез нужно отдельным commit только если принят conscious vendor/intake policy.
- Для текущей работы предпочтительно переносить не код, а идеи: protocol-first, terminal scene DSL, pseudo-image expansion, text_cell/text_frame, read-only sandbox.

## Файлы

Содержит 19 fetched-файлов: README, docs, ai protocol docs, Go snippets из `pkg/pseudo`, `pkg/scene`, `pkg/sketch`, `go.mod`, `tvcp-appendix.md`.

## Следующий безопасный шаг

Если нужно зафиксировать этот intake в git, сначала добавить/проверить точный upstream commit SHA и license file. Без этого папка остается рабочим внешним материалом, а не каноническим источником проекта.
