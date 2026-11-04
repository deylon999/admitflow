#!/usr/bin/env python3
"""Host-side signal for cron: worker, sources, disk and backup age. Prints reasons, not data.

Exit code 1 means someone should look. With ALERT_WEBHOOK_URL set, the same JSON is posted there.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import urllib.request


def status(compose):
    # Runs inside the network: /api/status is deliberately closed at the public edge.
    output=subprocess.run([*compose.split(),'exec','-T','backend','python','-m','app.observability','status'],capture_output=True,text=True,timeout=60)
    if output.returncode:
        return None
    return json.loads(output.stdout)


def problems(report,*,free_share,backup_age_hours,max_backup_hours=26,min_free_share=.15):
    found=[]
    if report is None:
        return ['api_status_unavailable']
    if report['worker']['state']!='alive':
        found.append('worker_'+report['worker']['state'])
    for state in ('source_error','quarantined','stale'):
        if report['sources']['byState'].get(state):
            found.append(f'sources_{state}')
    if report['jobs']['overdue']:
        found.append('jobs_overdue')
    if free_share<min_free_share:
        found.append('disk_low')
    if backup_age_hours is None:
        found.append('backup_missing')
    elif backup_age_hours>max_backup_hours:
        found.append('backup_old')
    return found


def newest_backup_hours(folder):
    if not folder or not Path(folder).is_dir():
        return None
    stamps=[item.stat().st_mtime for item in Path(folder).iterdir() if (item/'restored-counts.txt').exists()]
    return (datetime.now(timezone.utc).timestamp()-max(stamps))/3600 if stamps else None


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compose',default='docker compose -f compose.prod.yaml')
    parser.add_argument('--backups')
    parser.add_argument('--disk',default='/')
    args=parser.parse_args()
    usage=shutil.disk_usage(args.disk)
    found=problems(status(args.compose),free_share=usage.free/usage.total,backup_age_hours=newest_backup_hours(args.backups))
    message=json.dumps(dict(ok=not found,problems=found,checkedAt=datetime.now(timezone.utc).isoformat()))
    print(message)
    webhook=os.getenv('ALERT_WEBHOOK_URL')
    if found and webhook:
        request=urllib.request.Request(webhook,data=message.encode(),headers={'Content-Type':'application/json'})
        urllib.request.urlopen(request,timeout=10).close()
    return 1 if found else 0


if __name__=='__main__':
    sys.exit(main())
