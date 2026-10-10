import sys
import random
from pathlib import Path

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt
from rich import box

from bestiary import load_monsters, Monster

console = Console()
monsters = load_monsters()


def highlight_weakness(w: str) -> str:
    """Applies thematic colors to Signs, Oils, and Bombs."""
    wl = w.lower()
    if "igni" in wl:
        return f"[bold orange3]{w}[/bold orange3]"
    elif "quen" in wl:
        return f"[bold yellow]{w}[/bold yellow]"
    elif "aard" in wl:
        return f"[bold cyan]{w}[/bold cyan]"
    elif "axii" in wl:
        return f"[bold bright_blue]{w}[/bold bright_blue]"
    elif "yrden" in wl:
        return f"[bold magenta]{w}[/bold magenta]"
    elif "oil" in wl:
        return f"[bold green]{w}[/bold green]"
    elif any(b in wl for b in ["bomb", "wind", "dust", "puffball", "dimeritium"]):
        return f"[bold red]{w}[/bold red]"
    elif "silver" in wl:
        return f"[bold white]{w}[/bold white]"
    return f"[white]{w}[/white]"


def display_monster_card(m: Monster):
    """Renders an atmospheric Witcher-themed card for a monster."""
    grid = Table.grid(padding=(0, 2))
    grid.add_column(style="bold yellow", justify="right", min_width=12)
    grid.add_column()

    grid.add_row("Class:", f"[bold cyan]{m.Class or 'Unknown'}[/bold cyan]")
    
    locations = ", ".join(m.Location) if m.Location else "Unknown"
    grid.add_row("Location:", f"[italic dim]{locations}[/italic dim]")

    if m.Weaknesses:
        weaknesses_str = ", ".join(highlight_weakness(w) for w in m.Weaknesses)
    else:
        weaknesses_str = "[dim]None known[/dim]"
    grid.add_row("Weaknesses:", weaknesses_str)

    if m.Loot:
        loot_str = ", ".join(f"[bold gold1]{item}[/bold gold1]" for item in m.Loot)
    else:
        loot_str = "[dim]None[/dim]"
    grid.add_row("Loot Drops:", loot_str)

    panel = Panel(
        grid,
        title=f"[bold white on red] {m.Name} [/bold white on red]",
        subtitle=f"[dim]Class: {m.Class}[/dim]",
        border_style="red",
        box=box.ROUNDED,
        padding=(1, 2)
    )
    console.print(panel)


def list_all_monsters():
    """Displays all monsters in an organized multi-column table."""
    table = Table(
        title=f"[bold gold1]The Witcher 3 Bestiary ({len(monsters)} Monsters)[/bold gold1]",
        box=box.ROUNDED,
        border_style="dim white",
        header_style="bold red"
    )
    table.add_column("#", justify="right", style="dim", width=4)
    table.add_column("Monster Name", style="bold white", min_width=25)
    table.add_column("Class", style="cyan", min_width=16)
    table.add_column("Weaknesses Preview", style="dim", max_width=40)

    for idx, m in enumerate(sorted(monsters, key=lambda x: x.Name), 1):
        weak_preview = ", ".join(m.Weaknesses[:3])
        if len(m.Weaknesses) > 3:
            weak_preview += f" (+{len(m.Weaknesses) - 3})"
        table.add_row(str(idx), m.Name, m.Class or "Unknown", weak_preview or "None")

    console.print(table)


def show_details():
    """Finds and shows detailed cards with case-insensitive and partial matching."""
    query = Prompt.ask("\n[bold yellow]Enter monster name[/bold yellow]").strip()
    if not query:
        return

    matches = [m for m in monsters if query.lower() in m.Name.lower()]

    if not matches:
        console.print(f"[bold red]No monsters found matching '{query}'.[/bold red]\n")
        return

    console.print(f"\n[green]Found {len(matches)} matching monster(s):[/green]")
    for m in matches:
        display_monster_card(m)


def search_by_class():
    """Displays available classes and lists monsters belonging to that class."""
    classes = sorted({m.Class for m in monsters if m.Class and m.Class != "Unknown"})
    
    console.print("\n[bold yellow]Available Classes:[/bold yellow]")
    class_grid = Table.grid(padding=(0, 2))
    class_grid.add_column(style="cyan")
    # Display in lines of 4
    for i in range(0, len(classes), 4):
        batch = classes[i:i+4]
        console.print("  " + "   •   ".join(f"[bold cyan]{c}[/bold cyan]" for c in batch))

    query = Prompt.ask("\n[bold yellow]Enter class name[/bold yellow]").strip()
    if not query:
        return

    matches = [m for m in monsters if query.lower() in m.Class.lower()]

    if not matches:
        console.print(f"[bold red]No monsters found in class '{query}'.[/bold red]\n")
        return

    table = Table(
        title=f"[bold gold1]Monsters in Class: {query.title()} ({len(matches)})[/bold gold1]",
        box=box.ROUNDED,
        border_style="cyan",
        header_style="bold cyan"
    )
    table.add_column("Monster Name", style="bold white", min_width=25)
    table.add_column("Locations", style="dim", min_width=25)
    table.add_column("Weaknesses", min_width=30)

    for m in matches:
        w_str = ", ".join(highlight_weakness(w) for w in m.Weaknesses[:3])
        loc_str = ", ".join(m.Location[:2]) or "Unknown"
        table.add_row(m.Name, loc_str, w_str)

    console.print(table)


