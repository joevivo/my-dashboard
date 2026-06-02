param(
  [string]$InputRoot = "$env:USERPROFILE\ams\Apple_Media_Services\Apple Music Activity",
  [string]$OutputRoot = "$env:USERPROFILE\apple-music-sanitized"
)

$ErrorActionPreference = "Stop"

New-Item -ItemType Directory -Force -Path $OutputRoot | Out-Null

$denyPattern = "(?i)(apple.?id|account|client.?ip|ip city|ip latitude|ip longitude|ip network|device|identifier|subscription|user.?id|hardware|payment|latitude|longitude|geo|postal|email|phone|address|token|^track reference$|^item reference$|^container reference$|^station id$|reference number$)"

function Export-SafeAppleMusicCsv {
  param(
    [string]$InputName,
    [string]$OutputName,
    [string[]]$Columns
  )

  $inputPath = Join-Path $InputRoot $InputName
  $outputPath = Join-Path $OutputRoot $OutputName

  if (-not (Test-Path $inputPath)) {
    throw "Missing input file: $InputName"
  }

  $badRequestedColumns = $Columns | Where-Object { $_ -match $denyPattern }
  if ($badRequestedColumns.Count -gt 0) {
    throw "Blocked column detected in sanitizer allowlist for $InputName."
  }

  $headerLine = Get-Content -Path $inputPath -TotalCount 1
  $headers = ($headerLine -split ",") | ForEach-Object { $_.Trim('"') }

  $missingColumns = $Columns | Where-Object { $_ -notin $headers }
  if ($missingColumns.Count -gt 0) {
    throw "Missing expected sanitized column(s) in $InputName`: $($missingColumns -join ', ')"
  }

  $rows = Import-Csv -Path $inputPath
  $rowCount = @($rows).Count

  $rows |
    Select-Object -Property $Columns |
    Export-Csv -Path $outputPath -NoTypeInformation -Encoding UTF8

  $outputHeader = Get-Content -Path $outputPath -TotalCount 1
  if ($outputHeader -match $denyPattern) {
    throw "Blocked header detected in sanitized output: $OutputName"
  }

  [pscustomobject]@{
    file = $OutputName
    rows = $rowCount
    columns = $Columns
  }
}

$summary = @()

$summary += Export-SafeAppleMusicCsv `
  -InputName "Apple Music - Play History Daily Tracks.csv" `
  -OutputName "apple-music-daily-track-summary.csv" `
  -Columns @("Media type", "Date Played", "Hours", "Play Duration Milliseconds", "End Reason Type", "Source Type", "Play Count", "Skip Count", "Ignore For Recommendations", "Track Description")

$summary += Export-SafeAppleMusicCsv `
  -InputName "Apple Music - Track Play History.csv" `
  -OutputName "apple-music-track-history.csv" `
  -Columns @("Track Name", "Last Played Date", "Is User Initiated")

$summary += Export-SafeAppleMusicCsv `
  -InputName "Apple Music - Recently Played Tracks.csv" `
  -OutputName "apple-music-recently-played.csv" `
  -Columns @("Last Modified", "Container Type", "Container Description", "Track Description", "Ignore For Recommendations", "Feature Name", "First Event Timestamp", "Last End Reason Tyoe", "Last Event End Timestamp", "Last Event Start Timestamp", "Max Event End Position in millis", "Max Play Duration in millis", "Media duration in millis", "Media type", "Min Event Start Position in millis", "Total plays", "Total skips", "Total play duration in millis")

$summary += Export-SafeAppleMusicCsv `
  -InputName "Apple Music - Top Content.csv" `
  -OutputName "apple-music-top-content.csv" `
  -Columns @("Content", "Play Duration Milliseconds", "First Played", "Last Played", "Source Type", "Rankings")

$summary += Export-SafeAppleMusicCsv `
  -InputName "Apple Music - Favorites.csv" `
  -OutputName "apple-music-favorites.csv" `
  -Columns @("Favorite Type", "Item Description", "Last Modified", "Preference")

$summary += Export-SafeAppleMusicCsv `
  -InputName "Apple Music - Play Statistics.csv" `
  -OutputName "apple-music-play-statistics.csv" `
  -Columns @("Play Duration Milliseconds", "First Played", "Last Played", "Source Type", "Date Created")

$summary += Export-SafeAppleMusicCsv `
  -InputName "Music - Liked Radio Tracks.csv" `
  -OutputName "apple-music-liked-radio-tracks.csv" `
  -Columns @("Created", "Track Description", "Event Type")

$summary += Export-SafeAppleMusicCsv `
  -InputName "Music - Favorite Stations.csv" `
  -OutputName "apple-music-favorite-stations.csv" `
  -Columns @("Shared?", "Created", "Last Modified", "Deleted?", "Station Description")

$summaryPath = Join-Path $OutputRoot "apple-music-summary.json"
$summary | ConvertTo-Json -Depth 6 | Set-Content -Path $summaryPath -Encoding UTF8

foreach ($item in $summary) {
  Write-Host "WROTE: $($item.file) rows=$($item.rows) columns=$(@($item.columns).Count)"
}

Write-Host "WROTE: apple-music-summary.json"
Write-Host "DONE: sanitized Apple Music outputs are in $OutputRoot"
