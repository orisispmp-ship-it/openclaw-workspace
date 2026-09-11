// 일요일/공휴일/토요일 색상 DOM 검증
const puppeteer = require('puppeteer-core');

(async () => {
  const browser = await puppeteer.launch({
    executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe',
    headless: 'new',
    args: ['--no-sandbox', '--disable-gpu'],
  });
  const page = await browser.newPage();
  await page.goto('file:///C:/Users/orisi/.openclaw/workspace/calendar2027/calendar-2027.html', { waitUntil: 'networkidle0' });
  const res = await page.evaluate(() => {
    function findCell(m, d) {
      const mon = document.querySelectorAll('.month')[m - 1];
      const cells = mon.querySelectorAll('.d');
      for (const c of cells) {
        if (parseInt(c.textContent.trim()) === d) {
          return { cls: c.className, color: getComputedStyle(c).color, weight: getComputedStyle(c).fontWeight };
        }
      }
      return null;
    }
    const probes = [[1,1],[1,3],[1,2],[1,7],[1,8],[2,7],[2,6],[6,6],[8,15],[10,9]];
    const out = {};
    for (const [m,d] of probes) out[`${m}/${d}`] = findCell(m,d);
    // 요일 헤더 '일' 색 확인
    const dw = document.querySelectorAll('.month')[0].querySelector('.dow-r');
    out['dow-SUN'] = dw ? getComputedStyle(dw).color : null;
    return out;
  });
  console.log(JSON.stringify(res, null, 2));
  await browser.close();
})();
