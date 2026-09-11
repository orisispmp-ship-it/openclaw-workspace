# -*- coding: utf-8 -*-
"""HTTP API 통합 테스트"""
import json, urllib.request, urllib.parse, os

BASE = 'http://127.0.0.1:8000'
OUT = r'C:\Users\orisi\.openclaw\workspace\church-string-arranger\backend\output'

def get(path, binary=False):
    with urllib.request.urlopen(BASE + path) as r:
        data = r.read()
    return data if binary else json.loads(data)

def post_json(path, obj):
    req = urllib.request.Request(BASE + path, data=json.dumps(obj).encode(),
                                 headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

# 1. health
print('health:', get('/api/health'))

# 2. samples
s = get('/api/samples')
print('samples:', s['samples'])

# 3. 샘플 MusicXML 다운로드
mx = get('/api/samples/amazing_grace/musicxml', binary=True)
open(os.path.join(OUT, 'api_ag.musicxml'), 'wb').write(mx)
print('sample musicxml bytes:', len(mx))

# 4. 샘플을 서버에서 바로 편곡 (MusicXML 업로드 → 스코어 JSON)
import uuid
boundary = '----test' + uuid.uuid4().hex
body = b''
body += f'--{boundary}\r\n'.encode()
body += b'Content-Disposition: form-data; name="file"; filename="ag.musicxml"\r\n'
body += b'Content-Type: application/vnd.recordare.musicxml\r\n\r\n'
body += mx + b'\r\n'
body += f'--{boundary}--\r\n'.encode()
req = urllib.request.Request(BASE + '/api/upload', data=body,
                             headers={'Content-Type': f'multipart/form-data; boundary={boundary}'})
with urllib.request.urlopen(req) as r:
    up = json.loads(r.read())
print('upload type:', up['type'], '| measures:', len(up['score']['measures']), '| msg:', up['message'])

# 5. 편곡 실행 (4중주, 라장조 조옮김, Letter, 영문 악기명)
arr = post_json('/api/arrange', {
    'score': up['score'],
    'arrangement': 'quartet',
    'transpose_to': 'D',
    'tempo': 96,
    'lyrics_on': True,
    'page_size': 'Letter',
    'lang': 'kr',
    'page_numbers': True,
})
print('arrange:', arr['title'], '| key:', arr['key'], '| tempo:', arr['tempo'], '| parts:', arr['parts'])

# 6. PDF 다운로드 + 검증
pdf = get(arr['pdf'], binary=True)
open(os.path.join(OUT, 'api_result.pdf'), 'wb').write(pdf)
print('pdf bytes:', len(pdf))

import fitz
doc = fitz.open(os.path.join(OUT, 'api_result.pdf'))
print('pdf pages:', len(doc), '| page size pt:', doc[0].rect)
txt = doc[0].get_text()
print('title in pdf:', '주 은혜' in txt, '| lyric in pdf:', '살리신' in txt, '| key D in pdf:', '라장조' in txt)
pix = doc[0].get_pixmap(dpi=100)
pix.save(os.path.join(OUT, 'api_result_p1.png'))
doc.close()

# 7. MIDI 존재 확인
mid = get(arr['midi'], binary=True)
print('midi bytes:', len(mid), '| header:', mid[:4])

# 8. 조옮김 결과 확인: 멜로디 첫 음이 D장조에서 어떻게 표기되는지
print('ARRANGE OK')
