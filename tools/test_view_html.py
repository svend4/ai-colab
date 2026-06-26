"""Тест view_html.py — компиляция среза в <details>-HTML (escaping, свёрнуто, ссылки)."""
import os
import sys

os.environ.setdefault("PYTHONUTF8", "1")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import view_html as vh

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


def main():
    fails = []
    canon = {
        "a": {"id": "a", "path": "tasks/a.md", "body": "тело a <script>alert(1)</script> опасное", "links": {"b"}},
        "b": {"id": "b", "path": "tasks/b.md", "body": "тело b нормальное", "links": set()},
    }
    doc = vh.compile_html(canon, ["a", "b"], "тест")

    if doc.count("<details") != 2:
        fails.append("должно быть 2 <details>: %d" % doc.count("<details"))
    if "<!doctype html>" not in doc.lower() or "</body></html>" not in doc:
        fails.append("самодостаточный HTML-каркас обязателен")
    # XSS-escaping: сырой <script> НЕ должен попасть, должен быть экранирован
    if "<script>alert" in doc:
        fails.append("сырой <script> попал в HTML (нет escaping — XSS-риск!)")
    if "&lt;script&gt;" not in doc:
        fails.append("тело должно быть HTML-экранировано")
    # свёрнуто по умолчанию: ни одного open-атрибута
    if "<details open" in doc or "<details id='a' open" in doc:
        fails.append("должно быть свёрнуто (без open) — progressive disclosure")
    # ссылка a→b отрендерена как навигация
    if "href='#b'" not in doc:
        fails.append("ссылка a→b должна стать навигацией href='#b'")
    # оба id присутствуют
    if "id='a'" not in doc or "id='b'" not in doc:
        fails.append("оба блока должны быть якорями")

    if fails:
        print("FAIL test_view_html:")
        for f in fails:
            print("  -", f)
        sys.exit(1)
    print("OK test_view_html: 2×<details> · самодостаточный каркас · XSS-escaping · свёрнуто · ссылка→навигация")


if __name__ == "__main__":
    main()
