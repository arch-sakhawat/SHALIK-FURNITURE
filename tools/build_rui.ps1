# ==============================================================================
# Shalik Furniture Suite - Rhino Toolbar Builder (.rui)
# Compatible with Rhino 8 and Rhino 7
# Embedded SVG Data URI and High-Res PNG Bitmaps (48px and 128px)
# ==============================================================================

param()

$root = "E:\antigravity\Shalik Furniture"
$iconDir = Join-Path $root "icons"
$outFile = Join-Path $root "ShalikFurniture.rui"
$distFile = Join-Path $root "dist\ShalikFurniture.rui"

$pluginGuid = "0ce7337f-ec52-45da-9fd3-cc40db64b2fa"

function Escape-Xml([string]$str) {
    if ([string]::IsNullOrEmpty($str)) { return "" }
    return [System.Security.SecurityElement]::Escape($str)
}

function Get-Base64([string]$path) {
    if (Test-Path $path) {
        $bytes = [System.IO.File]::ReadAllBytes($path)
        return [Convert]::ToBase64String($bytes)
    }
    return ""
}

$tools = @(
    # 1. Master Hub Launcher
    @{ 
        id = "f0000001-ec52-45da-9fd3-cc40db64b2fa"; 
        name = "ShalikFurniture";      
        label = "Furniture Hub";      
        tip = "Shalik Furniture Master Hub & All-in-One Generator Launcher";    
        cmd = "! _ShalikFurniture";      
        icon = "ShalikFurniture";
        right_id = "f0000002-ec52-45da-9fd3-cc40db64b2fa";
        right_label = "Arch Furniture Hub";
        right_tip = "Shalik Furniture Master Hub & All-in-One Generator Launcher";
        right_cmd = "! _ArchFurniture"
    },
    # 2. Bed Generator
    @{ 
        id = "b0000001-ec52-45da-9fd3-cc40db64b2fa"; 
        name = "ShalikBed"; 
        label = "Bed Generator";        
        tip = "Modern Architectural Bed & Bedroom Suite Generator (Shalik Furniture)"; 
        cmd = "! _ShalikBed"; 
        icon = "ShalikBed";
        right_id = "b0000002-ec52-45da-9fd3-cc40db64b2fa";
        right_label = "Select/Edit Bed";
        right_tip = "Select or edit an existing modern architectural bed in place";
        right_cmd = "! _ArchBed"
    },
    # 3. Sofa Generator
    @{ 
        id = "s0000001-ec52-45da-9fd3-cc40db64b2fa"; 
        name = "ShalikSofa";       
        label = "Sofa Generator";       
        tip = "Modern Architectural Sofa & Sectional Generator (Shalik Furniture)";       
        cmd = "! _ShalikSofa";       
        icon = "ShalikSofa";
        right_id = "s0000002-ec52-45da-9fd3-cc40db64b2fa";
        right_label = "Select/Edit Sofa";
        right_tip = "Select or edit an existing modern architectural sofa in place";
        right_cmd = "! _ArchSofa"
    },
    # 4. Dining Table & Chairs
    @{ 
        id = "d0000001-ec52-45da-9fd3-cc40db64b2fa"; 
        name = "ShalikDiningTable";       
        label = "Dining Set";       
        tip = "Modern Parametric Dining Table & Seating Set Generator (Shalik Furniture)";       
        cmd = "! _ShalikDiningTable";       
        icon = "ShalikDiningTable";
        right_id = "d0000002-ec52-45da-9fd3-cc40db64b2fa";
        right_label = "Dining Table & Chairs";
        right_tip = "Parametric Dining Table & Seating Set Generator (Shalik Furniture)";
        right_cmd = "! _ArchDiningTable"
    },
    # 5. Kitchen Cabinets & Millwork
    @{ 
        id = "k0000001-ec52-45da-9fd3-cc40db64b2fa"; 
        name = "ShalikKitchen";    
        label = "Kitchen Millwork";    
        tip = "Modern Ergonomic Kitchen Cabinet & Warm LED Lighting Generator (Shalik Furniture)";        
        cmd = "! _ShalikKitchen";    
        icon = "ShalikKitchen";
        right_id = "k0000002-ec52-45da-9fd3-cc40db64b2fa";
        right_label = "Select/Edit Kitchen";
        right_tip = "Select or edit an existing kitchen cabinet run in place";
        right_cmd = "! _ArchKitchen"
    },
    # 6. Office Desk & Chair
    @{ 
        id = "o0000001-ec52-45da-9fd3-cc40db64b2fa"; 
        name = "ShalikOfficeDesk";  
        label = "Office Desk";  
        tip = "Modern Parametric Office Workstation & Ergonomic Chair Generator (Shalik Furniture)";      
        cmd = "! _ShalikOfficeDesk";  
        icon = "ShalikOfficeDesk";
        right_id = "o0000002-ec52-45da-9fd3-cc40db64b2fa";
        right_label = "Workstation & Chair";
        right_tip = "Parametric Office Desk & Ergonomic Chair Generator (Shalik Furniture)";
        right_cmd = "! _ArchOfficeDesk"
    },
    # 7. InstantSKP & 3D Warehouse (Integration)
    @{ 
        id = "90000001-ec52-45da-9fd3-cc40db64b2fa"; 
        name = "InstantSKP";   
        label = "Instant SKP Warehouse";   
        tip = "InstantSKP - Browse & Import 3D Warehouse & SketchUp Furniture Models directly in Rhino"; 
        cmd = "! _InstantSKP";   
        icon = "InstantSKP";
        right_id = "90000002-ec52-45da-9fd3-cc40db64b2fa";
        right_label = "Import Local SKP";
        right_tip = "Shalik Smart SKP Furniture Importer & Local Library Browser";
        right_cmd = "! _ShalikImportSKP"
    },
    # 8. About & Licence (ALWAYS LAST)
    @{ 
        id = "a0000001-ec52-45da-9fd3-cc40db64b2fa"; 
        name = "ShalikAbout";   
        label = "About & Licence";   
        tip = "Licence Information & Credits - Sakhawat Hosen Sumon"; 
        cmd = "! _ShalikFurnitureAbout";   
        icon = "ShalikAbout";
        right_id = "a0000002-ec52-45da-9fd3-cc40db64b2fa";
        right_label = "Licence Information";
        right_tip = "Developer & Licence Holder: Sakhawat Hosen Sumon";
        right_cmd = "! _ShalikFurnitureLicense"
    }
)

