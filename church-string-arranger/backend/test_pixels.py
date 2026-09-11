# -*- coding: utf-8 -*-
"""객관적 검증: 음표 머리 중심 vs 오선 위치 (픽셀 분석)"""
import sys, os
sys.path.insert(0, r'C:\Users\orisi\.openclaw\workspace\church-string-arranger\backend')
import numpy as np
from PIL import Image

from app.samples import get_sample
from app.harmony import run_arrangement, ARRANGEMENTS
from app.engraver import Engraver

OUT = r'C:\Users\orisi\.openclaw\workspace\church-string-arranger\backend\output'

# 단순 테스트 악보: C장조, 한 줄에 E4 G4 B4 D5 F5 (오선 위 음들)
from app.model import Score, Measure, Note, Chord
sc = Score(title='검증', composer='', key='C', time=(4, 4), tempo=90, original_key='C')
m1 = Measure(chords=[Chord.parse('C')] * 4)
for step, octv in [('E', 4), ('G', 4), ('B', 4), ('D', 5)]:
    m1.notes.append(Note(step=step, octave=octv, duration=1.0))
sc.measures.append(m1)

work, parts = run_arrangement(sc, 'duo')
po = ARRANGEMENTS['duo']['parts']
eng = Engraver(po, lang='kr', page_size='A4', lyrics_on=True, page_numbers=True)
pdf_path = os.path.join(OUT, 'verify.pdf')
eng.render(work, parts, pdf_path)

import fitz
doc = fitz.open(pdf_path)
pix = doc[0].get_pixmap(dpi=300)
img = Image.frombytes('RGB', (pix.width, pix.height), pix.samples)
a = np.asarray(img.convert('L'))
doc.close()
print('image:', a.shape)

# 1) 첫 시스템(맨 위 오선) 찾기: 어두운 수평선 밀도
dark = a < 140
row_frac = dark.mean(axis=1)
# 첫 시스템 영역 (상단 1/3)
top_region = row_frac[:a.shape[0] // 3]
lines_y = []
in_line = False
for r, frac in enumerate(top_region):
    if frac > 0.30 and not in_line:
        start, in_line = r, True
    elif frac <= 0.30 and in_line:
        if r - start >= 3:
            lines_y.append((start + r) // 2)
        in_line = False
print('검출된 수평선 y (첫 시스템):', lines_y)
if len(lines_y) >= 5:
    gaps = [lines_y[i + 1] - lines_y[i] for i in range(4)]
    print('선 간격(px):', gaps, '→ 균일:', max(gaps) - min(gaps) <= 3)

# 2) 오선 위 음표 머리 검출: 첫 오선 라인 y 근처에서 어두운 덩어리(타원) 찾기
# 첫 번째 시스템의 오선 y 범위
y0, y1 = lines_y[0] - 15, lines_y[-1] + 15
band = a[y0:y1, :]
# 열 밀도로 음표 위치 추정
col_dark = (band < 140).sum(axis=0)
# 음표 머리는 오선보다 넓은 어두운 영역
cols = np.where(col_dark > 3)[0]
print('음표로 보이는 x 범위 개수:', len(cols), '샘플:', cols[:20])
