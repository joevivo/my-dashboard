[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$RequestedUrl,

    [Parameter(Mandatory = $true)]
    [string]$BodyPath,

    [Parameter(Mandatory = $true)]
    [string]$HeadersPath,

    [ValidateRange(1, 300)]
    [int]$RequestTimeoutSeconds = 60,

    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$failures = New-Object System.Collections.Generic.List[string]

if ($RequestedUrl -notmatch "^https://") {
    $failures.Add("requested_url_invalid")
}

foreach ($targetPath in @($BodyPath, $HeadersPath)) {
    if (-not [System.IO.Path]::IsPathRooted($targetPath)) {
        $failures.Add("target_path_not_absolute")
        continue
    }

    if (Test-Path -LiteralPath $targetPath) {
        $failures.Add("target_already_exists")
    }

    $parent = Split-Path -Parent $targetPath

    if (-not (Test-Path -LiteralPath $parent -PathType Container)) {
        $failures.Add("target_parent_missing")
    }
}

$validationPass = $failures.Count -eq 0

if ($DryRun -or -not $validationPass) {
    Write-Host "`n# RESULT SUMMARY"
    Write-Host "TRANSPORT_MODE: $(if ($DryRun) { 'DRY_RUN' } else { 'VALIDATION_FAILED' })"
    Write-Host "REQUESTED_URL: $RequestedUrl"
    Write-Host "BODY_PATH: $BodyPath"
    Write-Host "HEADERS_PATH: $HeadersPath"
    Write-Host "VALIDATION_FAILURES: $(if ($failures.Count) { $failures -join ', ' } else { 'none' })"
    Write-Host "TRANSPORT_VALIDATION: $(if ($validationPass) { 'PASS' } else { 'FAIL' })"
    Write-Host "HTTP_REQUESTS_EXECUTED: 0"

    if ($validationPass) {
        exit 0
    }

    exit 4
}

$curlArguments = @(
    "--ssl-no-revoke"
    "--location"
    "--silent"
    "--show-error"
    "--connect-timeout"
    "20"
    "--max-time"
    [string]$RequestTimeoutSeconds
    "--dump-header"
    $HeadersPath
    "--output"
    $BodyPath
    "--write-out"
    "%{http_code}|%{url_effective}|%{content_type}"
    $RequestedUrl
)

$curlOutput = @(& curl.exe @curlArguments 2>&1)
$curlExitCode = $LASTEXITCODE

$writeOutLine = if ($curlOutput.Count -gt 0) {
    $curlOutput[-1].ToString()
}
else {
    ""
}

$parts = @($writeOutLine -split "\|", 3)
$httpStatus = "<unavailable>"
$effectiveUrl = "<unavailable>"
$contentType = "<unavailable>"

if ($parts.Count -eq 3) {
    $httpStatus = $parts[0]
    $effectiveUrl = $parts[1]
    $contentType = $parts[2]
}

$bodyPresent = Test-Path -LiteralPath $BodyPath -PathType Leaf
$headersPresent = Test-Path -LiteralPath $HeadersPath -PathType Leaf
$byteCount = 0
$sha256 = "<unavailable>"

if ($bodyPresent) {
    $byteCount = (Get-Item -LiteralPath $BodyPath).Length
    $sha256 = (Get-FileHash -LiteralPath $BodyPath -Algorithm SHA256).Hash
}

$statusNumber = 0
$statusParsed = [int]::TryParse([string]$httpStatus, [ref]$statusNumber)

$httpSuccess = (
    $statusParsed -and
    $statusNumber -ge 200 -and
    $statusNumber -lt 300
)

$capturePass = (
    $curlExitCode -eq 0 -and
    $httpSuccess -and
    $bodyPresent -and
    $headersPresent -and
    $byteCount -gt 0
)

Write-Host "`n# RESULT SUMMARY"
Write-Host "TRANSPORT_MODE: LIVE"
Write-Host "REQUESTED_URL: $RequestedUrl"
Write-Host "CURL_EXIT_CODE: $curlExitCode"
Write-Host "HTTP_STATUS: $httpStatus"
Write-Host "EFFECTIVE_URL: $effectiveUrl"
Write-Host "CONTENT_TYPE: $contentType"
Write-Host "BODY_PRESENT: $(if ($bodyPresent) { 'PASS' } else { 'FAIL' })"
Write-Host "HEADERS_PRESENT: $(if ($headersPresent) { 'PASS' } else { 'FAIL' })"
Write-Host "BYTE_COUNT: $byteCount"
Write-Host "SHA256: $sha256"
Write-Host "TRANSPORT_VALIDATION: $(if ($capturePass) { 'PASS' } else { 'FAIL' })"
Write-Host "HTTP_REQUESTS_EXECUTED: 1"

if ($capturePass) {
    exit 0
}

exit 3
