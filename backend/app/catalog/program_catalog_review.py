"""Reviewed programme-document extraction; no applicant rows or implicit contests.

Original bytes must match a versioned review. Extractors preserve the scope of
the official document; aggregate places never become general-competition seats.
"""
import hashlib
from io import BytesIO
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

from bs4 import BeautifulSoup

REVIEWS = Path(__file__).resolve().parents[1] / 'data' / 'program-catalog-reviews.json'


def clean(value):
    return ' '.join(value.split())


def canonical_hash(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def _record(key, title, code=None, study_form=None, totals=None):
    return dict(source_key=key, title=title, code=code, study_form=study_form,
                funding=None, category=None, seats=None, admission_totals=totals,
                groups=[])


def hse_announcement(doc, review):
    if review['university_id'] != 'miccedu-1766' or review['level'] != 'bachelor':
        raise ValueError('catalog_university_scope_mismatch')
    paragraphs = doc.select('#w-3369 p.lead')
    if len(paragraphs) != 1:
        raise ValueError('catalog_source_structure_changed')
    paragraph = paragraphs[0]
    text = clean(paragraph.get_text(' ', strip=True))
    if not text.startswith(f'В {review["year"]} году') or 'бакалаврские программы' not in text:
        raise ValueError('catalog_campaign_mismatch')
    # Scope ends at the explicit Moscow marker, before branch programmes.
    marker = '(Школа дизайна НИУ ВШЭ — Москва)'
    if text.count(marker) != 1:
        raise ValueError('catalog_university_scope_mismatch')
    moscow = text[:text.index(marker)]
    moscow_links = []
    for child in paragraph.children:
        if marker in clean(child.get_text(' ', strip=True) if hasattr(child, 'get_text') else str(child)):
            break
        if getattr(child, 'name', None) == 'a':
            moscow_links.append(child)
    records = []
    for selection in review['selection']:
        path = selection['source_key']
        links = [a for a in paragraph.select('a[href]') if urlsplit(a['href']).hostname == 'design.hse.ru' and urlsplit(a['href']).path == path]
        if len(links) != 1:
            raise ValueError('catalog_program_identity_ambiguous')
        literal = clean(links[0].get_text(' ', strip=True))
        if links[0] not in moscow_links or literal not in moscow:
            raise ValueError('catalog_university_scope_mismatch')
        title = literal.removeprefix('«').removesuffix('»')
        records.append(_record(path, title))
    return records


def sgu_admission_plan(doc, review):
    if review['university_id'] != 'sgu-saratov' or review['level'] != 'bachelor':
        raise ValueError('catalog_university_scope_mismatch')
    year = review['year']
    links = [a for a in doc.select('a[href]') if a.get('href') == review['url']]
    scoped = False
    for link in links:
        menu = link.find_parent('li', class_='burger-menu__wrap-sub-disclosure')
        label = menu.select_one('a.burger-menu__sub-disclosure') if menu else None
        if label and clean(label.get_text(' ', strip=True)) == f'Приём {year}':
            scoped = True
    if not scoped:
        raise ValueError('catalog_campaign_mismatch')
    tables = [t for t in doc.select('table') if review['selection'][0]['source_key'] in t.get_text()]
    if len(tables) != 1:
        raise ValueError('catalog_source_structure_changed')
    table = tables[0]
    subtitle = table.find_previous('div', class_='subtitle')
    heading = table.find_previous('h2')
    if (not subtitle or clean(subtitle.get_text(' ', strip=True)) != 'СГУ (головной вуз) Бакалавриат'
            or not heading or 'по очной форме обучения' not in clean(heading.get_text(' ', strip=True))):
        raise ValueError('catalog_university_scope_mismatch')
    headers = table.select('tr')[0].find_all('th', recursive=False)
    if (len(headers) != 8 or '(общее число мест)' not in clean(headers[2].get_text(' ', strip=True))
            or f'15.04.{year}' not in headers[3].get_text() or 'Отдельная квота' not in headers[5].get_text()
            or 'платных' not in headers[6].get_text()):
        raise ValueError('catalog_source_structure_changed')
    records = []
    def number(cell):
        value = clean(cell.get_text(' ', strip=True))
        if not value or value in ('—', '–', '-'):
            return None
        if not re.fullmatch(r'\d{1,7}', value):
            raise ValueError('catalog_invalid_places')
        return int(value)
    for selection in review['selection']:
        code = selection['source_key']
        if not re.fullmatch(r'\d{2}\.03\.\d{2}', code):
            raise ValueError('catalog_invalid_program_code')
        cells = [n for n in table.select('.direction-name') if clean(n.get_text(' ', strip=True)).startswith(code + ' ')]
        if len(cells) != 1:
            raise ValueError('catalog_program_identity_ambiguous')
        title = clean(cells[0].get_text(' ', strip=True))[len(code)+1:]
        row = cells[0].find_parent('tr').find_all('td', recursive=False)
        if len(row) != 8:
            raise ValueError('catalog_source_structure_changed')
        totals = dict(budget_total=number(row[2]), target_quota=number(row[3]),
                      special_quota=number(row[4]), separate_quota=number(row[5]), paid_total=number(row[6]))
        records.append(_record(code, title, code, 'full-time', totals))
    return records


def hse_urban_announcement(doc, review):
    if review['university_id'] != 'miccedu-1766' or review['level'] != 'bachelor':
        raise ValueError('catalog_university_scope_mismatch')
    year = review['year']
    headings = [clean(node.get_text(' ', strip=True)) for node in doc.select('.post__text h4.block-title')]
    if headings.count(f'5. Как поступить в бакалавриат в {year} году?') != 1:
        raise ValueError('catalog_campaign_mismatch')
    key = '/ba/up/'
    title = 'Девелопмент и городское планирование'
    links = doc.select('.post__text p a[href="https://www.hse.ru/ba/up/"]')
    lead = [link for link in links
            if clean(link.get_text(' ', strip=True)) == f'«{title}»'
            and f'от поступления в {year} году' in clean(link.parent.get_text(' ', strip=True))]
    titles = doc.select('.post__content h1.post-title')
    if (len(lead) != 1 or len(titles) != 1
            or not clean(titles[0].get_text(' ', strip=True)).startswith(f'Бакалавриат «{title}»:')
            or [selection['source_key'] for selection in review['selection']] != [key]):
        raise ValueError('catalog_source_structure_changed')
    return [_record(key, title)]


EXTRACTORS = {'hse-moscow-announcement-v1': hse_announcement, 'sgu-head-full-time-plan-v1': sgu_admission_plan,
              'hse-urban-announcement-v1': hse_urban_announcement}


def nntu_department_brochure(body, review):
    from pypdf import PdfReader
    from pypdf.errors import PyPdfError

    if review['university_id'] != 'miccedu-169' or review['level'] != 'bachelor':
        raise ValueError('catalog_university_scope_mismatch')
    try:
        pdf = PdfReader(BytesIO(body), strict=True)
        if pdf.is_encrypted or len(pdf.pages) != 2:
            raise ValueError('catalog_source_structure_changed')
        cover, admission = (clean(page.extract_text()) for page in pdf.pages)
    except PyPdfError as error:
        raise ValueError('catalog_invalid_pdf') from error
    if ('Нижегородский государственный технический университет им. Р.Е. Алексеева' not in cover
            or 'Металлургические технологии и оборудование' not in cover):
        raise ValueError('catalog_university_scope_mismatch')
    heading = f'В {review["year"]} году проводится приём для ОЧНОГО обучения по следующим образовательным программам:'
    if admission.count(heading) != 1:
        raise ValueError('catalog_campaign_mismatch')
    contents = admission.split(heading, 1)[1].strip()
    match = re.match(r'Бакалавриат ([0-9]{2}\.03\.[0-9]{2}) «Металлургия» Профиль «([^»]+)»', contents)
    if not match or len(re.findall(r'Бакалавриат [0-9]{2}\.03\.[0-9]{2}', contents)) != 1:
        raise ValueError('catalog_source_structure_changed')
    code, profile = match.groups()
    key = f'{code}:{profile}'
    if [s['source_key'] for s in review['selection']] != [key]:
        raise ValueError('catalog_program_identity_ambiguous')
    return [_record(key, profile, code, 'full-time')]


PDF_EXTRACTORS = {'nntu-metallurgy-brochure-v1': nntu_department_brochure}


def extract_reviewed(body, review):
    if not review['selection'] or len({s['source_key'] for s in review['selection']}) != len(review['selection']):
        raise ValueError('catalog_incomplete_document')
    if not isinstance(body, bytes) or not 1 <= len(body) <= 5 * 1024 * 1024:
        raise ValueError('catalog_invalid_document_size')
    if hashlib.sha256(body).hexdigest() != review['original_sha256']:
        raise ValueError('catalog_original_hash_mismatch')
    content_type = review.get('content_type', 'text/html')
    extractors = {'text/html': EXTRACTORS, 'application/pdf': PDF_EXTRACTORS}.get(content_type, {})
    extractor = extractors.get(review['extractor_version'])
    if not extractor:
        raise ValueError('catalog_unsupported_extractor')
    original = BeautifulSoup(body.decode('utf-8', errors='strict'), 'html.parser') if content_type == 'text/html' else body
    records = extractor(original, review)
    if records != review['programs']:
        raise ValueError('catalog_review_facts_mismatch')
    if len({p['source_key'] for p in records}) != len(records):
        raise ValueError('catalog_program_identity_ambiguous')
    return records


def load_reviews():
    data = json.loads(REVIEWS.read_text(encoding='utf-8'))
    if data['format'] != 'reviewed-program-catalog-v1' or not data['sources']:
        raise ValueError('catalog_invalid_review_package')
    if (len({r['key'] for r in data['sources']}) != len(data['sources'])
            or len({(r['university_id'], r['year'], r['level'], r['source_namespace']) for r in data['sources']}) != len(data['sources'])):
        raise ValueError('catalog_duplicate_review_scope')
    return data['sources']
