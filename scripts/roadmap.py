"""Validate the persistent plan and render its human-readable task cards.

Uses only Python's standard library. Does not change task statuses or run app code.
"""
import argparse
import copy
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'docs'
STATUSES = {'todo', 'in_progress', 'review', 'done', 'blocked', 'deferred'}


def read_json(name):
    return json.loads((DOCS / name).read_text(encoding='utf-8'))


def local_path(value):
    path = (ROOT / value).resolve()
    if not path.is_relative_to(ROOT):
        raise ValueError(f'Path outside project: {value}')
    return path


def validate(data, state):
    errors = []
    if data.get('schemaVersion') != 1 or state.get('schemaVersion') != 1:
        errors.append('Unsupported schemaVersion')
    tasks = data.get('tasks', [])
    phases = {p['id'] for p in data.get('phases', [])}
    ids = [task.get('id') for task in tasks]
    if len(ids) != len(set(ids)):
        errors.append('Duplicate task IDs')
    by_id = {task.get('id'): task for task in tasks}
    for task in tasks:
        task_id = task.get('id', '?')
        if not re.fullmatch(r'T\d{3}', str(task_id)):
            errors.append(f'Invalid task ID: {task_id}')
        for field in ('title', 'steps', 'acceptance', 'deliverables'):
            if not task.get(field):
                errors.append(f'{task_id}: missing {field}')
        for field in ('steps', 'acceptance', 'deliverables', 'dependsOn', 'evidence'):
            if not isinstance(task.get(field), list):
                errors.append(f'{task_id}: {field} must be a list')
        if task.get('phase') not in phases:
            errors.append(f'{task_id}: unknown phase')
        if task.get('priority') not in {'P0', 'P1', 'P2'} or task.get('size') not in {'S', 'M', 'L'}:
            errors.append(f'{task_id}: invalid priority or size')
        if task.get('status') not in STATUSES:
            errors.append(f'{task_id}: unknown status')
        if task.get('status') in {'blocked', 'deferred'} and not task.get('blockedReason'):
            errors.append(f'{task_id}: blocked/deferred needs a reason and resumption condition')
        for dependency in task.get('dependsOn', []):
            if dependency not in by_id:
                errors.append(f'{task_id}: missing dependency {dependency}')
            elif task.get('status') in {'in_progress', 'review', 'done'} and by_id[dependency]['status'] != 'done':
                errors.append(f'{task_id}: dependency {dependency} is not done')
        if task.get('status') == 'done' and not task.get('evidence'):
            errors.append(f'{task_id}: done requires evidence')
        for item in task.get('evidence', []):
            try:
                if not item.get('note') or not local_path(item['path']).is_file():
                    errors.append(f'{task_id}: missing evidence file or note')
            except (ValueError, KeyError) as error:
                errors.append(f'{task_id}: invalid evidence: {error}')

    visiting, visited = set(), set()

    def visit(task_id):
        if task_id in visiting:
            errors.append(f'Dependency cycle at {task_id}')
            return
        if task_id in visited or task_id not in by_id:
            return
        visiting.add(task_id)
        for dependency in by_id[task_id].get('dependsOn', []):
            visit(dependency)
        visiting.remove(task_id)
        visited.add(task_id)

    for task_id in ids:
        visit(task_id)
    active = [task['id'] for task in tasks if task['status'] == 'in_progress']
    if len(active) > 1:
        errors.append('More than one in_progress task')
    if active != ([state['currentTask']] if state.get('currentTask') else []):
        errors.append('STATE.currentTask does not match in_progress task')
    next_id = state.get('nextTask')
    if next_id:
        if next_id not in by_id:
            errors.append('STATE.nextTask does not exist')
        elif by_id[next_id]['status'] in {'done', 'blocked', 'deferred'}:
            errors.append('STATE.nextTask is not actionable')
        elif any(by_id.get(dep, {}).get('status') != 'done' for dep in by_id[next_id]['dependsOn']):
            errors.append('STATE.nextTask has unfinished dependencies')
    gates = data.get('gates', [])
    gate_ids = [gate['id'] for gate in gates]
    if len(gate_ids) != len(set(gate_ids)):
        errors.append('Duplicate gate IDs')
    for gate in gates:
        if not gate.get('tasks'):
            errors.append(f'{gate["id"]}: empty gate')
        for task_id in gate.get('tasks', []):
            if task_id not in by_id:
                errors.append(f'{gate["id"]}: missing task {task_id}')
    completed = state.get('completedGates', [])
    if completed != gate_ids[:len(completed)]:
        errors.append('Completed gates must be a sequential prefix of G0…G6')
    for gate in gates:
        if gate['id'] in completed and any(by_id.get(task_id, {}).get('status') != 'done' for task_id in gate['tasks']):
            errors.append(f'{gate["id"]}: declared complete with unfinished tasks')
    if not state.get('resumeAction') or not state.get('lastSession'):
        errors.append('STATE needs resumeAction and lastSession')
    return errors


