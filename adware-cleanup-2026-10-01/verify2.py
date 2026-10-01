import json, hashlib, os, re, datetime


def root_order(roots):
    base = [k for k in ('bookmark_bar', 'other', 'synced') if k in roots]
    extra = [k for k in roots.keys() if k not in ('bookmark_bar', 'other', 'synced')]
    return base + extra


def cc(roots):
    md5 = hashlib.md5()

    def walk(n):
        md5.update(str(n.get('id', '')).encode('utf-8'))
        md5.update((n.get('name') or '').encode('utf-16-le'))
        if n.get('type') == 'url':
            md5.update(b'url')
            md5.update((n.get('url') or '').encode('utf-8'))
        else:
            md5.update(b'folder')
            for c in n.get('children') or []:
                walk(c)

    for k in root_order(roots):
        walk(roots[k])
    return md5.hexdigest()


BAD = re.compile(
    r'xn--|socialfriendsinc|shortcuticon|planbplus|smartbridge|searchalgorithm|mjbiz|쇼핑바로가기|'
    r'consroute|AmazonBrowserBar|voxox|shopping\.zum|coupa\.ng|halfclub|wemakeprice\.com/affiliate',
    re.I)

for label, p in [
    ('Chrome', os.path.join(os.environ['LOCALAPPDATA'], 'Google', 'Chrome', 'User Data', 'Default', 'Bookmarks')),
    ('Edge', os.path.join(os.environ['LOCALAPPDATA'], 'Microsoft', 'Edge', 'User Data', 'Default', 'Bookmarks')),
]:
    if not os.path.exists(p):
        print(label + ': no file')
        continue
    with open(p, 'r', encoding='utf-8') as f:
        d = json.load(f)
    hits = []

    def scan(n):
        for c in n.get('children') or []:
            if c.get('type') == 'folder':
                scan(c)
            else:
                t = (c.get('url') or '') + ' ' + (c.get('name') or '')
                if BAD.search(t):
                    hits.append((c.get('name'), c.get('url')))

    for k, v in d['roots'].items():
        if isinstance(v, dict):
            scan(v)
    stored = d.get('checksum', '')
    calc = cc(d['roots'])
    print('%s: mtime=%s' % (label, datetime.datetime.fromtimestamp(os.path.getmtime(p)).strftime('%H:%M:%S')))
    print('   checksum stored=%s calc=%s -> %s' % (stored, calc, 'MATCH' if stored == calc else 'MISMATCH'))
    print('   suspicious = %d' % len(hits))
    for n, u in hits[:12]:
        print('     - %s | %s' % (n.encode('unicode_escape').decode(), u))
