"""Private content-addressed store. Never mount this directory under a web root."""
import hashlib
import math
import os
import re
import tempfile
import threading
import time
from contextlib import contextmanager
from pathlib import Path

_states = {}
_states_guard = threading.Lock()


class LockState:
    def __init__(self):
        self.lock = threading.RLock()
        self.depth = 0


class StorageError(Exception):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


@contextmanager
def thread_lock(state, deadline):
    remaining=max(0,deadline-time.monotonic())
    if not state.lock.acquire(timeout=remaining):
        raise StorageError('raw_lock_timeout')
    try:
        yield
    finally:
        state.lock.release()


class RawStore:
    def __init__(self, root: str | Path, max_bytes=8*1024*1024):
        if type(max_bytes) is not int or not 1 <= max_bytes <= 8*1024*1024:
            raise ValueError('invalid_storage_limit')
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.max_bytes = max_bytes
        with _states_guard:
            self._lock_state = _states.setdefault(os.path.normcase(str(self.root)),LockState())

    @contextmanager
    def locked(self, timeout=10):
        if not isinstance(timeout,(int,float)) or not math.isfinite(timeout) or timeout<0:
            raise ValueError('invalid_lock_timeout')
        deadline=time.monotonic()+timeout
        state = self._lock_state
        with thread_lock(state,deadline):
            if state.depth:
                state.depth += 1
                try:
                    yield
                finally:
                    state.depth -= 1
                return
            path = self.root/'.store.lock'
            if path.is_symlink():
                raise StorageError('unsafe_storage_path')
            descriptor = os.open(path,os.O_RDWR|os.O_CREAT|getattr(os,'O_NOFOLLOW',0),0o600)
            acquired = False
            try:
                if os.fstat(descriptor).st_size == 0:
                    os.write(descriptor,b'0')
                while True:
                    try:
                        os.lseek(descriptor,0,os.SEEK_SET)
                        if os.name == 'nt':
                            import msvcrt
                            msvcrt.locking(descriptor,msvcrt.LK_NBLCK,1)
                        else:
                            import fcntl
                            fcntl.flock(descriptor,fcntl.LOCK_EX|fcntl.LOCK_NB)
                        acquired = True
                        break
                    except OSError:
                        if time.monotonic()>=deadline:
                            raise StorageError('raw_lock_timeout') from None
                        time.sleep(min(0.02,max(0,deadline-time.monotonic())))
                state.depth = 1
                try:
                    yield
                finally:
                    state.depth = 0
            finally:
                try:
                    if acquired:
                        if os.name == 'nt':
                            import msvcrt
                            os.lseek(descriptor,0,os.SEEK_SET)
                            msvcrt.locking(descriptor,msvcrt.LK_UNLCK,1)
                        else:
                            import fcntl
                            fcntl.flock(descriptor,fcntl.LOCK_UN)
                finally:
                    os.close(descriptor)

    def _path(self, digest):
        if not isinstance(digest,str) or not re.fullmatch(r'[a-f0-9]{64}',digest):
            raise StorageError('invalid_digest')
        target = self.root / digest
        if target.is_symlink() or target.resolve().parent != self.root:
            raise StorageError('unsafe_storage_path')
        return target

    def read(self, digest) -> bytes:
        with self.locked():
            return self._read(digest)

    def _read(self, digest) -> bytes:
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
        with self.locked():
            return self._put(body,expected_hash)

    def _put(self, body: bytes, expected_hash: str | None = None) -> str:
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