$rui = New-Object System.Text.StringBuilder
[void]$rui.AppendLine('<?xml version="1.0" encoding="utf-8"?>')
[void]$rui.AppendLine("<RhinoUI guid=""$pluginGuid"" plug_in_guid=""$pluginGuid"" major_ver=""5"" minor_ver=""0"" localize=""False"" default_language_id=""1033"">")
[void]$rui.AppendLine('  <extend_rhino_menus />')
[void]$rui.AppendLine('  <menus />')
[void]$rui.AppendLine('  <tool_bar_groups>')
[void]$rui.AppendLine("    <tool_bar_group guid=""$pluginGuid"" dock_bar_guid32=""$pluginGuid"" dock_bar_guid64=""$pluginGuid"" active_tool_bar_group=""$pluginGuid"" single_file=""False"" hide_single_tab=""True"">")
[void]$rui.AppendLine('      <text><locale_1033>Shalik Furniture</locale_1033></text>')
[void]$rui.AppendLine('      <dock_bar_info visible="True" floating="True" />')
[void]$rui.AppendLine("      <tool_bar_group_item guid=""$pluginGuid"" major_version=""1"" minor_version=""1"">")
[void]$rui.AppendLine('        <text><locale_1033>Shalik Furniture</locale_1033></text>')
[void]$rui.AppendLine("        <tool_bar_id>$pluginGuid</tool_bar_id>")
[void]$rui.AppendLine('      </tool_bar_group_item>')
[void]$rui.AppendLine('    </tool_bar_group>')
[void]$rui.AppendLine('  </tool_bar_groups>')
[void]$rui.AppendLine('  <tool_bars>')
[void]$rui.AppendLine("    <tool_bar guid=""$pluginGuid"" bitmap_id=""$pluginGuid"" item_display_style=""control_only"">")
[void]$rui.AppendLine('      <text><locale_1033>Shalik Furniture</locale_1033></text>')

foreach ($t in $tools) {
    $itemText = Escape-Xml $t['label']
    [void]$rui.AppendLine("      <tool_bar_item guid=""$($t['id'])"" button_display_mode=""control_only"" button_style=""normal"">")
    [void]$rui.AppendLine("        <text><locale_1033>$itemText</locale_1033></text>")
    [void]$rui.AppendLine("        <left_macro_id>$($t['id'])</left_macro_id>")
    if ($t.ContainsKey('right_id') -and $t['right_id']) {
        [void]$rui.AppendLine("        <right_macro_id>$($t['right_id'])</right_macro_id>")
    }
    [void]$rui.AppendLine('      </tool_bar_item>')
}

