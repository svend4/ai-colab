#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ==========================================
# [FILE ID CARD]
# ID: tools._canon
# TYPE: helper-module
# DOMAIN: core.parsing
# DEPTH_LEVEL: 1
# SUMMARY: Канонический parser front-matter для задач, решений, вопросов и служебных инструментов.
# ==========================================
"""
Канонический парсер front-matter для инструментов канона (T-085, ревью T-078 находка L).

Единый источник вместо 8 идентичных копий по `tools/*.py`. Логика намеренно
идентична прежним копиям, чтобы консолидация не меняла поведение: берётся блок
между первым `---` и следующим `\n---`, строки `key: value` парсятся через
`split(':', 1)`.

Имена `parse_front_matter` и `parse_fm` — синонимы (исторически использовались оба).
"""


def parse_front_matter(text):
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    fm = {}
    for line in text[3:end].strip().splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip()
    return fm


# Исторический синоним (queue/pipeline/dispatch/metrics/risk_gate/drivers_catalog).
parse_fm = parse_front_matter
