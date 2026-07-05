#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.execute_preflight
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт execute_preflight.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""
Preflight-чекер для execute-sandbox (Gates 4/5, 6, 9).
Реализует проверки до реального запуска кода (T-212 / P3, P5, P9).

Запуск:
    python tools/execute_preflight.py check-probe
    python tools/execute_preflight.py check-command <cmd>...
"""
import os
import sys
import subprocess
from _ioutil import configure_output
from _cli import help_guard
from _canon import parse_front_matter

configure_output()

# Gate 1 (D-014, волна 2 C7-a, решение Stefan Q-W2-2a): у execute-драйвера должно быть
# машинно-проверяемое поле `execute_decision: D-0XX`, указывающее на ACCEPTED-решение.
def check_execute_decision(driver_id, root=None):
    """Gate 1: execute-сценарий требует accepted-решения (D-014, гейт «б»).

    Ищем манифест драйвера по front-matter id (fallback — имя файла), читаем поле
    `execute_decision` и проверяем, что decisions/<id>.md существует и status: accepted.
    Возвращает (ok, msg). Для драйверов НЕ в mode: execute гейт неприменим (ok).
    """
    base = root or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    drivers_dir = os.path.join(base, "drivers")
    fm = None
    cand = os.path.join(drivers_dir, "%s.md" % driver_id)
    paths = [cand] if os.path.exists(cand) else []
    if not paths and os.path.isdir(drivers_dir):
        paths = [os.path.join(drivers_dir, fn) for fn in sorted(os.listdir(drivers_dir))
                 if fn.endswith(".md") and not fn.startswith("_")]
    for p in paths:
        try:
            with open(p, encoding="utf-8", errors="replace") as f:
                cur = parse_front_matter(f.read())
        except OSError:
            continue
        if cur.get("type") == "driver" and (cur.get("id") == driver_id or p == cand):
            fm = cur
            break
    if fm is None:
        return False, "Gate 1: driver manifest for %r not found in drivers/" % driver_id
    if fm.get("mode") != "execute":
        return True, "Gate 1: driver %r is not mode: execute — gate not applicable" % driver_id
    dec = (fm.get("execute_decision") or "").strip()
    if not dec:
        return False, ("Gate 1: mode: execute without execute_decision field is forbidden "
                       "(D-014: accepted decision required per scenario)")
    dec_path = os.path.join(base, "decisions", "%s.md" % dec)
    try:
        with open(dec_path, encoding="utf-8", errors="replace") as f:
            status = (parse_front_matter(f.read()).get("status") or "").strip().lower()
    except OSError:
        return False, "Gate 1: execute_decision %s points to missing decisions/%s.md" % (dec, dec)
    if status != "accepted":
        return False, ("Gate 1: execute_decision %s has status %r — accepted required (D-014)"
                       % (dec, status))
    return True, "Gate 1: execute_decision %s is accepted" % dec

# Gate 9: anti-fake-sandbox
def probe_sandbox_backend(sandbox_type):
    if sandbox_type == "docker":
        try:
            # Пытаемся вызвать docker info (timeout 5s)
            p = subprocess.run(["docker", "info"], capture_output=True, text=True, timeout=5)
            if p.returncode == 0:
                return True, "Docker is available and responsive"
            else:
                return False, f"Docker command failed: {p.stderr}"
        except Exception as e:
            return False, f"Docker backend not reachable: {e}"
    elif sandbox_type in ("container", "nsjail", "firejail", "gvisor", "sandboxed-vm"):
        return False, f"Backend probe for {sandbox_type} not implemented yet"
    else:
        return False, f"Unknown sandbox type: {sandbox_type}"

# Gate 4/5: mount/network
# Белый список источников маунта: только work/out каталоги sandbox
# (их создаёт execute_audit.AuditLogger.prepare_workspace в корне репозитория).
_SANDBOX_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALLOWED_MOUNT_SOURCES = (
    os.path.join(_SANDBOX_ROOT, ".sandbox_work"),
    os.path.join(_SANDBOX_ROOT, ".sandbox_out"),
)

# Запрещённые префиксы источников маунта (D-014: не монтировать профиль
# пользователя и системные каталоги хоста). Сравниваем в нормализованном
# виде: нижний регистр, прямые слэши.
FORBIDDEN_MOUNT_PREFIXES = (
    "c:/users",      # весь профиль пользователя Windows
    "/c/users",      # тот же профиль в нотации git-bash
    "/mnt/c/users",  # тот же профиль в нотации WSL
    "/home",         # домашние каталоги Linux
    "/root",
    "/etc",
)

# Запрещённые фрагменты источника маунта (секреты и ключи по D-014).
FORBIDDEN_MOUNT_FRAGMENTS = (
    ".ssh",
    ".gitconfig",
    ".git-credentials",
    ".aws",
    ".gnupg",
    "id_rsa",
    "docker.sock",
    "%userprofile%",
    "$home",
)


def _norm_mount_path(path):
    """Нормализует путь для сравнения: раскрывает ~ и %VAR%, делает
    абсолютным, приводит к нижнему регистру и прямым слэшам."""
    expanded = os.path.expandvars(os.path.expanduser(path))
    return os.path.abspath(expanded).replace("\\", "/").lower()


def _split_volume_source(value):
    """Выделяет источник из значения -v/--volume вида SRC:DST[:opts].
    Учитывает букву диска Windows (C:\\...) в начале источника.
    Возвращает None для анонимного volume (значение без разделителя)."""
    start = 2 if len(value) >= 2 and value[1] == ":" and value[0].isalpha() else 0
    sep = value.find(":", start)
    if sep == -1:
        return None
    return value[:sep]


def _extract_mount_sources(args):
    """Собирает источники маунтов из docker-аргументов.
    Понимает формы: `-v SRC:DST` (два аргумента — именно так строит команду
    sandbox_runner.py), `-v=SRC:DST`, `-vSRC:DST`, `--volume SRC:DST`,
    `--volume=SRC:DST`, `--mount type=bind,source=SRC,target=DST`."""
    sources = []
    i = 0
    while i < len(args):
        arg = args[i]
        value = None
        kind = None
        for flag in ("--volume", "--mount", "-v"):
            if arg == flag:
                if i + 1 < len(args):
                    value = args[i + 1]
                    i += 1
                kind = flag
                break
            if arg.startswith(flag + "="):
                value = arg[len(flag) + 1:]
                kind = flag
                break
            if flag == "-v" and arg.startswith("-v") and len(arg) > 2:
                # Слитная короткая форма: -vC:\src:/dst
                value = arg[2:]
                kind = flag
                break
        if value is not None:
            if kind == "--mount":
                # Формат: type=bind,source=SRC,target=DST (source|src)
                for part in value.split(","):
                    key, _, val = part.partition("=")
                    if key.strip().lower() in ("source", "src") and val:
                        sources.append(val)
            else:
                src = _split_volume_source(value)
                if src is not None:
                    sources.append(src)
        i += 1
    return sources


def _looks_like_host_path(source):
    """Отличает хостовый путь от именованного docker-volume."""
    if "/" in source or "\\" in source:
        return True
    if len(source) >= 2 and source[1] == ":" and source[0].isalpha():
        return True
    return source.startswith((".", "~", "%", "$"))


def _check_mount_source(source):
    """Проверяет один источник маунта (Gate 4). Возвращает (ok, msg)."""
    raw = source.replace("\\", "/").lower()
    norm = _norm_mount_path(source)
    if _looks_like_host_path(source):
        # 1. Белый список: только work/out каталоги sandbox. Проверяется
        #    первым, потому что сам репозиторий может лежать под C:\Users.
        for allowed in ALLOWED_MOUNT_SOURCES:
            allowed_norm = _norm_mount_path(allowed)
            if norm == allowed_norm or norm.startswith(allowed_norm + "/"):
                return True, "Mount source is inside sandbox whitelist"
        # 2. Явно запрещённые чувствительные пути и фрагменты (D-014).
        for prefix in FORBIDDEN_MOUNT_PREFIXES:
            if norm == prefix or norm.startswith(prefix + "/"):
                return False, "Mounting sensitive host paths is forbidden (Gate 4): %s" % source
        for frag in FORBIDDEN_MOUNT_FRAGMENTS:
            if frag in raw or frag in norm:
                return False, "Mounting sensitive host paths is forbidden (Gate 4): %s" % source
        # 3. Всё остальное вне белого списка тоже запрещено (deny-by-default).
        return False, "Mount source outside sandbox work/out whitelist is forbidden (Gate 4): %s" % source
    # Именованный docker-volume: хостового пути нет, но чувствительные
    # фрагменты всё равно запрещаем.
    for frag in FORBIDDEN_MOUNT_FRAGMENTS:
        if frag in raw:
            return False, "Mounting sensitive host paths is forbidden (Gate 4): %s" % source
    return True, "Named volume"


def _extract_network_modes(args):
    """Собирает значения --network/--net (алиас) в порядке следования,
    включая формы `--network none`, `--network=none`, `--net host`, `--net=host`."""
    modes = []
    i = 0
    while i < len(args):
        arg = args[i]
        for flag in ("--network", "--net"):
            if arg == flag:
                if i + 1 < len(args):
                    modes.append(args[i + 1])
                    i += 1
                break
            if arg.startswith(flag + "="):
                modes.append(arg[len(flag) + 1:])
                break
        i += 1
    return modes


def check_sandbox_isolation(args):
    # args: list of arguments, e.g. ["docker", "run", "--rm", "--network", "none", ...]
    args_str = " ".join(args)

    # Gate 5: сеть. --net — алиас --network; docker берёт последнее значение,
    # но host в любом месте запрещаем сразу.
    net_modes = _extract_network_modes(args)
    if any(mode == "host" for mode in net_modes):
        return False, "Host network is strictly forbidden (Gate 5)"
    # We require explicit --network none
    if not net_modes or net_modes[-1] != "none":
        return False, "Explicit --network none is required (Gate 5)"

    if "--privileged" in args_str:
        return False, "Privileged mode is strictly forbidden (Gate 4)"

    # Gate 4: маунты. Реально парсим значения -v/--volume/--mount (включая
    # двухаргументную форму `-v <путь>`) и резолвим источник каждого маунта.
    for src in _extract_mount_sources(args):
        ok, msg = _check_mount_source(src)
        if not ok:
            return False, msg

    return True, "Isolation checks passed"

# Gate 6: limits
def check_sandbox_limits(args):
    args_str = " ".join(args)
    
    required_limits = ["--memory", "--cpus", "--pids-limit"]
    missing = []
    
    for lim in required_limits:
        if lim not in args_str:
            missing.append(lim)
            
    if missing:
        return False, f"Missing required resource limits: {', '.join(missing)} (Gate 6)"
        
    return True, "Resource limits checks passed"

def main():
    help_guard(__doc__)
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 2
        
    cmd = args[0]
    if cmd == "check-probe":
        sandbox_type = args[1] if len(args) > 1 else "docker"
        ok, msg = probe_sandbox_backend(sandbox_type)
        if ok:
            print(f"OK: {msg}")
            return 0
        else:
            print(f"ERROR: {msg}")
            return 1
            
    elif cmd == "check-command":
        cmd_args = args[1:]
        ok_iso, msg_iso = check_sandbox_isolation(cmd_args)
        if not ok_iso:
            print(f"ERROR: {msg_iso}")
            return 1
            
        ok_lim, msg_lim = check_sandbox_limits(cmd_args)
        if not ok_lim:
            print(f"ERROR: {msg_lim}")
            return 1
            
        print("OK: Command preflight checks passed")
        return 0
        
    elif cmd == "check-all":
        # Aggregate probe for P11
        # Expects: execute_preflight.py check-all <driver_id> <sandbox_type> <cmd>...
        if len(args) < 3:
            print("Usage: execute_preflight.py check-all <driver_id> <sandbox_type> <cmd>...")
            return 2
            
        driver_id = args[1]
        sandbox_type = args[2]
        cmd_args = args[3:]
        
        # 1. P3: Probe backend
        ok, msg = probe_sandbox_backend(sandbox_type)
        if not ok:
            print(f"ERROR: {msg}")
            return 1
            
        # 2. P5/P9: Command isolation and limits
        ok_iso, msg_iso = check_sandbox_isolation(cmd_args)
        if not ok_iso:
            print(f"ERROR: {msg_iso}")
            return 1
            
        ok_lim, msg_lim = check_sandbox_limits(cmd_args)
        if not ok_lim:
            print(f"ERROR: {msg_lim}")
            return 1
            
        # 3. P10: Check if audit logger exists
        audit_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "execute_audit.py")
        if not os.path.exists(audit_script):
            print("ERROR: Audit logger not found (Gate 7/8)")
            return 1

        # 4. Gate 1 (D-014, C7-a): execute требует машинной ссылки на accepted-решение
        ok_dec, msg_dec = check_execute_decision(driver_id)
        if not ok_dec:
            print(f"ERROR: {msg_dec}")
            return 1

        # 5. P6: Human Gate
        import execute_human_gate
        if execute_human_gate.check_approval(driver_id) != 0:
            return 1
            
        print("OK: All preflight gates passed. Ready for execute.")
        return 0
    else:
        print(f"Unknown command: {cmd}")
        return 2

if __name__ == "__main__":
    sys.exit(main())
