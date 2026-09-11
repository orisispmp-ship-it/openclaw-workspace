# -*- coding: utf-8 -*-
"""OCR 오선 감지 테스트 — 실제 스캔 스타일 이미지"""
import sys, os, io
sys.path.insert(0, r'C:\Users\orisi\.openclaw\workspace\church-string-arranger\backend')
from PIL import Image, ImageDraw
from app import ocr

# 실제 스캔처럼: 5줄이 붙어 있는 오선 2개 시스템 (간격 10px, 두께 3px)
img = Image.new('L', (900, 500), 255)
d = ImageDraw.Draw(img)
for sy in (80, 200):
    for i in range(5):
        y = sy + i * 10
        d.rectangle([40, y, 860, y + 3], fill=0)
# 음표 모양 점들 (어두운 픽셀 추가)
for x in range(100, 800, 40):
    d.ellipse([x, 120, x + 8, 128], fill=0)

buf = io.BytesIO()
img.save(buf, format='PNG')
info = ocr.analyze_score_image(buf.getvalue())
print('detected_staves:', info['detected_staves'], '| status:', info['status'])
print('staves:', info.get('staves'))
print('msg:', info['message'])
assert info['detected_staves'] == 2, '2개 시스템 감지 실패'
print('OCR TEST PASSED ✅')
