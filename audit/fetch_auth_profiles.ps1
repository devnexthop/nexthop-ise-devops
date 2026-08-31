<#
.SYNOPSIS
  Download all ISE authorization profiles (full bodies) via ERS.

.DESCRIPTION
  Read-only. Lists every authorization profile, then GETs each by id.
  Profile content lives under /ers/config/authorizationprofile/{id} (not OpenAPI).

  Prereq: Administration > System > Settings > API Settings > ERS (Read) enabled.

  Writes: profiles\*.json  and  profiles_index.json (name,id)

.PARAMETER Pan
  ISE PAN hostname or IP.

.PARAMETER User
  Optional ERS username.

.PARAMETER Port
  ERS HTTPS port (default 443).

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File .\fetch_auth_profiles.ps1 -Pan ise-pan.example.com
#>
param([string]$Pan, [string]$User, [int]$Port = 443)

[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
try {
  Add-Type @"
using System.Net;using System.Security.Cryptography.X509Certificates;
public class TrustAllAP: ICertificatePolicy{public bool CheckValidationResult(ServicePoint s,X509Certificate c,WebRequest r,int p){return true;}}
"@ -ErrorAction SilentlyContinue
  [Net.ServicePointManager]::CertificatePolicy = New-Object TrustAllAP
} catch {}

while ([string]::IsNullOrWhiteSpace($Pan)) { $Pan = Read-Host "ISE PAN hostname" }
$Pan = $Pan.Trim() -replace '^\s*https?://', '' -replace '/.*$', ''
$base = "https://${Pan}:${Port}/ers/config/authorizationprofile"
if ([string]::IsNullOrWhiteSpace($User)) {
  $cred = Get-Credential -Message "ISE ERS account"
} else {
  $cred = Get-Credential -Message "ISE ERS password" -UserName $User
}
$auth = [Convert]::ToBase64String(
  [Text.Encoding]::ASCII.GetBytes($cred.UserName + ":" + $cred.GetNetworkCredential().Password)
)
$H = @{ Authorization = "Basic $auth"; Accept = "application/json" }
Write-Host "=== fetch_auth_profiles ===" -ForegroundColor Magenta

function Get-Json($url) {
  $r = Invoke-WebRequest -Uri $url -Headers $H -Method Get -TimeoutSec 60 -UseBasicParsing
  return ($r.Content | ConvertFrom-Json)
}
function Get-Coll() {
  $all = @(); $page = 1
  while ($true) {
    $url = if ($page -eq 1) { $base } else { "$base`?page=$page" }
    try { $j = Get-Json $url }
    catch {
      Write-Host ("  list page {0}: {1}" -f $page, $_.Exception.Message) -ForegroundColor Red
      break
    }
    if ($j.SearchResult.resources) { $all += $j.SearchResult.resources }
    if ($j.SearchResult.nextPage -and $j.SearchResult.nextPage.href) { $page++ } else { break }
  }
  return $all
}

Write-Host "Listing authorization profiles..." -ForegroundColor Yellow
$list = Get-Coll
$list | Select-Object name, id | ConvertTo-Json -Depth 5 |
  Out-File -Encoding UTF8 "profiles_index.json"
Write-Host ("  {0} profiles indexed -> profiles_index.json" -f $list.Count) -ForegroundColor Green

New-Item -ItemType Directory -Force -Path ".\profiles" | Out-Null
$n = 0
foreach ($p in $list) {
  try {
    (Get-Json "$base/$($p.id)") | ConvertTo-Json -Depth 20 |
      Out-File -Encoding UTF8 (".\profiles\" + (($p.name) -replace '[\\/:*?"<>| ]', '_') + ".json")
    $n++
    if (($n % 25) -eq 0) { Write-Host ("  ... {0}/{1}" -f $n, $list.Count) }
  } catch {
    Write-Host ("  FAIL {0}: {1}" -f $p.name, $_.Exception.Message) -ForegroundColor Red
  }
}
Write-Host ("  saved {0} profile bodies -> .\profiles\" -f $n) -ForegroundColor Green
Write-Host "Done. Do not commit customer exports." -ForegroundColor Cyan
