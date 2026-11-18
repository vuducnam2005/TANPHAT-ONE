"""Check the JS/CSS actually referenced by Odoo, without login or business writes."""
import argparse
import hashlib
import json
import re
import subprocess
import sys
import urllib.request
from pathlib import Path
from urllib.parse import urljoin, urlsplit

ROOT = Path(__file__).resolve().parents[2]


def fetch(url):
    request = urllib.request.Request(url, headers={'Cache-Control': 'no-cache'})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read(), dict(response.headers)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url', required=True)
    parser.add_argument('--output', type=Path, help='Optional JSON evidence file under ignored .local/')
    args = parser.parse_args()
    if urlsplit(args.base_url).scheme not in ('http', 'https'):
        parser.error('--base-url must use http or https')
    if args.output:
        output = args.output.resolve()
        if not output.is_relative_to(ROOT / '.local'):
            parser.error('--output must be inside the repository .local directory')
        ignored = subprocess.run(
            ['git', 'check-ignore', '-q', str(output)], cwd=ROOT, check=False,
        )
        if ignored.returncode:
            parser.error('--output must be ignored by Git')

    bundle_url = urljoin(args.base_url.rstrip('/') + '/', '/web/bundle/web.assets_web')
    raw, _ = fetch(bundle_url)
    assets = []
    checks = {}
    for node in json.loads(raw):
        if node.get('type') not in ('script', 'link'):
            continue
        url = urljoin(bundle_url, node['src'])
        raw, headers = fetch(url)
        text = raw.decode('utf-8')
        kind = 'js' if node['type'] == 'script' else 'css'
        assets.append({
            'kind': kind, 'url': url, 'bytes': len(raw),
            'sha256': hashlib.sha256(raw).hexdigest(),
            'headers': {key: value for key, value in headers.items()
                        if key.lower() in ('cache-control', 'etag', 'last-modified', 'cf-cache-status', 'age')},
        })
        checks[f'{kind}_no_old_handle'] = all(
            token not in text for token in ('tp_hr_handle', 'o_tp_hr_drag_handle')
        )
        if kind == 'js':
            start = text.find("odoo.define('@tp_hr_workspace/table/table'")
            end = text.find('odoo.define(', start + 1) if start >= 0 else -1
            module = text[start:end if end >= 0 else None] if start >= 0 else ''
            checks['js_hr_module_found'] = bool(module)
            checks['js_final_pointerup_bounds'] = all(
                token in module for token in ('lastPointer', 'pointerup', 'getBoundingClientRect', 'isInsideSource')
            )
            checks['js_whole_row_with_control_exclusions'] = (
                '.o_tp_hr_draggable_row' in module and 'contenteditable=true' in module
                and 'ignore:' in module and '.o_list_record_selector' in module
            )
            checks['js_no_old_hit_test'] = 'isPointerInValidZone' not in module
            checks['js_optimistic_employee_order'] = all(
                token in module for token in ('originalRecords', 'departmentList', 'records.splice', 'ordered_ids')
            )
            checks['js_reorder_animation'] = all(
                token in module for token in ('animateEmployeeRows', 'prefers-reduced-motion', 'ROW_SHIFT_MS')
            )
            # Drop glide runs after Owl's patch (onPatched), not in a pre-patch animation frame.
            checks['js_drop_settle_after_patch'] = all(
                token in module for token in ('settleDroppedRow', 'onPatched', 'releaseRect', 'o_tp_hr_row_settling')
            ) and '_tpAnimationFrame' not in module
        else:
            checks['css_whole_row_cursor'] = bool(re.search(
                r'\.o_tp_hr_draggable_row\s*>\s*\.o_data_cell\s*\{[^}]*cursor:\s*grab\s*;', text,
            ))
            checks['css_drop_settle'] = '.o_tp_hr_row_settling' in text
    checks['js_and_css_fetched'] = {asset['kind'] for asset in assets} == {'js', 'css'}
    report = {'bundle_url': bundle_url, 'passed': all(checks.values()), 'checks': checks, 'assets': assets}
    if args.output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    sys.stdout.write(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
