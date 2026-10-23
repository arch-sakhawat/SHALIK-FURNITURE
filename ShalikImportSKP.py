# -*- coding: utf-8 -*-
# ==============================================================================
# Shalik Furniture Suite - In-Rhino 3D Warehouse Browser & Instant SKP Importer
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
import time
import subprocess
import webbrowser

_this_dir = os.path.dirname(os.path.abspath(__file__)) if "__file__" in locals() else os.getcwd()
if _this_dir not in sys.path:
    sys.path.insert(0, _this_dir)
_parent_dir = os.path.dirname(_this_dir)
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

try:
    import Rhino
    import Rhino.UI
    import Rhino.Geometry as rg
    import Rhino.Input as rinput
    import Eto.Forms as forms
    import Eto.Drawing as drawing
    import rhinoscriptsyntax as rs
    import scriptcontext as sc
    import System
    import System.IO as sio
    import System.Threading as sthread
    RHINO_AVAILABLE = True
except ImportError:
    RHINO_AVAILABLE = False

try:
    import ArchUnits
except ImportError:
    ArchUnits = None

# Active browser window singleton instance to prevent multiple duplicate windows
_ACTIVE_WAREHOUSE_FORM = None

# Monitored download folders
USER_DOWNLOADS = os.path.join(os.environ.get("USERPROFILE", ""), "Downloads")
INSTANTSKP_DOWNLOADS = os.path.join(USER_DOWNLOADS, "InstantSKP")
SHALIK_DOWNLOADS = os.path.join(USER_DOWNLOADS, "ShalikWarehouse")

for d in [INSTANTSKP_DOWNLOADS, SHALIK_DOWNLOADS]:
    try:
        if not os.path.exists(d):
            os.makedirs(d)
    except Exception:
        pass


def is_file_ready(file_path):
    """Verifies that a downloaded file is completely flushed and accessible."""
    if not os.path.exists(file_path):
        return False
    try:
        # Check size stability over 150ms
        s1 = os.path.getsize(file_path)
        if s1 == 0:
            return False
        time.sleep(0.15)
        s2 = os.path.getsize(file_path)
        if s1 != s2:
            return False
        with open(file_path, "rb") as f:
            f.seek(0, 2)
        return True
    except Exception:
        return False


