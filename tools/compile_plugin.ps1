$ErrorActionPreference = "Stop"
$csc = "C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe"
$src = "E:\antigravity\Shalik Furniture\src\ShalikFurniturePlugin.cs"
$refRhino = "C:\Program Files\Rhino 8\System\RhinoCommon.dll"

$outRoot = "E:\antigravity\Shalik Furniture\ShalikFurniture.rhp"
$outDist = "E:\antigravity\Shalik Furniture\dist\ShalikFurniture.rhp"

Write-Host "Compiling ShalikFurniture.rhp..."
& $csc /target:library /optimize+ /out:$outRoot /reference:$refRhino /reference:System.dll /reference:System.Core.dll $src
if ($LASTEXITCODE -ne 0) { throw "CSC compile failed for ShalikFurniture.rhp" }

Copy-Item $outRoot $outDist -Force
Write-Host "Compilation SUCCESS! Plugin generated at: $outRoot and $outDist"

# Compile ShalikFurnitureLauncher.exe
$launcherSrc = "E:\antigravity\Shalik Furniture\src\ShalikFurnitureLauncher.cs"
$launcherOutRoot = "E:\antigravity\Shalik Furniture\ShalikFurnitureLauncher.exe"
$launcherOutDist = "E:\antigravity\Shalik Furniture\dist\ShalikFurnitureLauncher.exe"
$setupIco = "E:\antigravity\Shalik Furniture\setup.ico"

Write-Host "Compiling ShalikFurnitureLauncher.exe..."
& $csc /target:winexe /optimize+ /win32icon:$setupIco /out:$launcherOutRoot /reference:System.dll /reference:System.Core.dll /reference:System.Windows.Forms.dll /reference:System.Drawing.dll $launcherSrc
if ($LASTEXITCODE -ne 0) { throw "CSC compile failed for ShalikFurnitureLauncher.exe" }

Copy-Item $launcherOutRoot $launcherOutDist -Force
Write-Host "Compilation SUCCESS! Launcher generated at: $launcherOutRoot and $launcherOutDist"
Get-Item $outRoot, $outDist, $launcherOutRoot, $launcherOutDist | Select-Object Name, Length, LastWriteTime
