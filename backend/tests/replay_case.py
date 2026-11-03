"""Genuine-derived anonymized DOMs;syntheticchanges are never called real events."""
from dataclasses import replace
from datetime import datetime,timedelta,timezone
import hashlib
from bs4 import BeautifulSoup
from fastapi.testclient import TestClient
from app.config import Settings
from app.main import create_app
from app.jobs import enqueue
from app.scenario_storage import enable_scenarios
from app.sources.profile_registration import register_profile
from app.sources.table_profiles import SGU,GUAP
from app.sources.storage import RawStore
from app.sources.publishing import publish
from app.worker import run_once
from test_api import HEADERS,start
from test_table_family import fetch,binding


def replay_case(engine,folder):
    app=create_app(Settings(database_url=engine.url.render_as_string(hide_password=False),auto_create_schema=False))
    profiles={p.source_id:p for p in (SGU,GUAP)};base=datetime(2026,11,1,tzinfo=timezone.utc)
    bodies={p.source_id:fetch(p).body for p in (SGU,GUAP)};clock=[base];transports=[0]
    store=RawStore(folder/'raw');states=[]
    def captured(source_binding,*_,**__):
        transports[0]+=1;profile=profiles[source_binding.source_id];raw=fetch(profile,bodies[profile.source_id]);return replace(raw,fetched_at=clock[0])
    def cycles(offset):
        clock[0]=base+timedelta(seconds=offset)
        for p in profiles.values():enqueue(app.state.engine,p.source_id,now=clock[0])
        values=[run_once(app.state.engine,store,registry=app.state.source_registry,fetch=captured,now=lambda:clock[0]) for _ in range(2)]
        assert {x.get('sourceId') for x in values}==set(profiles)
        return sorted((x['sourceId'],x['state']) for x in values)
    with TestClient(app) as client:
        for p in profiles.values():register_profile(app.state.engine,p,enable=True,registry=app.state.source_registry)
        assert all(value[1]=='success' for value in cycles(0))
        for p in profiles.values():enable_scenarios(app.state.engine,p.source_id,registry=app.state.source_registry)
        start(client);ids={}
        for p in profiles.values():
            found=client.post(f'/api/v1/sources/{p.source_id}/lookup',json={'publicCode':'FIXTURE-000020'},headers=HEADERS)
            assert found.status_code==200
            saved=client.post('/api/v1/subscriptions',json={'confirmationToken':found.json()['confirmationToken']},headers=HEADERS)
            assert saved.status_code==201;ids[p.source_id]=saved.json()['id']
        def record(name,outcomes=None):
            results={}
            for p in profiles.values():
                scenario=client.get(f'/api/v1/subscriptions/{ids[p.source_id]}/scenario').json()
                status=client.get(f'/api/v1/sources/{p.source_id}/status').json()
                assert status['dataKind']=='archive' and status['season']==2026
                results[p.source_id]={'state':status['state'],'fetchedAt':status['fetchedAt'],'result':scenario['result'],'changes':scenario['changes'],
                    'explanation':scenario['explanation'],'historyTotal':client.get(f'/api/v1/subscriptions/{ids[p.source_id]}/scenario-history').json()['total']}
            states.append({'step':name,'workerOutcomes':outcomes,'sources':results});return results
        first=record('genuine-derived-baseline')
        assert first[GUAP.source_id]['result']['state']=='unsupported'
        soup=BeautifulSoup(bodies[SGU.source_id],'html.parser');cell=soup.select_one('td[data-label="Согласие на зачисление"]');cell.clear();cell.append('Да')
        bodies[SGU.source_id]=('<!-- SYNTHETIC consent change;not observed event -->\n'+str(soup)).encode()
        bodies[GUAP.source_id]=b'<!-- SYNTHETIC template-only change -->\n'+bodies[GUAP.source_id]
        changed=record('synthetic-consent-and-template',cycles(901))
        assert changed[SGU.source_id]['result']['numbers']['currentLower']==first[SGU.source_id]['result']['numbers']['currentLower']+1
        assert changed[GUAP.source_id]['changes']==[]
        for p in profiles.values():
            raw=replace(fetch(p,bodies[p.source_id]),fetched_at=base+timedelta(seconds=902))
            publish(app.state.engine,p.source_id,app.state.source_registry.resolve(binding(p)).parse(raw,binding(p)),raw,store,registry=app.state.source_registry)
        repeated=record('same-payload-safe-repeat')
        assert repeated==changed
        good=bodies[SGU.source_id];bodies[SGU.source_id]=b'<html>Login required</html>'
        failed=record('synthetic-source-failure',cycles(1802))
        assert failed[SGU.source_id]['state']=='source_error' and failed[SGU.source_id]['result']==changed[SGU.source_id]['result']
        bodies[SGU.source_id]=good
        recovered=record('synthetic-recovery',cycles(2703))
        assert recovered[SGU.source_id]['state']=='archived' and recovered[SGU.source_id]['fetchedAt']==changed[SGU.source_id]['fetchedAt']
        bodies[SGU.source_id]=good.replace(b'FIXTURE-000020',b'FIXTURE-999999')
        missing=record('synthetic-row-absence',cycles(3604))
        assert missing[SGU.source_id]['result']['reasonCodes']==['candidate_not_in_snapshot']
        assert missing[SGU.source_id]['result']['numbers'] is None
        assert missing[SGU.source_id]['historyTotal']==3 and missing[GUAP.source_id]['historyTotal']==2
        checks=client.get(f'/api/v1/sources/{SGU.source_id}/checks').json()
        assert any(c['outcome']=='failed' for c in checks)
    return {'steps':states,'replayedTransportCalls':transports[0],'externalHttpFetches':0,'sourceFetchClock':'fixed2026-11-01+offsets,syntheticchange times','processingClock':'actual replay execution,excluded from semanticcomparison','scope':'anonymized genuine-derived baseline plus explicitly synthetic changes/failure/recovery;not live observation'}