def search_by_loot():
    """Searches for monsters that drop a specific item."""
    query = Prompt.ask("\n[bold yellow]Enter loot name (e.g. mutagen, liver, hide)[/bold yellow]").strip()
    if not query:
        return

    matches = [
        (m, [item for item in m.Loot if query.lower() in item.lower()])
        for m in monsters
        if any(query.lower() in item.lower() for item in m.Loot)
    ]

    if not matches:
        console.print(f"[bold red]No monsters drop loot matching '{query}'.[/bold red]\n")
        return

    table = Table(
        title=f"[bold gold1]Monsters dropping '{query}' ({len(matches)})[/bold gold1]",
        box=box.ROUNDED,
        border_style="yellow",
        header_style="bold gold1"
    )
    table.add_column("Monster Name", style="bold white", min_width=24)
    table.add_column("Class", style="cyan", min_width=16)
    table.add_column("Matching Drops", style="bold yellow")

    for m, matching_items in matches:
        table.add_row(m.Name, m.Class, ", ".join(matching_items))

    console.print(table)


def search_by_weakness():
    """Searches for monsters weak to a specific Sign, Oil, or Bomb."""
    query = Prompt.ask("\n[bold yellow]Enter weakness (e.g. Igni, Quen, Necrophage oil, Northern wind)[/bold yellow]").strip()
    if not query:
        return

    matches = [
        (m, [w for w in m.Weaknesses if query.lower() in w.lower()])
        for m in monsters
        if any(query.lower() in w.lower() for w in m.Weaknesses)
    ]

    if not matches:
        console.print(f"[bold red]No monsters found weak to '{query}'.[/bold red]\n")
        return

    table = Table(
        title=f"[bold gold1]Monsters weak to '{query}' ({len(matches)})[/bold gold1]",
        box=box.ROUNDED,
        border_style="red",
        header_style="bold red"
    )
    table.add_column("Monster Name", style="bold white", min_width=24)
    table.add_column("Class", style="cyan", min_width=16)
    table.add_column("Matching Weakness", style="bold")

    for m, matching_weak in matches:
        w_highlighted = ", ".join(highlight_weakness(w) for w in matching_weak)
        table.add_row(m.Name, m.Class, w_highlighted)

    console.print(table)


def random_encounter():
    """Picks a random monster from the bestiary for a Witcher quiz or preparation."""
    m = random.choice(monsters)
    console.print("\n[bold red]*** SURPRISE ENCOUNTER ON THE PATH ***[/bold red]")
    display_monster_card(m)


def print_banner():
    banner = (
        "[bold red] _    _ _ _       _               [/bold red][bold white]____  [/bold white]\n"
        "[bold red]| |  | (_) |     | |             [/bold red][bold white]|___ \\ [/bold white]\n"
        "[bold red]| |  | |_| |_ ___| |__   ___ _ __  [/bold red][bold white]__) |[/bold white]\n"
        "[bold red]| |/\\| | | __/ __| '_ \\ / _ \\ '__|[/bold red][bold white]|__ < [/bold white]\n"
        "[bold red]\\  /\\  / | || (__| | | |  __/ |   [/bold red][bold white]___) |[/bold white]\n"
        "[bold red] \\/  \\/|_|\\__\\___|_| |_|\\___|_|  [/bold red][bold white]|____/ [/bold white]\n"
        "\n"
        "[bold gold1]  ⚔  THE WITCHER 3 : BESTIARY COMPENDIUM  ⚔[/bold gold1]\n"
        "[italic dim]    \"Knowledge is the Witcher's finest blade.\"[/italic dim]"
    )
    console.print(Panel(banner, border_style="red", box=box.DOUBLE, padding=(0, 2)))




def main_menu():
    print_banner()

    while True:
        menu_table = Table.grid(padding=(0, 2))
        menu_table.add_column(style="bold yellow", justify="right")
        menu_table.add_column(style="bold white")

        menu_table.add_row("[1]", "List all monsters")
        menu_table.add_row("[2]", "Show monster details")
        menu_table.add_row("[3]", "Search by class")
        menu_table.add_row("[4]", "Search by loot drop")
        menu_table.add_row("[5]", "Search by weakness (Sign / Oil / Bomb)")
        menu_table.add_row("[6]", "Random encounter")
        menu_table.add_row("[7]", "Exit")

        console.print(Panel(menu_table, title="[bold gold1]Main Menu[/bold gold1]", border_style="dim white", box=box.ROUNDED))

        choice = Prompt.ask("[bold red]Select an option[/bold red]", choices=["1", "2", "3", "4", "5", "6", "7"], default="1")

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
            random_encounter()
        elif choice == "7":
            console.print("\n[bold yellow]Safe travels on the Path. Farewell, Witcher![/bold yellow]\n")
            break


if __name__ == "__main__":
    main_menu()
