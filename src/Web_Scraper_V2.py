import requests
from bs4 import BeautifulSoup
import json
import time
from pathlib import Path

BASE_URL = "https://thewitcher3.wiki.fextralife.com"
START_URL = f"{BASE_URL}/Creatures+and+Monsters"
DATA_PATH = Path("data/monsters.json")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/116.0.0.0 Safari/537.36"
}

# -----------------------------
# Helpers
# -----------------------------
def clean_text(text):
    """Strip whitespace and remove excess newlines."""
    return " ".join(text.split()) if text else ""

def split_items(text):
    """Split comma or newline-separated strings into a list."""
    if not text:
        return []
    return [clean_text(item) for item in text.replace("\n", ",").split(",") if item.strip()]

# -----------------------------
# Step 1: Get all monster links
# -----------------------------
def get_all_monster_links():
    print(f"Scraping main page: {START_URL}")
    res = requests.get(START_URL, headers=HEADERS)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")

    content_div = soup.find_all("div", class_="col-sm-6")
    monster_links_div = content_div[1]  # pick the second one
    links = []
    for a in monster_links_div.find_all("a", class_="wiki_link"):
        name = a.get("title")
        href = a.get("href")
        if name and href:
            links.append({"name": name, "url": BASE_URL + href})
    print(f"Found {len(links)} monster links")
    print(links)
    return links


if __name__ == "__main__":
    get_all_monster_links()