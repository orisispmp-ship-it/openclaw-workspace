# -*- coding: utf-8 -*-
"""고해상도 크롭 검증: 첫 시스템 영역 확대"""
import sys, os
sys.path.insert(0, r'C:\Users\orisi\.openclaw\workspace\church-string-arranger\backend')
import fitz

doc = fitz.open(r'C:\Users\orisi\.openclaw\workspace\church-string-arranger\backend\output\test_duo_p1.pdf' if False else r'C:\Users\orisi\.openclaw\workspace\church-string-arranger\backend\output\test_duo.pdf') if False else None

# 다시 그리기 (최신 코드)
from app.samples import get_sample
from app.harmony import run_arrangement, ARRANGEMENTS
from app.engraver import Engraver

OUT = r'C:\Users\orisi\.openclaw\workspace\church-string-arranger\backend\output'
sc = get_sample('amazing_grace')
work, parts = run_arrangement(sc, 'quartet')
po = ARRANGEMENTS['quartet']['parts']
eng = Engraver(po, lang='kr', page_size='A4', lyrics_on=True, page_numbers=True)
pdf_path = os.path.join(OUT, 'test_quartet.pdf')
eng.render(work, parts, pdf_path)

doc = fitz.open(pdf_path)
print('pages:', len(doc))
pix = doc[0].get_pixmap(dpi=200)
pix.save(os.path.join(OUT, 'quartet_p1_200.png'))
# 첫 시스템 상단 크롭
page = doc[0]
rect = fitz.Rect(30, 60, 580, 300)  # 상단 시스템 (pt 기준)
pix2 = page.get_pixmap(dpi=300, clip=rect)
pix2.save(os.path.join(OUT, 'quartet_crop_top.png'))
# 둘째 시스템 크롭 (중간)
rect3 = fitz.Rect(30, 320, 580, 600)
pix3 = page.get_pixmap(dpi=300, clip=rect3)
pix3.save(os.path.join(OUT, 'quartet_crop_mid.png'))
doc.close()
print('saved crops')
