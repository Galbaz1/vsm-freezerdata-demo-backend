#!/usr/bin/env python3
"""Quick verification that Mermaid integration is complete"""
from pathlib import Path

print('Mermaid Integration Verification')
print('=' * 80)

# 1. Check all mermaid files exist
user_facing = Path('features/diagrams_vsm/user_facing')
mermaid_files = list(user_facing.glob('*.mermaid'))
print(f'\n1. User-facing Mermaid files: {len(mermaid_files)} found')
for f in sorted(mermaid_files):
    size = f.stat().st_size
    print(f'   - {f.name} ({size} bytes)')

# 2. Check custom_tools.py has correct implementation
custom_tools = Path('elysia/api/custom_tools.py')
content = custom_tools.read_text()
checks = {
    'Path import': 'from pathlib import Path' in content,
    'show_diagram function': 'async def show_diagram' in content,
    'Filesystem read': 'diagram_file = Path(__file__)' in content,
    'Mermaid code fence': '```mermaid' in content,
    'Response return': 'yield Response(response_text)' in content,
}
print(f'\n2. custom_tools.py checks:')
for check, passed in checks.items():
    status = '✓' if passed else '✗'
    print(f'   {status} {check}: {passed}')

# 3. Check frontend has mermaid
frontend_md = Path('elysia-frontend-main/app/components/chat/components/MarkdownFormat.tsx')
frontend_content = frontend_md.read_text()
frontend_checks = {
    'mermaid import': 'import mermaid from "mermaid"' in frontend_content,
    'MermaidCode component': 'const MermaidCode' in frontend_content,
    'mermaid.render call': 'mermaid.render' in frontend_content,
    'code component mapping': 'code: MermaidCode' in frontend_content,
    'images enabled': 'prose-img:max-w-full' in frontend_content,
}
print(f'\n3. MarkdownFormat.tsx checks:')
for check, passed in frontend_checks.items():
    status = '✓' if passed else '✗'
    print(f'   {status} {check}: {passed}')

# 4. Check package.json
pkg_json = Path('elysia-frontend-main/package.json')
pkg_content = pkg_json.read_text()
print(f'\n4. package.json checks:')
print(f'   ✓ Has mermaid dependency: {"mermaid" in pkg_content}')

# 5. Check static build exists and has mermaid
static_dir = Path('elysia/api/static')
has_static = static_dir.exists() and (static_dir / '_next').exists()
print(f'\n5. Static build checks:')
print(f'   ✓ Static files exist: {has_static}')

# 6. Check if mermaid is bundled
if has_static:
    chunks_dir = static_dir / '_next' / 'static' / 'chunks'
    if chunks_dir.exists():
        # Count files containing 'mermaid'
        import subprocess
        result = subprocess.run(
            ['grep', '-l', 'mermaid', '--include=*.js', '-r', str(chunks_dir)],
            capture_output=True,
            text=True
        )
        mermaid_chunks = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
        print(f'   ✓ Mermaid bundled in {mermaid_chunks} chunk(s)')

all_passed = all([
    len(mermaid_files) == 8,
    all(checks.values()),
    all(frontend_checks.values()),
    has_static,
])

print('\n' + '=' * 80)
if all_passed:
    print('✅ All verification checks passed!')
    print('\nReady to test:')
    print('  1. Start backend: elysia start')
    print('  2. Open browser: http://localhost:8000')
    print('  3. Ask: "Wat is SMIDO?" or use show_diagram tool')
else:
    print('❌ Some checks failed - review above')
print('=' * 80)

