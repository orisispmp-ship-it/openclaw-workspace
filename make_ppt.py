from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.dml.color import RGBColor
import os

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)

BLUE = RGBColor(0x1A, 0x3C, 0x6E)
LIGHT_BLUE = RGBColor(0xD6, 0xE4, 0xF0)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
DARK_GRAY = RGBColor(0x33, 0x33, 0x33)
RED = RGBColor(0xC0, 0x39, 0x2B)
GREEN = RGBColor(0x1E, 0x84, 0x45)
ACCENT = RGBColor(0x2E, 0x86, 0xDE)

def add_bg(slide, color=BLUE):
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = color

def add_shape(slide, left, top, width, height, color):
    from pptx.util import Inches, Pt
    shape = slide.shapes.add_shape(1, left, top, width, height)  # 1 = rectangle
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    shape.line.fill.background()
    return shape

def add_text_box(slide, left, top, width, height, text, font_size=14, bold=False, color=DARK_GRAY, align=PP_ALIGN.LEFT, font_name='Malgun Gothic'):
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(font_size)
    p.font.bold = bold
    p.font.color.rgb = color
    p.font.name = font_name
    p.alignment = align
    return txBox

def add_multi_text(slide, left, top, width, height, lines, font_size=13, color=DARK_GRAY, line_spacing=1.3):
    """lines: list of (text, bold, color_override) or just strings"""
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = True
    for i, item in enumerate(lines):
        if isinstance(item, str):
            txt, bld, clr = item, False, color
        else:
            txt, bld, clr = item[0], item[1] if len(item) > 1 else False, item[2] if len(item) > 2 else color
        if i == 0:
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()
        p.text = txt
        p.font.size = Pt(font_size)
        p.font.bold = bld
        p.font.color.rgb = clr
        p.font.name = 'Malgun Gothic'
        p.space_after = Pt(4)
    return txBox

# ---- Slide 1: Title ----
slide = prs.slides.add_slide(prs.slide_layouts[6])  # blank
add_bg(slide, BLUE)
add_text_box(slide, Inches(1), Inches(1.5), Inches(11), Inches(1.5),
    'P4 Ph4 한미글로벌 감리품질관리계획서\n개정 비교 분석', 
    font_size=36, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
add_text_box(slide, Inches(1), Inches(3.5), Inches(11), Inches(1),
    'Rev.3 (2026.06.23) → Rev.4 (2026.07.16)', 
    font_size=22, color=LIGHT_BLUE, align=PP_ALIGN.CENTER)
add_text_box(slide, Inches(1), Inches(5.0), Inches(11), Inches(0.6),
    '작성: 윤익현  |  검토: 유지우  |  승인: 박상진  |  작성일: 2026.07.14', 
    font_size=14, color=LIGHT_BLUE, align=PP_ALIGN.CENTER)

# ---- Slide 2: Executive Summary ----
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide, WHITE)
add_shape(slide, Inches(0), Inches(0), Inches(13.333), Inches(0.8), BLUE)
add_text_box(slide, Inches(0.5), Inches(0.1), Inches(12), Inches(0.6),
    'Ⅰ. 종합 결과', font_size=26, bold=True, color=WHITE)

add_text_box(slide, Inches(0.5), Inches(1.2), Inches(12), Inches(0.6),
    '개정 목적: 2026년 상반기 QMS Audit 지적사항 추가 반영', 
    font_size=16, bold=True, color=BLUE)

lines = [
    ('📌 총 15개 조항 + 신규 표 5건 변경·추가', True, BLUE),
    ('', False),
    ('① 업무절차의 단계별 구체화', True, DARK_GRAY),
    ('   기존 나열식 절차 → (1)~(4) 단계 구조 또는 "가.나.다." 절차로 재구성', False, DARK_GRAY),
    ('   각 단계의 수행주체(단장/공무팀장/공종팀장/담당 감리원) 명시', False, DARK_GRAY),
    ('', False),
    ('② 책임과 권한의 역할별 명확화', True, DARK_GRAY),
    ('   5.2(R&R), 6.2(품질목표), 8.6(품질감리) 등 직책별 책임과 권한 재정리', False, DARK_GRAY),
    ('', False),
    ('③ 관리기준의 표 체계화', True, DARK_GRAY),
    ('   7.3, 7.5, 7.6 조항 중심으로 신규 기준표 5건 추가 (서술형 → 표)', False, DARK_GRAY),
]
add_multi_text(slide, Inches(0.5), Inches(2.0), Inches(12), Inches(5), lines, font_size=14)

