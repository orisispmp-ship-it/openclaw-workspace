# -*- coding: utf-8 -*-
"""최종 스모크 테스트 + 데모 PDF 생성"""
import json, urllib.request, os, uuid, io

BASE = 'http://127.0.0.1:8000'
OUT = r'C:\Users\orisi\.openclaw\workspace\church-string-arranger\backend\output'

def get(path, binary=False):
    with urllib.request.urlopen(BASE + path) as r:
        return r.read() if binary else json.loads(r.read())

def upload_bytes(data, fname, ctype):
    boundary = '----t' + uuid.uuid4().hex
    body = b''
    body += f'--{boundary}\r\n'.encode()
    body += f'Content-Disposition: form-data; name="file"; filename="{fname}"\r\n'.encode()
    body += f'Content-Type: {ctype}\r\n\r\n'.encode()
    body += data + b'\r\n--' + boundary.encode() + b'--\r\n'
    req = urllib.request.Request(BASE + '/api/upload', data=body,
                                 headers={'Content-Type': f'multipart/form-data; boundary={boundary}'})
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

def arrange(score, **kw):
    req = urllib.request.Request(BASE + '/api/arrange',
                                 data=json.dumps({'score': score, **kw}).encode(),
                                 headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

# 1. 프론트 + 헬스
assert 'Church String Arranger' in get('/', binary=True).decode('utf-8', 'ignore')
print('✅ 프론트엔드 서빙')

# 2. 이미지 업로드 → 오선 감지 (새 OCR 코드)
from PIL import Image, ImageDraw
img = Image.new('L', (900, 500), 255)
d = ImageDraw.Draw(img)
for sy in (80, 200):
    for i in range(5):
        d.rectangle([40, sy + i * 10, 860, sy + i * 10 + 3], fill=0)
buf = io.BytesIO(); img.save(buf, format='PNG')
up = upload_bytes(buf.getvalue(), 'score.png', 'image/png')
print('✅ 이미지 업로드 → 오선', up['ocr']['detected_staves'], '개 감지')

# 3. 샘플 → 2중주 데모 PDF
mx = get('/api/samples/amazing_grace/musicxml', binary=True)
sc = upload_bytes(mx, 'ag.musicxml', 'application/xml')['score']
r1 = arrange(sc, arrangement='duo', lyrics_on=True, page_size='A4', lang='kr', page_numbers=True)
pdf1 = get(r1['pdf'], binary=True)
open(os.path.join(OUT, 'demo_duo.pdf'), 'wb').write(pdf1)
print('✅ 2중주 PDF:', r1['title'], len(pdf1), 'bytes')

# 4. 샘플 → 4중주 데모 PDF (가사 포함)
r2 = arrange(sc, arrangement='quartet', lyrics_on=True, page_size='A4', lang='kr', page_numbers=True)
pdf2 = get(r2['pdf'], binary=True)
open(os.path.join(OUT, 'demo_quartet.pdf'), 'wb').write(pdf2)
print('✅ 4중주 PDF:', r2['title'], len(pdf2), 'bytes')

# 5. 이미지 → 편집기 → 편곡 플로우 (텍스트 악보로)
text_score = {
    'title': '주 은혜 (직접 입력)', 'composer': '전통', 'key': 'C', 'time': [4, 4], 'tempo': 80,
    'measures': [
        {'chords': ['C', 'F', 'C', 'G'], 'notes': [
            {'step': 'C', 'octave': 4, 'duration': 1, 'lyric': '주'}, {'step': 'E', 'octave': 4, 'duration': 1, 'lyric': '은'},
            {'step': 'G', 'octave': 4, 'duration': 1, 'lyric': '혜'}, {'step': 'C', 'octave': 5, 'duration': 1, 'lyric': '로'},
        ]},
        {'chords': ['C'], 'notes': [
            {'step': 'B', 'octave': 4, 'duration': 2, 'lyric': '우리'}, {'step': 'C', 'octave': 5, 'duration': 2, 'lyric': '함께'},
        ]},
    ],
}
r3 = arrange(text_score, arrangement='quartet', transpose_to='G', tempo=88, lyrics_on=True, page_size='Letter', lang='en', page_numbers=True)
pdf3 = get(r3['pdf'], binary=True)
open(os.path.join(OUT, 'demo_manual.pdf'), 'wb').write(pdf3)
print('✅ 텍스트 입력 → 4중주(G조) PDF:', len(pdf3), 'bytes')

print('\nSMOKE TEST ALL PASSED ✅')
