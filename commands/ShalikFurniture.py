# -*- coding: utf-8 -*-
# ==============================================================================
# Shalik Furniture Modeling Suite for Rhino 8 & 7
# Master Furniture Hub & Generator Launcher
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

_this_dir = os.path.dirname(os.path.abspath(__file__)) if "__file__" in locals() else os.getcwd()
if _this_dir not in sys.path:
    sys.path.insert(0, _this_dir)
_parent_dir = os.path.dirname(_this_dir)
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)
_code_dir = os.path.join(_parent_dir, "Code")
if os.path.exists(_code_dir) and _code_dir not in sys.path:
    sys.path.insert(0, _code_dir)

try:
    import Rhino
    import Rhino.UI
    import Eto.Forms as forms
    import Eto.Drawing as drawing
    import rhinoscriptsyntax as rs
    import scriptcontext as sc
    RHINO_AVAILABLE = True
except ImportError:
    RHINO_AVAILABLE = False

try:
    import ArchUnits
except ImportError:
    ArchUnits = None


def get_plugin_dir():
    try:
        p = os.path.dirname(os.path.abspath(__file__))
        if os.path.exists(p):
            return p
    except Exception:
        pass
    appdata = os.environ.get("APPDATA", "")
    candidates = [
        os.path.join(appdata, r"McNeel\Rhinoceros\packages\8.0\ShalikFurniture\1.0.0"),
        os.path.join(appdata, r"ShalikFurniture"),
        r"E:\antigravity\Shalik Furniture"
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return _this_dir


def ensure_toolbar_visible():
    if not RHINO_AVAILABLE:
        return False
    try:
        pdir = get_plugin_dir()
        candidates = [
            os.path.join(pdir, "ShalikFurniture.rui"),
            os.path.join(os.environ.get("APPDATA", ""), r"McNeel\Rhinoceros\packages\8.0\ShalikFurniture\1.0.0\ShalikFurniture.rui"),
            os.path.join(os.path.dirname(pdir), "ShalikFurniture.rui"),
            r"E:\antigravity\Shalik Furniture\ShalikFurniture.rui"
        ]
        rui_path = None
        for c in candidates:
            if os.path.exists(c):
                rui_path = c
                break

        if rui_path and hasattr(Rhino, "RhinoApp") and hasattr(Rhino.RhinoApp, "ToolbarFiles"):
            tf = Rhino.RhinoApp.ToolbarFiles.FindByPath(rui_path)
            if not tf:
                tf = Rhino.RhinoApp.ToolbarFiles.Open(rui_path)
            if tf:
                for i in range(tf.GroupCount):
                    grp = tf.GetGroup(i)
                    if grp:
                        grp.Visible = True
                Rhino.RhinoApp.WriteLine("Shalik Furniture Toolbar is now open and visible.")
                return True
    except Exception as ex:
        if hasattr(Rhino, "RhinoApp"):
            Rhino.RhinoApp.WriteLine("Toolbar notice: %s" % ex)

    # Fallback to command
    try:
        Rhino.RhinoApp.RunScript("! _Toolbar", False)
    except Exception:
        pass
    return False


def launch_generator(name):
    key = name.lower()
    if key in ("instantskp", "skp", "warehouse", "3dwarehouse"):
        try:
            Rhino.RhinoApp.RunScript("! _InstantSKP", False)
        except Exception as ex:
            if rs:
                rs.MessageBox("Error launching InstantSKP: {}".format(ex), 0, "Shalik Furniture")
        return

    cmd_map = {
        "bed": ("ShalikBed.py", "bed.py", "! _ShalikBed"),
        "sofa": ("ShalikSofa.py", "sofa.py", "! _ShalikSofa"),
        "dining": ("ShalikDiningTable.py", "dining table.py", "! _ShalikDiningTable"),
        "kitchen": ("ShalikKitchen.py", "kitchen.py", "! _ShalikKitchen"),
        "desk": ("ShalikOfficeDesk.py", "office desk.py", "! _ShalikOfficeDesk"),
        "about": ("ShalikAbout.py", "ShalikAbout.py", "! _ShalikFurnitureAbout"),
    }
    targets = cmd_map.get(key)
    if not targets:
        return

    try:
        search_dirs = [_this_dir, _code_dir, _parent_dir, get_plugin_dir()]
        found_file = None
        for fn in targets[:2]:
            for d in search_dirs:
                p = os.path.join(d, fn)
                if os.path.exists(p):
                    found_file = p
                    break
            if found_file:
                break

        if found_file:
            run_cmd = '! _-RunPythonScript "{}"'.format(found_file.replace('\\', '/'))
            Rhino.RhinoApp.RunScript(run_cmd, False)
        else:
            Rhino.RhinoApp.RunScript(targets[2], False)
    except Exception as ex:
        if rs:
            rs.MessageBox("Error launching {}: {}".format(name, ex), 0, "Shalik Furniture")


if RHINO_AVAILABLE:
    class FurnitureHubDialog(forms.Dialog[bool]):
        def __init__(self):
            super(FurnitureHubDialog, self).__init__()
            self.Title = "Shalik Furniture - Parametric Generator Hub"
            self.ClientSize = drawing.Size(580, 780)
            self.Resizable = True
            self.Padding = drawing.Padding(18)

            # Auto-ensure toolbar is visible
            ensure_toolbar_visible()

            main_layout = forms.DynamicLayout()
            main_layout.Spacing = drawing.Size(10, 10)

            # Header Banner
            lbl_title = forms.Label()
            lbl_title.Text = "SHALIK FURNITURE GENERATOR"
            lbl_title.Font = drawing.Font(drawing.FontFamilies.Sans, 16, drawing.FontStyle.Bold)
            lbl_title.TextColor = drawing.Color.FromArgb(139, 0, 0) # Deep Dark Red
            lbl_title.TextAlignment = forms.TextAlignment.Center

            lbl_sub = forms.Label()
            lbl_sub.Text = "Automated Parametric Architecture & Interior Millwork Suite"
            lbl_sub.Font = drawing.Font(drawing.FontFamilies.Sans, 9.5, drawing.FontStyle.Italic)
            lbl_sub.TextAlignment = forms.TextAlignment.Center

            main_layout.AddRow(lbl_title)
            main_layout.AddRow(lbl_sub)

            # Unit Status Banner
            unit_name = "in"
            if ArchUnits:
                _, unit_name, _ = ArchUnits.get_doc_unit_info()
            elif sc and hasattr(sc, "doc") and sc.doc:
                us = sc.doc.ModelUnitSystem
                unit_name = str(us).lower()

            lbl_unit = forms.Label()
            lbl_unit.Text = u"Active Model Units: {} (Auto-converted & dynamically scaled)".format(unit_name.upper())
            lbl_unit.Font = drawing.Font(drawing.FontFamilies.Sans, 8.5)
            lbl_unit.TextColor = drawing.Color.FromArgb(100, 100, 100)
            lbl_unit.TextAlignment = forms.TextAlignment.Center
            main_layout.AddRow(lbl_unit)

            sep1 = forms.GroupBox()
            sep1.Height = 2
            main_layout.AddRow(sep1)

            # Cards for each furniture generator
            items = [
                ("1. Modern Bed & Suite Generator",
                 "Platform, cantilever, wingback, hotel wall-panel, four-poster canopy beds.\n"
                 "Includes mattress presets, tufted headboards, duvets, pillows & nightstands.",
                 "bed"),
                ("2. Modern Sofa & Sectional Generator",
                 "Linear sofas, L-chaise (left/right), U-sectionals, tuxedo, curved & daybeds.\n"
                 "Includes cushions, plush bolsters, armrests, plinth bases & throw pillows.",
                 "sofa"),
                ("3. Dining Table & Seating Generator",
                 "Parametric rectangular, circular, oval & boat tables with auto-scaled seating.\n"
                 "Includes modern Wishbone, sculptural, upholstered & minimalist dining chairs.",
                 "dining"),
                ("4. Ergonomic Kitchen & Millwork Generator",
                 "Base, tall pantry, and wall cabinets with 18mm standard carcass construction.\n"
                 "Includes undermount sinks, designer faucets, induction cooktop & warm LED lighting.",
                 "kitchen"),
                ("5. Modern Office Desk & Workstation",
                 "Executive desks, minimalist computer workstations with ergonomic mesh chairs.\n"
                 "Includes privacy modesty panels, wire management grommets & pedestal drawers.",
                 "desk"),
                ("6. InstantSKP 3D Warehouse Importer",
                 "Browse Trimble 3D Warehouse directly in Rhino and import SketchUp\n"
                 "models (.SKP) with full textures, materials, and layer hierarchy.",
                 "instantskp"),
            ]

            for title, desc, key in items:
                gb = forms.GroupBox()
                gb.Text = title
                gb.Font = drawing.Font(drawing.FontFamilies.Sans, 9.5, drawing.FontStyle.Bold)
                gbl = forms.DynamicLayout()
                gbl.Spacing = drawing.Size(8, 4)
                gbl.Padding = drawing.Padding(10, 6, 10, 8)

                desc_lbl = forms.Label()
                desc_lbl.Text = desc
                desc_lbl.Font = drawing.Font(drawing.FontFamilies.Sans, 8.5)

                btn_launch = forms.Button()
                if key == "instantskp":
                    btn_launch.Text = "Launch InstantSKP"
                else:
                    btn_launch.Text = "Launch " + key.capitalize()
                btn_launch.Size = drawing.Size(120, 28)
                btn_launch.BackgroundColor = drawing.Color.FromArgb(139, 0, 0)
                btn_launch.TextColor = drawing.Color.FromArgb(255, 255, 255)

                def make_handler(target_key):
                    def handler(sender, args):
                        self.Close(True)
                        launch_generator(target_key)
                    return handler

                btn_launch.Click += make_handler(key)

                row_box = forms.DynamicLayout()
                row_box.AddRow(desc_lbl, None, btn_launch)
                gbl.AddRow(row_box)
                gb.Content = gbl
                main_layout.AddRow(gb)

            # Footer Action Buttons
            btn_toolbar = forms.Button()
            btn_toolbar.Text = "Show Shalik Toolbar"
            btn_toolbar.Click += lambda s, e: ensure_toolbar_visible()

            btn_about = forms.Button()
            btn_about.Text = "About & Licence"
            btn_about.Click += lambda s, e: launch_generator("about")

            btn_close = forms.Button()
            btn_close.Text = "Close"
            btn_close.Click += lambda s, e: self.Close(False)

            foot_box = forms.DynamicLayout()
            foot_box.Spacing = drawing.Size(8, 0)
            foot_box.AddRow(btn_toolbar, btn_about, None, btn_close)
            main_layout.AddRow(foot_box)

            self.Content = main_layout


def show_hub():
    if not RHINO_AVAILABLE:
        print("Shalik Furniture Generator Suite")
        print("Available tools: Bed, Sofa, Dining Table, Kitchen, Office Desk")
        return
    dlg = FurnitureHubDialog()
    dlg.ShowModal(Rhino.UI.RhinoEtoApp.MainWindow)


def run():
    show_hub()


if __name__ in ["__main__", "ShalikFurniture", "ArchFurniture", "FurnitureHub"]:
    show_hub()

