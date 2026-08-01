[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$RunDirectory,

    [ValidateRange(1, 54)]
    [int]$MaxRequests = 3,

    [switch]$DryRun,

    [switch]$Live,

    [ValidateRange(1, 300)]
    [int]$RequestTimeoutSeconds = 60,

    [Parameter(Mandatory = $true)]
    [ValidatePattern("^[A-Fa-f0-9]{64}$")]
    [string]$ExpectedFrozenPlanSha256

)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ExpectedTransportSha256 =
    "F139D1457598489F989EDBE8EF5503C617C8CB8E5A6EF4D67BF56FD413439133"

$script:ObservedHttpRequests = 0

function Get-Field {
    param(
        [AllowNull()]
        [object]$InputObject,

        [Parameter(Mandatory = $true)]
        [string]$Name
    )

    if ($null -eq $InputObject) {
        return $null
    }

    $property = $InputObject.PSObject.Properties[$Name]

    if ($null -eq $property) {
        return $null
    }

    return $property.Value
}

function Set-Field {
    param(
        [Parameter(Mandatory = $true)]
        [object]$InputObject,

        [Parameter(Mandatory = $true)]
        [string]$Name,

        [AllowNull()]
        [object]$Value
    )

    $property = $InputObject.PSObject.Properties[$Name]

    if ($null -eq $property) {
        Add-Member `
            -InputObject $InputObject `
            -MemberType NoteProperty `
            -Name $Name `
            -Value $Value
    }
    else {
        $property.Value = $Value
    }
}

function ConvertTo-ComparableJson {
    param([AllowNull()][object]$Value)

    if ($null -eq $Value) {
        return "null"
    }

    return $Value | ConvertTo-Json -Depth 100 -Compress
}

function Test-PathContained {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ParentPath,

        [Parameter(Mandatory = $true)]
        [string]$ChildPath
    )

    $parent = [System.IO.Path]::GetFullPath($ParentPath).
        TrimEnd(
            [System.IO.Path]::DirectorySeparatorChar,
            [System.IO.Path]::AltDirectorySeparatorChar
        ) + [System.IO.Path]::DirectorySeparatorChar

    $child = [System.IO.Path]::GetFullPath($ChildPath)

    return $child.StartsWith(
        $parent,
        [System.StringComparison]::OrdinalIgnoreCase
    )
}

function Resolve-StoredPath {
    param(
        [Parameter(Mandatory = $true)]
        [string]$StoredPath
    )

    if ([string]::IsNullOrWhiteSpace($StoredPath)) {
        throw "Stored artifact path is empty."
    }

    $fullPath = if ([System.IO.Path]::IsPathRooted($StoredPath)) {
        [System.IO.Path]::GetFullPath($StoredPath)
    }
    else {
        [System.IO.Path]::GetFullPath(
            (Join-Path $script:RepoRoot $StoredPath)
        )
    }

    if (-not (Test-PathContained -ParentPath $script:RunPath -ChildPath $fullPath)) {
        throw "Artifact path escapes the authoritative run: $StoredPath"
    }

    return $fullPath
}