def render(data):
    lines = ['# Карточки задач', '',
             'Генерируется из [TASKS.json](TASKS.json) командой `python scripts/roadmap.py --render`. Не редактировать вручную.', '',
             'Общие требования для каждой задачи: [Definition of Done](QUALITY.md), [правила расчёта](DATA_RULES.md), [протокол работы](RUNBOOK.md).', '',
             'Пути результатов ниже — планируемые файлы; их наличие и готовность подтверждаются статусом и evidence, а не этой таблицей.', '']
    for phase in data['phases']:
        lines += [f'## {phase["id"]}. {phase["title"]}', '', f'Плановый интервал: {phase["window"]}.', '']
        for task in data['tasks']:
            if task['phase'] != phase['id']:
                continue
            lines += [f'### {task["id"]}. {task["title"]}', '',
                      f'**Статус:** `{task["status"]}` · **Приоритет:** {task["priority"]} · **Размер:** {task["size"]}.', '',
                      '**Зависимости:** ' + (', '.join(task['dependsOn']) or 'нет') + '.', '',
                      '**Результаты/файлы:** ' + '; '.join(f'`{path}`' for path in task['deliverables']) + '.', '', '**Шаги:**', '']
            lines += [f'{i}. {step}.' for i, step in enumerate(task['steps'], 1)]
            lines += ['', '**Критерии закрытия:**', '']
            lines += [f'- {item}.' for item in task['acceptance']]
            lines += ['- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.', '', '**Доказательства:**', '']
            lines += [f'- [{item["path"]}](../{item["path"]}) — {item["note"]}' for item in task['evidence']] or ['Пока нет.']
            if task.get('blockedReason'):
                lines += ['', '**Причина блокировки/переноса:** ' + task['blockedReason']]
            lines += ['']
    return '\n'.join(lines).rstrip() + '\n'


def render_checklist(data):
    done = sum(task['status'] == 'done' for task in data['tasks'])
    lines = ['# Чек-лист AdmitFlow', '',
             '`[x]` — сделано и проверено. `[ ]` — ещё не завершено.', '',
             f'**Закрыто {done} из {len(data["tasks"])} задач.** Это счёт задач, не процент готовности продукта.', '',
             'Частично реализованные пункты остаются без галочки. Последний раздел относится к развитию после MVP.', '',
             'Подробности и доказательства: [карточки задач](docs/TASKS.md). '
             'Файл обновляется из `docs/TASKS.json` командой `python scripts/roadmap.py --render`.', '']
    labels = {'in_progress': ' — **в работе**', 'review': ' — **нужна проверка / завершение**',
              'blocked': ' — **заблокировано**', 'deferred': ' — отложено'}
    for phase in data['phases']:
        lines += [f'## {phase["title"]}', '']
        for task in data['tasks']:
            if task['phase'] == phase['id']:
                mark = 'x' if task['status'] == 'done' else ' '
                lines.append(f'- [{mark}] {task["id"]} {task["title"]}{labels.get(task["status"], "")}')
        lines.append('')
    return '\n'.join(lines).rstrip() + '\n'


