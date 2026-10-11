import sys
import json
import random
from pathlib import Path
from flask import Flask, render_template, jsonify, request

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


app = Flask(
    __name__,
    template_folder=str(Path(__file__).parent / "templates"),
    static_folder=str(Path(__file__).parent / "static")
)

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "monsters.json"
ALCHEMY_PATH = Path(__file__).resolve().parent.parent / "data" / "alchemy_recipes.json"


def load_raw_monsters():
    if not DATA_PATH.exists():
        return []
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_raw_recipes():
    if not ALCHEMY_PATH.exists():
        return []
    with open(ALCHEMY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/monsters")
def get_monsters():
    monsters = load_raw_monsters()
    q = request.args.get("q", "").strip().lower()
    creature_class = request.args.get("class", "").strip().lower()
    weakness = request.args.get("weakness", "").strip().lower()
    loot = request.args.get("loot", "").strip().lower()

    filtered = monsters

    if creature_class and creature_class != "all":
        filtered = [
            m for m in filtered 
            if creature_class in m.get("Class", "").lower()
        ]

    if weakness:
        filtered = [
            m for m in filtered 
            if any(weakness in w.lower() for w in m.get("Weaknesses", []))
        ]

    if loot:
        filtered = [
            m for m in filtered 
            if any(loot in item.lower() for item in m.get("Loot", []))
        ]

    if q:
        filtered = [
            m for m in filtered
            if q in m.get("Name", "").lower()
            or q in m.get("Class", "").lower()
            or any(q in loc.lower() for loc in m.get("Location", []))
            or any(q in w.lower() for w in m.get("Weaknesses", []))
            or any(q in item.lower() for item in m.get("Loot", []))
        ]

    return jsonify({
        "total": len(filtered),
        "monsters": filtered
    })


@app.route("/api/alchemy")
def get_alchemy():
    recipes = load_raw_recipes()
    q = request.args.get("q", "").strip().lower()
    recipe_type = request.args.get("type", "").strip().lower()
    ingredient = request.args.get("ingredient", "").strip().lower()
    monster = request.args.get("monster", "").strip().lower()

    filtered = recipes

    if recipe_type and recipe_type != "all":
        filtered = [r for r in filtered if r.get("type", "").lower() == recipe_type]

    if ingredient:
        filtered = [
            r for r in filtered 
            if ingredient in r.get("monster_ingredient", "").lower() 
            or any(ingredient in item.lower() for item in r.get("all_ingredients", []))
        ]

    if monster:
        filtered = [
            r for r in filtered 
            if any(monster in target.lower() for target in r.get("target_monsters", []))
        ]

    if q:
        filtered = [
            r for r in filtered
            if q in r.get("name", "").lower()
            or q in r.get("effect", "").lower()
            or q in r.get("monster_ingredient", "").lower()
            or any(q in target.lower() for target in r.get("target_monsters", []))
        ]

    return jsonify({
        "total": len(filtered),
        "recipes": filtered
    })


@app.route("/api/stats")
def get_stats():
    monsters = load_raw_monsters()
    recipes = load_raw_recipes()
    classes = {}
    weaknesses_set = set()
    loot_set = set()

    for m in monsters:
        cls = m.get("Class", "Unknown")
        classes[cls] = classes.get(cls, 0) + 1
        for w in m.get("Weaknesses", []):
            weaknesses_set.add(w)
        for item in m.get("Loot", []):
            if not item.startswith("None ("):
                loot_set.add(item)

    return jsonify({
        "total_monsters": len(monsters),
        "total_classes": len(classes),
        "classes": classes,
        "total_weaknesses": len(weaknesses_set),
        "total_loot_types": len(loot_set),
        "total_alchemy_recipes": len(recipes)
    })


@app.route("/api/random")
def get_random():
    monsters = load_raw_monsters()
    if not monsters:
        return jsonify({"error": "No monsters found"}), 404
    return jsonify(random.choice(monsters))


if __name__ == "__main__":
    print("⚔️ Launching Witcher 3 Bestiary Dashboard on http://127.0.0.1:5000 ...")
    app.run(host="127.0.0.1", port=5000, debug=True)

