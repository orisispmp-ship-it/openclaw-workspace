// 달력 HTML을 PNG로 스크린샷 (시각 확인용)
const puppeteer = require('puppeteer-core');

(async () => {
  const browser = await puppeteer.launch({
    executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe',
    headless: 'new',
    args: ['--no-sandbox', '--disable-gpu', '--font-render-hinting=none'],
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 1200, height: 840, deviceScaleFactor: 2 });
  await page.goto('file:///C:/Users/orisi/.openclaw/workspace/calendar2027/calendar-2027.html', { waitUntil: 'networkidle0' });
  await page.screenshot({ path: 'C:/Users/orisi/.openclaw/workspace/calendar2027/calendar-preview.png', clip: { x: 0, y: 0, width: 1148, height: 800 } });
  await browser.close();
  console.log('screenshot saved');
})();
