"""감리원 평가 서버"""
import http.server, json, subprocess, sys, os, urllib.parse

PORT = 19789
WORKSPACE = os.path.dirname(os.path.abspath(__file__))
CRITERIA = open(os.path.join(WORKSPACE, '평가기준.md'), 'r', encoding='utf-8').read()

def evaluate(prompt):
    ps_code = f'@\"\n{prompt}\n\"@ | openclaw infer deepseek/deepseek-v4-flash -s'
    p = subprocess.run(
        ['powershell', '-NoProfile', '-Command', ps_code],
        capture_output=True, text=True, timeout=120,
        env={**os.environ}
    )
    if p.returncode != 0:
        raise Exception(f"infer 실패: {p.stderr[:300]}")
    return p.stdout.strip()

class Handler(http.server.BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        if self.path == '/evaluate':
            try:
                length = int(self.headers['Content-Length'])
                body = json.loads(self.rfile.read(length))
                rt = body.get('resumeText', '')
                rn = body.get('resumeName', '이력서')
                prompt = f"""다음 평가기준으로 감리원 이력서를 평가해주세요.

=== 평가기준 ===
{CRITERIA}

=== 감리원 이력서 ({rn}) ===
{rt}

각 항목별 점수와 총점을 산출하고 근거를 설명해주세요.
70점 이상 합격. 애매하면 질문을 남겨주세요.

출력 형식:
### ① 항목명 — X점/25
### ② 항목명 — X점/25
### ③ 항목명 — X점/25
### ④ 항목명 — X점/25
### ⑤ 가점 — X점
### 🎯 총점: XX/100
### 결과: 합격/불합격"""
                result = evaluate(prompt)
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'success': True, 'result': result}).encode())
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode())
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == '__main__':
    s = http.server.HTTPServer(('127.0.0.1', PORT), Handler)
    print(f'감리평가 서버: http://127.0.0.1:{PORT}')
    s.serve_forever()
