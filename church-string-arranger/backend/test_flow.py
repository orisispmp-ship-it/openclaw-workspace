# -*- coding: utf-8 -*-
"""프론트엔드 요청 형식 그대로 백엔드 검증 (2단계→3단계 흐름)"""
import json, urllib.request, uuid

BASE = 'http://127.0.0.1:8000'

def post_json(path, obj):
    req = urllib.request.Request(BASE + path, data=json.dumps(obj).encode(),
                                 headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

# 프론트 score.js textToScore(DEFAULT_TEXT)와 동일한 형식
score = {
    'title': '주 은혜', 'composer': '전통 찬송', 'key': 'G', 'time': [4, 4], 'tempo': 84,
    'measures': [
        {'chords': ['G'], 'notes': [
            {'step': 'G', 'alter': 0, 'octave': 4, 'duration': 1, 'dots': 0, 'is_rest': False, 'lyric': '나'},
            {'step': 'G', 'alter': 0, 'octave': 4, 'duration': 1, 'dots': 0, 'is_rest': False, 'lyric': '같은'},
            {'step': 'A', 'alter': 0, 'octave': 4, 'duration': 1, 'dots': 0, 'is_rest': False, 'lyric': '죄인'},
            {'step': 'G', 'alter': 0, 'octave': 4, 'duration': 1, 'dots': 0, 'is_rest': False, 'lyric': '살리신'},
        ]},
        {'chords': ['G'], 'notes': [
            {'step': 'B', 'alter': 0, 'octave': 4, 'duration': 2, 'dots': 0, 'is_rest': False, 'lyric': '주'},
            {'step': 'G', 'alter': 0, 'octave': 4, 'duration': 1, 'dots': 0, 'is_rest': False, 'lyric': '은혜'},
            {'step': 'G', 'alter': 0, 'octave': 4, 'duration': 1, 'dots': 0, 'is_rest': False, 'lyric': '놀라워'},
        ]},
        {'chords': [], 'notes': [
            {'step': 'D', 'alter': 0, 'octave': 4, 'duration': 4, 'dots': 0, 'is_rest': False, 'lyric': '아멘'},
        ]},
    ],
}
req = {'score': score, 'arrangement': 'duo', 'transpose_to': None, 'tempo': None,
       'lyrics_on': True, 'page_size': 'A4', 'lang': 'kr', 'page_numbers': True}
r = post_json('/api/arrange', req)
print('✅ arrange 응답:', r['title'], '|', r['arrangement_label'], '| pdf:', r['pdf'])
print('   parts:', r['parts'], '| measures:', r['measures'])

# PDF 다운로드 가능 확인
with urllib.request.urlopen(BASE + r['pdf']) as res:
    pdf = res.read()
print('✅ PDF 다운로드:', len(pdf), 'bytes')

# 4중주 + 조옮김도 확인
req2 = dict(req, arrangement='quartet', transpose_to='D', tempo=96)
r2 = post_json('/api/arrange', req2)
print('✅ 4중주(D조):', r2['key'], '|', r2['pdf'])

print('\nFLOW OK — 2단계 → 3단계 전환에 필요한 API 정상 동작 ✅')
