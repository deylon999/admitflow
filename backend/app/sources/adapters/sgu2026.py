"""Narrow, archive-only SGU4588 parser attested against the2026 original."""
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import re

from ..contracts import AdapterError, CandidateRow, ParsedList, scoped_candidate_key
from ..html_inspection import sgu_structure
from ..registry import Adapter, Attestation

VERSION = 'sgu-2026-4588-v1'
SOURCE_ID = GROUP_ID = 'sgu-2026-4588'
URL = 'https://www.sgu.ru/svodka/4588'
ROWS = 573
METADATA = {
    'Код:': '09.03.04', 'Направление / Специальность:': 'Программная инженерия',
    'Уровень образования:': 'Бакалавр', 'Форма обучения:': 'Очная',
    'Конкурсная группа:': 'Бюджет/Общие места / Профиль: Разработка программно-информационных систем',
    'Бюджетных мест:': '16',
}
LABELS = {'№','Код поступающего','Сумма баллов','Элементарная математика / Математика',
          'Основы физики / Основы алгоритмизации и программирование / Физика / Информатика и ИКТ',
          'Русский язык','Индивидуальное достижение','Согласие на зачисление','Статус зачисления',
          'Приоритет / ОВП / ВПП','Другие конкурсные группы'}


def parse(response, binding, secret):
    if (binding.source_id != SOURCE_ID or binding.group_id != GROUP_ID or binding.url != URL
            or binding.domain != 'www.sgu.ru' or binding.year != 2026 or binding.kind != 'archive'
            or binding.adapter_version != VERSION or response.url != URL):
        raise AdapterError('invalid_binding')
    if not binding.enabled:
        raise AdapterError('source_disabled')
    try:
        if (response.content_type != 'text/html' or (response.charset or 'utf-8').lower() not in ('utf-8','utf8')
                or hashlib.sha256(response.body).hexdigest() != response.payload_hash
                or not response.body.rstrip().endswith(b'</html>')):
            raise ValueError()
        soup, table, rows, metadata = sgu_structure(response.body)
        years = {int(match[1]) for value in soup.find_all(string=True)
                 if (match := re.fullmatch(r'При[её]м\s+(20[0-9]{2})',value.strip()))}
        if (len(rows) != ROWS or any(metadata.get(key) != value for key,value in METADATA.items())
                or years != {2026}
                or soup.select('.pager,.pagination,a[rel="next"]')):
            raise ValueError()
        headers = {item.get_text(' ',strip=True) for item in table.find_all('th')}
        if not {'№','Код поступающего','Сумма баллов','Согласие на зачисление','Статус зачисления'} <= headers:
            raise ValueError()
        entries, keys = [], set()
        for index,row in enumerate(rows,1):
            cells = row.find_all('td',recursive=False)
            if len(cells) != len(LABELS) or {cell.get('data-label') for cell in cells} != LABELS:
                raise ValueError()
            fields = {cell['data-label']:cell.get_text(' ',strip=True) for cell in cells}
            public_id = fields['Код поступающего']
            if not re.fullmatch(r'[A-Za-z0-9-]{1,64}',public_id) or fields['№'] != str(index):
                raise ValueError()
            key = scoped_candidate_key(binding,public_id,secret)
            if key in keys:
                raise ValueError()
            keys.add(key)
            score_text = fields['Сумма баллов']
            if not re.fullmatch(r'[0-9]{1,4}(?:[.,][0-9]{1,2})?',score_text):
                raise ValueError()
            score = Decimal(score_text.replace(',','.'))
            consent_text = fields['Согласие на зачисление']
            if consent_text not in ('Да','Нет','---',''):
                raise ValueError()
            consent = {'Да':True,'Нет':False}.get(consent_text)
            status = fields['Статус зачисления']
            if status not in ('Зачислен','---',''):
                raise ValueError()
            priority_text = fields['Приоритет / ОВП / ВПП']
            priority = None
            if priority_text not in ('---',''):
                match = re.fullmatch(r'([0-9]{1,4})\s*/\s*([01])\s*/\s*([01])',priority_text)
                if match is None:
                    raise ValueError()
                priority = int(match[1])
            entries.append(CandidateRow(candidate_key=key,row_ref=f'row/{index}',official_rank=index,score=score,
                                        consent=consent,priority=priority,participation='enrolled' if status=='Зачислен' else 'unknown'))
        warnings = ['no_source_timestamp']
        if any(row.consent is None for row in entries): warnings.append('unknown_consent')
        if any(row.priority is None for row in entries): warnings.append('unknown_priority')
        return ParsedList(source_id=binding.source_id,group_id=binding.group_id,year=2026,adapter_version=VERSION,
                          kind='archive',complete=True,expected_rows=ROWS,seats=16,source_updated_at=None,
                          entries=tuple(entries),warnings=tuple(warnings))
    except AdapterError:
        raise
    except (ValueError, TypeError, KeyError, InvalidOperation):
        raise AdapterError('invalid_format') from None


def make_adapter(secret: bytes):
    if not isinstance(secret,bytes) or len(secret) < 32:
        raise ValueError('source_identity_key_required')
    def decode(response,binding):
        return parse(response,binding,secret)
    proof = Attestation(passport='docs/sources/sgu-4588.md',fixture='backend/tests/fixtures/sgu-2026/sgu-4588-derived.html',
                        fixture_sha256='09b86aaf9b6d53b3a51008312569545c61c351405951c4b6a135374050bbcefd',
                        original_sha256='e2e8686ed7de4687104aeac64bade4165afd90c354ff2265e869b9cd560906e8',
                        source_url=URL,year=2026,kind='archive',sample_rows=ROWS,checked_rows=ROWS,
                        verified_at=datetime(2026,11,3,tzinfo=timezone.utc),adapter_version=VERSION)
    return Adapter(VERSION,frozenset({'www.sgu.ru'}),decode,attested=True,attestation=proof,max_bytes=8*1024*1024)
