# -*- coding: utf-8 -*-
"""Church String Arranger - 내장 샘플 찬송가 (퍼블릭 도메인 멜로디)"""
from __future__ import annotations
from typing import List, Tuple
from .model import Note, Chord, Measure, Score


def _measure(notes: List[Tuple[str, int, float]], chords: List[str], lyric: str = '') -> Measure:
    """notes: (step, octave, duration), chords: 코드 진행, lyric: 띄어쓰기 구분 가사"""
    m = Measure()
    syllables = lyric.split() if lyric else []
    for i, (step, octv, dur) in enumerate(notes):
        lyr = syllables[i] if i < len(syllables) else ''
        m.notes.append(Note(step=step, octave=octv, duration=dur, lyric=lyr))
    m.chords = [Chord.parse(c) for c in chords]
    return m


def _lyric_notes(notes: List[Tuple[str, int, float]], lyric_syllables: List[str]) -> List[Tuple[str, int, float]]:
    """가사를 음표 수에 맞게 분배 (가사 없으면 공백)"""
    return notes


def sample_amazing_grace() -> Score:
    """주 은혜 (Amazing Grace) — G장조 4/4, 8마디 (퍼블릭 도메인)"""
    # 멜로디 (G4~D5)
    mel = [
        # 1: G G A G B
        [('G', 4, 1.0), ('G', 4, 1.0), ('A', 4, 1.0), ('G', 4, 1.0)],
        [('B', 4, 2.0), ('G', 4, 1.0), ('G', 4, 1.0)],
        # 3
        [('G', 4, 1.0), ('G', 4, 1.0), ('A', 4, 1.0), ('G', 4, 1.0)],
        [('C', 5, 2.0), ('B', 4, 1.0), ('G', 4, 1.0)],
        # 5
        [('D', 5, 1.0), ('D', 5, 1.0), ('B', 4, 1.0), ('A', 4, 1.0)],
        [('G', 4, 2.0), ('A', 4, 1.0), ('B', 4, 1.0)],
        # 7
        [('G', 4, 1.0), ('A', 4, 1.0), ('G', 4, 1.0), ('E', 4, 1.0)],
        [('D', 4, 3.0), ('D', 4, 1.0)],
    ]
    chords = [
        ['G', 'G', 'D', 'G'], ['G', 'C', 'G', 'D'],
        ['G', 'G', 'D', 'G'], ['G', 'C', 'G', 'G'],
        ['D', 'D', 'G', 'Em'], ['C', 'G', 'D', 'D'],
        ['G', 'G', 'C', 'G'], ['G', 'D', 'G', 'G'],
    ]
    lyrics = [
        '나 같은 죄인 살리신', '주 은혜 놀라워',
        '잃었던 생명 찾았네', '주 은혜 놀라워',
        '나 같은 죄인 살리신', '주 은혜 놀라워',
        '잃었던 생명 찾았네', '주 은혜 놀라워',
    ]
    measures = []
    for i, m in enumerate(mel):
        measures.append(_measure(m, chords[i], lyrics[i]))
    return Score(title='주 은혜 (Amazing Grace)', composer='전통 찬송 (퍼블릭 도메인)',
                 arranger='Carmen (AI)', key='G', time=(4, 4), tempo=84,
                 original_key='G', measures=measures)


