#!/usr/bin/env python3
"""Check tracked/build artifacts against private SGU codes/key without printing them."""
import argparse
from datetime import datetime,timezone
import json
from pathlib import Path
import re
import stat
import subprocess
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--guap-original',type=Path);p.add_argument('--original',type=Path,required=True);p.add_argument('--key-file',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    original=a.original.read_bytes()
    if len(original)>8*1024*1024:raise RuntimeError('Private original exceeds audit bound')
    soup=BeautifulSoup(original,'html.parser')
    codes={td.get_text(strip=True).encode() for td in soup.select('td[data-label="Код поступающего"]')}
    if len(codes)!=573:raise RuntimeError('Private original code scope differs; no codes printed')
    compared=len(codes)
    if a.guap_original:
        guap=a.guap_original.read_bytes()
        if len(guap)>8*1024*1024:raise RuntimeError('Additional private original exceeds bound')
        rows=BeautifulSoup(guap,'html.parser').select('table.pk-ratings-table tr')
        additional={re.sub(r'\s*\(Зачислен\)\s*$','',row.find_all('td')[1].get_text(' ',strip=True)).encode() for row in rows if len(row.find_all('td'))==14}
        if len(additional)!=581:raise RuntimeError('Additional private code scope differs;no codes printed')
        codes|=additional;compared+=len(additional)
    key=a.key_file.read_text().strip().split('=',1)[1].encode()
    if not re.fullmatch(b'[a-fA-F0-9]{64,128}',key):raise RuntimeError('Private key format differs; not printed')
    pattern=re.compile(rb'(?<![A-Za-z0-9-])(?:'+b'|'.join(re.escape(x) for x in sorted(codes))+rb')(?![A-Za-z0-9-])')
    tracked=[ROOT/Path(x.decode()) for x in subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).split(b'\0') if x]
    build=list((ROOT/'frontend/dist').rglob('*'))
    matches=[];scanned=0
    for path in [*tracked,*build]:
        if not path.is_file() or path.is_symlink():continue
        body=path.read_bytes();scanned+=1
        if key in body or pattern.search(body):matches.append(str(path.relative_to(ROOT)))
    permissions={name:stat.S_IMODE(path.stat().st_mode)==0o600 for name,path in [('original',a.original),('keyFile',a.key_file)]}
    if a.guap_original:permissions['guapOriginal']=stat.S_IMODE(a.guap_original.stat().st_mode)==0o600
    result={'recordedAt':datetime.now(timezone.utc).isoformat(),'format':'private-artifact-audit-v1','sourceCodesCompared':compared,'filesScanned':scanned,'privateMatches':len(matches),'affectedPaths':matches[:20],'privateFileModes600':permissions,'success':not matches and all(permissions.values()),'scope':'tracked working-tree files + current frontend/dist only;no real codes/key printed;not full Git-history or external-host audit'}
    a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
    return 0 if result['success'] else 1


if __name__=='__main__':raise SystemExit(main())
