import os, shutil, sqlite3, datetime, collections

SRC = os.path.join(os.environ['LOCALAPPDATA'], 'Google', 'Chrome', 'User Data', 'Default', 'History')
TMP = os.path.join(os.environ['TEMP'], 'hist_copy.db')
shutil.copy2(SRC, TMP)
con = sqlite3.connect(TMP)
EPOCH = datetime.datetime(1601, 1, 1)
def t(x):
    return EPOCH + datetime.timedelta(microseconds=x) + datetime.timedelta(hours=9)  # local KST

MALLS = ['coupang', '11st', 'gmarket', 'auction.co.kr', 'wemakeprice', 'tmon', 'interpark', 'ssg.com',
         'lotteon', 'lotteimall', 'emart', 'hmall', 'akmall', 'danawa', 'yes24', 'cjmall', 'gsshop',
         'funshop', 'zerogram', 'k-tank', 'timemecca']

print('=== 전체 방문 최근 30건 (KST) ===')
for url, title, lv in con.execute(
        'select url, title, last_visit_time from urls order by last_visit_time desc limit 30'):
    print(t(lv).strftime('%m-%d %H:%M:%S'), '|', (url or '')[:110])

print()
print('=== 오늘(09-11) 시간대별 방문 수 ===')
start = EPOCH + datetime.timedelta(hours=-9)  # 09-11 00:00 KST as chrome time
rows = list(con.execute('select visit_time, url from visits where visit_time > ?', (start,)))
per_hour = collections.Counter()
for vt, url in rows:
    per_hour[t(vt).strftime('%H')] += 1
for h in sorted(per_hour):
    print('  %s시 : %d건' % (h, per_hour[h]))

print()
print('=== 오늘 쇼핑몰 방문 (시각/사이트) ===')
m = [(t(vt), url) for vt, url in rows if any(k in (url or '').lower() for k in MALLS)]
for tt, url in sorted(m):
    print('  ' + tt.strftime('%H:%M:%S'), '|', url[:100])
print('  총 %d건' % len(m))

print()
print('=== 마지막 쇼핑몰 방문 시각 ===')
if m:
    print('  ' + max(m)[0].strftime('%m-%d %H:%M:%S'))
else:
    print('  없음')

con.close()
os.remove(TMP)
