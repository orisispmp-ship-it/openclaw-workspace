const https = require('https');
const fs = require('fs');

const url = 'https://calendar.google.com/calendar/ical/orisispmp%40gmail.com/private-0488d5ea3968df94a5b5cb5f6a8a4af9/basic.ics';

https.get(url, (res) => {
  let data = '';
  res.on('data', chunk => data += chunk);
  res.on('end', () => {
    // Save raw
    fs.writeFileSync('C:/Users/orisi/.openclaw/workspace/calendar_raw.txt', data, 'utf8');
    
    const events = data.match(/BEGIN:VEVENT[\s\S]*?END:VEVENT/g) || [];
    const now = new Date('2026-07-13T23:59:59+09:00');
    const upcoming = [];

    for (const e of events) {
      const s = e.match(/SUMMARY:(.+)/);
      if (!s) continue;
      const d1 = e.match(/DTSTART;VALUE=DATE:(\d{4})(\d{2})(\d{2})/);
      const d2 = e.match(/DTSTART:(\d{4})(\d{2})(\d{2})/);
      const match = d1 || d2;
      if (!match) continue;
      const dt = new Date(parseInt(match[1]), parseInt(match[2])-1, parseInt(match[3]));
      if (dt >= now) {
        upcoming.push({
          date: dt.toLocaleDateString('ko-KR', { timeZone: 'Asia/Seoul', year: 'numeric', month: '2-digit', day: '2-digit', weekday: 'short' }),
          summary: s[1].trim()
        });
      }
    }

    upcoming.sort((a, b) => a.date.localeCompare(b.date));
    
    let out = '=== 2026년 7월 13일 이후 다가오는 일정 ===\n\n';
    if (upcoming.length === 0) {
      out += '등록된 일정이 없습니다.\n';
    } else {
      for (const u of upcoming) {
        out += `${u.date}  ${u.summary}\n`;
      }
      out += `\n총 ${upcoming.length}개 일정\n`;
    }
    
    fs.writeFileSync('C:/Users/orisi/.openclaw/workspace/calendar_result.txt', out, 'utf8');
    console.log(out);
  });
}).on('error', err => {
  const msg = 'Error: ' + err.message;
  fs.writeFileSync('C:/Users/orisi/.openclaw/workspace/calendar_result.txt', msg, 'utf8');
  console.error(msg);
});
