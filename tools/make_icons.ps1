# ==============================================================================
# Shalik Furniture Modeling Suite - Icon Processor & Generator
# Loads IconBuilder.dll, extracts clean alpha transparency, scales to 24, 32, 48, 64, 128, 256
# Generates multi-res ICO for setup, icon.png for Yak, and embedded SVG/PNG assets.
# ==============================================================================

Add-Type -AssemblyName System.Drawing

$root = "E:\antigravity\Shalik Furniture"
$iconDir = Join-Path $root "icons"
$sourceDir = Join-Path $iconDir "source"
$builderDll = Join-Path $root "tools\IconBuilder.dll"

[System.Reflection.Assembly]::LoadFrom($builderDll) | Out-Null

$tools = @{
    "Bed"             = "Bed_source.jpg"
    "Sofa"            = "Sofa_source.jpg"
    "DiningTable"     = "DiningTable_source.jpg"
    "Kitchen"         = "Kitchen_source.jpg"
    "OfficeDesk"      = "OfficeDesk_source.jpg"
    "ShalikFurniture" = "ShalikFurniture_source.jpg"
}

$sizes = @(24, 32, 48, 64, 128, 256)

Write-Host "Processing tool icons with transparency & multi-resolution scaling..."

foreach ($item in $tools.GetEnumerator()) {
    $toolName = $item.Key
    $srcFileName = $item.Value
    $srcPath = Join-Path $sourceDir $srcFileName

    if (-not (Test-Path $srcPath)) {
        Write-Warning "Source not found: $srcPath"
        continue
    }

    $rawImg = [System.Drawing.Bitmap]::FromFile($srcPath)
    # Remove white background smoothly
    $transImg = [IconBuilder]::RemoveWhiteBackground($rawImg, 225, 248)
    $rawImg.Dispose()

    foreach ($sz in $sizes) {
        $bmp = New-Object System.Drawing.Bitmap($sz, $sz, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
        $g = [System.Drawing.Graphics]::FromImage($bmp)
        $g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
        $g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::HighQuality
        $g.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
        $g.CompositingQuality = [System.Drawing.Drawing2D.CompositingQuality]::HighQuality
        $g.Clear([System.Drawing.Color]::Transparent)

        $pad = [int]($sz * 0.04)
        $targetSize = $sz - ($pad * 2)
        $g.DrawImage($transImg, $pad, $pad, $targetSize, $targetSize)
        $g.Dispose()

        $outPrimary = Join-Path $iconDir "${toolName}_${sz}.png"
        $outShalik  = Join-Path $iconDir "Shalik${toolName}_${sz}.png"
        $outArch    = Join-Path $iconDir "Arch${toolName}_${sz}.png"

        $bmp.Save($outPrimary, [System.Drawing.Imaging.ImageFormat]::Png)
        $bmp.Save($outShalik, [System.Drawing.Imaging.ImageFormat]::Png)
        $bmp.Save($outArch, [System.Drawing.Imaging.ImageFormat]::Png)
        $bmp.Dispose()
    }

    $transImg.Dispose()
    Write-Host "  -> Successfully processed: $toolName"
}

# Generate ShalikAbout icon
Write-Host "Generating About & License badge icons..."
foreach ($sz in $sizes) {
    $badgeBmp = [IconBuilder]::CreateAboutBadge($sz)
    $p1 = Join-Path $iconDir "ShalikAbout_${sz}.png"
    $p2 = Join-Path $iconDir "ArchAbout_${sz}.png"
    $p3 = Join-Path $iconDir "About_${sz}.png"
    $badgeBmp.Save($p1, [System.Drawing.Imaging.ImageFormat]::Png)
    $badgeBmp.Save($p2, [System.Drawing.Imaging.ImageFormat]::Png)
    $badgeBmp.Save($p3, [System.Drawing.Imaging.ImageFormat]::Png)
    $badgeBmp.Dispose()
}

# Generate InstantSKP icons
Write-Host "Generating InstantSKP dark-red icons..."
foreach ($sz in $sizes) {
    $skpBmp = [IconBuilder]::CreateInstantSKPIcon($sz)
    $p1 = Join-Path $iconDir "InstantSKP_${sz}.png"
    $p2 = Join-Path $iconDir "ShalikInstantSKP_${sz}.png"
    $p3 = Join-Path $iconDir "ArchInstantSKP_${sz}.png"
    $p4 = Join-Path $iconDir "SKP_${sz}.png"
    $skpBmp.Save($p1, [System.Drawing.Imaging.ImageFormat]::Png)
    $skpBmp.Save($p2, [System.Drawing.Imaging.ImageFormat]::Png)
    $skpBmp.Save($p3, [System.Drawing.Imaging.ImageFormat]::Png)
    $skpBmp.Save($p4, [System.Drawing.Imaging.ImageFormat]::Png)
    $skpBmp.Dispose()
}

# Generate 256x256 icon.png for Yak package
$logo256 = Join-Path $iconDir "ShalikFurniture_256.png"
if (Test-Path $logo256) {
    Copy-Item $logo256 (Join-Path $root "icon.png") -Force
    Write-Host "Created Yak icon.png at root."
}

# Generate Windows Setup ICO (multi-res 16, 24, 32, 48, 64, 128, 256)
Write-Host "Generating Windows setup.ico..."
$icoSizes = @(16, 24, 32, 48, 64, 128, 256)
$masterImg = [System.Drawing.Bitmap]::FromFile((Join-Path $iconDir "ShalikFurniture_256.png"))

$master512 = New-Object System.Drawing.Bitmap(512, 512, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
$g512 = [System.Drawing.Graphics]::FromImage($master512)
$g512.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
$g512.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
$g512.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
$g512.Clear([System.Drawing.Color]::Transparent)

# Rounded dark red badge
$rect = New-Object System.Drawing.Rectangle(12, 12, 488, 488)
$rad = 90
$path = New-Object System.Drawing.Drawing2D.GraphicsPath
$path.AddArc($rect.X, $rect.Y, $rad, $rad, 180, 90)
$path.AddArc($rect.X + $rect.Width - $rad, $rect.Y, $rad, $rad, 270, 90)
$path.AddArc($rect.X + $rect.Width - $rad, $rect.Y + $rect.Height - $rad, $rad, $rad, 0, 90)
$path.AddArc($rect.X, $rect.Y + $rect.Height - $rad, $rad, $rad, 90, 90)
$path.CloseFigure()

$brush = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(255, 139, 0, 0)) # Deep Dark Red
$g512.FillPath($brush, $path)

$goldPen = New-Object System.Drawing.Pen([System.Drawing.Color]::FromArgb(220, 220, 180, 100), 8)
$g512.DrawPath($goldPen, $path)

$g512.DrawImage($masterImg, 35, 35, 442, 442)
$g512.Dispose()
$masterImg.Dispose()
$brush.Dispose()
$goldPen.Dispose()
$path.Dispose()

$targetIco = Join-Path $iconDir "setup.ico"
$targetIcoRoot = Join-Path $root "setup.ico"

$imageEntries = @()
$imageDataBlocks = @()

foreach ($sz in $icoSizes) {
    $bmp = New-Object System.Drawing.Bitmap($sz, $sz, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
    $bg = [System.Drawing.Graphics]::FromImage($bmp)
    $bg.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $bg.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $bg.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
    $bg.DrawImage($master512, 0, 0, $sz, $sz)
    $bg.Dispose()

    $ms = New-Object System.IO.MemoryStream
    $bmp.Save($ms, [System.Drawing.Imaging.ImageFormat]::Png)
    $pngBytes = $ms.ToArray()
    $ms.Dispose()
    $bmp.Dispose()

    $imageDataBlocks += ,$pngBytes
    $imageEntries += ,@{
        Width = if ($sz -eq 256) { 0 } else { $sz }
        Height = if ($sz -eq 256) { 0 } else { $sz }
        ColorCount = 0
        Planes = 1
        BitCount = 32
        BytesInRes = $pngBytes.Length
    }
}

$master512.Dispose()

$icoFs = [System.IO.File]::Create($targetIco)
$icoBw = New-Object System.IO.BinaryWriter($icoFs)

$icoBw.Write([uint16]0)
$icoBw.Write([uint16]1)
$icoBw.Write([uint16]$imageEntries.Count)

$offset = 6 + ($imageEntries.Count * 16)

for ($i = 0; $i -lt $imageEntries.Count; $i++) {
    $e = $imageEntries[$i]
    $icoBw.Write([byte]$e.Width)
    $icoBw.Write([byte]$e.Height)
    $icoBw.Write([byte]$e.ColorCount)
    $icoBw.Write([byte]0)
    $icoBw.Write([uint16]$e.Planes)
    $icoBw.Write([uint16]$e.BitCount)
    $icoBw.Write([uint32]$e.BytesInRes)
    $icoBw.Write([uint32]$offset)

    $offset += $e.BytesInRes
}

for ($i = 0; $i -lt $imageDataBlocks.Count; $i++) {
    $icoBw.Write($imageDataBlocks[$i])
}

$icoBw.Flush()
$icoBw.Close()
$icoFs.Close()

Copy-Item $targetIco $targetIcoRoot -Force
Write-Host "Created setup.ico: $((Get-Item $targetIco).Length) bytes"
Write-Host "All icons generated successfully!"