# ---- Slide 3: Revision History ----
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide, WHITE)
add_shape(slide, Inches(0), Inches(0), Inches(13.333), Inches(0.8), BLUE)
add_text_box(slide, Inches(0.5), Inches(0.1), Inches(12), Inches(0.6),
    '개정 이력', font_size=26, bold=True, color=WHITE)

# Table
rows, cols = 5, 5
table = slide.shapes.add_table(rows, cols, Inches(0.5), Inches(1.3), Inches(12), Inches(2.5)).table
headers = ['개정번호', '개정일자', '개정내용 및 사유', '작성', '검토']
data = [
    ['REV3', '2026.06.23', '26년 상반기 QMS Audit 반영', '윤익현', '유지우'],
    ['REV4', '2026.07.16', '26년 상반기 QMS Audit 추가 반영', '윤익현', '유지우'],
]
for j, h in enumerate(headers):
    cell = table.cell(0, j)
    cell.text = h
    for p in cell.text_frame.paragraphs:
        p.font.size = Pt(12)
        p.font.bold = True
        p.font.color.rgb = WHITE
        p.font.name = 'Malgun Gothic'
    cell.fill.solid()
    cell.fill.fore_color.rgb = BLUE

for i, row in enumerate(data):
    for j, val in enumerate(row):
        cell = table.cell(i+1, j)
        cell.text = val
        for p in cell.text_frame.paragraphs:
            p.font.size = Pt(12)
            p.font.name = 'Malgun Gothic'
        if i == 1:
            cell.fill.solid()
            cell.fill.fore_color.rgb = LIGHT_BLUE

# Merge 승인 column for header
table.cell(0, 3).merge(table.cell(0, 4))
table.cell(0, 3).text = '작성 / 검토 / 승인'

# ---- Slide 4: Changes Overview ----
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide, WHITE)
add_shape(slide, Inches(0), Inches(0), Inches(13.333), Inches(0.8), BLUE)
add_text_box(slide, Inches(0.5), Inches(0.1), Inches(12), Inches(0.6),
    'Ⅱ. 항목별 변경사항 총괄 (1/2)', font_size=26, bold=True, color=WHITE)

changes_1 = [
    ('1. 표지/1.2 개정현황 (1. 일반사항)', '서지사항 갱신 — Rev.3→Rev.4, 발행일 갱신, 개정이력표 행 추가'),
    ('2. 4.2.5 이해관계자 요구사항 관리 (4. 조직상황)', '절차 세분화 — 나열식→3단계 재구성, 반기/월간 주기 기준 신설'),
    ('3. 5.1.1~5.1.2 품질방침 (5. 리더십)', '절차 신설 — 작성→승인→게시공유→기록관리 체계, 역할 명확화'),
    ('4. 5.2.4~5.2.5 R&R 업무분장 (5. 리더십)', 'R&R 명확화 — 개정→취합→검토→승인 절차 흐름 구체화'),
    ('5. 6.2.4~6.2.5 품질목표관리 (6. 기획)', '절차 재구성 — KPI 8단계, 3대 평가분야 명시, 경영검토 보고체계 신설'),
    ('6. 6.3.1~6.3.5 품질관리계획서 변경관리 (6. 기획)', '조항 신설 — 작성→검토→승인 3단계 개정절차, 용어정의 추가'),
    ('7. 7.3.5~7.3.8 지식관리 (7. 지원)', '절차 재구성/표 신설 — 4단계 + 지식유형별 담당·보관 표'),
    ('8. 7.4.7 교육훈련 (7. 지원)', '절차 신설/표 갱신 — 교육후 결과보고, 신규감리원 비동기학습 개편'),
]
y = 1.1
for i, (title, desc) in enumerate(changes_1):
    add_shape(slide, Inches(0.3), Inches(y), Inches(0.06), Inches(0.45), ACCENT)
    add_text_box(slide, Inches(0.5), Inches(y), Inches(12.3), Inches(0.3),
        title, font_size=13, bold=True, color=BLUE)
    add_text_box(slide, Inches(0.7), Inches(y+0.28), Inches(12), Inches(0.3),
        desc, font_size=12, color=DARK_GRAY)
    y += 0.65

