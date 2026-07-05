# ==========================================
# [FILE ID CARD]
# ID: tools.thread_runner
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: terminal-thread runner (workbench этап 2): тред-файл → контекст → модель → append.
# ==========================================
"""thread_runner.py — terminal-thread runner (workbench этап 2): тред-файл → контекст → модель → append.

Компонент 2+4 offline/headless workbench (topics/offline-headless-workbench-mvp-2026-06-26). Headless
агент-цикл в терминале: читает Markdown-тред (front-matter: agent/model/task), собирает релевантный
контекст из канона (canon_index FTS-retrieval, не весь репо), зовёт ЛОКАЛЬНУЮ модель (llama-server,
OpenAI-совместимый) или offline-синтетик-фолбэк, дописывает шаг в тред. Stdlib (urllib). Termux-friendly.

Тред-файл `threads/<имя>.md`: front-matter `task:`/`agent:`/`model:` + тело = накопленные шаги.

CLI:
  python tools/thread_runner.py threads/x.md                 # синтетик-шаг (без модели)
  python tools/thread_runner.py threads/x.md --llama --endpoint http://localhost:8080/v1 --model <gguf>
"""
import os
from _ioutil import configure_output
from _cli import help_guard
import sys
import re
import json
import urllib.request
import canon_index

configure_output()
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("COLLAB_ROOT") or os.path.dirname(HERE)


def load_thread(path):
    """Тред → {fm, body, task}: front-matter + тело + извлечённая задача."""
    text = open(path, encoding="utf-8", errors="replace").read()
    fm, body = {}, text
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end >= 0:
            for line in text[3:end].splitlines():
                m = re.match(r"^([A-Za-z0-9_\-]+):\s*(.*)$", line)
                if m:
                    fm[m.group(1)] = m.group(2).strip()
            nl = text.find("\n", end + 1)
            body = text[nl + 1:] if nl >= 0 else ""
    task = fm.get("task") or _last_human(body) or "(нет задачи)"
    return {"fm": fm, "body": body, "task": task}


def assemble_context(task, db_path=None, k=5):
    """FTS-retrieval релевантных блоков под задачу (не весь репо). Возвращает (текст, [id])."""
    db = db_path or canon_index.DB
    res = canon_index.search(task, db_path=db, limit=k) or []
    ctx = "\n".join("[%s %s] %s" % (r["id"], r["type"] or "—", r["snippet"]) for r in res)
    return ctx, [r["id"] for r in res]


def step(task, ctx, use_llama=False, endpoint="", model="", agent="runner"):
    """Один шаг: собрать промпт, вызвать модель (или синтетик), вернуть текст ответа."""
    prompt = ("Ты агент «%s» в общем каноне. Задача:\n%s\n\nРелевантный контекст (FTS-срез):\n%s\n\n"
              "Дай краткий ответ/план по задаче, ссылаясь на блоки контекста по id." % (agent, task, ctx or "(пусто)"))
    if use_llama:
        try:
            return _call_llama(prompt, endpoint, model)
        except Exception as e:
            return "[llama недоступна: %s; offline-фолбэк] %s" % (str(e)[:50], _synth(task, ctx))
    return _synth(task, ctx)


def run(thread_path, db_path=None, use_llama=False, endpoint="", model="", k=5):
    """Прогнать один шаг по треду: контекст → модель → append шага в файл. Возвращает {ids, answer}."""
    th = load_thread(thread_path)
    ctx, ids = assemble_context(th["task"], db_path, k)
    agent = th["fm"].get("agent", "runner")
    answer = step(th["task"], ctx, use_llama, endpoint, model, agent)
    n = th["body"].count("\n## шаг ") + 1
    block = "\n## шаг %d · %s%s\n**контекст:** %s\n\n%s\n" % (
        n, agent, " (llama)" if use_llama else " (offline-синтетик)", ", ".join(ids) or "—", answer.strip())
    with open(thread_path, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(block)
    return {"ids": ids, "answer": answer, "step": n}


def _synth(task, ctx):
    ids = re.findall(r"\[([A-Za-z0-9_\-]+)\s", ctx)
    return ("[offline-синтетик] По задаче «%s»: опираюсь на блоки %s. План: (1) свериться с %s; "
            "(2) предложить вариант; (3) вынести на сверку." % (
                task[:60], ", ".join(ids[:3]) or "(нет контекста)", ids[0] if ids else "каноном"))


def _call_llama(prompt, endpoint, model):
    url = endpoint.rstrip("/") + "/chat/completions"
    payload = json.dumps({"model": model, "messages": [{"role": "user", "content": prompt}],
                          "temperature": 0.3, "max_tokens": 600}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode("utf-8"))["choices"][0]["message"]["content"]


def _last_human(body):
    for ln in reversed(body.splitlines()):
        s = ln.strip()
        if s and not s.startswith("#") and not s.startswith("**"):
            return s[:200]
    return ""


def main(argv):
    help_guard(__doc__, argv)
    args = [a for a in argv if not a.startswith("--")]
    if not args:
        print("thread_runner: нужен тред-файл. Пример: thread_runner.py threads/x.md"); return 2
    tp = args[0] if os.path.isabs(args[0]) else os.path.join(ROOT, args[0])
    if not os.path.exists(tp):
        print("thread_runner: тред не найден: %s" % tp); return 2
    use_llama = "--llama" in argv
    endpoint = _opt(argv, "--endpoint", "http://localhost:8080/v1")
    model = _opt(argv, "--model", "local-gguf")
    k = int(_opt(argv, "--k", "5"))
    r = run(tp, use_llama=use_llama, endpoint=endpoint, model=model, k=k)
    print("=== THREAD-RUNNER: шаг %d · %s ===" % (r["step"], "llama" if use_llama else "offline-синтетик"))
    print("  контекст (FTS): %s" % (", ".join(r["ids"]) or "—"))
    print("  ответ дописан в тред:\n  %s" % r["answer"][:200])
    return 0


def _opt(argv, flag, default):
    if flag in argv:
        i = argv.index(flag)
        if i + 1 < len(argv):
            return argv[i + 1]
    return default


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
