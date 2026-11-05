"""Declarative source profiles;new source data needs no new decoder code."""
from datetime import datetime
import re
from pathlib import Path
from types import MappingProxyType
from .registry import Attestation
from .table_family import TableProfile
from .profile_catalog import active_catalog,read_profile_data


def build_profiles(data):
    try:
        if set(data)!={'format','profiles'} or data['format']!='reviewed-table-profiles-v1' or not isinstance(data['profiles'],dict):raise ValueError()
        profiles={};scopes=set()
        for name,fields in data['profiles'].items():
            if (not isinstance(name,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,35}',name) or not isinstance(fields,dict)
                or name!=fields.get('source_id') or not isinstance(fields.get('group_id'),str) or not 1<=len(fields['group_id'])<=36):raise ValueError()
            fields=dict(fields)
            for key in ('columns','identity','catalog'):fields[key]=tuple(tuple(pair) for pair in fields.get(key,[]))
            for key in ('headers','cell_labels'):fields[key]=tuple(fields[key])
            if 'unordered_label_groups' in fields:fields['unordered_label_groups']=tuple(tuple(group) for group in fields['unordered_label_groups'])
            if fields['proof'] is not None:
                proof=dict(fields['proof']);proof['verified_at']=datetime.fromisoformat(proof['verified_at']);fields['proof']=Attestation(**proof)
            profiles[name]=TableProfile(**fields)
            profile=profiles[name]
            if (profile.proof is None or profile.proof.source_url!=profile.url or profile.proof.year!=profile.year
                or profile.proof.kind!=profile.kind or profile.proof.adapter_version!=profile.version or profile.proof.sample_rows!=profile.rows):raise ValueError()
            scope=(profile.version,profile.url)
            if scope in scopes:raise ValueError()
            scopes.add(scope)
        return MappingProxyType(profiles)
    except (ValueError,TypeError,KeyError,OSError):raise ValueError('invalid_reviewed_table_profiles') from None


def load_profiles(path=None):
    try:
        return build_profiles(read_profile_data(path or active_catalog(Path(__file__).with_name('profiles'))))
    except (ValueError,TypeError,KeyError,OSError):raise ValueError('invalid_reviewed_table_profiles') from None


PROFILES=load_profiles()
SGU=PROFILES['sgu-2026-4588']
GUAP=PROFILES['guap-2026-math-contract']
