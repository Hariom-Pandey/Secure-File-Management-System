import os
import sys

# Ensure repository root and project folder are in python search path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
PROJECT_DIR = os.path.join(ROOT_DIR, "project")

if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)
if ROOT_DIR not in sys.path:
    sys.path.insert(1, ROOT_DIR)

from project.main import create_app

app = create_app()

if __name__ == "__main__":
    app.run()
