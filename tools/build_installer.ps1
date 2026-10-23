# ==============================================================================
# Shalik Furniture Suite - Windows Setup Installer (.exe) Builder
# ==============================================================================

$ErrorActionPreference = "Stop"

$root = "E:\antigravity\Shalik Furniture"
$installerDir = Join-Path $root "installer"
$payloadDir = Join-Path $installerDir "payload"
$distDir = Join-Path $root "dist"
$isccExe = "C:\Users\archs\AppData\Local\Programs\Inno Setup 6\ISCC.exe"

if (-not (Test-Path $isccExe)) {
    throw "Inno Setup Compiler not found at: $isccExe"
}

Write-Host "Preparing installer payload..."
if (Test-Path $payloadDir) {
    Remove-Item -Recurse -Force $payloadDir
}
New-Item -ItemType Directory -Path $payloadDir | Out-Null

# 1. Copy application files to payload
Copy-Item (Join-Path $root "ShalikFurniture.rhp") $payloadDir -Force
Copy-Item (Join-Path $root "ShalikFurniture.rui") $payloadDir -Force
Copy-Item (Join-Path $root "ShalikFurnitureLauncher.exe") $payloadDir -Force
Copy-Item (Join-Path $root "ArchUnits.py") $payloadDir -Force
Copy-Item (Join-Path $root "ShalikAbout.py") $payloadDir -Force
Copy-Item (Join-Path $root "ShalikFurniture.py") $payloadDir -Force
Copy-Item (Join-Path $root "setup.ico") $payloadDir -Force
Copy-Item (Join-Path $root "icon.png") $payloadDir -Force
Copy-Item (Join-Path $root "manifest.yml") $payloadDir -Force
Copy-Item (Join-Path $root "README.md") $payloadDir -Force
Copy-Item (Join-Path $root "LICENSE.txt") $payloadDir -Force
Copy-Item (Join-Path $installerDir "USER_README.txt") $payloadDir -Force

if (Test-Path (Join-Path $root "author.png")) {
    Copy-Item (Join-Path $root "author.png") $payloadDir -Force
}
if (Test-Path (Join-Path $root "author.jpg")) {
    Copy-Item (Join-Path $root "author.jpg") $payloadDir -Force
}

Copy-Item (Join-Path $root "commands") $payloadDir -Recurse -Force
Copy-Item (Join-Path $root "Code") $payloadDir -Recurse -Force
Copy-Item (Join-Path $root "icons") $payloadDir -Recurse -Force

# Stage official InstantSKP payload
$instantSkpPayloadDir = Join-Path $installerDir "instant_skp_payload"
if (Test-Path $instantSkpPayloadDir) {
    Remove-Item -Recurse -Force $instantSkpPayloadDir
}
New-Item -ItemType Directory -Path $instantSkpPayloadDir | Out-Null
Copy-Item (Join-Path $root "instant skp\1.0.1\*") $instantSkpPayloadDir -Recurse -Force

Write-Host "Payload prepared with $((Get-ChildItem -Recurse $payloadDir).Count) files."

# 2. Run Inno Setup Compiler
$issFile = Join-Path $installerDir "ShalikFurnitureSetup.iss"
Write-Host "Compiling Windows Installer EXE via ISCC..."
& $isccExe $issFile
if ($LASTEXITCODE -ne 0) {
    throw "Inno Setup compilation failed with exit code $LASTEXITCODE"
}

# 3. Copy final installer to root folder as well
$setupExeDist = Join-Path $distDir "ShalikFurniture-Setup.exe"
if (Test-Path $setupExeDist) {
    $setupExeRoot = Join-Path $root "ShalikFurniture-Setup.exe"
    Copy-Item $setupExeDist $setupExeRoot -Force
    Write-Host "SUCCESS! Installer executable created:"
    Write-Host "  -> Root: $setupExeRoot ($((Get-Item $setupExeRoot).Length) bytes)"
    Write-Host "  -> Dist: $setupExeDist ($((Get-Item $setupExeDist).Length) bytes)"
} else {
    throw "Expected setup exe not found at: $setupExeDist"
}
