using System;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Drawing.Imaging;

public static class IconBuilder
{
    public static Bitmap RemoveWhiteBackground(Bitmap src, int lowThresh, int highThresh)
    {
        int w = src.Width;
        int h = src.Height;
        Bitmap dest = new Bitmap(w, h, PixelFormat.Format32bppArgb);

        BitmapData srcData = src.LockBits(new Rectangle(0, 0, w, h), ImageLockMode.ReadOnly, PixelFormat.Format32bppArgb);
        BitmapData destData = dest.LockBits(new Rectangle(0, 0, w, h), ImageLockMode.WriteOnly, PixelFormat.Format32bppArgb);

        unsafe
        {
            byte* sPtr = (byte*)srcData.Scan0;
            byte* dPtr = (byte*)destData.Scan0;

            for (int y = 0; y < h; y++)
            {
                byte* sRow = sPtr + (y * srcData.Stride);
                byte* dRow = dPtr + (y * destData.Stride);

                for (int x = 0; x < w; x++)
                {
                    byte b = sRow[x * 4 + 0];
                    byte g = sRow[x * 4 + 1];
                    byte r = sRow[x * 4 + 2];

                    int minVal = Math.Min(r, Math.Min(g, b));

                    if (minVal >= highThresh)
                    {
                        dRow[x * 4 + 0] = 0;
                        dRow[x * 4 + 1] = 0;
                        dRow[x * 4 + 2] = 0;
                        dRow[x * 4 + 3] = 0;
                    }
                    else if (minVal > lowThresh)
                    {
                        double t = (double)(highThresh - minVal) / (highThresh - lowThresh);
                        if (t < 0) t = 0;
                        if (t > 1) t = 1;
                        byte alpha = (byte)(t * 255.0);

                        dRow[x * 4 + 0] = b;
                        dRow[x * 4 + 1] = g;
                        dRow[x * 4 + 2] = r;
                        dRow[x * 4 + 3] = alpha;
                    }
                    else
                    {
                        dRow[x * 4 + 0] = b;
                        dRow[x * 4 + 1] = g;
                        dRow[x * 4 + 2] = r;
                        dRow[x * 4 + 3] = 255;
                    }
                }
            }
        }

        src.UnlockBits(srcData);
        dest.UnlockBits(destData);
        return dest;
    }

    public static Bitmap CreateAboutBadge(int size)
    {
        Bitmap bmp = new Bitmap(size, size, PixelFormat.Format32bppArgb);
        using (Graphics g = Graphics.FromImage(bmp))
        {
            g.SmoothingMode = SmoothingMode.AntiAlias;
            g.InterpolationMode = InterpolationMode.HighQualityBicubic;
            g.PixelOffsetMode = PixelOffsetMode.HighQuality;
            g.Clear(Color.Transparent);

            int pad = (int)(size * 0.08);
            int diam = size - (pad * 2);

            using (SolidBrush darkRedBrush = new SolidBrush(Color.FromArgb(139, 0, 0)))
            {
                g.FillEllipse(darkRedBrush, pad, pad, diam, diam);
            }

            using (Pen goldPen = new Pen(Color.FromArgb(220, 180, 100), Math.Max(1.5f, size * 0.04f)))
            {
                g.DrawEllipse(goldPen, pad + 1, pad + 1, diam - 2, diam - 2);
            }

            using (Font f = new Font(FontFamily.GenericSansSerif, size * 0.44f, FontStyle.Bold))
            using (SolidBrush textBrush = new SolidBrush(Color.White))
            {
                StringFormat sf = new StringFormat();
                sf.Alignment = StringAlignment.Center;
                sf.LineAlignment = StringAlignment.Center;
                g.DrawString("i", f, textBrush, new RectangleF(0, 0, size, size), sf);
            }
        }
        return bmp;
    }

