<#
.SYNOPSIS
  Pull OpenAPI policy conditions + dictionaries; probe profiling-related endpoints.

.DESCRIPTION
  Read-only. Saves condition libraries and dictionaries used when building policy maps.
  Also probes several profiling / logical-profile URLs and prints status only (useful
  to learn which APIs exist on this ISE build).

  Writes: cond_all.json, cond_authentication.json, cond_authorization.json,
          cond_policyset.json, dictionaries.json

.PARAMETER Pan
  ISE PAN hostname or IP.

.PARAMETER User
  Optional API username.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File .\pull_policy_meta.ps1 -Pan ise-pan.example.com
#>
param([string]$Pan, [string]$User)

[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
try {
  Add-Type @"
using System.Net;using System.Security.Cryptography.X509Certificates;
public class TrustAllM: ICertificatePolicy{public bool CheckValidationResult(ServicePoint s,X509Certificate c,WebRequest r,int p){return true;}}
"@ -ErrorAction SilentlyContinue
  [Net.ServicePointManager]::CertificatePolicy = New-Object TrustAllM
} catch {}

while ([string]::IsNullOrWhiteSpace($Pan)) { $Pan = Read-Host "ISE PAN hostname" }
$Pan = $Pan.Trim() -replace '^\s*https?://', '' -replace '/.*$', ''
if ([string]::IsNullOrWhiteSpace($User)) {
  $cred = Get-Credential -Message "ISE API account"
} else {
  $cred = Get-Credential -Message "ISE API password" -UserName $User
}
$auth = [Convert]::ToBase64String(
  [Text.Encoding]::ASCII.GetBytes($cred.UserName + ":" + $cred.GetNetworkCredential().Password)
)
$H = @{ Authorization = "Basic $auth"; Accept = "application/json" }
Write-Host "=== pull_policy_meta ===" -ForegroundColor Magenta

function Save($url, $out) {
  try {
    $r = Invoke-WebRequest -Uri $url -Headers $H -Method Get -TimeoutSec 60 -UseBasicParsing
    $r.Content | Out-File -Encoding UTF8 $out
    Write-Host ("  [200] {0} -> {1}" -f $url, $out) -ForegroundColor Green
  } catch {
    $code = $_.Exception.Response.StatusCode.value__
    Write-Host ("  [{0}] {1}" -f $(if ($code) { $code } else { 'ERR' }), $url) -ForegroundColor Red
  }
}

$na = "https://$Pan/api/v1/policy/network-access"
Write-Host "Pulling conditions + dictionaries (OpenAPI)..." -ForegroundColor Yellow
Save "$na/condition"                "cond_all.json"
Save "$na/condition/authentication" "cond_authentication.json"
Save "$na/condition/authorization"  "cond_authorization.json"
Save "$na/condition/policyset"      "cond_policyset.json"
Save "$na/dictionaries"             "dictionaries.json"

Write-Host "PROBING profiling / logical-profile endpoints (status only)..." -ForegroundColor Yellow
$probes = @(
  "https://$Pan/api/v1/profiling/profilingrules",
  "https://$Pan/api/v1/policy/profiling",
  "https://${Pan}:9060/ers/config/profilerprofile",
  "https://$Pan/ers/config/profilerprofile",
  "https://${Pan}:9060/ers/config/logicalprofile",
  "https://$Pan/ers/config/endpoint?size=1"
)
foreach ($u in $probes) {
  try {
    $r = Invoke-WebRequest -Uri $u -Headers $H -Method Get -TimeoutSec 30 -UseBasicParsing
    $b = $r.Content
    if ($b.Length -gt 90) { $b = $b.Substring(0, 90) }
    Write-Host ("  [200] {0}" -f $u) -ForegroundColor Green
    Write-Host ("        {0}" -f ($b -replace '\s+', ' ')) -ForegroundColor DarkGray
  } catch {
    $code = $_.Exception.Response.StatusCode.value__
    Write-Host ("  [{0}] {1}" -f $(if ($code) { $code } else { 'ERR' }), $u) -ForegroundColor Red
  }
}
Write-Host ""
Write-Host "Done. Note which probe URLs returned 200. Do not commit JSON exports." -ForegroundColor Cyan