def import_and_place_skp(file_path, insert_pt=None, drop_to_floor=True):
    """
    Imports a SketchUp (.skp) model into Rhino with clean layer organization,
    accurate bounding box alignment, and optional viewport placement.
    """
    if not RHINO_AVAILABLE or not os.path.exists(file_path):
        return False

    doc = Rhino.RhinoDoc.ActiveDoc
    if not doc:
        return False

    # Snapshot existing objects to detect newly imported geometry
    existing_ids = set()
    for obj in doc.Objects:
        if not obj.IsDeleted:
            existing_ids.add(obj.Id)

    clean_path = os.path.normpath(file_path).replace("\\", "/")
    base_name = os.path.splitext(os.path.basename(file_path))[0].strip()
    safe_name = "".join(c for c in base_name if c.isalnum() or c in (" ", "_", "-")).strip()
    if not safe_name:
        safe_name = "Model"

    Rhino.RhinoApp.WriteLine(u"Shalik Furniture: Importing SketchUp model '{}'...".format(base_name))

    rs.EnableRedraw(False)
    try:
        cmd = '! _-Import "{}" _Enter'.format(clean_path)
        Rhino.RhinoApp.RunScript(cmd, False)
    finally:
        rs.EnableRedraw(True)

    # Detect newly imported objects
    imported_ids = []
    for obj in doc.Objects:
        if not obj.IsDeleted and obj.Id not in existing_ids:
            imported_ids.append(obj.Id)

    if not imported_ids:
        # Fallback to selected objects
        sel = [o.Id for o in doc.Objects.GetSelectedObjects(False, False)]
        if sel:
            imported_ids = sel

    if not imported_ids:
        Rhino.RhinoApp.WriteLine("Import completed, but no geometry was imported.")
        return False

    # Create hierarchical layer: FURNITURE :: SKP_WAREHOUSE :: <ModelName>
    parent_layer = "FURNITURE"
    sub_layer_1 = "SKP_WAREHOUSE"
    sub_layer_2 = safe_name[:32]
    full_layer = parent_layer + "::" + sub_layer_1 + "::" + sub_layer_2

    p_idx = doc.Layers.FindByFullPath(parent_layer, -1)
    if p_idx < 0:
        p_idx = doc.Layers.Add(parent_layer, System.Drawing.Color.FromArgb(139, 0, 0))

    s1_idx = doc.Layers.FindByFullPath(parent_layer + "::" + sub_layer_1, -1)
    if s1_idx < 0:
        nl1 = Rhino.DocObjects.Layer()
        nl1.Name = sub_layer_1
        nl1.ParentLayerId = doc.Layers[p_idx].Id
        nl1.Color = System.Drawing.Color.FromArgb(170, 30, 30)
        s1_idx = doc.Layers.Add(nl1)

    s2_idx = doc.Layers.FindByFullPath(full_layer, -1)
    if s2_idx < 0:
        nl2 = Rhino.DocObjects.Layer()
        nl2.Name = sub_layer_2
        nl2.ParentLayerId = doc.Layers[s1_idx].Id
        nl2.Color = System.Drawing.Color.FromArgb(200, 60, 60)
        s2_idx = doc.Layers.Add(nl2)

    # Calculate cumulative bounding box
    bbox = rg.BoundingBox.Empty
    for id_ in imported_ids:
        rh_obj = doc.Objects.FindId(id_)
        if rh_obj:
            if s2_idx >= 0:
                rh_obj.Attributes.LayerIndex = s2_idx
                rh_obj.CommitChanges()
            geo = rh_obj.Geometry
            if geo:
                bbox.Union(geo.GetBoundingBox(True))

    # Calculate transformation
    if bbox.IsValid:
        base_center = rg.Point3d(
            (bbox.Min.X + bbox.Max.X) * 0.5,
            (bbox.Min.Y + bbox.Max.Y) * 0.5,
            bbox.Min.Z
        )

        if insert_pt is not None:
            target_pt = insert_pt
        elif drop_to_floor:
            target_pt = rg.Point3d(base_center.X, base_center.Y, 0.0)
        else:
            target_pt = base_center

        translation_vec = target_pt - base_center
        if translation_vec.Length > 1e-4:
            xform = rg.Transform.Translation(translation_vec)
            for id_ in imported_ids:
                doc.Objects.Transform(id_, xform, True)

    # Group the imported objects
    grp_name = "SKP_" + safe_name
    grp_idx = doc.Groups.Add(grp_name)
    if grp_idx >= 0:
        doc.Groups.AddToGroup(grp_idx, imported_ids)

    # Select the newly imported group
    doc.Objects.UnselectAll()
    for id_ in imported_ids:
        doc.Objects.Select(id_, True)

    doc.Views.Redraw()
    Rhino.RhinoApp.WriteLine(u"✓ Successfully imported '{}' ({} components grouped into {})".format(
        safe_name, len(imported_ids), full_layer))
    return True