# ---- Slide 5: Changes Overview 2/2 ----
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide, WHITE)
add_shape(slide, Inches(0), Inches(0), Inches(13.333), Inches(0.8), BLUE)
add_text_box(slide, Inches(0.5), Inches(0.1), Inches(12), Inches(0.6),
    'Ⅱ. 항목별 변경사항 총괄 (2/2)', font_size=26, bold=True, color=WHITE)

changes_2 = [
    ('9. 7.5.3, 7.5.6 의사소통관리 (7. 지원)', '절차 재구성/표 확대 — 4단계 재구성, 의사소통기준표 4행→11행, 외부/내부 대상표 2건 신규'),
    ('10. 7.6.5~7.6.7 문서화된 정보관리 (7. 지원)', '신설/표 신설 — 문서/기록 관리방법 구분, 관리기준표 2건 신규'),
    ('11. 8.5.5 공정감리 업무절차 (8. 운용)', '절차 구체화 — 공정/테마점검, 기술검토, ITP, PCM, 기계설비법 신고 등 수행주체 명시'),
    ('12. 8.6.4~8.6.5 품질감리 (8. 운용)', 'R&R 재정리/기준 신설 — D-1일 사전검토, Random 통보, CPMS 처리기한 1일 이내'),
    ('13. 8.8.5 부적합 공사의 관리 (8. 운용)', '절차 재구성 — 발견→보고→CPMS 등재→조치→확인→승인, 최종 승인: 삼성전자 담당자'),
    ('14. 9.2.5 분석 및 평가 (9. 성과관리)', '절차 재구성 — 데이터 수집→분석→F/B 3단계, 개선대책 차기 경영검토 반영'),
    ('15. 10.1.5 부적합 및 시정조치 (10. 개선)', '절차 재구성 — 대상선정→시정조치→결과검토→기록 4단계, 부적합 대상 정의 구체화'),
]
y = 1.1
for i, (title, desc) in enumerate(changes_2):
    add_shape(slide, Inches(0.3), Inches(y), Inches(0.06), Inches(0.45), ACCENT)
    add_text_box(slide, Inches(0.5), Inches(y), Inches(12.3), Inches(0.3),
        title, font_size=13, bold=True, color=BLUE)
    add_text_box(slide, Inches(0.7), Inches(y+0.28), Inches(12), Inches(0.3),
        desc, font_size=12, color=DARK_GRAY)
    y += 0.7

# ---- Slide 6: New Forms ----
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide, WHITE)
add_shape(slide, Inches(0), Inches(0), Inches(13.333), Inches(0.8), BLUE)
add_text_box(slide, Inches(0.5), Inches(0.1), Inches(12), Inches(0.6),
    'Ⅲ. 신설 서식(표) 목록', font_size=26, bold=True, color=WHITE)

add_text_box(slide, Inches(0.5), Inches(1.2), Inches(12), Inches(0.5),
    '이번 개정에서 5건의 관리기준 표가 신규 추가됨', font_size=16, color=DARK_GRAY)

rows, cols = 6, 3
tbl = slide.shapes.add_table(rows, cols, Inches(1.5), Inches(2.0), Inches(9), Inches(3.5)).table
tbl_h = ['조항', '신설 표 명칭', '분류']
tbl_d = [
    ['7.3.5', '지식유형별 담당·보관방법 표', '지식관리'],
    ['7.5.6', '외부 의사소통 대상·방법·기준 표', '의사소통'],
    ['7.5.6', '내부 의사소통 대상·방법·기준 표', '의사소통'],
    ['7.6.6', '문서 관리기준 표', '문서관리'],
    ['7.6.7', '기록 관리기준 표', '문서관리'],
]
for j, h in enumerate(tbl_h):
    cell = tbl.cell(0, j)
    cell.text = h
    for p in cell.text_frame.paragraphs:
        p.font.size = Pt(14)
        p.font.bold = True
        p.font.color.rgb = WHITE
        p.font.name = 'Malgun Gothic'
        p.alignment = PP_ALIGN.CENTER
    cell.fill.solid()
    cell.fill.fore_color.rgb = BLUE

