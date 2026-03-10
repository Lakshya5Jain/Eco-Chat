"""Entry point so `uv run econ-chat` launches the Streamlit app."""

import subprocess
import sys
from pathlib import Path


def main():
    app_path = Path(__file__).parent / "app.py"
    sys.exit(subprocess.run(["streamlit", "run", str(app_path)]).returncode)


if __name__ == "__main__":
    main()
