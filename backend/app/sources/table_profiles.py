"""Declarative source profiles;new source data needs no new decoder code."""
from datetime import datetime
import json
from pathlib import Path
from types import MappingProxyType
from .registry import Attestation
from .table_family import TableProfile


def load_profiles():
    try:
        body=Path(__file__).with_name('profiles').joinpath('reviewed.json').read_bytes()
        if len(body)>128*1024:raise ValueError()
        data=json.loads(body)
        if set(data)!={'format','profiles'} or data['format']!='reviewed-table-profiles-v1' or not 1<=len(data['profiles'])<=100:raise ValueError()
        profiles={}
        for name,fields in data['profiles'].items():
            if name!=fields.get('source_id'):raise ValueError()
            fields=dict(fields)
            for key in ('columns','identity'):fields[key]=tuple(tuple(pair) for pair in fields[key])
            for key in ('headers','cell_labels'):fields[key]=tuple(fields[key])
            if fields['proof'] is not None:
                proof=dict(fields['proof']);proof['verified_at']=datetime.fromisoformat(proof['verified_at']);fields['proof']=Attestation(**proof)
            profiles[name]=TableProfile(**fields)
        return MappingProxyType(profiles)
    except (ValueError,TypeError,KeyError,OSError):raise ValueError('invalid_reviewed_table_profiles') from None


PROFILES=load_profiles()
SGU=PROFILES['sgu-2026-4588']
GUAP=PROFILES['guap-2026-math-contract']
