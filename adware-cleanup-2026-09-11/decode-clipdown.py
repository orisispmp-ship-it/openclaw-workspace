import base64

KEY = b'clip'

def dec(s):
    try:
        raw = base64.b64decode(s)
    except Exception:
        return '(base64 fail)'
    out = bytearray()
    for i, b in enumerate(raw):
        out.append(b ^ KEY[i % len(KEY)])
    try:
        return out.decode('utf-8')
    except Exception:
        return repr(bytes(out))

import xml.etree.ElementTree as ET
path = r'C:\Program Files (x86)\clipdown\ad_shortcutbookmark.xml'
root = ET.parse(path).getroot()
print('install_type:', root.findtext('install_type'), '| visible_count:', root.findtext('visible_count'), '| expire_day:', root.findtext('expire_day'))
print()
for ad in root.iter('ad'):
    print('--- idx', ad.findtext('idx'), '|', ad.findtext('ad_name'), '| use:', ad.findtext('use_yn'))
    print('    shortcut  :', ad.findtext('shortcut_name'))
    print('    bookmark  :', ad.findtext('bookmark_name'))
    t = ad.findtext('target_url')
    p = ad.findtext('target_punycode_url')
    if t:
        print('    target    :', dec(t))
    if p:
        print('    target(puny):', dec(p))
    ck = ad.findtext('check_shortcutblacklist_url')
    if ck:
        print('    check_url :', dec(ck))
    tr = ad.findtext('traget_regs')
    if tr:
        print('    target_regs:', dec(tr)[:400])
    print()
