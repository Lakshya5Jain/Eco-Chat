"""Entry point so `uv run econ-chat` launches the Streamlit app."""

import subprocess
import sys
from pathlib import Path


def main():
    project_root = Path(__file__).resolve().parent.parent
    app_path = Path(__file__).parent / "app.py"
    sys.exit(
        subprocess.run(
            ["streamlit", "run", str(app_path)],
            cwd=str(project_root),
        ).returncode
    )


if __name__ == "__main__":
    main()
