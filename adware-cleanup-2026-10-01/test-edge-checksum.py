import json, hashlib, os

p = os.path.join(os.environ['LOCALAPPDATA'], 'Microsoft', 'Edge', 'User Data', 'Default', 'Bookmarks')
d = json.load(open(p, encoding='utf-8'))
stored = d.get('checksum', '')
roots = d['roots']
print('stored      =', stored)
print('roots keys  =', ','.join(roots.keys()))


def cc(order):
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

    for k in order:
        if k in roots:
            walk(roots[k])
    return md5.hexdigest()


tests = [
    ('bb,other,synced', ['bookmark_bar', 'other', 'synced']),
    ('bb,other,synced,workspaces_v2', ['bookmark_bar', 'other', 'synced', 'workspaces_v2']),
    ('bb,other,workspaces_v2,synced', ['bookmark_bar', 'other', 'workspaces_v2', 'synced']),
    ('workspaces_v2,bb,other,synced', ['workspaces_v2', 'bookmark_bar', 'other', 'synced']),
    ('bb,workspaces_v2,other,synced', ['bookmark_bar', 'workspaces_v2', 'other', 'synced']),
]
for name, order in tests:
    c = cc(order)
    print('%-38s %s %s' % (name, c, '<== MATCH' if c == stored else ''))

# chrome for reference
cp = os.path.join(os.environ['LOCALAPPDATA'], 'Google', 'Chrome', 'User Data', 'Default', 'Bookmarks')
cd = json.load(open(cp, encoding='utf-8'))
print()
print('chrome stored =', cd.get('checksum', ''))
print('chrome roots  =', ','.join(cd['roots'].keys()))
cr = cd['roots']


def cc2(order, r):
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

    for k in order:
        if k in r:
            walk(r[k])
    return md5.hexdigest()


print('chrome calc   =', cc2(['bookmark_bar', 'other', 'synced'], cr))
