# Pet Soul Atlas

A farming map for AION 2 pet souls. Each pet gets one pin on the Verteron, Altgard and Abyss (Lower Reshanta) maps, placed at the densest cluster of the monsters that drop its soul.

## Use it

Download **`pet-soul-atlas.html`** and double-click it. It's one self-contained file (maps and portraits are built in), so it works offline with no install.

- **Zones:** switch between Verteron, Altgard and Abyss. "Only spawns in …" hides pets you can also get on another map.
- **Filters:** family (Cogni, Fera, Natura, Varian, Special), level, and search by pet or monster name.
- **Pins and list rows** are colored by family. A gold ring means maxed; a dark center dot means not owned yet.
- **Click a pin or a list row** to open the pet's card: best farming spot, backup spots, the other zones it spawns in, its Owned Effect per level, and which monsters drop its soul.
- **Set your level** on the card (Not owned / Lv1 / Lv2 / Max).
- **✓ Mark collected** in the list to hide a pet from the map.

Your levels and checkmarks are saved in your own browser, per file location. Clearing site data or opening the file in a different browser starts fresh.

## Rebuild

```bash
cd scripts
python fetch.py                         # pulls pets, monsters, spawns and map regions from questlog.gg (~50 MB, not committed)
python build.py                         # computes the pins -> data.json
python make_app.py data.json ../pet-soul-atlas.html
```

`make_app.py --personal` keeps the collection levels from `owned.py` baked in instead of starting everyone at zero.

## Credits

Pet, monster and spawn data, map region outlines and the world map images come from [questlog.gg](https://questlog.gg/aion-2/en). Game art, pet portraits and names are © NCSOFT. This is an unofficial fan tool.
