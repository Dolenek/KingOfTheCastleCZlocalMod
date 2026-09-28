param([switch]$Install)
$ErrorActionPreference = 'Stop'
$modRoot = Split-Path -Parent $PSScriptRoot
$gameRoot = Split-Path -Parent $modRoot
$python = Join-Path $PSScriptRoot 'venv\Scripts\python.exe'
function Run-Python([string]$script,[string[]]$arguments=@()) {
    & $python (Join-Path $PSScriptRoot $script) @arguments
    if ($LASTEXITCODE -ne 0) { throw "Failed: $script" }
}
function Run-DotNet([string[]]$arguments) {
    & dotnet @arguments
    if ($LASTEXITCODE -ne 0) { throw "Failed: dotnet $arguments" }
}
function Status([string]$stage) {
    @{stage=$stage;updated_utc=[DateTime]::UtcNow.ToString('o');game_started=$false} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $modRoot 'status.json') -Encoding UTF8
    Write-Output "STAGE: $stage"
}
Push-Location $gameRoot
try {
    Status 'final_translation_and_repairs'
    Run-Python 'prepare_names.py'
    Run-Python 'manual_ui.py'
    Run-Python 'manual_extra.py'
    Run-Python 'manual_rules.py'
    Run-Python 'preserve_identifiers.py'
    Run-Python 'repair_cache.py'
    Run-Python 'translate.py'
    Run-Python 'check_translations.py'
    Run-Python 'build_code_overrides.py'
    Run-Python 'check_translations.py'
    Status 'building_mod'
    Run-DotNet @('build',(Join-Path $PSScriptRoot 'Runtime'),'-c','Release','--no-restore')
    Run-DotNet @('build',(Join-Path $PSScriptRoot 'PatchTool'),'-c','Release','--no-restore')
    $patchTool = Join-Path $PSScriptRoot 'PatchTool\bin\Release\net9.0\PatchTool.dll'
    $runtime = Join-Path $PSScriptRoot 'Runtime\bin\Release\netstandard2.0\Kotc.Czech.dll'
    $managed = Join-Path $gameRoot 'KingOfTheCastle_Data\Managed'
    $output = Join-Path $modRoot 'patched\KingOfTheCastle_Data\Managed'
    Run-DotNet @($patchTool,'patch-game',(Join-Path $managed 'KotcAssembly.dll'),(Join-Path $output 'KotcAssembly.dll'),(Join-Path $PSScriptRoot 'code-overrides.json'))
    Run-DotNet @($patchTool,'patch-tmp',(Join-Path $managed 'Unity.TextMeshPro.dll'),$runtime,(Join-Path $output 'Unity.TextMeshPro.dll'))
    Copy-Item -LiteralPath $runtime -Destination (Join-Path $output 'Kotc.Czech.dll') -Force
    Run-Python 'pipeline.py' @('build')
    Run-Python 'prepare_package.py'
    Status 'validating_mod'
    Run-Python 'check_pipeline.py'
    Run-Python 'validate_assets.py'
    Run-DotNet @('run','--project',(Join-Path $PSScriptRoot 'Checks'),'-c','Release','--no-restore','--',$modRoot,(Join-Path $PSScriptRoot 'ink-translated'))
    if ($Install) {
        Status 'installing_with_backup'
        & (Join-Path $modRoot 'Install.ps1')
        $manifest=Get-Content -LiteralPath (Join-Path $modRoot 'manifest.json') -Raw -Encoding UTF8 | ConvertFrom-Json
        foreach ($file in $manifest.files) {
            $target=Join-Path $gameRoot $file.path
            if ((Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant() -ne $file.patched_sha256) { throw "Installed hash mismatch: $($file.path)" }
        }
    }
    Status 'complete'
} catch {
    Status 'needs_repair'
    throw
} finally { Pop-Location }
