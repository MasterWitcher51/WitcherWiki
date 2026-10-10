"""
Utility to fill in missing monster loot from the Witcher Wiki (Fandom) API.
Website: https://witcher.fandom.com/wiki/The_Witcher_3_bestiary
"""

import json
import re
import time
from pathlib import Path
import requests

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "monsters.json"
FANDOM_API = "https://witcher.fandom.com/api.php"
HEADERS = {"User-Agent": "WitcherWikiBot/1.0 (contact: student@witcherwiki.local)"}

# Custom name mappings for page titles that differ on Fandom
NAME_ALIASES = {
    "Alps": "Alp",
    "Wight": "Wight_(creature)",
    "Speartip": "Old_Speartip",
    "Giant Centipede": "Giant_centipede",
    "Spotted Wight": "Spotted_wight",
}

# Story bosses / encounters that have no loot drops in The Witcher 3
NO_LOOT_BOSSES = {
    "Caranthir": ["None (Wild Hunt Boss - Cutscene)"],
    "Eredin": ["None (Final Boss - Cutscene)"],
    "Nithral": ["None (Story Boss - Keira Metz quest)"],
    "King of Wolves": ["None (Quest Wolf - Ciri encounter)"],
    "The Toad Prince": ["None (Story Boss - Cutscene)"],
    "Ethereal": ["None (Olgierd Nightmare - Cutscene)"],
    "The Wraith from the Painting": ["None (Iris' Memory Boss)"],
    "Shaelmaar from the emperor of Nilfgaard": ["None (Tourney Arena Boss - Cutscene)"],
    "Speartip": ["None (Sleeping Cyclops - Optional Cave encounter)"],
}


def fetch_fandom_loot(monster_name: str) -> list[str]:
    """Fetches loot drops from Fandom MediaWiki API for a given monster name."""
    search_names = []
    if monster_name in NAME_ALIASES:
        search_names.append(NAME_ALIASES[monster_name])
    search_names.extend([
        monster_name,
        monster_name.replace(" ", "_"),
        monster_name.rstrip("s"),  # singular form
        monster_name.replace("The ", ""),
    ])

    for title in search_names:
        params = {
            "action": "parse",
            "page": title,
            "format": "json",
            "prop": "wikitext",
            "redirects": 1,
        }
        try:
            res = requests.get(FANDOM_API, params=params, headers=HEADERS, timeout=8)
            if res.status_code != 200:
                continue
            data = res.json()
            if "error" in data:
                continue

            wikitext = data.get("parse", {}).get("wikitext", {}).get("*", "")

            # If there's a TW3 specific section, prioritize it
            tw3_idx = wikitext.find("{{Tw3}}")
            search_area = wikitext[tw3_idx:] if tw3_idx != -1 else wikitext

            loot_match = re.search(r"\|loot\s*=\s*(.*?)(?=\n\s*\||\}\})", search_area, re.DOTALL | re.I)
            if not loot_match and tw3_idx != -1:
                loot_match = re.search(r"\|loot\s*=\s*(.*?)(?=\n\s*\||\}\})", wikitext, re.DOTALL | re.I)

            if loot_match:
                raw_loot = loot_match.group(1).strip()
                # Extract [[Item Name]] or [[Link|Item Name]]
                items = re.findall(r"\[\[(?:[^\|\]]+\|)?([^\]]+)\]\]", raw_loot)
                if not items:
                    # Fallback to lines/breaks if no wikilinks
                    items = [
                        re.sub(r"<[^>]+>", "", line).strip()
                        for line in re.split(r"<br\s*/?>|\n", raw_loot)
                        if line.strip() and not line.strip().startswith("{")
                    ]
                # Filter out garbage
                clean_items = [i for i in items if i and not i.startswith("File:") and not i.startswith("Category:")]
                if clean_items:
                    return clean_items
        except Exception:
            continue
        time.sleep(0.15)

    return []


def patch_missing_loot():
    if not DATA_PATH.exists():
        print(f"Error: Could not find {DATA_PATH}")
        return

    with open(DATA_PATH, "r", encoding="utf-8") as f:
        monsters = json.load(f)

    updated_count = 0
    story_boss_count = 0

    for m in monsters:
        name = m.get("Name", "")
        current_loot = m.get("Loot", [])

        # If loot is empty
        if not current_loot:
            print(f"Checking missing loot for: {name}...")
            fandom_loot = fetch_fandom_loot(name)

            if fandom_loot:
                m["Loot"] = fandom_loot
                updated_count += 1
                print(f"  -> Added {len(fandom_loot)} items from Fandom: {', '.join(fandom_loot[:3])}...")
            elif name in NO_LOOT_BOSSES:
                m["Loot"] = NO_LOOT_BOSSES[name]
                story_boss_count += 1
                print(f"  -> Marked story/boss note: {m['Loot'][0]}")
            else:
                print(f"  -> No loot found on Fandom.")
            time.sleep(0.2)

    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(monsters, f, indent=2, ensure_ascii=False)

    print(f"\nDone! Updated {updated_count} monsters with Fandom loot and annotated {story_boss_count} story bosses.")


if __name__ == "__main__":
    patch_missing_loot()
