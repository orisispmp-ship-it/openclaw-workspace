import os, shutil, sqlite3, datetime

SRC = os.path.join(os.environ['LOCALAPPDATA'], 'Google', 'Chrome', 'User Data', 'Default', 'History')
TMP = os.path.join(os.environ['TEMP'], 'h4.db')
shutil.copy2(SRC, TMP)
con = sqlite3.connect(TMP)
BASE = datetime.datetime(1601, 1, 1)
KST = datetime.timedelta(hours=9)

def to_dt(ct):
    return BASE + datetime.timedelta(microseconds=ct) + KST

print('=== 가짜 쇼핑바로가기(xn--o39an...) 및 쇼핑몰 접속 시각 (09-09~) ===')
rows = list(con.execute(
    'select v.visit_time, u.url from visits v join urls u on u.id = v.url '
    'where v.visit_time > ? order by v.visit_time',
    (int(((datetime.datetime(2026, 9, 9) - KST) - BASE).total_seconds() * 1_000_000),)))
keys = ['xn--o39an', 'searchalgorithm', 'mjbiz', 'hode.co.kr', 'link.coupang', 'www.coupang', 'mc.coupang',
        'checkout.coupang', 'smartbridge', 'rabinoa', 'helpstart', 'gotosearchresult']
after = int(((datetime.datetime(2026, 9, 11, 11, 13) - KST) - BASE).total_seconds() * 1_000_000)
for vt, url in rows:
    if any(k in (url or '') for k in keys):
        mark = '  <-- 11:13 제거 이후' if vt > after else ''
        print(' ', to_dt(vt).strftime('%m-%d %H:%M:%S'), '|', (url or '')[:95], mark)
con.close()
os.remove(TMP)
