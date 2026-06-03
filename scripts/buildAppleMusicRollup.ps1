param(
  [string]$InputRoot = "$env:USERPROFILE\apple-music-sanitized",
  [string]$OutputName = "apple-music-dashboard-rollup.json"
)

$ErrorActionPreference = "Stop"

# Privacy posture:
# - Reads sanitized Apple Music exports only.
# - Produces aggregate-only rollup.
# - Does not emit track names, artist names, album names, playlist names, favorite item descriptions,
#   recently played descriptions, top content names, or station descriptions.
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

$maxReasonableMinutesPerPlay = 30
$maxReasonableDailyRowHours = 24

$daily = Import-Csv -Path $dailyPath

$datedDaily = foreach ($row in $daily) {
  $date = Convert-CompactAppleDate $row.'Date Played'

  if ($null -ne $date) {
    $plays = Convert-ToNumber $row.'Play Count'
    $skips = Convert-ToNumber $row.'Skip Count'
    $durationMs = Convert-ToNumber $row.'Play Duration Milliseconds'

    $rowHoursRaw = [math]::Round(($durationMs / 1000 / 60 / 60), 2)
    $averageMinutesPerPlayRaw = if ($plays -gt 0) {
      [math]::Round(($durationMs / $plays / 1000 / 60), 2)
    } else {
      0
    }

    $cappedByAverageMs = if ($plays -gt 0) {
      [math]::Min($durationMs, ($plays * $maxReasonableMinutesPerPlay * 60 * 1000))
    } else {
      $durationMs
    }

    $cappedDurationMs = [math]::Min($cappedByAverageMs, ($maxReasonableDailyRowHours * 60 * 60 * 1000))

    [pscustomobject]@{
      Date = $date.Date
      Year = $date.ToString("yyyy")
      Month = $date.ToString("yyyy-MM")
      Plays = $plays
      Skips = $skips
      DurationMsRaw = $durationMs
      DurationMsCapped = $cappedDurationMs
      SourceType = $row.'Source Type'
      IsSuspiciousAverageDuration = $averageMinutesPerPlayRaw -gt $maxReasonableMinutesPerPlay
      IsSuspiciousDailyDuration = $rowHoursRaw -gt $maxReasonableDailyRowHours
    }
  }
}

if (@($datedDaily).Count -eq 0) {
  throw "No dated daily rows parsed. Rollup not created."
}

$totalPlays = Sum-Property -Rows $datedDaily -Property "Plays"
$totalSkips = Sum-Property -Rows $datedDaily -Property "Skips"
$totalDurationMsRaw = Sum-Property -Rows $datedDaily -Property "DurationMsRaw"
$totalDurationMsCapped = Sum-Property -Rows $datedDaily -Property "DurationMsCapped"

$totalHoursRaw = [math]::Round(($totalDurationMsRaw / 1000 / 60 / 60), 2)
$totalHoursCapped = [math]::Round(($totalDurationMsCapped / 1000 / 60 / 60), 2)

$suspiciousAverageDurationRows = @($datedDaily | Where-Object { $_.IsSuspiciousAverageDuration }).Count
$suspiciousDailyDurationRows = @($datedDaily | Where-Object { $_.IsSuspiciousDailyDuration }).Count

$durationQuality = if ($suspiciousAverageDurationRows -gt 0 -or $suspiciousDailyDurationRows -gt 0) {
  "needs-review"
} else {
  "clean"
}

$firstDate = ($datedDaily | Sort-Object Date | Select-Object -First 1).Date
$lastDate = ($datedDaily | Sort-Object Date -Descending | Select-Object -First 1).Date

$activeListeningDays = @($datedDaily | Group-Object Date).Count
$totalCalendarDays = (($lastDate - $firstDate).Days + 1)
$activeDayRate = if ($totalCalendarDays -gt 0) { [math]::Round(($activeListeningDays / $totalCalendarDays), 4) } else { 0 }
$skipRate = if ($totalPlays -gt 0) { [math]::Round(($totalSkips / $totalPlays), 4) } else { 0 }

$playsByYear = $datedDaily |
  Group-Object Year |
  Sort-Object Name |
  ForEach-Object {
    [pscustomobject]@{
      year = $_.Name
      plays = [int](Sum-Property -Rows $_.Group -Property "Plays")
      skips = [int](Sum-Property -Rows $_.Group -Property "Skips")
      durationHoursRaw = [math]::Round(((Sum-Property -Rows $_.Group -Property "DurationMsRaw") / 1000 / 60 / 60), 2)
      durationHoursCapped = [math]::Round(((Sum-Property -Rows $_.Group -Property "DurationMsCapped") / 1000 / 60 / 60), 2)
      activeDays = @($_.Group | Group-Object Date).Count
    }
  }

