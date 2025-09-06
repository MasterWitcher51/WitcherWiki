from dataclasses import dataclass
import json
from pathlib import Path

DATA_PATH = Path("data/monsters.json")

# Create monster dataclass with attributes from JSON 
@dataclass
class Monster():
    Name: str
    Class: str
    Location: list
    Weaknesses: list
    Loot: list


def load_monsters():
    with open(DATA_PATH, 'r') as file:
        data = json.load(file)
    monsters = []
    for m in data:
        monster_info = Monster(
            Name = m.get("Name", "Unknown"),
            Class = m.get("Class", "Unknown"),
            Location = m.get("Location", []),
            Weaknesses = m.get("Weaknesses", []),
            Loot = m.get("Loot", [])

        )
        monsters.append(monster_info)
    return monsters

def main():
    monsters = load_monsters()
    print(f"Loaded {len(monsters)} monsters.\n")
    
    # Example: List all monsters
    for m in monsters:
        print(m)

if __name__ == "__main__":
    main()
        