    public static Bitmap CreateInstantSKPIcon(int size)
    {
        Bitmap bmp = new Bitmap(size, size, PixelFormat.Format32bppArgb);
        using (Graphics g = Graphics.FromImage(bmp))
        {
            g.SmoothingMode = SmoothingMode.AntiAlias;
            g.InterpolationMode = InterpolationMode.HighQualityBicubic;
            g.PixelOffsetMode = PixelOffsetMode.HighQuality;
            g.Clear(Color.Transparent);

            float cx = size * 0.5f;
            float cy = size * 0.52f;
            float r = size * 0.44f;

            PointF top = new PointF(cx, cy - r * 0.88f);
            PointF center = new PointF(cx, cy - r * 0.08f);
            PointF left = new PointF(cx - r * 0.78f, cy - r * 0.48f);
            PointF right = new PointF(cx + r * 0.78f, cy - r * 0.48f);
            PointF bLeft = new PointF(cx - r * 0.78f, cy + r * 0.38f);
            PointF bRight = new PointF(cx + r * 0.78f, cy + r * 0.38f);
            PointF bottom = new PointF(cx, cy + r * 0.78f);

            // 1. Top face (lighter crimson highlight)
            using (SolidBrush topBrush = new SolidBrush(Color.FromArgb(185, 30, 45)))
            {
                g.FillPolygon(topBrush, new PointF[] { top, right, center, left });
            }

            // 2. Left face (rich dark red)
            using (SolidBrush leftBrush = new SolidBrush(Color.FromArgb(139, 0, 0)))
            {
                g.FillPolygon(leftBrush, new PointF[] { left, center, bottom, bLeft });
            }

            // 3. Right face (deep burgundy shadow)
            using (SolidBrush rightBrush = new SolidBrush(Color.FromArgb(95, 0, 0)))
            {
                g.FillPolygon(rightBrush, new PointF[] { center, right, bRight, bottom });
            }

            // 4. Elegant gold trim outlines
            using (Pen goldPen = new Pen(Color.FromArgb(235, 195, 110), Math.Max(1.2f, size * 0.038f)))
            {
                goldPen.LineJoin = LineJoin.Round;
                g.DrawPolygon(goldPen, new PointF[] { top, right, bRight, bottom, bLeft, left });
                g.DrawLine(goldPen, center, top);
                g.DrawLine(goldPen, center, left);
                g.DrawLine(goldPen, center, bottom);
                g.DrawLine(goldPen, center, right);
            }

            // 5. Stylized "SKP" text badge on the cube
            float fontEm = Math.Max(7f, size * 0.22f);
            using (Font f = new Font("Arial Black", fontEm, FontStyle.Bold))
            using (SolidBrush shadowBrush = new SolidBrush(Color.FromArgb(50, 0, 0)))
            using (SolidBrush textBrush = new SolidBrush(Color.White))
            {
                StringFormat sf = new StringFormat();
                sf.Alignment = StringAlignment.Center;
                sf.LineAlignment = StringAlignment.Center;

                RectangleF textRect = new RectangleF(0, size * 0.48f, size, size * 0.35f);
                RectangleF shadowRect = new RectangleF(1, size * 0.48f + 1, size, size * 0.35f);

                g.DrawString("SKP", f, shadowBrush, shadowRect, sf);
                g.DrawString("SKP", f, textBrush, textRect, sf);
            }

            // 6. Subtle download/warehouse arrow indicator at top
            if (size >= 32)
            {
                using (SolidBrush arrowBrush = new SolidBrush(Color.FromArgb(255, 230, 140)))
                {
                    float aw = size * 0.12f;
                    float ah = size * 0.15f;
                    float ay = cy - r * 0.52f;
                    PointF[] arrowPts = new PointF[] {
                        new PointF(cx, ay + ah),
                        new PointF(cx - aw, ay),
                        new PointF(cx - aw * 0.4f, ay),
                        new PointF(cx - aw * 0.4f, ay - ah * 0.6f),
                        new PointF(cx + aw * 0.4f, ay - ah * 0.6f),
                        new PointF(cx + aw * 0.4f, ay),
                        new PointF(cx + aw, ay)
                    };
                    g.FillPolygon(arrowBrush, arrowPts);
                }
            }
        }
        return bmp;
    }
}
