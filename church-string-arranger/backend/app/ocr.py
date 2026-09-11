# -*- coding: utf-8 -*-
"""Church String Arranger - 악보 OCR(OMR) 인터페이스

현재 구현:
- PDF/이미지 → 페이지 이미지 추출
- 오선(staff line) 감지 (수평 투영 기반) — 실제 음표 인식은 OMR 엔진 연동 포인트

참고: 음표 단위 정밀 인식(OMR)은 연구급 문제라,
MVP에서는 (1) 오선/마디 수 자동 감지, (2) 편집 가능한 텍스트 입력으로
멜로디·코드·가사를 확정하는 파이프라인을 제공합니다.
향후 Audiveris 등 OMR 엔진을 ocr_engine.py 에 연결하면
자동 인식 → 수정(PRD: OCR 결과 수정 기능) 흐름이 완성됩니다.
"""
from __future__ import annotations
import io
from typing import List, Optional

import fitz  # PyMuPDF


def pdf_to_images(pdf_bytes: bytes, max_pages: int = 3, dpi: int = 150) -> List[bytes]:
    """PDF → 페이지별 PNG 바이트 리스트"""
    out = []
    doc = fitz.open(stream=pdf_bytes, filetype='pdf')
    for i in range(min(len(doc), max_pages)):
        pix = doc[i].get_pixmap(dpi=dpi)
        out.append(pix.tobytes('png'))
    return out


def detect_staff_lines(img_bytes: bytes) -> dict:
    """수평 투영으로 오선 감지 → 감지 정보 반환"""
    try:
        from PIL import Image
        import numpy as np
        im = Image.open(io.BytesIO(img_bytes)).convert('L')
        a = np.asarray(im)
        h, w = a.shape
        # 어두운 픽셀 비율 (이진화)
        dark = a < 150
        row_density = dark.sum(axis=1) / max(w, 1)
        # 오선: 밀도 높은 연속 행 그룹 (선 두께 몇 px)
        groups = []
        in_group = False
        start = 0
        for r in range(h):
            if row_density[r] > 0.30:
                if not in_group:
                    start, in_group = r, True
            else:
                if in_group and r - start >= 2:
                    groups.append((start, r))
                in_group = False
        if in_group and h - start >= 2:
            groups.append((start, h))
        # 가까운 선 그룹끼리 병합 → 오선 5줄 묶음 (실제 스캔: 선 간격 5~12px)
        staves = []
        cur = None
        for gs, ge in groups:
            if cur is None:
                cur = [gs, ge, 1]
            elif gs - cur[1] <= 12:
                cur[1] = ge
                cur[2] += 1
            else:
                if cur[2] >= 3:
                    staves.append({'y_top': int(cur[0]), 'y_bottom': int(cur[1]), 'lines': cur[2]})
                cur = [gs, ge, 1]
        if cur and cur[2] >= 3:
            staves.append({'y_top': int(cur[0]), 'y_bottom': int(cur[1]), 'lines': cur[2]})
        return {'detected_staves': len(staves), 'image_size': [w, h], 'staves': staves[:10],
                'status': 'staff_detected'}
    except Exception as e:
        return {'detected_staves': 0, 'status': 'error', 'message': str(e)}


def analyze_score_image(img_bytes: bytes) -> dict:
    """이미지 한 장 분석: 오선 감지 + 안내 메시지"""
    info = detect_staff_lines(img_bytes)
    info['note_level_ocr'] = False
    info['message'] = (
        '오선 ' + str(info.get('detected_staves', 0)) + '개 감지. '
        '음표 단위 자동 인식(OMR)은 향후 엔진 연동 예정 — '
        '아래 편집기에서 멜로디·코드·가사를 입력/확인해 주세요.'
    )
    return info
