#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
files driver (L2, read-only) — T-043.

Безопасный доступ к файлам в разрешённой папке: list / read / search / summarize.
Только чтение, без записи/удаления. Лимиты по `docs/driver-safety-policy.md`:
`max_output_bytes` для read, маскировка секрет-паттернов в выдаче search.
Потом тонко оборачивается в MCP-сервер (stdio) — это «движок» драйвера.

CLI (--base <allowed-root> обязателен: без него команда отказывает, fail-closed):
    python files_driver.py list <dir> --base <allowed-root>
    python files_driver.py read <file> --base <allowed-root> [--max-bytes N]
    python files_driver.py search <pattern> <dir> --base <allowed-root>
    python files_driver.py summarize <dir> --base <allowed-root>
"""
import errno
import os
import re
import stat
import sys
import json
from pathlib import Path

# Канонический redaction-хелпер (drivers/redaction.py) — общий для драйверов,
# чтобы files/data не держали расходящиеся копии SECRET_RE.
_DRIVERS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _DRIVERS_DIR not in sys.path:
    sys.path.insert(0, _DRIVERS_DIR)
from redaction import redact as redact_text


def configure_output():
    for name in ("stdout", "stderr"):
        s = getattr(sys, name, None)
        if s is not None and hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8", errors="replace")


configure_output()

MAX_OUTPUT_BYTES = 1_048_576  # совпадает с max_output_bytes в drivers/files.md
# O_NOFOLLOW и dir_fd есть не везде (нет на Windows): там чтение идёт по проверенному пути, как раньше.
_SAFE_OPEN = hasattr(os, "O_NOFOLLOW") and os.open in os.supports_dir_fd
DEFAULT_MAX_FILES = 1_000
DEFAULT_MAX_HITS = 1_000
SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    "node_modules",
    "venv",
    ".venv",
    "target",
    "build",
    "dist",
}


class PathAccessError(ValueError):
    pass


def _is_relative_to(path, base):
    try:
        path.relative_to(base)
        return True
    except ValueError:
        return False


def _is_physical(path):
    # На Python 3.12 resolve() после цикла симлинков не досказывает путь и схлопывает «..» по тексту,
    # так что в результате может остаться симлинк. Полностью разрешённый путь симлинков не содержит.
    return not any(part.is_symlink() for part in (path, *path.parents))


def _has_loop(path):
    # Цикл симлинков в пути, даже если «..» потом уводит результат внутрь: строгий realpath() кидает ELOOP.
    try:
        os.path.realpath(path, strict=True)
    except OSError as exc:
        return exc.errno == errno.ELOOP
    return False


def _expand_base(base_dir):
    # «~» раскрываем, но пустой HOME даёт «/»: такая база — отказ, а не корень файловой системы.
    expanded = os.path.expanduser(str(base_dir))
    if expanded == os.sep and str(base_dir).strip() != os.sep:
        raise PathAccessError("allowed root must not expand to / (fail-closed)")
    return expanded


def _resolve_base(base_dir):
    # Граница обязательна: без allowed-root движок ничего не отдаёт (fail-closed).
    # Пустая база и «.» (что даёт Path("")) тоже отказ: cwd не становится границей по ошибке.
    if base_dir is None or not str(base_dir).strip() or Path(base_dir).parts == ():
        raise PathAccessError("allowed root must be an explicit path, not blank or '.' (fail-closed)")
    try:
        resolved = Path(_expand_base(base_dir)).resolve()
    except (OSError, RuntimeError):  # цикл у самой базы: до Python 3.13 resolve() кидает RuntimeError
        raise PathAccessError("allowed root is not a usable directory (fail-closed)") from None
    if not _is_physical(resolved):  # на Python 3.13 resolve() после цикла не кидает, а оставляет симлинк
        raise PathAccessError("allowed root is not a usable directory (fail-closed)")
    return resolved


def _resolve_path(path_value, base_dir=None):
    base = _resolve_base(base_dir)
    # «~» под базой не раскрываем: иначе ответ зависит от учётных записей системы.
    raw_path = Path(path_value)
    joined = raw_path if raw_path.is_absolute() else base / raw_path
    try:
        candidate = joined.resolve()
        inside = _is_relative_to(candidate, base) and _is_physical(candidate) and not _has_loop(joined)
    except (OSError, RuntimeError):  # симлинк-цикл: до Python 3.13 resolve() кидает RuntimeError
        inside = False
    if not inside:
        # Сообщение печатает то, что передал вызывающий, а не разрешённую цель симлинка.
        raise PathAccessError(f"path is outside allowed root: {path_value}")
    return candidate


def _is_hardlink(path):
    # Жёсткая ссылка (несколько имён у одного inode) может вести к файлу снаружи: такие файлы не отдаём.
    try:
        return os.stat(path).st_nlink > 1
    except FileNotFoundError:
        return False  # цели нет: не жёсткая ссылка; при чтении или сводке это отказ «не файл», без имени цели
    except OSError:
        return True  # не удалось проверить: не отдаём (fail-closed)


def _parent_dirfd(base, physical):
    # Каталог файла открывается от базы цепочкой dir_fd: каждый компонент с O_NOFOLLOW, подменённый на симлинк
    # компонент даёт ELOOP (с O_DIRECTORY было бы ENOTDIR). Возвращает (fd каталога, имя файла); fd закрывает вызывающий.
    try:
        parts = physical.relative_to(base).parts
    except ValueError:
        raise PathAccessError("path is outside allowed root (fail-closed)") from None
    if not parts:
        raise FileNotFoundError(errno.ENOENT, "not a file")
    dirfd = os.open(str(base), os.O_RDONLY)
    try:
        for name in parts[:-1]:
            nextfd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=dirfd)
            os.close(dirfd)
            dirfd = nextfd
    except BaseException:
        os.close(dirfd)
        raise
    return dirfd, parts[-1]


def _refuse(exc, given):
    # Ошибка открытия: компонент стал симлинком (ELOOP) — путь снаружи; отсутствие — «не файл».
    if exc.errno == errno.ELOOP:
        return PathAccessError(f"path is outside allowed root: {given}")
    if exc.errno in (errno.ENOENT, errno.ENOTDIR):
        return FileNotFoundError(str(given))
    return type(exc)(exc.errno, exc.strerror, str(given))


def _stat_physical(base, physical, given):
    # Размер без открытия на чтение: файл, который нельзя прочитать, учитывается по размеру, как и раньше.
    if not _SAFE_OPEN:
        st = os.stat(str(physical))
    else:
        dirfd, name = _parent_dirfd(base, physical)
        try:
            st = os.stat(name, dir_fd=dirfd, follow_symlinks=False)
        finally:
            os.close(dirfd)
    if stat.S_ISLNK(st.st_mode):  # подменён на симлинк после проверки: не файл
        raise FileNotFoundError(str(given))
    return st


def _open_physical(base, physical, given):
    # Файл открывается цепочкой dir_fd с O_NOFOLLOW: подмена компонента после проверки даёт ELOOP, а не чтение.
    # Тип и число ссылок проверяются по stat до open(): open() на устройстве или терминале уже может что-то сделать
    # (O_NOCTTY не даёт терминалу стать управляющим). После open() сверяется, что открыт тот же объект.
    # Без O_NOFOLLOW или dir_fd (Windows) остаётся проверка по пути, как раньше.
    try:
        if _SAFE_OPEN:
            dirfd, name = _parent_dirfd(base, physical)
            try:
                before = os.stat(name, dir_fd=dirfd, follow_symlinks=False)
                _check_regular(before, given)
                fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_NOCTTY, dir_fd=dirfd)
            finally:
                os.close(dirfd)
        else:
            before = os.stat(str(physical))
            _check_regular(before, given)
            fd = os.open(str(physical), os.O_RDONLY | getattr(os, "O_BINARY", 0))
    except OSError as exc:
        raise _refuse(exc, given) from None
    try:
        st = os.fstat(fd)
        if _SAFE_OPEN and (st.st_dev, st.st_ino) != (before.st_dev, before.st_ino):
            raise PathAccessError(f"path changed while opening (fail-closed): {given}")
        _check_regular(st, given)
    except BaseException:
        os.close(fd)
        raise
    return fd


def _check_regular(st, given):
    # Симлинк, каталог, устройство и FIFO — не файл; жёсткая ссылка отказывает, её второе имя может быть снаружи.
    if stat.S_ISLNK(st.st_mode):  # подменён на симлинк после проверки: путь снаружи, как при ELOOP
        raise PathAccessError(f"path is outside allowed root: {given}")
    if not stat.S_ISREG(st.st_mode):
        raise FileNotFoundError(errno.ENOENT, "not a file", str(given))  # _refuse отдаёт это как «не файл»
    if st.st_nlink > 1:
        raise PathAccessError(f"hard-linked file is refused (fail-closed): {given}")


def _skip_dir(name, include_hidden=False):
    return name in SKIP_DIRS or (not include_hidden and name.startswith("."))


def _skip_file(name, include_hidden=False):
    return not include_hidden and name.startswith(".")


def _iter_files(root, max_files=DEFAULT_MAX_FILES, include_hidden=False, base_dir=None):
    root_path = _resolve_path(root, base_dir)
    if not root_path.is_dir():
        raise NotADirectoryError(str(root))  # как передали, а не разрешённую цель симлинка
    # граница — разрешённая папка (base_dir); файл-симлинк наружу не отдаём ни в list, ни в search
    allowed = _resolve_base(base_dir)

    count = 0
    for dp, dirs, fns in os.walk(root_path):
        dirs[:] = [name for name in dirs if not _skip_dir(name, include_hidden)]
        for fn in fns:
            if _skip_file(fn, include_hidden):
                continue
            if count >= max_files:
                return
            full_path = Path(dp) / fn
            try:
                real = full_path.resolve()
                inside = _is_relative_to(real, allowed) and _is_physical(real) and not _is_hardlink(real)
            except (OSError, RuntimeError):  # RuntimeError: цикл симлинков до Python 3.13
                inside = False
            if not inside:
                continue
            rel = full_path.relative_to(root_path).as_posix()
            count += 1
            yield rel, real  # физический путь: читаем его, а не то, что вернул обход


def list_files(root, max_files=DEFAULT_MAX_FILES, include_hidden=False, base_dir=None):
    out = []
    for rel, _path in _iter_files(root, max_files=max_files, include_hidden=include_hidden, base_dir=base_dir):
        out.append(rel)
    return sorted(out)


def read_file(path, max_bytes=MAX_OUTPUT_BYTES, base_dir=None, redact=True):
    # Предел держим в 0..MAX_OUTPUT_BYTES: отрицательный давал read(-1) и читал файл целиком мимо лимита.
    max_bytes = max(0, min(max_bytes, MAX_OUTPUT_BYTES))
    resolved = _resolve_path(path, base_dir)
    # Файл открываем цепочкой dir_fd с O_NOFOLLOW: подмена компонента после проверки не даёт чтения.
    fd = _open_physical(_resolve_base(base_dir), resolved, path)
    # Ошибки называют путь так, как его передали, а не разрешённую цель симлинка внутри базы.
    try:
        with os.fdopen(fd, "rb") as f:
            data = f.read(max_bytes + 1)
    except OSError as exc:
        raise type(exc)(exc.errno, exc.strerror, str(path)) from None
    truncated = len(data) > max_bytes
    text = data[:max_bytes].decode("utf-8", "replace")
    if redact:
        text = redact_text(text)
    return {"path": str(resolved), "truncated": truncated, "bytes": min(len(data), max_bytes), "text": text}


def search(
    pattern,
    root,
    max_files=DEFAULT_MAX_FILES,
    max_hits=DEFAULT_MAX_HITS,
    include_hidden=False,
    base_dir=None,
    regex=False,
):
    rx = re.compile(pattern) if regex else None
    hits = []
    base = _resolve_base(base_dir)
    for rel, p in _iter_files(root, max_files=max_files, include_hidden=include_hidden, base_dir=base_dir):
        try:
            fd = _open_physical(base, p, rel)
            with os.fdopen(fd, encoding="utf-8", errors="replace") as f:
                for i, line in enumerate(f, 1):
                    if (rx.search(line) if rx else pattern in line):
                        hits.append({"path": rel, "line": i, "text": redact_text(line.rstrip())[:300]})
                        if len(hits) >= max_hits:
                            return hits
        except Exception:
            continue
    return hits


def summarize(root, max_files=DEFAULT_MAX_FILES, include_hidden=False, base_dir=None):
    base = _resolve_base(base_dir)
    listed = list(_iter_files(root, max_files=max_files, include_hidden=include_hidden, base_dir=base_dir))
    by_ext = {}
    total = 0
    for rel, p in listed:
        try:
            total += _stat_physical(base, p, rel).st_size
        except (OSError, PathAccessError):
            pass
        ext = os.path.splitext(rel)[1] or "(none)"
        by_ext[ext] = by_ext.get(ext, 0) + 1
    return {"files": len(listed), "total_bytes": total, "by_ext": by_ext, "max_files": max_files}


def _option(args, name, default=None):
    if name not in args:
        return default
    index = args.index(name)
    if index + 1 >= len(args):
        raise ValueError(f"missing value for {name}")
    return args[index + 1]


def _int_option(args, name, default):
    return int(_option(args, name, default))


def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__)
        return 2
    cmd = a[0]
    try:
        base_dir = _option(a, "--base")
        if cmd in ("list", "read", "search", "summarize") and not (base_dir or "").strip():
            print(json.dumps({"error": "ConfigError", "message": "--base is required: pass the allowed root (fail-closed)"}, ensure_ascii=False))
            return 2
        if base_dir is not None:
            # Явная «.» или относительная база становятся абсолютным путём уже в CLI.
            base_dir = os.path.abspath(_expand_base(base_dir))
        include_hidden = "--include-hidden" in a
        if cmd == "list" and len(a) > 1:
            print(json.dumps(
                list_files(a[1], max_files=_int_option(a, "--max-files", DEFAULT_MAX_FILES),
                           include_hidden=include_hidden, base_dir=base_dir),
                ensure_ascii=False, indent=2))
            return 0
        if cmd == "read" and len(a) > 1:
            print(json.dumps(
                read_file(a[1], _int_option(a, "--max-bytes", MAX_OUTPUT_BYTES),
                          base_dir=base_dir, redact="--no-redact" not in a),
                ensure_ascii=False, indent=2))
            return 0
        if cmd == "search" and len(a) > 2:
            print(json.dumps(
                search(a[1], a[2], max_files=_int_option(a, "--max-files", DEFAULT_MAX_FILES),
                       max_hits=_int_option(a, "--max-hits", DEFAULT_MAX_HITS),
                       include_hidden=include_hidden, base_dir=base_dir, regex="--regex" in a),
                ensure_ascii=False, indent=2))
            return 0
        if cmd == "summarize" and len(a) > 1:
            print(json.dumps(
                summarize(a[1], max_files=_int_option(a, "--max-files", DEFAULT_MAX_FILES),
                          include_hidden=include_hidden, base_dir=base_dir),
                ensure_ascii=False, indent=2))
            return 0
    except Exception as exc:
        print(json.dumps({"error": type(exc).__name__, "message": str(exc)}, ensure_ascii=False))
        return 1
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
