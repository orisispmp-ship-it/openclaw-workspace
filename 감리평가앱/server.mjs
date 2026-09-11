import http from 'http';
import https from 'https';
import { readFileSync } from 'fs';

const PORT = 19789;
const DEEPSEEK_KEY = process.env.DEEPSEEK_API_KEY || readFileSync(new URL('./deepseek.key.local', import.meta.url), 'utf-8').trim();
const CRITERIA = readFileSync(
  'C:\\Users\\orisi\\.openclaw\\workspace\\감리평가앱\\평가기준.md',
  'utf-8'
);

function callDeepSeek(prompt) {
  return new Promise((resolve, reject) => {
    var body = JSON.stringify({
      model: 'deepseek-chat',
      messages: [{role: 'user', content: prompt}],
      max_tokens: 3000,
      temperature: 0.15
    });
    var req = https.request({
      hostname: 'api.deepseek.com',
      path: '/v1/chat/completions',
      method: 'POST',
      headers: {
        'Authorization': 'Bearer ' + DEEPSEEK_KEY,
        'Content-Type': 'application/json'
      }
    }, (res) => {
      var data = '';
      res.on('data', c => data += c);
      res.on('end', () => {
        try {
          var j = JSON.parse(data);
          if (j.choices && j.choices[0] && j.choices[0].message) {
            resolve(j.choices[0].message.content);
          } else if (j.error) {
            reject(j.error.message || JSON.stringify(j.error));
          } else {
            reject('Unexpected response format');
          }
        } catch(e) {
          reject('JSON parse error: ' + data.slice(0, 300));
        }
      });
    });
    req.on('error', e => reject(e.message));
    req.write(body);
    req.end();
  });
}

function parseJSON(text) {
  var m = text.match(/```(?:json)?\s*\n?([\s\S]*?)```/);
  if (m) text = m[1];
  return JSON.parse(text);
}

const server = http.createServer((req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS, GET');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  if (req.method === 'OPTIONS') { res.writeHead(200); res.end(); return; }

  if (req.method === 'POST' && req.url === '/analyze') {
    var body = '';
    req.on('data', c => body += c);
    req.on('end', async () => {
      try {
        var data = JSON.parse(body);
        var resumeText = data.resumeText || '';
        var resumeName = data.resumeName || '이력서';

        var prompt = `당신은 감리원 평가 전문가입니다. 평가기준에 따라 이력서를 분석하고 결과를 정해진 JSON 형식으로만 출력하세요.

[평가기준]
${CRITERIA}

[이력서: ${resumeName}]
${resumeText}

출력은 아래 JSON 구조 그대로, 다른 텍스트나 설명 없이 순수 JSON만 출력하세요.

{
  "items": [
    {
      "id": 1,
      "name": "반도체/플랜트 경력",
      "maxScore": 25,
      "currentScore": <추천점수>,
      "reason": "이력서에서 찾은 구체적 경력기간을 바탕으로 점수 산출 사유",
      "evidence": "이력서에서 발췌한 관련 문장(150자 이내)",
      "selectedOption": "<아래 options 중 선택된 id>",
      "ambiguous": <true/false — 경력기간 애매, 전공 관련성 모호 등 판단이 어려우면 true>,
      "options": [
        {"id":"opt_5y_plus","label":"5년 이상","score":25},
        {"id":"opt_3y_5y","label":"3년 이상 ~ 5년 미만","score":20},
        {"id":"opt_1y_3y","label":"1년 이상 ~ 3년 미만","score":15},
        {"id":"opt_under_1y","label":"1년 미만","score":10}
      ]
    },
    {
      "id": 2,
      "name": "설계/감리 경력",
      "maxScore": 25,
      "currentScore": <추천점수>,
      "reason": "점수 산출 사유",
      "evidence": "이력서 발췌문",
      "selectedOption": "<options 중 선택된 id>",
      "ambiguous": <true/false>,
      "options": [
        {"id":"opt_10y_plus","label":"10년 이상","score":25},
        {"id":"opt_5y_10y","label":"5년 이상 ~ 10년 미만","score":20},
        {"id":"opt_3y_5y","label":"3년 이상 ~ 5년 미만","score":15},
        {"id":"opt_under_3y","label":"3년 미만","score":10}
      ]
    },
    {
      "id": 3,
      "name": "학력",
      "maxScore": 25,
      "currentScore": <점수>,
      "reason": "점수 산출 사유",
      "evidence": "이력서 발췌문",
      "selectedOption": "<options 중 선택된 id>",
      "ambiguous": <true/false — 전공 관련성 모호하면 true>,
      "options": [
        {"id":"opt_master","label":"석사(관련전공)","score":25},
        {"id":"opt_bachelor","label":"학사(관련학과)","score":20},
        {"id":"opt_associate","label":"전문학사(관련학과)","score":15},
        {"id":"opt_high","label":"고졸(관련학과)","score":10}
      ]
    },
    {
      "id": 4,
      "name": "자격",
      "maxScore": 25,
      "currentScore": <점수>,
      "reason": "점수 산출 사유",
      "evidence": "이력서 발췌문",
      "selectedOption": "<options 중 선택된 id>",
      "ambiguous": <true/false>,
      "options": [
        {"id":"opt_tech","label":"기술사","score":25},
        {"id":"opt_multi","label":"기사/산업기사/기능장/해외자격 2개 이상","score":20},
        {"id":"opt_single","label":"기사/산업기사/기능장/해외자격 1개","score":15}
      ]
    },
    {
      "id": 5,
      "name": "가점",
      "maxScore": 15,
      "currentScore": <합산점수>,
      "reason": "각 항목별 적용 사유",
      "evidence": "관련 이력서 문구",
      "selectedOption": null,
      "ambiguous": <true/false>,
      "subOptions": [
        {"id":"award","label":"국가공인 시상 (+5)","score":5,"applied":<true/false>,"reason":"적용/미적용 사유"},
        {"id":"patent","label":"특허 (+5)","score":5,"applied":<true/false>,"reason":"적용/미적용 사유"},
        {"id":"phd","label":"박사(관련전공) (+5)","score":5,"applied":<true/false>,"reason":"적용/미적용 사유"}
      ]
    }
  ],
  "total": <모든 항목 합계>,
  "pass": <70점 이상 true, 미만 false>,
  "ambiguousItems": [<ambiguous가 true인 항목의 id>]
}`;

        console.log('분석 시작:', resumeName);
        var result = await callDeepSeek(prompt);
        console.log('AI 응답:', result.slice(0, 200));

        var analysis;
        try {
          analysis = parseJSON(result);
        } catch(e) {
          console.error('JSON 파싱 오류');
          res.writeHead(500, {'Content-Type': 'application/json; charset=utf-8'});
          res.end(JSON.stringify({error: 'AI 응답 파싱 오류', raw: result.slice(0, 500)}));
          return;
        }

        res.writeHead(200, {'Content-Type': 'application/json; charset=utf-8'});
        res.end(JSON.stringify({success: true, analysis: analysis}));
        console.log('분석 완료');
      } catch(e) {
        console.error('Error:', e.message);
        res.writeHead(500, {'Content-Type': 'application/json; charset=utf-8'});
        res.end(JSON.stringify({error: e.message}));
      }
    });
    return;
  }

  res.writeHead(200);
  res.end('OK');
});

server.listen(PORT, '127.0.0.1', () => console.log('감리평가 서버: http://127.0.0.1:' + PORT));
