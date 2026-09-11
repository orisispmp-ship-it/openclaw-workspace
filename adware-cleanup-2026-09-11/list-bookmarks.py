import os, json
from urllib.parse import urlsplit

PF = os.path.join(os.environ['LOCALAPPDATA'], 'Google', 'Chrome', 'User Data', 'Default', 'Bookmarks')
with open(PF, 'r', encoding='utf-8') as f:
    data = json.load(f)

def walk(node, depth=0):
    for ch in node.get('children', []) or []:
        if ch.get('type') == 'url':
            d = urlsplit(ch.get('url', '')).netloc
            print('  -', ch.get('name'), '|', d)
        else:
            print('  [', ch.get('name'), ']')
            walk(ch, depth + 1)

for key, root in data['roots'].items():
    if isinstance(root, dict) and root.get('children'):
        print('==', key)
        walk(root)
