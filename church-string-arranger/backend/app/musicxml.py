# -*- coding: utf-8 -*-
"""Church String Arranger - MusicXML 읽기/쓰기 (score-partwise, 단순 악보 서브셋)"""
from __future__ import annotations
import xml.etree.ElementTree as ET
from typing import List, Optional
from .model import Note, Chord, Measure, Score

NS = {'m': 'http://www.musicxml.org/ns/musicxml-3.1'}
_DUR_TYPE = {4.0: 'whole', 2.0: 'half', 1.0: 'quarter', 0.5: 'eighth', 0.25: '16th', 0.125: '32nd'}

# ---------- 쓰기 ----------

def _type_of(duration: float) -> str:
    t = _DUR_TYPE.get(duration)
    if t:
        return t
    # dotted 처리
    for base, name in _DUR_TYPE.items():
        if abs(duration - base * 1.5) < 1e-6:
            return name
        if abs(duration - base * 1.75) < 1e-6:
            return name
    # 가장 가까운 타입
    best = min(_DUR_TYPE.items(), key=lambda kv: abs(kv[0] - duration))
    return best[1]


def _fifths_of(key: str) -> int:
    from .model import KEY_FIFTHS
    return KEY_FIFTHS.get(key, (0, 'major'))[0]


def write_musicxml(score: Score, path: str, part_names: Optional[List[str]] = None) -> None:
    """내부 모델 → MusicXML 파일 (멜로디 파트 + 코드)"""
    root = ET.Element('score-partwise', {'version': '3.1'})
    work = ET.SubElement(root, 'work')
    ET.SubElement(work, 'work-title').text = score.title

    # part-list
    pl = ET.SubElement(root, 'part-list')
    score_part = ET.SubElement(pl, 'score-part', {'id': 'P1'})
    ET.SubElement(score_part, 'part-name').text = part_names[0] if part_names else 'Melody'

    part = ET.SubElement(root, 'part', {'id': 'P1'})
    for i, m in enumerate(score.measures, start=1):
        meas = ET.SubElement(part, 'measure', {'number': str(i)})
        if i == 1:
            attrs = ET.SubElement(meas, 'attributes')
            ET.SubElement(attrs, 'divisions').text = '4'
            k = ET.SubElement(attrs, 'key')
            ET.SubElement(k, 'fifths').text = str(_fifths_of(score.key))
            ET.SubElement(k, 'mode').text = 'major' if not score.key.endswith('m') else 'minor'
            t = ET.SubElement(attrs, 'time')
            ET.SubElement(t, 'beats').text = str(score.time[0])
            ET.SubElement(t, 'beat-type').text = str(score.time[1])
            clef = ET.SubElement(attrs, 'clef')
            ET.SubElement(clef, 'sign').text = 'G'
            ET.SubElement(clef, 'line').text = '2'
        # 코드
        if m.chords and any(m.chords):
            harmony = ET.SubElement(meas, 'harmony')
            chord0 = next((c for c in m.chords if c), None)
            if chord0:
                root_el = ET.SubElement(harmony, 'root')
                ET.SubElement(root_el, 'root-step').text = chord0.root
                if chord0.alter:
                    ET.SubElement(root_el, 'root-alter').text = str(chord0.alter)
                if chord0.quality in ('', 'm', '7', 'm7', 'M7', 'dim', 'aug', 'sus4', 'sus2', '6', 'm6', '5'):
                    kind = ET.SubElement(harmony, 'kind', {'text': str(chord0)})
                    kind.text = chord0.quality if chord0.quality else 'major'
        # 음표
        if not m.notes:
            n = ET.SubElement(meas, 'note')
            ET.SubElement(n, 'rest')
            ET.SubElement(n, 'duration').text = str(int(score.time[0] * 4))
            ET.SubElement(n, 'type').text = _type_of(float(score.time[0]))
            continue
        for n in m.notes:
            note = ET.SubElement(meas, 'note')
            if n.is_rest:
                ET.SubElement(note, 'rest')
            else:
                p = ET.SubElement(note, 'pitch')
                ET.SubElement(p, 'step').text = n.step
                if n.alter:
                    ET.SubElement(p, 'alter').text = str(n.alter)
                ET.SubElement(p, 'octave').text = str(n.octave)
            ET.SubElement(note, 'duration').text = str(int(round(n.duration * 4)))
            ET.SubElement(note, 'type').text = _type_of(n.duration)
            if n.dots:
                for _ in range(n.dots):
                    ET.SubElement(note, 'dot')
            if n.lyric:
                ly = ET.SubElement(note, 'lyric', {'number': '1'})
                ET.SubElement(ly, 'text').text = n.lyric
    ET.ElementTree(root).write(path, encoding='UTF-8', xml_declaration=True)


