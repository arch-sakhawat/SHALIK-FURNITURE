# -*- coding: utf-8 -*-
# ==============================================================================
# Shalik Furniture Modeling Suite for Rhino 8 & 7
# Author & Architect: Sakhawat Hosen Sumon
# Email: arch.sakhawat@gmail.com
# Facebook: https://www.facebook.com/sakhawat.sumon2
# GitHub: https://github.com/arch-sakhawat/SHALIK-FURNITURE
#
# COPYRIGHT & LEGAL WARNING:
# Copyright (c) 2026 Sakhawat Hosen Sumon. All Rights Reserved.
# THIS SOFTWARE IS STRICTLY PROPRIETARY AND COMMERCIAL - NOT FREE.
# Unauthorized copying, reverse-engineering, redistribution, or illegal sharing
# is strictly prohibited and subject to immediate legal lawsuits and prosecution.
# ==============================================================================

import os
import sys
import webbrowser

try:
    import Rhino
    import Rhino.UI
    import Eto.Forms as forms
    import Eto.Drawing as drawing
    RHINO_AVAILABLE = True
except ImportError:
    RHINO_AVAILABLE = False


def get_plugin_dir():
    try:
        p = os.path.dirname(os.path.abspath(__file__))
        if os.path.exists(p):
            return p
    except Exception:
        pass
    appdata = os.environ.get("APPDATA", "")
    p1 = os.path.join(appdata, r"McNeel\Rhinoceros\packages\8.0\ShalikFurniture\1.0.0")
    if os.path.exists(p1):
        return p1
    p2 = os.path.join(appdata, r"ShalikFurniture")
    if os.path.exists(p2):
        return p2
    return r"E:\antigravity\Shalik Furniture"


