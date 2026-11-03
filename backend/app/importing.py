"""Import manual exports into the current owner; original IDs never grant access."""
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import func, select

from .calculation import calculate
from .database import Snapshot, Watch
from .schemas import WatchCreate


def stamp(value):
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError('Timezone required')
    return value.astimezone(timezone.utc)


def signature(snapshot):
    return snapshot.model_dump(exclude={'calculation':{'status'}})


def validate_import(bundle,now):
    try:
        if 'format_version' not in bundle.model_fields_set or not bundle.watches:
            raise ValueError()
        exported=stamp(bundle.exported_at)
        if exported>now+timedelta(minutes=5):
            raise ValueError()
        watch_ids=set()
        snapshot_ids=set()
        validated=[]
        for watch in bundle.watches:
            if not watch.id or len(watch.id)>100 or watch.id in watch_ids or not 1<=len(watch.history)<=500:
                raise ValueError()
            watch_ids.add(watch.id)
            cleaned=WatchCreate(university=watch.university,title=watch.title,source_url=watch.source_url,values=watch.latest.values)
            created=stamp(watch.created_at)
            if created.year<2000 or created>exported or signature(watch.latest)!=signature(watch.history[0]):
                raise ValueError()
            previous=None
            for snapshot in watch.history:
                captured=stamp(snapshot.captured_at)
                if snapshot.model_version!='manual-v1' or not snapshot.id or len(snapshot.id)>100 or snapshot.id in snapshot_ids:
                    raise ValueError()
                snapshot_ids.add(snapshot.id)
                key=(captured,snapshot.id)
                if captured<created or captured>exported or captured>now+timedelta(minutes=5) or (previous and key>=previous):
                    raise ValueError()
                previous=key
                supplied=snapshot.calculation.model_dump(exclude={'status'})
                if supplied!=calculate(snapshot.values).model_dump(exclude={'status'}):
                    raise ValueError()
                if not snapshot.calculation.status or len(snapshot.calculation.status)>500:
                    raise ValueError()
            validated.append((watch,cleaned))
        return validated
    except (ValueError,TypeError,ValidationError):
        raise HTTPException(422,'Файл содержит некорректную ручную историю, формулу, дату или ссылку.') from None


def import_bundle(db,owner,bundle,now):
    validated=validate_import(bundle,now)
    from .direction_budget import direction_budget
    existing=direction_budget(db,owner).total
    if existing+len(validated)>20:
        raise HTTPException(409,'После импорта будет больше 20 направлений. Удалите лишние или выберите другую сессию.')
    snapshots=0
    for original,cleaned in validated:
        watch=Watch(owner_hash=owner,university=cleaned.university,title=cleaned.title,source_url=str(cleaned.source_url),created_at=stamp(original.created_at))
        db.add(watch)
        db.flush()
        # Keep input order when timestamps tie, while replacing every external ID.
        ids=sorted((str(uuid4()) for _ in original.history),reverse=True)
        db.add_all([Snapshot(id=id,watch_id=watch.id,captured_at=stamp(snapshot.captured_at),**snapshot.values.model_dump()) for id,snapshot in zip(ids,original.history)])
        snapshots+=len(original.history)
    db.flush()
    return len(validated),snapshots
