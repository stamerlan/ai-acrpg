# Key the magenta background out of the generated HUD icons.
#
# Reads Art/UI/HUD/Source/<Name>_gen.png (Nano Banana, 1024 px on #FF00FF),
# makes the magenta transparent (edge pixels take the outline color),
# crops to the picture and scales it to the HUD height. Writes
# Art/UI/HUD/T_HUD_<Name>.png and T_HUD_<Name>Empty.png (a white silhouette
# for the empty slots). Run: powershell -File key_icons.ps1
$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Drawing
Add-Type -ReferencedAssemblies System.Drawing -TypeDefinition @"
using System;
using System.Drawing;
using System.Drawing.Imaging;
using System.Runtime.InteropServices;
public static class Keyer {
    // Magenta-ness of a pixel: min(r, b) - g. The background is about
    // 255, the dark outline about 0. Alpha falls from 1 to 0 between lo
    // and hi; partly keyed pixels take the outline color.
    public static Bitmap Key(Bitmap src, int lo, int hi, Color edge) {
        int w = src.Width, h = src.Height;
        var dst = new Bitmap(w, h, PixelFormat.Format32bppArgb);
        var r = new Rectangle(0, 0, w, h);
        var sd = src.LockBits(r, ImageLockMode.ReadOnly,
            PixelFormat.Format32bppArgb);
        var dd = dst.LockBits(r, ImageLockMode.WriteOnly,
            PixelFormat.Format32bppArgb);
        var px = new byte[w * h * 4];
        Marshal.Copy(sd.Scan0, px, 0, px.Length);
        for (int i = 0; i < px.Length; i += 4) {
            int b = px[i], g = px[i + 1], rr = px[i + 2];
            int m = Math.Min(rr, b) - g;
            double a = 1.0 - (m - lo) / (double)(hi - lo);
            a = Math.Max(0.0, Math.Min(1.0, a));
            if (a < 1.0) {
                px[i] = edge.B; px[i + 1] = edge.G; px[i + 2] = edge.R;
            }
            px[i + 3] = (byte)Math.Round(a * 255);
        }
        Marshal.Copy(px, 0, dd.Scan0, px.Length);
        src.UnlockBits(sd);
        dst.UnlockBits(dd);
        return dst;
    }

    // The same picture as a flat white silhouette (alpha kept), for the
    // empty slots: tinted gray in the HUD it shows only the shape.
    public static Bitmap Silhouette(Bitmap src) {
        int w = src.Width, h = src.Height;
        var dst = new Bitmap(w, h, PixelFormat.Format32bppArgb);
        var r = new Rectangle(0, 0, w, h);
        var sd = src.LockBits(r, ImageLockMode.ReadOnly,
            PixelFormat.Format32bppArgb);
        var dd = dst.LockBits(r, ImageLockMode.WriteOnly,
            PixelFormat.Format32bppArgb);
        var px = new byte[w * h * 4];
        Marshal.Copy(sd.Scan0, px, 0, px.Length);
        for (int i = 0; i < px.Length; i += 4)
            px[i] = px[i + 1] = px[i + 2] = 255;
        Marshal.Copy(px, 0, dd.Scan0, px.Length);
        src.UnlockBits(sd);
        dst.UnlockBits(dd);
        return dst;
    }

    public static Rectangle Bounds(Bitmap bmp) {
        int x0 = bmp.Width, y0 = bmp.Height, x1 = -1, y1 = -1;
        for (int y = 0; y < bmp.Height; y++)
            for (int x = 0; x < bmp.Width; x++)
                if (bmp.GetPixel(x, y).A > 8) {
                    x0 = Math.Min(x0, x); y0 = Math.Min(y0, y);
                    x1 = Math.Max(x1, x); y1 = Math.Max(y1, y);
                }
        return new Rectangle(x0, y0, x1 - x0 + 1, y1 - y0 + 1);
    }
}
"@

$hud = Join-Path $PSScriptRoot "..\HUD"
$edge = [System.Drawing.ColorTranslator]::FromHtml("#1E1610")
# Name, target height in px (the HUD draws them at about half that).
$icons = @(@("Shell", 208), @("Corn", 160))
foreach ($ic in $icons) {
    $name = $ic[0]; $height = $ic[1]
    $src = New-Object System.Drawing.Bitmap (
        Join-Path $hud "Source\$($name)_gen.png")
    $keyed = [Keyer]::Key($src, 60, 200, $edge)
    $b = [Keyer]::Bounds($keyed)
    $pad = 6
    $crop = New-Object System.Drawing.Rectangle ($b.X - $pad), ($b.Y - $pad),
        ($b.Width + 2 * $pad), ($b.Height + 2 * $pad)
    $cut = $keyed.Clone($crop, $keyed.PixelFormat)
    $width = [int][Math]::Round($cut.Width * $height / $cut.Height)
    $out = New-Object System.Drawing.Bitmap $width, $height
    $g = [System.Drawing.Graphics]::FromImage($out)
    $g.InterpolationMode = "HighQualityBicubic"
    $g.PixelOffsetMode = "HighQuality"
    $g.DrawImage($cut, 0, 0, $width, $height)
    $g.Dispose()
    $path = Join-Path $hud "T_HUD_$name.png"
    $out.Save($path, [System.Drawing.Imaging.ImageFormat]::Png)
    $sil = [Keyer]::Silhouette($out)
    $sil.Save((Join-Path $hud "T_HUD_$($name)Empty.png"),
        [System.Drawing.Imaging.ImageFormat]::Png)
    "$path $($width)x$height"
    $src.Dispose(); $keyed.Dispose(); $cut.Dispose(); $out.Dispose()
    $sil.Dispose()
}
