# ==============================================================================
# Shalik Furniture Suite - Yak Package Builder
# ==============================================================================

$ErrorActionPreference = "Stop"

$root = "E:\antigravity\Shalik Furniture"
$stage = Join-Path $root "yak_stage"
$dist = Join-Path $root "dist"

if (Test-Path $stage) {
    Remove-Item -Recurse -Force $stage
}
New-Item -ItemType Directory -Path $stage | Out-Null

Copy-Item (Join-Path $root "ShalikFurniture.rhp") $stage
Copy-Item (Join-Path $root "ShalikFurniture.rui") $stage
Copy-Item (Join-Path $root "ArchUnits.py") $stage
Copy-Item (Join-Path $root "ShalikAbout.py") $stage
Copy-Item (Join-Path $root "ShalikFurniture.py") $stage
Copy-Item (Join-Path $root "icon.png") $stage
Copy-Item (Join-Path $root "manifest.yml") $stage
Copy-Item (Join-Path $root "README.md") $stage
Copy-Item (Join-Path $root "LICENSE.txt") $stage

if (Test-Path (Join-Path $root "author.png")) {
    Copy-Item (Join-Path $root "author.png") $stage
}
if (Test-Path (Join-Path $root "author.jpg")) {
    Copy-Item (Join-Path $root "author.jpg") $stage
}

Copy-Item (Join-Path $root "icons") $stage -Recurse
Copy-Item (Join-Path $root "commands") $stage -Recurse
Copy-Item (Join-Path $root "Code") $stage -Recurse

Write-Host "Staged files for Yak:"
Get-ChildItem $stage | Select-Object Name, Length

$yakExe = "C:\Program Files\Rhino 8\System\Yak.exe"
Push-Location $stage
try {
    & $yakExe build
} finally {
    Pop-Location
}

$yakFiles = Get-ChildItem -Path $stage -Filter "*.yak"
foreach ($f in $yakFiles) {
    Copy-Item $f.FullName (Join-Path $root $f.Name) -Force
    Copy-Item $f.FullName (Join-Path $dist $f.Name) -Force
    Write-Host "Created Yak package: $($f.Name) ($($f.Length) bytes)"
}
