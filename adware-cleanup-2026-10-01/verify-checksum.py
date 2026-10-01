import json, hashlib, os

def cc(roots):
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

for label, p in [
    ('Chrome', os.path.join(os.environ['LOCALAPPDATA'], 'Google', 'Chrome', 'User Data', 'Default', 'Bookmarks')),
    ('Edge', os.path.join(os.environ['LOCALAPPDATA'], 'Microsoft', 'Edge', 'User Data', 'Default', 'Bookmarks')),
]:
    if not os.path.exists(p):
        print(label, 'no file')
        continue
    with open(p, 'r', encoding='utf-8') as f:
        d = json.load(f)
    stored = d.get('checksum', '')
    calc = cc(d['roots'])
    print('%s: stored=%s calc=%s -> %s' % (label, stored, calc, 'MATCH' if stored == calc else 'MISMATCH'))
    print('   roots keys: %s' % ','.join(d.get('roots', {}).keys()))
    print('   top-level keys: %s' % ','.join(sorted(d.keys())))
