# -*- coding: utf-8 -*-
"""증명사진 → 수채화 풍 변환 (로컬 PIL 필터)"""
from PIL import Image, ImageFilter, ImageEnhance
import numpy as np

SRC = r"C:\Users\orisi\.openclaw\media\inbound\KakaoTalk_20260809_182717307---da3d3852-0a32-4e4d-a584-354034779669.jpg"
OUT = r"C:\Users\orisi\.openclaw\workspace\watercolor\지우-수채화.png"

img = Image.open(SRC).convert("RGB")
w, h = img.size
print("size:", img.size)

rng = np.random.default_rng(42)

# 1) 번짐(bleeding) 레이어: 축소 → 큰 블러 → 확대
small = img.resize((max(64, w // 4), max(64, h // 4)), Image.LANCZOS)
bleed = small.filter(ImageFilter.GaussianBlur(radius=5))
bleed = bleed.resize((w, h), Image.LANCZOS)

# 2) 디테일 레이어: median 스무딩 (수채화 특유의 색 덩어리)
detail = img.filter(ImageFilter.MedianFilter(size=5))

# 3) 합성: 디테일 위에 번짐을 살짝
base = Image.blend(detail, bleed, 0.32)

# 4) 채도/밝기/대비 보정
base = ImageEnhance.Color(base).enhance(1.18)
base = ImageEnhance.Brightness(base).enhance(1.04)
base = ImageEnhance.Contrast(base).enhance(1.02)

# 5) 미묘한 경계선(엣지) 강조 — 수채화는 색 덩어리 경계에 선이 남음
arr = np.asarray(base).astype(np.float32)
gray = arr.mean(axis=2)
gy, gx = np.gradient(gray)
mag = np.sqrt(gx ** 2 + gy ** 2)
mag = mag / (mag.max() + 1e-6)
edge = np.clip(1 - 0.30 * mag, 0.55, 1.0)[..., None]
arr2 = arr * edge
painted = Image.fromarray(np.clip(arr2, 0, 255).astype(np.uint8))

# 6) 배경 → 종이 톤 (크림색 + 질감), 인물은 유지
orig = np.asarray(img).astype(np.float32)
sat = orig.max(axis=2) - orig.min(axis=2)
bright = orig.mean(axis=2)
bg = (sat < 35) & (bright > 225)
bgm = bg.astype(np.float32)
bgm = np.asarray(Image.fromarray((bgm * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(radius=9))) / 255.0
bgm = bgm[..., None]

paper = np.full((h, w, 3), (251, 247, 238), dtype=np.float32)
noise = rng.normal(0, 5, (h, w, 1))
paper = np.clip(paper + noise, 0, 255)

arr3 = np.asarray(painted).astype(np.float32)
final = arr3 * (1 - bgm) + paper * bgm

# 7) 전체에 종이 질감을 아주 약하게 (그림 전체가 종이 위 느낌)
final = final + rng.normal(0, 2.2, final.shape)
final = np.clip(final, 0, 255).astype(np.uint8)
out = Image.fromarray(final)

out.save(OUT)
print("saved:", OUT)
