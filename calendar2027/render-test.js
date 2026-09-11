// test3.pdf 렌더링 검증
const { getDocument } = require('pdfjs-dist/legacy/build/pdf.mjs');
const { createCanvas } = require('canvas');
const fs = require('fs');

(async () => {
  const data = new Uint8Array(fs.readFileSync('test3.pdf'));
  const pdf = await getDocument({ data }).promise;
  const page = await pdf.getPage(1);
  const viewport = page.getViewport({ scale: 2 });
  const canvas = createCanvas(viewport.width, viewport.height);
  const ctx = canvas.getContext('2d');
  ctx.fillStyle = '#ffffff';
  ctx.fillRect(0, 0, viewport.width, viewport.height);
  await page.render({ canvasContext: ctx, viewport }).promise;
  const buf = canvas.toBuffer('image/png');
  fs.writeFileSync('test3-render.png', buf);
  console.log('saved', buf.length);
})();
