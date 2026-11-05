"""Build a synthetic candidate fixture using public reviewed HTML shape only."""
from html import escape
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def build_fixture(scope):
    p=scope['profile'];output=['<!-- SYNTHETIC CANDIDATE VALUES; no real applicant identifiers or scores -->','<html><head><title>'+escape(dict(p['identity'])['title'])+'</title></head><body><form method="post">']
    for control in scope['controls']:
        output.append('<select id="'+control['id']+'"><option value="'+escape(control['value'],quote=True)+'" selected>'+escape(control['label'])+'</option><option value="other">Other scope</option></select>')
    for selector,text in p['identity']:
        if selector.startswith('#MainContent_'):output.append('<div id="'+selector[1:]+'">'+escape(text)+'</div>')
    output.extend(['<div id="MainContent_divCountPeaple">Количество заявлений - '+str(p['rows'])+' (данные на 1 сентября 2026 г. 12:00)</div>',
        '<input id="cbdogpaid" type="checkbox"><input type="hidden" name="__VIEWSTATE" value="SYNTHETIC-STATE"><table id="rating">'])
    start=0
    for end in (12,16,17):
        output.append('<tr>'+''.join('<th rowspan="'+str(p['header_spans'][i][0])+'" colspan="'+str(p['header_spans'][i][1])+'">'+escape(p['headers'][i])+'</th>' for i in range(start,end))+'</tr>');start=end
    for ordinal in range(1,p['rows']+1):
        cells=['']*p['cell_count'];cells[0]=cells[4]=str(ordinal);cells[2]=str(ordinal) if ordinal<=14 else ''
        cells[3]='<span class="text-secondary">'+str(70000+ordinal)+'/00000000000/'+str(ordinal).zfill(7)+'</span>'
        if ordinal<=14:cells[3]+='<br><span class="text-success">Зачислен (Приказ № 1-2П от 01.09.2026)</span>'
        cells[6]=str(350-ordinal);cells[7]=str(340-ordinal);cells[11]='10';cells[15]='Организация строительного производства';cells[16]='Оплачен' if ordinal<=19 else ''
        output.append('<tr>'+''.join('<td class="'+escape(p['cell_classes'][i],quote=True)+'">'+(value if i==3 else escape(value))+'</td>' for i,value in enumerate(cells))+'</tr>')
    output.append('</table></form></body></html>')
    return ('\n'.join(output)+'\n').encode()


if __name__=='__main__':
    scope=json.loads((ROOT/'docs/sources/bgu2026-scope.json').read_text(encoding='utf-8'))
    path=ROOT/'backend/tests/fixtures/filtered-table/bgu2026-construction.html';path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(build_fixture(scope))
    print('Synthetic fixture written; real candidate rows not copied.')
