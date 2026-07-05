# ==========================================
# [FILE ID CARD]
# ID: tools.text_brain
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: proposal-only brain-adapter для textscene-канвы (трилогия scene→mux→BRAIN, спец §5).
# ==========================================
"""text_brain.py — proposal-only brain-adapter для textscene-канвы (трилогия scene→mux→BRAIN, спец §5).

Завершает textscene (topics/textscene-unified-spec-2026-06-26 §5): модель ПРЕДЛАГАЕТ типизированные ячейки
`text_cell.v1` (status:proposed, owner:brain:<model>), но НИКОГДА не принимает — это шаг-ГЕЙТ формулы
(defect-class-formula §C.2 п.4 / D-031): «галочку ставит гейт/человек, не автор». Бэкенды как tvcp-ai/1:
offline-синтетик (ДЕТЕРМИНИРОВАН, дефолт) ИЛИ локальная llama (urllib, OpenAI-совместимая). Вывод санируется
(clamp длины, status ПРИНУДИТЕЛЬНО proposed) и кладётся в `cells/` канвы как предложения — принимает их
text_mux/человек. Инвариант: brain не мутирует canon и не ставит accepted.

CLI:
  python tools/text_brain.py <canvas-dir> --topic "<тема>" [--kind claim] [--n 3]
  python tools/text_brain.py <canvas-dir> --topic "<тема>" --llama --endpoint http://localhost:8080/v1 --model x
"""
import os
from _ioutil import configure_output
from _cli import help_guard
import sys
import re
import json
import urllib.request

configure_output()
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import text_mux as tm  # переиспуем validate_cell / load_cells / emit_event

ROOT = os.environ.get("COLLAB_ROOT") or os.path.dirname(HERE)
KINDS = ("claim", "risk", "question", "proposal", "summary")  # что модель ВПРАВЕ предлагать (не decision/accept)


def _slug(s):
    return re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")[:40] or "x"


def _synth(topic, kind, i):
    """Детерминированное синтетик-предложение (offline-бэкенд)."""
    t = {
        "claim": "Тезис №%d по «%s»: требует проверки кворумом (independent-consensus), не принимать соло.",
        "risk": "Риск №%d по «%s»: возможный дефект класса a–f — нужна верификация на месте.",
        "question": "Вопрос №%d по «%s»: какой инвариант здесь ещё не покрыт тестом?",
        "proposal": "Предложение №%d по «%s»: вынести на гейт после красной команды.",
        "summary": "Сводка №%d по «%s»: ключевые узлы и открытые хвосты.",
    }
    return (t.get(kind, "Заметка №%d по «%s».")) % (i, topic)


def _call_llama(prompt, endpoint, model):
    url = endpoint.rstrip("/") + "/chat/completions"
    payload = json.dumps({"model": model, "messages": [{"role": "user", "content": prompt}],
                          "temperature": 0.3, "max_tokens": 400}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))["choices"][0]["message"]["content"]


def propose(topic, kind="claim", n=3, canvas_id="canvas", model="offline", endpoint="", context=None):
    """Список ПРЕДЛОЖЕННЫХ ячеек. status ВСЕГДА 'proposed' (модель не принимает). Offline — детерминирован."""
    if kind not in KINDS:
        kind = "claim"
    cells = []
    for i in range(1, max(1, n) + 1):
        if model != "offline" and endpoint:
            try:
                body = _call_llama("Тема: %s. Дай краткий %s №%d (1-2 предложения)." % (topic, kind, i), endpoint, model)
            except Exception as e:
                body = "[llama недоступна: %s; offline] %s" % (str(e)[:40], _synth(topic, kind, i))
        else:
            body = _synth(topic, kind, i)
        cell = {
            "schema": "text_cell.v1",
            "id": "brain-%s-%s-%d" % (_slug(topic), kind, i),
            "canvas_id": canvas_id, "kind": kind, "owner": "brain:%s" % model, "topic": topic,
            "position": {"row": kind, "col": "brain:%s" % model},
            "status": "proposed",                       # ПРИНУДИТЕЛЬНО — никогда accepted
            "body": (body or "").strip()[:400],          # clamp (санитизация вывода модели)
            "links": [{"rel": "derived_from", "target": t} for t in (context or [])][:5],
            "lamport": i,
        }
        ok, _why = tm.validate_cell(cell)
        if ok:
            cell["status"] = "proposed"                  # гарантия после валидации
            cells.append(cell)
    return cells


def write_proposals(canvas_dir, cells):
    """Записать предложения в cells/ канвы (status принудительно proposed) + событие cell_seed в outbox."""
    d = os.path.join(canvas_dir, "cells")
    os.makedirs(d, exist_ok=True)
    written = []
    for c in cells:
        c = dict(c); c["status"] = "proposed"            # двойная гарантия на записи
        p = os.path.join(d, c["id"] + ".json")
        with open(p, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(c, fh, ensure_ascii=False, indent=2)
        written.append(p)
        tm.emit_event(os.path.join(canvas_dir, "outbox"),
                      {"kind": "cell_seed", "id": c["id"], "owner": c["owner"], "status": "proposed"})
    return written


def _opt(argv, flag, default=None):
    if flag in argv:
        i = argv.index(flag)
        if i + 1 < len(argv):
            return argv[i + 1]
    return default


def main(argv):
    help_guard(__doc__, argv)
    args = [a for a in argv if not a.startswith("--")]
    if not args:
        print("text_brain: нужен <canvas-dir>. Пример: text_brain.py sandbox/canvas-demo --topic \"оракул\""); return 2
    canvas_dir = args[0] if os.path.isabs(args[0]) else os.path.join(ROOT, args[0])
    topic = _opt(argv, "--topic")
    if not topic:
        print("text_brain: нужен --topic \"<тема>\""); return 2
    kind = _opt(argv, "--kind", "claim")
    n = int(_opt(argv, "--n", "3"))
    use_llama = "--llama" in argv
    model = _opt(argv, "--model", "local-gguf") if use_llama else "offline"
    endpoint = _opt(argv, "--endpoint", "http://localhost:8080/v1") if use_llama else ""
    cid = os.path.basename(os.path.abspath(canvas_dir))
    cells = propose(topic, kind=kind, n=n, canvas_id=cid, model=model, endpoint=endpoint)
    written = write_proposals(canvas_dir, cells)
    print("text_brain: %d предложений (☐ proposed, owner brain:%s) → %s/cells/" % (len(written), model, cid))
    for c in cells:
        print("  ☐ %s [%s] %s" % (c["id"], c["kind"], c["body"][:70]))
    print("  (принимает text_mux/человек — brain НЕ ставит accepted)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
