// calendar-2027.pdf 렌더링 확인
const { getDocument } = require('pdfjs-dist/legacy/build/pdf.mjs');
const { createCanvas } = require('canvas');
const fs = require('fs');

(async () => {
  const data = new Uint8Array(fs.readFileSync('calendar-2027.pdf'));
  const pdf = await getDocument({ data }).promise;
  console.log('pages:', pdf.numPages);
  const page = await pdf.getPage(1);
  const viewport = page.getViewport({ scale: 1.6 });
  const canvas = createCanvas(viewport.width, viewport.height);
  const ctx = canvas.getContext('2d');
  ctx.fillStyle = '#ffffff';
  ctx.fillRect(0, 0, viewport.width, viewport.height);
  await page.render({ canvasContext: ctx, viewport }).promise;
  fs.writeFileSync('cal-render.png', canvas.toBuffer('image/png'));
  console.log('saved cal-render.png', canvas.toBuffer('image/png').length);
})();
