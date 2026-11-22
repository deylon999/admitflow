"""Access pinned documentation and data that are no longer in the checkout."""

from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE_REF = '6fdafc999606b486b200a8eac68d732dfd0a956e'
PR4_ARCHIVE_REF = 'a54ed718d7fb944c3bb64dc82fd9d3779750a634'
ARCHIVE_REFS = (ARCHIVE_REF, PR4_ARCHIVE_REF)
GITHUB_BLOB_URL = 'https://github.com/deylon999/admitflow/blob'


def archive_git(*args):
    try:
        return subprocess.check_output(['git', *args], cwd=ROOT, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError as error:
        refs = ' '.join(ARCHIVE_REFS)
        raise ValueError(f'Cannot read documentation archive; run git fetch origin {refs}') from error


def read_input(path, archived_path):
    """Read a supplied or regenerated input, falling back only for the default."""
    if path == ROOT / archived_path and not path.exists():
        return archive_git('show', f'{ARCHIVE_REF}:{archived_path}')
    return path.read_bytes()
