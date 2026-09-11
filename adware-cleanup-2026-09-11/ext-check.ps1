$base = "$env:LOCALAPPDATA\Google\Chrome\User Data\Default\Extensions"
$ids = @(
  'dgenbagabmmjpfjlbcnnlmpopipdapjo','kobncfkmjelbefaoohoblamnbacjggk','ihljmnfgkkmoikgkdkjejbkpdpbmcgeh',
  'ofgdcdohlhjfdhbnfkikfeakhpojhpgm','nkbihfbeogaeaoehlefnkodbefgpgknn','fkepacicchenbjecpbpbclokcabebhah',
  'dncepekefegjiljlfbihljgogephdhph','hghadmnjlclmajeenogjjjefdecofpag','hipbfijinpcgfogaopmgehiegacbhmob',
  'icadabneccecohhaonmhgbjelhgodfaa','ligfpkgaijhppilphabeoligampecpce','ooadnieabchijkibjpeieeliohjidnjj',
  'ajlcfcekeahcekcceikefojgpadlmmlk','ddkjhcenboebfkblgooihmhigblajcpi'
)
foreach ($id in $ids) {
  $d = Join-Path $base $id
  if (-not (Test-Path $d)) { Write-Output ("== {0} : (not installed)" -f $id); continue }
  $v = Get-ChildItem $d -Directory | Select-Object -First 1
  $mfPath = Join-Path $v.FullName 'manifest.json'
  try { $mf = Get-Content $mfPath -Raw | ConvertFrom-Json } catch { Write-Output ("== {0} : manifest unreadable" -f $id); continue }
  $nm = [string]$mf.name
  if ($nm -like '__MSG_*') {
    $key = $nm.Substring(6).TrimEnd('_')
    foreach ($loc in @('ko','en','en_US','en_GB')) {
      $mp = Join-Path $v.FullName ("_locales\{0}\messages.json" -f $loc)
      if (Test-Path $mp) {
        try {
          $msgs = Get-Content $mp -Raw | ConvertFrom-Json
          $msg = $msgs.PSObject.Properties[$key]
          if ($msg -and $msg.Value.message) { $nm = $msg.Value.message; break }
        } catch {}
      }
    }
  }
  Write-Output ("== {0} | {1} | v{2} | homepage={3}" -f $id, $nm, $mf.version, $mf.homepage_url)
  Write-Output ("   perms={0}" -f ($mf.permissions -join ','))
  Write-Output ("   hosts={0}" -f (($mf.host_permissions + $mf.optional_permissions) -join ','))
}
