"""Validate executed automated auth evidence; never accept external release gates."""
import argparse
import json
from pathlib import Path
import xml.etree.ElementTree as ET


ENGINES = ('chromium', 'firefox', 'webkit')


def validate(matrix, backend_xml, browser_root):
    cases = list(ET.parse(backend_xml).iter('testcase'))
    if len(cases) < matrix['minimumBackendTests']:
        raise ValueError('Incomplete backend regression evidence')
    if any(case.find(tag) is not None for case in cases for tag in ('failure', 'error', 'skipped')):
        raise ValueError('Backend evidence contains failures/errors/skips')
    for control in matrix['automated']:
        for selector in control['tests']:
            path, function = selector.split('::')
            module = Path(path).stem
            if not any(case.get('classname', '').split('.')[-1] == module and
                       (case.get('name') == function or case.get('name', '').startswith(function+'[')) for case in cases):
                raise ValueError(f"Missing executed control: {control['id']}")
    browsers = {}
    for engine in ENGINES:
        report = json.loads((Path(browser_root)/engine/'results.json').read_text())
        stats = report['stats']
        if (stats['expected'] < matrix['minimumBrowserTests'] or report.get('errors')
                or any(stats.get(key, 0) for key in ('unexpected', 'flaky', 'skipped'))):
            raise ValueError(f'Incomplete or failing browser evidence: {engine}')
        browsers[engine] = {'passed': stats['expected'], 'skipped': 0}
    return {'scope': 'automated-acceptance-only', 'backendPassed': len(cases),
            'automatedControlsVerified': len(matrix['automated']), 'browsers': browsers,
            'productionReady': False, 'externalGates': matrix['externalGates']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--matrix', type=Path, default=Path('docs/evidence/kan-214-controls.json'))
    parser.add_argument('--backend-junit', type=Path, required=True)
    parser.add_argument('--browser-results', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        result = validate(json.loads(args.matrix.read_text()), args.backend_junit, args.browser_results)
    except (ValueError, KeyError, OSError, ET.ParseError) as error:
        # Never dump report contents: they can include failed-test request context.
        raise SystemExit('Automated auth acceptance evidence is incomplete or unsuccessful.') from error
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print(f"Automated controls verified: {result['automatedControlsVerified']}; production gates NOT accepted.")


if __name__ == '__main__':
    main()
