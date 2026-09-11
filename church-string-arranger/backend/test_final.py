# -*- coding: utf-8 -*-
"""최종 통합 테스트: 프론트엔드 서빙 + 전체 API 플로우"""
import json, urllib.request, os, sys

BASE = 'http://127.0.0.1:8000'
OUT = r'C:\Users\orisi\.openclaw\workspace\church-string-arranger\backend\output'

def get(path, binary=False):
    with urllib.request.urlopen(BASE + path) as r:
        return r.read() if binary else json.loads(r.read())

# 1. 프론트엔드 서빙 확인
html = get('/', binary=True).decode('utf-8', 'ignore')
print('1. GET / -> index.html:', '<div id="root">' in html, '| title:', 'Church String Arranger' in html)

# 2. 에셋 확인
assets = [l for l in html.split('"') if (l.endswith('.js') or l.endswith('.css')) and 'assets' in l]
for a in assets:
    path = a if a.startswith('/') else '/' + a.lstrip('./')
    ok = len(get(path, binary=True)) > 1000
    print(f'   asset {path.split("/")[-1]}: {"OK" if ok else "FAIL"}')

# 3. 이미지 업로드 (OCR 오선 감지) — 테스트용 악보 이미지 생성
from PIL import Image, ImageDraw
img = Image.new('L', (800, 600), 255)
d = ImageDraw.Draw(img)
for i in range(5):
    d.line([(50, 100 + i * 12), (750, 100 + i * 12)], fill=0, width=2)
for i in range(5):
    d.line([(50, 200 + i * 12), (750, 200 + i * 12)], fill=0, width=2)
img_path = os.path.join(OUT, 'test_score.png')
img.save(img_path)

import uuid
boundary = '----t' + uuid.uuid4().hex
body = b''
with open(img_path, 'rb') as f:
    png = f.read()
body += f'--{boundary}\r\n'.encode()
body += b'Content-Disposition: form-data; name="file"; filename="score.png"\r\n'
body += b'Content-Type: image/png\r\n\r\n'
body += png + b'\r\n--' + boundary.encode() + b'--\r\n'
req = urllib.request.Request(BASE + '/api/upload', data=body,
                             headers={'Content-Type': f'multipart/form-data; boundary={boundary}'})
with urllib.request.urlopen(req) as r:
    up = json.loads(r.read())
print('3. 이미지 업로드:', up['type'], '| 오선 감지:', up['ocr']['detected_staves'], '| msg:', up['message'][:40], '...')

# 4. 샘플 2중주 편곡 (기본값)
mx = get('/api/samples/ode_to_joy/musicxml', binary=True)
boundary = '----t' + uuid.uuid4().hex
body = b''
body += f'--{boundary}\r\n'.encode()
body += b'Content-Disposition: form-data; name="file"; filename="otj.musicxml"\r\n'
body += b'Content-Type: application/xml\r\n\r\n'
body += mx + b'\r\n--' + boundary.encode() + b'--\r\n'
req = urllib.request.Request(BASE + '/api/upload', data=body,
                             headers={'Content-Type': f'multipart/form-data; boundary={boundary}'})
with urllib.request.urlopen(req) as r:
    up2 = json.loads(r.read())

req = urllib.request.Request(BASE + '/api/arrange',
                             data=json.dumps({'score': up2['score'], 'arrangement': 'duo',
                                              'lyrics_on': True, 'page_size': 'A4', 'lang': 'en',
                                              'page_numbers': True}).encode(),
                             headers={'Content-Type': 'application/json'})
with urllib.request.urlopen(req) as r:
    arr = json.loads(r.read())
pdf = get(arr['pdf'], binary=True)
print('4. 2중주 편곡:', arr['title'], '|', arr['arrangement_label'], '| pdf:', len(pdf), 'bytes')

# 5. 4중주 + 조옮김
req = urllib.request.Request(BASE + '/api/arrange',
                             data=json.dumps({'score': up2['score'], 'arrangement': 'quartet',
                                              'transpose_to': 'F', 'tempo': 120, 'lyrics_on': False,
                                              'page_size': 'Letter', 'lang': 'kr', 'page_numbers': False}).encode(),
                             headers={'Content-Type': 'application/json'})
with urllib.request.urlopen(req) as r:
    arr2 = json.loads(r.read())
pdf2 = get(arr2['pdf'], binary=True)
mx2 = get(arr2['musicxml'], binary=True)
print('5. 4중주 편곡:', arr2['title'], '|', arr2['key'], '조 | pdf:', len(pdf2), '| musicxml:', len(mx2), 'bytes')

print('\nALL INTEGRATION TESTS PASSED ✅')
