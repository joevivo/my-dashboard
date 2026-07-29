[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$RunSpecPath,

    [switch]$InitializeRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Resolve-RepositoryRoot {
    $baseballRoot = Split-Path -Parent $PSScriptRoot
    return Split-Path -Parent $baseballRoot
}

function Resolve-RunSpecPath {
    param(
        [string]$RepositoryRoot,
        [string]$RequestedPath
    )

    if ([System.IO.Path]::IsPathRooted($RequestedPath)) {
        return [System.IO.Path]::GetFullPath($RequestedPath)
    }

    return [System.IO.Path]::GetFullPath(
        (Join-Path $RepositoryRoot $RequestedPath)
    )
}

function Test-RepositoryContainment {
    param(
        [string]$RepositoryRoot,
        [string]$CandidatePath
    )

    $rootPrefix = [System.IO.Path]::GetFullPath($RepositoryRoot).
        TrimEnd([System.IO.Path]::DirectorySeparatorChar) +
        [System.IO.Path]::DirectorySeparatorChar

    $fullCandidate = [System.IO.Path]::GetFullPath($CandidatePath)

    return $fullCandidate.StartsWith(
        $rootPrefix,
        [System.StringComparison]::OrdinalIgnoreCase
    )
}

function Get-RepositoryRelativePath {
    param(
        [string]$RepositoryRoot,
        [string]$CandidatePath
    )

    return [System.IO.Path]::GetFullPath($CandidatePath).
        Substring([System.IO.Path]::GetFullPath($RepositoryRoot).Length).
        TrimStart("\").
        Replace("\", "/")
}

function Write-Utf8NoBomJson {
    param(
        [string]$Path,
        [object]$Value
    )

    $json = $Value | ConvertTo-Json -Depth 30
    $json = $json.TrimEnd("`r", "`n") + [Environment]::NewLine
    $encoding = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, $json, $encoding)
}

$repoRoot = Resolve-RepositoryRoot
$resolvedRunSpecPath = Resolve-RunSpecPath `
    -RepositoryRoot $repoRoot `
    -RequestedPath $RunSpecPath

$failures = New-Object System.Collections.Generic.List[string]

if (-not (Test-RepositoryContainment `
    -RepositoryRoot $repoRoot `
    -CandidatePath $resolvedRunSpecPath)) {
    $failures.Add("run_spec_outside_repository")
}

if (-not (Test-Path -LiteralPath $resolvedRunSpecPath -PathType Leaf)) {
    $failures.Add("run_spec_not_found")
}

$runSpec = $null

if ($failures.Count -eq 0) {
    try {
        $runSpec = Get-Content -LiteralPath $resolvedRunSpecPath -Raw |
            ConvertFrom-Json -ErrorAction Stop
    }
    catch {
        $failures.Add("run_spec_json_invalid")
    }
}

if ($null -ne $runSpec) {
    if ($runSpec.schemaVersion -ne "strat365-league-capture-run-v0") {
        $failures.Add("schema_version_invalid")
    }

    if ($runSpec.baseUri -notmatch "^https://") {
        $failures.Add("base_uri_invalid")
    }

    if ($runSpec.playerSetYear -notmatch "^\d{4}$") {
        $failures.Add("player_set_year_invalid")
    }

    if ($runSpec.leagueId -notmatch "^\d+$") {
        $failures.Add("league_id_invalid")
    }

    $parsedDate = [datetime]::MinValue
    $dateValid = [datetime]::TryParseExact(
        $runSpec.leagueDate,
        "yyyy-MM-dd",
        [System.Globalization.CultureInfo]::InvariantCulture,
        [System.Globalization.DateTimeStyles]::None,
        [ref]$parsedDate
    )

    if (-not $dateValid) {
        $failures.Add("league_date_invalid")
    }

    if ($runSpec.expectedCounts.teamCount -lt 1 -or
        $runSpec.expectedCounts.gameCount -lt 1 -or
        $runSpec.expectedCounts.seriesCount -lt 1) {
        $failures.Add("expected_counts_invalid")
    }

    $uniqueTeamIds = @($runSpec.teamIds | Sort-Object -Unique)
    if ($uniqueTeamIds.Count -ne $runSpec.expectedCounts.teamCount) {
        $failures.Add("team_count_mismatch")
    }

    if (@($runSpec.teamIds).Count -ne $uniqueTeamIds.Count) {
        $failures.Add("duplicate_team_ids")
    }

    $uniqueFamilies = @(
        $runSpec.requiredSourceFamilies | Sort-Object -Unique
    )

    if (@($runSpec.requiredSourceFamilies).Count -ne
        $uniqueFamilies.Count) {
        $failures.Add("duplicate_source_families")
    }

    if ($runSpec.captureRootPolicy.
        requireRepositoryContainment -ne $true) {
        $failures.Add("repository_containment_not_required")
    }

    if ($runSpec.captureRootPolicy.allowOverwrite -ne $false) {
        $failures.Add("overwrite_not_blocked")
    }

    if ($runSpec.transportPolicy.client -ne "curl.exe" -or
        $runSpec.transportPolicy.sslNoRevoke -ne $true -or
        $runSpec.transportPolicy.followRedirects -ne $true -or
        $runSpec.transportPolicy.useAuthenticationCookies -ne $false -or
        $runSpec.transportPolicy.useRefererHeader -ne $false) {
        $failures.Add("transport_policy_invalid")
    }

    if ($runSpec.capturePlanPolicy.
        freezeBeforeBulkCapture -ne $true -or
        $runSpec.capturePlanPolicy.deduplicateUrls -ne $true -or
        $runSpec.capturePlanPolicy.rejectCrossLeagueLinks -ne $true -or
        $runSpec.capturePlanPolicy.rejectUnknownTeamIds -ne $true -or
        $runSpec.capturePlanPolicy.rejectUnplannedExpansion -ne $true) {
        $failures.Add("capture_plan_policy_invalid")
    }
}

$scoresUrl = "<unavailable>"
$projectedRunRoot = "<unavailable>"
$relativeRunSpec = $resolvedRunSpecPath

if ($null -ne $runSpec) {
    $scoresUrl = "{0}/league/scores/{1}/{2}" -f
        $runSpec.baseUri.TrimEnd("/"),
        $runSpec.leagueId,
        $runSpec.leagueDate

    $captureRoot = $runSpec.captureRootPolicy.relativeRootTemplate.
        Replace("{playerSetYear}", $runSpec.playerSetYear)

    $projectedRunRoot = "{0}/league-{1}/{2}/capture-{{utcTimestamp}}" -f
        $captureRoot.TrimEnd("/"),
        $runSpec.leagueId,
        $runSpec.leagueDate

    if (Test-RepositoryContainment `
        -RepositoryRoot $repoRoot `
        -CandidatePath $resolvedRunSpecPath) {
        $relativeRunSpec = $resolvedRunSpecPath.
            Substring($repoRoot.Length).
            TrimStart("\").
            Replace("\", "/")
    }
}

$preflightPass = $failures.Count -eq 0
$runInitialized = $false
$runDirectory = "<not initialized>"
$manifestFile = "<not initialized>"
$runSpecCopyFile = "<not initialized>"
$initialDirectoriesCreated = 0
$initialFilesCreated = 0
$initializationError = "none"

if ($preflightPass -and $InitializeRun) {
    try {
        $captureTimestampUtc = [datetime]::UtcNow
        $timestampToken = $captureTimestampUtc.ToString(
            $runSpec.captureRootPolicy.timestampFormat,
            [System.Globalization.CultureInfo]::InvariantCulture
        )

        $captureRootRelative = $runSpec.captureRootPolicy.
            relativeRootTemplate.
            Replace("{playerSetYear}", $runSpec.playerSetYear).
            TrimEnd("/")

        $runDirectory = "{0}/league-{1}/{2}/capture-{3}" -f
            $captureRootRelative,
            $runSpec.leagueId,
            $runSpec.leagueDate,
            $timestampToken

        $runFullPath = Join-Path $repoRoot (
            $runDirectory.Replace("/", "\")
        )

        if (-not (Test-RepositoryContainment `
            -RepositoryRoot $repoRoot `
            -CandidatePath $runFullPath)) {
            throw "Projected run directory is outside the repository."
        }

        if (Test-Path -LiteralPath $runFullPath) {
            throw "Projected run directory already exists."
        }

        [System.IO.Directory]::CreateDirectory($runFullPath) | Out-Null
        $initialDirectoriesCreated++

        $subdirectories = @(
            "responses/league"
            "responses/games"
            "responses/transactions"
            "responses/statistics"
            "responses/teams"
            "metadata"
        )

        foreach ($subdirectory in $subdirectories) {
            $subdirectoryPath = Join-Path $runFullPath (
                $subdirectory.Replace("/", "\")
            )

            [System.IO.Directory]::CreateDirectory(
                $subdirectoryPath
            ) | Out-Null

            $initialDirectoriesCreated++
        }

        $runSpecCopyPath = Join-Path $runFullPath "run-spec.json"
        $runSpecBytes = [System.IO.File]::ReadAllBytes(
            $resolvedRunSpecPath
        )

        [System.IO.File]::WriteAllBytes(
            $runSpecCopyPath,
            $runSpecBytes
        )

        $initialFilesCreated++

        $sourceRunSpecHash = (
            Get-FileHash `
                -LiteralPath $resolvedRunSpecPath `
                -Algorithm SHA256
        ).Hash

        $copiedRunSpecHash = (
            Get-FileHash `
                -LiteralPath $runSpecCopyPath `
                -Algorithm SHA256
        ).Hash

        if ($sourceRunSpecHash -ne $copiedRunSpecHash) {
            throw "Run-specification copy hash mismatch."
        }

        $harvesterHash = (
            Get-FileHash `
                -LiteralPath $PSCommandPath `
                -Algorithm SHA256
        ).Hash

        $manifestPath = Join-Path $runFullPath "run-manifest.json"

        $manifest = [ordered]@{
            schemaVersion = "strat365-league-capture-manifest-v0"
            runState = "initialized"
            captureTimestampUtc = $captureTimestampUtc.ToString("o")
            captureTimestampToken = $timestampToken
            runDirectory = $runDirectory
            leagueId = $runSpec.leagueId
            leagueDate = $runSpec.leagueDate
            playerSetYear = $runSpec.playerSetYear
            runSpecSource = Get-RepositoryRelativePath `
                -RepositoryRoot $repoRoot `
                -CandidatePath $resolvedRunSpecPath
            runSpecCopy = "$runDirectory/run-spec.json"
            runSpecSha256 = $sourceRunSpecHash
            harvesterScript = Get-RepositoryRelativePath `
                -RepositoryRoot $repoRoot `
                -CandidatePath $PSCommandPath
            harvesterSha256 = $harvesterHash
            plannedRequestCount = 0
            attemptedRequestCount = 0
            capturedResponseCount = 0
            failedRequestCount = 0
            httpRequestCount = 0
            canonicalPromotionEligibility = "NO"
            capturePlanFrozen = $false
            validation = [ordered]@{
                preflight = "PASS"
                repositoryContainment = "PASS"
                overwriteProtection = "PASS"
                runSpecCopyHash = "PASS"
            }
            provenance = [ordered]@{
                sourceContract = "docs/baseball/strat365-league-season-ingestion-source-contract-v0.md"
                harvesterDesign = "docs/baseball/strat365-manual-league-raw-capture-harvester-design-v0.md"
            }
            requests = @()
        }

        Write-Utf8NoBomJson `
            -Path $manifestPath `
            -Value $manifest

        $initialFilesCreated++

        $savedManifest = Get-Content `
            -LiteralPath $manifestPath `
            -Raw | ConvertFrom-Json -ErrorAction Stop

        if ($savedManifest.runState -ne "initialized" -or
            $savedManifest.httpRequestCount -ne 0 -or
            $savedManifest.runSpecSha256 -ne $sourceRunSpecHash -or
            $savedManifest.canonicalPromotionEligibility -ne "NO") {
            throw "Initial manifest validation failed."
        }

        $runInitialized = $true
        $manifestFile = "$runDirectory/run-manifest.json"
        $runSpecCopyFile = "$runDirectory/run-spec.json"
    }
    catch {
        $failures.Add("run_initialization_failed")
        $initializationError = $_.Exception.Message.
            Replace("`r", " ").
            Replace("`n", " ")
    }
}

$finalPass = $failures.Count -eq 0

Write-Host "`n# RESULT SUMMARY"
Write-Host "PREFLIGHT_MODE: PASS"
Write-Host "RUN_SPEC: $relativeRunSpec"
Write-Host "SCHEMA_VERSION: $(if ($runSpec) { $runSpec.schemaVersion } else { 'unavailable' })"
Write-Host "LEAGUE_ID: $(if ($runSpec) { $runSpec.leagueId } else { 'unavailable' })"
Write-Host "LEAGUE_DATE: $(if ($runSpec) { $runSpec.leagueDate } else { 'unavailable' })"
Write-Host "EXPECTED_COUNTS: $(if ($runSpec) { "teams=$($runSpec.expectedCounts.teamCount); games=$($runSpec.expectedCounts.gameCount); series=$($runSpec.expectedCounts.seriesCount)" } else { 'unavailable' })"
Write-Host "TEAM_ID_COUNT: $(if ($runSpec) { @($runSpec.teamIds).Count } else { 0 })"
Write-Host "SOURCE_FAMILY_COUNT: $(if ($runSpec) { @($runSpec.requiredSourceFamilies).Count } else { 0 })"
Write-Host "SCORES_URL: $scoresUrl"
Write-Host "PROJECTED_RUN_ROOT: $projectedRunRoot"
Write-Host "RUN_INITIALIZED: $(if ($runInitialized) { 'YES' } else { 'NO' })"
Write-Host "RUN_DIRECTORY: $runDirectory"
Write-Host "RUN_SPEC_COPY: $runSpecCopyFile"
Write-Host "MANIFEST_FILE: $manifestFile"
Write-Host "INITIAL_DIRECTORIES_CREATED: $initialDirectoriesCreated"
Write-Host "INITIAL_FILES_CREATED: $initialFilesCreated"
Write-Host "RUN_INITIALIZATION_ERROR: $initializationError"
Write-Host "PREFLIGHT_FAILURES: $(if ($failures.Count) { $failures -join ', ' } else { 'none' })"
Write-Host "PREFLIGHT_VALIDATION: $(if ($finalPass) { 'PASS' } else { 'FAIL' })"
Write-Host "HTTP_REQUESTS_EXECUTED: 0"
Write-Host "NEXT_ACTION: $(if ($runInitialized) { 'Implement scores capture as a separate validated helper.' } else { 'Run with -InitializeRun to create the immutable run model.' })"

if ($finalPass) {
    exit 0
}

exit 4
