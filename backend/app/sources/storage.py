"""Private content-addressed store. Never mount this directory under a web root."""
import hashlib
import os
import re
import tempfile
from pathlib import Path


class StorageError(Exception):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


class RawStore:
    def __init__(self, root: str | Path, max_bytes=5*1024*1024):
        if max_bytes < 1:
            raise ValueError('invalid_storage_limit')
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.max_bytes = max_bytes

    def _path(self, digest):
        if not isinstance(digest,str) or not re.fullmatch(r'[a-f0-9]{64}',digest):
            raise StorageError('invalid_digest')
        target = self.root / digest
        if target.is_symlink() or target.resolve().parent != self.root:
            raise StorageError('unsafe_storage_path')
        return target

    def read(self, digest) -> bytes:
        target = self._path(digest)
        try:
            flags = os.O_RDONLY | getattr(os,'O_NOFOLLOW',0) | getattr(os,'O_BINARY',0)
            with os.fdopen(os.open(target,flags),'rb') as file:
                body = file.read(self.max_bytes+1)
        except OSError:
            raise StorageError('raw_unavailable') from None
        if not body or len(body) > self.max_bytes:
            raise StorageError('raw_size_invalid')
        if hashlib.sha256(body).hexdigest() != digest:
            raise StorageError('raw_hash_mismatch')
        return body

    def put(self, body: bytes, expected_hash: str | None = None) -> str:
        if not isinstance(body,bytes) or not body or len(body) > self.max_bytes:
            raise StorageError('raw_size_invalid')
        digest = hashlib.sha256(body).hexdigest()
        if expected_hash is not None and expected_hash != digest:
            raise StorageError('raw_hash_mismatch')
        target = self._path(digest)
        if target.exists():
            self.read(digest)
            return digest
        name = None
        try:
            with tempfile.NamedTemporaryFile(dir=self.root,prefix='.writing-',delete=False) as file:
                name = Path(file.name)
                file.write(body)
                file.flush()
                os.fsync(file.fileno())
            try:
                # No partial target and no overwrite, even with concurrent writers.
                os.link(name,target)
            except FileExistsError:
                self.read(digest)
            return digest
        except OSError:
            raise StorageError('raw_write_failed') from None
        finally:
            if name is not None:
                name.unlink(missing_ok=True)
