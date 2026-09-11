# -*- coding: utf-8 -*-
"""증명사진 → 수채화 풍 변환 v2 (OpenCV stylization + 색 양자화 + 종이 질감)"""
import cv2
import numpy as np

SRC = r"C:\Users\orisi\.openclaw\media\inbound\KakaoTalk_20260809_182717307---da3d3852-0a32-4e4d-a584-354034779669.jpg"
OUT_DIR = r"C:\Users\orisi\.openclaw\workspace\watercolor"

img = cv2.imread(SRC)
img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
h, w = img.shape[:2]
print("size:", img.shape)

rng = np.random.default_rng(7)

def posterize(img, levels):
    """채널별 색상 단계 축소 → 수채화 색 덩어리"""
    step = 255 // levels
    lut = np.clip((np.arange(256) // step) * step + step // 2, 0, 255).astype(np.uint8)
    return lut[img]

def paper_texture(h, w, rng):
    """섬유 느낌 종이 질감 (크림 톤 + 방향성 노이즈)"""
    base = np.full((h, w, 3), (251, 247, 238), dtype=np.float32)
    # 방향성 섬유: x 방향으로 부드러운 랜덤 줄무늬
    fiber = rng.normal(0, 1, (h, w // 8)).astype(np.float32)
    fiber = cv2.resize(fiber, (w, h), interpolation=cv2.INTER_CUBIC)
    fiber = cv2.GaussianBlur(fiber, (0, 0), 1.2)
    noise = rng.normal(0, 1, (h, w)).astype(np.float32)
    tex = base + fiber[..., None] * 3.5 + noise[..., None] * 2.5
    return np.clip(tex, 0, 255)

def watercolor_variant(sigma_s, sigma_r, levels, bleed_ratio, out_name):
    # 1) 스타일화: 표면 부드럽게 + 엣지 보존 (수채화의 핵심)
    styl = cv2.stylization(img, sigma_s=sigma_s, sigma_r=sigma_r)
    styl = cv2.cvtColor(styl, cv2.COLOR_BGR2RGB)

    # 2) 색 양자화 → 물감 덩어리
    quant = posterize(styl, levels)

    # 3) 번짐: 큰 블러를 소량 섞기
    small = cv2.resize(img, (w // 4, h // 4), interpolation=cv2.INTER_AREA)
    bleed = cv2.GaussianBlur(small, (0, 0), 5)
    bleed = cv2.resize(bleed, (w, h), interpolation=cv2.INTER_CUBIC)
    blended = cv2.addWeighted(quant, 1 - bleed_ratio, bleed, bleed_ratio, 0)

    # 4) 배경(흰색·저채도) → 종이 톤
    hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
    sat = hsv[:, :, 1].astype(np.float32)
    bright = hsv[:, :, 2].astype(np.float32)
    bg = ((sat < 40) & (bright > 215)).astype(np.float32)
    bgm = cv2.GaussianBlur(bg, (0, 0), 11)[..., None]
    paper = paper_texture(h, w, rng)
    out = blended * (1 - bgm) + paper * bgm

    # 5) 미세 종이 질감을 그림 전체에 아주 약하게
    out = out + rng.normal(0, 1.8, out.shape)
    out = np.clip(out, 0, 255).astype(np.uint8)
    out_bgr = cv2.cvtColor(out, cv2.COLOR_RGB2BGR)
    ok, buf = cv2.imencode(".png", out_bgr)
    if ok:
        with open(f"{OUT_DIR}\\{out_name}", "wb") as f:
            f.write(buf.tobytes())
        print("saved:", out_name)
    else:
        print("FAILED:", out_name)

# 변형 3종 비교
watercolor_variant(70, 0.55, 7, 0.18, "지우-수채화-v2a.png")
watercolor_variant(90, 0.65, 6, 0.25, "지우-수채화-v2b.png")
watercolor_variant(50, 0.45, 8, 0.12, "지우-수채화-v2c.png")
print("done")
