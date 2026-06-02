param(
  [string]$InputRoot = "$env:USERPROFILE\apple-music-sanitized",
  [string]$OutputName = "apple-music-dashboard-rollup.json"
)

$ErrorActionPreference = "Stop"

# This script reads sanitized Apple Music exports only.
# Do not point this at raw Apple export files.
# The generated rollup is personal data and should remain outside Git.

$dailyPath = Join-Path $InputRoot "apple-music-daily-track-summary.csv"
$rollupPath = Join-Path $InputRoot $OutputName

if (-not (Test-Path $dailyPath)) {
  throw "Missing sanitized daily file: $dailyPath"
}

function Convert-ToNumber {
  param($Value)

  if ($null -eq $Value -or [string]::IsNullOrWhiteSpace([string]$Value)) {
    return 0
  }

  $clean = ([string]$Value).Replace(",", "")
  $number = 0.0

  if ([double]::TryParse($clean, [ref]$number)) {
    return $number
  }

  return 0
}

function Convert-CompactAppleDate {
  param($Value)

  if ($null -eq $Value -or [string]::IsNullOrWhiteSpace([string]$Value)) {
    return $null
  }

  $text = [string]$Value
  $date = [datetime]::MinValue

  if ($text -match "^\d{8}$") {
    if ([datetime]::TryParseExact($text, "yyyyMMdd", $null, [Globalization.DateTimeStyles]::None, [ref]$date)) {
      return $date
    }

    if ([datetime]::TryParseExact($text, "MMddyyyy", $null, [Globalization.DateTimeStyles]::None, [ref]$date)) {
      return $date
    }
  }

  if ([datetime]::TryParse($text, [ref]$date)) {
    return $date
  }

  return $null
}

$daily = Import-Csv -Path $dailyPath

$datedDaily = foreach ($row in $daily) {
  $date = Convert-CompactAppleDate $row.'Date Played'

  if ($null -ne $date) {
    [pscustomobject]@{
      Date = $date
      Plays = Convert-ToNumber $row.'Play Count'
      Skips = Convert-ToNumber $row.'Skip Count'
      DurationMs = Convert-ToNumber $row.'Play Duration Milliseconds'
    }
  }
}

if (@($datedDaily).Count -eq 0) {
  throw "No dated daily rows parsed. Rollup not created."
}

$totalPlays = ($datedDaily | Measure-Object -Property Plays -Sum).Sum
$totalSkips = ($datedDaily | Measure-Object -Property Skips -Sum).Sum
$totalDurationMs = ($datedDaily | Measure-Object -Property DurationMs -Sum).Sum
$totalHours = [math]::Round(($totalDurationMs / 1000 / 60 / 60), 2)

$firstDate = ($datedDaily | Sort-Object Date | Select-Object -First 1).Date
$lastDate = ($datedDaily | Sort-Object Date -Descending | Select-Object -First 1).Date

$playsByYear = $datedDaily |
  Group-Object { $_.Date.ToString("yyyy") } |
  Sort-Object Name |
  ForEach-Object {
    [pscustomobject]@{
      year = $_.Name
      plays = [int](($_.Group | Measure-Object -Property Plays -Sum).Sum)
      skips = [int](($_.Group | Measure-Object -Property Skips -Sum).Sum)
      durationHours = [math]::Round((($_.Group | Measure-Object -Property DurationMs -Sum).Sum / 1000 / 60 / 60), 2)
    }
  }

$playsByMonth = $datedDaily |
  Group-Object { $_.Date.ToString("yyyy-MM") } |
  Sort-Object Name |
  ForEach-Object {
    [pscustomobject]@{
      month = $_.Name
      plays = [int](($_.Group | Measure-Object -Property Plays -Sum).Sum)
      skips = [int](($_.Group | Measure-Object -Property Skips -Sum).Sum)
      durationHours = [math]::Round((($_.Group | Measure-Object -Property DurationMs -Sum).Sum / 1000 / 60 / 60), 2)
    }
  }

$rollup = [pscustomobject]@{
  generatedAt = (Get-Date).ToString("s")
  source = "sanitized Apple Music exports only"
  totals = [pscustomobject]@{
    dailyRows = @($daily).Count
    datedDailyRows = @($datedDaily).Count
    totalPlays = [int]$totalPlays
    totalSkips = [int]$totalSkips
    totalDurationHours = $totalHours
    firstDatePlayed = $firstDate.ToString("yyyy-MM-dd")
    lastDatePlayed = $lastDate.ToString("yyyy-MM-dd")
  }
  playsByYear = $playsByYear
  playsByMonth = $playsByMonth
}

$rollup | ConvertTo-Json -Depth 6 | Set-Content -Path $rollupPath -Encoding UTF8

Write-Host "WROTE: $OutputName"
Write-Host "Daily rows: $($rollup.totals.dailyRows)"
Write-Host "Dated rows: $($rollup.totals.datedDailyRows)"
Write-Host "Total plays: $($rollup.totals.totalPlays)"
Write-Host "Total skips: $($rollup.totals.totalSkips)"
Write-Host "Total hours: $($rollup.totals.totalDurationHours)"
Write-Host "Date range: $($rollup.totals.firstDatePlayed) to $($rollup.totals.lastDatePlayed)"
Write-Host "Year buckets: $(@($rollup.playsByYear).Count)"
Write-Host "Month buckets: $(@($rollup.playsByMonth).Count)"
Write-Host "DONE: dashboard rollup created from sanitized files."
