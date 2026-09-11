import cv2
import numpy as np

img = cv2.imread(r'C:\Users\orisi\.openclaw\media\inbound\IMG_2219---5e65bc66-5572-474c-974f-0500daccfc9a.jpg')
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
faces = face_cascade.detectMultiScale(gray, 1.1, 4)
x, y, w, h = faces[0]

face_roi = gray[y:y+h, x:x+w]

print('=== 얼굴 분석 결과 ===')
print(f'얼굴형 비율(가로/세로): {w/h:.2f}')

if w/h > 1.05:
    shape = '각진형'
elif w/h > 0.92:
    shape = '계란형 또는 각진형'
elif w/h > 0.8:
    shape = '계란형'
else:
    shape = '긴형'
print(f'얼굴형 분류: {shape}')

# Region brightness analysis
forehead = gray[y:y+int(h*0.28), x:x+w]
eye_region = gray[y+int(h*0.3):y+int(h*0.52), x:x+w]
nose_region = gray[y+int(h*0.45):y+int(h*0.65), x:x+w]
mouth_region = gray[y+int(h*0.62):y+int(h*0.78), x:x+w]
chin_region = gray[y+int(h*0.75):y+h, x:x+w]

print(f'이마 밝기: {np.mean(forehead):.0f}')
print(f'눈 영역 밝기: {np.mean(eye_region):.0f}')
print(f'코 영역 밝기: {np.mean(nose_region):.0f}')
print(f'입 영역 밝기: {np.mean(mouth_region):.0f}')
print(f'턱 영역 밝기: {np.mean(chin_region):.0f}')

# Contrast within face areas (higher = more defined features)
forehead_std = np.std(forehead)
eye_std = np.std(eye_region)
nose_std = np.std(nose_region)
mouth_std = np.std(mouth_region)

print(f'이마 대비: {forehead_std:.1f}')
print(f'눈 대비: {eye_std:.1f}')
print(f'코 대비: {nose_std:.1f}')
print(f'입 대비: {mouth_std:.1f}')

# Color analysis
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
face_hsv = hsv[y:y+h, x:x+w]
avg_sat = np.mean(face_hsv[:,:,1])
avg_val = np.mean(face_hsv[:,:,2])
print(f'피부 채도: {avg_sat:.0f}')
print(f'피부 명도: {avg_val:.0f}')

# Wrinkle/line detection
edges = cv2.Canny(face_roi, 50, 150)
edge_density = np.sum(edges > 0) / (h * w)
print(f'주름/라인 밀도: {edge_density:.4f}')

# Eye detection and analysis
eyes_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
eyes = eyes_cascade.detectMultiScale(face_roi, 1.05, 3)
if len(eyes) >= 2:
    sorted_eyes = sorted(eyes, key=lambda e: e[0])
    le, re = sorted_eyes[0], sorted_eyes[1]
    eye_dist = re[0] - (le[0] + le[2])
    eye_size = (le[2] + re[2]) / 2
    print(f'눈 사이 간격: {eye_dist}px')
    print(f'평균 눈 크기: {eye_size:.0f}px')
    print(f'눈 너비/얼굴비: {eye_size/w:.3f}')
