"""Local operator batch: exact closed-manifest IDs, one atomic transaction."""
import argparse
import json
from ..config import Settings
from ..database import make_engine
from .contracts import AdapterError
from .profile_registration import register_profiles,select_profiles
from .registry import runtime_registry


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source_ids',nargs='+',help='1–100 distinct IDs from the reviewed manifest; no URLs')
    parser.add_argument('--enable',action='store_true',help='Enable exact reviewed bindings using the existing stable identity key')
    parser.add_argument('--plan',action='store_true',help='Print selected scope metadata without connecting to a database or writing')
    args=parser.parse_args(argv);engine=None
    try:
        selected=select_profiles(args.source_ids)
        if args.plan:
            result=dict(readOnly=True,databaseChecked=False,count=len(selected),enableRequested=args.enable,
                items=[dict(sourceId=p.source_id,groupId=p.group_id,year=p.year,kind=p.kind,adapterVersion=p.version) for p in selected])
        else:
            engine=make_engine(Settings.from_env().database_url)
            result=register_profiles(engine,args.source_ids,enable=args.enable,registry=runtime_registry())
        print(json.dumps(result));return 0
    except AdapterError as error:print(json.dumps(dict(error=error.code)));return 1
    except Exception:print(json.dumps(dict(error='operation_failed')));return 1
    finally:
        if engine is not None:engine.dispose()


if __name__=='__main__':raise SystemExit(main())
