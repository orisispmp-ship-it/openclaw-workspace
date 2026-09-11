// Chrome(puppeteer-core)으로 HTML -> PDF 변환
const puppeteer = require('puppeteer-core');

(async () => {
  const browser = await puppeteer.launch({
    executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe',
    headless: 'new',
    args: ['--no-sandbox', '--disable-gpu', '--font-render-hinting=none'],
  });
  const page = await browser.newPage();
  await page.goto('file:///C:/Users/orisi/.openclaw/workspace/calendar2027/calendar-2027.html', { waitUntil: 'networkidle0' });
  await page.pdf({
    path: 'C:/Users/orisi/.openclaw/workspace/calendar2027/calendar-2027.pdf',
    format: 'A4',
    landscape: true,
    printBackground: true,
    preferCSSPageSize: true,
    margin: { top: 0, bottom: 0, left: 0, right: 0 },
  });
  await browser.close();
  console.log('PDF created');
})();