# ---------- 읽기 ----------

def _find(el: ET.Element, tag: str, ns=NS):
    return el.find('m:' + tag, ns) if ns else el.find(tag)


def _text(el: Optional[ET.Element]) -> str:
    return (el.text or '').strip() if el is not None else ''


def read_musicxml(path: str) -> Score:
    """MusicXML → 내부 모델 (멜로디 + 코드 + 가사)"""
    tree = ET.parse(path)
    root = tree.getroot()
    # namespaces 자동 감지
    ns = {}
    if '}' in root.tag:
        ns['m'] = root.tag.split('}')[0].strip('{')
    else:
        ns['m'] = ''

    def f(el, tag):
        return el.find('m:' + tag, ns) if ns.get('m') else el.find(tag)

    title = ''
    w = f(root, 'work')
    if w is not None:
        title = _text(f(w, 'work-title'))
    key, time_sig, tempo = 'C', (4, 4), 90
    measures: List[Measure] = []
    part = root.find('m:part', ns) if ns.get('m') else root.find('part')
    if part is None:
        return Score(title=title or 'MusicXML', key=key, time=time_sig, tempo=tempo)
    cur_chord: Optional[Chord] = None
    for meas_el in part.findall('m:measure', ns) if ns.get('m') else part.findall('measure'):
        attrs = f(meas_el, 'attributes')
        if attrs is not None:
            k = f(attrs, 'key')
            if k is not None:
                fifths = int(_text(f(k, 'fifths')) or 0)
                mode = _text(f(k, 'mode'))
                key = _key_from_fifths(fifths, mode)
            t = f(attrs, 'time')
            if t is not None:
                time_sig = (int(_text(f(t, 'beats')) or 4), int(_text(f(t, 'beat-type')) or 4))
        m = Measure()
        for note_el in meas_el.findall('m:note', ns) if ns.get('m') else meas_el.findall('note'):
            is_chord = f(note_el, 'chord') is not None
            rest = f(note_el, 'rest')
            dur_el = f(note_el, 'duration')
            dur = (int(_text(dur_el)) / 4.0) if dur_el is not None else 1.0
            dots = len(note_el.findall('m:dot', ns)) if ns.get('m') else len(note_el.findall('dot'))
            if rest is not None:
                m.notes.append(Note.rest(dur, dots))
                continue
            p = f(note_el, 'pitch')
            if p is None:
                continue
            step = _text(f(p, 'step'))
            alter = int(_text(f(p, 'alter')) or 0)
            octave = int(_text(f(p, 'octave')) or 4)
            ly = f(note_el, 'lyric')
            lyric = _text(f(ly, 'text')) if ly is not None else ''
            if is_chord:
                # 화음은 무시 (멜로디만)
                continue
            n = Note(step=step, alter=alter, octave=octave, duration=dur, dots=dots, lyric=lyric)
            m.notes.append(n)
        # 코드 하모니
        for harm in meas_el.findall('m:harmony', ns) if ns.get('m') else meas_el.findall('harmony'):
            r = f(harm, 'root')
            if r is not None:
                step = _text(f(r, 'root-step'))
                alt = int(_text(f(r, 'root-alter')) or 0)
                kind_el = f(harm, 'kind')
                kind = _text(kind_el)
                qmap = {'major': '', 'minor': 'm', 'dominant': '7', 'diminished': 'dim',
                        'augmented': 'aug', 'major-seventh': 'M7', 'minor-seventh': 'm7',
                        'dominant-seventh': '7', 'suspended-fourth': 'sus4', 'suspended-second': 'sus2',
                        'major-sixth': '6', 'minor-sixth': 'm6'}
                q = qmap.get(kind, '')
                cur_chord = Chord(step, alt, q)
        m.chords = [cur_chord] * time_sig[0]
        measures.append(m)
    return Score(title=title or '불러온 악보', key=key, time=time_sig, tempo=tempo, measures=measures)


def _key_from_fifths(fifths: int, mode: str) -> str:
    from .model import KEY_FIFTHS
    for k, (f, md) in KEY_FIFTHS.items():
        if f == fifths and md == (mode or 'major'):
            return k
    return 'C'
