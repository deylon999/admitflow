"""Run or import the canonical module behind an existing scripts/ path."""
from importlib import import_module
from pathlib import Path
from runpy import run_module
import sys


def forward(name, target):
    root = str(Path(__file__).resolve().parents[1])
    if root not in sys.path:
        sys.path.insert(0, root)
    if name == "__main__":
        run_module(target, run_name="__main__", alter_sys=True)
    else:
        sys.modules[name] = import_module(target)
