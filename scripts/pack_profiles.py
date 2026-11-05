"""Publish validated immutable profile shards, preserving the legacy artifact."""
import argparse
from pathlib import Path
import sys
import json
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'backend'))
from app.sources.profile_catalog import active_catalog,read_profile_data,publish_profile_data


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',type=Path)
    p.add_argument('--output-dir',type=Path,default=ROOT/'backend/app/sources/profiles')
    args=p.parse_args();data=read_profile_data(args.input or active_catalog(ROOT/'backend/app/sources/profiles'))
    manifest=publish_profile_data(data['profiles'],args.output_dir)
    print(json.dumps(dict(profiles=manifest['profileCount'],shards=len(manifest['shards']))))


if __name__=='__main__':main()
