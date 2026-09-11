$r = ntn pages create < "C:\Users\orisi\.openclaw\workspace\kospi_notion.md" 2>&1
if ($LASTEXITCODE -eq 0) { "OK" | Out-File "C:\Users\orisi\.openclaw\workspace\nstatus.txt" -Encoding UTF8 }
else { "FAIL" | Out-File "C:\Users\orisi\.openclaw\workspace\nstatus.txt" -Encoding UTF8 }
