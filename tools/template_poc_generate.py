"""
Backward-compatible entrypoint.

This file is intentionally kept as a thin wrapper so older commands still work:
python tools/template_poc_generate.py ...
"""

import sys
from pathlib import Path


def main():
    tools_dir = Path(__file__).resolve().parent
    if str(tools_dir) not in sys.path:
        sys.path.insert(0, str(tools_dir))
    from sie_autoppt.cli import main as real_main

    real_main()


if __name__ == "__main__":
    main()
