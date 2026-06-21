# Knowledge Bridge Corpus

Назначение: маленький безопасный корпус для проверки L6 workflow `tools/knowledge.py`.

Корпус синтетический:

- нет персональных данных;
- нет секретов, токенов, ключей или паролей;
- нет чужого исполняемого кода;
- файлы маленькие и подходят для ручного review.

Основной тестовый термин: `bridge`.

Повторяемая команда:

```powershell
python tools\knowledge.py report data\knowledge-corpus --query bridge --out reports\knowledge-corpus-report.md
```
