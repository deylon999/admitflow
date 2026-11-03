#!/usr/bin/env python3
"""Create and destroy an owned Compose project to verify volume/worker recovery."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
import httpx


def require(value, message):
    if not value:
        raise RuntimeError(message)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--backend-image', required=True, help='Freshly built backend image; also used by worker')
    parser.add_argument('--frontend-image', required=True, help='Freshly built nginx/frontend image')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    # No existing project name/volume/DB URL is accepted.
    project = f'admitflow-rehearsal-{uuid4().hex[:12]}'
    with socket.socket() as reservation:
        reservation.bind(('127.0.0.1', 0))
        port = reservation.getsockname()[1]
    with tempfile.TemporaryDirectory(prefix='admitflow-compose-') as folder:
        override = Path(folder) / 'images.json'
        override.write_text(json.dumps({'services': {
            'backend': {'image': args.backend_image}, 'worker': {'image': args.backend_image},
            'frontend': {'image': args.frontend_image},
        }}))
        command = ['docker', 'compose', '-p', project, '-f', str(ROOT / 'compose.yaml'), '-f', str(override), '--profile', 'automation']
        env = {**os.environ, 'WEB_PORT': str(port)}

        def compose(*parts, **kwargs):
            return subprocess.run([*command, *parts], cwd=ROOT, env=env, check=True,
                                  capture_output=True, text=True, timeout=180, **kwargs)

        def execute(service, script):
            return json.loads(compose('exec', '-T', service, 'python', '-', input=script).stdout)

        def containers():
            ids = compose('ps', '-q').stdout.split()
            values = json.loads(subprocess.check_output(['docker', 'inspect', *ids]))
            return {item['Config']['Labels']['com.docker.compose.service']: {
                'id': item['Id'], 'image': item['Image'], 'ports': item['HostConfig']['PortBindings'] or {},
                'volumes': {mount['Destination']: mount['Name'] for mount in item['Mounts'] if mount['Type'] == 'volume'},
                'state': item['State']['Status'], 'health': item['State'].get('Health', {}).get('Status'),
            } for item in values}

        report = {'recordedAt': datetime.now(timezone.utc).isoformat(), 'scope': 'owned local synthetic Compose recreation; no production/live-source guarantee'}
        try:
            compose('up', '-d', '--no-build', '--wait', '--wait-timeout', '90')
            before = containers()
            require(set(before) == {'db', 'backend', 'frontend', 'worker'}, 'Expected four services')
            headers = {'X-Requested-With': 'abiturient'}
            body = dict(university='Compose rehearsal example', title='Synthetic manual group', sourceUrl='https://example.org/list',
                        values=dict(rank=120, seats=90, excluded=30, noConsent=16))
            with httpx.Client(base_url=f'http://127.0.0.1:{port}', headers=headers, timeout=15, trust_env=False) as owner, \
                    httpx.Client(base_url=f'http://127.0.0.1:{port}', headers=headers, timeout=15, trust_env=False) as other:
                require(owner.post('/api/v1/session').status_code == 204, 'Owner bootstrap failed')
                require(other.post('/api/v1/session').status_code == 204, 'Other bootstrap failed')
                create_headers = {'Idempotency-Key': 'compose-recreate-create'}
                created = owner.post('/api/v1/watches', json=body, headers=create_headers)
                require(created.status_code == 201, 'Create failed')
                watch = created.json()
                path = f"/api/v1/watches/{watch['id']}"
                update_headers = {'Idempotency-Key': 'compose-recreate-update'}
                values = body['values'] | {'rank': 121}
                updated = owner.post(path + '/snapshots', json=values, headers=update_headers)
                require(updated.status_code == 201, 'Update failed')
                removed = owner.post('/api/v1/watches', json=body, headers={'Idempotency-Key': 'compose-recreate-deleted'})
                require(removed.status_code == 201, 'Tombstone preparation failed')
                require(owner.delete('/api/v1/watches/' + removed.json()['id']).status_code == 204, 'Delete failed')
                history = owner.get(path).json()
                deadline = owner.get('/api/v1/session').json()
                owner_cookies, other_cookies = dict(owner.cookies), dict(other.cookies)
            compose('stop', 'worker')
            prepared = execute('backend', '''
import json,os
from datetime import datetime,timezone
from sqlalchemy.orm import Session
from app.admissions import University,Campaign,CompetitionGroup,Source
from app.config import Settings
from app.database import make_engine
from app.jobs import enqueue
from app.sources.storage import RawStore
engine=make_engine(Settings.from_env().database_url)
with Session(engine) as db:
    db.add(University(id='rehearsal-u',name='Synthetic only',official_url='https://example.org',provenance_url='https://example.org/list',verified_at=datetime.now(timezone.utc)));db.flush()
    db.add(Campaign(id='rehearsal-c',university_id='rehearsal-u',year=2026,level='bachelor'));db.flush()
    db.add(CompetitionGroup(id='rehearsal-g',campaign_id='rehearsal-c',official_id='test',title='Synthetic only',study_form='full-time',funding='budget',category='general',seats=10,coverage='candidate'));db.flush()
    db.add(Source(id='rehearsal-source',group_id='rehearsal-g',url='https://example.org/list',domain='example.org',adapter_version='rehearsal-unsupported-v1',snapshot_kind='archive',enabled=True));db.commit()
store=RawStore(os.environ['RAW_STORE_PATH'])
digest=store.put(b'Compose volume rehearsal raw')
print(json.dumps(dict(queued=enqueue(engine,'rehearsal-source'),digest=digest,uid=os.getuid(),mode=oct(store.root.stat().st_mode & 0o777))))
engine.dispose()
''')
            require(prepared['queued'] and prepared['uid'] > 0 and prepared['mode'] == '0o700', 'Queue or raw permissions invalid')
            started = time.monotonic()
            compose('up', '-d', '--no-build', '--force-recreate', '--wait', '--wait-timeout', '90')
            after = containers()
            for service in before:
                require(before[service]['id'] != after[service]['id'], 'Service was not recreated')
                require(before[service]['image'] == after[service]['image'], 'Image unexpectedly changed')
                require(before[service]['volumes'] == after[service]['volumes'], 'Persistent mount changed')
                require(after[service]['state'] == 'running', 'Service did not resume')
                if service != 'worker':
                    require(after[service]['health'] == 'healthy', 'Healthcheck failed')
                if service != 'frontend':
                    require(after[service]['ports'] == {}, 'Private service published ports')
            require(after['frontend']['ports']['80/tcp'] == [{'HostIp': '127.0.0.1', 'HostPort': str(port)}], 'Frontend binding changed')
            with httpx.Client(base_url=f'http://127.0.0.1:{port}', headers=headers, cookies=owner_cookies, timeout=15, trust_env=False) as owner, \
                    httpx.Client(base_url=f'http://127.0.0.1:{port}', headers=headers, cookies=other_cookies, timeout=15, trust_env=False) as other:
                require(owner.get(path).json() == history, 'History differs after recreation')
                require(owner.get('/api/v1/session').json() == deadline, 'Session deadline/scope changed')
                require(other.get(path).status_code == 404 and other.get('/api/v1/watches').json() == [], 'Ownership isolation failed')
                replay = owner.post('/api/v1/watches', json=body, headers=create_headers)
                require(replay.status_code == 201 and replay.json() == watch, 'Create replay changed')
                replay = owner.post(path + '/snapshots', json=values, headers=update_headers)
                require(replay.status_code == 201 and replay.json() == updated.json(), 'Update replay changed')
                require(owner.post('/api/v1/watches', json=body, headers={'Idempotency-Key': 'compose-recreate-deleted'}).status_code == 410, 'Deleted operation resurrected data')
                require(owner.get(path).json() == history, 'Replay duplicated history')
            poll_deadline = time.monotonic() + 30
            while True:
                job = execute('backend', '''
import json
from sqlalchemy import select,func
from sqlalchemy.orm import Session
from app.admissions import SourceSnapshot
from app.config import Settings
from app.database import make_engine
from app.jobs import SourceJob
engine=make_engine(Settings.from_env().database_url)
with Session(engine) as db:
    job=db.get(SourceJob,'rehearsal-source')
    print(json.dumps(dict(state=job.state,error=job.last_error_code,snapshots=db.scalar(select(func.count()).select_from(SourceSnapshot)))))
engine.dispose()
''')
                if job['state'] == 'failed':
                    break
                require(time.monotonic() < poll_deadline, 'Actual worker did not process the persisted job')
                time.sleep(0.5)
            require(job == {'state': 'failed', 'error': 'adapter_unavailable', 'snapshots': 0}, 'Unsupported adapter published or failed unexpectedly')
            worker_raw = execute('worker', f'''
import json,os
from app.sources.storage import RawStore
store=RawStore(os.environ['RAW_STORE_PATH'])
print(json.dumps(dict(uid=os.getuid(),rawMatches=store.read({prepared['digest']!r})==b'Compose volume rehearsal raw')))
''')
            require(worker_raw['uid'] > 0 and worker_raw['rawMatches'], 'Worker cannot read persistent backend raw')
            diagnostic = json.loads(compose('exec', '-T', 'backend', 'python', '-m', 'app.diagnostics', 'database').stdout)
            require(diagnostic['dialect'] == 'postgresql' and diagnostic['status'] == 'revision_current', 'Database revision failed')
            report.update(success=True, recreatedServices=sorted(after), images={key: item['image'] for key, item in after.items()},
                          recreationAndValidationSeconds=round(time.monotonic()-started, 3), exactHistory=True,
                          stableDeadlineAndScope=True, ownership=True, retryAndTombstone=True, rawSharedAsNonRoot=True,
                          persistentMounts=True, privatePorts=True, workerJob=job, databaseDiagnostic=diagnostic)
        finally:
            # Only the randomly named project created above is ever removed.
            compose('down', '--volumes', '--remove-orphans')
        report['cleanup'] = True
        args.output.write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(report))


if __name__ == '__main__':
    main()
