import os, shutil, sqlite3, datetime, urllib.parse, json

SRC = os.path.join(os.environ['LOCALAPPDATA'], 'Google', 'Chrome', 'User Data', 'Default', 'History')
TMP = os.path.join(os.environ['TEMP'], 'h3.db')
shutil.copy2(SRC, TMP)
con = sqlite3.connect(TMP)
BASE = datetime.datetime(1601, 1, 1)
KST = datetime.timedelta(hours=9)

pats = ['searchalgorithm', 'tab_open', 'mjbiz', 'rabinoa', 'chatgot', 'hode.co.kr', 'searchconsole', 'helpstart']

print('=== 의심 URL 전체 (긴 형태) ===')
seen = set()
for (u,) in con.execute('select url from urls'):
    if not u or not any(p in u for p in pats):
        continue
    if u in seen:
        continue
    seen.add(u)
    print('-', u)
    # decode shortcut/params if present
    try:
        q = urllib.parse.parse_qs(urllib.parse.urlsplit(u).query)
        for k in ('shortcut', 'data', 'keyword', 'domain', 'app', 'aid', 'custom', 'uid'):
            if k in q:
                print('    [%s] = %s' % (k, q[k][0][:300]))
    except Exception as e:
        print('    (parse fail)', e)
    print()

con.close()
os.remove(TMP)