[void]$rui.AppendLine('    </tool_bar>')
[void]$rui.AppendLine('  </tool_bars>')
[void]$rui.AppendLine('  <macros>')

foreach ($t in $tools) {
    $labelText = Escape-Xml $t['label']
    $tipText = Escape-Xml $t['tip']
    $cmdText = Escape-Xml $t['cmd']

    [void]$rui.AppendLine("    <macro_item guid=""$($t['id'])"" bitmap_id=""$($t['id'])"">")
    [void]$rui.AppendLine("      <text><locale_1033>$labelText</locale_1033></text>")
    [void]$rui.AppendLine("      <tooltip><locale_1033>$tipText</locale_1033></tooltip>")
    [void]$rui.AppendLine("      <help_text><locale_1033>$tipText</locale_1033></help_text>")
    [void]$rui.AppendLine("      <button_text><locale_1033>$labelText</locale_1033></button_text>")
    [void]$rui.AppendLine("      <menu_text><locale_1033>$labelText</locale_1033></menu_text>")
    [void]$rui.AppendLine("      <script>$cmdText</script>")
    [void]$rui.AppendLine('    </macro_item>')

    if ($t.ContainsKey('right_id') -and $t['right_id']) {
        $rLabelText = Escape-Xml $t['right_label']
        $rTipText = Escape-Xml $t['right_tip']
        $rCmdText = Escape-Xml $t['right_cmd']
        [void]$rui.AppendLine("    <macro_item guid=""$($t['right_id'])"" bitmap_id=""$($t['id'])"">")
        [void]$rui.AppendLine("      <text><locale_1033>$rLabelText</locale_1033></text>")
        [void]$rui.AppendLine("      <tooltip><locale_1033>$rTipText</locale_1033></tooltip>")
        [void]$rui.AppendLine("      <help_text><locale_1033>$rTipText</locale_1033></help_text>")
        [void]$rui.AppendLine("      <button_text><locale_1033>$rLabelText</locale_1033></button_text>")
        [void]$rui.AppendLine("      <menu_text><locale_1033>$rLabelText</locale_1033></menu_text>")
        [void]$rui.AppendLine("      <script>$rCmdText</script>")
        [void]$rui.AppendLine('    </macro_item>')
    }
}

[void]$rui.AppendLine('  </macros>')
[void]$rui.AppendLine('  <icons>')

foreach ($t in $tools) {
    $p48  = Join-Path $iconDir "$($t['icon'])_48.png"
    $p128 = Join-Path $iconDir "$($t['icon'])_128.png"
    $b48  = Get-Base64 $p48
    $b128 = Get-Base64 $p128
    
    $svgImage = "<svg viewBox=""0 0 48 48"" width=""48"" height=""48"" version=""1.1"" xmlns=""http://www.w3.org/2000/svg"" xmlns:xlink=""http://www.w3.org/1999/xlink""><image width=""48"" height=""48"" xlink:href=""data:image/png;base64,$b48"" /></svg>"
    
    [void]$rui.AppendLine("    <icon guid=""$($t['id'])"">")
    [void]$rui.AppendLine("      <light>$svgImage</light>")
    [void]$rui.AppendLine("      <dark>$svgImage</dark>")
    if ($b48) {
        [void]$rui.AppendLine("      <bitmap>$b48</bitmap>")
        [void]$rui.AppendLine("      <bitmap_large>$b128</bitmap_large>")
    }
    [void]$rui.AppendLine('    </icon>')
}

[void]$rui.AppendLine('  </icons>')
[void]$rui.AppendLine('</RhinoUI>')

[System.IO.File]::WriteAllText($outFile, $rui.ToString(), [System.Text.Encoding]::UTF8)
[System.IO.File]::WriteAllText($distFile, $rui.ToString(), [System.Text.Encoding]::UTF8)
Write-Host "ShalikFurniture.rui successfully built with 7 tools and embedded dark-red icons!"
Write-Host "File size: $((Get-Item $outFile).Length) bytes"

# Validate XML structure
try {
    $xmlDoc = New-Object System.Xml.XmlDocument
    $xmlDoc.Load($outFile)
    Write-Host "XML Validation: SUCCESS! The RUI file is fully well-formed and valid XML."
} catch {
    Write-Error "XML Validation FAILED: $_"
}