for i, row in enumerate(tbl_d):
    for j, val in enumerate(row):
        cell = tbl.cell(i+1, j)
        cell.text = val
        for p in cell.text_frame.paragraphs:
            p.font.size = Pt(13)
            p.font.name = 'Malgun Gothic'
            p.alignment = PP_ALIGN.CENTER
        if i % 2 == 1:
            cell.fill.solid()
            cell.fill.fore_color.rgb = LIGHT_BLUE

# ---- Slide 7: Key Area Changes ----
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide, WHITE)
add_shape(slide, Inches(0), Inches(0), Inches(13.333), Inches(0.8), BLUE)
add_text_box(slide, Inches(0.5), Inches(0.1), Inches(12), Inches(0.6),
    'Ⅳ. 주요 변경 분야별 요약', font_size=26, bold=True, color=WHITE)

areas = [
    ('📋 의사소통 관리 (7.5)',
     ['기준표 4행→11행 확대', '정기/수시보고, 공문수발신, 검측·기성, 인허가서류 등 추가',
      '외부/내부 의사소통 대상표 2건 신규']),
    ('📚 문서화된 정보관리 (7.6)',
     ['문서와 기록 관리방법을 분리하여 신설', '보관연한을 표로 체계화 (문서/기록 관리기준표 2건)']),
    ('🔍 품질감리 (8.6)',
     ['D-1일 사전검토 후 입회여부 Random 통보', 'CPMS 처리기한: 작업일 기준 1일 이내']),
    ('⚙️ 부적합 관리 (8.8 / 10.1)',
     ['발견→승인까지 6단계 절차 재구성', '부적합 대상 정의 구체화 (Audit, B/P, VOC 등)']),
]

y = 1.2
for title, items in areas:
    add_text_box(slide, Inches(0.5), Inches(y), Inches(12), Inches(0.4),
        title, font_size=16, bold=True, color=BLUE)
    y += 0.4
    for item in items:
        add_text_box(slide, Inches(0.8), Inches(y), Inches(11.5), Inches(0.35),
            f'• {item}', font_size=13, color=DARK_GRAY)
        y += 0.35
    y += 0.15

# ---- Slide 8: Methodology ----
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide, WHITE)
add_shape(slide, Inches(0), Inches(0), Inches(13.333), Inches(0.8), BLUE)
add_text_box(slide, Inches(0.5), Inches(0.1), Inches(12), Inches(0.6),
    'Ⅴ. 비교 방법 및 유의사항', font_size=26, bold=True, color=WHITE)

lines8 = [
    ('본 비교 분석 방법', True, BLUE),
    ('', False),
    ('• 개정 전(Rev.3) / 개정 후(Rev.4) 두 파일의 본문 단락 및 표 내용을 텍스트 대조', False, DARK_GRAY),
    ('• 실질적으로 변경된 항목(절차·기준·책임소재) 위주로 정리', False, DARK_GRAY),
    ('', False),
    ('제외 사항', True, BLUE),
    ('', False),
    ('• 문구·어미 표현 통일 등 의미 변화가 없는 경미한 수정은 제외', False, DARK_GRAY),
    ('• 그림·도면·서식 레이아웃 등 시각적 요소 변경 여부는 미포함', False, DARK_GRAY),
    ('', False),
    ('⚠ 주의사항', True, RED),
    ('', False),
    ('• 본 자료는 자동 대조 결과 기반 — 최종 활용 전 원문 대조 확인 권장', False, RED),
]
add_multi_text(slide, Inches(0.5), Inches(1.2), Inches(12), Inches(5.5), lines8, font_size=14)

# Save
output_path = r'C:\Users\orisi\.openclaw\workspace\감리품질관리계획서_개정비교분석.pptx'
prs.save(output_path)
print(f'Saved to: {output_path}')
