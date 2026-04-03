import sys
from pathlib import Path


def _bootstrap():
    tools_dir = Path(__file__).resolve().parent
    if str(tools_dir) not in sys.path:
        sys.path.insert(0, str(tools_dir))


def main():
    _bootstrap()
    from sie_autoppt.cli import main as real_main

    real_main()


if __name__ == "__main__":
    main()
