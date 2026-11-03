"""One per-owner limit shared by manual watches and confirmed source subscriptions."""
from sqlalchemy import func,select
from .admissions import Subscription
from .calculation import CamelModel
from .database import Watch

LIMIT=20


class DirectionBudget(CamelModel):
    limit:int=LIMIT
    total:int
    manual_count:int
    archive_count:int


def direction_budget(db,owner):
    manual=select(func.count()).select_from(Watch).where(Watch.owner_hash==owner).scalar_subquery()
    archive=select(func.count()).select_from(Subscription).where(Subscription.owner_hash==owner).scalar_subquery()
    m,a=db.execute(select(manual,archive)).one()
    return DirectionBudget(total=m+a,manual_count=m,archive_count=a)