function Get-RepositoryRelativePath {
    param(
        [Parameter(Mandatory = $true)]
        [string]$FullPath
    )

    $resolved = [System.IO.Path]::GetFullPath($FullPath)

    if (-not (Test-PathContained -ParentPath $script:RepoRoot -ChildPath $resolved)) {
        throw "Path is outside repository: $resolved"
    }

    return $resolved.
        Substring($script:RepoRoot.Length).
        TrimStart(
            [System.IO.Path]::DirectorySeparatorChar,
            [System.IO.Path]::AltDirectorySeparatorChar
        ).
        Replace("\", "/")
}

function Read-JsonFile {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    return Get-Content `
        -LiteralPath $Path `
        -Raw `
        -Encoding UTF8 |
            ConvertFrom-Json
}

function Save-ManifestAtomic {
    param(
        [Parameter(Mandatory = $true)]
        [object]$Manifest
    )

    if ([string](Get-Field $Manifest "canonicalPromotionEligibility") -ne "NO") {
        throw "Manifest canonical promotion eligibility changed."
    }

    $temporaryManifest = Join-Path $script:RunPath `
        "run-manifest.write-$PID-$([guid]::NewGuid().ToString('N')).tmp"

    $replacementBackup = Join-Path $script:RunPath `
        "run-manifest.replace-backup-$PID-$([guid]::NewGuid().ToString('N')).tmp"

    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)

    try {
        $json = $Manifest | ConvertTo-Json -Depth 100

        [System.IO.File]::WriteAllText(
            $temporaryManifest,
            $json + [Environment]::NewLine,
            $utf8NoBom
        )

        $validated = Read-JsonFile -Path $temporaryManifest

        if ([string](Get-Field $validated "canonicalPromotionEligibility") -ne "NO") {
            throw "Temporary manifest validation failed."
        }

        $replaceSucceeded = $false
        $lastReplaceError = $null

        for ($replaceAttempt = 1; $replaceAttempt -le 8; $replaceAttempt++) {
            try {
                [System.IO.File]::Replace(
                    $temporaryManifest,
                    $script:ManifestPath,
                    $replacementBackup,
                    $true
                )

                $replaceSucceeded = $true
                break
            }
            catch {
                $replaceException = $_.Exception

                $rootReplaceException = if ($null -ne $replaceException.InnerException) {
                    $replaceException.InnerException
                }
                else {
                    $replaceException
                }

                $retryableReplaceError = (
                    $rootReplaceException -is [System.IO.IOException] -or
                    $rootReplaceException -is [System.UnauthorizedAccessException]
                )

                if (-not $retryableReplaceError) {
                    throw
                }

                $lastReplaceError = $rootReplaceException

                if ($replaceAttempt -ge 8) {
                    break
                }

                [System.GC]::Collect()
                [System.GC]::WaitForPendingFinalizers()

                $replaceDelayMilliseconds = [int][Math]::Min(
                    2000,
                    125 * [Math]::Pow(2, $replaceAttempt - 1)
                )

                Start-Sleep -Milliseconds $replaceDelayMilliseconds
            }
        }

        if (-not $replaceSucceeded) {
            throw "Atomic manifest replacement failed after 8 attempts: $($lastReplaceError.Message)"
        }

        if (Test-Path -LiteralPath $replacementBackup) {
            Remove-Item -LiteralPath $replacementBackup -Force
        }
    }
    finally {
        if (Test-Path -LiteralPath $temporaryManifest) {
            Remove-Item -LiteralPath $temporaryManifest -Force
        }

        if (Test-Path -LiteralPath $replacementBackup) {
            Remove-Item -LiteralPath $replacementBackup -Force
        }
    }
}

function Update-GameExecutionAggregates {
    param(
        [Parameter(Mandatory = $true)]
        [object]$Manifest
    )

    $gameRows = @(
        @($Manifest.requests) | Where-Object {
            $requestId = [string](Get-Field $_ "requestId")
            $requestId -match '^game-\d+-(recap|play-by-play|replay)$'
        }
    )

    $capturedRows = @(
        $gameRows | Where-Object {
            [string](Get-Field $_ "requestStatus") -eq "captured"
        }
    )

    $plannedRows = @(
        $gameRows | Where-Object {
            [string](Get-Field $_ "requestStatus") -eq "planned"
        }
    )

    $failedRows = @(
        $gameRows | Where-Object {
            [string](Get-Field $_ "requestStatus") -eq "failed"
        }
    )

    $completedGameIds = @()

    $gameIds = @(
        $gameRows |
            ForEach-Object {
                [int](Get-Field $_ "gameId")
            } |
            Sort-Object -Unique
    )

    foreach ($gameId in $gameIds) {
        $rowsForGame = @(
            $gameRows | Where-Object {
                [int](Get-Field $_ "gameId") -eq $gameId
            }
        )

        $nonCaptured = @(
            $rowsForGame | Where-Object {
                [string](Get-Field $_ "requestStatus") -ne "captured"
            }
        )

        if (
            $rowsForGame.Count -eq 3 -and
            $nonCaptured.Count -eq 0
        ) {
            $completedGameIds += $gameId
        }
    }

    $lastCompletedGameId = if ($completedGameIds.Count -gt 0) {
        ($completedGameIds | Measure-Object -Maximum).Maximum
    }
    else {
        $null
    }

    $execution = Get-Field $Manifest "gameCaptureExecution"

    Set-Field $execution "capturedGameRequestCount" $capturedRows.Count
    Set-Field $execution "pendingGameRequestCount" $plannedRows.Count
    Set-Field $execution "failedGameRequestCount" $failedRows.Count
    Set-Field $execution "lastCompletedGameId" $lastCompletedGameId
    Set-Field $execution "executionLedger" "run-manifest.json requests"
    Set-Field $execution "frozenPlanImmutable" $true
    Set-Field $execution "planMutationAllowed" $false

    Set-Field $Manifest "canonicalPromotionEligibility" "NO"
}

function Get-TransportValue {
    param(
        [Parameter(Mandatory = $true)]
        [AllowEmptyString()]
        [AllowEmptyCollection()]
        [string[]]$Lines,

        [Parameter(Mandatory = $true)]
        [string]$Key
    )

    for ($index = $Lines.Count - 1; $index -ge 0; $index--) {
        $text = [string]$Lines[$index]

        if ($text -match ("^" + [regex]::Escape($Key) + ":\s*(.*)$")) {
            return $Matches[1].Trim()
        }
    }

    return $null
}

function Test-ManifestConsistency {
    param(
        [Parameter(Mandatory = $true)]
        [object]$Plan,

        [Parameter(Mandatory = $true)]
        [object]$Manifest,

        [switch]$ValidateArtifacts,

        [AllowNull()]
        [string]$AllowedInProgressRequestId
    )

    $planRequests = @($Plan.requests)
    $manifestRequests = @($Manifest.requests)

    $plannedRequestCountValue = Get-Field $Plan "plannedRequestCount"

    if ($null -eq $plannedRequestCountValue) {
        throw "Frozen plan plannedRequestCount is missing."
    }

    $expectedPlanRequestCount = [int]$plannedRequestCountValue

    if ($expectedPlanRequestCount -le 0) {
        throw "Frozen plan plannedRequestCount must be greater than zero."
    }

    if ($planRequests.Count -ne $expectedPlanRequestCount) {
        throw "Frozen plan request count does not match plannedRequestCount."
    }

    $expectedManifestRequestCount = $expectedPlanRequestCount + 1

    if ($manifestRequests.Count -ne $expectedManifestRequestCount) {
        throw "Manifest request count does not match frozen plan plus source-discovery request."
    }

    if ([string](Get-Field $Plan "planState") -ne "frozen") {
        throw "Capture plan is not frozen."
    }

    if ([string](Get-Field $Plan "canonicalPromotionEligibility") -ne "NO") {
        throw "Frozen plan permits canonical promotion."
    }

    if ([string](Get-Field $Manifest "canonicalPromotionEligibility") -ne "NO") {
        throw "Manifest permits canonical promotion."
    }

    $recordedPlanHash = [string](
        Get-Field (Get-Field $Manifest "gameCapturePlan") "planSha256"
    )

    if ($recordedPlanHash.ToUpperInvariant() -ne $ExpectedFrozenPlanSha256) {
        throw "Manifest records an unauthorized frozen-plan hash."
    }

    $planById = @{}
    $ledgerById = @{}
    $scoresRows = @()

    foreach ($planRequest in $planRequests) {
        $requestId = [string](Get-Field $planRequest "requestId")

        if ([string]::IsNullOrWhiteSpace($requestId)) {
            throw "Frozen plan contains a request without requestId."
        }

        if ($planById.ContainsKey($requestId)) {
            throw "Duplicate frozen-plan requestId: $requestId"
        }

        if ([string](Get-Field $planRequest "planStatus") -ne "planned") {
            throw "Frozen-plan planStatus changed for $requestId."
        }

        if ([int](Get-Field $planRequest "attemptCount") -ne 0) {
            throw "Frozen plan contains execution state for $requestId."
        }

        $planById[$requestId] = $planRequest
    }

    foreach ($ledgerRequest in $manifestRequests) {
        $requestId = [string](Get-Field $ledgerRequest "requestId")

        if ([string]::IsNullOrWhiteSpace($requestId)) {
            $scoresRows += $ledgerRequest
            continue
        }

        if ($ledgerById.ContainsKey($requestId)) {
            throw "Duplicate manifest requestId: $requestId"
        }

        $ledgerById[$requestId] = $ledgerRequest
    }

    if ($scoresRows.Count -ne 1) {
        throw "Manifest must contain exactly one scores ledger row."
    }

    $scoresRow = $scoresRows[0]

    if (
        [string](Get-Field $scoresRow "sourceFamily") -ne "leagueScores" -or
        [string](Get-Field $scoresRow "requestStatus") -ne "captured" -or
        [int](Get-Field $scoresRow "attemptNumber") -ne 1
    ) {
        throw "Scores ledger row is inconsistent."
    }

    $correlationFields = @(
        "requestedUrl",
        "rawResponsePath",
        "responseHeadersPath",
        "metadataPath",
        "sourceFamily",
        "gameId",
        "leagueId",
        "leagueDate",
        "seriesKey",
        "required",
        "teamIds"
    )

    $artifactPaths = @()
    $plannedRows = @()
    $capturedRows = @()
    $failedRows = @()
    $inProgressRows = @()
    $derivedAttemptedCount = 1

    foreach ($planRequest in $planRequests) {
        $requestId = [string](Get-Field $planRequest "requestId")

        if (-not $ledgerById.ContainsKey($requestId)) {
            throw "Plan request missing from manifest: $requestId"
        }

        $ledgerRequest = $ledgerById[$requestId]

        foreach ($fieldName in $correlationFields) {
            $planValue = Get-Field $planRequest $fieldName
            $ledgerValue = Get-Field $ledgerRequest $fieldName

            if (
                (ConvertTo-ComparableJson $planValue) -ne
                (ConvertTo-ComparableJson $ledgerValue)
            ) {
                throw "Plan/manifest mismatch: $requestId field $fieldName."
            }
        }

        $status = [string](Get-Field $ledgerRequest "requestStatus")
        $attemptCountValue = Get-Field $ledgerRequest "attemptCount"

        if ($null -eq $attemptCountValue) {
            throw "Manifest attemptCount missing for $requestId."
        }

        $attemptCount = [int]$attemptCountValue

        if ($attemptCount -gt 0) {
            $derivedAttemptedCount++
        }

        switch ($status) {
            "planned" {
                if ($attemptCount -ne 0) {
                    throw "Planned request has nonzero attempts: $requestId"
                }

                $plannedRows += $ledgerRequest
            }

            "captured" {
                if ($attemptCount -ne 1) {
                    throw "Captured request has invalid attempts: $requestId"
                }

                $capturedRows += $ledgerRequest
            }

            "failed" {
                $failedRows += $ledgerRequest
            }

            "in_progress" {
                $inProgressRows += $ledgerRequest
            }

            default {
                throw "Unexpected requestStatus '$status' for $requestId."
            }
        }

        foreach ($fieldName in @(
            "rawResponsePath",
            "responseHeadersPath",
            "metadataPath"
        )) {
            $storedPath = [string](Get-Field $ledgerRequest $fieldName)
            $fullPath = Resolve-StoredPath -StoredPath $storedPath
            $artifactPaths += $fullPath
        }

        if ($ValidateArtifacts) {
            $bodyPath = Resolve-StoredPath `
                -StoredPath ([string](Get-Field $ledgerRequest "rawResponsePath"))

            $headersPath = Resolve-StoredPath `
                -StoredPath ([string](Get-Field $ledgerRequest "responseHeadersPath"))

            $metadataPath = Resolve-StoredPath `
                -StoredPath ([string](Get-Field $ledgerRequest "metadataPath"))

            if ($status -eq "captured") {
                foreach ($requiredArtifact in @(
                    $bodyPath,
                    $headersPath,
                    $metadataPath
                )) {
                    if (-not (Test-Path -LiteralPath $requiredArtifact -PathType Leaf)) {
                        throw "Captured artifact missing for $requestId."
                    }
                }

                $actualHash = (
                    Get-FileHash -LiteralPath $bodyPath -Algorithm SHA256
                ).Hash.ToUpperInvariant()

                $ledgerHash = [string](Get-Field $ledgerRequest "sha256")

                if ($actualHash -ne $ledgerHash.ToUpperInvariant()) {
                    throw "Captured body hash mismatch for $requestId."
                }
            }

            if ($status -eq "planned") {
                foreach ($plannedArtifact in @(
                    $bodyPath,
                    $headersPath,
                    $metadataPath
                )) {
                    if (Test-Path -LiteralPath $plannedArtifact) {
                        throw "Overwrite risk for planned request $requestId."
                    }
                }
            }
        }
    }

    $duplicateArtifactPaths = @(
        $artifactPaths |
            Group-Object |
            Where-Object { $_.Count -gt 1 }
    )

    if ($duplicateArtifactPaths.Count -gt 0) {
        throw "Duplicate artifact paths exist in the request plan."
    }

    if ($failedRows.Count -gt 0) {
        throw "Manifest contains failed requests; manual review is required."
    }

    if ($inProgressRows.Count -gt 0) {
        $authorizedInProgressState = (
            -not [string]::IsNullOrWhiteSpace($AllowedInProgressRequestId) -and
            $inProgressRows.Count -eq 1 -and
            [string](Get-Field $inProgressRows[0] "requestId") -eq
                $AllowedInProgressRequestId
        )

        if (-not $authorizedInProgressState) {
            throw "Manifest contains an unauthorized in-progress request."
        }
    }

    $allCapturedRows = @(
        $manifestRequests | Where-Object {
            [string](Get-Field $_ "requestStatus") -eq "captured"
        }
    )

    $allFailedRows = @(
        $manifestRequests | Where-Object {
            [string](Get-Field $_ "requestStatus") -eq "failed"
        }
    )

    if (
        [int](Get-Field $Manifest "attemptedRequestCount") -ne
            $derivedAttemptedCount
    ) {
        throw "Manifest attemptedRequestCount is inconsistent."
    }

    if (
        [int](Get-Field $Manifest "capturedResponseCount") -ne
            $allCapturedRows.Count
    ) {
        throw "Manifest capturedResponseCount is inconsistent."
    }

    if (
        [int](Get-Field $Manifest "failedRequestCount") -ne
            $allFailedRows.Count
    ) {
        throw "Manifest failedRequestCount is inconsistent."
    }

    $expectedPersistedHttpRequestCount =
        $derivedAttemptedCount - $inProgressRows.Count

    if (
        [int](Get-Field $Manifest "httpRequestCount") -ne
            $expectedPersistedHttpRequestCount
    ) {
        throw "Manifest persisted HTTP request count is inconsistent."
    }

    $execution = Get-Field $Manifest "gameCaptureExecution"

    if (
        [int](Get-Field $execution "capturedGameRequestCount") -ne
            $capturedRows.Count -or
        [int](Get-Field $execution "pendingGameRequestCount") -ne
            $plannedRows.Count -or
        [int](Get-Field $execution "failedGameRequestCount") -ne
            $failedRows.Count -or
        [string](Get-Field $execution "executionLedger") -ne
            "run-manifest.json requests" -or
        [bool](Get-Field $execution "frozenPlanImmutable") -ne $true -or
        [bool](Get-Field $execution "planMutationAllowed") -ne $false
    ) {
        throw "Manifest gameCaptureExecution is inconsistent."
    }

    return [pscustomobject]@{
        PlanById      = $planById
        LedgerById    = $ledgerById
        PlannedRows   = @($plannedRows)
        CapturedRows  = @($capturedRows)
        FailedRows    = @($failedRows)
        InProgressRows = @($inProgressRows)
    }
}

