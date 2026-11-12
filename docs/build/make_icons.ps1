# Génère les icônes EyeControl à partir du logo officiel (assets/logo.png, 1536x1024).
#   assets/icon-512.png, assets/icon-256.png, assets/icon.ico (PNG 256/128/64/48/32/16)
# Utilise System.Drawing (Pillow est bloqué par Smart App Control sur ce poste).
param([string]$Root = (Resolve-Path "$PSScriptRoot\..\..").Path)

Add-Type -AssemblyName System.Drawing
$assets = Join-Path $Root "assets"
$logo = [System.Drawing.Image]::FromFile((Join-Path $assets "logo.png"))

# Zone de l'œil + écran (sans le texte « EyeControl »), posée au centre d'un carré noir.
$crop = New-Object System.Drawing.Rectangle 360, 185, 810, 460
$side = 810
$square = New-Object System.Drawing.Bitmap $side, $side
$g = [System.Drawing.Graphics]::FromImage($square)
$g.Clear([System.Drawing.Color]::Black)
$g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
$top = [int](($side - $crop.Height) / 2)
$dest = New-Object System.Drawing.Rectangle 0, $top, $crop.Width, $crop.Height
$g.DrawImage($logo, $dest, $crop, [System.Drawing.GraphicsUnit]::Pixel)
$g.Dispose()

function Resize([System.Drawing.Image]$img, [int]$size) {
    $bmp = New-Object System.Drawing.Bitmap $size, $size
    $gr = [System.Drawing.Graphics]::FromImage($bmp)
    $gr.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $gr.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::HighQuality
    $gr.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
    $gr.DrawImage($img, 0, 0, $size, $size)
    $gr.Dispose()
    return $bmp
}

(Resize $square 512).Save((Join-Path $assets "icon-512.png"), [System.Drawing.Imaging.ImageFormat]::Png)
(Resize $square 256).Save((Join-Path $assets "icon-256.png"), [System.Drawing.Imaging.ImageFormat]::Png)

# ICO multi-tailles avec images PNG intégrées (format accepté par Windows Vista et suivants).
$sizes = 256, 128, 64, 48, 32, 16
$pngs = foreach ($s in $sizes) {
    $ms = New-Object System.IO.MemoryStream
    (Resize $square $s).Save($ms, [System.Drawing.Imaging.ImageFormat]::Png)
    , $ms.ToArray()
}
$out = New-Object System.IO.MemoryStream
$w = New-Object System.IO.BinaryWriter $out
$w.Write([UInt16]0); $w.Write([UInt16]1); $w.Write([UInt16]$sizes.Count)
$offset = 6 + 16 * $sizes.Count
for ($i = 0; $i -lt $sizes.Count; $i++) {
    $s = $sizes[$i]; $len = $pngs[$i].Length
    $w.Write([byte]($(if ($s -ge 256) { 0 } else { $s }))); $w.Write([byte]($(if ($s -ge 256) { 0 } else { $s })))
    $w.Write([byte]0); $w.Write([byte]0); $w.Write([UInt16]1); $w.Write([UInt16]32)
    $w.Write([UInt32]$len); $w.Write([UInt32]$offset)
    $offset += $len
}
foreach ($p in $pngs) { $w.Write($p) }
$w.Flush()
[System.IO.File]::WriteAllBytes((Join-Path $assets "icon.ico"), $out.ToArray())
$logo.Dispose(); $square.Dispose()
Get-ChildItem $assets | Select-Object Name, Length
