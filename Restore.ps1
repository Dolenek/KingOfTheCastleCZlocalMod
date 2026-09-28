$ErrorActionPreference = 'Stop'
$modRoot = $PSScriptRoot
$gameRoot = Split-Path -Parent $modRoot
if (Get-Process -Name 'KingOfTheCastle' -ErrorAction SilentlyContinue) { throw 'Nejprve zavrete King of the Castle.' }
$record = Join-Path $modRoot 'installed-manifest.json'
if (-not (Test-Path -LiteralPath $record)) { throw 'Cestina zatim nebyla nainstalovana.' }
$manifest = Get-Content -LiteralPath $record -Raw -Encoding UTF8 | ConvertFrom-Json
function Get-TargetPath([string]$relative, [string]$root) {
    $resolved = [IO.Path]::GetFullPath((Join-Path $root $relative))
    $prefix = [IO.Path]::GetFullPath($root).TrimEnd('\') + '\'
    if (-not $resolved.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) { throw 'Neplatna cesta v manifestu.' }
    return $resolved
}
foreach ($item in $manifest.files) {
    $target = Get-TargetPath $item.path $gameRoot
    if (Test-Path -LiteralPath $target) {
        $hash = (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($hash -ne $item.patched_sha256 -and $hash -ne $item.original_sha256) { throw "Soubor byl mezitim zmenen: $($item.path). Obnova zastavena." }
    }
    if ($item.original_sha256) {
        $backup = Get-TargetPath $item.path (Join-Path $modRoot 'backup')
        if (-not (Test-Path -LiteralPath $backup) -or (Get-FileHash -LiteralPath $backup -Algorithm SHA256).Hash.ToLowerInvariant() -ne $item.original_sha256) { throw "Chybi platna zaloha: $($item.path)" }
    }
}
foreach ($item in $manifest.files) {
    $target = Get-TargetPath $item.path $gameRoot
    if ($item.original_sha256) {
        $backup = Get-TargetPath $item.path (Join-Path $modRoot 'backup')
        Copy-Item -LiteralPath $backup -Destination $target -Force
    } elseif (Test-Path -LiteralPath $target) {
        Remove-Item -LiteralPath $target
    }
}
Write-Output 'Puvodni anglicke soubory hry byly obnoveny. Zaloha zustava ulozena.'
