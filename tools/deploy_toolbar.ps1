# ==============================================================================
# Deploy and Auto-Show Shalik Furniture Toolbar for Rhino 8
# ==============================================================================

$root = "E:\antigravity\Shalik Furniture"
$pluginGuid = "0ce7337f-ec52-45da-9fd3-cc40db64b2fa"
$pkgDir = "$env:APPDATA\McNeel\Rhinoceros\packages\8.0\ShalikFurniture\1.0.0"
$schemeDir = "$env:APPDATA\McNeel\Rhinoceros\8.0\settings\Scheme__Default"
$importedDir = Join-Path $schemeDir "imported_rui_files"
$containersXmlPath = Join-Path $schemeDir "containers.xml"

Write-Host "1. Deploying to packages directory ($pkgDir)..."
if (-not (Test-Path $pkgDir)) { New-Item -ItemType Directory -Path $pkgDir -Force | Out-Null }
if (-not (Test-Path $importedDir)) { New-Item -ItemType Directory -Path $importedDir -Force | Out-Null }

# Copy core files
$files = @("ShalikFurniture.rhp", "ShalikFurniture.rui", "ArchUnits.py", "ShalikFurniture.py", "ShalikAbout.py", "ShalikImportSKP.py", "author.jpg", "author.png", "icon.png", "setup.ico", "manifest.yml", "README.md", "LICENSE.txt")
foreach ($f in $files) {
    Copy-Item (Join-Path $root $f) (Join-Path $pkgDir $f) -Force
}

if (Test-Path (Join-Path $root "author.png")) {
    Copy-Item (Join-Path $root "author.png") (Join-Path $pkgDir "author.png") -Force
}

Copy-Item (Join-Path $root "commands") $pkgDir -Recurse -Force
Copy-Item (Join-Path $root "Code") $pkgDir -Recurse -Force
Copy-Item (Join-Path $root "icons") $pkgDir -Recurse -Force

Write-Host "2. Copying to imported_rui_files cache..."
$cachedRui = Join-Path $importedDir "ShalikFurniture_$pluginGuid.rui"
Copy-Item (Join-Path $root "ShalikFurniture.rui") $cachedRui -Force

Write-Host "3. Injecting into containers.xml..."
if (Test-Path $containersXmlPath) {
    [xml]$cDoc = Get-Content -LiteralPath $containersXmlPath

    # 3.1 plug_in_files
    $pFilesNode = $cDoc.SelectSingleNode("//plug_in_files")
    if (-not $pFilesNode) {
        $pFilesNode = $cDoc.CreateElement("plug_in_files")
        $cDoc.DocumentElement.AppendChild($pFilesNode) | Out-Null
    }
    $targetRui = Join-Path $pkgDir "ShalikFurniture.rui"
    $pEntry = $pFilesNode.SelectSingleNode("file_name[@plug_in_guid='$pluginGuid']")
    if (-not $pEntry) {
        $newPElem = $cDoc.CreateElement("file_name")
        $newPElem.SetAttribute("plug_in_guid", $pluginGuid)
        $newPElem.InnerText = $targetRui
        $pFilesNode.AppendChild($newPElem) | Out-Null
        Write-Host "   Added to <plug_in_files>."
    } else {
        $pEntry.InnerText = $targetRui
        Write-Host "   Updated <plug_in_files>."
    }

    # 3.2 dock_bars
    $dockBarsNode = $cDoc.SelectSingleNode("//dock_bars")
    if ($dockBarsNode) {
        $existingBar = $dockBarsNode.SelectSingleNode("dock_bar[@guid='$pluginGuid']")
        if ($existingBar) {
            $dockBarsNode.RemoveChild($existingBar) | Out-Null
        }

        $newBar = $cDoc.CreateElement("dock_bar")
        $newBar.SetAttribute("guid", $pluginGuid)
        $newBar.SetAttribute("source_group_file", $pluginGuid)
        $newBar.SetAttribute("source_group", $pluginGuid)
        $newBar.InnerXml = @"
        <placement dock_location="Floating" recent_dock_location="Floating" dock_band_size="-1,47" dock_band_item_size="1,-1" docked_placement="1,1" float_point="250,150" float_size="520,68" visible="True" />
        <tabs name="Shalik Furniture" selected_item="$pluginGuid" display_style="ControlOnly">
          <name>
            <locale_1033>Shalik Furniture</locale_1033>
          </name>
          <tool_bar guid="$pluginGuid" file="$pluginGuid" side_bar_file="$pluginGuid" />
        </tabs>
"@
        $dockBarsNode.AppendChild($newBar) | Out-Null
        Write-Host "   Added floating dock_bar entry."
    }

    $cDoc.Save($containersXmlPath)
    Write-Host "   Saved containers.xml."
}

Write-Host "4. Registering command aliases..."
& powershell.exe -ExecutionPolicy Bypass -File (Join-Path $root "installer\register_furniture_plugin.ps1") -InstallDir $pkgDir

Write-Host "`nDeployment completed successfully!"
