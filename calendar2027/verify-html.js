// 특정 날짜의 색상/클래스 DOM 검증
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
      // 12개월 .month 중 m번째, 그 안에서 textContent==d 인 .d 찾기
      const months = document.querySelectorAll('.month');
      const mon = months[m - 1];
      const cells = mon.querySelectorAll('.d');
      for (const c of cells) {
        if (parseInt(c.textContent.trim()) === d) {
          const cs = getComputedStyle(c);
          return { cls: c.className, color: cs.color };
        }
      }
      return null;
    }
    const out = {};
    // 1월 1일, 2월 6/7/8/9일, 3월 1일, 5월 13일, 5월 5일, 10월 9일
    const probes = [[1,1],[2,6],[2,7],[2,8],[2,9],[3,1],[5,5],[5,13],[6,6],[7,17],[8,15],[9,15],[10,3],[10,9],[12,25]];
    for (const [m,d] of probes) out[`${m}/${d}`] = findCell(m,d);
    return out;
  });
  console.log(JSON.stringify(res, null, 2));
  await browser.close();
})();
