import requests
from bs4 import BeautifulSoup
from pathlib import Path
import json
from utils import clean_text, split_items
import time

BASE_URL = "https://thewitcher3.wiki.fextralife.com"
START_URL = f"{BASE_URL}/Creatures+and+Monsters"
DATA_PATH = Path("data/monsters.json")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/116.0.0.0 Safari/537.36"
}


def extract_drops(soup):
    """Extracts monster drops from the page without duplicates."""
    drops = []

    # Find all <li> tags
    for li in soup.find_all("li"):
        strong_tag = li.find("strong")
        if strong_tag and "drops" in strong_tag.text.lower():
            # Extract linked drops
            for a in li.find_all("a", class_="wiki_link"):
                drop_name = a.get_text(strip=True)
                if drop_name not in drops:
                    drops.append(drop_name)
            
            # Extract plain text drops (after removing <strong>Drops</strong> text)
            text = li.get_text(" ", strip=True)
            text = text.replace(strong_tag.get_text(), "").strip()
            # Remove leading colon if exists
            if text.startswith(":"):
                text = text[1:].strip()
            
            # Split by commas and add unique items
            for item in text.split(","):
                item = item.strip()
                if item and item not in drops:
                    drops.append(item)
            break  # stop after first Drops li

    return drops



# -----------------------------
# Step 1: Get all monster links
# -----------------------------
def get_all_monster_links():
    print(f"Scraping main page: {START_URL}")
    res = requests.get(START_URL, headers=HEADERS)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")

    content_divs = soup.find_all("div", class_="col-sm-3")
    links = []
    seen = set()  # to avoid duplicates

    for div in content_divs:
        for a in div.find_all("a", class_="wiki_link"):
            name = a.get("title")
            href = a.get("href")
            if name and href:
                url = BASE_URL + href
                if url not in seen:
                    seen.add(url)
                    links.append({"name": name, "url": url})
                    print(f"  Found link: {name} -> {url}")

    print(f"\nTotal unique monsters found: {len(links)}")
    return links

# -----------------------------
# Step 2: Scrape one monster for info
# -----------------------------
def scrape_monster(url):
    print(f"Scraping monster page: {url}")
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        res.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print(f" Skipped {url} (HTTP error: {e})")
        return None
    except requests.exceptions.RequestException as e:
        print(f" Skipped {url} (Request error: {e})")
        return None
    
    soup = BeautifulSoup(res.text, "html.parser")

    # Name of Monster (strip "| The Witcher 3 Wiki" if present)
    name = clean_text(soup.find("h1").text.split("|")[0])

    # Extract info box table
    info_box = soup.find("div", id="infobox")
    fields = {}

    if info_box:
        table = info_box.find("table", class_="wiki_table")
        if table:
            for row in table.find_all("tr"):
                cells = row.find_all(["th", "td"])
                if len(cells) == 2:
                    key = clean_text(cells[0].get_text())
                    # Use link text if present, else plain text
                    value = ", ".join([a.get_text(strip=True) for a in cells[1].find_all("a")]) \
                            or clean_text(cells[1].get_text())
                    fields[key] = value



    # Build JSON-friendly dictionary
    monster = {
        "Name": name,
        "Class": fields.get("Creature Class", "Unknown"),
        "Location": split_items(fields.get("Locations", "")),
        "Weaknesses": split_items(fields.get("Weaknesses", "")),
        "Loot": extract_drops(soup)
    }

    print(f"  Parsed monster: {name}")
    return monster

def scrape_all_monsters():
    links = get_all_monster_links()
    monsters = []
    
    for i, link in enumerate(links, 1):
        print(f"[{i}/{len(links)}]")
        monster = scrape_monster(link["url"])  
        if monster:
            monsters.append(monster)
        time.sleep(1)  # Be polite to the server
    
    # Save to JSON
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(monsters, f, indent=2, ensure_ascii=False)
    
    print(f"\nSaved {len(monsters)} monsters to {DATA_PATH}")

if __name__ == "__main__":
    scrape_all_monsters()

