<#
.SYNOPSIS
  Resolve profiler-profile GUIDs to names via ERS by-id GET.

.DESCRIPTION
  Read-only. AuthZ rules often store EndPointPolicy as opaque GUIDs. This script
  resolves a list of IDs from a CSV (or a small inline sample) into a name map.

  Input CSV columns: id  (optional name column ignored)
  See examples/profiling_guids_sample.csv

  Writes: profiling_guid_names.json

.PARAMETER Pan
  ISE PAN hostname or IP.

.PARAMETER User
  Optional ERS username.

.PARAMETER Port
  ERS HTTPS port (default 443).

.PARAMETER GuidCsv
  Path to CSV with an 'id' column. Default: .\profiling_guids.csv

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File .\resolve_profiling_guids.ps1 `
    -Pan ise-pan.example.com -GuidCsv .\examples\profiling_guids_sample.csv
#>
param(
  [string]$Pan,
  [string]$User,
  [int]$Port = 443,
  [string]$GuidCsv = ".\profiling_guids.csv"
)

[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
try {
  Add-Type @"
using System.Net;using System.Security.Cryptography.X509Certificates;
public class TrustAllG: ICertificatePolicy{public bool CheckValidationResult(ServicePoint s,X509Certificate c,WebRequest r,int p){return true;}}
"@ -ErrorAction SilentlyContinue
  [Net.ServicePointManager]::CertificatePolicy = New-Object TrustAllG
} catch {}

while ([string]::IsNullOrWhiteSpace($Pan)) { $Pan = Read-Host "ISE PAN hostname" }
$Pan = $Pan.Trim() -replace '^\s*https?://', '' -replace '/.*$', ''
$base = "https://${Pan}:${Port}/ers/config/profilerprofile"
if ([string]::IsNullOrWhiteSpace($User)) {
  $cred = Get-Credential -Message "ISE ERS account"
} else {
  $cred = Get-Credential -Message "ISE ERS password" -UserName $User
}
$auth = [Convert]::ToBase64String(
  [Text.Encoding]::ASCII.GetBytes($cred.UserName + ":" + $cred.GetNetworkCredential().Password)
)
$H = @{ Authorization = "Basic $auth"; Accept = "application/json" }
Write-Host "=== resolve_profiling_guids ===" -ForegroundColor Magenta

if (-not (Test-Path $GuidCsv)) {
  Write-Host @"
CSV not found: $GuidCsv

Create a file with header 'id' and one profiler GUID per row, e.g.:
  id
  00000000-0000-0000-0000-000000000001

Or copy examples\profiling_guids_sample.csv and replace with IDs from your policy export.
"@ -ForegroundColor Yellow
  exit 1
}

$ids = Import-Csv $GuidCsv | ForEach-Object { $_.id } | Where-Object { $_ -and $_ -notmatch '^\s*#' }
if (-not $ids) {
  Write-Host "No id values found in $GuidCsv" -ForegroundColor Red
  exit 1
}

$out = @{}
foreach ($id in $ids) {
  try {
    $j = (Invoke-WebRequest -Uri "$base/$id" -Headers $H -Method Get -TimeoutSec 30 -UseBasicParsing).Content |
      ConvertFrom-Json
    $pp = $j.ProfilerProfile
    $out[$id] = @{ name = $pp.name; parent = $pp.parentId; minCertainty = $pp.minimumCertaintyFactor }
    Write-Host ("  OK  {0}  ->  {1}" -f $id, $pp.name) -ForegroundColor Green
  } catch {
    Write-Host ("  FAIL {0}: {1}" -f $id, $_.Exception.Message) -ForegroundColor Red
  }
}
$out | ConvertTo-Json -Depth 6 | Out-File -Encoding UTF8 "profiling_guid_names.json"
Write-Host "Done -> profiling_guid_names.json (keep local; do not commit)." -ForegroundColor Cyan
