$path = 'C:\Windows\TEMP\openclaw-web-fetch-3babc63100e66ab0.log'
$lines = Get-Content $path -Encoding UTF8
$in = $false
$ev = @()
foreach ($l in $lines) {
    if ($l -match '^BEGIN:VEVENT') { $in = $true; $ev = @() }
    if ($in) { $ev += $l }
    if ($l -match '^END:VEVENT') {
        $in = $false
        $all = $ev -join ' '
        if ($all -match '탁구|레슨|이영우') {
            Write-Output '=== EVENT ==='
            $ev | ForEach-Object { Write-Output $_ }
        }
    }
}
