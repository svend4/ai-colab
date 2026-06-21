#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Канонический redaction-хелпер для драйверов (слой безопасности).

Маскирует секрет-паттерны (`api_key`/`token`/`password=...`, голые AWS `AKIA`-ключи)
в текстовых выдачах драйверов. Чистая stdlib, без состояния.

Единый источник правды, чтобы не плодить копии `SECRET_RE` по драйверам
(см. ревью T-078, находка L). `files_driver.py` исторически держит свою копию
этих паттернов; `files` и `data` уже используют этот модуль, новые драйверы
должны импортировать отсюда.

Семантика паттернов покрыта тестами `files`/`data`, поэтому поведение между
драйверами должно оставаться консистентным.
"""
import re

# key=value / key: value для типовых секрет-имён → маскируем значение.
SECRET_RE = re.compile(
    r"(?i)\b(api[_-]?key|secret[_-]?key|access[_-]?key|aws[_-]?key|token|secret|password|passwd)"
    r"\b(\s*[=:]\s*)(\S+)"
)
# «Голый» AWS access key id (AKIA + 16 символов), без key=value.
AWS_KEY_RE = re.compile(r"\bAKIA[0-9A-Z]{16}\b")


def redact(value):
    """Замаскировать секреты в строке.

    Не-строки возвращаются без изменений (удобно для ячеек CSV, где встречаются
    None/числа после csv-парсинга значения всегда строковые, но защищаемся явно).
    """
    if not isinstance(value, str):
        return value
    value = SECRET_RE.sub(lambda m: m.group(1) + m.group(2) + "***", value)
    return AWS_KEY_RE.sub("***", value)
