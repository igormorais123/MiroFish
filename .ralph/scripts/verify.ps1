param(
    [string]$Command = ""
)

if ($Command.Trim().Length -gt 0) {
    Invoke-Expression $Command
    exit $LASTEXITCODE
}

if (Test-Path "package.json") {
    if (Test-Path ".\\backend\\.venv\\Scripts\\python.exe") {
        .\\backend\\.venv\\Scripts\\python.exe -m pytest backend\\tests -q
    } else {
        python -m pytest backend\\tests -q
    }
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    npm run build
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    git diff --check
    exit $LASTEXITCODE
}

if (Test-Path "pyproject.toml") {
    python -m pytest
    exit $LASTEXITCODE
}

if (Test-Path "pytest.ini") {
    python -m pytest
    exit $LASTEXITCODE
}

Write-Output "No default verification command detected. Update .ralph/VERIFY.md or call verify.ps1 -Command '<command>'."
exit 0
