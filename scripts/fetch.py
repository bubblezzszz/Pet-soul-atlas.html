import json, os, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor

BASE = "https://questlog.gg/aion-2/api/trpc/"
CDN = "https://cdn.questlog.gg/aion-2"
HDR = {"User-Agent": "Mozilla/5.0"}
OUT = os.path.dirname(os.path.abspath(__file__))


def call(method, **inp):
    inp["language"] = "en"
    url = BASE + method + "?input=" + urllib.parse.quote(json.dumps(inp, separators=(",", ":")))
    with urllib.request.urlopen(urllib.request.Request(url, headers=HDR), timeout=60) as r:
        return json.load(r)["result"]["data"]


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=HDR), timeout=60) as r:
        return r.read()


pets = []
for p in range(1, 7):
    pets += call("database.getPets", page=p)["pageData"]
print("pets", len(pets))

with ThreadPoolExecutor(8) as ex:
    det = dict(zip([p["id"] for p in pets], ex.map(lambda p: call("database.getPet", id=p["id"]), pets)))

npc_ids = sorted({n["id"] for d in det.values() for n in (d.get("petIsDroppedByNpcs") or [])})
with ThreadPoolExecutor(8) as ex:
    npcs = dict(zip(npc_ids, ex.map(lambda i: call("database.getNpc", id=i), npc_ids)))
print("npcs", len(npcs))

markers = call("map.getMarkers")
regions = call("map.getRegions")

json.dump({"pets": pets, "det": det, "npcs": npcs}, open(os.path.join(OUT, "db.json"), "w"))
json.dump(markers, open(os.path.join(OUT, "markers.json"), "w"))
json.dump(regions, open(os.path.join(OUT, "regions.json"), "w"))

os.makedirs(os.path.join(OUT, "icons"), exist_ok=True)


def icon(p):
    path = p["icon"].split(".")[0]
    dest = os.path.join(OUT, "icons", p["id"] + ".webp")
    if not os.path.exists(dest):
        open(dest, "wb").write(get(CDN + path + ".webp"))


with ThreadPoolExecutor(8) as ex:
    list(ex.map(icon, pets))
print("done")
