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
Get-Item $outRoot, $outDist | Select-Object Name, Length, LastWriteTime
