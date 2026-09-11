import os, shutil, json, datetime, re

PF = os.path.join(os.environ['LOCALAPPDATA'], 'Google', 'Chrome', 'User Data', 'Default', 'Bookmarks')
BK = r'C:\Users\orisi\.openclaw\workspace\adware-cleanup-2026-09-11'

stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
shutil.copy2(PF, os.path.join(BK, 'Bookmarks.backup-removecoupang-%s.json' % stamp))
print('backup -> Bookmarks.backup-removecoupang-%s.json' % stamp)

with open(PF, 'r', encoding='utf-8') as f:
    data = json.load(f)

BAD = re.compile(r'coupang\.com|쿠팡', re.I)

removed = []

def clean(node):
    kids = node.get('children')
    if not kids:
        return
    keep = []
    for ch in kids:
        name = ch.get('name') or ''
        url = ch.get('url') or ''
        if ch.get('type') == 'url' and BAD.search(url + ' ' + name):
            removed.append((name, url))
            continue
        if ch.get('type') == 'folder':
            clean(ch)
        keep.append(ch)
    node['children'] = keep

for root in data['roots'].values():
    if isinstance(root, dict):
        clean(root)

print('removed count = %d' % len(removed))
for n, u in removed:
    print('  -', n.encode('unicode_escape').decode(), '|', u)

if removed:
    data.setdefault('checksum', '')
    with open(PF, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=3)
    print('Bookmarks file rewritten (checksum cleared)')
else:
    print('nothing to remove')
