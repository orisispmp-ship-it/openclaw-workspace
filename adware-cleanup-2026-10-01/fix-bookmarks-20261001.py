import json, hashlib, os, shutil, datetime, re

BK = r'C:\Users\orisi\.openclaw\workspace\adware-cleanup-2026-10-01'
stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')


def compute_checksum(roots):
    md5 = hashlib.md5()

    def walk(node):
        md5.update(str(node.get('id', '')).encode('utf-8'))
        md5.update((node.get('name') or '').encode('utf-16-le'))
        if node.get('type') == 'url':
            md5.update(b'url')
            md5.update((node.get('url') or '').encode('utf-8'))
        else:
            md5.update(b'folder')
            for ch in node.get('children') or []:
                walk(ch)

    for key in ('bookmark_bar', 'other', 'synced'):
        if key in roots:
            walk(roots[key])
    return md5.hexdigest()


BAD = re.compile(r'xn--o39|searchalgorithm|mjbiz\.co\.kr|hode\.co\.kr|쇼핑바로가기|clipdown|smartbridge', re.I)

targets = [
    ('Chrome', os.path.join(os.environ['LOCALAPPDATA'], 'Google', 'Chrome', 'User Data', 'Default', 'Bookmarks')),
    ('Edge', os.path.join(os.environ['LOCALAPPDATA'], 'Microsoft', 'Edge', 'User Data', 'Default', 'Bookmarks')),
]

for label, pf in targets:
    print('=== %s ===' % label)
    if not os.path.exists(pf):
        print('  (no file)')
        continue
    shutil.copy2(pf, os.path.join(BK, '%s-Bookmarks.before-%s.json' % (label, stamp)))
    with open(pf, 'r', encoding='utf-8') as f:
        data = json.load(f)
    stored = data.get('checksum', '')
    calc = compute_checksum(data['roots'])
    print('  checksum %s vs %s -> %s' % (stored, calc, 'MATCH' if stored == calc else 'MISMATCH'))

    removed = []

    def clean(node):
        kids = node.get('children')
        if not kids:
            return
        keep = []
        for ch in kids:
            nm = ch.get('name') or ''
            url = ch.get('url') or ''
            if ch.get('type') == 'url' and BAD.search(url + ' ' + nm):
                removed.append((nm, url))
                continue
            if ch.get('type') == 'folder':
                clean(ch)
            keep.append(ch)
        node['children'] = keep

    for k, v in data['roots'].items():
        if isinstance(v, dict):
            clean(v)

    if removed:
        data['checksum'] = compute_checksum(data['roots'])
        with open(pf, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=3)
        print('  removed %d:' % len(removed))
        for n, u in removed:
            print('   - %s | %s' % (n.encode('unicode_escape').decode(), u))
        print('  new checksum = %s' % data['checksum'])
    else:
        print('  nothing to remove')

    with open(pf, 'r', encoding='utf-8') as f:
        chk = json.load(f)
    print('  VERIFY: stored=%s calc=%s -> %s' % (
        chk.get('checksum', ''), compute_checksum(chk['roots']),
        'MATCH' if chk.get('checksum', '') == compute_checksum(chk['roots']) else 'MISMATCH'))
