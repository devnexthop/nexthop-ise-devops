<#
.SYNOPSIS
  Collect dACLs, endpoint groups, identity sequences, and network device groups via ERS.

.DESCRIPTION
  Read-only ERS GETs for objects needed in a policy cross-reference / ISE assessment.
  Uses page=N paging without a size= query (many ISE builds 404 when size is set).

  Writes into the current directory:
    dacls\*.json
    endpointgroups.json
    idstoresequences.json
    networkdevicegroups.json

  Keep these outputs out of git — they are customer configuration.

.PARAMETER Pan
  ISE PAN hostname or IP.

.PARAMETER User
  Optional ERS username.

.PARAMETER Port
  ERS HTTPS port (default 443; try 9060 if diag shows 443 failing).

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File .\pull_ise_objects.ps1 -Pan ise-pan.example.com
#>
param([string]$Pan, [string]$User, [int]$Port = 443)

[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
try {
  Add-Type @"
using System.Net;using System.Security.Cryptography.X509Certificates;
public class TrustAllObj: ICertificatePolicy{public bool CheckValidationResult(ServicePoint s,X509Certificate c,WebRequest r,int p){return true;}}
"@ -ErrorAction SilentlyContinue
  [Net.ServicePointManager]::CertificatePolicy = New-Object TrustAllObj
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
Write-Host "=== pull_ise_objects (page=N, no size param) ===" -ForegroundColor Magenta

function Get-Json($url) {
  $r = Invoke-WebRequest -Uri $url -Headers $H -Method Get -TimeoutSec 60 -UseBasicParsing
  return ($r.Content | ConvertFrom-Json)
}
function Get-Coll($res) {
  $all = @(); $page = 1
  while ($true) {
    $url = if ($page -eq 1) { "$base/$res" } else { "$base/$res`?page=$page" }
    try { $j = Get-Json $url }
    catch {
      Write-Host ("  list {0} page {1}: {2}" -f $res, $page, $_.Exception.Message) -ForegroundColor Red
      break
    }
    if ($j.SearchResult.resources) { $all += $j.SearchResult.resources }
    if ($j.SearchResult.nextPage -and $j.SearchResult.nextPage.href) { $page++ } else { break }
  }
  return $all
}

Write-Host "Collecting downloadable ACLs..." -ForegroundColor Yellow
$dacls = Get-Coll "downloadableacl"
Write-Host ("  {0} dACLs found; fetching content..." -f $dacls.Count)
New-Item -ItemType Directory -Force -Path ".\dacls" | Out-Null
$n = 0
foreach ($d in $dacls) {
  try {
    (Get-Json "$base/downloadableacl/$($d.id)") | ConvertTo-Json -Depth 20 |
      Out-File -Encoding UTF8 (".\dacls\" + (($d.name) -replace '[\\/:*?"<>| ]', '_') + ".json")
    $n++
  } catch {
    Write-Host "  dACL $($d.name) FAILED: $($_.Exception.Message)" -ForegroundColor Red
  }
}
Write-Host ("  saved {0} dACL bodies -> .\dacls\" -f $n) -ForegroundColor Green

Write-Host "Collecting endpoint identity groups..." -ForegroundColor Yellow
$eg = Get-Coll "endpointgroup"
$eg | ConvertTo-Json -Depth 10 | Out-File -Encoding UTF8 "endpointgroups.json"
Write-Host ("  {0} endpoint groups -> endpointgroups.json" -f $eg.Count) -ForegroundColor Green

Write-Host "Collecting identity source sequences..." -ForegroundColor Yellow
$seq = Get-Coll "idstoresequence"; $seqD = @()
foreach ($s in $seq) {
  try { $seqD += (Get-Json "$base/idstoresequence/$($s.id)") } catch {}
}
$seqD | ConvertTo-Json -Depth 20 | Out-File -Encoding UTF8 "idstoresequences.json"
Write-Host ("  {0} sequences -> idstoresequences.json" -f $seq.Count) -ForegroundColor Green

Write-Host "Collecting network device groups..." -ForegroundColor Yellow
$ndg = Get-Coll "networkdevicegroup"
$ndg | ConvertTo-Json -Depth 10 | Out-File -Encoding UTF8 "networkdevicegroups.json"
Write-Host ("  {0} NDGs -> networkdevicegroups.json" -f $ndg.Count) -ForegroundColor Green

Write-Host ""
Write-Host "Done. Keep JSON outputs local — do not commit customer exports." -ForegroundColor Cyan
