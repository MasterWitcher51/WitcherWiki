from bestiary import load_monsters, Monster

monsters = load_monsters()


def list_all_monsters():
    """Lists all monster names sorted alphabetically."""
    print("\n=== Monster List ===")
    for m in sorted(monsters, key=lambda x: x.Name):
        print(f" • {m.Name}")
    print(f"==================== (Total: {len(monsters)})\n")


def show_details():
    """Finds and shows monster details with case-insensitive and partial matching."""
    choice = input("\nEnter a monster name: ").strip().lower()
    matches = [m for m in monsters if choice in m.Name.lower()]

    if not matches:
        print(f"No monster found matching '{choice}'.\n")
        return

    print("\n=== Monster Info ===")
    for m in matches:
        print(m)
        print("-" * 25)
    print()


def search_by_class():
    """Displays available classes and filters monsters by class."""
    # Collect all unique classes
    classes = sorted({m.Class for m in monsters if m.Class and m.Class != "Unknown"})
    print("\nAvailable classes:")
    print(", ".join(classes))

    choice = input("\nEnter a class: ").strip().lower()
    matches = [m for m in monsters if choice in m.Class.lower()]

    if not matches:
        print(f"No monsters found in class '{choice}'.\n")
        return

    print(f"\n=== Monsters in class '{choice.title()}' ===")
    for m in matches:
        print(f" • {m.Name}")
    print()


def search_by_loot():
    """Lists monsters that drop a specific item (supports partial names like 'mutagen')."""
    choice = input("\nEnter a loot item (e.g., 'mutagen', 'claw'): ").strip().lower()
    matches = [
        (m, [item for item in m.Loot if choice in item.lower()])
        for m in monsters
        if any(choice in item.lower() for item in m.Loot)
    ]

    if not matches:
        print(f"No monsters drop loot matching '{choice}'.\n")
        return

    print(f"\n=== Monsters dropping '{choice}' ===")
    for m, matching_items in matches:
        print(f" • {m.Name} (Drops: {', '.join(matching_items)})")
    print()


def search_by_weakness():
    """Lists monsters weak to a specific Sign, Oil, or Bomb (e.g., 'Igni', 'Necrophage oil')."""
    choice = input("\nEnter a weakness (e.g., 'Igni', 'Quen', 'oil', 'bomb'): ").strip().lower()
    matches = [
        (m, [w for w in m.Weaknesses if choice in w.lower()])
        for m in monsters
        if any(choice in w.lower() for w in m.Weaknesses)
    ]

    if not matches:
        print(f"No monsters found weak to '{choice}'.\n")
        return

    print(f"\n=== Monsters weak to '{choice}' ===")
    for m, matching_weaknesses in matches:
        print(f" • {m.Name} ({', '.join(matching_weaknesses)})")
    print()


def main_menu():
    while True:
        print("=== Witcher 3 Bestiary ===")
        print("1. List all monsters")
        print("2. Show monster details")
        print("3. Search by class")
        print("4. Search by loot drop")
        print("5. Search by weakness (Sign/Oil/Bomb)")
        print("6. Exit")

        choice = input("\nSelect an option (1-6): ").strip()

        if choice == "1":
            list_all_monsters()
        elif choice == "2":
            show_details()
        elif choice == "3":
            search_by_class()
        elif choice == "4":
            search_by_loot()
        elif choice == "5":
            search_by_weakness()
        elif choice == "6":
            print("\nSafe travels on the Path. Goodbye!\n")
            break
        else:
            print("\nInvalid choice, please select between 1 and 6.\n")


if __name__ == "__main__":
    main_menu()
