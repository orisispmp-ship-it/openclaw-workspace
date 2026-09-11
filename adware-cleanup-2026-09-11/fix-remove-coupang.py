import json, hashlib, os, datetime, shutil

PF = os.path.join(os.environ['LOCALAPPDATA'], 'Google', 'Chrome', 'User Data', 'Default', 'Bookmarks')
BK = r'C:\Users\orisi\.openclaw\workspace\adware-cleanup-2026-09-11'
CHROME_EPOCH = datetime.datetime(1601, 1, 1)

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

def human(da):
    try:
        return (CHROME_EPOCH + datetime.timedelta(microseconds=int(da))).strftime('%Y-%m-%d %H:%M:%S UTC')
    except Exception:
        return str(da)

stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
shutil.copy2(PF, os.path.join(BK, 'Bookmarks.backup-removecoupang2-%s.json' % stamp))
print('backup -> Bookmarks.backup-removecoupang2-%s.json' % stamp)

data = json.load(open(PF, 'r', encoding='utf-8'))
stored = data.get('checksum', '')
calc = compute_checksum(data['roots'])
print('CHECKSUM stored=%s calc=%s => %s' % (stored, calc, 'MATCH' if stored == calc else 'MISMATCH'))

print('=== coupang entries found ===')
def show(node, path=''):
    for ch in node.get('children') or []:
        nm = ch.get('name') or ''
        url = ch.get('url') or ''
        if '쿠팡' in nm or 'coupang.com' in url.lower():
            print('  id=%s name=%s url=%s date_added=%s guid=%s'
                  % (ch.get('id'), nm.encode('unicode_escape').decode(), url, human(ch.get('date_added')), ch.get('guid')))
        if ch.get('children'):
            show(ch, path + '/' + nm)
for k, v in data['roots'].items():
    if isinstance(v, dict):
        show(v, k)

removed = []
def clean(node):
    kids = node.get('children')
    if not kids:
        return
    keep = []
    for ch in kids:
        nm = ch.get('name') or ''
        url = ch.get('url') or ''
        if ch.get('type') == 'url' and ('쿠팡' in nm or 'coupang.com' in url.lower()):
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
    with open(PF, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=3)
    print('removed %d entry(ies)' % len(removed))
    for n, u in removed:
        print('  -', n.encode('unicode_escape').decode(), u)
    print('new checksum =', data['checksum'])
else:
    print('no coupang entry to remove')

chk = json.load(open(PF, 'r', encoding='utf-8'))
print('VERIFY after write: stored=%s calc=%s => %s'
      % (chk.get('checksum', ''), compute_checksum(chk['roots']),
         'MATCH' if chk.get('checksum', '') == compute_checksum(chk['roots']) else 'MISMATCH'))
