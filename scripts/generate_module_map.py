#!/usr/bin/env python3
import json
from datetime import datetime
from pathlib import Path

ROOT = Path('.')
OUT = Path('results/item_001_module_map.json')

OWNER_BY_PATH = {
    'research_rubric.json': 'orchestrator/researcher',
    'TASK_researcher.md': 'researcher',
    'main.py': 'researcher',
}

PURPOSE_BY_SUFFIX = {
    '.py': 'Python source/script',
    '.md': 'Task or technical documentation',
    '.json': 'Structured data artifact',
    '.png': 'Figure output',
}


def infer_owner(path: Path) -> str:
    if path.as_posix() in OWNER_BY_PATH:
        return OWNER_BY_PATH[path.as_posix()]
    parts = path.parts
    if parts and parts[0] == 'results':
        return 'researcher (experiments)'
    if parts and parts[0] == 'figures':
        return 'researcher (experiments)'
    if parts and parts[0] == 'scripts':
        return 'researcher (tooling)'
    if parts and parts[0] == '.archivara':
        return 'framework/runtime'
    return 'researcher'


def infer_purpose(path: Path) -> str:
    if path.as_posix() == 'results/item_001_module_map.json':
        return 'Repository module map for rubric item_001'
    if path.is_dir():
        return 'Directory container'
    return PURPOSE_BY_SUFFIX.get(path.suffix, 'Project artifact')


def infer_dependencies(path: Path) -> list[str]:
    p = path.as_posix()
    deps = []
    if p.startswith('scripts/'):
        deps.append('research_rubric.json')
    if p.startswith('results/') or p.startswith('figures/'):
        deps.extend(['scripts/*', 'main.py'])
    if p == 'results/item_001_module_map.json':
        deps = ['scripts/generate_module_map.py']
    if p == 'main.py':
        deps.extend(['src/alphago5d/*'])
    return deps


def to_entry(path: Path) -> dict:
    return {
        'path': path.as_posix(),
        'type': 'directory' if (ROOT / path).is_dir() else 'file',
        'purpose': infer_purpose(path),
        'owner_agent': infer_owner(path),
        'dependencies': infer_dependencies(path),
    }


def main() -> None:
    entries = []
    for path in sorted(ROOT.rglob('*')):
        rel = path.relative_to(ROOT)
        if '.git' in rel.parts:
            continue
        entries.append(to_entry(rel))
    if OUT.as_posix() not in {e['path'] for e in entries}:
        entries.append({
            'path': OUT.as_posix(),
            'type': 'file',
            'purpose': infer_purpose(OUT),
            'owner_agent': infer_owner(OUT),
            'dependencies': infer_dependencies(OUT),
        })
    entries.sort(key=lambda e: e['path'])

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        'seed': 42,
        'generated_at': datetime.utcnow().isoformat() + 'Z',
        'total_entries': len(entries),
        'entries': entries,
    }, indent=2) + '\n')


if __name__ == '__main__':
    main()