$playsByMonth = $datedDaily |
  Group-Object Month |
  Sort-Object Name |
  ForEach-Object {
    [pscustomobject]@{
      month = $_.Name
      plays = [int](Sum-Property -Rows $_.Group -Property "Plays")
      skips = [int](Sum-Property -Rows $_.Group -Property "Skips")
      durationHoursRaw = [math]::Round(((Sum-Property -Rows $_.Group -Property "DurationMsRaw") / 1000 / 60 / 60), 2)
      durationHoursCapped = [math]::Round(((Sum-Property -Rows $_.Group -Property "DurationMsCapped") / 1000 / 60 / 60), 2)
      activeDays = @($_.Group | Group-Object Date).Count
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
$highestRawHourYear = $playsByYear | Sort-Object durationHoursRaw -Descending | Select-Object -First 1
$highestCappedHourYear = $playsByYear | Sort-Object durationHoursCapped -Descending | Select-Object -First 1
$highestPlayMonth = $playsByMonth | Sort-Object plays -Descending | Select-Object -First 1
$highestRawHourMonth = $playsByMonth | Sort-Object durationHoursRaw -Descending | Select-Object -First 1
$highestCappedHourMonth = $playsByMonth | Sort-Object durationHoursCapped -Descending | Select-Object -First 1

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
    totalDurationHoursRaw = $totalHoursRaw
    totalDurationHoursCapped = $totalHoursCapped
    firstDatePlayed = $firstDate.ToString("yyyy-MM-dd")
    lastDatePlayed = $lastDate.ToString("yyyy-MM-dd")
    favoriteRows = @($favorites).Count
    recentlyPlayedRows = @($recent).Count
    topContentRows = @($topContent).Count
  }
  durationSanity = [pscustomobject]@{
    quality = $durationQuality
    maxReasonableMinutesPerPlay = $maxReasonableMinutesPerPlay
    maxReasonableDailyRowHours = $maxReasonableDailyRowHours
    suspiciousAverageDurationRows = $suspiciousAverageDurationRows
    suspiciousDailyDurationRows = $suspiciousDailyDurationRows
    rawDurationHours = $totalHoursRaw
    cappedDurationHours = $totalHoursCapped
    rawMinusCappedHours = [math]::Round(($totalHoursRaw - $totalHoursCapped), 2)
  }
  activity = [pscustomobject]@{
    activeListeningDays = $activeListeningDays
    totalCalendarDays = $totalCalendarDays
    activeDayRate = $activeDayRate
    averagePlaysPerActiveDay = [math]::Round(($totalPlays / $activeListeningDays), 2)
    averageSkipsPerActiveDay = [math]::Round(($totalSkips / $activeListeningDays), 2)
    averageHoursPerActiveDayRaw = [math]::Round(($totalHoursRaw / $activeListeningDays), 2)
    averageHoursPerActiveDayCapped = [math]::Round(($totalHoursCapped / $activeListeningDays), 2)
    skipRate = $skipRate
    averageMinutesPerPlayRaw = if ($totalPlays -gt 0) { [math]::Round(($totalDurationMsRaw / $totalPlays / 1000 / 60), 2) } else { 0 }
    averageMinutesPerPlayCapped = if ($totalPlays -gt 0) { [math]::Round(($totalDurationMsCapped / $totalPlays / 1000 / 60), 2) } else { 0 }
  }
  peaks = [pscustomobject]@{
    highestPlayYear = $highestPlayYear
    highestRawHourYear = $highestRawHourYear
    highestCappedHourYear = $highestCappedHourYear
    highestPlayMonth = $highestPlayMonth
    highestRawHourMonth = $highestRawHourMonth
    highestCappedHourMonth = $highestCappedHourMonth
  }
  recent = [pscustomobject]@{
    last12MonthStart = $last12MonthStart.ToString("yyyy-MM-dd")
    last12MonthEnd = $lastDate.ToString("yyyy-MM-dd")
    last12MonthsPlays = [int](Sum-Property -Rows $last12Months -Property "Plays")
    last12MonthsSkips = [int](Sum-Property -Rows $last12Months -Property "Skips")
    last12MonthsHoursRaw = [math]::Round(((Sum-Property -Rows $last12Months -Property "DurationMsRaw") / 1000 / 60 / 60), 2)
    last12MonthsHoursCapped = [math]::Round(((Sum-Property -Rows $last12Months -Property "DurationMsCapped") / 1000 / 60 / 60), 2)
    mostRecentCompleteYear = $mostRecentCompleteYear
    priorCompleteYear = $priorCompleteYear
    mostRecentCompleteYearPlays = if ($mostRecentYearSummary) { $mostRecentYearSummary.plays } else { $null }
    priorCompleteYearPlays = if ($priorYearSummary) { $priorYearSummary.plays } else { $null }
    yearOverYearPlayDelta = if ($mostRecentYearSummary -and $priorYearSummary) { [int]($mostRecentYearSummary.plays - $priorYearSummary.plays) } else { $null }
    mostRecentCompleteYearHoursRaw = if ($mostRecentYearSummary) { $mostRecentYearSummary.durationHoursRaw } else { $null }
    priorCompleteYearHoursRaw = if ($priorYearSummary) { $priorYearSummary.durationHoursRaw } else { $null }
    yearOverYearHourDeltaRaw = if ($mostRecentYearSummary -and $priorYearSummary) { [math]::Round(($mostRecentYearSummary.durationHoursRaw - $priorYearSummary.durationHoursRaw), 2) } else { $null }
    mostRecentCompleteYearHoursCapped = if ($mostRecentYearSummary) { $mostRecentYearSummary.durationHoursCapped } else { $null }
    priorCompleteYearHoursCapped = if ($priorYearSummary) { $priorYearSummary.durationHoursCapped } else { $null }
    yearOverYearHourDeltaCapped = if ($mostRecentYearSummary -and $priorYearSummary) { [math]::Round(($mostRecentYearSummary.durationHoursCapped - $priorYearSummary.durationHoursCapped), 2) } else { $null }
  }
  favoritesByType = $favoritesByType
  playsByYear = $playsByYear
  playsByMonth = $playsByMonth
}


