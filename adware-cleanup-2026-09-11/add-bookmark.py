import json, hashlib, os, uuid, datetime, shutil, sys

PF = os.path.join(os.environ['LOCALAPPDATA'], 'Google', 'Chrome', 'User Data', 'Default', 'Bookmarks')
BK = r'C:\Users\orisi\.openclaw\workspace\adware-cleanup-2026-09-11'

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

# --- 1) validate algorithm against files Chrome itself wrote ---
print('=== checksum algorithm validation ===')
for label, path in [
        ('original backup (9 bookmarks)', os.path.join(BK, 'Bookmarks.backup-20260911-195844.json')),
        ('current file (Chrome-written, 7 bookmarks)', PF)]:
    data = json.load(open(path, 'r', encoding='utf-8'))
    stored = data.get('checksum', '')
    calc = compute_checksum(data['roots'])
    print('  %-42s stored=%s calc=%s  %s' % (label, stored, calc, 'MATCH' if stored == calc else 'MISMATCH'))

# --- 2) add the Coupang bookmark ---
data = json.load(open(PF, 'r', encoding='utf-8'))
shutil.copy2(PF, os.path.join(BK, 'Bookmarks.before-add-%s.json'
                              % datetime.datetime.now().strftime('%Y%m%d-%H%M%S')))

def all_ids(node, acc):
    if node.get('id'):
        acc.append(int(node['id']))
    for ch in node.get('children') or []:
        all_ids(ch, acc)

ids = []
for k, v in data['roots'].items():
    if isinstance(v, dict):
        all_ids(v, ids)
new_id = max(ids) + 1

CHROME_EPOCH = datetime.datetime(1601, 1, 1)
now_ct = int((datetime.datetime.utcnow() - CHROME_EPOCH).total_seconds() * 1_000_000)

node = {
    "date_added": str(now_ct),
    "date_last_used": "0",
    "guid": str(uuid.uuid4()),
    "id": str(new_id),
    "meta_info": {"power_bookmark_meta": ""},
    "name": "쿠팡",
    "type": "url",
    "url": "https://www.coupang.com/",
}
data['roots']['bookmark_bar'].setdefault('children', []).append(node)

data['checksum'] = compute_checksum(data['roots'])

before = open(PF, 'rb').read()
with open(PF, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=3)
after = open(PF, 'rb').read()

print()
print('=== added bookmark ===')
print('  name :', node['name'])
print('  url  :', node['url'])
print('  id   :', node['id'], '(max was', max(ids), ')')
print('  guid :', node['guid'])
print('  new checksum :', data['checksum'])
print('  file written :', len(before), '->', len(after), 'bytes')

# --- 3) re-read and verify ---
chk = json.load(open(PF, 'r', encoding='utf-8'))
names = [c.get('name') for c in chk['roots']['bookmark_bar'].get('children', [])]
print()
print('=== bookmark bar now ===')
for n in names:
    print('  -', n)
print('  checksum stored =', chk.get('checksum'))
