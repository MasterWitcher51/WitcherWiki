from dataclasses import dataclass
import json
from pathlib import Path

DATA_PATH = "../data/monsters.json"

# Create monster dataclass with attributes from JSON 
@dataclass
class Monster():
    Name: str
    Class: str
    Location: list
    Weaknesses: list
    Loot: list

    def __str__(self):
        """Nicely format the monster when printed."""
        return (
            f"Name: {self.Name}\n"
            f"Class: {self.Class}\n"
            f"Location: {', '.join(self.Location) if self.Location else 'Unknown'}\n"
            f"Weaknesses: {', '.join(self.Weaknesses) if self.Weaknesses else 'Unknown'}\n"
            f"Loot: {', '.join(self.Loot) if self.Loot else 'Unknown'}\n"
        )

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

if __name__ == "__main__":
    monsters = load_monsters()
    print(f"Loaded {len(monsters)} monsters.\n")

    for monster in monsters:
        print(monster)

        

