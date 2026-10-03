$ErrorActionPreference = 'Stop'
$sourceRoot = [IO.Path]::GetFullPath((Split-Path -Parent $PSScriptRoot))
$skillName = 'dqtx-WeFlow-Daily'
if (-not (Test-Path -LiteralPath (Join-Path $sourceRoot 'SKILL.md'))) {
    throw 'Extract the complete skill package before installing.'
}
$desktopRoot = [Environment]::GetFolderPath('Desktop')
$desktopTarget = [IO.Path]::GetFullPath((Join-Path $desktopRoot $skillName))
$skillParent = Join-Path $env:USERPROFILE '.agents\skills'
$installTarget = [IO.Path]::GetFullPath((Join-Path $skillParent $skillName))
$destinations = @($desktopTarget, $installTarget) | Select-Object -Unique
foreach ($destination in $destinations) {
    if ($destination -eq $sourceRoot) { continue }
    if (Test-Path -LiteralPath $destination) {
        throw "Existing folder preserved: $destination. Rename it before installation."
    }
}
foreach ($destination in $destinations) {
    if ($destination -eq $sourceRoot) { continue }
    New-Item -ItemType Directory -Path $destination -Force | Out-Null
    Get-ChildItem -LiteralPath $sourceRoot -Force | Where-Object { $_.Name -ne '.git' } | ForEach-Object {
        Copy-Item -LiteralPath $_.FullName -Destination $destination -Recurse
    }
    Write-Output "Created: $destination"
}
Write-Output 'Restart Codex and connect WeFlow MCP. Invoke $dqtx-WeFlow-Daily followed by the group name.'
