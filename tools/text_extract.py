#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.text_extract
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт text_extract.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""
Generic text extract (T-133) — read-only stdlib extraction for core/portals.

Supported now: .md, .markdown, .txt, .text, .html, .htm, .docx (DOCX via stdlib zipfile — no dependency).
.pdf still needs an explicit dependency decision (pypdf) and stays gated until then.

CLI:
    python tools/text_extract.py extract <file> [--base ROOT]
    python tools/text_extract.py summary <file> [--base ROOT]
"""
import errno
import os
import stat
import sys
from pathlib import Path
from _ioutil import configure_output
from _cli import help_guard
import re
import json
import zipfile
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DRIVERS = os.path.join(ROOT, "drivers")
if DRIVERS not in sys.path:
    sys.path.insert(0, DRIVERS)
from files.files_driver import read_file, PathAccessError
from redaction import redact  # канонический redaction для бинарного docx-пути

# .docx читается stdlib-зипом (без внешней зависимости — котёл-пункт 5, agree с Codex);
# .pdf по-прежнему требует осознанного решения о зависимости (pypdf) и сюда не входит.
SUPPORTED = {".md", ".markdown", ".txt", ".text", ".html", ".htm", ".docx"}
MAX_EXTRACT_CHARS = 20000
MAX_MEMORY_CHARS = 4000
MAX_SUMMARY_CHARS = 240
W_NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

configure_output()

class _HTMLText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag.lower() in {"script", "style", "noscript"}:
            self.skip += 1
        if tag.lower() in {"p", "div", "br", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6"}:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag.lower() in {"script", "style", "noscript"} and self.skip:
            self.skip -= 1
        if tag.lower() in {"p", "div", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6"}:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.skip and data:
            self.parts.append(data)

    def text(self):
        return "".join(self.parts)

def _normalize(text):
    lines = []
    for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        compact = re.sub(r"\s+", " ", line).strip()
        if compact:
            lines.append(compact)
    return "\n".join(lines)

def _strip_markdown_noise(text):
    # Keep readable words, remove common Markdown syntax that hurts summaries/search snippets.
    # Drop leading YAML-ish front-matter from docs/topics before FTS summaries.
    text = re.sub(r"^\s*---\s*\n.*?\n---\s*\n", "", text, flags=re.S)
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"^\s{0,3}#{1,6}\s*", "", text, flags=re.M)
    text = re.sub(r"^[\s>*_`#-]+", "", text, flags=re.M)
    return text

def _is_physical(path):
    # На Python 3.12 realpath() после цикла симлинков оставляет хвост нерешённым и схлопывает «..» по тексту,
    # так что результат может всё ещё называть симлинк. Полностью разрешённый путь симлинков не содержит.
    current = path
    while True:
        if os.path.islink(current):
            return False
        parent = os.path.dirname(current)
        if parent == current:
            return True
        current = parent


def _has_loop(path):
    # Цикл симлинков в пути, даже если «..» потом уводит результат внутрь: строгий realpath() кидает ELOOP.
    try:
        os.path.realpath(path, strict=True)
    except OSError as exc:
        return exc.errno == errno.ELOOP
    return False


# O_NOFOLLOW and dir_fd are not available everywhere (not on Windows); there the path-based check stays.
_SAFE_OPEN = hasattr(os, "O_NOFOLLOW") and os.open in os.supports_dir_fd


def _check_regular(st, given):
    # Симлинк (подменён после проверки), каталог, устройство и FIFO — не файл; жёсткая ссылка отказывает.
    if stat.S_ISLNK(st.st_mode):
        raise PathAccessError("path outside allowed root: %s" % given)
    if not stat.S_ISREG(st.st_mode):
        raise FileNotFoundError(errno.ENOENT, "not a file", str(given))  # каталог, устройство или FIFO
    if st.st_nlink > 1:
        raise PathAccessError("hard-linked file is refused (fail-closed): %s" % given)


def _open_physical(base, physical, given):
    # Открывает уже разрешённый путь внутри базы цепочкой dir_fd с O_NOFOLLOW (как в drivers/files): компонент,
    # подменённый на симлинк после проверки, даёт ELOOP и не открывается. Тип и число ссылок проверяются по stat
    # до open(): открытие устройства или FIFO уже может что-то сделать. После open() сверяется тот же объект.
    try:
        if not _SAFE_OPEN:
            before = os.stat(str(physical))
            _check_regular(before, given)
            fd = os.open(str(physical), os.O_RDONLY | getattr(os, "O_BINARY", 0))
        else:
            parts = Path(physical).relative_to(base).parts
            if not parts:
                raise FileNotFoundError(errno.ENOENT, "not a file")
            dirfd = os.open(str(base), os.O_RDONLY)
            try:
                for name in parts[:-1]:
                    nextfd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=dirfd)
                    os.close(dirfd)
                    dirfd = nextfd
                before = os.stat(parts[-1], dir_fd=dirfd, follow_symlinks=False)
                _check_regular(before, given)
                fd = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_NOCTTY, dir_fd=dirfd)
            finally:
                os.close(dirfd)
    except OSError as exc:
        if exc.errno == errno.ELOOP:  # компонент стал симлинком: путь снаружи
            raise PathAccessError("path outside allowed root: %s" % given) from None
        raise type(exc)(exc.errno, exc.strerror, str(given)) from None
    try:
        st = os.fstat(fd)
        if _SAFE_OPEN and (st.st_dev, st.st_ino) != (before.st_dev, before.st_ino):
            raise PathAccessError("path changed while opening: %s" % given)
        _check_regular(st, given)
    except BaseException:
        os.close(fd)
        raise
    return fd


def _docx_read(path, base_dir):
    """Извлечь текст .docx чистой stdlib (zipfile + WordprocessingML), с confinement и redaction.

    .docx — бинарный Open XML, поэтому идёт мимо read_file (тот читает текст). Confinement к
    base_dir (allowed-root) и маскирование секретов делаем здесь явно, как и read_file(redact=True)."""
    # Пустая база и «.» отказывают: иначе границей становится текущая папка (fail-closed).
    if base_dir is None or os.path.normpath(str(base_dir).strip()) == ".":
        raise PathAccessError("allowed root must be an explicit path, not blank or '.' (fail-closed)")
    raw = path if os.path.isabs(str(path)) else os.path.join(base_dir, str(path))
    real = os.path.realpath(raw)
    base_real = os.path.realpath(base_dir)
    try:
        inside = os.path.commonpath([real, base_real]) == base_real and _is_physical(real) and not _has_loop(raw)
    except ValueError:  # разные диски (Windows) — точно вне корня
        inside = False
    if not inside:
        raise PathAccessError("path outside allowed root: %s" % path)
    # Файл читается через fd от базы: подмена компонента после проверки и жёсткая ссылка не дают чтения снаружи.
    fd = _open_physical(base_real, real, path)
    try:
        with os.fdopen(fd, "rb") as f, zipfile.ZipFile(f) as zf:
            xml = zf.read("word/document.xml")
    except (zipfile.BadZipFile, KeyError) as exc:
        raise ValueError("not a valid .docx (Open XML): %s" % exc)
    try:
        root = ET.fromstring(xml)
    except ET.ParseError as exc:
        raise ValueError("not a valid .docx document.xml: %s" % exc)

    paragraphs = []
    for paragraph in root.iter(W_NS + "p"):
        parts = []
        for node in paragraph.iter():
            if node.tag == W_NS + "t" and node.text:
                parts.append(node.text)
            elif node.tag == W_NS + "tab":
                parts.append("\t")
            elif node.tag in {W_NS + "br", W_NS + "cr"}:
                parts.append("\n")
        text = "".join(parts).strip()
        if text:
            paragraphs.append(text)

    if not paragraphs:
        paragraphs = [node.text for node in root.iter(W_NS + "t") if node.text]
    return real, redact("\n".join(paragraphs))

def extract(path, base_dir=ROOT, max_chars=MAX_EXTRACT_CHARS):
    ext = os.path.splitext(str(path))[1].lower()
    supported = ext in SUPPORTED
    if ext == ".docx":
        real, text = _docx_read(path, base_dir)
        data_path, data_truncated = real, False
    else:
        data = read_file(path, base_dir=base_dir, redact=True)
        raw = data.get("text", "")
        if ext in {".html", ".htm"}:
            parser = _HTMLText()
            parser.feed(raw)
            text = parser.text()
        elif ext in {".md", ".markdown"}:
            text = _strip_markdown_noise(raw)
        else:
            text = raw
        data_path, data_truncated = data.get("path"), bool(data.get("truncated"))
    text = _normalize(text)
    truncated = len(text) > max_chars
    return {
        "path": data_path,
        "type": ext.lstrip(".") or "file",
        "supported": supported,
        "text": text[:max_chars],
        "chars": min(len(text), max_chars),
        "truncated": truncated or data_truncated,
    }

def summary_from_text(text, max_chars=MAX_SUMMARY_CHARS):
    text = _normalize(text)
    if not text:
        return ""
    return text[:max_chars]

def memory_text(path, base_dir=ROOT, max_chars=MAX_MEMORY_CHARS):
    """Text fragment safe to store in workbench.summary for FTS/search."""
    item = extract(path, base_dir=base_dir, max_chars=max_chars)
    return item["text"]

def _arg_value(args, name, default=None):
    if name not in args:
        return default
    pos = args.index(name) + 1
    if pos >= len(args):
        raise ValueError("missing value for %s" % name)
    return args[pos]

def main():
    help_guard(__doc__)
    a = sys.argv[1:]
    if len(a) < 2:
        print(__doc__)
        return 2
    cmd = a[0]
    base = _arg_value(a, "--base", ROOT)
    try:
        if cmd == "extract":
            print(json.dumps(extract(a[1], base_dir=base), ensure_ascii=False, indent=2))
            return 0
        if cmd == "summary":
            item = extract(a[1], base_dir=base)
            print(summary_from_text(item["text"]))
            return 0
    except (OSError, PathAccessError, ValueError) as exc:
        print(json.dumps({"error": type(exc).__name__, "message": str(exc)}, ensure_ascii=False))
        return 1
    print(__doc__)
    return 2

if __name__ == "__main__":
    sys.exit(main())
