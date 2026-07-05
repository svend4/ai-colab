#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ==========================================
# [FILE ID CARD]
# ID: tools._claims
# TYPE: helper-module
# DOMAIN: core.orchestration
# DEPTH_LEVEL: 1
# SUMMARY: Общие claim-примитивы queues/claimed: read/fresh/atomic-create/atomic-takeover/release-с-fencing.
# ==========================================
"""
Единые claim-примитивы над `queues/claimed/<id>.claim.md` (волна 2, C35-a).

До консолидации claim-механика жила ДВАЖДЫ: в `pipeline.py` (try_claim с
takeover-lock и os.replace — фиксы гонок T-082/T-084) и в `agent_queue.py`
(write_claim — порт той же схемы, фикс C9 волны 1). Копии уже расходились
(agent_queue долго жил с plain overwrite — находка C35 аудита 2026-07-02).
Здесь — единый источник по образцу консолидации `parse_front_matter` в
`_canon.py`: правка гонок делается в одном месте, а не в двух.

ВАЖНО: формат claim-файла НЕ меняется — объединяется код, не формат.
Оба потребителя читают файлы друг друга (`agent_queue.cmd_check` видит
claim'ы pipeline и наоборот):
- pipeline пишет поля `task/agent/claim_id/lease_epoch`;
- agent_queue дополнительно пишет `claimed_at/lease_until` (человекочитаемые).
Общая логика (freshness, fencing) опирается ТОЛЬКО на `lease_epoch` —
это поведение pipeline-версии; `claimed_at`/`lease_until` — необязательные
информационные поля, примитивы их не интерпретируют и не требуют.

Примитивы (тексты claim-файлов рендерят вызывающие — здесь только механика):
- `claim_file(dir, task)`   — единый путь claim-файла `<dir>/<task>.claim.md`;
- `read_claim(path)`        — front-matter claim-файла или None;
- `is_fresh(claim, now)`    — жив ли lease (`lease_epoch` строго в будущем);
- `claim_is_fresh(path)`    — read + fresh одним вызовом, не бросает;
- `create_claim(path, text)` — атомарное создание через O_CREAT|O_EXCL;
- `takeover_claim(...)`     — атомарный перехват протухшего claim (T-082)
  с перепроверкой под lock'ом (T-084) и подменой через os.replace;
- `release_claim(path, ...)` — снятие claim, опционально с fencing-проверкой.
"""
import os
import time
import uuid

from _canon import parse_fm  # единый парсер front-matter (T-085, находка L)

# Единый TTL lease по умолчанию (раньше константа дублировалась в обоих модулях).
DEFAULT_TTL_MIN = 30

# Суффикс claim-файла — общий контракт обоих потребителей (cmd_check/cmd_mine
# режут имена файлов ровно по нему).
CLAIM_SUFFIX = ".claim.md"


def claim_file(claimed_dir, task):
    """Путь claim-файла задачи в каталоге queues/claimed (единый формат имени)."""
    return os.path.join(claimed_dir, task + CLAIM_SUFFIX)


def read_claim(path):
    """Front-matter claim-файла как dict, или None (нет файла / транзиентный отказ ФС).

    OSError → None: Windows может кратковременно запрещать доступ, пока
    конкурент подменяет тот же claim через os.replace. Вызывающие повторяют
    попытку или отказывают безопасно вместо падения (заметка из
    pipeline.claim_holder — поведение pipeline-версии сохранено).
    """
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return parse_fm(f.read())
    except OSError:
        return None


def is_fresh(claim, now=None):
    """Жив ли lease: `lease_epoch` строго в будущем. None/мусор → False (протух).

    Мусорный `lease_epoch` считается протухшим, а не исключением: битый claim
    не должен вечно блокировать задачу (поведение agent_queue.is_fresh,
    распространено на обоих потребителей).
    """
    if not claim:
        return False
    if now is None:
        now = time.time()
    try:
        return int(claim.get("lease_epoch", "0")) > int(now)
    except (TypeError, ValueError):
        return False


