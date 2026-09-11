# -*- coding: utf-8 -*-
"""Church String Arranger - FastAPI 서버"""
from __future__ import annotations
import io
import os
import re
import tempfile
import uuid
from typing import List, Optional

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .model import Score, Note, Measure, Chord, INSTRUMENTS, KEY_FIFTHS
from .harmony import run_arrangement, ARRANGEMENTS
from .musicxml import write_musicxml, read_musicxml
from .engraver import Engraver
from . import samples as samples_mod
from . import ocr

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(ROOT, 'output')
FRONTEND_DIR = os.path.join(os.path.dirname(ROOT), 'frontend', 'dist')
os.makedirs(OUTPUT_DIR, exist_ok=True)

app = FastAPI(title='Church String Arranger API', version='0.1.0')

# ---------- 요청 모델 ----------

class NoteIn(BaseModel):
    step: str = 'C'
    alter: int = 0
    octave: int = 4
    duration: float = 1.0
    dots: int = 0
    is_rest: bool = False
    lyric: str = ''

class MeasureIn(BaseModel):
    chords: List[str] = []
    notes: List[NoteIn] = []

class ScoreIn(BaseModel):
    title: str = '제목 없음'
    composer: str = ''
    key: str = 'C'
    time: List[int] = [4, 4]
    tempo: int = 90
    measures: List[MeasureIn]

class ArrangeRequest(BaseModel):
    score: ScoreIn
    arrangement: str = 'duo'          # duo | quartet
    transpose_to: Optional[str] = None
    tempo: Optional[int] = None
    lyrics_on: bool = True
    page_size: str = 'A4'             # A4 | Letter
    lang: str = 'kr'                  # kr | en
    page_numbers: bool = True

# ---------- 변환 ----------

def score_to_model(s: ScoreIn) -> Score:
    sc = Score(title=s.title, composer=s.composer, key=s.key, time=tuple(s.time),
               tempo=s.tempo, original_key=s.key)
    for m in s.measures:
        nm = Measure()
        nm.notes = [Note(n.step, n.alter, n.octave, n.duration, n.dots, n.is_rest, n.lyric)
                    for n in m.notes]
        nm.chords = [Chord.parse(c) if c else None for c in m.chords]
        if nm.chords and len(nm.chords) < 1:
            nm.chords = [None] * s.time[0]
        sc.measures.append(nm)
    return sc


def model_to_scorein(sc: Score) -> ScoreIn:
    return ScoreIn(
        title=sc.title, composer=sc.composer, key=sc.key, time=list(sc.time), tempo=sc.tempo,
        measures=[MeasureIn(
            chords=[str(c) if c else '' for c in m.chords],
            notes=[NoteIn(step=n.step, alter=n.alter, octave=n.octave, duration=n.duration,
                          dots=n.dots, is_rest=n.is_rest, lyric=n.lyric) for n in m.notes]
        ) for m in sc.measures]
    )

# ---------- API ----------

@app.get('/api/health')
def health():
    return {'status': 'ok', 'service': 'church-string-arranger'}


@app.get('/api/samples')
def list_samples():
    out = []
    for sid, s in samples_mod.SAMPLES.items():
        out.append({'id': sid, 'title': s['title'], 'key': s['key'], 'time': s['time']})
    return {'samples': out}


@app.get('/api/samples/{sid}/musicxml')
def sample_musicxml(sid: str):
    if sid not in samples_mod.SAMPLES:
        raise HTTPException(404, '샘플 없음')
    sc = samples_mod.get_sample(sid)
    path = os.path.join(OUTPUT_DIR, f'sample_{sid}.musicxml')
    write_musicxml(sc, path)
    return FileResponse(path, media_type='application/vnd.recordare.musicxml',
                        filename=f'{sid}.musicxml')


@app.get('/api/instruments')
def instruments():
    return {'parts': {k: v for k, v in INSTRUMENTS.items()},
            'arrangements': {k: {'label_kr': v['label_kr'], 'label_en': v['label_en'], 'parts': v['parts']}
                             for k, v in ARRANGEMENTS.items()},
            'keys': list(KEY_FIFTHS.keys())}


