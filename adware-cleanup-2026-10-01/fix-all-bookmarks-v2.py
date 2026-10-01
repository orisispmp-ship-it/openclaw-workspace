import json, hashlib, os, shutil, datetime, re, subprocess

BK = r'C:\Users\orisi\.openclaw\workspace\adware-cleanup-2026-10-01'
stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')


def root_order(roots):
    """Chromium order: bookmark_bar, other, synced, then any extra roots (Edge: workspaces_v2)."""
    base = [k for k in ('bookmark_bar', 'other', 'synced') if k in roots]
    extra = [k for k in roots.keys() if k not in ('bookmark_bar', 'other', 'synced')]
    return base + extra


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

    for key in root_order(roots):
        walk(roots[key])
    return md5.hexdigest()


BAD = re.compile(
    r'socialfriendsinc|shortcuticon\.net|planbplus|xn--|smartbridge|searchalgorithm|mjbiz\.co\.kr|쇼핑바로가기|'
    r'consroute\.mcafee|AmazonBrowserBar|voxox\.com|shopping\.zum\.com|coupa\.ng|'
    r'halfclub\.com/partner|partner/h_zum|wemakeprice\.com/affiliate',
    re.I)

TARGETS = [
    ('Chrome', 'chrome', os.path.join(os.environ['LOCALAPPDATA'], 'Google', 'Chrome', 'User Data', 'Default', 'Bookmarks')),
    ('Edge', 'msedge', os.path.join(os.environ['LOCALAPPDATA'], 'Microsoft', 'Edge', 'User Data', 'Default', 'Bookmarks')),
]

running = []
for label, proc, pf in TARGETS:
    try:
        n = len(subprocess.run(['powershell', '-NoProfile', '-Command',
                                "(Get-Process %s -ErrorAction SilentlyContinue | Measure-Object).Count" % proc],
                               capture_output=True, text=True, timeout=30).stdout.strip())
    except Exception:
        n = 0
    print('%s processes running: %s' % (label, n))

print()

for label, proc, pf in TARGETS:
    print('=== %s ===' % label)
    if not os.path.exists(pf):
        print('  (no file)')
        continue
    shutil.copy2(pf, os.path.join(BK, '%s-Bookmarks.v2-before-%s.json' % (label, stamp)))
    with open(pf, 'r', encoding='utf-8') as f:
        data = json.load(f)

    stored = data.get('checksum', '')
    calc = compute_checksum(data['roots'])
    print('  BEFORE checksum: stored=%s calc=%s -> %s' % (stored, calc, 'MATCH' if stored == calc else 'MISMATCH'))
    print('  roots: %s' % ','.join(root_order(data['roots'])))

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
        ok = chk.get('checksum', '') == compute_checksum(chk['roots'])
        print('  AFTER checksum: %s -> %s' % (chk.get('checksum', ''), 'MATCH' if ok else 'MISMATCH'))
    else:
        print('  nothing to remove')
