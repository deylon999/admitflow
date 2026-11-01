"""Idempotent manual mutations, executed under the owner's transaction lock."""
import hashlib
import json
import re
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import func, select, update

from .database import OperationRecord


def begin_operation(request, body, owner_hash, db):
    key = request.headers.get('Idempotency-Key')
    if key is None:
        return None, None, None
    if not re.fullmatch(r'[A-Za-z0-9._:-]{8,100}', key):
        raise HTTPException(400, 'Некорректный ключ операции.')
    payload = json.dumps(body.model_dump(mode='json', by_alias=True), sort_keys=True, separators=(',', ':'), ensure_ascii=False)
    fingerprint = hashlib.sha256(f'{request.method} {request.url.path}\n{payload}'.encode()).hexdigest()
    existing = db.get(OperationRecord, (owner_hash, key))
    if existing:
        if existing.fingerprint != fingerprint:
            raise HTTPException(409, 'Ключ операции уже использован для других данных.')
        if existing.response_status == 410:
            raise HTTPException(410, 'Направление уже удалено. Начните новое сохранение.')
        return key, fingerprint, existing.response
    count = db.scalar(select(func.count()).select_from(OperationRecord).where(OperationRecord.owner_hash == owner_hash))
    if count >= 12000:
        raise HTTPException(409, 'Достигнут лимит операций гостевой сессии.')
    return key, fingerprint, None


def remember_operation(db, owner_hash, key, fingerprint, watch_id, response):
    if key is not None:
        db.add(OperationRecord(owner_hash=owner_hash, key=key, fingerprint=fingerprint,
                               watch_id=watch_id, response=response.model_dump(mode='json', by_alias=True),
                               response_status=201, created_at=datetime.now(timezone.utc)))


def retire_operations(db, watch_id):
    # Preserve only the key/fingerprint tombstone; delete all saved response data.
    db.execute(update(OperationRecord).where(OperationRecord.watch_id == watch_id)
               .values(watch_id=None, response=None, response_status=410))
