param(
  [string]$InputRoot = "$env:USERPROFILE\apple-music-sanitized",
  [string]$OutputName = "apple-music-dashboard-rollup.json"
)

$ErrorActionPreference = "Stop"

# Privacy posture:
# - Reads sanitized Apple Music exports only.
# - Produces aggregate-only rollup.
# - Does not emit track names, artist names, album names, playlist names, favorite item descriptions, recently played descriptions, or top content names.
# - Generated rollup is personal data and should remain outside Git.

$dailyPath = Join-Path $InputRoot "apple-music-daily-track-summary.csv"
$favoritesPath = Join-Path $InputRoot "apple-music-favorites.csv"
$recentPath = Join-Path $InputRoot "apple-music-recently-played.csv"
$topContentPath = Join-Path $InputRoot "apple-music-top-content.csv"
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

function Sum-Property {
  param(
    [object[]]$Rows,
    [string]$Property
  )

  return ($Rows | Measure-Object -Property $Property -Sum).Sum
}

$daily = Import-Csv -Path $dailyPath

$datedDaily = foreach ($row in $daily) {
  $date = Convert-CompactAppleDate $row.'Date Played'

  if ($null -ne $date) {
    [pscustomobject]@{
      Date = $date.Date
      Year = $date.ToString("yyyy")
      Month = $date.ToString("yyyy-MM")
      Plays = Convert-ToNumber $row.'Play Count'
      Skips = Convert-ToNumber $row.'Skip Count'
      DurationMs = Convert-ToNumber $row.'Play Duration Milliseconds'
      SourceType = $row.'Source Type'
    }
  }
}

if (@($datedDaily).Count -eq 0) {
  throw "No dated daily rows parsed. Rollup not created."
}

$totalPlays = Sum-Property -Rows $datedDaily -Property "Plays"
$totalSkips = Sum-Property -Rows $datedDaily -Property "Skips"
$totalDurationMs = Sum-Property -Rows $datedDaily -Property "DurationMs"
$totalHours = [math]::Round(($totalDurationMs / 1000 / 60 / 60), 2)

$firstDate = ($datedDaily | Sort-Object Date | Select-Object -First 1).Date
$lastDate = ($datedDaily | Sort-Object Date -Descending | Select-Object -First 1).Date

$activeListeningDays = @($datedDaily | Group-Object Date).Count
$totalCalendarDays = (($lastDate - $firstDate).Days + 1)
$activeDayRate = if ($totalCalendarDays -gt 0) { [math]::Round(($activeListeningDays / $totalCalendarDays), 4) } else { 0 }
$skipRate = if ($totalPlays -gt 0) { [math]::Round(($totalSkips / $totalPlays), 4) } else { 0 }
$averageMinutesPerPlay = if ($totalPlays -gt 0) { [math]::Round(($totalDurationMs / $totalPlays / 1000 / 60), 2) } else { 0 }

$playsByYear = $datedDaily |
  Group-Object Year |
  Sort-Object Name |
  ForEach-Object {
    $groupDurationMs = Sum-Property -Rows $_.Group -Property "DurationMs"

    [pscustomobject]@{
      year = $_.Name
      plays = [int](Sum-Property -Rows $_.Group -Property "Plays")
      skips = [int](Sum-Property -Rows $_.Group -Property "Skips")
      durationHours = [math]::Round(($groupDurationMs / 1000 / 60 / 60), 2)
      activeDays = @($_.Group | Group-Object Date).Count
    }
  }

$playsByMonth = $datedDaily |
  Group-Object Month |
  Sort-Object Name |
  ForEach-Object {
    $groupDurationMs = Sum-Property -Rows $_.Group -Property "DurationMs"

    [pscustomobject]@{
      month = $_.Name
      plays = [int](Sum-Property -Rows $_.Group -Property "Plays")
      skips = [int](Sum-Property -Rows $_.Group -Property "Skips")
      durationHours = [math]::Round(($groupDurationMs / 1000 / 60 / 60), 2)
      activeDays = @($_.Group | Group-Object Date).Count
    }
  }

$sourceTypeSummary = $datedDaily |
  Group-Object SourceType |
  Sort-Object Count -Descending |
  ForEach-Object {
    [pscustomobject]@{
      sourceType = if ([string]::IsNullOrWhiteSpace($_.Name)) { "Unspecified" } else { $_.Name }
      rows = $_.Count
      plays = [int](Sum-Property -Rows $_.Group -Property "Plays")
      skips = [int](Sum-Property -Rows $_.Group -Property "Skips")
      durationHours = [math]::Round(((Sum-Property -Rows $_.Group -Property "DurationMs") / 1000 / 60 / 60), 2)
    }
  }

$favorites = if (Test-Path $favoritesPath) { Import-Csv -Path $favoritesPath } else { @() }
$recent = if (Test-Path $recentPath) { Import-Csv -Path $recentPath } else { @() }
$topContent = if (Test-Path $topContentPath) { Import-Csv -Path $topContentPath } else { @() }

$favoritesByType = $favorites |
  Group-Object 'Favorite Type' |
  Sort-Object Count -Descending |
  ForEach-Object {
    [pscustomobject]@{
      favoriteType = if ([string]::IsNullOrWhiteSpace($_.Name)) { "Unspecified" } else { $_.Name }
      count = $_.Count
    }
  }

$last12MonthStart = $lastDate.AddMonths(-12).AddDays(1)
$last12Months = @($datedDaily | Where-Object { $_.Date -ge $last12MonthStart -and $_.Date -le $lastDate })

$mostRecentCompleteYear = $lastDate.Year - 1
$priorCompleteYear = $mostRecentCompleteYear - 1

