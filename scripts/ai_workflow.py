"""Check that maintained TANPHAT ONE source and AI handoff records agree.

This is a local documentation gate, independent of Git history. It does not
execute tests or prove business approval. It never reads credentials or data.
"""
# CLI output and user-facing validation messages are intentional.
# ruff: noqa: T201, EM101
import argparse
import hashlib
import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE_FILE = 'docs/AI_WORKFLOW_STATE.json'
CHECKPOINT_FILE = '.local/ai-workflow/active.json'
REQUIRED_DOCS = ('docs/PROJECT_STATUS.md', 'docs/CHANGELOG.md')
POLICY_DOCS = (
    'AGENTS.md', 'README_TANPHAT.md', 'docs/AI_CHANGE_WORKFLOW.md',
    'docs/ROADMAP.md', 'docs/DECISIONS.md', 'docs/HANDOFF_TEMPLATE.md',
    'docs/architecture/TP_BUSINESS_WORKFLOW.md',
    'docs/architecture/TP_DATABASE_DESIGN.md',
    'docs/architecture/TP_PLATFORM_SOURCE_STRUCTURE.md',
    'docs/architecture/TP_PRODUCT_NAMING.md',
)
CODE_DIRS = ('frontend/src', 'frontend/tests', 'scripts', 'contracts/openapi', 'ops/config')
CODE_FILES = (
    'frontend/index.html', 'frontend/package.json', 'frontend/package-lock.json',
    'frontend/tsconfig.json', 'frontend/vite.config.ts', 'frontend/playwright.config.ts',
    'ops/runtime-baseline.json', 'ops/requirements-tools.txt',
    'ops/requirements-windows-py312.lock.txt',
)
EXTENSIONS = {'.py', '.ps1', '.js', '.ts', '.tsx', '.css', '.html', '.json', '.yaml', '.yml', '.xml', '.csv', '.txt', '.example'}
EXCLUDED_PARTS = {'__pycache__', 'node_modules', 'dist', '.pytest_cache', '.ruff_cache'}
CHANGE_ID = re.compile(r'^CHG-\d{8}-\d{3}$')


def file_hash(path):
    content = path.read_bytes().removeprefix(b'\xef\xbb\xbf').replace(b'\r\n', b'\n')
    return hashlib.sha256(content).hexdigest()


