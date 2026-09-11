# -*- coding: utf-8 -*-
"""Church String Arranger - 음악 데이터 모델"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List

# ---------- 기본 상수 ----------
STEP_INDEX = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}
INDEX_STEP = {v: k for k, v in STEP_INDEX.items()}

# 악기 정의 (이름 한글/영문, 클레프, 음역)
INSTRUMENTS = {
    'violin1': {'kr': '바이올린 1', 'en': 'Violin I', 'clef': 'treble', 'range': (55, 88)},   # G3 ~ E6
    'violin2': {'kr': '바이올린 2', 'en': 'Violin II', 'clef': 'treble', 'range': (55, 84)},  # G3 ~ C6
    'viola':   {'kr': '비올라', 'en': 'Viola', 'clef': 'alto', 'range': (48, 76)},            # C3 ~ E5
    'cello':   {'kr': '첼로', 'en': 'Cello', 'clef': 'bass', 'range': (36, 64)},              # C2 ~ E4
}


@dataclass
class Note:
    """음표. step: C~B, alter: -2..2 (플랫/샤프), octave: 과학적 표기 (C4=중앙 도)"""
    step: str
    alter: int = 0
    octave: int = 4
    duration: float = 1.0          # 박 (quarter=1)
    dots: int = 0
    is_rest: bool = False
    lyric: str = ''                # 가사 음절
    tied: bool = False             # 이전 음과 붙임줄

    @property
    def pitch_class(self) -> int:
        return (STEP_INDEX[self.step] + self.alter) % 12

    @property
    def midi(self) -> int:
        return (self.octave + 1) * 12 + self.pitch_class

    @property
    def duration_beats(self) -> float:
        d = self.duration
        for _ in range(self.dots):
            d += self.duration / (2 ** (self.dots))
        return self.duration * (1 + 0.5 + (0.25 if self.dots >= 2 else 0)) if self.dots else self.duration

    @staticmethod
    def rest(duration: float, dots: int = 0) -> 'Note':
        return Note(step='C', alter=0, octave=4, duration=duration, dots=dots, is_rest=True)

    @staticmethod
    def from_midi(midi: int, duration: float = 1.0) -> 'Note':
        pc = midi % 12
        octave = midi // 12 - 1
        # 자연스러운 스펠링 (C장조 기준)
        for step, idx in STEP_INDEX.items():
            for alt in (0, 1, -1, 2, -2):
                if (idx + alt) % 12 == pc:
                    return Note(step=step, alter=alt, octave=octave, duration=duration)
        return Note(step='C', alter=0, octave=octave, duration=duration)

    def transposed(self, delta_pc: int, new_key: Optional[str] = None) -> 'Note':
        """반음 이동 + 새 조에 맞는 스펠링 보정"""
        if self.is_rest:
            return self
        pc = (self.pitch_class + delta_pc) % 12
        octave = self.octave + (self.pitch_class + delta_pc) // 12
        step, alter = spell_pitch_class(pc, new_key)
        return Note(step=step, alter=alter, octave=octave, duration=self.duration,
                    dots=self.dots, lyric=self.lyric, tied=self.tied)


@dataclass
class Chord:
    """코드 심볼 (예: C, Am, G7, Dsus4)"""
    root: str          # C, D, E, F, G, A, B (with alter)
    alter: int = 0
    quality: str = ''  # '', 'm', '7', 'm7', 'maj7', 'dim', 'aug', 'sus4', 'sus2', '6', 'm6', '5'

    def __post_init__(self):
        self.quality = self.quality.replace('maj7', 'M7')  # 정규화

    @property
    def root_pc(self) -> int:
        return (STEP_INDEX[self.root] + self.alter) % 12

    def intervals(self) -> List[int]:
        return CHORD_INTERVALS.get(self.quality, CHORD_INTERVALS[''])

    @staticmethod
    def parse(text: str) -> Optional['Chord']:
        t = text.strip()
        if not t:
            return None
        quality = ''
        root_ch = t[0].upper()
        if root_ch not in STEP_INDEX:
            return None
        i = 1
        alter = 0
        if i < len(t) and t[i] in '#♯b♭':
            alter = 1 if t[i] in '#♯' else -1
            i += 1
        rest = t[i:]
        qmap = {'': '', 'm': 'm', 'min': 'm', 'M7': 'M7', 'maj7': 'M7', '7': '7', 'm7': 'm7',
                'min7': 'm7', 'dim': 'dim', 'aug': 'aug', '+': 'aug', 'sus4': 'sus4', 'sus': 'sus4',
                'sus2': 'sus2', '6': '6', 'm6': 'm6', '5': '5', 'maj': '', 'M': ''}
        quality = qmap.get(rest)
        if quality is None:
            return None
        return Chord(root=root_ch, alter=alter, quality=quality)

    def __str__(self) -> str:
        return self.root + ('#' if self.alter > 0 else 'b' if self.alter < 0 else '') + \
            {'': '', 'm': 'm', 'M7': 'maj7', '7': '7', 'm7': 'm7', 'dim': 'dim', 'aug': 'aug',
             'sus4': 'sus4', 'sus2': 'sus2', '6': '6', 'm6': 'm6', '5': '5'}[self.quality]


CHORD_INTERVALS = {
    '':    [0, 4, 7],
    'm':   [0, 3, 7],
    '7':   [0, 4, 7, 10],
    'm7':  [0, 3, 7, 10],
    'M7':  [0, 4, 7, 11],
    'dim': [0, 3, 6],
    'aug': [0, 4, 8],
    'sus4': [0, 5, 7],
    'sus2': [0, 2, 7],
    '6':   [0, 4, 7, 9],
    'm6':  [0, 3, 7, 9],
    '5':   [0, 7],
}


def spell_pitch_class(pc: int, key: Optional[str] = None) -> tuple:
    """피치클래스를 주어진 조(key)에 맞는 step/alter로 스펠링"""
    if key:
        ks = key_scale_steps(key)
        for step in ks:
            base = STEP_INDEX[step]
            for alt in (0, 1, -1):
                if (base + alt) % 12 == pc:
                    return step, alt
    for step, base in STEP_INDEX.items():
        for alt in (0, 1, -1):
            if (base + alt) % 12 == pc:
                return step, alt
    for step, base in STEP_INDEX.items():
        for alt in (2, -2):
            if (base + alt) % 12 == pc:
                return step, alt
    return 'C', 0


# 조(key) 관련
KEY_FIFTHS = {  # key -> (fifths, mode)
    'C': (0, 'major'), 'G': (1, 'major'), 'D': (2, 'major'), 'A': (3, 'major'), 'E': (4, 'major'),
    'B': (5, 'major'), 'F#': (6, 'major'), 'C#': (7, 'major'), 'F': (-1, 'major'), 'Bb': (-2, 'major'),
    'Eb': (-3, 'major'), 'Ab': (-4, 'major'), 'Db': (-5, 'major'), 'Gb': (-6, 'major'),
    'Am': (0, 'minor'), 'Em': (1, 'minor'), 'Bm': (2, 'minor'), 'F#m': (3, 'minor'), 'C#m': (4, 'minor'),
    'G#m': (5, 'minor'), 'D#m': (6, 'minor'), 'A#m': (7, 'minor'), 'Dm': (-1, 'minor'),
    'Gm': (-2, 'minor'), 'Cm': (-3, 'minor'), 'Fm': (-4, 'minor'), 'Bbm': (-5, 'minor'), 'Ebm': (-6, 'minor'),
}
SHARP_ORDER = ['F', 'C', 'G', 'D', 'A', 'E', 'B']
FLAT_ORDER = ['B', 'E', 'A', 'D', 'G', 'C', 'F']


def key_scale_steps(key: str) -> List[str]:
    """장조 기준 온음계 (minor는 자연단음계)"""
    fifths, mode = KEY_FIFTHS.get(key, (0, 'major'))
    if fifths >= 0:
        acc_steps = SHARP_ORDER[:fifths]
    else:
        acc_steps = ['*'] * (-fifths)  # placeholder, flat steps handled below
    # 근음 계산
    pc0 = STEP_INDEX[key[0]] + (1 if key.endswith('#') else -1 if key.endswith('b') else 0)
    pc0 %= 12
    if mode == 'major':
        steps_pc = [(pc0 + d) % 12 for d in (0, 2, 4, 5, 7, 9, 11)]
    else:
        steps_pc = [(pc0 + d) % 12 for d in (0, 2, 3, 5, 7, 8, 10)]
    out = []
    for pc in steps_pc:
        best = None
        for step, base in STEP_INDEX.items():
            for alt in (-2, -1, 0, 1, 2):
                if (base + alt) % 12 == pc:
                    if best is None or abs(alt) < abs(best[1]):
                        best = (step, alt)
        out.append(best[0] if best else 'C')
    return out


@dataclass
class Measure:
    """마디: 코드 진행 + 멜로디 음들"""
    chords: List[Optional[Chord]] = field(default_factory=list)   # 박자 단위 (박자 수만큼)
    notes: List[Note] = field(default_factory=list)               # 멜로디 (duration 합 = 박자 수)


@dataclass
class Score:
    title: str = '제목 없음'
    composer: str = ''
    arranger: str = 'Carmen (AI)'
    key: str = 'C'
    time: tuple = (4, 4)
    tempo: int = 90
    measures: List[Measure] = field(default_factory=list)
    original_key: str = 'C'

    def total_beats(self) -> float:
        return sum(m.notes and sum(n.duration for n in m.notes) or self.time[0] for m in self.measures)
