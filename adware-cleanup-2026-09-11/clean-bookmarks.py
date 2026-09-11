import os, shutil, json, datetime, re

PF = os.path.join(os.environ['LOCALAPPDATA'], 'Google', 'Chrome', 'User Data', 'Default', 'Bookmarks')
BK = r'C:\Users\orisi\.openclaw\workspace\adware-cleanup-2026-09-11'

stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
shutil.copy2(PF, os.path.join(BK, 'Bookmarks.backup-%s.json' % stamp))
print('backup ->', 'Bookmarks.backup-%s.json' % stamp)

with open(PF, 'r', encoding='utf-8') as f:
    data = json.load(f)

BAD = re.compile(r'xn--o39an|쇼핑바로가기|searchalgorithm|mjbiz\.co\.kr|hode\.co\.kr|chatgot\.co\.kr|'
                 r'helpstart\.co\.kr|helpclean\.co\.kr|searchconsole\.co\.kr|searchcategory\.co\.kr|'
                 r'helpbrowser\.co\.kr|timecheck\.co\.kr|rabinoa|chatopenai\.co\.kr', re.I)

removed = []

def clean(node):
    kids = node.get('children')
    if not kids:
        return
    keep = []
    for ch in kids:
        if ch.get('type') == 'url' and BAD.search(ch.get('url', '') or ''):
            removed.append((ch.get('name'), ch.get('url')))
            continue
        if ch.get('type') == 'folder':
            clean(ch)
        keep.append(ch)
    node['children'] = keep

print()
print('=== 현재 북마크 전체 ===')
def show(node, depth=0):
    for ch in node.get('children', []) or []:
        if ch.get('type') == 'url':
            print('  ' * depth, '-', ch.get('name'), '|', (ch.get('url') or '')[:70])
        else:
            print('  ' * depth, '[', ch.get('name'), ']')
            show(ch, depth + 1)
show(data['roots'])

for root in data['roots'].values():
    if isinstance(root, dict):
        clean(root)

print()
print('=== 삭제한 항목 %d개 ===' % len(removed))
for n, u in removed:
    print('  -', n, '|', u[:90])

if removed:
    data['roots']['bookmark_bar'].setdefault('children', [])
    # update meta so Chrome accepts the file
    data.setdefault('checksum', '')
    with open(PF, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=3)
    print()
    print('Bookmarks 파일 수정 완료')
else:
    print()
    print('삭제 대상 없음 (이미 정리됨)')
