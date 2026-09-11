# -*- coding: utf-8 -*-
"""음표 머리 중심 vs 오선 라인 위치 비교"""
import numpy as np
from PIL import Image

img = Image.open(r'C:\Users\orisi\.openclaw\workspace\church-string-arranger\backend\output\verify.pdf' .replace('.pdf', '.png')) if False else None

import fitz, sys, os
sys.path.insert(0, r'C:\Users\orisi\.openclaw\workspace\church-string-arranger\backend')
doc = fitz.open(r'C:\Users\orisi\.openclaw\workspace\church-string-arranger\backend\output\verify.pdf')
pix = doc[0].get_pixmap(dpi=300)
img = Image.frombytes('RGB', (pix.width, pix.height), pix.samples)
a = np.asarray(img.convert('L'))
doc.close()

# 첫 시스템 오선 (검증 결과 재사용)
lines_y = [274, 299, 325, 351, 377]
# 음표 머리 찾기: 오선 밴드에서 열별 어두운 픽셀 수
y0, y1 = lines_y[0] - 12, lines_y[-1] + 12
band = a[y0:y1, :]
dark = band < 140
col_count = dark.sum(axis=0)
# 음표 머리 = 열당 어두운 픽셀이 12개 이상인 열 (오선만 있으면 ~3개)
note_cols = np.where(col_count > 12)[0]
print('음표 머리 후보 열 수:', len(note_cols))

# 연속 열 그룹화 → 각 음표의 x 중심, y 중심
groups = []
if len(note_cols):
    start = note_cols[0]; prev = note_cols[0]
    for c in note_cols[1:]:
        if c - prev > 4:
            groups.append((start, prev)); start = c
        prev = c
    groups.append((start, prev))
print('음표 그룹 수:', len(groups))
for gx0, gx1 in groups:
    xc = (gx0 + gx1) // 2
    col = dark[:, gx0:gx1 + 1].any(axis=1)
    rows = np.where(col)[0] + y0
    yc = rows.mean()
    # 가장 가까운 오선 라인과의 거리
    d = min(abs(yc - ly) for ly in lines_y)
    print(f'  x={xc:4d} y={yc:5.1f} → 오선과 거리 {d:4.1f}px ({"정렬" if d < 6 else "어긋남!"})')
