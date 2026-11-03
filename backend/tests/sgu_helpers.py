"""Known real-group identity seeded only into disposable test databases."""
from sqlalchemy.orm import Session
from app.admissions import Campaign,CompetitionGroup,Source
from app.catalog import seed_catalog
from app.sources.adapters.sgu2026 import GROUP_ID,SOURCE_ID,URL,VERSION


def seed_sgu(engine,*,enabled=True):
    seed_catalog(engine)
    with Session(engine) as db:
        db.add(Campaign(id='sgu-2026-bachelor',university_id='sgu-saratov',year=2026,level='bachelor'));db.flush()
        db.add(CompetitionGroup(id=GROUP_ID,campaign_id='sgu-2026-bachelor',official_id='4588',title='09.03.04 Программная инженерия — общий конкурс',study_form='full-time',funding='budget',category='general',seats=16,coverage='candidate'));db.flush()
        db.add(Source(id=SOURCE_ID,group_id=GROUP_ID,url=URL,domain='www.sgu.ru',adapter_version=VERSION,snapshot_kind='archive',enabled=enabled));db.commit()