def check_links():
    errors = []
    for path in [ROOT / 'README.md', *DOCS.rglob('*.md')]:
        for raw in re.findall(r'\[[^\]]*\]\(([^)]+)\)', path.read_text(encoding='utf-8')):
            target = raw.strip('<>').split('#', 1)[0]
            if not target or re.match(r'^[a-z]+:', target, re.I):
                continue
            resolved = (path.parent / target).resolve()
            if not resolved.exists():
                errors.append(f'Broken local link in {path.relative_to(ROOT)}: {raw}')
    return errors


def self_test(data, state):
    # Build a stable test baseline even when real tasks/gates are completed later.
    data, state = copy.deepcopy(data), copy.deepcopy(state)
    for task in data['tasks']:
        task['status'] = 'done' if task['id'] == 'T001' else 'todo'
    state.update(currentTask=None, nextTask='T002', completedGates=[])
    cases = []
    changed = copy.deepcopy(data)
    changed['tasks'].append(copy.deepcopy(changed['tasks'][0]))
    cases.append(('duplicate ID', changed, state, 'Duplicate task'))
    changed = copy.deepcopy(data)
    changed['tasks'][0]['dependsOn'] = ['T002']
    cases.append(('cycle', changed, state, 'Dependency cycle'))
    changed = copy.deepcopy(data)
    changed['tasks'][0]['evidence'] = []
    cases.append(('done without proof', changed, state, 'done requires evidence'))
    changed = copy.deepcopy(data)
    changed['tasks'][1]['dependsOn'] = ['T999']
    cases.append(('missing dependency', changed, state, 'missing dependency'))
    changed_state = copy.deepcopy(state)
    changed_state['completedGates'] = ['G0']
    cases.append(('false gate', data, changed_state, 'declared complete'))
    changed_state = copy.deepcopy(state)
    changed_state['nextTask'] = 'T001'
    cases.append(('completed next task', data, changed_state, 'not actionable'))
    for name, candidate, candidate_state, expected in cases:
        assert any(expected in error for error in validate(candidate, candidate_state)), name
    print(f'Self-test: {len(cases)} invalid states correctly rejected.')


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--render', action='store_true')
    parser.add_argument('--next', action='store_true')
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    data, state = read_json('TASKS.json'), read_json('STATE.json')
    errors = validate(data, state)
    if errors:
        print('\n'.join('ERROR: ' + error for error in errors))
        return 1
    expected = render(data)
    target = DOCS / 'TASKS.md'
    checklist = ROOT / 'CHECKLIST.md'
    expected_checklist = render_checklist(data)
    if args.render:
        target.write_text(expected, encoding='utf-8')
        checklist.write_text(expected_checklist, encoding='utf-8')
        print('Rendered docs/TASKS.md')
        print('Rendered CHECKLIST.md')
    if args.check or not any(vars(args).values()):
        errors = check_links()
        if not target.exists() or target.read_text(encoding='utf-8') != expected:
            errors.append('TASKS.md is stale or missing; run --render')
        if not checklist.exists() or checklist.read_text(encoding='utf-8') != expected_checklist:
            errors.append('CHECKLIST.md is stale or missing; run --render')
        if state['lastSession'] not in (DOCS / 'LOG.md').read_text(encoding='utf-8'):
            errors.append('STATE.lastSession is missing from LOG.md')
        if errors:
            print('\n'.join('ERROR: ' + error for error in errors))
            return 1
        counts = Counter(task['status'] for task in data['tasks'])
        print(f'Plan valid: {len(data["tasks"])} tasks, {len(data["gates"])} gates; statuses={dict(counts)}')
        print('Structure and evidence-file existence checked; correctness of application tests is not inferred.')
    if args.next:
        by_id = {task['id']: task for task in data['tasks']}
        print(f'Current: {state["currentTask"] or "none"}; next: {state["nextTask"]}')
        print(state['resumeAction'])
        ready = [task for task in data['tasks'] if task['status'] == 'todo' and all(by_id[dep]['status'] == 'done' for dep in task['dependsOn'])]
        for task in sorted(ready, key=lambda item: (item['priority'], item['id']))[:8]:
            print(f'Available {task["id"]} [{task["priority"]}]: {task["title"]}')
    if args.self_test:
        self_test(data, state)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
