import re, base64, os, sys

log = r'C:\Users\orisi\AppData\Local\Temp\openclaw-web-fetch-4f58fd5210443554.log'
if not os.path.exists(log):
    print('spill log not found:', log); sys.exit(1)

raw = open(log, 'r', encoding='utf-8', errors='replace').read()
m = re.search(r'<<<EXTERNAL_UNTRUSTED_CONTENT[^>]*>>>(.*?)<<<END_EXTERNAL_UNTRUSTED_CONTENT', raw, re.S)
body = m.group(1) if m else raw

# longest base64 run
cands = re.findall(r'[A-Za-z0-9+/=]{500,}', body)
cands.sort(key=len, reverse=True)
print('base64 runs found:', [len(c) for c in cands[:5]])
blob = max(cands, key=len)
blob = blob[:len(blob) - (len(blob) % 4)]
src = base64.b64decode(blob).decode('utf-8', errors='replace')
print('decoded source length:', len(src))
open(r'C:\Users\orisi\.openclaw\workspace\adware-cleanup-2026-09-11\bookmark_codec.cc.txt', 'w', encoding='utf-8').write(src)

print()
print('===== every line mentioning checksum =====')
for i, line in enumerate(src.splitlines(), 1):
    if 'checksum' in line.lower():
        print('%5d| %s' % (i, line.rstrip()))
