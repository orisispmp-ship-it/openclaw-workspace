# -*- coding: utf-8 -*-
"""Church String Arranger - 악보 PDF 조판기 (matplotlib + PdfPages)

출력 규격 (PRD): 제목, 작곡자, AI 편곡자, 조표, 박자, 가사 포함
- 페이지: A4 / Letter, 페이지 번호, 악기명 한글/영문, 가사 표시/숨기기
"""
from __future__ import annotations
import math
from typing import List, Optional, Tuple

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.backends.backend_pdf import PdfPages

from .model import Note, Score, INSTRUMENTS, KEY_FIFTHS, SHARP_ORDER, FLAT_ORDER

for f in font_manager.fontManager.ttflist:
    if 'Malgun' in f.name:
        plt.rcParams['font.family'] = f.name
        break
plt.rcParams['axes.unicode_minus'] = False

SPACING = 2.2            # 오선 간격 (mm)
LINE_SPAN = SPACING * 4  # 5선 높이
PAGE_SIZES = {'A4': (210.0, 297.0), 'Letter': (215.9, 279.4)}

# 오선 위치 (line0 space0 line1 space1 ... line4) — MIDI 피치
STAFF_POSITIONS = {
    'treble': [64, 65, 67, 69, 71, 72, 74, 76, 77],   # E4 F4 G4 A4 B4 C5 D5 E5 F5
    'alto':   [53, 55, 57, 59, 60, 62, 64, 65, 67],   # F3 G3 A3 B3 C4 D4 E4 F4 G4
    'bass':   [43, 45, 47, 48, 50, 52, 53, 55, 57],   # G2 A2 B2 C3 D3 E3 F3 G3 A3
}

# 보조선(ledger line) 피치 테이블 (오선 밖의 '선' 위치, MIDI)
EXTENDED_LINES = {
    'treble': [43, 47, 50, 55, 59, 62, 64, 67, 71, 74, 77, 81, 84, 88, 91],
    'alto':   [43, 47, 50, 53, 57, 60, 64, 67, 71, 74, 77, 81],
    'bass':   [36, 40, 43, 47, 50, 53, 57, 60, 64, 67, 71],
}
KEYSIG_PITCHES = {
    'treble': {'sharp': [77, 72, 67, 74, 69, 76, 71], 'flat': [71, 76, 69, 74, 67, 72, 77]},
    'alto':   {'sharp': [65, 60, 67, 62, 57, 64, 59], 'flat': [59, 64, 57, 62, 67, 60, 65]},
    'bass':   {'sharp': [53, 48, 55, 50, 57, 52, 47], 'flat': [47, 52, 57, 50, 55, 48, 53]},
}
KEY_KR = {'C': '다장조', 'G': '사장조', 'D': '라장조', 'A': '가장조', 'E': '마장조', 'B': '나장조',
          'F#': '올림바장조', 'C#': '올림다장조', 'F': '바장조', 'Bb': '내림나장조', 'Eb': '내림마장조',
          'Ab': '내림가장조', 'Db': '내림라장조', 'Gb': '내림사장조',
          'Am': '가단조', 'Em': '마단조', 'Bm': '나단조', 'F#m': '올림바단조', 'C#m': '올림다단조',
          'Dm': '라단조', 'Gm': '사단조', 'Cm': '다단조', 'Fm': '바단조', 'Bbm': '내림나단조', 'Ebm': '내림마단조'}


def _fifths(key: str) -> int:
    return KEY_FIFTHS.get(key, (0, 'major'))[0]


def _key_accidentals(key: str) -> dict:
    """조표에 포함된 임시표: {step: alter}"""
    f = _fifths(key)
    out = {}
    if f > 0:
        for s in SHARP_ORDER[:f]:
            out[s] = 1
    elif f < 0:
        for s in FLAT_ORDER[:abs(f)]:
            out[s] = -1
    return out


SYM_FONT = 'DejaVu Sans'  # 음악 기호(♯♭♮♩) 전용 폰트


