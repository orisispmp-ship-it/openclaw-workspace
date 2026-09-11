// PDF 첫 4페이지를 PNG로 변환 (미리보기용)
const { getDocument } = require('pdfjs-dist/legacy/build/pdf.mjs');
const { createCanvas } = require('canvas');
const fs = require('fs');

(async () => {
  const data = new Uint8Array(fs.readFileSync('C:/Users/orisi/.openclaw/workspace/calendar2027/2027-달력.pdf'));
  const pdf = await getDocument({ data }).promise;
  const scale = 1.4;
  const pagesToRender = [1, 2, 5, 9]; // 1월, 2월, 5월, 9월 미리보기
  for (const p of pagesToRender) {
    const page = await pdf.getPage(p);
    const viewport = page.getViewport({ scale });
    const canvas = createCanvas(viewport.width, viewport.height);
    const ctx = canvas.getContext('2d');
    await page.render({ canvasContext: ctx, viewport }).promise;
    fs.writeFileSync(`C:/Users/orisi/.openclaw/workspace/calendar2027/preview-p${p}.png`, canvas.toBuffer('image/png'));
    console.log('saved preview-p' + p + '.png');
  }
  console.log('TOTAL_PAGES:', pdf.numPages);
})();
