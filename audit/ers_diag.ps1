<#
.SYNOPSIS
  Probe ISE ERS endpoints (ports 443 vs 9060, with/without paging params).

.DESCRIPTION
  Read-only connectivity check before a full audit pull. Prints HTTP status and a
  short body snippet for each URL variant. Use this first when ERS returns unexpected
  404s — some ISE builds reject ?size= on certain collections.

.PARAMETER Pan
  ISE PAN hostname or IP (no scheme). Prompted if omitted.

.PARAMETER User
  Optional ERS username; otherwise Get-Credential prompts for both.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File .\ers_diag.ps1 -Pan ise-pan.example.com
#>
param([string]$Pan, [string]$User)

[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
try {
  Add-Type @"
using System.Net;using System.Security.Cryptography.X509Certificates;
public class TrustAllD: ICertificatePolicy{public bool CheckValidationResult(ServicePoint s,X509Certificate c,WebRequest r,int p){return true;}}
"@ -ErrorAction SilentlyContinue
  [Net.ServicePointManager]::CertificatePolicy = New-Object TrustAllD
} catch {}

while ([string]::IsNullOrWhiteSpace($Pan)) { $Pan = Read-Host "ISE PAN hostname" }
$Pan = $Pan.Trim() -replace '^\s*https?://', '' -replace '/.*$', ''
if ([string]::IsNullOrWhiteSpace($User)) {
  $cred = Get-Credential -Message "ISE ERS account"
} else {
  $cred = Get-Credential -Message "ISE ERS password" -UserName $User
}
$auth = [Convert]::ToBase64String(
  [Text.Encoding]::ASCII.GetBytes($cred.UserName + ":" + $cred.GetNetworkCredential().Password)
)
$H = @{ Authorization = "Basic $auth"; Accept = "application/json" }

$tests = @(
  "https://${Pan}:443/ers/config/authorizationprofile",
  "https://${Pan}:443/ers/config/authorizationprofile?size=100&page=1",
  "https://${Pan}:9060/ers/config/authorizationprofile",
  "https://${Pan}:443/ers/config/downloadableacl",
  "https://${Pan}:9060/ers/config/downloadableacl",
  "https://${Pan}:443/ers/config/endpointgroup",
  "https://${Pan}:9060/ers/config/endpointgroup"
)
foreach ($u in $tests) {
  try {
    $r = Invoke-WebRequest -Uri $u -Headers $H -Method Get -TimeoutSec 30 -UseBasicParsing
    $body = $r.Content
    if ($body.Length -gt 120) { $body = $body.Substring(0, 120) }
    Write-Host ("[{0}] {1}" -f $r.StatusCode, $u) -ForegroundColor Green
    Write-Host ("        {0}" -f ($body -replace '\s+', ' ')) -ForegroundColor DarkGray
  } catch {
    $code = $_.Exception.Response.StatusCode.value__
    Write-Host ("[{0}] {1}" -f $(if ($code) { $code } else { 'ERR' }), $u) -ForegroundColor Red
    Write-Host ("        {0}" -f $_.Exception.Message) -ForegroundColor DarkGray
  }
}