def _measures_per_line(beats: int) -> int:
    return {4: 4, 3: 5, 2: 6, 6: 4}.get(beats, 4)


class Engraver:
    def __init__(self, parts_order: List[str], lang: str = 'kr', page_size: str = 'A4',
                 lyrics_on: bool = True, page_numbers: bool = True):
        self.parts_order = parts_order
        self.lang = 'kr' if lang == 'kr' else 'en'
        self.page_size = page_size
        self.lyrics_on = lyrics_on
        self.page_numbers = page_numbers
        self.w, self.h = PAGE_SIZES[page_size]
        self.margin = 14.0
        self.title_h = 20.0
        self.staff_gap = 9.0
        self.sys_gap = 12.0
        self.lyrics_h = 5.5

    # ---------- 기하 ----------
    def _pitch_y(self, midi: int, clef: str, staff_y: float) -> float:
        """MIDI 피치 → 오선 위 y좌표 (오선 위치 사이는 비례 보간)"""
        pos = STAFF_POSITIONS[clef]
        half = SPACING / 2
        if midi <= pos[0]:
            return staff_y + (midi - pos[0]) * half
        if midi >= pos[-1]:
            return staff_y + 8 * half + (midi - pos[-1]) * half
        for i in range(len(pos) - 1):
            if midi == pos[i]:
                return staff_y + i * half
            if pos[i] < midi < pos[i + 1]:
                return staff_y + (i + (midi - pos[i]) / (pos[i + 1] - pos[i])) * half
        return staff_y

    def _staff_lines(self, clef: str) -> List[int]:
        return [STAFF_POSITIONS[clef][i] for i in (0, 2, 4, 6, 8)]

    # ---------- 기본 그리기 ----------
    def _draw_staff(self, ax, x0, x1, sy):
        for i in range(5):
            ax.plot([x0, x1], [sy + i * SPACING, sy + i * SPACING], color='black', lw=0.7)

    def _draw_clef(self, ax, x, sy, clef):
        cy = sy + 2 * SPACING  # 모든 클레프의 기준선 (중앙부)
        if clef == 'treble':
            cx = x + 3.0
            # 나선 본체 (G4 기준, 아래로 감김)
            xs, ys = [], []
            for t in range(0, 900, 10):
                th = math.radians(t)
                r = 0.45 + (t / 900) * 1.5
                xs.append(cx + r * math.sin(th) * 1.25)
                ys.append(cy - r * math.cos(th))
            ax.plot(xs, ys, color='black', lw=1.3)
            # 세로 줄기 (D4 ~ B4)
            ax.plot([cx + 1.05, cx + 1.05], [cy - 1.9, cy + 1.5], color='black', lw=1.8)
            # 위 고리
            ax.plot([cx + 1.05, cx + 0.2], [cy + 1.5, cy + 2.1], color='black', lw=1.4)
            ax.plot([cx + 0.2, cx - 0.8], [cy + 2.1, cy + 1.2], color='black', lw=1.4)
            # 아래 고리
            ax.plot([cx - 0.9, cx - 0.2], [cy - 1.2, cy - 1.9], color='black', lw=1.4)
        elif clef == 'bass':
            # F3 기준 커브 + 두 점
            xs, ys = [], []
            for t in range(0, 300, 10):
                th = math.radians(t)
                xs.append(x + 1.3 - 1.0 * math.sin(th))
                ys.append(cy + 0.9 - (t / 300) * 3.2)
            ax.plot(xs, ys, color='black', lw=1.5)
            for dx in (3.5, 4.7):
                ax.plot([x + dx, x + dx], [cy - 0.5, cy + 0.5], color='black', lw=2.2)
        elif clef == 'alto':
            # C4 중심 괄호형
            for sgn in (1, -1):
                xs, ys = [], []
                for t in range(0, 200, 8):
                    th = math.radians(t)
                    xs.append(x + 1.7 - sgn * 1.15 * math.cos(th))
                    ys.append(cy + sgn * 2.1 * math.sin(th))
                ax.plot(xs, ys, color='black', lw=1.5)
            ax.plot([x + 1.7, x + 1.7], [cy - 2.3, cy + 2.3], color='black', lw=1.6)

    def _draw_keysig(self, ax, x, sy, clef, key):
        f = _fifths(key)
        if f == 0:
            return x
        order = SHARP_ORDER if f > 0 else FLAT_ORDER
        pitches = KEYSIG_PITCHES[clef]['sharp' if f > 0 else 'flat']
        for i in range(abs(f)):
            py = self._pitch_y(pitches[i], clef, sy)
            ax.text(x + i * 2.1, py + 0.9, '♯' if f > 0 else '♭', fontsize=10, ha='center', va='center',
                    fontname=SYM_FONT)
        return x + abs(f) * 2.1

    def _draw_timesig(self, ax, x, sy, beats, beat_type):
        ax.text(x + 1.6, sy + 1.5 * SPACING, str(beats), fontsize=9.5, ha='center', va='center')
        ax.text(x + 1.6, sy + 0.5 * SPACING, str(beat_type), fontsize=9.5, ha='center', va='center')

    def _notehead(self, ax, x, y):
        from matplotlib.patches import Ellipse
        ax.add_patch(Ellipse((x, y), 2.6, 1.8, angle=-18, facecolor='black', edgecolor='black', lw=0.8))

    def _draw_rest(self, ax, x, sy, dur, dots):
        mid = sy + 2 * SPACING
        if dur >= 3.9:
            ax.add_patch(plt.Rectangle((x - 1.4, sy + 3 * SPACING - 0.5), 2.8, 1.1, facecolor='black'))
        elif dur >= 1.9:
            ax.add_patch(plt.Rectangle((x - 1.4, sy + 2 * SPACING - 0.5), 2.8, 1.1, facecolor='black'))
        elif dur >= 0.9:
            ax.plot([x - 1.2, x + 0.5], [mid + 1.7, mid - 0.3], color='black', lw=1.2)
            ax.plot([x + 0.5, x - 0.5], [mid - 0.3, mid + 0.9], color='black', lw=1.2)
            ax.plot([x - 0.5, x + 1.2], [mid + 0.9, mid - 1.0], color='black', lw=1.2)
        else:
            ax.plot([x - 0.8, x + 1.0], [mid + 2.0, mid - 0.1], color='black', lw=1.2)
            ax.plot([x + 1.0, x - 1.0], [mid - 0.1, mid + 0.6], color='black', lw=1.2)
            ax.plot([x + 0.6, x + 1.4], [mid + 0.2, mid - 1.5], color='black', lw=1.2)
        for i in range(dots):
            ax.plot([x + 1.9 + i * 1.2, x + 1.9 + i * 1.2], [mid - 1.3, mid - 1.3], 'o', ms=2.6, color='black')

    def _ledger_pitches(self, midi, clef):
        lines = self._staff_lines(clef)
        lo, hi = lines[0], lines[-1]
        ext = EXTENDED_LINES[clef]
        out = []
        if midi < lo:
            out = [p for p in ext if midi <= p < lo]
        elif midi > hi:
            out = [p for p in ext if hi < p <= midi]
        return out

    # ---------- 마디 렌더 ----------
    def _draw_measure_notes(self, ax, mx, sy, clef, notes, meas_w, beats, melody=False,
                            key_acc: Optional[dict] = None):
        total = sum(n.duration for n in notes) or beats
        x = mx + 1.2
        short: List[Tuple[float, float, bool]] = []  # (x, stem_end_y, stem_up)
        for n in notes:
            w = meas_w * n.duration / beats
            if n.is_rest:
                self._draw_rest(ax, x, sy, n.duration, n.dots)
            else:
                y = self._pitch_y(n.midi, clef, sy)
                # 임시표: 조표와 다른 경우에만 표기
                if n.alter:
                    ka = (key_acc or {}).get(n.step, 0)
                    if n.alter != ka:
                        ax.text(x - 1.6, y + 0.9, '♯' if n.alter > 0 else '♭' if n.alter < 0 else '♮',
                                fontsize=8, ha='center', va='center', fontname=SYM_FONT)
                for lp in self._ledger_pitches(n.midi, clef):
                    ly = self._pitch_y(lp, clef, sy)
                    ax.plot([x - 1.7, x + 1.7], [ly, ly], color='black', lw=0.7)
                self._notehead(ax, x, y)
                mid_y = sy + 2 * SPACING
                stem_up = y < mid_y
                sy2 = y + 3.5 * SPACING if stem_up else y - 3.5 * SPACING
                self._draw_stem(ax, x + 1.3, y, sy2)
                if n.duration <= 0.5:
                    short.append((x + 1.3, sy2, stem_up))
                else:
                    if len(short) >= 2:
                        self._beam(ax, short)
                    short = []
                if n.duration == 0.5 and len(short) == 1:
                    pass
                for _ in range(n.dots):
                    ax.plot([x + 2.0, x + 2.0], [y - 0.8, y - 0.8], 'o', ms=2.6, color='black')
            if melody and self.lyrics_on and n.lyric:
                ax.text(x, sy - 2.6, n.lyric, ha='center', va='top', fontsize=8)
            x += w
        if len(short) >= 2:
            self._beam(ax, short)
        elif len(short) == 1:
            # 단독 8분음표 → 깃발
            xf, yf, up = short[0]
            if up:
                ax.plot([xf, xf - 1.5], [yf, yf - 2.6], color='black', lw=1.1, solid_capstyle='round')
            else:
                ax.plot([xf, xf + 1.5], [yf, yf + 2.6], color='black', lw=1.1, solid_capstyle='round')

    def _draw_stem(self, ax, x, y, y2):
        ax.plot([x, x], [y, y2], color='black', lw=1.1, solid_capstyle='round')

    def _beam(self, ax, group: List[Tuple[float, float, bool]]):
        if len(group) < 2:
            return
        xs = [g[0] for g in group]
        ups = [g[2] for g in group]
        ys = [g[1] for g in group]
        if all(ups):
            y0 = min(ys)
        elif not any(ups):
            y0 = max(ys)
        else:
            y0 = sum(ys) / len(ys)
        ax.plot([xs[0], xs[-1]], [y0, y0], color='black', lw=2.4, solid_capstyle='butt')

    # ---------- 페이지/시스템 ----------
    def render(self, score: Score, parts_by_measure: list, out_path: str):
        beats, beat_type = score.time
        n_measures = len(score.measures)
        mpl = _measures_per_line(beats)
        usable_w = self.w - 2 * self.margin
        clef_zone = 13.0                      # 클레프/조표/박자 영역
        meas_w = (usable_w - clef_zone) / mpl
        sys_h = (LINE_SPAN + self.staff_gap) * len(self.parts_order)
        usable_h = self.h - self.margin - 30.0
        lines_per_page = max(1, int(usable_h // (sys_h + self.sys_gap + self.lyrics_h)))

        # 마디 → (페이지, 줄) 배치
        layout = []
        for i in range(0, n_measures, mpl):
            layout.append(list(range(i, min(i + mpl, n_measures))))
        pages: List[List[List[int]]] = []
        for i in range(0, len(layout), lines_per_page):
            pages.append(layout[i:i + lines_per_page])

        with PdfPages(out_path) as pdf:
            for pi, page_measures in enumerate(pages):
                fig = plt.figure(figsize=(self.w / 25.4, self.h / 25.4), dpi=150)
                ax = fig.add_axes([0, 0, 1, 1])
                ax.set_xlim(0, self.w)
                ax.set_ylim(0, self.h)
                ax.axis('off')

                if pi == 0:
                    ax.text(self.w / 2, self.h - 8.0, score.title, ha='center', va='center',
                            fontsize=17, fontweight='bold')
                    ax.text(self.w / 2, self.h - 12.6,
                            f"작곡: {score.composer or '전통'}   ·   AI 편곡: {score.arranger}",
                            ha='center', va='center', fontsize=8.5, color='#444')
                    ax.text(self.w / 2, self.h - 16.4,
                            f"조표: {KEY_KR.get(score.key, score.key)} ({score.key})   ·   박자: {beats}/{beat_type}   ·   템포: {score.tempo}",
                            ha='center', va='center', fontsize=8.5, color='#666')
                    top = self.h - 32.0
                else:
                    top = self.h - 20.0

                for li, line_measures in enumerate(page_measures):
                    sy_top = top - li * (sys_h + self.sys_gap + self.lyrics_h)
                    staffs = {}
                    yy = sy_top
                    for p in self.parts_order:
                        staffs[p] = yy
                        yy -= LINE_SPAN + self.staff_gap
                    # 시스템 시작: 오선+클레프+조표+박자 (+ 악보 브래킷)
                    x_start = self.margin
                    system_x0 = x_start + clef_zone
                    if len(self.parts_order) > 1:
                        ax.plot([x_start + 0.6, x_start + 0.6],
                                [staffs[self.parts_order[-1]], staffs[self.parts_order[0]] + LINE_SPAN],
                                color='black', lw=1.0)
                        ax.plot([x_start + 0.2, x_start + 1.0],
                                [staffs[self.parts_order[0]] + LINE_SPAN] * 2, color='black', lw=1.0)
                        ax.plot([x_start + 0.2, x_start + 1.0],
                                [staffs[self.parts_order[-1]]] * 2, color='black', lw=1.0)
                    for p in self.parts_order:
                        clef = INSTRUMENTS[p]['clef']
                        sy = staffs[p]
                        self._draw_staff(ax, x_start, self.margin + usable_w, sy)
                        name = INSTRUMENTS[p]['kr' if self.lang == 'kr' else 'en']
                        ax.text(x_start - 1.0, sy + LINE_SPAN / 2, name, ha='right', va='center',
                                fontsize=7.5, color='#333')
                        self._draw_clef(ax, x_start + 1.2, sy, clef)
                        kx = self._draw_keysig(ax, x_start + 6.4, sy, clef, score.key)
                        self._draw_timesig(ax, kx + 1.4, sy, beats, beat_type)
                        ax.plot([system_x0, system_x0], [sy, sy + LINE_SPAN], color='black', lw=0.8)
                    # 마디
                    for mi in line_measures:
                        mx = system_x0 + (line_measures.index(mi)) * meas_w
                        m = score.measures[mi]
                        for p in self.parts_order:
                            sy = staffs[p]
                            ax.plot([mx, mx], [sy, sy + LINE_SPAN], color='black', lw=0.8)
                        if m.chords and m.chords[0] and 'violin1' in self.parts_order:
                            ax.text(mx + meas_w / 2, staffs['violin1'] + LINE_SPAN + 2.0, str(m.chords[0]),
                                    ha='center', va='bottom', fontsize=7.5, color='#555', style='italic')
                        for p in self.parts_order:
                            clef = INSTRUMENTS[p]['clef']
                            sy = staffs[p]
                            notes = parts_by_measure[mi].get(p, [])
                            self._draw_measure_notes(ax, mx, sy, clef, notes, meas_w, beats,
                                                     melody=(p == 'violin1'),
                                                     key_acc=_key_accidentals(score.key))
                        # 마디 끝 세로줄
                        ex = mx + meas_w
                        last = (mi == n_measures - 1)
                        for p in self.parts_order:
                            sy = staffs[p]
                            if last:
                                ax.plot([ex - 0.8, ex - 0.8], [sy, sy + LINE_SPAN], color='black', lw=1.2)
                                ax.plot([ex, ex], [sy, sy + LINE_SPAN], color='black', lw=2.2)
                            else:
                                ax.plot([ex, ex], [sy, sy + LINE_SPAN], color='black', lw=0.8)
                if self.page_numbers:
                    ax.text(self.w / 2, 7.0, str(pi + 1), ha='center', va='center', fontsize=9)
                pdf.savefig(fig)
                plt.close(fig)
