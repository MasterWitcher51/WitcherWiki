"""
Fetch Witcher 3 Alchemy Recipes (Decoctions, Oils, Potions) from Fandom MediaWiki API
and link each recipe to the corresponding monsters in data/monsters.json.
"""

import json
import re
import time
from pathlib import Path
import requests

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
MONSTERS_PATH = DATA_DIR / "monsters.json"
RECIPES_PATH = DATA_DIR / "alchemy_recipes.json"

FANDOM_API = "https://witcher.fandom.com/api.php"
HEADERS = {"User-Agent": "WitcherWikiBot/1.0 (contact: student@witcherwiki.local)"}


def clean_wikitext(text: str) -> str:
    if not text:
        return ""
    # Remove templates {{...}}
    cleaned = re.sub(r"\{\{[^}]+\}\}", "", text)
    # Convert [[link|label]] or [[label]] to label
    cleaned = re.sub(r"\[\[(?:[^\|\]]+\|)?([^\]]+)\]\]", r"\1", cleaned)
    # Remove HTML tags
    cleaned = re.sub(r"<[^>]+>", " ", cleaned)
    # Clean whitespace
    return " ".join(cleaned.split())


def get_page_wikitext(title: str) -> str:
    params = {
        "action": "parse",
        "page": title,
        "prop": "wikitext",
        "format": "json",
        "redirects": 1
    }
    try:
        res = requests.get(FANDOM_API, params=params, headers=HEADERS, timeout=8)
        if res.status_code == 200:
            data = res.json()
            return data.get("parse", {}).get("wikitext", {}).get("*", "")
    except Exception as e:
        print(f"Error fetching {title}: {e}")
    return ""


def parse_recipe_from_wikitext(title: str, wikitext: str, monsters: list) -> dict:
    if not wikitext:
        return None

    # Name
    name_m = re.search(r"\|name\s*=\s*(.*?)(?=\n\s*\||\}\})", wikitext, re.I)
    name = clean_wikitext(name_m.group(1)) if name_m else title

    # Type
    type_m = re.search(r"\|type\s*=\s*(.*?)(?=\n\s*\||\}\})", wikitext, re.I)
    raw_type = clean_wikitext(type_m.group(1)).lower() if type_m else ""
    if "decoction" in name.lower() or "decoction" in raw_type:
        recipe_type = "Decoction"
    elif "oil" in name.lower() or "oil" in raw_type:
        recipe_type = "Blade Oil"
    else:
        recipe_type = "Potion"

    # Effects
    effects_m = re.search(r"\|effects\s*=\s*(.*?)(?=\n\s*\||\}\})", wikitext, re.I)
    effects = clean_wikitext(effects_m.group(1)) if effects_m else "Enhances Witcher combat abilities."

    # Toxicity
    tox_m = re.search(r"\|toxicity\s*=\s*(\d+)", wikitext, re.I)
    toxicity = int(tox_m.group(1)) if tox_m else (70 if recipe_type == "Decoction" else 20 if recipe_type == "Potion" else 0)

    # Ingredients
    ingr_m = re.search(r"\|alchemy_ingredients\s*=\s*(.*?)(?=\n\s*\||\}\})", wikitext, re.DOTALL | re.I)
    ingredients_list = []
    monster_ingredient = ""

    if ingr_m:
        raw_ingr = ingr_m.group(1)
        # Find all linked ingredients
        items = re.findall(r"\[\[(?:[^\|\]]+\|)?([^\]]+)\]\]", raw_ingr)
        ingredients_list = items

        # Identify monster ingredient (mutagen, liver, saliva, eye, feather, tooth, heart, blood, venom, etc.)
        monster_keywords = [
            "mutagen", "liver", "saliva", "eye", "feather", "tooth", "teeth", "heart",
            "blood", "venom", "marrow", "ear", "tongue", "gland", "stomach", "pelt", "hide", "fat", "tissue"
        ]
        for item in items:
            if any(k in item.lower() for k in monster_keywords) and not any(k in item.lower() for k in ["white", "arenaria", "celandine"]):
                monster_ingredient = item
                break

    # If monster ingredient not found from ingredients list, try name heuristic
    if not monster_ingredient and recipe_type == "Decoction":
        base_name = name.replace(" decoction", "").replace("Decoction", "").strip()
        monster_ingredient = f"{base_name} mutagen"

    # Match target monsters from our monsters database
    target_monsters = []
    if monster_ingredient:
        ingr_lower = monster_ingredient.lower()
        # Find monsters that drop this item
        for m in monsters:
            m_loot = [loot_item.lower() for loot_item in m.get("Loot", [])]
            m_name = m.get("Name", "").lower()
            
            # Direct loot match or name match
            if any(ingr_lower in item or item in ingr_lower for item in m_loot):
                target_monsters.append(m.get("Name"))
            elif any(part in m_name for part in monster_ingredient.lower().split() if len(part) > 4):
                if m.get("Name") not in target_monsters:
                    target_monsters.append(m.get("Name"))

    return {
        "name": name.title(),
        "type": recipe_type,
        "effect": effects,
        "toxicity": toxicity,
        "monster_ingredient": monster_ingredient or "Monster Remains",
        "all_ingredients": ingredients_list,
        "target_monsters": target_monsters[:5]  # top matching monsters
    }


def fetch_all_recipes():
    with open(MONSTERS_PATH, "r", encoding="utf-8") as f:
        monsters = json.load(f)

    print("Fetching template lists from Witcher Wiki...")
    # Decoctions
    potions_template = get_page_wikitext("Template:Tw3_potions_and_decoctions")
    decoctions = re.findall(r"\[\[([^\]\|]+decoction)\]\]", potions_template, re.I)
    
    # Specific standard potions
    core_potions = [
        "Swallow", "Thunderbolt", "Tawny Owl", "Cat (potion)", "White Raffard's Decoction",
        "Black Blood", "Golden Oriole", "Blizzard", "Maribor Forest (potion)", "Petri's Philter"
    ]

    # Oils
    oils_template = get_page_wikitext("Template:Tw3_oils")
    oils = re.findall(r"\[\[([^\]\|]+(?:oil|Hanged Man's Venom))\]\]", oils_template, re.I)

    # Combine unique titles
    all_titles = []
    for d in decoctions:
        if d not in all_titles:
            all_titles.append(d)
    for p in core_potions:
        if p not in all_titles:
            all_titles.append(p)
    for o in oils:
        if o not in all_titles and "enhanced" not in o.lower() and "superior" not in o.lower():
            # Add base and superior
            all_titles.append(o)
            all_titles.append(f"Superior {o.lower()}")

    print(f"Total alchemy pages to process: {len(all_titles)}")
    recipes = []
    seen_names = set()

    for idx, title in enumerate(all_titles, 1):
        print(f"[{idx}/{len(all_titles)}] Processing: {title}")
        wt = get_page_wikitext(title)
        if not wt:
            continue
        recipe = parse_recipe_from_wikitext(title, wt, monsters)
        if recipe and recipe["name"] not in seen_names:
            seen_names.add(recipe["name"])
            recipes.append(recipe)
        time.sleep(0.15)

    print(f"\nSuccessfully parsed {len(recipes)} alchemy recipes!")
    with open(RECIPES_PATH, "w", encoding="utf-8") as f:
        json.dump(recipes, f, indent=2, ensure_ascii=False)
    print(f"Saved to {RECIPES_PATH}")


if __name__ == "__main__":
    fetch_all_recipes()
