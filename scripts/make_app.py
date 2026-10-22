"""Bundle the atlas into one HTML file that opens by double-click (no server needed).

    python make_app.py <data.json> <out.html> [--personal]

Without --personal every pet starts as "not owned" so the file can be shared;
each viewer sets their own levels and checkmarks in the app (saved in their browser).
"""
import base64, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

data_path, out_path = sys.argv[1], sys.argv[2]
personal = "--personal" in sys.argv

data = json.load(open(data_path, encoding="utf-8"))
if not personal:
    for p in data["pets"]:
        p["lvl"], p["prog"] = 0, 0

html = open(os.path.join(HERE, "template.html"), encoding="utf-8").read()
html = html.replace("/*DATA*/null", json.dumps(data, separators=(",", ":")))
for name in ("verteron", "altgard", "abyss"):
    b64 = base64.b64encode(open(os.path.join(ROOT, name + ".webp"), "rb").read()).decode()
    html = html.replace(f'"{name}.webp"', f'"data:image/webp;base64,{b64}"')

# the page is written as body content; give it a full document so it renders standards-mode from disk
head, body = html.split('<div class="app">', 1)
doc = '<!doctype html>\n<html lang="en"><head>' + head + '</head><body><div class="app">' + body + "</body></html>"
open(out_path, "w", encoding="utf-8").write(doc)
print(out_path, round(os.path.getsize(out_path) / 1e6, 2), "MB")
