# ==============================================================================
# Shalik Furniture Suite - Master Build Script
# Rebuilds Plugin, Icons, Toolbar, Yak Package & Setup Installer in sequence
# ==============================================================================

$ErrorActionPreference = "Stop"

$root = "E:\antigravity\Shalik Furniture"
$toolsDir = Join-Path $root "tools"

Write-Host "=========================================================="
Write-Host " Building Shalik Furniture Suite by Sakhawat Hosen Sumon"
Write-Host "=========================================================="

Write-Host "`n[Step 1/5] Compiling Rhino Plugin (ShalikFurniture.rhp)..."
& powershell.exe -ExecutionPolicy Bypass -File (Join-Path $toolsDir "compile_plugin.ps1")

Write-Host "`n[Step 2/5] Generating Dark-Red Icons & Setup Icon..."
& powershell.exe -ExecutionPolicy Bypass -File (Join-Path $toolsDir "make_icons.ps1")

Write-Host "`n[Step 3/5] Building Rhino Toolbar (ShalikFurniture.rui)..."
& powershell.exe -ExecutionPolicy Bypass -File (Join-Path $toolsDir "build_rui.ps1")

Write-Host "`n[Step 4/5] Building McNeel Yak Package (.yak)..."
& powershell.exe -ExecutionPolicy Bypass -File (Join-Path $toolsDir "build_yak.ps1")

Write-Host "`n[Step 5/5] Compiling Launcher and Windows Installer (.exe)..."
& powershell.exe -ExecutionPolicy Bypass -File (Join-Path $toolsDir "build_installer.ps1")

Write-Host "`n=========================================================="
Write-Host " Build Finished Successfully! Deliverables in dist/:"
Get-ChildItem (Join-Path $root "dist") | Select-Object Name, Length, LastWriteTime
Write-Host "=========================================================="
