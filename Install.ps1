$ErrorActionPreference = 'Stop'
$modRoot = $PSScriptRoot
$gameRoot = Split-Path -Parent $modRoot
if (Get-Process -Name 'KingOfTheCastle' -ErrorAction SilentlyContinue) {
    throw 'Nejprve zavrete King of the Castle.'
}
$manifest = Get-Content -LiteralPath (Join-Path $modRoot 'manifest.json') -Raw -Encoding UTF8 | ConvertFrom-Json
function Get-TargetPath([string]$relative, [string]$root) {
    $resolved = [IO.Path]::GetFullPath((Join-Path $root $relative))
    $prefix = [IO.Path]::GetFullPath($root).TrimEnd('\') + '\'
    if (-not $resolved.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) { throw 'Neplatna cesta v manifestu.' }
    return $resolved
}
foreach ($item in $manifest.files) {
    $source = Get-TargetPath $item.path (Join-Path $modRoot 'patched')
    $target = Get-TargetPath $item.path $gameRoot
    if (-not (Test-Path -LiteralPath $source) -or (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToLowerInvariant() -ne $item.patched_sha256) { throw "Poskozeny soubor cestiny: $($item.path)" }
    if (Test-Path -LiteralPath $target) {
        $hash = (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($hash -ne $item.original_sha256 -and $hash -ne $item.patched_sha256) { throw "Jina verze hry nebo jiny mod: $($item.path). Instalace zastavena; zadne soubory nebyly prepsany." }
    } elseif ($item.original_sha256) { throw "Chybi herni soubor: $($item.path)" }
}
foreach ($item in $manifest.files) {
    $target = Get-TargetPath $item.path $gameRoot
    $backup = Get-TargetPath $item.path (Join-Path $modRoot 'backup')
    if ($item.original_sha256) {
        if (Test-Path -LiteralPath $backup) {
            if ((Get-FileHash -LiteralPath $backup -Algorithm SHA256).Hash.ToLowerInvariant() -ne $item.original_sha256) { throw "Nesouhlasi zaloha: $($item.path)" }
        } else {
            if ((Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant() -ne $item.original_sha256) { throw "Chybi puvodni zaloha: $($item.path)" }
            New-Item -ItemType Directory -Path (Split-Path -Parent $backup) -Force | Out-Null
            Copy-Item -LiteralPath $target -Destination $backup
        }
    }
}
foreach ($item in $manifest.files) {
    $source = Get-TargetPath $item.path (Join-Path $modRoot 'patched')
    $target = Get-TargetPath $item.path $gameRoot
    Copy-Item -LiteralPath $source -Destination $target -Force
}
$manifest | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $modRoot 'installed-manifest.json') -Encoding UTF8
Write-Output 'Cestina je nainstalovana. Hru spustte obvykle pres Steam.'