@app.post('/api/upload')
async def upload(file: UploadFile = File(...)):
    """PDF/이미지/MusicXML 업로드 → 분석 결과"""
    data = await file.read()
    name = (file.filename or 'upload').lower()
    if name.endswith(('.mxl', '.musicxml', '.xml')):
        # MusicXML 직접 입력
        if name.endswith('.mxl'):
            import zipfile
            zf = zipfile.ZipFile(io.BytesIO(data))
            xml_name = [n for n in zf.namelist() if n.endswith('.xml')][0]
            xml_bytes = zf.read(xml_name)
        else:
            xml_bytes = data
        tmp = os.path.join(OUTPUT_DIR, f'up_{uuid.uuid4().hex}.musicxml')
        with open(tmp, 'wb') as f:
            f.write(xml_bytes)
        try:
            sc = read_musicxml(tmp)
        except Exception as e:
            raise HTTPException(400, f'MusicXML 파싱 실패: {e}')
        return {'type': 'musicxml', 'score': model_to_scorein(sc),
                'message': 'MusicXML 파싱 완료 — 편곡 설정으로 진행하세요.'}
    # 이미지/PDF → OCR(오선 감지)
    pages = []
    if name.endswith('.pdf'):
        try:
            pages = ocr.pdf_to_images(data)
        except Exception as e:
            raise HTTPException(400, f'PDF 처리 실패: {e}')
        if not pages:
            raise HTTPException(400, 'PDF에서 페이지를 추출할 수 없습니다.')
        first = ocr.analyze_score_image(pages[0])
    elif name.endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp')):
        first = ocr.analyze_score_image(data)
    else:
        raise HTTPException(400, '지원 형식: PDF, PNG, JPG (또는 MusicXML)')
    return {'type': 'image', 'pages': len(pages) if pages else 1, 'ocr': first,
            'message': '악보 이미지를 분석했습니다. 편집기에서 멜로디·코드·가사를 확인/입력해 주세요.'}


@app.post('/api/arrange')
def arrange(req: ArrangeRequest):
    """편곡 실행 → PDF/MusicXML/MIDI 생성"""
    if req.arrangement not in ARRANGEMENTS:
        raise HTTPException(400, 'arrangement는 duo 또는 quartet')
    if req.page_size not in ('A4', 'Letter'):
        raise HTTPException(400, 'page_size는 A4 또는 Letter')
    if req.lang not in ('kr', 'en'):
        raise HTTPException(400, 'lang은 kr 또는 en')
    if req.transpose_to and req.transpose_to not in KEY_FIFTHS:
        raise HTTPException(400, '지원하지 않는 조(key)')

    sc = score_to_model(req.score)
    if not sc.measures:
        raise HTTPException(400, '악보에 마디가 없습니다')
    work, parts = run_arrangement(sc, req.arrangement, req.transpose_to, req.tempo)
    parts_order = ARRANGEMENTS[req.arrangement]['parts']

    uid = uuid.uuid4().hex
    pdf_path = os.path.join(OUTPUT_DIR, f'{uid}.pdf')
    mx_path = os.path.join(OUTPUT_DIR, f'{uid}.musicxml')
    midi_path = os.path.join(OUTPUT_DIR, f'{uid}.mid')

    # PDF
    eng = Engraver(parts_order, lang=req.lang, page_size=req.page_size,
                   lyrics_on=req.lyrics_on, page_numbers=req.page_numbers)
    eng.render(work, parts, pdf_path)

    # MusicXML (파트별)
    _write_parts_musicxml(work, parts, parts_order, mx_path)

    # MIDI (간단 포맷 0)
    _write_midi(work, parts, parts_order, midi_path)

    label = ARRANGEMENTS[req.arrangement]['label_kr']
    return {
        'job_id': uid,
        'pdf': f'/api/output/{uid}.pdf',
        'musicxml': f'/api/output/{uid}.musicxml',
        'midi': f'/api/output/{uid}.mid',
        'title': work.title, 'key': work.key, 'tempo': work.tempo,
        'arrangement_label': label, 'parts': parts_order,
        'measures': len(work.measures),
    }


