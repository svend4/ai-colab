# Sandbox sources

Локальная quarantine-зона для сырых внешних источников.

Примеры:

```text
sandbox/sources/svend4-profile-20260621/
sandbox/sources/demo-external-repo-20260621/
```

Правила:

- источник считается недоверенным;
- не запускать скрипты, install, tests, hooks или binaries;
- не хранить секреты;
- не монтировать домашнюю папку или системные каталоги;
- сначала делать read-only inventory;
- не коммитить содержимое этой папки.

Если source большой или чувствительный, лучше оставить его вне repo и указать абсолютный read-only путь в manifest.
