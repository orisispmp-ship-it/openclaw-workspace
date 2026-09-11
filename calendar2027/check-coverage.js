// checkcoverage.apple.com 시리얼 조회 (puppeteer)
const puppeteer = require('puppeteer-core');

(async () => {
  const browser = await puppeteer.launch({
    executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe',
    headless: 'new',
    args: ['--no-sandbox', '--disable-gpu'],
  });
  const page = await browser.newPage();
  await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36');
  await page.goto('https://checkcoverage.apple.com/?locale=ko_KR', { waitUntil: 'networkidle2', timeout: 45000 });
  await new Promise(r => setTimeout(r, 2000));

  // 입력 필드 찾기
  const inputInfo = await page.evaluate(() => {
    const inputs = Array.from(document.querySelectorAll('input'));
    return inputs.map(i => ({ id: i.id, name: i.name, type: i.type, ph: i.placeholder }));
  });
  console.log('INPUTS:', JSON.stringify(inputInfo));

  // 시리얼 입력
  const typed = await page.evaluate((sn) => {
    const inp = document.querySelector('input[type="text"], input[name="sn"], input#sn, input[autocomplete="off"]');
    if (!inp) return false;
    const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
    setter.call(inp, sn);
    inp.dispatchEvent(new Event('input', { bubbles: true }));
    inp.dispatchEvent(new Event('change', { bubbles: true }));
    return true;
  }, 'CM9CQJ72R6');
  console.log('TYPED:', typed);
  await new Promise(r => setTimeout(r, 1000));

  // 제출 버튼 클릭
  const clicked = await page.evaluate(() => {
    const btn = document.querySelector('button[type="submit"], form button, .button, input[type="submit"]');
    if (!btn) return false;
    btn.click();
    return true;
  });
  console.log('CLICKED:', clicked);
  await new Promise(r => setTimeout(r, 6000));

  // 결과 텍스트 추출
  const text = await page.evaluate(() => document.body.innerText);
  console.log('=== PAGE TEXT ===');
  console.log(text.slice(0, 3000));

  await browser.close();
})();