if RHINO_AVAILABLE:
    class ModelPlacementDialog(forms.Dialog[bool]):
        """Clean modal prompt allowing the user to pick viewport placement or origin."""
        def __init__(self, file_name, file_size_mb):
            super(ModelPlacementDialog, self).__init__()
            self.Title = "3D Warehouse Model Downloaded"
            self.ClientSize = drawing.Size(460, 260)
            self.Resizable = False
            self.Padding = drawing.Padding(18)
            self.ChosenMode = "pick"  # "pick", "origin", "cancel"

            layout = forms.DynamicLayout()
            layout.Spacing = drawing.Size(10, 8)

            lbl_header = forms.Label()
            lbl_header.Text = "3D Warehouse Model Ready to Import"
            lbl_header.Font = drawing.Font(drawing.FontFamilies.Sans, 12, drawing.FontStyle.Bold)
            lbl_header.TextColor = drawing.Color.FromArgb(139, 0, 0)
            lbl_header.TextAlignment = forms.TextAlignment.Center
            layout.AddRow(lbl_header)

            lbl_file = forms.Label()
            lbl_file.Text = u"File: {} ({:.2f} MB)".format(file_name, file_size_mb)
            lbl_file.Font = drawing.Font(drawing.FontFamilies.Sans, 9.5)
            lbl_file.TextAlignment = forms.TextAlignment.Center
            layout.AddRow(lbl_file)

            lbl_hint = forms.Label()
            lbl_hint.Text = "Choose how to place this furniture model in your Rhino scene:"
            lbl_hint.TextAlignment = forms.TextAlignment.Center
            layout.AddRow(lbl_hint)

            # Buttons
            btn_pick = forms.Button()
            btn_pick.Text = u"Pick Insertion Point in Viewport (Recommended)"
            btn_pick.Font = drawing.Font(drawing.FontFamilies.Sans, 9.5, drawing.FontStyle.Bold)
            btn_pick.Height = 36
            btn_pick.BackgroundColor = drawing.Color.FromArgb(139, 0, 0)
            btn_pick.TextColor = drawing.Color.FromArgb(255, 255, 255)
            btn_pick.Click += self.OnPickClicked
            layout.AddRow(btn_pick)

            btn_origin = forms.Button()
            btn_origin.Text = u"Place at World Origin (0, 0, 0)"
            btn_origin.Font = drawing.Font(drawing.FontFamilies.Sans, 9)
            btn_origin.Height = 32
            btn_origin.Click += self.OnOriginClicked
            layout.AddRow(btn_origin)

            btn_cancel = forms.Button()
            btn_cancel.Text = "Cancel"
            btn_cancel.Height = 28
            btn_cancel.Click += self.OnCancelClicked
            layout.AddRow(None, btn_cancel)

            self.Content = layout

        def OnPickClicked(self, sender, e):
            self.ChosenMode = "pick"
            self.Close(True)

        def OnOriginClicked(self, sender, e):
            self.ChosenMode = "origin"
            self.Close(True)

        def OnCancelClicked(self, sender, e):
            self.ChosenMode = "cancel"
            self.Close(False)


    class WarehouseBrowserForm(forms.Form):
        """
        Native In-Rhino 3D Warehouse Browser with Edge/Chromium engine,
        automatic download interceptor, category shortcuts, and 1-click Rhino placement.
        """
        def __init__(self):
            super(WarehouseBrowserForm, self).__init__()
            self.Title = "Shalik Furniture - Instant 3D Warehouse & SKP Importer"
            self.ClientSize = drawing.Size(1080, 800)
            self.MinimumSize = drawing.Size(760, 500)
            self.Resizable = True
            self.Topmost = False

            # Set Form Icon if available
            try:
                ico_path = os.path.join(_parent_dir, "setup.ico")
                if os.path.exists(ico_path):
                    self.Icon = drawing.Icon(ico_path)
            except Exception:
                pass

            self.processed_files = set()
            self.InitUI()
            self.StartWatchers()

        def InitUI(self):
            main_layout = forms.DynamicLayout()
            main_layout.Spacing = drawing.Size(0, 0)

            # --- TOP BRANDED HEADER ---
            pnl_header = forms.Panel()
            pnl_header.BackgroundColor = drawing.Color.FromArgb(139, 0, 0)
            pnl_header.Padding = drawing.Padding(12, 8)

            hdr_layout = forms.DynamicLayout()
            hdr_layout.Spacing = drawing.Size(10, 4)

            lbl_title = forms.Label()
            lbl_title.Text = "SHALIK FURNITURE - 3D WAREHOUSE & INSTANT SKP"
            lbl_title.Font = drawing.Font(drawing.FontFamilies.Sans, 13, drawing.FontStyle.Bold)
            lbl_title.TextColor = drawing.Color.FromArgb(255, 255, 255)

            lbl_sub = forms.Label()
            lbl_sub.Text = "Browse SketchUp 3D Warehouse, download any furniture model, and 1-click auto-import with correct scale & floor placement"
            lbl_sub.Font = drawing.Font(drawing.FontFamilies.Sans, 8.5)
            lbl_sub.TextColor = drawing.Color.FromArgb(240, 220, 220)

            hdr_layout.AddRow(lbl_title)
            hdr_layout.AddRow(lbl_sub)
            pnl_header.Content = hdr_layout
            main_layout.AddRow(pnl_header)

            # --- NAVIGATION & ACTION TOOLBAR ---
            pnl_nav = forms.Panel()
            pnl_nav.BackgroundColor = drawing.Color.FromArgb(242, 242, 245)
            pnl_nav.Padding = drawing.Padding(8, 6)

            nav_layout = forms.DynamicLayout()
            nav_layout.Spacing = drawing.Size(6, 4)

            btn_back = forms.Button()
            btn_back.Text = "< Back"
            btn_back.Width = 65
            btn_back.Click += lambda s, e: self.web_view.GoBack() if self.web_view.CanGoBack else None

            btn_fwd = forms.Button()
            btn_fwd.Text = "Forward >"
            btn_fwd.Width = 80
            btn_fwd.Click += lambda s, e: self.web_view.GoForward() if self.web_view.CanGoForward else None

            btn_reload = forms.Button()
            btn_reload.Text = "Reload"
            btn_reload.Width = 70
            btn_reload.Click += lambda s, e: self.web_view.Reload()

            btn_home = forms.Button()
            btn_home.Text = "Home"
            btn_home.Width = 70
            btn_home.Click += lambda s, e: self.NavigateTo("https://3dwarehouse.sketchup.com/search/models?q=furniture")

            self.txt_search = forms.TextBox()
            self.txt_search.PlaceholderText = "Search furniture models (e.g., modern sofa, bed, executive desk, dining chair)..."
            self.txt_search.KeyDown += self.OnSearchKeyDown

            btn_search = forms.Button()
            btn_search.Text = "Search"
            btn_search.Width = 80
            btn_search.Click += self.OnSearchClicked

            btn_local = forms.Button()
            btn_local.Text = "Import Local .SKP"
            btn_local.Font = drawing.Font(drawing.FontFamilies.Sans, 8.5, drawing.FontStyle.Bold)
            btn_local.Width = 140
            btn_local.Click += self.OnImportLocalClicked

            btn_folder = forms.Button()
            btn_folder.Text = "Downloads"
            btn_folder.Width = 95
            btn_folder.Click += self.OnOpenFolderClicked

            nav_row = forms.DynamicLayout()
            nav_row.Spacing = drawing.Size(6, 0)
            nav_row.AddRow(btn_back, btn_fwd, btn_reload, btn_home, self.txt_search, btn_search, btn_local, btn_folder)
            nav_layout.AddRow(nav_row)

            # --- CATEGORY QUICK JUMP PILLS ---
            cat_row = forms.DynamicLayout()
            cat_row.Spacing = drawing.Size(4, 0)

            lbl_cat = forms.Label()
            lbl_cat.Text = "Quick Categories:"
            lbl_cat.Font = drawing.Font(drawing.FontFamilies.Sans, 8, drawing.FontStyle.Bold)
            lbl_cat.TextColor = drawing.Color.FromArgb(90, 90, 90)

            cats = [
                ("Sofas & Couches", "modern sofa couch sectional"),
                ("Beds & Suites", "luxury platform bed master suite"),
                ("Dining Tables", "modern dining table chairs set"),
                ("Kitchen Cabinets", "kitchen cabinet millwork island"),
                ("Office Desks", "executive office workstation desk"),
                ("Armchairs & Lounges", "contemporary lounge armchair"),
                ("Coffee & Side Tables", "modern coffee table end table"),
                ("Lighting & Lamps", "interior pendant light chandelier lamp"),
            ]

            cat_buttons = [lbl_cat]
            for cname, cquery in cats:
                b = forms.Button()
                b.Text = cname
                b.Font = drawing.Font(drawing.FontFamilies.Sans, 8)
                b.Height = 24
                # Closure binding
                b.Click += (lambda q: lambda s, e: self.SearchCategory(q))(cquery)
                cat_buttons.append(b)

            cat_row.AddRow(*cat_buttons)
            nav_layout.AddRow(cat_row)

            pnl_nav.Content = nav_layout
            main_layout.AddRow(pnl_nav)

            # --- EMBEDDED CHROMIUM WEB VIEW ---
            self.web_view = forms.WebView()
            initial_url = System.Uri("https://3dwarehouse.sketchup.com/search/models?q=furniture")
            self.web_view.Url = initial_url

            main_layout.AddRow(self.web_view)

            # --- BOTTOM STATUS BAR ---
            pnl_status = forms.Panel()
            pnl_status.BackgroundColor = drawing.Color.FromArgb(245, 245, 247)
            pnl_status.Padding = drawing.Padding(10, 4)

            stat_layout = forms.DynamicLayout()
            self.lbl_status = forms.Label()
            self.lbl_status.Text = "ℹ 3D Warehouse Active. When you click Download on any model, Shalik Furniture will automatically prompt to place it into your Rhino scene."
            self.lbl_status.Font = drawing.Font(drawing.FontFamilies.Sans, 8)
            self.lbl_status.TextColor = drawing.Color.FromArgb(80, 80, 80)
            stat_layout.AddRow(self.lbl_status)
            pnl_status.Content = stat_layout

            main_layout.AddRow(pnl_status)

            self.Content = main_layout
            self.Closed += self.OnFormClosed

        def NavigateTo(self, url_str):
            try:
                self.web_view.Url = System.Uri(url_str)
            except Exception as ex:
                Rhino.RhinoApp.WriteLine("Navigation error: %s" % ex)

        def SearchCategory(self, query):
            q_enc = query.replace(" ", "+")
            self.txt_search.Text = query
            self.NavigateTo("https://3dwarehouse.sketchup.com/search/models?q=" + q_enc)

        def OnSearchClicked(self, sender, e):
            q = self.txt_search.Text.strip()
            if q:
                self.SearchCategory(q)

        def OnSearchKeyDown(self, sender, e):
            if e.Key == forms.Keys.Enter:
                self.OnSearchClicked(sender, None)

        def OnOpenFolderClicked(self, sender, e):
            folder = USER_DOWNLOADS
            if os.path.exists(folder):
                subprocess.Popen(["explorer.exe", folder])

        def OnImportLocalClicked(self, sender, e):
            dlg = forms.OpenFileDialog()
            dlg.Title = "Select SketchUp Model (.skp) to Import"
            dlg.Filters.Add(forms.FileFilter("SketchUp Models (*.skp)", ".skp"))
            dlg.Filters.Add(forms.FileFilter("All Files (*.*)", ".*"))
            if dlg.ShowDialog(self) == forms.DialogResult.Ok:
                skp_path = dlg.FileName
                if skp_path and os.path.exists(skp_path):
                    self.HandleDownloadedModel(skp_path)

        def StartWatchers(self):
            """Initializes background watchers on user download folders."""
            # Snapshot existing files so we only detect new downloads
            for d in [USER_DOWNLOADS, INSTANTSKP_DOWNLOADS, SHALIK_DOWNLOADS]:
                if os.path.exists(d):
                    try:
                        for f in os.listdir(d):
                            if f.lower().endswith(".skp"):
                                self.processed_files.add(os.path.join(d, f))
                    except Exception:
                        pass

            self.watch_timer = forms.UITimer()
            self.watch_timer.Interval = 1.0  # Check every 1 second
            self.watch_timer.Elapsed += self.OnWatchTick
            self.watch_timer.Start()

        def OnWatchTick(self, sender, e):
            """Checks for newly downloaded .skp files."""
            for d in [INSTANTSKP_DOWNLOADS, SHALIK_DOWNLOADS, USER_DOWNLOADS]:
                if not os.path.exists(d):
                    continue
                try:
                    for f in os.listdir(d):
                        if f.lower().endswith(".skp"):
                            full_path = os.path.join(d, f)
                            if full_path not in self.processed_files:
                                # Found a new .skp file! Check if it's done downloading
                                if is_file_ready(full_path):
                                    self.processed_files.add(full_path)
                                    self.HandleDownloadedModel(full_path)
                                    return
                except Exception:
                    pass

        def HandleDownloadedModel(self, file_path):
            """Invoked whenever a new .skp file is detected."""
            try:
                file_name = os.path.basename(file_path)
                size_mb = os.path.getsize(file_path) / (1024.0 * 1024.0)
                self.lbl_status.Text = u"✓ Downloaded: {} ({:.2f} MB). Select placement...".format(file_name, size_mb)

                # Show placement modal dialog
                dlg = ModelPlacementDialog(file_name, size_mb)
                res = dlg.ShowModal(self)

                if dlg.ChosenMode == "cancel":
                    self.lbl_status.Text = "Import cancelled."
                    return

                insert_pt = None
                if dlg.ChosenMode == "pick":
                    # Minimize this browser window so user can click in Rhino viewport
                    prev_state = self.WindowState
                    self.WindowState = forms.WindowState.Minimized

                    Rhino.RhinoApp.SetFocusToMainWindow()
                    Rhino.RhinoApp.WriteLine(u"Pick floor insertion point for '{}'...".format(file_name))

                    rc, pt = rinput.RhinoGet.GetPoint("Pick floor insertion point for imported furniture model", False)
                    if rc == Rhino.Commands.Result.Success:
                        insert_pt = pt

                    # Restore browser
                    self.WindowState = prev_state

                # Import and place
                import_and_place_skp(file_path, insert_pt=insert_pt, drop_to_floor=True)
                self.lbl_status.Text = u"✓ Successfully imported '{}' into Rhino!".format(file_name)

            except Exception as ex:
                Rhino.RhinoApp.WriteLine("Import handler error: %s" % ex)

        def OnFormClosed(self, sender, e):
            global _ACTIVE_WAREHOUSE_FORM
            if hasattr(self, "watch_timer") and self.watch_timer:
                self.watch_timer.Stop()
            _ACTIVE_WAREHOUSE_FORM = None


def show_warehouse_browser():
    """Opens or activates the native in-Rhino 3D Warehouse Browser window."""
    global _ACTIVE_WAREHOUSE_FORM
    if not RHINO_AVAILABLE:
        print("Shalik Furniture - 3D Warehouse Browser requires Rhino 8 environment.")
        return

    if _ACTIVE_WAREHOUSE_FORM is not None:
        try:
            _ACTIVE_WAREHOUSE_FORM.BringToFront()
            _ACTIVE_WAREHOUSE_FORM.WindowState = forms.WindowState.Normal
            return
        except Exception:
            _ACTIVE_WAREHOUSE_FORM = None

    _ACTIVE_WAREHOUSE_FORM = WarehouseBrowserForm()
    _ACTIVE_WAREHOUSE_FORM.Show()


def run():
    show_warehouse_browser()


if __name__ in ["__main__", "ShalikImportSKP", "InstantSKP", "ShalikInstantSKP", "ShalikWarehouse"]:
    show_warehouse_browser()

