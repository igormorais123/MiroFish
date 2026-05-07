param(
    [string]$OutputDir = "docs/validation/helena_report_lab_2026-05-07",
    [string]$ChromePath = "C:\Program Files\Google\Chrome\Application\chrome.exe"
)

$ErrorActionPreference = "Stop"

python -m backend.scripts.helena_report_lab --output-dir $OutputDir

if (-not (Test-Path $ChromePath)) {
    throw "Chrome headless not found at $ChromePath"
}

$root = Resolve-Path $OutputDir
$screenshots = Join-Path $root "screenshots"
New-Item -ItemType Directory -Force -Path $screenshots | Out-Null

$manifestPath = Join-Path $root "validation_manifest.json"
$manifest = Get-Content $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
$results = @()

foreach ($report in $manifest.reports) {
    $reportPath = Join-Path $root $report.filename
    $uri = (Resolve-Path $reportPath).Path
    $fileUrl = "file:///" + ($uri -replace "\\", "/")

    $targets = @(
        @{ Suffix = "desktop"; Size = "1440,1200" },
        @{ Suffix = "mobile"; Size = "390,1200" },
        @{ Suffix = "internal"; Size = "1024,1800" }
    )

    foreach ($target in $targets) {
        $shot = Join-Path $screenshots "$($report.slug)-$($target.Suffix).png"
        & $ChromePath `
            --headless=new `
            --disable-gpu `
            --hide-scrollbars `
            --window-size=$($target.Size) `
            --screenshot="$shot" `
            $fileUrl | Out-Null

        $item = Get-Item $shot
        $results += [pscustomobject]@{
            report = $report.slug
            viewport = $target.Suffix
            file = "screenshots/$($report.slug)-$($target.Suffix).png"
            size = $item.Length
            passes = $item.Length -gt 10000
        }
    }
}

$failed = @($results | Where-Object { $_.passes -ne $true })
$audit = [pscustomobject]@{
    schema = "mirofish.helena_report_lab.screenshot_audit.v1"
    generated_at = (Get-Date).ToUniversalTime().ToString("o")
    reports_count = $manifest.reports_count
    expected_screenshots = $manifest.reports_count * 3
    screenshots_count = $results.Count
    passes = ($failed.Count -eq 0 -and $results.Count -eq ($manifest.reports_count * 3))
    screenshots = $results
    errors = $failed
}

$audit | ConvertTo-Json -Depth 8 | Set-Content -Path (Join-Path $root "screenshot_audit.json") -Encoding UTF8

if ($audit.passes -ne $true) {
    throw "Helena report lab screenshot audit failed"
}

$cards = foreach ($report in $manifest.reports) {
    $shots = @("desktop", "mobile", "internal") | ForEach-Object {
        $file = "screenshots/$($report.slug)-$_.png"
        "<figure><img src=`"$file`" alt=`"$($report.title) - $_`"><figcaption>$($_)</figcaption></figure>"
    }
    @"
<section class="report-card">
  <h2>$($report.title)</h2>
  <p><strong>Pergunta:</strong> $($report.decision_question)</p>
  <p><strong>Confiança:</strong> $($report.confidence)</p>
  <p><a href="$($report.filename)">Abrir relatório HTML</a></p>
  <div class="shots">
    $($shots -join "`n")
  </div>
</section>
"@
}

$visualHtml = @"
<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Validação Visual Helena | INTEIA</title>
  <style>
    :root { --ink:#111827; --muted:#4b5563; --line:#d9dee8; --gold:#b7791f; --panel:#f8fafc; }
    * { box-sizing:border-box; }
    body { margin:0; font-family:Inter, Segoe UI, Arial, sans-serif; background:#eef2f7; color:var(--ink); }
    header { padding:40px; background:#111827; color:#fff; border-bottom:5px solid var(--gold); }
    h1 { margin:0; font-size:42px; letter-spacing:0; }
    main { max-width:1180px; margin:0 auto; padding:30px; background:#fff; }
    .summary { display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:12px; margin-bottom:28px; }
    .metric, .report-card { border:1px solid var(--line); border-radius:8px; background:var(--panel); padding:16px; }
    .metric span { display:block; color:var(--muted); font-size:12px; text-transform:uppercase; }
    .metric strong { display:block; font-size:24px; margin-top:4px; }
    .report-card { margin:22px 0; background:#fff; }
    .shots { display:grid; grid-template-columns:repeat(auto-fit,minmax(260px,1fr)); gap:14px; }
    figure { margin:0; border:1px solid var(--line); background:#f8fafc; padding:8px; }
    img { width:100%; height:360px; object-fit:cover; object-position:top; display:block; border:1px solid var(--line); background:#fff; }
    figcaption { margin-top:6px; color:var(--muted); font-size:13px; text-transform:uppercase; }
    a { color:#8a5a00; font-weight:700; }
  </style>
</head>
<body>
  <header>
    <p>RELATÓRIO DE VALIDAÇÃO VISUAL | INTEIA</p>
    <h1>Helena coordena, Efesto corrige, Oracle valida</h1>
  </header>
  <main>
    <section class="summary">
      <div class="metric"><span>Relatórios</span><strong>$($manifest.reports_count)</strong></div>
      <div class="metric"><span>Screenshots</span><strong>$($results.Count)</strong></div>
      <div class="metric"><span>Oracle</span><strong>$($manifest.oracle_verdict)</strong></div>
      <div class="metric"><span>Auditoria visual</span><strong>$($audit.passes)</strong></div>
    </section>
    $($cards -join "`n")
  </main>
</body>
</html>
"@

$visualHtml | Set-Content -Path (Join-Path $root "visual_validation_report.html") -Encoding UTF8

Write-Host "Helena report lab passed: $($manifest.reports_count) reports, $($results.Count) screenshots."
