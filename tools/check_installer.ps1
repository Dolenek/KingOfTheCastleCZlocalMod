$ErrorActionPreference = 'Stop'
$modRoot = Split-Path -Parent $PSScriptRoot
$fixtureRoot = Join-Path $PSScriptRoot 'installer-fixture'
$fixtureMod = Join-Path $fixtureRoot 'KingOfTheCastleCZlocalMod'
New-Item -ItemType Directory -Path $fixtureMod -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $fixtureMod 'patched') -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $fixtureMod 'fonts') -Force | Out-Null
Get-ChildItem -LiteralPath (Join-Path $modRoot 'fonts') -File | ForEach-Object {
    Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $fixtureMod 'fonts') -Force
}
Copy-Item -LiteralPath (Join-Path $modRoot 'Install.ps1') -Destination $fixtureMod -Force
Copy-Item -LiteralPath (Join-Path $modRoot 'Restore.ps1') -Destination $fixtureMod -Force
function Assert([bool]$value,[string]$message) { if (-not $value) { throw $message } }
function Hash([string]$path) { return (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() }
$original = Join-Path $fixtureRoot 'original.bin'
$patched = Join-Path $fixtureMod 'patched\original.bin'
$added = Join-Path $fixtureMod 'patched\added.bin'
[IO.File]::WriteAllText($original,'original fixture data')
[IO.File]::WriteAllText($patched,'Czech fixture data')
[IO.File]::WriteAllText($added,'new helper fixture data')
$originalHash = Hash $original
$manifest = @{ version='fixture'; files=@(
    @{path='original.bin';original_sha256=$originalHash;patched_sha256=(Hash $patched)},
    @{path='added.bin';original_sha256=$null;patched_sha256=(Hash $added)}
) }
$manifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $fixtureMod 'manifest.json') -Encoding UTF8
& (Join-Path $fixtureMod 'Install.ps1')
Assert ((Hash $original) -eq (Hash $patched)) 'Install did not apply patch'
Assert ((Hash (Join-Path $fixtureMod 'backup\original.bin')) -eq $originalHash) 'Original backup is invalid'
& (Join-Path $fixtureMod 'Install.ps1')
& (Join-Path $fixtureMod 'Restore.ps1')
Assert ((Hash $original) -eq $originalHash) 'Restore did not restore original bytes'
Assert (-not (Test-Path -LiteralPath (Join-Path $fixtureRoot 'added.bin'))) 'Restore retained added file'
[IO.File]::WriteAllText($original,'different mod fixture')
$conflictingHash = Hash $original
$rejected = $false
try { & (Join-Path $fixtureMod 'Install.ps1') } catch { $rejected = $true }
Assert $rejected 'Installer overwrote a conflicting version'
Assert ((Hash $original) -eq $conflictingHash) 'Rejection changed conflicting file'
Assert (-not (Test-Path -LiteralPath (Join-Path $fixtureRoot 'added.bin'))) 'Rejection partially installed files'
[IO.File]::WriteAllText($original,'original fixture data')
$fontFixture = Join-Path $fixtureMod 'fonts\MedievalSharp.ttf'
[IO.File]::WriteAllText($fontFixture,'corrupt font fixture')
$rejected = $false
try { & (Join-Path $fixtureMod 'Install.ps1') } catch { $rejected = $true }
Assert $rejected 'Installer accepted a corrupt packaged font'
Assert ((Hash $original) -eq $originalHash) 'Font rejection changed game data'
Assert (-not (Test-Path -LiteralPath (Join-Path $fixtureRoot 'added.bin'))) 'Font rejection partially installed files'
Copy-Item -LiteralPath (Join-Path $modRoot 'fonts\MedievalSharp.ttf') -Destination $fontFixture -Force
$manifest.files[0].path = '..\outside.bin'
$manifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $fixtureMod 'manifest.json') -Encoding UTF8
$rejected = $false
try { & (Join-Path $fixtureMod 'Install.ps1') } catch { $rejected = $true }
Assert $rejected 'Installer accepted path traversal'
foreach ($name in @('Install.ps1','Restore.ps1')) {
    $parseErrors = $null; $tokens = $null
    [System.Management.Automation.Language.Parser]::ParseFile((Join-Path $modRoot $name),[ref]$tokens,[ref]$parseErrors) | Out-Null
    Assert ($parseErrors.Count -eq 0) ('PowerShell syntax error in '+$name)
}
@{installation=$true;idempotence=$true;restoration=$true;version_conflict_rejected=$true;path_traversal_rejected=$true;corrupt_font_rejected=$true;game_started=$false} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'checks-installer.json') -Encoding UTF8
Write-Output 'INSTALLER CODE CHECKS PASSED. Only synthetic fixture files were modified.'
