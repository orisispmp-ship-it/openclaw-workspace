# -*- coding: utf-8 -*-
"""Church String Arranger - 규칙 기반 화성/편곡 엔진

원칙 (PRD):
- 자연스러운 화성 (코드 톤 우선, 3도/6도 진행)
- 연주하기 쉬운 운지 (도약 최소화, 악기 음역 준수)
- 멜로디 유지 (바이올린 1 = 원곡 멜로디)
- 예배용 편곡 (절제된 리듬, 가사 유지)
"""
from __future__ import annotations
from typing import List, Optional, Tuple
from .model import Note, Chord, Score, Measure, INSTRUMENTS, CHORD_INTERVALS, spell_pitch_class

# ---------- 유틸 ----------

def _chord_tones_pc(chord: Optional[Chord]) -> List[int]:
    if chord is None:
        return [0, 4, 7]  # C
    return [(chord.root_pc + iv) % 12 for iv in chord.intervals()]


def _nearest_chord_tone(chord: Optional[Chord], midi: int) -> int:
    """midi 피치에 가장 가까운 코드 톤 (옥타브 고려)"""
    pcs = _chord_tones_pc(chord)
    best, bestd = midi, 999
    for pc in pcs:
        cand = pc + 12 * ((midi - pc) // 12)
        for c in (cand, cand + 12, cand - 12):
            if abs(c - midi) < bestd:
                best, bestd = c, abs(c - midi)
    return best


def _clamp(note: Note, rng: Tuple[int, int]) -> Note:
    """음역 밖이면 옥타브 이동으로 보정"""
    m = note.midi
    if m < rng[0]:
        note = Note.from_midi(m + 12, note.duration)
        note.lyric = ''
        return note
    if m > rng[1]:
        note = Note.from_midi(m - 12, note.duration)
        note.lyric = ''
        return note
    return note


# ---------- 2중주 (바이올린 1 + 바이올린 2) ----------

def _harmony_below(melody_midi: int, chord: Optional[Chord]) -> int:
    """멜로디 아래 3도/6도 중 코드 톤 우선 하모니 음정 계산"""
    third = _nearest_chord_tone(chord, melody_midi - 4)  # 3도 아래
    # 3도 아래가 너무 낮으면 (G3 아래) 6도 위로
    if third < 55:  # G3
        sixth = _nearest_chord_tone(chord, melody_midi + 9)  # 6도 위
        return sixth
    return third


def arrange_duo(score: Score) -> list:
    """바이올린 2중주: V1=멜로디, V2=3도/6도 하모니 → 마디별 파트 구조"""
    out = []
    for m in score.measures:
        chord = m.chords[0] if m.chords else None
        v1: List[Note] = []
        v2: List[Note] = []
        for n in m.notes:
            v1.append(n)
            if n.is_rest:
                v2.append(Note.rest(n.duration, n.dots))
            else:
                h = _harmony_below(n.midi, chord)
                hn = Note.from_midi(h, n.duration)
                hn.dots = n.dots
                hn = _clamp(hn, INSTRUMENTS['violin2']['range'])
                v2.append(hn)
        out.append({'violin1': v1, 'violin2': v2})
    return out


# ---------- 현악 4중주 ----------

def _bass_line(score: Score) -> List[List[Note]]:
    """첼로: 코드 루트 기반 베이스 라인 (도약 최소화, 자리바꿈) → 마디별"""
    out: List[List[Note]] = []
    prev: Optional[int] = None
    for m in score.measures:
        chord = m.chords[0] if m.chords else None
        beats = sum(n.duration for n in m.notes) or score.time[0]
        if chord is None:
            out.append([Note.rest(beats)])
            continue
        cands = [pc + 12 * ((36 - pc) // 12) for pc in [chord.root_pc, (chord.root_pc + 7) % 12, (chord.root_pc + 3) % 12]]
        cands = sorted(set(c + 12 * k for c in cands for k in range(3) if 36 <= c + 12 * k <= 60))
        if prev is None:
            pick = min(cands, key=lambda c: abs(c - 43))  # G2 근처
        else:
            pick = min(cands, key=lambda c: abs(c - prev))
        prev = pick
        n = Note.from_midi(pick, beats)
        out.append([n])
    return out


def _viola_line(score: Score, bass_notes: List[Note]) -> List[List[Note]]:
    """비올라: 코드 톤 필러 (중간 음역, 멜로디 리듬) → 마디별"""
    out: List[List[Note]] = []
    prev: Optional[int] = None
    for m in score.measures:
        chord = m.chords[0] if m.chords else None
        meas: List[Note] = []
        for n in m.notes:
            if n.is_rest:
                meas.append(Note.rest(n.duration, n.dots))
                continue
            pcs = _chord_tones_pc(chord)
            cands = sorted(set(pc + 12 * k for pc in pcs for k in (4, 5, 6) if 48 <= pc + 12 * k <= 76))
            if prev is None:
                pick = min(cands, key=lambda c: abs(c - 57))  # A3
            else:
                pick = min(cands, key=lambda c: abs(c - prev))
            prev = pick
            v = Note.from_midi(pick, n.duration)
            v.dots = n.dots
            meas.append(v)
        out.append(meas)
    return out


def arrange_quartet(score: Score) -> list:
    """현악 4중주: V1=멜로디, V2=하모니, Va=필러, Vc=베이스 → 마디별 파트 구조"""
    duo = arrange_duo(score)  # list of dicts
    bass = _bass_line(score)
    viola = _viola_line(score, bass)
    out = []
    for i, m in enumerate(score.measures):
        v2 = [_clamp(n, INSTRUMENTS['violin2']['range']) for n in duo[i]['violin2']]
        out.append({'violin1': duo[i]['violin1'], 'violin2': v2,
                    'viola': viola[i], 'cello': bass[i]})
    return out


# ---------- 조옮김 ----------

def transpose_score(score: Score, new_key: str) -> Score:
    """전체 악보를 새 조로 이동 (장조 기준 반음 계산)"""
    from .model import KEY_FIFTHS, STEP_INDEX
    old = KEY_FIFTHS.get(score.original_key, (0, 'major'))
    new = KEY_FIFTHS.get(new_key)
    if new is None:
        return score
    delta = (new[0] - old[0]) * 7 % 12  # 5도권 차이 → 반음 수
    # 실제로는 근음 기준으로 계산하는 게 안전
    old_root = STEP_INDEX[score.original_key[0]] + (1 if score.original_key.endswith('#') else -1 if score.original_key.endswith('b') else 0)
    new_root = STEP_INDEX[new_key[0]] + (1 if new_key.endswith('#') else -1 if new_key.endswith('b') else 0)
    delta = (new_root - old_root) % 12
    ns = Score(title=score.title, composer=score.composer, arranger=score.arranger,
               key=new_key, time=score.time, tempo=score.tempo, original_key=score.original_key)
    for m in score.measures:
        nm = Measure(chords=[Chord(c.root, c.alter, c.quality) if c else None for c in m.chords])
        # 코드도 이동
        for i, c in enumerate(nm.chords):
            if c:
                new_pc = (c.root_pc + delta) % 12
                # 새 조 기준 스펠링
                from .model import spell_pitch_class
                step, alt = spell_pitch_class(new_pc, new_key)
                nm.chords[i] = Chord(root=step, alter=alt, quality=c.quality)
        for n in m.notes:
            nm.notes.append(n.transposed(delta, new_key))
        ns.measures.append(nm)
    return ns


# ---------- 악보 단위 편곡 실행 ----------

ARRANGEMENTS = {
    'duo': {'parts': ['violin1', 'violin2'], 'label_kr': '바이올린 2중주', 'label_en': 'Violin Duet'},
    'quartet': {'parts': ['violin1', 'violin2', 'viola', 'cello'], 'label_kr': '현악 4중주', 'label_en': 'String Quartet'},
}


def run_arrangement(score: Score, arrangement: str = 'duo', transpose_to: Optional[str] = None,
                    tempo: Optional[int] = None) -> Tuple[Score, list]:
    """편곡 실행 → (최종 악보, 마디별 파트 구조: [{'violin1':[Note], ...}, ...])"""
    work = score
    if transpose_to and transpose_to != score.key:
        work = transpose_score(work, transpose_to)
    if tempo:
        work.tempo = tempo
    if arrangement == 'quartet':
        parts = arrange_quartet(work)
    else:
        parts = arrange_duo(work)
    return work, parts
