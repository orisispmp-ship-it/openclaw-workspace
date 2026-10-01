import json, os, shutil, datetime

BK = r'C:\Users\orisi\.openclaw\workspace\adware-cleanup-2026-10-01'
base = os.path.join(os.environ['LOCALAPPDATA'], 'Microsoft', 'Edge', 'User Data')
stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')

# 1) backup Preferences
pf = os.path.join(base, 'Default', 'Preferences')
shutil.copy2(pf, os.path.join(BK, 'Edge-Preferences.before-%s.json' % stamp))
print('backup Preferences -> Edge-Preferences.before-%s.json' % stamp)

with open(pf, 'r', encoding='utf-8') as f:
    d = json.load(f)

s = d.get('sync') or {}
print('BEFORE: has_been_enabled=%s keep_everything_synced=%s gaia_id=%s edge_account_type=%s'
      % (s.get('has_been_enabled'), s.get('keep_everything_synced'), s.get('gaia_id'), s.get('edge_account_type')))

# 2) turn sync off (bookmarks can no longer be pulled back from the cloud)
s['has_been_enabled'] = False
s['keep_everything_synced'] = False
s['selected_types'] = {}
d['sync'] = s

with open(pf, 'w', encoding='utf-8') as f:
    json.dump(d, f, ensure_ascii=False)

with open(pf, 'r', encoding='utf-8') as f:
    chk = json.load(f)
cs = chk.get('sync', {})
print('AFTER : has_been_enabled=%s keep_everything_synced=%s selected_types=%s'
      % (cs.get('has_been_enabled'), cs.get('keep_everything_synced'), cs.get('selected_types')))

# 3) quarantine local sync DB so it cannot restore server state at startup
sd = os.path.join(base, 'Default', 'Sync Data')
if os.path.exists(sd):
    dst = os.path.join(BK, 'Edge-SyncData.bak-%s' % stamp)
    shutil.move(sd, dst)
    print('MOVED Sync Data -> %s' % dst)
else:
    print('Sync Data: not found')
