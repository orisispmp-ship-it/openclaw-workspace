const http = require('http');
const { execSync } = require('child_process');
const path = require('path');

const PORT = 19789;
const CRITERIA_PATH = path.join(__dirname, '평가기준.md');

function loadCriteria() {
  try {
    return require('fs').readFileSync(CRITERIA_PATH, 'utf-8');
  } catch {
    return '평가기준 파일 없음';
  }
}

const server = http.createServer((req, res) => {
  // CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    res.writeHead(200);
    res.end();
    return;
  }

  if (req.method === 'POST' && req.url === '/evaluate') {
    let body = '';
    req.on('data', chunk => body += chunk);
    req.on('end', () => {
      try {
        const { resumeText, resumeName } = JSON.parse(body);
        if (!resumeText) {
          res.writeHead(400, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ error: 'resumeText is required' }));
          return;
        }

        const criteria = loadCriteria();
        const prompt = `다음 평가기준으로 감리원 이력서를 평가해주세요.

=== 평가기준 ===
${criteria}

=== 감리원 이력서 (${resumeName || '이력서'}) ===
${resumeText}

위 평가기준에 따라 각 항목별 점수와 총점을 산출하고, 근거를 설명해주세요.
70점 이상이 합격입니다.
애매한 부분은 질문을 남겨주세요.

출력 형식:
## 평가 결과

### ① [항목명] — X점/만점X
- 근거: ...
- 애매한 점: (있을 경우)

... (각 항목 반복)

### 🎯 총점: XX점 / 100점
### 결과: 합격/불합격`;

        console.log(`Evaluating: ${resumeName || 'unknown'}`);

        const result = execSync(
          `openclaw infer --model deepseek/deepseek-v4-flash -s`,
          {
            input: prompt,
            encoding: 'utf-8',
            timeout: 60000,
            maxBuffer: 50 * 1024 * 1024,
            shell: 'powershell.exe',
            env: { ...process.env, OPENCLAW_GATEWAY_PORT: '18789' }
          }
        );

        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ success: true, result: result.trim() }));
      } catch (err) {
        console.error('Error:', err.message);
        res.writeHead(500, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: err.message }));
      }
    });
    return;
  }

  // Health check
  res.writeHead(200, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify({ status: 'ok' }));
});

server.listen(PORT, '127.0.0.1', () => {
  console.log(`감리평가 서버 실행 중: http://127.0.0.1:${PORT}`);
});
