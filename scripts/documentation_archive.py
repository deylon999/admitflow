"""Access pinned documentation and data that are no longer in the checkout."""

from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE_REF = '6fdafc999606b486b200a8eac68d732dfd0a956e'
ARCHIVE_URL = f'https://github.com/deylon999/admitflow/blob/{ARCHIVE_REF}'


def archive_git(*args):
    try:
        return subprocess.check_output(['git', *args], cwd=ROOT, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError as error:
        raise ValueError(f'Cannot read documentation archive; run git fetch origin {ARCHIVE_REF}') from error


def read_input(path, archived_path):
    """Read a supplied or regenerated input, falling back only for the default."""
    if path == ROOT / archived_path and not path.exists():
        return archive_git('show', f'{ARCHIVE_REF}:{archived_path}')
    return path.read_bytes()
