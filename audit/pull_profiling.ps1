<#
.SYNOPSIS
  Pull profiling policy index (name↔id) and logical profiles via ERS.

.DESCRIPTION
  Read-only. Large deployments often have 1000+ profiler profiles; this writes a
  lightweight name/id index plus full logical-profile bodies when ERS exposes them.

  Writes: profilerprofiles_index.json, logicalprofiles\*.json (if available)

.PARAMETER Pan
  ISE PAN hostname or IP.

.PARAMETER User
  Optional ERS username.

.PARAMETER Port
  ERS HTTPS port (default 443).

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File .\pull_profiling.ps1 -Pan ise-pan.example.com
#>
param([string]$Pan, [string]$User, [int]$Port = 443)

[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
try {
  Add-Type @"
using System.Net;using System.Security.Cryptography.X509Certificates;
public class TrustAllP: ICertificatePolicy{public bool CheckValidationResult(ServicePoint s,X509Certificate c,WebRequest r,int p){return true;}}
"@ -ErrorAction SilentlyContinue
  [Net.ServicePointManager]::CertificatePolicy = New-Object TrustAllP
} catch {}

while ([string]::IsNullOrWhiteSpace($Pan)) { $Pan = Read-Host "ISE PAN hostname" }
$Pan = $Pan.Trim() -replace '^\s*https?://', '' -replace '/.*$', ''
$base = "https://${Pan}:${Port}/ers/config"
if ([string]::IsNullOrWhiteSpace($User)) {
  $cred = Get-Credential -Message "ISE ERS account"
} else {
  $cred = Get-Credential -Message "ISE ERS password" -UserName $User
}
$auth = [Convert]::ToBase64String(
  [Text.Encoding]::ASCII.GetBytes($cred.UserName + ":" + $cred.GetNetworkCredential().Password)
)
$H = @{ Authorization = "Basic $auth"; Accept = "application/json" }
Write-Host "=== pull_profiling ===" -ForegroundColor Magenta

function Get-Json($u) {
  (Invoke-WebRequest -Uri $u -Headers $H -Method Get -TimeoutSec 60 -UseBasicParsing).Content | ConvertFrom-Json
}
function Get-Coll($res) {
  $all = @(); $page = 1
  while ($true) {
    $u = if ($page -eq 1) { "$base/$res" } else { "$base/$res`?page=$page" }
    try { $j = Get-Json $u }
    catch {
      Write-Host ("  list {0} page {1}: {2}" -f $res, $page, $_.Exception.Message) -ForegroundColor Red
      break
    }
    if ($j.SearchResult.resources) { $all += $j.SearchResult.resources }
    if ($j.SearchResult.nextPage -and $j.SearchResult.nextPage.href) { $page++ } else { break }
  }
  return $all
}

Write-Host "Profiling policies (name<->id map)..." -ForegroundColor Yellow
$pp = Get-Coll "profilerprofile"
$pp | Select-Object name, id | ConvertTo-Json -Depth 5 |
  Out-File -Encoding UTF8 "profilerprofiles_index.json"
Write-Host ("  {0} profiling policies -> profilerprofiles_index.json" -f $pp.Count) -ForegroundColor Green

Write-Host "Logical profiles (with membership)..." -ForegroundColor Yellow
$lp = Get-Coll "logicalprofile"
if ($lp.Count -gt 0) {
  New-Item -ItemType Directory -Force -Path ".\logicalprofiles" | Out-Null
  $n = 0
  foreach ($l in $lp) {
    try {
      (Get-Json "$base/logicalprofile/$($l.id)") | ConvertTo-Json -Depth 20 |
        Out-File -Encoding UTF8 (".\logicalprofiles\" + (($l.name) -replace '[\\/:*?"<>| ]', '_') + ".json")
      $n++
    } catch {}
  }
  Write-Host ("  {0} logical profiles -> .\logicalprofiles\" -f $n) -ForegroundColor Green
} else {
  Write-Host "  logicalprofile not available via ERS on this build — use GUI export if needed." -ForegroundColor DarkYellow
}
Write-Host ""
Write-Host "Done. Do not commit customer exports." -ForegroundColor Cyan
