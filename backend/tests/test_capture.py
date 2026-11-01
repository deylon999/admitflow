from dataclasses import replace
import json

import pytest

from app.sources.capture import CaptureError, TARGETS, capture, main, verify
from app.sources.fetcher import FetchError
from source_helpers import raw


def test_capture_preserves_original_bytes_and_does_not_attest(tmp_path):
    response = replace(raw(b'<html>synthetic capture fixture</html>'),url=TARGETS['sgu-2026-4588'],content_type='text/html')
    folder=capture('sgu-2026-4588',tmp_path,fetch=lambda *_:response)
    assert (folder/'response.bin').read_bytes()==response.body
    manifest=verify(folder)
    assert manifest.payload_hash==response.payload_hash and not manifest.attested
    assert manifest.data_kind=='archive'
    assert main(['verify',str(folder)])==0
    (folder/'response.bin').write_bytes(b'corrupt')
    with pytest.raises(CaptureError,match='hash_mismatch'):
        verify(folder)


def test_capture_failure_does_not_leave_success_bundle(tmp_path):
    def denied(*_):
        raise FetchError('access_denied')
    with pytest.raises(FetchError):
        capture('sgu-2026-4588',tmp_path,fetch=denied)
    assert list(tmp_path.iterdir())==[]
    with pytest.raises(CaptureError,match='unknown_capture_target'):
        capture('arbitrary-url',tmp_path)


def test_manifest_tampering_cannot_change_binding_or_claim_attestation(tmp_path):
    response=replace(raw(),url=TARGETS['sgu-2026-4588'])
    folder=capture('sgu-2026-4588',tmp_path,fetch=lambda *_:response)
    path=folder/'manifest.json'
    original=json.loads(path.read_text())
    for changes in [{'attested':True},{'final_url':'https://evil.org/list'},{'source_key':'unknown'},{'payload_bytes':1}]:
        path.write_text(json.dumps(original|changes))
        with pytest.raises(CaptureError):
            verify(folder)
