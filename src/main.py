import sys
from pathlib import Path

# Ensure src directory is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from cli import main_menu

if __name__ == "__main__":
    main_menu()