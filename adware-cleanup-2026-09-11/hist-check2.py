import os, shutil, sqlite3, datetime, collections
from urllib.parse import urlsplit

SRC = os.path.join(os.environ['LOCALAPPDATA'], 'Google', 'Chrome', 'User Data', 'Default', 'History')
TMP = os.path.join(os.environ['TEMP'], 'hist_copy2.db')
shutil.copy2(SRC, TMP)
con = sqlite3.connect(TMP)

BASE = datetime.datetime(1601, 1, 1)
KST = datetime.timedelta(hours=9)

def to_dt(ct):
    return BASE + datetime.timedelta(microseconds=ct) + KST

def to_ct(dt_kst):
    return int(((dt_kst - KST) - BASE).total_seconds() * 1_000_000)

MALLS = ['coupang', '11st', 'gmarket', 'auction.co.kr', 'wemakeprice', 'tmon', 'interpark', 'ssg.com',
         'lotteon', 'lotteimall', 'emart', 'hmall', 'akmall', 'danawa', 'yes24', 'cjmall', 'gsshop',
         'funshop', 'zerogram', 'k-tank', 'timemecca', 'smartstore']

start = to_ct(datetime.datetime(2026, 9, 9, 0, 0, 0))
rows = list(con.execute(
    'select v.visit_time, u.url from visits v join urls u on u.id = v.url where v.visit_time > ? order by v.visit_time',
    (start,)))
print('총 방문 레코드(09-09 이후):', len(rows))

print()
print('=== 09-09 ~ 09-11 쇼핑몰 URL 방문 ===')
m = [(to_dt(vt), url) for vt, url in rows if any(k in (url or '').lower() for k in MALLS)]
for tt, url in m:
    print('  ' + tt.strftime('%m-%d %H:%M:%S'), '|', url[:100])
print('  총 %d건' % len(m))

print()
print('=== 일자별 쇼핑몰 방문 요약 ===')
for day in ('09-09', '09-10', '09-11'):
    dd = [(tt, url) for tt, url in m if tt.strftime('%m-%d') == day]
    if dd:
        print('  %s : %d건, 처음 %s ~ 마지막 %s' % (day, len(dd), dd[0][0].strftime('%H:%M'), dd[-1][0].strftime('%H:%M')))
    else:
        print('  %s : 0건' % day)

print()
print('=== 09-11 시간대별 전체 방문 건수 (KST) ===')
per_hour = collections.Counter()
for vt, url in rows:
    tt = to_dt(vt)
    if tt.strftime('%m-%d') == '09-11':
        per_hour[tt.strftime('%H')] += 1
for h in sorted(per_hour):
    print('  %s시 : %3d건 %s' % (h, per_hour[h], '#' * min(per_hour[h], 60)))

print()
print('=== 11:13 제거 이후 방문한 도메인 ===')
after = to_ct(datetime.datetime(2026, 9, 11, 11, 13, 0))
dom = collections.Counter()
for vt, url in rows:
    if vt > after:
        d = urlsplit(url or '').netloc or (url or '')[:40]
        dom[d] += 1
for d, c in dom.most_common(40):
    print('  %3d  %s' % (c, d))
print('  총 %d건 / %d개 도메인' % (sum(dom.values()), len(dom)))

con.close()
os.remove(TMP)