try {
    if (
        ($DryRun -and $Live) -or
        (-not $DryRun -and -not $Live)
    ) {
        throw "Specify exactly one execution mode: -DryRun or -Live."
    }

    $script:RepoRoot = [System.IO.Path]::GetFullPath(
        (Split-Path -Parent (Split-Path -Parent $PSScriptRoot))
    )

    $script:RunPath = if (
        [System.IO.Path]::IsPathRooted($RunDirectory)
    ) {
        [System.IO.Path]::GetFullPath($RunDirectory)
    }
    else {
        [System.IO.Path]::GetFullPath(
            (Join-Path $script:RepoRoot $RunDirectory)
        )
    }

    if (-not (Test-PathContained -ParentPath $script:RepoRoot -ChildPath $script:RunPath)) {
        throw "Run directory is outside the repository."
    }

    if (-not (Test-Path -LiteralPath $script:RunPath -PathType Container)) {
        throw "Run directory does not exist."
    }

    $script:PlanPath = Join-Path $script:RunPath "game-capture-plan.json"
    $script:ManifestPath = Join-Path $script:RunPath "run-manifest.json"

    $transportPath = Join-Path $script:RepoRoot `
        "baseball/harvester/invoke_strat365_raw_get_v0.ps1"

    foreach ($requiredPath in @(
        $script:PlanPath,
        $script:ManifestPath,
        $transportPath
    )) {
        if (-not (Test-Path -LiteralPath $requiredPath -PathType Leaf)) {
            throw "Required file is missing: $requiredPath"
        }
    }

    $planHash = (
        Get-FileHash -LiteralPath $script:PlanPath -Algorithm SHA256
    ).Hash.ToUpperInvariant()

    if ($planHash -ne $ExpectedFrozenPlanSha256) {
        throw "Frozen-plan SHA-256 mismatch."
    }

    $transportHash = (
        Get-FileHash -LiteralPath $transportPath -Algorithm SHA256
    ).Hash.ToUpperInvariant()

    if ($transportHash -ne $ExpectedTransportSha256) {
        throw "Transport-helper SHA-256 mismatch."
    }

    $plan = Read-JsonFile -Path $script:PlanPath
    $manifest = Read-JsonFile -Path $script:ManifestPath

    $state = Test-ManifestConsistency `
        -Plan $plan `
        -Manifest $manifest `
        -ValidateArtifacts

    $selected = @()

    foreach ($planRequest in @($plan.requests)) {
        $requestId = [string](Get-Field $planRequest "requestId")
        $ledgerRequest = $state.LedgerById[$requestId]

        if (
            [string](Get-Field $ledgerRequest "requestStatus") -eq "planned" -and
            [int](Get-Field $ledgerRequest "attemptCount") -eq 0
        ) {
            $selected += [pscustomobject]@{
                Plan   = $planRequest
                Ledger = $ledgerRequest
            }
        }

        if ($selected.Count -eq $MaxRequests) {
            break
        }
    }

    if ($selected.Count -eq 0) {
        throw "No eligible planned requests remain."
    }

    Write-Host "`n# RESULT SUMMARY"
    Write-Host "EXECUTOR_MODE: $(if ($DryRun) { 'DRY_RUN' } else { 'LIVE' })"
    Write-Host "RUN_DIRECTORY: $(Get-RepositoryRelativePath $script:RunPath)"
    Write-Host "PLAN_HASH_MATCH: PASS"
    Write-Host "TRANSPORT_HASH_MATCH: PASS"
    Write-Host "CAPTURED_GAME_REQUEST_COUNT: $($state.CapturedRows.Count)"
    Write-Host "PENDING_GAME_REQUEST_COUNT: $($state.PlannedRows.Count)"
    Write-Host "SELECTED_REQUEST_COUNT: $($selected.Count)"

    foreach ($selection in $selected) {
        $request = $selection.Ledger

        Write-Host (
            "SELECTED_REQUEST: " +
            [string](Get-Field $request "requestId")
        )
    }

    if ($DryRun) {
        Write-Host "HTTP_REQUESTS_EXECUTED: 0"
        Write-Host "FILES_MODIFIED: 0"
        Write-Host "CANONICAL_PROMOTION_ELIGIBILITY: NO"
        Write-Host "EXECUTOR_VALIDATION: PASS"
        exit 0
    }

    $shellExecutable = (Get-Process -Id $PID).Path
    $batchHttpRequests = 0
    $capturedThisBatch = 0

    foreach ($selection in $selected) {
        $requestId = [string](Get-Field $selection.Plan "requestId")

        $currentPlanHash = (
            Get-FileHash -LiteralPath $script:PlanPath -Algorithm SHA256
        ).Hash.ToUpperInvariant()

        if ($currentPlanHash -ne $ExpectedFrozenPlanSha256) {
            throw "Frozen-plan hash changed before $requestId."
        }

        $currentManifest = Read-JsonFile -Path $script:ManifestPath

        $currentState = Test-ManifestConsistency `
            -Plan $plan `
            -Manifest $currentManifest `
            -ValidateArtifacts

        if (-not $currentState.LedgerById.ContainsKey($requestId)) {
            throw "Selected request disappeared from ledger: $requestId"
        }

        $ledgerRequest = $currentState.LedgerById[$requestId]

        if (
            [string](Get-Field $ledgerRequest "requestStatus") -ne "planned" -or
            [int](Get-Field $ledgerRequest "attemptCount") -ne 0
        ) {
            throw "Duplicate or inconsistent execution state for $requestId."
        }

        $bodyFinal = Resolve-StoredPath `
            -StoredPath ([string](Get-Field $ledgerRequest "rawResponsePath"))

        $headersFinal = Resolve-StoredPath `
            -StoredPath ([string](Get-Field $ledgerRequest "responseHeadersPath"))

        $metadataFinal = Resolve-StoredPath `
            -StoredPath ([string](Get-Field $ledgerRequest "metadataPath"))

        foreach ($finalPath in @(
            $bodyFinal,
            $headersFinal,
            $metadataFinal
        )) {
            if (Test-Path -LiteralPath $finalPath) {
                throw "Overwrite risk detected for $requestId."
            }
        }

        Set-Field $ledgerRequest "requestStatus" "in_progress"
        Set-Field $ledgerRequest "attemptCount" 1
        Set-Field $ledgerRequest "attemptNumber" 1

        Set-Field `
            $currentManifest `
            "attemptedRequestCount" `
            ([int](Get-Field $currentManifest "attemptedRequestCount") + 1)

        Update-GameExecutionAggregates -Manifest $currentManifest
        Save-ManifestAtomic -Manifest $currentManifest

        $workDirectory = Join-Path `
            ([System.IO.Path]::GetTempPath()) `
            "strat365-$PID-$requestId-$([guid]::NewGuid().ToString('N'))"

        New-Item `
            -ItemType Directory `
            -Path $workDirectory `
            -ErrorAction Stop |
                Out-Null

        $bodyTemporary = Join-Path $workDirectory "body.tmp"
        $headersTemporary = Join-Path $workDirectory "headers.tmp"
        $metadataTemporary = Join-Path $workDirectory "metadata.tmp"

        $transportLines = @(
            & $shellExecutable `
                -NoProfile `
                -ExecutionPolicy Bypass `
                -File $transportPath `
                -RequestedUrl ([string](Get-Field $ledgerRequest "requestedUrl")) `
                -BodyPath $bodyTemporary `
                -HeadersPath $headersTemporary `
                -RequestTimeoutSeconds $RequestTimeoutSeconds `
                2>&1 |
                    ForEach-Object { $_.ToString() }
        )

        $helperExitCode = $LASTEXITCODE

        $httpRequestsExecutedText = Get-TransportValue `
            -Lines $transportLines `
            -Key "HTTP_REQUESTS_EXECUTED"

        $httpRequestsExecuted = 0

        if (
            -not [string]::IsNullOrWhiteSpace($httpRequestsExecutedText)
        ) {
            [void][int]::TryParse(
                $httpRequestsExecutedText,
                [ref]$httpRequestsExecuted
            )
        }

        $batchHttpRequests += $httpRequestsExecuted
        $script:ObservedHttpRequests += $httpRequestsExecuted

        $httpStatusText = Get-TransportValue `
            -Lines $transportLines `
            -Key "HTTP_STATUS"

        $effectiveUrl = Get-TransportValue `
            -Lines $transportLines `
            -Key "EFFECTIVE_URL"

        $contentType = Get-TransportValue `
            -Lines $transportLines `
            -Key "CONTENT_TYPE"

        $byteCountText = Get-TransportValue `
            -Lines $transportLines `
            -Key "BYTE_COUNT"

        $helperSha256 = Get-TransportValue `
            -Lines $transportLines `
            -Key "SHA256"

        $transportValidation = Get-TransportValue `
            -Lines $transportLines `
            -Key "TRANSPORT_VALIDATION"

        $httpStatus = 0
        [void][int]::TryParse(
            [string]$httpStatusText,
            [ref]$httpStatus
        )

        [long]$byteCount = 0
        [void][long]::TryParse(
            [string]$byteCountText,
            [ref]$byteCount
        )

        $failureReasons = New-Object `
            System.Collections.Generic.List[string]

        if ($helperExitCode -ne 0) {
            $failureReasons.Add("transport_helper_failed")
        }

        if ($transportValidation -ne "PASS") {
            $failureReasons.Add("transport_validation_failed")
        }

        if ($httpRequestsExecuted -ne 1) {
            $failureReasons.Add("unexpected_http_execution_count")
        }

        if ($httpStatus -ne 200) {
            $failureReasons.Add("unexpected_http_status")
        }

        if (
            [string]$effectiveUrl -ne
            [string](Get-Field $ledgerRequest "requestedUrl")
        ) {
            $failureReasons.Add("effective_url_mismatch")
        }

        if (
            [string]::IsNullOrWhiteSpace($contentType) -or
            $contentType -notmatch '^text/html'
        ) {
            $failureReasons.Add("content_type_invalid")
        }

        if (
            -not (Test-Path -LiteralPath $bodyTemporary -PathType Leaf) -or
            -not (Test-Path -LiteralPath $headersTemporary -PathType Leaf)
        ) {
            $failureReasons.Add("transport_artifact_missing")
        }

        $bodyHash = $null
        $bodyText = ""
        $headerText = ""

        if (Test-Path -LiteralPath $bodyTemporary -PathType Leaf) {
            $bodyHash = (
                Get-FileHash -LiteralPath $bodyTemporary -Algorithm SHA256
            ).Hash.ToUpperInvariant()

            $bodyText = Get-Content `
                -LiteralPath $bodyTemporary `
                -Raw `
                -Encoding UTF8

            if ($bodyHash -ne ([string]$helperSha256).ToUpperInvariant()) {
                $failureReasons.Add("raw_body_hash_mismatch")
            }

            if ((Get-Item -LiteralPath $bodyTemporary).Length -ne $byteCount) {
                $failureReasons.Add("raw_body_byte_count_mismatch")
            }
        }

        if (Test-Path -LiteralPath $headersTemporary -PathType Leaf) {
            $headerText = Get-Content `
                -LiteralPath $headersTemporary `
                -Raw `
                -Encoding UTF8
        }

        $httpBlocks = @(
            [regex]::Matches(
                $headerText,
                '(?im)^HTTP/\S+\s+\d{3}[^\r\n]*'
            )
        )

        $locationHeaders = @(
            [regex]::Matches(
                $headerText,
                '(?im)^Location:\s*[^\r\n]+'
            )
        )

        if (
            $httpBlocks.Count -ne 1 -or
            $locationHeaders.Count -ne 0
        ) {
            $failureReasons.Add("unexpected_redirect_or_header_chain")
        }

        $title = ""

        if ($bodyText -match '(?is)<title[^>]*>\s*(.*?)\s*</title>') {
            $title = ($Matches[1] -replace '\s+', ' ').Trim()
        }

        $tableCount = @(
            [regex]::Matches(
                $bodyText,
                '(?i)<table\b'
            )
        ).Count

        $topInningMarkerCount = @(
            [regex]::Matches(
                $bodyText,
                '(?i)\bTop\b'
            )
        ).Count

        $bottomInningMarkerCount = @(
            [regex]::Matches(
                $bodyText,
                '(?i)\bBottom\b'
            )
        ).Count

        $replayMarkerPresent = (
            $bodyText -match '(?i)\breplay\b'
        )

        $teamIds = @(
            Get-Field $ledgerRequest "teamIds" |
                ForEach-Object { [string]$_ }
        )

        $missingTeamIds = @(
            $teamIds | Where-Object {
                $bodyText.IndexOf(
                    $_,
                    [System.StringComparison]::OrdinalIgnoreCase
                ) -lt 0
            }
        )

        $semanticValidation = (
            $tableCount -gt 0 -and
            $topInningMarkerCount -gt 0 -and
            $bottomInningMarkerCount -gt 0 -and
            $replayMarkerPresent
        )

        $sourceValidation = (
            $failureReasons.Count -eq 0 -and
            $title -eq "365 by Strat-O-Matic" -and
            $missingTeamIds.Count -eq 0
        )

        if (-not $semanticValidation) {
            $failureReasons.Add("semantic_validation_failed")
        }

        if (-not $sourceValidation) {
            $failureReasons.Add("source_validation_failed")
        }

        if ($failureReasons.Count -gt 0) {
            $failedManifest = Read-JsonFile -Path $script:ManifestPath
            $failedState = Test-ManifestConsistency `
                -Plan $plan `
                -Manifest $failedManifest `
                -AllowedInProgressRequestId $requestId

            $failedRow = $failedState.LedgerById[$requestId]

            if (
                [string](Get-Field $failedRow "requestStatus") -ne "in_progress" -or
                [int](Get-Field $failedRow "attemptCount") -ne 1
            ) {
                throw "Failed request ledger state changed unexpectedly."
            }

            Set-Field $failedRow "requestStatus" "failed"
            Set-Field $failedRow "httpStatus" $httpStatus
            Set-Field $failedRow "effectiveUrl" $effectiveUrl
            Set-Field $failedRow "byteCount" $byteCount
            Set-Field $failedRow "sha256" $helperSha256

            Set-Field `
                $failedManifest `
                "httpRequestCount" `
                ([int](Get-Field $failedManifest "httpRequestCount") +
                    $httpRequestsExecuted)

            Set-Field `
                $failedManifest `
                "failedRequestCount" `
                ([int](Get-Field $failedManifest "failedRequestCount") + 1)

            Update-GameExecutionAggregates -Manifest $failedManifest
            Save-ManifestAtomic -Manifest $failedManifest

            Remove-Item `
                -LiteralPath $workDirectory `
                -Recurse `
                -Force `
                -ErrorAction SilentlyContinue

            Write-Host "`n# RESULT SUMMARY"
            Write-Host "EXECUTOR_MODE: LIVE"
            Write-Host "FAILED_REQUEST: $requestId"
            Write-Host "FAILURE_REASONS: $($failureReasons -join ', ')"
            Write-Host "HTTP_REQUESTS_EXECUTED: $batchHttpRequests"
            Write-Host "CANONICAL_PROMOTION_ELIGIBILITY: NO"
            Write-Host "EXECUTOR_VALIDATION: FAIL"
            exit 3
        }

        $capturedAtUtc = [DateTime]::UtcNow.ToString("o")

        $metadata = [ordered]@{
            schemaVersion = "strat365-raw-response-metadata-v0"
            sourceFamily = [string](Get-Field $ledgerRequest "sourceFamily")
            sourceRouteClassification = $requestId
            requestedUrl = [string](Get-Field $ledgerRequest "requestedUrl")
            effectiveUrl = $effectiveUrl
            leagueId = [string](Get-Field $ledgerRequest "leagueId")
            leagueDate = [string](Get-Field $ledgerRequest "leagueDate")
            teamIds = $teamIds
            gameId = [string](Get-Field $ledgerRequest "gameId")
            seriesKey = [string](Get-Field $ledgerRequest "seriesKey")
            attemptNumber = 1
            capturedAtUtc = $capturedAtUtc
            httpStatus = $httpStatus
            contentType = $contentType
            byteCount = $byteCount
            sha256 = $bodyHash
            rawResponsePath = [string](Get-Field $ledgerRequest "rawResponsePath")
            responseHeadersPath = [string](Get-Field $ledgerRequest "responseHeadersPath")
            transportResult = "PASS"
            validation = [ordered]@{
                helperExitCode = $helperExitCode
                rawBodyPresent = $true
                responseHeadersPresent = $true
                rawBodyHashMatch = $true
                effectiveRouteMatch = $true
                tableCount = $tableCount
                topInningMarkerCount = $topInningMarkerCount
                bottomInningMarkerCount = $bottomInningMarkerCount
                replayMarkerPresent = $replayMarkerPresent
                semanticValidation = "PASS"
                sourceValidation = "PASS"
            }
            provenance = [ordered]@{
                runManifest = Get-RepositoryRelativePath $script:ManifestPath
                runSpec = (
                    Get-RepositoryRelativePath (
                        Join-Path $script:RunPath "run-spec.json"
                    )
                )
                gameCapturePlan = Get-RepositoryRelativePath $script:PlanPath
                transportHelper = Get-RepositoryRelativePath $transportPath
                governingContract =
                    "docs/baseball/strat365-league-season-ingestion-source-contract-v0.md"
            }
        }

        $utf8NoBom = New-Object System.Text.UTF8Encoding($false)

        [System.IO.File]::WriteAllText(
            $metadataTemporary,
            ($metadata | ConvertTo-Json -Depth 30) +
                [Environment]::NewLine,
            $utf8NoBom
        )

        [void](Read-JsonFile -Path $metadataTemporary)

        foreach ($finalPath in @(
            $bodyFinal,
            $headersFinal,
            $metadataFinal
        )) {
            if (Test-Path -LiteralPath $finalPath) {
                throw "Overwrite risk appeared during capture: $requestId"
            }

            $parent = Split-Path -Parent $finalPath

            if (-not (Test-Path -LiteralPath $parent -PathType Container)) {
                New-Item `
                    -ItemType Directory `
                    -Path $parent `
                    -Force |
                        Out-Null
            }
        }

        Move-Item -LiteralPath $bodyTemporary -Destination $bodyFinal
        Move-Item -LiteralPath $headersTemporary -Destination $headersFinal
        Move-Item -LiteralPath $metadataTemporary -Destination $metadataFinal

        $capturedManifest = Read-JsonFile -Path $script:ManifestPath
        $capturedState = Test-ManifestConsistency `
            -Plan $plan `
            -Manifest $capturedManifest `
            -AllowedInProgressRequestId $requestId

        $capturedRow = $capturedState.LedgerById[$requestId]

        if (
            [string](Get-Field $capturedRow "requestStatus") -ne "in_progress" -or
            [int](Get-Field $capturedRow "attemptCount") -ne 1
        ) {
            throw "Capture ledger state changed unexpectedly."
        }

        Set-Field $capturedRow "requestStatus" "captured"
        Set-Field $capturedRow "httpStatus" $httpStatus
        Set-Field $capturedRow "effectiveUrl" $effectiveUrl
        Set-Field $capturedRow "byteCount" $byteCount
        Set-Field $capturedRow "sha256" $bodyHash

        Set-Field `
            $capturedManifest `
            "httpRequestCount" `
            ([int](Get-Field $capturedManifest "httpRequestCount") +
                $httpRequestsExecuted)

        Set-Field `
            $capturedManifest `
            "capturedResponseCount" `
            ([int](Get-Field $capturedManifest "capturedResponseCount") + 1)

        Update-GameExecutionAggregates -Manifest $capturedManifest
        Save-ManifestAtomic -Manifest $capturedManifest

        Remove-Item `
            -LiteralPath $workDirectory `
            -Recurse `
            -Force `
            -ErrorAction SilentlyContinue

        $capturedThisBatch++
    }

    $finalPlanHash = (
        Get-FileHash -LiteralPath $script:PlanPath -Algorithm SHA256
    ).Hash.ToUpperInvariant()

    if ($finalPlanHash -ne $ExpectedFrozenPlanSha256) {
        throw "Frozen-plan hash changed during live batch."
    }

    $finalManifest = Read-JsonFile -Path $script:ManifestPath

    $finalState = Test-ManifestConsistency `
        -Plan $plan `
        -Manifest $finalManifest `
        -ValidateArtifacts

    Write-Host "`n# RESULT SUMMARY"
    Write-Host "EXECUTOR_MODE: LIVE"
    Write-Host "CAPTURED_THIS_BATCH: $capturedThisBatch"
    Write-Host "HTTP_REQUESTS_EXECUTED: $batchHttpRequests"
    Write-Host "CAPTURED_GAME_REQUEST_COUNT: $($finalState.CapturedRows.Count)"
    Write-Host "PENDING_GAME_REQUEST_COUNT: $($finalState.PlannedRows.Count)"
    Write-Host "PLAN_HASH_UNCHANGED: PASS"
    Write-Host "CANONICAL_PROMOTION_ELIGIBILITY: NO"
    Write-Host "EXECUTOR_VALIDATION: PASS"
    exit 0
}
catch {
    Write-Host "`n# RESULT SUMMARY"
    Write-Host "EXECUTOR_MODE: $(if ($DryRun) { 'DRY_RUN' } elseif ($Live) { 'LIVE' } else { 'INVALID' })"
    Write-Host "EXECUTOR_ERROR: $($_.Exception.Message)"
    Write-Host "HTTP_REQUESTS_EXECUTED: $script:ObservedHttpRequests"
    Write-Host "CANONICAL_PROMOTION_ELIGIBILITY: NO"
    Write-Host "EXECUTOR_VALIDATION: FAIL"
    exit 4
}
