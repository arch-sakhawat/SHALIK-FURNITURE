# ==============================================================================
# Shalik Furniture - Register Plugin & Command Aliases in Rhino 8
# ==============================================================================

param(
    [string]$InstallDir = ""
)

if ([string]::IsNullOrEmpty($InstallDir)) {
    $InstallDir = "$env:APPDATA\McNeel\Rhinoceros\packages\8.0\ShalikFurniture\1.0.0"
    if (-not (Test-Path $InstallDir)) {
        $InstallDir = "$env:APPDATA\ShalikFurniture"
    }
}

Write-Host "Registering Shalik Furniture from: $InstallDir"

$settingsDir = "$env:APPDATA\McNeel\Rhinoceros\8.0\settings"
if (Test-Path $settingsDir) {
    $settingsFiles = Get-ChildItem -Path $settingsDir -Filter "settings-*.xml"

    $toolMap = @{
        "ShalikFurniture"        = "ShalikFurniture.py"
        "ArchFurniture"          = "ShalikFurniture.py"
        "FurnitureHub"           = "ShalikFurniture.py"
        "ShalikBed"              = "ShalikBed.py"
        "ArchBed"                = "ShalikBed.py"
        "FurnitureBed"           = "ShalikBed.py"
        "Bed"                    = "ShalikBed.py"
        "ShalikSofa"             = "ShalikSofa.py"
        "ArchSofa"               = "ShalikSofa.py"
        "FurnitureSofa"          = "ShalikSofa.py"
        "Sofa"                   = "ShalikSofa.py"
        "ShalikDiningTable"      = "ShalikDiningTable.py"
        "ArchDiningTable"        = "ShalikDiningTable.py"
        "FurnitureDiningTable"   = "ShalikDiningTable.py"
        "ShalikDiningSet"        = "ShalikDiningTable.py"
        "DiningTable"            = "ShalikDiningTable.py"
        "DiningSet"              = "ShalikDiningTable.py"
        "ShalikKitchen"          = "ShalikKitchen.py"
        "ArchKitchen"            = "ShalikKitchen.py"
        "FurnitureKitchen"       = "ShalikKitchen.py"
        "KitchenCabinet"         = "ShalikKitchen.py"
        "Kitchen"                = "ShalikKitchen.py"
        "ShalikOfficeDesk"       = "ShalikOfficeDesk.py"
        "ArchOfficeDesk"         = "ShalikOfficeDesk.py"
        "FurnitureOfficeDesk"    = "ShalikOfficeDesk.py"
        "ShalikDesk"             = "ShalikOfficeDesk.py"
        "OfficeDesk"             = "ShalikOfficeDesk.py"
        "Desk"                   = "ShalikOfficeDesk.py"
        "ShalikImportSKP"        = "ShalikImportSKP.py"
        "ArchImportSKP"          = "ShalikImportSKP.py"
        "ImportSKP"              = "ShalikImportSKP.py"
        "InstantSKP"             = "ShalikImportSKP.py"
        "ShalikInstantSKP"       = "ShalikImportSKP.py"
        "ShalikWarehouse"        = "ShalikImportSKP.py"
        "ShalikFurnitureAbout"   = "ShalikAbout.py"
        "ShalikFurnitureLicense" = "ShalikAbout.py"
        "ArchFurnitureAbout"     = "ShalikAbout.py"
        "ArchFurnitureLicense"   = "ShalikAbout.py"
    }

    foreach ($file in $settingsFiles) {
        try {
            [xml]$xml = Get-Content $file.FullName
            $dict = $xml.SelectSingleNode("//child[@key='AliasList']/entry[@key='AliasDictionary']/dictionary")
            if ($dict -ne $null) {
                foreach ($entry in $toolMap.GetEnumerator()) {
                    $aliasName = $entry.Key
                    $scriptName = $entry.Value
                    
                    $scriptPath = Join-Path $InstallDir $scriptName
                    if (-not (Test-Path $scriptPath)) {
                        $scriptPath = Join-Path $InstallDir "commands\$scriptName"
                    }
                    if (-not (Test-Path $scriptPath)) {
                        $scriptPath = Join-Path $InstallDir "Code\$scriptName"
                    }

                    $cleanPath = $scriptPath.Replace('\', '/')
                    $macro = "! _-RunPythonScript `"$cleanPath`""

                    $node = $dict.SelectSingleNode("value[@key='$aliasName']")
                    if ($node -eq $null) {
                        $node = $xml.CreateElement("value")
                        $node.SetAttribute("key", $aliasName)
                        $dict.AppendChild($node) | Out-Null
                    }
                    $node.InnerText = $macro
                }
                $xml.Save($file.FullName)
                Write-Host "Updated aliases in $($file.Name)"
            }
        } catch {
            Write-Host "Notice: Skipped $($file.Name): $_"
        }
    }
}

Write-Host "Registration completed successfully."
