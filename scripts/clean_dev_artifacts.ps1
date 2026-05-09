param(
    [switch]$Apply,
    [switch]$IncludeLogs
)

$ErrorActionPreference = "Stop"

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$targets = New-Object System.Collections.Generic.List[string]

function Add-Target {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        return
    }
    $resolved = (Resolve-Path -LiteralPath $Path).Path
    if (-not $resolved.StartsWith($Root, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to clean path outside repository: $resolved"
    }
    $protected = @(
        (Join-Path $Root ".git"),
        (Join-Path $Root ".env"),
        (Join-Path $Root "backend\.venv"),
        (Join-Path $Root "backend\uploads"),
        (Join-Path $Root "frontend\node_modules")
    )
    foreach ($item in $protected) {
        if ($resolved.Equals($item, [System.StringComparison]::OrdinalIgnoreCase) -or
            $resolved.StartsWith("$item\", [System.StringComparison]::OrdinalIgnoreCase)) {
            throw "Refusing to clean protected path: $resolved"
        }
    }
    $targets.Add($resolved) | Out-Null
}

Get-ChildItem -LiteralPath $Root -Directory -Recurse -Force -Filter "__pycache__" |
    Where-Object {
        $_.FullName -notlike "*\backend\.venv\*" -and
        $_.FullName -notlike "*\frontend\node_modules\*"
    } |
    ForEach-Object { Add-Target $_.FullName }

Add-Target (Join-Path $Root "backend\.pytest_cache")
Add-Target (Join-Path $Root "frontend\dist")

if ($IncludeLogs) {
    @(
        "logs_backend.err.log",
        "logs_backend.log",
        "logs_backend.out.log",
        "logs_codex_proxy.err.log",
        "logs_codex_proxy.log",
        "logs_frontend.err.log",
        "logs_frontend.out.log"
    ) | ForEach-Object { Add-Target (Join-Path $Root $_) }
}

$uniqueTargets = $targets | Sort-Object -Unique
if (-not $uniqueTargets) {
    Write-Output "No generated development artifacts found."
    exit 0
}

if (-not $Apply) {
    Write-Output "Dry run. Re-run with -Apply to remove:"
    $uniqueTargets | ForEach-Object { Write-Output "  $_" }
    exit 0
}

foreach ($target in $uniqueTargets) {
    try {
        Remove-Item -LiteralPath $target -Recurse -Force
        Write-Output "Removed $target"
    } catch {
        Write-Warning "Could not remove $target`: $($_.Exception.Message)"
    }
}
