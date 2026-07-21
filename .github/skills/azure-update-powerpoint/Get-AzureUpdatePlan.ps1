[CmdletBinding()]
param(
    [string]$RepositoryRoot = (Get-Location).Path,
    [datetime]$AsOfDate = (Get-Date)
)

$root = (Resolve-Path -LiteralPath $RepositoryRoot).Path
$requiredFiles = @(
    'README.md',
    '1_get_azure_update.py',
    '2_make_jp_update_pptx.py'
)

$missingFiles = @(
    $requiredFiles | Where-Object {
        -not (Test-Path -LiteralPath (Join-Path $root $_) -PathType Leaf)
    }
)

if ($missingFiles.Count -gt 0) {
    throw "Missing required files: $($missingFiles -join ', ')"
}

$deckPattern = '^pptx_azure_update_(?<start>\d{8})_(?<end>\d{8})(?:_(?<variant>[^.]+))?\.pptx$'
$decks = @(
    Get-ChildItem -LiteralPath $root -File -Filter 'pptx_azure_update_*.pptx' |
        Where-Object { $_.Length -gt 0 } |
        ForEach-Object {
            if ($_.Name -match $deckPattern) {
                try {
                    [pscustomobject]@{
                        Name = $_.Name
                        StartDate = [datetime]::ParseExact(
                            $Matches.start,
                            'yyyyMMdd',
                            [Globalization.CultureInfo]::InvariantCulture
                        )
                        EndDate = [datetime]::ParseExact(
                            $Matches.end,
                            'yyyyMMdd',
                            [Globalization.CultureInfo]::InvariantCulture
                        )
                        Variant = $Matches.variant
                        LastWriteTime = $_.LastWriteTime
                    }
                }
                catch {
                    Write-Warning "Ignoring invalid deck filename: $($_.Name)"
                }
            }
        }
)

if ($decks.Count -eq 0) {
    throw 'No non-empty standard Azure Update PowerPoint deck was found.'
}

$latestEndDate = (
    $decks |
        Sort-Object EndDate -Descending |
        Select-Object -First 1
).EndDate

$baselineDecks = @(
    $decks |
        Where-Object { $_.EndDate -eq $latestEndDate } |
        Sort-Object @{ Expression = { [string]::IsNullOrEmpty($_.Variant) }; Descending = $true },
                    LastWriteTime -Descending
)

$primaryDeck = $baselineDecks | Select-Object -First 1
$fromCompact = $latestEndDate.ToString('yyyyMMdd')
$fromIso = $latestEndDate.ToString('yyyy-MM-dd')
$toCompact = $AsOfDate.ToString('yyyyMMdd')
$markdownFile = "azure_update_${fromCompact}_${toCompact}.md"
$powerPointFile = "pptx_azure_update_${fromCompact}_${toCompact}.pptx"
$markdownPath = Join-Path $root $markdownFile

$existingMarkdownState = if (-not (Test-Path -LiteralPath $markdownPath -PathType Leaf)) {
    'absent'
}
elseif ((Get-Item -LiteralPath $markdownPath).Length -eq 0) {
    'zero-byte'
}
else {
    'non-empty'
}

[pscustomobject]@{
    RepositoryRoot = $root
    BaselineEndDate = $fromIso
    PrimaryBaselineDeck = $primaryDeck.Name
    BaselineDecks = @($baselineDecks.Name)
    AsOfDate = $AsOfDate.ToString('yyyy-MM-dd')
    MarkdownFile = $markdownFile
    PowerPointFile = $powerPointFile
    ExistingMarkdownState = $existingMarkdownState
    PythonPath = Join-Path $root 'venv\Scripts\python.exe'
    PythonExists = Test-Path -LiteralPath (Join-Path $root 'venv\Scripts\python.exe') -PathType Leaf
    EnvironmentFileExists = Test-Path -LiteralPath (Join-Path $root '.env') -PathType Leaf
} | ConvertTo-Json -Depth 3
