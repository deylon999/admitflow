"""Build backend/app/data/exam-requirements.json from reviewed official documents (KAN-219).

Input: review files in docs/sources/exam-rules/*.json (what a person read in the
document) and the original documents (PDF). The builder trusts neither alone:
- the document hash must equal the hash declared in the review;
- every group anchor and evidence line must be found in the declared block of
  the document text, and every minimum score must be backed by an evidence line
  with that subject and number;
- a subject listed under "conflicts" must have a null minimum score, and both
  conflicting lines must be in the document.
The output depends only on the inputs, so a repeated run gives the same bytes.

Usage:
    python scripts/build_exam_requirements.py --pdf <document.pdf> [--pdf ...] [--check]
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
REVIEWS = ROOT/'docs'/'sources'/'exam-rules'
OUTPUT = ROOT/'backend'/'app'/'data'/'exam-requirements.json'
STEMS = {
    'russian': 'русский язык', 'math': 'математика', 'physics': 'физика', 'informatics': 'информатика',
    'chemistry': 'химия', 'biology': 'биология', 'history': 'история', 'geography': 'география',
    'social': 'обществознание', 'literature': 'литература', 'foreign': 'иностранный язык',
}
GROUP_KEYS = ('groupId', 'year', 'level', 'code', 'studyForm', 'tests', 'additionalTests', 'benefits', 'notes')


class ReviewError(ValueError):
    pass


def normalise(text):
    return '\n'.join(' '.join(line.split()) for line in text.splitlines() if line.strip())


def pdf_text(path):
    result = subprocess.run(['pdftotext', '-layout', str(path), '-'], check=True, capture_output=True)
    return result.stdout.decode('utf-8')


def block(text, start, end):
    if text.count(start) != 1:
        raise ReviewError(f'block start must occur once: {start}')
    begin = text.index(start)
    finish = text.find(end, begin)
    if finish < 0:
        raise ReviewError(f'block end not found: {end}')
    return text[begin:finish]


def check_review(review, text):
    """Raise ReviewError unless every declared fact is in the document text."""
    text = normalise(text)
    folded = text.casefold()
    part = block(text, review['block']['start'], review['block']['end']).casefold()
    evidence = [e.casefold() for e in review['block']['evidence']]
    for line in evidence:
        if line not in part:
            raise ReviewError(f'evidence not in block: {line}')
    conflicts = {}
    for conflict in review.get('conflicts', []):
        for line in conflict['evidence']:
            if line.casefold() not in folded:
                raise ReviewError(f'conflict evidence not in document: {line}')
        conflicts[conflict['subject']] = conflict['note']
    for group in review['groups']:
        if group['anchor'].casefold() not in part or not group['anchor'].startswith(group['code']):
            raise ReviewError(f"group anchor not in block: {group['anchor']}")
        for test in group['tests'] + (group['additionalTests'] or []):
            for option in test['options']:
                subject, score = option['subject'], option['minScore']
                if subject in conflicts:
                    if score is not None:
                        raise ReviewError(f'{subject} is in conflict and must stay null')
                elif score is None:
                    raise ReviewError(f'{subject} has no score and no recorded conflict')
                elif not any(STEMS[subject] in line and re.search(rf'(?<!\d){score}(?!\d)', line) for line in evidence):
                    raise ReviewError(f'no evidence for {subject} {score}')
    return conflicts


def build(reviews, texts):
    """reviews: parsed review files; texts: document sha256 -> extracted text."""
    sources, groups = [], []
    for review in sorted(reviews, key=lambda r: r['source']['id']):
        source = review['source']
        if source['sha256'] not in texts:
            raise ReviewError(f"document with sha256 {source['sha256']} was not given")
        conflicts = check_review(review, texts[source['sha256']])
        sources.append({k: source[k] for k in ('id', 'universityId', 'title', 'url', 'documentDate', 'sha256', 'pages', 'checkedAt', 'crossCheck')})
        for group in review['groups']:
            row = {k: group[k] for k in GROUP_KEYS}
            used = {o['subject'] for t in group['tests'] for o in t['options']}
            row['notes'] = list(group['notes']) + [note for subject, note in sorted(conflicts.items()) if subject in used]
            row['source'] = source['id']
            groups.append(row)
    ids = [g['groupId'] for g in groups]
    if len(ids) != len(set(ids)):
        raise ReviewError('a group is described twice')
    artifact = {'format': 'exam-requirements-v1', 'sources': sources, 'groups': sorted(groups, key=lambda g: g['groupId'])}
    return (json.dumps(artifact, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


def load_reviews(directory=REVIEWS):
    return [json.loads(path.read_text(encoding='utf-8')) for path in sorted(directory.glob('*.json'))]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--pdf', action='append', default=[], help='Original document; may repeat')
    parser.add_argument('--check', action='store_true', help='Fail if the committed artifact differs from a fresh build')
    args = parser.parse_args(argv)
    texts = {}
    for path in args.pdf:
        texts[hashlib.sha256(Path(path).read_bytes()).hexdigest()] = pdf_text(path)
    try:
        body = build(load_reviews(), texts)
    except ReviewError as error:
        print(f'review failed: {error}', file=sys.stderr)
        return 1
    if args.check:
        same = OUTPUT.exists() and OUTPUT.read_bytes() == body
        print('artifact is up to date' if same else 'artifact differs from a fresh build')
        return 0 if same else 1
    OUTPUT.write_bytes(body)
    print(f'wrote {OUTPUT.relative_to(ROOT)}: {body.count(b"groupId")} groups')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
