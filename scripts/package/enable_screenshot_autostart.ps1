$ErrorActionPreference = "Stop"

$dir = Join-Path $env:LOCALAPPDATA "activitywatch\activitywatch\aw-qt"
New-Item -ItemType Directory -Force -Path $dir | Out-Null
$path = Join-Path $dir "aw-qt.toml"

$wanted = '["aw-server", "aw-watcher-afk", "aw-watcher-window", "aw-watcher-screenshot"]'

if (-not (Test-Path $path)) {
    Set-Content -Path $path -Encoding utf8 -Value @"
[aw-qt]
autostart_modules = $wanted
"@
    exit 0
}

$lines = @(Get-Content -Path $path)
$done = $false
$out = foreach ($line in $lines) {
    if (-not $done -and $line -match 'autostart_modules\s*=\s*\[([^\]]*)\]') {
        $done = $true
        $inner = $Matches[1]
        if ($inner -match 'aw-watcher-screenshot') {
            $line -replace '^\s*#\s*', ''
        } else {
            $trimmed = $inner.Trim().TrimEnd(',')
            if ($trimmed) {
                "autostart_modules = [$trimmed, `"aw-watcher-screenshot`"]"
            } else {
                "autostart_modules = $wanted"
            }
        }
    } else {
        $line
    }
}

if (-not $done) {
    $out = @("[aw-qt]", "autostart_modules = $wanted", "") + $out
}

Set-Content -Path $path -Encoding utf8 -Value $out
