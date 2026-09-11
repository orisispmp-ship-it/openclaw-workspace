# -*- coding: utf-8 -*-
"""백엔드 파이프라인 테스트: 샘플 → 편곡 → PDF 검증"""
import sys, os
sys.path.insert(0, r'C:\Users\orisi\.openclaw\workspace\church-string-arranger\backend')
from app.samples import get_sample
from app.harmony import run_arrangement, ARRANGEMENTS
from app.engraver import Engraver
from app.musicxml import write_musicxml, read_musicxml
from app import ocr
import fitz

OUT = r'C:\Users\orisi\.openclaw\workspace\church-string-arranger\backend\output'
os.makedirs(OUT, exist_ok=True)

sc = get_sample('amazing_grace')
print('sample measures:', len(sc.measures), 'key:', sc.key, 'time:', sc.time)

# MusicXML 라운드트립
p = os.path.join(OUT, 'test_ag.musicxml')
write_musicxml(sc, p)
sc2 = read_musicxml(p)
print('roundtrip measures:', len(sc2.measures), 'first notes:', [(n.step, n.octave, n.duration) for n in sc2.measures[0].notes])
print('first lyric:', sc2.measures[0].notes[0].lyric)

# 2중주 편곡 + PDF
for arr in ['duo', 'quartet']:
    work, parts = run_arrangement(sc, arr)
    po = ARRANGEMENTS[arr]['parts']
    eng = Engraver(po, lang='kr', page_size='A4', lyrics_on=True, page_numbers=True)
    pdf_path = os.path.join(OUT, f'test_{arr}.pdf')
    eng.render(work, parts, pdf_path)
    doc = fitz.open(pdf_path)
    print(f'{arr}: pages={len(doc)}')
    txt = doc[0].get_text()
    print('  page1 text has title:', sc.title.split('(')[0].strip() in txt, '| has lyric:', '살리신' in txt)
    pix = doc[0].get_pixmap(dpi=110)
    pix.save(os.path.join(OUT, f'test_{arr}_p1.png'))
    if len(doc) > 1:
        pix2 = doc[1].get_pixmap(dpi=110)
        pix2.save(os.path.join(OUT, f'test_{arr}_p2.png'))
    doc.close()
print('DONE')