def sample_ode_to_joy() -> Score:
    """기쁨의 노래 (Ode to Joy) — C장조 4/4, 8마디 (베토벤, 퍼블릭 도메인)"""
    mel = [
        [('E', 4, 1.0), ('E', 4, 1.0), ('F', 4, 1.0), ('G', 4, 1.0)],
        [('G', 4, 1.0), ('F', 4, 1.0), ('E', 4, 1.0), ('D', 4, 1.0)],
        [('C', 4, 1.0), ('C', 4, 1.0), ('D', 4, 1.0), ('E', 4, 1.0)],
        [('E', 4, 1.5), ('D', 4, 0.5), ('D', 4, 2.0)],
        [('E', 4, 1.0), ('E', 4, 1.0), ('F', 4, 1.0), ('G', 4, 1.0)],
        [('G', 4, 1.0), ('F', 4, 1.0), ('E', 4, 1.0), ('D', 4, 1.0)],
        [('C', 4, 1.0), ('C', 4, 1.0), ('D', 4, 1.0), ('E', 4, 1.0)],
        [('D', 4, 1.5), ('C', 4, 0.5), ('C', 4, 2.0)],
    ]
    chords = [
        ['C', 'C', 'F', 'C'], ['G', 'C', 'G', 'G'],
        ['C', 'C', 'F', 'C'], ['G', 'C', 'G', 'G'],
        ['C', 'C', 'F', 'C'], ['G', 'C', 'G', 'G'],
        ['C', 'C', 'F', 'C'], ['G', 'C', 'C', 'C'],
    ]
    lyrics = [
        '기쁨의 노래 함께', '부르자 모두',
        '화합하여 찬양', '소리 높여',
        '기쁨의 노래 함께', '부르자 모두',
        '화합하여 찬양', '소리 높여',
    ]
    measures = []
    for i, m in enumerate(mel):
        measures.append(_measure(m, chords[i], lyrics[i]))
    return Score(title='기쁨의 노래 (Ode to Joy)', composer='L. v. Beethoven (퍼블릭 도메인)',
                 arranger='Carmen (AI)', key='C', time=(4, 4), tempo=100,
                 original_key='C', measures=measures)


def sample_come_thou_fount() -> Score:
    """만복의 근원 (Come, Thou Fount) — G장조 4/4, 8마디 (넬턴 선율, 퍼블릭 도메인)"""
    mel = [
        [('D', 5, 1.0), ('G', 4, 1.0), ('A', 4, 1.0), ('B', 4, 1.0)],
        [('C', 5, 1.0), ('B', 4, 1.0), ('A', 4, 1.0), ('G', 4, 1.0)],
        [('A', 4, 1.0), ('B', 4, 1.0), ('C', 5, 1.0), ('D', 5, 1.0)],
        [('E', 5, 2.0), ('D', 5, 1.0), ('B', 4, 1.0)],
        [('D', 5, 1.0), ('G', 4, 1.0), ('A', 4, 1.0), ('B', 4, 1.0)],
        [('C', 5, 1.0), ('B', 4, 1.0), ('A', 4, 1.0), ('G', 4, 1.0)],
        [('A', 4, 1.0), ('G', 4, 1.0), ('E', 4, 1.0), ('G', 4, 1.0)],
        [('D', 4, 4.0)],
    ]
    chords = [
        ['G', 'C', 'G', 'G'], ['C', 'G', 'D', 'G'],
        ['Am', 'D', 'G', 'G'], ['C', 'G', 'D', 'D'],
        ['G', 'C', 'G', 'G'], ['C', 'G', 'D', 'G'],
        ['Am', 'D', 'G', 'C'], ['G', 'D', 'G', 'G'],
    ]
    lyrics = [
        '만복의 근원', '하나님',
        '우리 모두', '찬송하세',
        '천사들의', '목소리로',
        '주를 찬양', '하리로다',
    ]
    measures = []
    for i, m in enumerate(mel):
        measures.append(_measure(m, chords[i], lyrics[i]))
    return Score(title='만복의 근원 (Come, Thou Fount)', composer='Nettleton 선율 (퍼블릭 도메인)',
                 arranger='Carmen (AI)', key='G', time=(4, 4), tempo=88,
                 original_key='G', measures=measures)


SAMPLES = {
    'amazing_grace': {'id': 'amazing_grace', 'title': '주 은혜 (Amazing Grace)', 'key': 'G', 'time': '4/4', 'build': sample_amazing_grace},
    'ode_to_joy': {'id': 'ode_to_joy', 'title': '기쁨의 노래 (Ode to Joy)', 'key': 'C', 'time': '4/4', 'build': sample_ode_to_joy},
    'come_thou_fount': {'id': 'come_thou_fount', 'title': '만복의 근원 (Come, Thou Fount)', 'key': 'G', 'time': '4/4', 'build': sample_come_thou_fount},
}


def get_sample(sample_id: str) -> Score:
    return SAMPLES[sample_id]['build']()
