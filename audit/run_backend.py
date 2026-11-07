"""Run repository tests from native Linux storage to avoid Windows bind-mount spawn delays."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

source = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='admitflow-audit-') as temporary:
    root = Path(temporary)
    for name in ('backend', 'scripts', 'shared', 'docs'):
        shutil.copytree(source / name, root / name,
                        ignore=shutil.ignore_patterns('.venv', '__pycache__', '.pytest_cache', 'var', '*.db', 'test-results'))
    raise SystemExit(subprocess.run([sys.executable, '-m', 'pytest', *sys.argv[1:]], cwd=root / 'backend').returncode)
