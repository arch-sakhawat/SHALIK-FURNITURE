# ==============================================================================
# Shalik Furniture - Unregister Command Aliases in Rhino 8
# ==============================================================================

$settingsDir = "$env:APPDATA\McNeel\Rhinoceros\8.0\settings"
if (Test-Path $settingsDir) {
    $settingsFiles = Get-ChildItem -Path $settingsDir -Filter "settings-*.xml"
    $aliases = @(
        "ShalikFurniture", "ArchFurniture", "FurnitureHub",
        "ShalikBed", "ArchBed", "FurnitureBed",
        "ShalikSofa", "ArchSofa", "FurnitureSofa",
        "ShalikDiningTable", "ArchDiningTable", "FurnitureDiningTable", "ShalikDiningSet",
        "ShalikKitchen", "ArchKitchen", "FurnitureKitchen",
        "ShalikOfficeDesk", "ArchOfficeDesk", "FurnitureOfficeDesk", "ShalikDesk",
        "ShalikInstantSKP", "ShalikFurnitureAbout", "ShalikFurnitureLicense"
    )

    foreach ($file in $settingsFiles) {
        try {
            [xml]$xml = Get-Content $file.FullName
            $dict = $xml.SelectSingleNode("//child[@key='AliasList']/entry[@key='AliasDictionary']/dictionary")
            if ($dict -ne $null) {
                foreach ($alias in $aliases) {
                    $node = $dict.SelectSingleNode("value[@key='$alias']")
                    if ($node -ne $null) {
                        $dict.RemoveChild($node) | Out-Null
                    }
                }
                $xml.Save($file.FullName)
            }
        } catch { }
    }
}
