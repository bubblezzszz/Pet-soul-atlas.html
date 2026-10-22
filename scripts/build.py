import base64, io, json, math, os
from PIL import Image
from owned import OWNED

D = os.path.dirname(os.path.abspath(__file__))
db = json.load(open(os.path.join(D, "db.json")))
regions = json.load(open(os.path.join(D, "regions.json")))
order = json.load(open(os.path.join(D, "sheet_order.json")))
status = {order[i]: v for i, v in OWNED.items()}

WORLDS = {"1010": "V", "1110": "A", "20": "R"}
FAM = {"intellect": "cogni", "feral": "fera", "nature": "natura", "trans": "varian", "special": "special"}
STAT = {
    "hpmax": "Max HP", "critical": "Critical Hit", "criticalresist": "Critical Hit Resist",
    "accuracy": "Accuracy", "evasion": "Evasion", "str": "Might", "dex": "Precision",
    "agi": "Agility", "con": "Health", "spmax": "Max Stamina",
    "groundvehiclespeed": "Mount Speed", "vehiclesprintcost": "Mount Sprint Cost",
}


def walk(o, out):
    if isinstance(o, list):
        for x in o:
            walk(x, out)
    elif isinstance(o, dict):
        if "coordinates" in o and "mapWorldId" in o:
            out.append(o)
        else:
            for v in o.values():
                walk(v, out)


markers = []
walk(json.load(open(os.path.join(D, "markers.json"))), markers)
spawns = {}
for m in markers:
    if m.get("dbType") == "npc" and m["mapWorldId"] in WORLDS:
        for c in m["coordinates"]:
            spawns.setdefault(m["dbId"], []).append((WORLDS[m["mapWorldId"]], c[0], c[1]))


def inside(x, y, poly):
    hit = False
    j = len(poly) - 1
    for i in range(len(poly)):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            hit = not hit
        j = i
    return hit


def simplify(poly, step):
    out = [poly[0]]
    for p in poly[1:]:
        if math.dist(p, out[-1]) >= step:
            out.append(p)
    return [[round(x / 100), round(y / 100)] for x, y in out]


regs = {"V": [], "A": [], "R": []}
for r in regions:
    w = WORLDS.get(r["mapWorldId"])
    if not w:
        continue
    regs[w].append({
        "n": r["name"], "k": r["kind"], "r": r["rank"],
        "l": [round(r["label"][0] / 100), round(r["label"][1] / 100)],
        "p": [simplify(p, 1500) for p in r["polygons"]],
        "_raw": r["polygons"],
    })


def area_of(w, x, y):
    best = None
    for r in regs[w]:
        if any(inside(x, y, p) for p in r["_raw"]):
            if best is None or (r["k"] == "battlefield" and best["k"] != "battlefield"):
                best = r
    if best:
        return best["n"]
    return min(regs[w], key=lambda r: math.dist((x / 100, y / 100), r["l"]))["n"]


def hotspots(pts, n=3, radius=7000, min_k=3):
    """Greedy: take the densest cluster, drop everything near it, repeat. Up to n distinct spots."""
    left, out = list(pts), []
    while left and len(out) < n:
        best = max((([q for q in left if math.dist(p, q) <= radius]) for p in left), key=len)
        if out and len(best) < min_k:
            break
        cx = sum(q[0] for q in best) / len(best)
        cy = sum(q[1] for q in best) / len(best)
        out.append((cx, cy, len(best)))
        left = [q for q in left if math.dist(q, (cx, cy)) > radius * 1.6]
    return out


def thumb(pid):
    im = Image.open(os.path.join(D, "icons", pid + ".webp")).convert("RGBA")
    im.thumbnail((128, 128))
    buf = io.BytesIO()
    im.save(buf, "WEBP", quality=72)
    return "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode()


pets = []
for p in db["pets"]:
    d = db["det"][p["id"]]
    srcs, pts = [], {"V": [], "A": [], "R": []}
    elsewhere = set()
    for n in d.get("petIsDroppedByNpcs") or []:
        nd = db["npcs"].get(n["id"]) or {}
        chance = next((i.get("chance") for i in nd.get("npcDropsItems", []) if i["name"].startswith("Soul:")), None)
        mine = spawns.get(n["id"], [])
        for w, x, y in mine:
            pts[w].append((x, y))
        for r in nd.get("npcIsFoundInRegions") or []:
            if r["id"] not in WORLDS:
                elsewhere.add(r["name"])
        if not nd.get("npcIsFoundInRegions"):
            elsewhere.add("Dungeon / instance")
        srcs.append({
            "n": nd.get("name", n["name"]), "lv": nd.get("level"),
            "t": nd.get("npcSubType", ""), "c": chance,
            "w": sorted({w for w, _, _ in mine}),
        })
    spots = {}
    for w in ("V", "A", "R"):
        if pts[w]:
            spots[w] = {"t": len(pts[w]), "s": [
                {"x": round(cx / 100), "y": round(cy / 100), "k": k, "a": area_of(w, cx, cy)}
                for cx, cy, k in hotspots(pts[w])
            ]}
    es = d.get("equipStats") or {}
    lv = [{"lv": 1, "s": [[STAT.get(s["id"], s["id"]), s["value"]] for s in es.get("mainStats", [])]}]
    for e in es.get("enchants", []):
        lv.append({"lv": e["level"], "s": [[STAT.get(k, k), v["value"]] for k, v in e["stats"].items()]})
    st = status.get(p["id"], (0, 0))
    pets.append({
        "id": p["id"], "n": p["name"], "f": FAM[p["mainCategory"]], "need": d.get("needSoul", 5),
        "lvl": st[0], "prog": st[1], "lvs": lv, "src": srcs, "sp": spots,
        "else": sorted(elsewhere), "img": thumb(p["id"]),
    })

for w in regs:
    for r in regs[w]:
        r.pop("_raw")

json.dump({"regions": regs, "pets": pets}, open(os.path.join(D, "data.json"), "w"), separators=(",", ":"))
both = sum(1 for p in pets if "V" in p["sp"] and "A" in p["sp"])
vonly = sum(1 for p in pets if p["sp"].keys() == {"V"})
aonly = sum(1 for p in pets if p["sp"].keys() == {"A"})
none = [p["n"] for p in pets if not p["sp"]]
print("both", both, "V only", vonly, "A only", aonly, "neither", len(none))
print("owned", sum(1 for p in pets if p["lvl"] > 0), "max", sum(1 for p in pets if p["lvl"] == 3))
print("size", os.path.getsize(os.path.join(D, "data.json")) // 1024, "KB")