def _write_parts_musicxml(score: Score, parts: list, parts_order: List[str], path: str):
    """편곡 결과를 파트별 MusicXML로 저장"""
    import xml.etree.ElementTree as ET
    from .model import KEY_FIFTHS
    root = ET.Element('score-partwise', {'version': '3.1'})
    work = ET.SubElement(root, 'work')
    ET.SubElement(work, 'work-title').text = score.title
    pl = ET.SubElement(root, 'part-list')
    for i, p in enumerate(parts_order, start=1):
        sp = ET.SubElement(pl, 'score-part', {'id': f'P{i}'})
        ET.SubElement(sp, 'part-name').text = INSTRUMENTS[p]['en']
    divisions = 4
    for pi, p in enumerate(parts_order, start=1):
        part_el = ET.SubElement(root, 'part', {'id': f'P{pi}'})
        for mi, m in enumerate(score.measures, start=1):
            meas = ET.SubElement(part_el, 'measure', {'number': str(mi)})
            if mi == 1:
                attrs = ET.SubElement(meas, 'attributes')
                ET.SubElement(attrs, 'divisions').text = str(divisions)
                k = ET.SubElement(attrs, 'key')
                ET.SubElement(k, 'fifths').text = str(KEY_FIFTHS.get(score.key, (0, 'major'))[0])
                t = ET.SubElement(attrs, 'time')
                ET.SubElement(t, 'beats').text = str(score.time[0])
                ET.SubElement(t, 'beat-type').text = str(score.time[1])
                clef = ET.SubElement(attrs, 'clef')
                ET.SubElement(clef, 'sign').text = {'treble': 'G', 'alto': 'C', 'bass': 'F'}[INSTRUMENTS[p]['clef']]
                ET.SubElement(clef, 'line').text = {'treble': '2', 'alto': '3', 'bass': '4'}[INSTRUMENTS[p]['clef']]
            notes = parts[mi - 1].get(p, [])
            if not notes:
                n = ET.SubElement(meas, 'note')
                ET.SubElement(n, 'rest')
                ET.SubElement(n, 'duration').text = str(int(score.time[0] * divisions))
                continue
            for n in notes:
                ne = ET.SubElement(meas, 'note')
                if n.is_rest:
                    ET.SubElement(ne, 'rest')
                else:
                    pit = ET.SubElement(ne, 'pitch')
                    ET.SubElement(pit, 'step').text = n.step
                    if n.alter:
                        ET.SubElement(pit, 'alter').text = str(n.alter)
                    ET.SubElement(pit, 'octave').text = str(n.octave)
                ET.SubElement(ne, 'duration').text = str(int(round(n.duration * divisions)))
                typ = {4.0: 'whole', 2.0: 'half', 1.0: 'quarter', 0.5: 'eighth', 0.25: '16th'}.get(n.duration, 'quarter')
                ET.SubElement(ne, 'type').text = typ
                if n.dots:
                    for _ in range(n.dots):
                        ET.SubElement(ne, 'dot')
                if pi == 1 and n.lyric:
                    ly = ET.SubElement(ne, 'lyric', {'number': '1'})
                    ET.SubElement(ly, 'text').text = n.lyric
    ET.ElementTree(root).write(path, encoding='UTF-8', xml_declaration=True)


def _write_midi(score: Score, parts: list, parts_order: List[str], path: str):
    """간단한 MIDI 포맷 0 저장 (재생 미리듣기용)"""
    import struct
    tracks = []
    # 트랙 1: 메타 (템포)
    tempo_us = int(60_000_000 / max(score.tempo, 1))
    tr = [0x00, 0xff, 0x51, 0x03, (tempo_us >> 16) & 0xff, (tempo_us >> 8) & 0xff, tempo_us & 0xff]
    tracks.append(tr)
    # 트랙 2: 모든 파트 합침 (채널별)
    tr = []
    tick = 480
    for mi, m in enumerate(score.measures):
        for pi, p in enumerate(parts_order):
            ch = pi
            for n in parts[mi].get(p, []):
                if n.is_rest:
                    continue
                dur_ticks = int(round(n.duration * tick))
                vel = 70 - pi * 5
                tr += [0x00, 0x90 | ch, n.midi, vel]
                tr += _varint(dur_ticks)
                tr += [0x80 | ch, n.midi, 0]
    tr += [0x00, 0xff, 0x2f, 0x00]
    tracks.append(tr)
    header = b'MThd' + struct.pack('>IHHH', 6, 0, len(tracks), tick)
    out = header
    for t in tracks:
        out += b'MTrk' + struct.pack('>I', len(t)) + bytes(t)
    with open(path, 'wb') as f:
        f.write(out)


def _varint(v: int) -> bytes:
    out = [v & 0x7f]
    v >>= 7
    while v:
        out.append(0x80 | (v & 0x7f))
        v >>= 7
    return bytes(reversed(out))


@app.get('/api/output/{fname}')
def output_file(fname: str):
    if not re.fullmatch(r'[0-9a-f]{32}\.(pdf|musicxml|mid)', fname):
        raise HTTPException(400, '잘못된 파일명')
    path = os.path.join(OUTPUT_DIR, fname)
    if not os.path.exists(path):
        raise HTTPException(404, '파일 없음')
    media = {'pdf': 'application/pdf', 'musicxml': 'application/vnd.recordare.musicxml', 'mid': 'audio/midi'}[fname.split('.')[-1]]
    return FileResponse(path, media_type=media, filename=fname)


# ---------- 정적 프론트엔드 ----------
if os.path.isdir(FRONTEND_DIR):
    app.mount('/', StaticFiles(directory=FRONTEND_DIR, html=True), name='frontend')
