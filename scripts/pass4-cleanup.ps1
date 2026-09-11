# pass4 cleanup: remove secureconnection leftovers + Chrome policy (admin required)
$ErrorActionPreference = 'Continue'
$log = 'C:\Users\orisi\.openclaw\workspace\adware-cleanup-2026-09-11\pass4-applied.log'
function W($m){ $m | Out-File -FilePath $log -Append -Encoding utf8 }
"=== pass4 cleanup $(Get-Date -Format o) ===" | Out-File -FilePath $log -Encoding utf8
W ("admin: " + ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator))
W ("whoami: " + (whoami))

$keys = @('HKCU:\Software\check_secureconnection','HKLM:\SOFTWARE\WOW6432Node\check_secureconnection')
foreach($k in $keys){
  if(Test-Path $k){
    try{ Remove-Item -Path $k -Recurse -Force -ErrorAction Stop; W "REMOVED key: $k" }
    catch{ W "FAILED key: $k :: $($_.Exception.Message)" }
  } else { W "ABSENT key: $k" }
}

$cp='HKLM:\SOFTWARE\Policies\Google\Chrome'
if(Test-Path $cp){
  $names = (Get-Item $cp).Property
  W ("chrome policy values before: " + ($names -join ', '))
  if($names -contains 'InsecurePrivateNetworkRequestsAllowed'){
    try{ Remove-ItemProperty -Path $cp -Name 'InsecurePrivateNetworkRequestsAllowed' -Force -ErrorAction Stop; W "REMOVED value: InsecurePrivateNetworkRequestsAllowed" }
    catch{ W "FAILED value: InsecurePrivateNetworkRequestsAllowed :: $($_.Exception.Message)" }
  } else { W "ABSENT value: InsecurePrivateNetworkRequestsAllowed" }
  $names2 = (Get-Item $cp).Property
  W ("chrome policy values after: " + ($names2 -join ', '))
} else { W "ABSENT key: $cp" }

W "--- verify ---"
foreach($k in $keys){ W ("{0} exists => {1}" -f $k, (Test-Path $k)) }
W ("chrome policy value still present => " + [bool](((Get-Item $cp -ErrorAction SilentlyContinue).Property) -contains 'InsecurePrivateNetworkRequestsAllowed'))
W "done"
