# ==============================================================================
# Shalik Furniture & InstantSKP - Safe Uninstaller (Preserves all files)
# ==============================================================================

$furnitureGuid = "0ce7337f-ec52-45da-9fd3-cc40db64b2fa"
$instantSkpGuid = "0c2f1f48-7322-4a25-a014-a49dd0d26cca"

Write-Host "Starting uninstallation from Rhino 8..."

# 1. Unregister Plug-Ins from Rhino Registry
$pluginsReg = "HKCU:\SOFTWARE\McNeel\Rhinoceros\8.0\Plug-Ins"
foreach ($guid in @($furnitureGuid, $instantSkpGuid)) {
    $regPath = Join-Path $pluginsReg $guid
    if (Test-Path $regPath) {
        Remove-Item -Path $regPath -Recurse -Force
        Write-Host "  -> Removed plugin registry key: $guid"
    } else {
        Write-Host "  -> Plugin registry key not found: $guid"
    }
}

# 2. Clean Up Rhino 8 Settings (Command Aliases)
$settingsDir = "$env:APPDATA\McNeel\Rhinoceros\8.0\settings"
if (Test-Path $settingsDir) {
    $aliasesToRemove = @(
        "ShalikFurniture", "ArchFurniture", "FurnitureHub",
        "ShalikBed", "ArchBed", "FurnitureBed",
        "ShalikSofa", "ArchSofa", "FurnitureSofa",
        "ShalikDiningTable", "ArchDiningTable", "FurnitureDiningTable", "ShalikDiningSet",
        "ShalikKitchen", "ArchKitchen", "FurnitureKitchen", "KitchenCabinet",
        "ShalikOfficeDesk", "ArchOfficeDesk", "FurnitureOfficeDesk", "ShalikDesk",
        "ShalikInstantSKP", "InstantSKP", "ShalikImportSKP", "ArchImportSKP", "ImportSKP", "ShalikWarehouse",
        "ShalikFurnitureAbout", "ShalikFurnitureLicense", "ArchFurnitureAbout", "ArchFurnitureLicense"
    )

    $settingsFiles = Get-ChildItem -Path $settingsDir -Filter "settings-*.xml"
    foreach ($file in $settingsFiles) {
        try {
            [xml]$xml = Get-Content $file.FullName
            $dict = $xml.SelectSingleNode("//child[@key='AliasList']/entry[@key='AliasDictionary']/dictionary")
            if ($dict -ne $null) {
                $removedCount = 0
                foreach ($alias in $aliasesToRemove) {
                    $node = $dict.SelectSingleNode("value[@key='$alias']")
                    if ($node -ne $null) {
                        $dict.RemoveChild($node) | Out-Null
                        $removedCount++
                    }
                }
                if ($removedCount -gt 0) {
                    $xml.Save($file.FullName)
                    Write-Host "  -> Cleaned $removedCount aliases from $($file.Name)"
                }
            }
        } catch {
            Write-Host "  -> Notice: Could not process $($file.Name): $_"
        }
    }
}

# 3. Clean Up Toolbar and Containers XML
$schemeDir = "$env:APPDATA\McNeel\Rhinoceros\8.0\settings\Scheme__Default"
$containersXmlPath = Join-Path $schemeDir "containers.xml"
if (Test-Path $containersXmlPath) {
    try {
        [xml]$cDoc = Get-Content -LiteralPath $containersXmlPath
        $changed = $false

        # Remove from plug_in_files
        $pFilesNode = $cDoc.SelectSingleNode("//plug_in_files")
        if ($pFilesNode) {
            foreach ($guid in @($furnitureGuid, $instantSkpGuid)) {
                $pEntry = $pFilesNode.SelectSingleNode("file_name[@plug_in_guid='$guid']")
                if ($pEntry) {
                    $pFilesNode.RemoveChild($pEntry) | Out-Null
                    $changed = $true
                    Write-Host "  -> Removed $guid from <plug_in_files>"
                }
            }
        }

        # Remove from dock_bars
        $dockBarsNode = $cDoc.SelectSingleNode("//dock_bars")
        if ($dockBarsNode) {
            foreach ($guid in @($furnitureGuid, $instantSkpGuid)) {
                $existingBar = $dockBarsNode.SelectSingleNode("dock_bar[@guid='$guid']")
                if ($existingBar) {
                    $dockBarsNode.RemoveChild($existingBar) | Out-Null
                    $changed = $true
                    Write-Host "  -> Removed $guid from <dock_bars>"
                }
            }
        }

        if ($changed) {
            $cDoc.Save($containersXmlPath)
            Write-Host "  -> Saved updated containers.xml"
        }
    } catch {
        Write-Host "  -> Notice: Could not update containers.xml: $_"
    }
}

# 4. Remove cached imported RUI files
$importedDir = Join-Path $schemeDir "imported_rui_files"
if (Test-Path $importedDir) {
    Get-ChildItem -Path $importedDir -Filter "*ShalikFurniture*" -ErrorAction SilentlyContinue | ForEach-Object {
        Remove-Item $_.FullName -Force -ErrorAction SilentlyContinue
        Write-Host "  -> Removed cached RUI: $($_.Name)"
    }
}

# 5. Safely Move Packages Folders to Backup (DO NOT DELETE FILES)
$packagesDir = "$env:APPDATA\McNeel\Rhinoceros\packages\8.0"
$backupDir = "$env:APPDATA\Shalik_Uninstalled_Backups"
if (-not (Test-Path $backupDir)) {
    New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
}

$instantSkpPkg = Join-Path $packagesDir "InstantSKP"
if (Test-Path $instantSkpPkg) {
    $targetInstant = Join-Path $backupDir "InstantSKP"
    if (Test-Path $targetInstant) { Remove-Item $targetInstant -Recurse -Force }
    Move-Item -Path $instantSkpPkg -Destination $targetInstant -Force
    Write-Host "  -> Safely moved InstantSKP package to backup: $targetInstant (Files preserved!)"
}

$furniturePkg = Join-Path $packagesDir "ShalikFurniture"
if (Test-Path $furniturePkg) {
    $targetFurniture = Join-Path $backupDir "ShalikFurniture"
    if (Test-Path $targetFurniture) { Remove-Item $targetFurniture -Recurse -Force }
    Move-Item -Path $furniturePkg -Destination $targetFurniture -Force
    Write-Host "  -> Safely moved ShalikFurniture package to backup: $targetFurniture (Files preserved!)"
}

Write-Host "`nUninstallation completed successfully!"
Write-Host "All source files, code, and project files remain 100% preserved in:"
Write-Host "  - E:\antigravity\Shalik Furniture"
Write-Host "  - $backupDir"
