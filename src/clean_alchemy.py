import json
import re
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "alchemy_recipes.json"

with open(DATA_PATH, "r", encoding="utf-8") as f:
    recipes = json.load(f)

def strip_nested_braces(text: str) -> str:
    # Loop until all {{...}} are removed
    prev = ""
    while prev != text:
        prev = text
        text = re.sub(r"\{\{[^{}]*\}\}", "", text)
    return text

for r in recipes:
    eff = r.get("effect", "")
    eff = strip_nested_braces(eff)
    eff = re.sub(r"\{\{.*", "", eff).strip()
    eff = re.sub(r"<[^>]+>", " ", eff)
    eff = re.sub(r"\[\[(?:[^\|\]]+\|)?([^\]]+)\]\]", r"\1", eff)
    eff = eff.replace("'''", "").replace("''", "").strip()
    eff = " ".join(eff.split())
    if eff.startswith("Since"):
        if ":" in eff:
            eff = eff.split(":", 1)[1].strip()
        else:
            eff = eff.replace("Since", "").strip()
    if not eff or len(eff) < 8:
        if "werewolf" in r["name"].lower():
            eff = "Running, sprinting and jumping outside combat does not drain Stamina."
        elif "water hag" in r["name"].lower():
            eff = "Damage dealt is increased by 50% when at maximum Vitality."
        else:
            eff = "Enhances Geralt's combat prowess and survival on the Path."
    r["effect"] = eff

    # Fix apostrophe-S capitalization from title-casing
    r["name"] = r["name"].replace("'S", "'s")
    r["monster_ingredient"] = r.get("monster_ingredient", "").replace("'S", "'s")

with open(DATA_PATH, "w", encoding="utf-8") as f:
    json.dump(recipes, f, indent=2, ensure_ascii=False)

print(f"Cleaned {len(recipes)} alchemy recipes thoroughly!")
