// Gemini 직접 호출로 수채화 변환 시도
const fs = require('fs');

(async () => {
  const apiKey = process.env.GEMINI_API_KEY;
  if (!apiKey) { console.log('NO GEMINI_API_KEY'); return; }

  const img = fs.readFileSync('C:/Users/orisi/.openclaw/media/inbound/KakaoTalk_20260809_182717307---fb89cb66-21bc-41f1-8d8d-99e16e49b59e.jpg');
  const b64 = img.toString('base64');

  const endpoint = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-image-preview:generateContent';
  const body = {
    contents: [{
      parts: [
        { inline_data: { mime_type: 'image/jpeg', data: b64 } },
        { text: "이 사진 속 한국 중년 남성(회색 머리, 파란 폴로 셔츠 + 회색 블레이저)을 멋진 수채화 초상화 스타일로 변환해주세요. 얼굴 표정과 특징을 유지하고, 배경은 부드러운 수채화 물감 번짐으로. 우아하고 세련된 분위기. 카카오톡 프로필용 정사각형." }
      ]
    }]
  };

  try {
    const res = await fetch(`${endpoint}?key=${apiKey}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    const txt = await res.text();
    console.log('STATUS:', res.status);
    if (!res.ok) { console.log('ERR:', txt.slice(0, 500)); return; }
    const json = JSON.parse(txt);
    // 응답에서 이미지 base64 추출
    const c = json.candidates?.[0]?.content?.parts;
    let saved = false;
    if (c) {
      for (const p of c) {
        if (p.inline_data?.data) {
          fs.writeFileSync('C:/Users/orisi/.openclaw/workspace/calendar2027/../jihu-watercolor-profile.png', Buffer.from(p.inline_data.data, 'base64'));
          console.log('SAVED png');
          saved = true;
          break;
        }
      }
    }
    if (!saved) console.log('no image in response. keys:', Object.keys(json));
  } catch (e) {
    console.log('FETCH ERR:', e.message);
  }
})();
