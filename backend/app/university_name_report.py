"""Compute coverage on the shipped catalog in a private temporary database.

Usage: python -m app.university_name_report --output path.json
Never connects to the configured application database or modifies source files.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from sqlalchemy.orm import Session

from .accreditation_registry import load_registry
from .catalog_import import import_reviewed
from .database import Base, make_engine
from .national_catalog import load_catalog
from .product_catalog import universities


def build_report(rows):
    counts = Counter(row.display_name_source.kind for row in rows)
    originals = [row for row in rows if row.display_name_source.kind == 'original']
    return {
        'catalogSha256': load_catalog().sha256,
        'accreditationSha256': load_registry().sha256,
        'total': len(rows),
        'official': counts['official'], 'normalized': counts['normalized'], 'manual': counts['manual'],
        'officialStrictlyShorter': sum(row.display_name_source.kind == 'official' and len(row.display_name) < len(row.legal_name) for row in rows),
        'original': counts['original'],
        # Overlapping queue: originals need review before shortening, not
        # another mutually exclusive bucket to add to the four above.
        'needsManualReview': len(originals),
        'branches': sum(row.is_branch for row in rows),
        'branchesWithVerifiedMetadata': sum(row.branch_info is not None for row in rows),
        'records': [dict(id=row.id, fullName=row.legal_name, displayName=row.display_name,
                         kind=row.display_name_source.kind, isBranch=row.is_branch,
                         source=row.display_name_source.model_dump(mode='json', by_alias=True),
                         branchInfo=row.branch_info.model_dump(mode='json', by_alias=True) if row.branch_info else None)
                    for row in sorted(rows, key=lambda row: row.id)],
        'manualReviewIds': sorted(row.id for row in originals),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    with TemporaryDirectory(prefix='admitflow-name-report-') as temporary:
        engine = make_engine(f'sqlite:///{Path(temporary) / "report.db"}')
        try:
            Base.metadata.create_all(engine)
            import_reviewed(engine)
            with Session(engine) as db:
                report = build_report(universities(db))
        finally:
            engine.dispose()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: value for key, value in report.items() if key not in ('records', 'manualReviewIds')}))


if __name__ == '__main__':
    main()
