"""Versioned templates read only verified scenario facts;no generated percentages."""
from typing import Literal
from .schema_base import CamelModel
from .scenarios import ScenarioResult


class Explanation(CamelModel):
    version:Literal['scenario-explanation-v1']='scenario-explanation-v1'
    summary:str
    basis:list[str]
    limitations:list[str]
    changes:list[str]


REASONS={
 'unsupported_funding':'Для этого платного конкурса сценарий общего бюджета не применяется. Договор и оплата не считаются согласием.',
 'unsupported_category':'Эта категория конкурса не поддержана выбранным сценарием.',
 'missing_or_zero_capacity':'Число мест отсутствует или равно нулю. Положение относительно границы мест не рассчитано.',
 'candidate_not_in_snapshot':'Записи нет в этом снимке. Причина отсутствия не установлена; это не подтверждает отзыв или отказ.',
 'candidate_withdrawn':'В снимке указан отзыв заявления. Условный сценарий для этой записи не рассчитан.',
 'incomplete_official_order':'Порядок или полнота списка не подтверждены. Числовой вывод недоступен.',
 'incomplete_snapshot':'Полнота сохранённого снимка не подтверждена. Числовой вывод недоступен.',
 'unsupported_model_version':'Эта версия сценария не поддерживается. Предыдущие результаты не заменены новым расчётом.',
}
LABELS={'officialRank':'Строка официального списка','score':'Ваши баллы','consent':'Ваше согласие в источнике','priority':'Ваш приоритет','participation':'Статус участия в источнике','present':'Наличие записи','currentLower':'Нижняя граница места при текущих согласиях','currentUpper':'Верхняя граница места при текущих согласиях','allConsentPlace':'Место при согласии всех выше','seats':'Мест в группе','consentYesAbove':'Согласий выше','consentNoAbove':'Без согласия выше','consentUnknownAbove':'Неизвестных согласий выше','withdrawnAbove':'Явно отозванных заявлений выше','state':'Состояние условного сценария','modelVersion':'Версия сценария'}
STATE={'within':'в пределах мест при обоих условиях','conditional':'в пределах только при текущих согласиях','out':'за границей мест','insufficient_data':'недостаточно данных','unsupported':'условия не поддержаны'}
PARTICIPATION={'unknown':'не подтверждён','enrolled':'источник указал зачисление','withdrawn':'источник указал отзыв','active':'участие подтверждено'}


def value(field,item):
    if item is None:return 'неизвестно'
    if isinstance(item,bool):return 'да' if item else 'нет'
    if field=='state':return STATE.get(item,'не поддержано')
    if field=='participation':return PARTICIPATION.get(item,'не подтверждён')
    return str(item)


def explain(result:ScenarioResult,changes):
    n=result.numbers;basis=[]
    if n is None:
        summary=next((REASONS[code] for code in result.reason_codes if code in REASONS),'Недостаточно подтверждённых данных для числового сценария.')
    else:
        current=str(n.current_lower) if n.current_lower==n.current_upper else f'{n.current_lower}–{n.current_upper}'
        summary={
          'within':f'При вашем согласии: условное место {current} из {n.seats} мест. При согласии всех выше — {n.all_consent_place}.',
          'conditional':f'При вашем согласии: условное место {current} из {n.seats} мест. Если все выше подадут согласие — {n.all_consent_place}, за границей мест.',
          'out':f'В этом сценарии даже нижняя граница места {n.current_lower} превышает {n.seats} мест.',
          'insufficient_data':f'Из-за неизвестных согласий условное место лежит между {n.current_lower} и {n.current_upper}; граница — {n.seats} мест. Однозначного вывода нет.',
        }[result.state]
        basis=[f'Выше вас: {n.consent_yes_above} с согласием, {n.consent_no_above} без согласия, {n.consent_unknown_above} с неизвестным согласием.',
               f'Текущая граница: 1 + {n.consent_yes_above} = {n.current_lower}; с неизвестными согласиями — {n.current_upper}.',
               f'При согласии всех учитываемых выше: {n.all_consent_place}. Явно отозванных выше исключено один раз: {n.withdrawn_above}.']
    descriptions=[f"{LABELS[item['field']]}: {value(item['field'],item['before'])} → {value(item['field'],item['after'])}." for item in changes if item['field'] in LABELS]
    return Explanation(summary=summary,basis=basis,limitations=list(result.assumptions),changes=descriptions)
