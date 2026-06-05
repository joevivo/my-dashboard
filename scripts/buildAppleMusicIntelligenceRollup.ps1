param(
  [string]$InputRoot = "$env:USERPROFILE\apple-music-sanitized",
  [string]$OutputName = "apple-music-intelligence-rollup.json"
)

$ErrorActionPreference = "Stop"

$dailyPath = Join-Path $InputRoot "apple-music-daily-track-summary.csv"
$outputPath = Join-Path $InputRoot $OutputName

if (-not (Test-Path $dailyPath)) {
  throw "Missing file: $dailyPath"
}

Write-Host "Loading daily summary..." -ForegroundColor Cyan
$rows = Import-Csv $dailyPath
Write-Host "Loaded $($rows.Count) rows." -ForegroundColor Cyan

$artistMap = @{}
$processed = 0
$skippedUnparseable = 0

foreach ($row in $rows) {
  $processed++

  $trackDescription = [string]$row.'Track Description'

  if ([string]::IsNullOrWhiteSpace($trackDescription)) {
    $skippedUnparseable++
    continue
  }

  $parts = $trackDescription -split ' - ', 2

  if ($parts.Count -lt 2) {
    $skippedUnparseable++
    continue
  }

  $artist = $parts[0].Trim()

  if ([string]::IsNullOrWhiteSpace($artist)) {
    $skippedUnparseable++
    continue
  }

  try {
    $datePlayed = [datetime]::ParseExact($row.'Date Played', 'yyyyMMdd', $null)
  }
  catch {
    $skippedUnparseable++
    continue
  }

  $year = $datePlayed.Year

  $plays = 0
  [int]::TryParse($row.'Play Count', [ref]$plays) | Out-Null

  $skips = 0
  [int]::TryParse($row.'Skip Count', [ref]$skips) | Out-Null

  if (-not $artistMap.ContainsKey($artist)) {
    $artistMap[$artist] = @{
      Artist = $artist
      FirstYear = $year
      LastYear = $year
      Years = New-Object System.Collections.Generic.HashSet[int]
      TotalPlays = 0
      TotalSkips = 0
    }
  }

  $entry = $artistMap[$artist]

  if ($year -lt $entry.FirstYear) {
    $entry.FirstYear = $year
  }

  if ($year -gt $entry.LastYear) {
    $entry.LastYear = $year
  }

  $null = $entry.Years.Add($year)
  $entry.TotalPlays += $plays
  $entry.TotalSkips += $skips
}

Write-Host "Processed $processed rows." -ForegroundColor Cyan
Write-Host "Skipped $skippedUnparseable unparseable rows." -ForegroundColor Yellow
Write-Host "Found $($artistMap.Count) artists." -ForegroundColor Cyan

$result = foreach ($entry in $artistMap.Values) {
  [pscustomobject]@{
    Artist = $entry.Artist
    FirstYear = $entry.FirstYear
    LastYear = $entry.LastYear
    DistinctYears = $entry.Years.Count
    TotalPlays = $entry.TotalPlays
    TotalSkips = $entry.TotalSkips
  }
}

$result =
  $result |
  Sort-Object @{ Expression = "DistinctYears"; Descending = $true },
              @{ Expression = "TotalPlays"; Descending = $true },
              @{ Expression = "Artist"; Descending = $false }

$result |
  ConvertTo-Json -Depth 5 |
  Set-Content $outputPath

Write-Host ""
Write-Host "Top 25 Constant Candidates" -ForegroundColor Green

$result |
  Select-Object -First 25 |
  Format-Table Artist, FirstYear, LastYear, DistinctYears, TotalPlays, TotalSkips -AutoSize

Write-Host ""
Write-Host "Output: $outputPath" -ForegroundColor Yellow