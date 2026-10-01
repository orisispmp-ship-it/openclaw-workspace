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


# pass3: OEM bundleware + affiliate links (user approved removal 2026-10-01)
BAD = re.compile(
    r'consroute\.mcafee|AmazonBrowserBar|voxox\.com|shopping\.zum\.com|'
    r'coupa\.ng|halfclub\.com/partner|partner/h_zum|wemakeprice\.com/affiliate',
    re.I)

targets = [
    ('Chrome', os.path.join(os.environ['LOCALAPPDATA'], 'Google', 'Chrome', 'User Data', 'Default', 'Bookmarks')),
    ('Edge', os.path.join(os.environ['LOCALAPPDATA'], 'Microsoft', 'Edge', 'User Data', 'Default', 'Bookmarks')),
]

for label, pf in targets:
    print('=== %s ===' % label)
    if not os.path.exists(pf):
        print('  (no file)')
        continue
    shutil.copy2(pf, os.path.join(BK, '%s-Bookmarks.pass3-%s.json' % (label, stamp)))
    with open(pf, 'r', encoding='utf-8') as f:
        data = json.load(f)

    removed = []

    def scan(node):
        kids = node.get('children')
        if not kids:
            return
        keep = []
        for ch in kids:
            if ch.get('type') == 'folder':
                scan(ch)
                keep.append(ch)
                continue
            nm = ch.get('name') or ''
            url = ch.get('url') or ''
            if BAD.search(url + ' ' + nm):
                removed.append((nm, url))
                continue
            keep.append(ch)
        node['children'] = keep

    for k, v in data['roots'].items():
        if isinstance(v, dict):
            scan(v)

    if removed:
        data['checksum'] = compute_checksum(data['roots'])
        with open(pf, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=3)
        print('  REMOVED %d:' % len(removed))
        for n, u in removed:
            print('   - %s | %s' % (n.encode('unicode_escape').decode(), u))
        with open(pf, 'r', encoding='utf-8') as f:
            chk = json.load(f)
        print('  checksum now: %s (%s)' % (
            chk.get('checksum', ''),
            'MATCH' if chk.get('checksum', '') == compute_checksum(chk['roots']) else 'MISMATCH'))
    else:
        print('  nothing to remove')