$mostRecentYearSummary = $playsByYear | Where-Object { $_.year -eq [string]$mostRecentCompleteYear } | Select-Object -First 1
$priorYearSummary = $playsByYear | Where-Object { $_.year -eq [string]$priorCompleteYear } | Select-Object -First 1

$highestPlayYear = $playsByYear | Sort-Object plays -Descending | Select-Object -First 1
$highestHourYear = $playsByYear | Sort-Object durationHours -Descending | Select-Object -First 1
$highestPlayMonth = $playsByMonth | Sort-Object plays -Descending | Select-Object -First 1
$highestHourMonth = $playsByMonth | Sort-Object durationHours -Descending | Select-Object -First 1

$rollup = [pscustomobject]@{
  generatedAt = (Get-Date).ToString("s")
  source = "sanitized Apple Music exports only"
  privacyLevel = "aggregate-only"
  excludedContent = @(
    "track names",
    "artist names",
    "album names",
    "playlist names",
    "favorite item descriptions",
    "recently played descriptions",
    "top content names",
    "station descriptions"
  )
  filesUsed = @(
    "apple-music-daily-track-summary.csv",
    "apple-music-favorites.csv",
    "apple-music-recently-played.csv",
    "apple-music-top-content.csv"
  )
  totals = [pscustomobject]@{
    dailyRows = @($daily).Count
    datedDailyRows = @($datedDaily).Count
    totalPlays = [int]$totalPlays
    totalSkips = [int]$totalSkips
    totalDurationHours = $totalHours
    firstDatePlayed = $firstDate.ToString("yyyy-MM-dd")
    lastDatePlayed = $lastDate.ToString("yyyy-MM-dd")
    favoriteRows = @($favorites).Count
    recentlyPlayedRows = @($recent).Count
    topContentRows = @($topContent).Count
  }
  activity = [pscustomobject]@{
    activeListeningDays = $activeListeningDays
    totalCalendarDays = $totalCalendarDays
    activeDayRate = $activeDayRate
    averagePlaysPerActiveDay = [math]::Round(($totalPlays / $activeListeningDays), 2)
    averageSkipsPerActiveDay = [math]::Round(($totalSkips / $activeListeningDays), 2)
    averageHoursPerActiveDay = [math]::Round(($totalHours / $activeListeningDays), 2)
    skipRate = $skipRate
    averageMinutesPerPlay = $averageMinutesPerPlay
  }
  peaks = [pscustomobject]@{
    highestPlayYear = $highestPlayYear
    highestHourYear = $highestHourYear
    highestPlayMonth = $highestPlayMonth
    highestHourMonth = $highestHourMonth
  }
  recent = [pscustomobject]@{
    last12MonthStart = $last12MonthStart.ToString("yyyy-MM-dd")
    last12MonthEnd = $lastDate.ToString("yyyy-MM-dd")
    last12MonthsPlays = [int](Sum-Property -Rows $last12Months -Property "Plays")
    last12MonthsSkips = [int](Sum-Property -Rows $last12Months -Property "Skips")
    last12MonthsHours = [math]::Round(((Sum-Property -Rows $last12Months -Property "DurationMs") / 1000 / 60 / 60), 2)
    mostRecentCompleteYear = $mostRecentCompleteYear
    priorCompleteYear = $priorCompleteYear
    mostRecentCompleteYearPlays = if ($mostRecentYearSummary) { $mostRecentYearSummary.plays } else { $null }
    priorCompleteYearPlays = if ($priorYearSummary) { $priorYearSummary.plays } else { $null }
    yearOverYearPlayDelta = if ($mostRecentYearSummary -and $priorYearSummary) { [int]($mostRecentYearSummary.plays - $priorYearSummary.plays) } else { $null }
    mostRecentCompleteYearHours = if ($mostRecentYearSummary) { $mostRecentYearSummary.durationHours } else { $null }
    priorCompleteYearHours = if ($priorYearSummary) { $priorYearSummary.durationHours } else { $null }
    yearOverYearHourDelta = if ($mostRecentYearSummary -and $priorYearSummary) { [math]::Round(($mostRecentYearSummary.durationHours - $priorYearSummary.durationHours), 2) } else { $null }
  }
  sourceTypeSummary = $sourceTypeSummary
  favoritesByType = $favoritesByType
  playsByYear = $playsByYear
  playsByMonth = $playsByMonth
}

$rollup | ConvertTo-Json -Depth 8 | Set-Content -Path $rollupPath -Encoding UTF8

Write-Host "WROTE: $OutputName"
Write-Host "Privacy level: $($rollup.privacyLevel)"
Write-Host "Daily rows: $($rollup.totals.dailyRows)"
Write-Host "Dated rows: $($rollup.totals.datedDailyRows)"
Write-Host "Total plays: $($rollup.totals.totalPlays)"
Write-Host "Total skips: $($rollup.totals.totalSkips)"
Write-Host "Total hours: $($rollup.totals.totalDurationHours)"
Write-Host "Date range: $($rollup.totals.firstDatePlayed) to $($rollup.totals.lastDatePlayed)"
Write-Host "Active listening days: $($rollup.activity.activeListeningDays)"
Write-Host "Active day rate: $($rollup.activity.activeDayRate)"
Write-Host "Skip rate: $($rollup.activity.skipRate)"
Write-Host "Source type buckets: $(@($rollup.sourceTypeSummary).Count)"
Write-Host "Favorite type buckets: $(@($rollup.favoritesByType).Count)"
Write-Host "Year buckets: $(@($rollup.playsByYear).Count)"
Write-Host "Month buckets: $(@($rollup.playsByMonth).Count)"
Write-Host "DONE: aggregate-only dashboard rollup created from sanitized files."
