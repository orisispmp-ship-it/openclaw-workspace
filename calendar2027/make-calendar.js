// 2027년 달력 PDF 생성 (A4 가로, 12페이지)
const PDFDocument = require('pdfkit');
const fs = require('fs');

// ---------- 공휴일/국경일 데이터 (2027) ----------
const holidays = {
  '2027-01-01': '신정',
  '2027-02-06': '설 연휴',
  '2027-02-07': '설날',
  '2027-02-08': '설 연휴',
  '2027-02-09': '대체공휴일',
  '2027-03-01': '삼일절',
  '2027-05-01': '노동절',
  '2027-05-03': '대체공휴일',
  '2027-05-05': '어린이날',
  '2027-05-13': '부처님오신날',
  '2027-06-06': '현충일',
  '2027-07-17': '제헌절',
  '2027-07-19': '대체공휴일',
  '2027-08-15': '광복절',
  '2027-08-16': '대체공휴일',
  '2027-09-14': '추석 연휴',
  '2027-09-15': '추석',
  '2027-09-16': '추석 연휴',
  '2027-10-03': '개천절',
  '2027-10-04': '대체공휴일',
  '2027-10-09': '한글날',
  '2027-10-11': '대체공휴일',
  '2027-12-25': '성탄절',
  '2027-12-27': '대체공휴일',
};

const RED = '#d32f2f';
const BLUE = '#1976d2';
const BLACK = '#222222';
const GRAY = '#999999';

// ---------- 레이아웃 (A4 가로) ----------
const W = 841.89, H = 595.28; // pt
const MARGIN = 36;
const gridX = MARGIN, gridW = W - MARGIN * 2;
const colW = gridW / 7;
const titleH = 78;
const headerH = 30;
const gridY0 = MARGIN + titleH + headerH;
const gridH = H - MARGIN - gridY0;
const rowH = gridH / 6;

const daysKo = ['일', '월', '화', '수', '목', '금', '토'];

function iso(y, m, d) { return `${y}-${String(m).padStart(2, '0')}-${String(d).padStart(2, '0')}`; }

const doc = new PDFDocument({ size: 'A4', layout: 'landscape', margin: MARGIN });
doc.registerFont('malgun', 'C:/Windows/Fonts/malgun.ttf');
doc.registerFont('malgun-bold', 'C:/Windows/Fonts/malgunbd.ttf');

const out = 'C:/Users/orisi/.openclaw/workspace/calendar2027/2027-달력.pdf';
doc.pipe(fs.createWriteStream(out));

// ---------- 페이지(월)별 렌더링 ----------
for (let m = 1; m <= 12; m++) {
  if (m > 1) doc.addPage();

  // 타이틀
  doc.font('malgun-bold').fontSize(30).fillColor(BLACK);
  doc.text(`2027년 ${m}월`, MARGIN, MARGIN, { width: gridW, align: 'center' });

  // 공휴일 요약 (타이틀 아래 작게)
  const hCount = Object.keys(holidays).filter(k => k.startsWith(`2027-${String(m).padStart(2, '0')}`)).length;
  doc.font('malgun').fontSize(10).fillColor(GRAY);
  doc.text(hCount > 0 ? `이달의 공휴일 ${hCount}일` : '공휴일 없음', MARGIN, MARGIN + 36, { width: gridW, align: 'center' });

  // 요일 헤더
  const hY = MARGIN + titleH;
  for (let d = 0; d < 7; d++) {
    const x = gridX + d * colW;
    const color = d === 0 ? RED : d === 6 ? BLUE : BLACK;
    doc.font('malgun-bold').fontSize(14).fillColor(color);
    doc.text(daysKo[d], x, hY, { width: colW, align: 'center', lineBreak: false });
  }
  // 헤더 밑줄
  doc.moveTo(gridX, hY + 22).lineTo(gridX + gridW, hY + 22).lineWidth(1).strokeColor(BLACK).stroke();

  // 날짜 그리드
  const firstDay = new Date(2027, m - 1, 1).getDay(); // 0=일
  const daysInMonth = new Date(2027, m, 0).getDate();

  for (let day = 1; day <= daysInMonth; day++) {
    const date = new Date(2027, m - 1, day);
    const dow = date.getDay();
    const week = Math.floor((firstDay + day - 1) / 7);
    const col = (firstDay + day - 1) % 7;

    const x = gridX + col * colW;
    const y = gridY0 + week * rowH;

    const key = iso(2027, m, day);
    const isHoliday = holidays[key] !== undefined;

    // 셀 배경 (공휴일 연휴는 연분홍)
    if (isHoliday) {
      doc.rect(x + 1, y + 1, colW - 2, rowH - 2).fill('#fdecea');
    } else if (dow === 0) {
      doc.rect(x + 1, y + 1, colW - 2, rowH - 2).fill('#fafafa');
    }

    // 날짜 숫자
    const numColor = isHoliday ? RED : dow === 0 ? RED : dow === 6 ? BLUE : BLACK;
    doc.font('malgun-bold').fontSize(15).fillColor(numColor);
    doc.text(String(day), x + 6, y + 4, { width: colW - 12, lineBreak: false });

    // 공휴일 이름 (숫자 오른쪽/아래)
    if (isHoliday) {
      doc.font('malgun').fontSize(9).fillColor(RED);
      doc.text(holidays[key], x + 6, y + 24, { width: colW - 12, lineBreak: false });
    }

    // 셀 테두리
    doc.rect(x, y, colW, rowH).lineWidth(0.5).strokeColor('#cccccc').stroke();
  }
}

doc.end();
console.log('DONE:', out);