function Assert-AppleMusicRollupContract {
  param($Rollup)

  $json = $Rollup | ConvertTo-Json -Depth 12

  $forbiddenPatterns = @(
    "trackName",
    "artistName",
    "albumName",
    "playlistName",
    "stationName",
    "Track Description",
    "Track Name",
    "Item Description",
    "Container Description",
    "Station Description",
    "Content",
    "SourceType",
    "Source Type",
    "Device",
    "Platform",
    "Apple ID",
    "IP",
    "Latitude",
    "Longitude",
    "Location"
  )

  $violations = @()

  foreach ($pattern in $forbiddenPatterns) {
    if ($json -match [regex]::Escape($pattern)) {
      $violations += $pattern
    }
  }

  if ($violations.Count -gt 0) {
    throw "Apple Music dashboard rollup contract failed. Forbidden fields/content detected: $($violations -join ', ')"
  }

  if ($Rollup.privacyLevel -ne "aggregate-only") {
    throw "Apple Music dashboard rollup contract failed. privacyLevel must be aggregate-only."
  }
}

Assert-AppleMusicRollupContract -Rollup $rollup

$rollup | ConvertTo-Json -Depth 8 | Set-Content -Path $rollupPath -Encoding UTF8

Write-Host "WROTE: $OutputName"
Write-Host "Privacy level: $($rollup.privacyLevel)"
Write-Host "Daily rows: $($rollup.totals.dailyRows)"
Write-Host "Dated rows: $($rollup.totals.datedDailyRows)"
Write-Host "Total plays: $($rollup.totals.totalPlays)"
Write-Host "Total skips: $($rollup.totals.totalSkips)"
Write-Host "Total hours raw: $($rollup.totals.totalDurationHoursRaw)"
Write-Host "Total hours capped: $($rollup.totals.totalDurationHoursCapped)"
Write-Host "Duration quality: $($rollup.durationSanity.quality)"
Write-Host "Suspicious avg-duration rows: $($rollup.durationSanity.suspiciousAverageDurationRows)"
Write-Host "Suspicious daily-duration rows: $($rollup.durationSanity.suspiciousDailyDurationRows)"
Write-Host "Date range: $($rollup.totals.firstDatePlayed) to $($rollup.totals.lastDatePlayed)"
Write-Host "Active listening days: $($rollup.activity.activeListeningDays)"
Write-Host "Active day rate: $($rollup.activity.activeDayRate)"
Write-Host "Skip rate: $($rollup.activity.skipRate)"
Write-Host "Favorite type buckets: $(@($rollup.favoritesByType).Count)"
Write-Host "Year buckets: $(@($rollup.playsByYear).Count)"
Write-Host "Month buckets: $(@($rollup.playsByMonth).Count)"
Write-Host "DONE: aggregate-only dashboard rollup created from sanitized files."
