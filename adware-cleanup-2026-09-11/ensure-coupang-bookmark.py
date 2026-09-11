import json, hashlib, os, uuid, datetime, shutil, sys

PF = (sys.argv[1] if len(sys.argv) > 1 else
      os.path.join(os.environ['LOCALAPPDATA'], 'Google', 'Chrome', 'User Data', 'Default', 'Bookmarks'))
BK = r'C:\Users\orisi\.openclaw\workspace\adware-cleanup-2026-09-11'
TARGET = '쿠팡'
URL = 'https://www.coupang.com/'

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

data = json.load(open(PF, 'r', encoding='utf-8'))

# idempotent: already there?
def has(node):
    if node.get('type') == 'url' and (node.get('url') or '').rstrip('/') == URL.rstrip('/'):
        return True
    return any(has(c) for c in node.get('children') or [])

if any(has(v) for v in data['roots'].values() if isinstance(v, dict)):
    print('ALREADY_PRESENT  (nothing to do)')
    sys.exit(0)

def all_ids(node, acc):
    if node.get('id'):
        acc.append(int(node['id']))
    for ch in node.get('children') or []:
        all_ids(ch, acc)

ids = []
for v in data['roots'].values():
    if isinstance(v, dict):
        all_ids(v, ids)

stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
if len(sys.argv) <= 1:
    shutil.copy2(PF, os.path.join(BK, 'Bookmarks.before-add-%s.json' % stamp))

CHROME_EPOCH = datetime.datetime(1601, 1, 1)
now_ct = int((datetime.datetime.utcnow() - CHROME_EPOCH).total_seconds() * 1_000_000)

node = {
    "date_added": str(now_ct),
    "date_last_used": "0",
    "guid": str(uuid.uuid4()),
    "id": str(max(ids) + 1),
    "meta_info": {"power_bookmark_meta": ""},
    "name": TARGET,
    "type": "url",
    "url": URL,
}
data['roots']['bookmark_bar'].setdefault('children', []).append(node)
data['checksum'] = compute_checksum(data['roots'])

with open(PF, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=3)

chk = json.load(open(PF, 'r', encoding='utf-8'))
ok = any(has(v) for v in chk['roots'].values() if isinstance(v, dict))
n = len([c for c in chk['roots']['bookmark_bar'].get('children', [])])
print('ADDED id=%s  verify=%s  bookmark_bar_count=%d  checksum_ok=%s'
      % (node['id'], ok, n, compute_checksum(chk['roots']) == chk.get('checksum')))