def claim_is_fresh(path, now=None):
    """read + fresh одним вызовом; никогда не бросает (поведение pipeline.claim_is_fresh)."""
    try:
        return is_fresh(read_claim(path), now)
    except Exception:
        return False


def create_claim(path, text):
    """Атомарно создать claim-файл: O_CREAT|O_EXCL — на одной ФС ровно один победитель.

    FileExistsError НЕ глотается: pipeline на нём уходит в ветку перехвата
    протухшего claim, agent_queue печатает RACE — различение за вызывающим.
    PermissionError тоже пробрасывается (pipeline трактует его как «занято»).
    """
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def takeover_claim(path, text, old_claim, renew_agent=None):
    """Атомарный перехват claim по снимку `old_claim` (T-082, ревью T-078 находка I).

    Гейтится эксклюзивным lock-файлом `<path>.take.<claim_id СТАРОГО claim>`:
    два агента, увидевшие один и тот же протухший claim, вычислят одинаковое
    имя lock'а, и O_CREAT|O_EXCL отдаст победу ровно одному. Под lock'ом —
    перепроверка, что на диске всё ещё ТОТ ЖЕ claim (T-084-перепроверка:
    иначе поздний писатель со старым снимком молча затёр бы уже СВЕЖИЙ claim
    победителя — двойной захват); затем запись во временный файл и атомарная
    подмена через os.replace.

    `renew_agent`: по умолчанию (None) СВЕЖИЙ claim перехватить нельзя ни при
    каких условиях (поведение pipeline). agent_queue передаёт имя агента —
    тогда свежий claim ТОГО ЖЕ агента заменить можно (продление своего lease).

    Возвращает True при успехе, False — гонка проиграна / claim уже не тот.
    (Замечание из pipeline сохранено: при падении победителя между взятием
    lock и os.replace lock может остаться — разрешается через
    reconcile_state/ручную чистку.)
    """
    lock = "%s.take.%s" % (path, old_claim.get("claim_id") or "none")
    try:
        lfd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except (FileExistsError, PermissionError):
        return False  # другой агент уже перехватывает этот же claim
    try:
        os.close(lfd)
        # повторная проверка ПОД lock'ом: claim всё ещё тот же и перехват законен?
        cur = read_claim(path)
        if cur is None or cur.get("claim_id") != old_claim.get("claim_id"):
            return False
        if is_fresh(cur) and (renew_agent is None or cur.get("agent") != renew_agent):
            return False
        tmp = "%s.tmp.%s" % (path, uuid.uuid4().hex[:12])
        with open(tmp, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        # Windows может кратковременно запрещать os.replace, пока другой
        # процесс/поток трогает тот же путь — несколько попыток, затем честный
        # отказ вместо утёкшего исключения в фоновом потоке агента.
        for _ in range(5):
            try:
                os.replace(tmp, path)  # атомарная подмена старого claim новым
                return True
            except PermissionError:
                time.sleep(0.02)
        try:
            os.remove(tmp)
        except OSError:
            pass
        return False
    finally:
        try:
            os.remove(lock)
        except OSError:
            pass


def release_claim(path, agent=None, claim_id=None):
    """Снять claim. Без agent/claim_id — безусловно (fencing уже проверен вызывающим).

    С agent/claim_id — совещательный fencing: claim снимается, только если
    текущий держатель совпадает по заданным полям; иначе False и файл не
    трогается. Пара read→remove не атомарна (как и прежние
    require_holder→os.remove в agent_queue) — это защита от ЧЕСТНОЙ ошибки
    агента, а не от злонамеренной гонки.

    Возвращает True, если claim-файл был удалён этим вызовом.
    """
    if agent is not None or claim_id is not None:
        cur = read_claim(path)
        if cur is None:
            return False
        if agent is not None and cur.get("agent") != agent:
            return False
        if claim_id is not None and cur.get("claim_id") != claim_id:
            return False
    try:
        os.remove(path)
    except FileNotFoundError:
        return False
    return True