def get_author_photo_path():
    pdir = get_plugin_dir()
    candidates = [
        os.path.join(pdir, "author.png"),
        os.path.join(pdir, "author.jpg"),
        os.path.join(pdir, "assets", "author.png"),
        os.path.join(pdir, "assets", "author.jpg"),
        os.path.join(pdir, "branding", "author.png"),
        os.path.join(pdir, "icons", "author.png"),
        os.path.join(os.path.dirname(pdir), "author.png"),
        os.path.join(os.path.dirname(pdir), "author.jpg"),
        r"E:\antigravity\Shalik Furniture\author.png",
        r"E:\antigravity\Shalik Furniture\author.jpg",
        r"E:\antigravity\code 2.0\ArchTools\author.png",
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return None


if RHINO_AVAILABLE:
    class LicenseDialog(forms.Dialog[bool]):
        def __init__(self):
            super(LicenseDialog, self).__init__()
            self.Title = "Shalik Furniture - Legal License & Author Verification"
            self.ClientSize = drawing.Size(530, 720)
            self.Resizable = False
            self.Padding = drawing.Padding(18)

            layout = forms.DynamicLayout()
            layout.Spacing = drawing.Size(10, 8)

            # --- Photo / Avatar ---
            photo_path = get_author_photo_path()
            if photo_path and os.path.exists(photo_path):
                try:
                    img = drawing.Bitmap(photo_path)
                    img_view = forms.ImageView()
                    img_view.Image = img
                    img_view.Size = drawing.Size(130, 130)

                    photo_box = forms.DynamicLayout()
                    photo_box.AddRow(None, img_view, None)
                    layout.AddRow(photo_box)
                except Exception as ex:
                    Rhino.RhinoApp.WriteLine("Could not load photo: %s" % ex)

            # --- Author Name & Title ---
            lbl_name = forms.Label()
            lbl_name.Text = "Architect Sakhawat Hosen Sumon"
            lbl_name.Font = drawing.Font(drawing.FontFamilies.Sans, 15, drawing.FontStyle.Bold)
            lbl_name.TextAlignment = forms.TextAlignment.Center
            lbl_name.TextColor = drawing.Color.FromArgb(139, 0, 0)

            lbl_role = forms.Label()
            lbl_role.Text = "Principal Architect & Computational Software Developer"
            lbl_role.Font = drawing.Font(drawing.FontFamilies.Sans, 9.5, drawing.FontStyle.Italic)
            lbl_role.TextAlignment = forms.TextAlignment.Center

            layout.AddRow(lbl_name)
            layout.AddRow(lbl_role)

            sep1 = forms.GroupBox()
            sep1.Height = 2
            layout.AddRow(sep1)

            # --- Software Info ---
            lbl_soft = forms.Label()
            lbl_soft.Text = "Shalik Furniture Generator Suite for Rhino 8 & 7"
            lbl_soft.Font = drawing.Font(drawing.FontFamilies.Sans, 11, drawing.FontStyle.Bold)
            lbl_soft.TextAlignment = forms.TextAlignment.Center

            lbl_ver = forms.Label()
            lbl_ver.Text = "Release Build v1.0.0 | InstantSKP Integrated"
            lbl_ver.Font = drawing.Font(drawing.FontFamilies.Sans, 8.5)
            lbl_ver.TextAlignment = forms.TextAlignment.Center

            layout.AddRow(lbl_soft)
            layout.AddRow(lbl_ver)

            # --- Included Modules ---
            gb_tools = forms.GroupBox()
            gb_tools.Text = "Included Parametric BIM Modules"
            gb_layout = forms.DynamicLayout()
            gb_layout.Spacing = drawing.Size(4, 3)
            gb_layout.Padding = drawing.Padding(8)

            tools_list = [
                ("Bed Generator", "Platform, Canopy, Hotel Suites & Daybeds"),
                ("Sofa Generator", "Sectionals, L-Chaise, Tuxedo & Modular Sofas"),
                ("Dining Table & Chairs", "Auto-Seated 2-12 Seats Rectangular, Round & Oval Sets"),
                ("Kitchen Cabinets", "Base, Tall & Wall Millwork with Yellow LED Lighting"),
                ("Office Workstation", "Executive Desks, Computer Setups & Ergonomic Chairs"),
                ("InstantSKP Importer", "3D Warehouse In-Rhino Browser & Local .SKP Importer"),
            ]
            for tname, tdesc in tools_list:
                row_lbl = forms.Label()
                row_lbl.Text = u"• {}: {}".format(tname, tdesc)
                row_lbl.Font = drawing.Font(drawing.FontFamilies.Sans, 8)
                gb_layout.AddRow(row_lbl)

            gb_tools.Content = gb_layout
            layout.AddRow(gb_tools)

            # --- STRICT COPYRIGHT & LAWSUIT WARNING BOX ---
            gb_legal = forms.GroupBox()
            gb_legal.Text = "CRITICAL LEGAL COPYRIGHT NOTICE"
            gb_legal_layout = forms.DynamicLayout()
            gb_legal_layout.Spacing = drawing.Size(4, 4)
            gb_legal_layout.Padding = drawing.Padding(8)

            lbl_warn = forms.Label()
            lbl_warn.Text = "⚠️ COMMERCIAL PROPRIETARY SOFTWARE - THIS IS NOT FREE"
            lbl_warn.Font = drawing.Font(drawing.FontFamilies.Sans, 9, drawing.FontStyle.Bold)
            lbl_warn.TextColor = drawing.Color.FromArgb(180, 0, 0)
            lbl_warn.TextAlignment = forms.TextAlignment.Center
            gb_legal_layout.AddRow(lbl_warn)

            lbl_notice = forms.Label()
            lbl_notice.Text = (
                "Copyright \u00a9 2026 Sakhawat Hosen Sumon. All Rights Reserved.\n\n"
                "All geometry solvers, parametric algorithms, compiled plug-in binaries, "
                "toolbar interfaces, and source code are the sole intellectual property "
                "of Sakhawat Hosen Sumon.\n\n"
                "STRICT LEGAL ENFORCEMENT: Any unauthorized copying, distribution, "
                "reproduction, decompilation, resale, or public sharing of this software "
                "is strictly illegal. Any individual or organization found violating this "
                "copyright will be subject to IMMEDIATE LEGAL ACTION, COPYRIGHT INFRINGEMENT "
                "LAWSUITS (COURT CASES), AND STATUTORY PUNITIVE DAMAGES."
            )
            lbl_notice.Font = drawing.Font(drawing.FontFamilies.Sans, 7.8)
            lbl_notice.TextAlignment = forms.TextAlignment.Center
            gb_legal_layout.AddRow(lbl_notice)

            gb_legal.Content = gb_legal_layout
            layout.AddRow(gb_legal)

            # --- Contact Buttons ---
            btn_git = forms.Button()
            btn_git.Text = "GitHub Repository"
            btn_git.Click += lambda s, e: webbrowser.open("https://github.com/arch-sakhawat/SHALIK-FURNITURE")

            btn_fb = forms.Button()
            btn_fb.Text = "Facebook Profile"
            btn_fb.Click += lambda s, e: webbrowser.open("https://www.facebook.com/sakhawat.sumon2")

            btn_mail = forms.Button()
            btn_mail.Text = "Email Author / Buy License"
            btn_mail.Click += lambda s, e: webbrowser.open("mailto:arch.sakhawat@gmail.com")

            btn_box = forms.DynamicLayout()
            btn_box.Spacing = drawing.Size(8, 0)
            btn_box.AddRow(None, btn_git, btn_fb, btn_mail, None)
            layout.AddRow(btn_box)

            # --- Close Button ---
            btn_close = forms.Button()
            btn_close.Text = "Close"
            btn_close.Click += lambda s, e: self.Close(True)
            self.DefaultButton = btn_close

            close_box = forms.DynamicLayout()
            close_box.AddRow(None, btn_close)
            layout.AddRow(close_box)

            self.Content = layout


def show_license_dialog():
    if not RHINO_AVAILABLE:
        print("==================================================================")
        print("Shalik Furniture Suite v1.0.0")
        print("Author & Architect: Sakhawat Hosen Sumon (arch.sakhawat@gmail.com)")
        print("GitHub: https://github.com/arch-sakhawat/SHALIK-FURNITURE")
        print("CRITICAL: THIS SOFTWARE IS PROPRIETARY AND COMMERCIAL. NOT FREE.")
        print("Unauthorized copying will result in legal lawsuits and prosecution.")
        print("Copyright (c) 2026 Sakhawat Hosen Sumon. All Rights Reserved.")
        print("==================================================================")
        return
    dlg = LicenseDialog()
    dlg.ShowModal(Rhino.UI.RhinoEtoApp.MainWindow)


def run():
    show_license_dialog()


if __name__ in ["__main__", "ArchAbout", "ShalikAbout", "ArchLicense", "ShalikLicense"]:
    show_license_dialog()