def snapshot(root):
    """Hash only maintained application/tooling code, never runtime or upstream."""
    paths = {root / name for name in CODE_FILES if (root / name).is_file()}
    directories = [root / name for name in CODE_DIRS]
    addons = root / 'custom_addons'
    if addons.exists():
        directories.extend(path for path in addons.iterdir() if path.is_dir() and path.name.startswith('tp_'))
    for directory in directories:
        if directory.exists():
            paths.update(path for path in directory.rglob('*')
                         if path.is_file() and path.suffix.lower() in EXTENSIONS
                         and not EXCLUDED_PARTS.intersection(path.relative_to(root).parts))
    files = {path.relative_to(root).as_posix(): file_hash(path)
             for path in sorted(paths) if not path.is_symlink()}
    digest = hashlib.sha256(json.dumps(files, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    return {'digest': digest, 'file_count': len(files), 'files': files}


def doc_hashes(root):
    return {name: file_hash(root / name) if (root / name).is_file() else None
            for name in (*REQUIRED_DOCS, *POLICY_DOCS)}


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temporary.replace(path)


def start(root):
    path = root / CHECKPOINT_FILE
    if path.exists():
        checkpoint = read_json(path)
        print(f"RESUME: existing change session from {checkpoint['started_at']}. Original checkpoint retained.")
        return
    if any(doc_hashes(root)[name] is None for name in REQUIRED_DOCS):
        raise ValueError('Create PROJECT_STATUS.md and CHANGELOG.md before starting.')
    write_json(path, {
        'started_at': datetime.now(UTC).isoformat(),
        'code': snapshot(root), 'docs': doc_hashes(root),
    })
    print('START: local checkpoint saved. Update status and changelog before finish.')


def finish(root, change_id, checks):
    if not CHANGE_ID.fullmatch(change_id):
        raise ValueError('Change ID must use CHG-YYYYMMDD-NNN.')
    path = root / CHECKPOINT_FILE
    if not path.exists():
        raise ValueError('Run start before editing; an interrupted session can be resumed.')
    checkpoint = read_json(path)
    hashes = doc_hashes(root)
    stale = [name for name in REQUIRED_DOCS if hashes[name] is None or hashes[name] == checkpoint['docs'].get(name)]
    if stale:
        raise ValueError('Update both handoff records after start: ' + ', '.join(stale))
    status = (root / REQUIRED_DOCS[0]).read_text(encoding='utf-8-sig')
    marker = re.search(r'^Last change:\s*`(CHG-\d{8}-\d{3})`\s*$', status, re.MULTILINE)
    if not marker or marker.group(1) != change_id:
        raise ValueError('PROJECT_STATUS.md must contain Last change: `<current change ID>`.')
    changelog = (root / REQUIRED_DOCS[1]).read_text(encoding='utf-8-sig')
    entries = re.findall(r'^## (CHG-\d{8}-\d{3})(?:\s|$)', changelog, re.MULTILINE)
    if len(entries) != len(set(entries)) or entries.count(change_id) != 1:
        raise ValueError('CHANGELOG.md must have exactly one uniquely identified heading for this change.')
    previous = read_json(root / STATE_FILE) if (root / STATE_FILE).exists() else {}
    if previous.get('last_change_id') == change_id:
        raise ValueError('Use a new change ID; do not reuse the last recorded session.')
    if not any(item.strip() for item in checks):
        raise ValueError('Record checks that actually ran, or an explicit reason they did not run.')
    code = snapshot(root)
    write_json(root / STATE_FILE, {
        'schema_version': 1, 'scope_version': 1,
        'updated_at': datetime.now(UTC).isoformat(),
        'last_change_id': change_id, 'code_digest': code['digest'],
        'code_file_count': code['file_count'], 'documentation': hashes,
        'reported_checks': checks,
    })
    path.unlink()
    print(f"FINISH: {change_id}, {code['file_count']} maintained files. Test results are reported, not executed by this tool.")


def check(root):
    path = root / STATE_FILE
    if not path.exists():
        raise ValueError('No workflow baseline. Run start, update status/changelog, then finish.')
    state = read_json(path)
    if state.get('schema_version') != 1 or state.get('scope_version') != 1:
        raise ValueError('Unknown workflow state version. Review the checker and state together.')
    if state.get('code_digest') != snapshot(root)['digest']:
        raise ValueError('Application/tooling code changed after the last handoff. Update documentation and run finish.')
    if state.get('documentation') != doc_hashes(root):
        raise ValueError('Handoff records changed after finish. Record this session before continuing.')
    if (root / CHECKPOINT_FILE).exists():
        raise ValueError('An unfinished change session exists. Resume it and finish the handoff.')
    print(f"PASS: maintained code matches handoff {state['last_change_id']}. Git history and business approval are separate checks.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest='action', required=True)
    subparsers.add_parser('start', help='Capture or resume a local session checkpoint.')
    subparsers.add_parser('check', help='Read-only verification of source and handoff records.')
    end = subparsers.add_parser('finish', help='Record handoff after documentation and tests.')
    end.add_argument('--change-id', required=True)
    end.add_argument('--check', action='append', required=True, dest='checks')
    args = parser.parse_args()
    try:
        if args.action == 'start':
            start(ROOT)
        elif args.action == 'finish':
            finish(ROOT, args.change_id, args.checks)
        else:
            check(ROOT)
    except (ValueError, OSError, KeyError, json.JSONDecodeError) as error:
        print(f'FAIL: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
