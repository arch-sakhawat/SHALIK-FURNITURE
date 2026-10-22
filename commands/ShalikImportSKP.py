# ==============================================================================
# Shalik Furniture Modeling Suite - InstantSKP & 3D Warehouse Integration
# Author & Architect: Sakhawat Hosen Sumon
# Email: arch.sakhawat@gmail.com
# Facebook: https://www.facebook.com/sakhawat.sumon2
# GitHub: https://github.com/arch-sakhawat/SHALIK-FURNITURE
#
# COPYRIGHT & LEGAL WARNING:
# Copyright (c) 2026 Sakhawat Hosen Sumon. All Rights Reserved.
# THIS SOFTWARE IS STRICTLY PROPRIETARY AND COMMERCIAL — NOT FREE.
# Unauthorized copying, reverse-engineering, redistribution, or illegal sharing
# is strictly prohibited and subject to immediate legal lawsuits and prosecution.
# ==============================================================================
# -*- coding: utf-8 -*-

import os
import sys

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

DEFAULT_SKP_DIRS = [
    r"C:\Users\archs\Downloads\InstantSKP",
    os.path.join(os.environ.get("USERPROFILE", ""), r"Downloads\InstantSKP"),
    os.path.join(os.environ.get("USERPROFILE", ""), r"Downloads"),
]

INSTANTSKP_PLUGIN_GUID = "0c2f1f48-7322-4a25-a014-a49dd0d26cca"


def is_instantskp_installed():
    appdata = os.environ.get("APPDATA", "")
    p1 = os.path.join(appdata, r"McNeel\Rhinoceros\packages\8.0\InstantSKP")
    if os.path.exists(p1):
        return True
    try:
        import Microsoft.Win32 as winreg
        key = winreg.Registry.CurrentUser.OpenSubKey(r"SOFTWARE\McNeel\Rhinoceros\8.0\Plug-Ins\"" + INSTANTSKP_PLUGIN_GUID)
        if key:
            key.Close()
            return True
    except Exception:
        pass
    return False


def launch_instantskp_warehouse():
    if not RHINO_AVAILABLE:
        return
    Rhino.RhinoApp.WriteLine("Launching InstantSKP 3D Warehouse browser...")
    Rhino.RhinoApp.RunScript("! _InstantSKP", False)


def get_available_skp_files(directory):
    if not os.path.exists(directory):
        return []
    result = []
    try:
        for f in os.listdir(directory):
            if f.lower().endswith(".skp"):
                full_path = os.path.join(directory, f)
                size_mb = os.path.getsize(full_path) / (1024.0 * 1024.0)
                result.append((f, full_path, size_mb))
        result.sort(key=lambda x: x[0].lower())
    except Exception:
        pass
    return result


def import_skp_file(file_path, insert_pt=None, drop_to_floor=True):
    if not RHINO_AVAILABLE or not os.path.exists(file_path):
        return False

    doc = Rhino.RhinoDoc.ActiveDoc
    if not doc:
        return False

    # Snapshot existing object IDs to identify newly imported objects
    existing_ids = set()
    for obj in doc.Objects:
        if not obj.IsDeleted:
            existing_ids.add(obj.Id)

    # Clean path for Rhino script command
    norm_path = os.path.normpath(file_path).replace("\\", "/")

    Rhino.RhinoApp.WriteLine(u"Importing SketchUp Model: {}".format(os.path.basename(file_path)))
    rs.EnableRedraw(False)
    try:
        # Run Rhino native Import command
        cmd = '! _-Import "{}" _Enter'.format(norm_path)
        Rhino.RhinoApp.RunScript(cmd, False)
    finally:
        rs.EnableRedraw(True)

    # Detect newly imported objects
    imported_ids = []
    for obj in doc.Objects:
        if not obj.IsDeleted and obj.Id not in existing_ids:
            imported_ids.append(obj.Id)

    if not imported_ids:
        # Fallback: check selected objects
        sel = [o.Id for o in doc.Objects.GetSelectedObjects(False, False)]
        if sel:
            imported_ids = sel

    if not imported_ids:
        Rhino.RhinoApp.WriteLine("Import completed, but no new geometry detected.")
        return False

    # Ensure Layer: FURNITURE :: SKP_WAREHOUSE
    parent_layer = "FURNITURE"
    sub_layer = "SKP_WAREHOUSE"
    full_layer = parent_layer + "::" + sub_layer

    parent_idx = doc.Layers.FindByFullPath(parent_layer, -1)
    if parent_idx < 0:
        parent_idx = doc.Layers.Add(parent_layer, System.Drawing.Color.FromArgb(139, 0, 0))

    sub_idx = doc.Layers.FindByFullPath(full_layer, -1)
    if sub_idx < 0:
        nl = Rhino.DocObjects.Layer()
        nl.Name = sub_layer
        nl.ParentLayerId = doc.Layers[parent_idx].Id
        nl.Color = System.Drawing.Color.FromArgb(180, 50, 50)
        sub_idx = doc.Layers.Add(nl)

    # Assign layer & calculate cumulative bounding box
    bbox = rg.BoundingBox.Empty
    for id_ in imported_ids:
        rh_obj = doc.Objects.FindId(id_)
        if rh_obj:
            if sub_idx >= 0:
                rh_obj.Attributes.LayerIndex = sub_idx
                rh_obj.CommitChanges()
            geo = rh_obj.Geometry
            if geo:
                bbox.Union(geo.GetBoundingBox(True))

    # Move to picked point or floor if requested
    if bbox.IsValid and (insert_pt is not None or drop_to_floor):
        base_center = rg.Point3d(
            (bbox.Min.X + bbox.Max.X) * 0.5,
            (bbox.Min.Y + bbox.Max.Y) * 0.5,
            bbox.Min.Z
        )
        target = insert_pt if insert_pt is not None else rg.Point3d(base_center.X, base_center.Y, 0.0)
        xform = rg.Transform.Translation(target - base_center)

        for id_ in imported_ids:
            doc.Objects.Transform(id_, xform, True)

    # Group imported objects
    base_name = os.path.splitext(os.path.basename(file_path))[0].replace(" ", "_")
    grp_name = "SKP_" + base_name
    grp_idx = doc.Groups.Add(grp_name)
    if grp_idx >= 0:
        doc.Groups.AddToGroup(grp_idx, imported_ids)

    doc.Views.Redraw()
    Rhino.RhinoApp.WriteLine(u"Successfully imported {} ({} components grouped to {})".format(
        os.path.basename(file_path), len(imported_ids), full_layer))
    return True


if RHINO_AVAILABLE:
    class InstantSKPDialog(forms.Dialog[bool]):
        def __init__(self):
            super(InstantSKPDialog, self).__init__()
            self.Title = "Shalik Furniture - InstantSKP & 3D Warehouse"
            self.ClientSize = drawing.Size(560, 620)
            self.Resizable = True
            self.Padding = drawing.Padding(16)

            # Locate default folder
            self.current_folder = ""
            for d in DEFAULT_SKP_DIRS:
                if os.path.exists(d):
                    self.current_folder = d
                    break
            if not self.current_folder:
                self.current_folder = os.path.expanduser("~")

            self.skp_files = []
            self.InitUI()
            self.RefreshFileList()

        def InitUI(self):
            layout = forms.DynamicLayout()
            layout.Spacing = drawing.Size(10, 8)

            # Header
            lbl_title = forms.Label()
            lbl_title.Text = "INSTANTSKP & 3D WAREHOUSE"
            lbl_title.Font = drawing.Font(drawing.FontFamilies.Sans, 15, drawing.FontStyle.Bold)
            lbl_title.TextColor = drawing.Color.FromArgb(139, 0, 0)
            lbl_title.TextAlignment = forms.TextAlignment.Center

            lbl_sub = forms.Label()
            lbl_sub.Text = "Browse Trimble 3D Warehouse or Import Local .SKP Furniture Models"
            lbl_sub.Font = drawing.Font(drawing.FontFamilies.Sans, 9.5, drawing.FontStyle.Italic)
            lbl_sub.TextAlignment = forms.TextAlignment.Center

            layout.AddRow(lbl_title)
            layout.AddRow(lbl_sub)

            # InstantSKP Status & Launch Banner
            gb_warehouse = forms.GroupBox()
            gb_warehouse.Text = "Online 3D Warehouse (via InstantSKP)"
            gb_warehouse.Font = drawing.Font(drawing.FontFamilies.Sans, 9.5, drawing.FontStyle.Bold)
            gb_layout = forms.DynamicLayout()
            gb_layout.Padding = drawing.Padding(10, 8)
            gb_layout.Spacing = drawing.Size(10, 6)

            lbl_status = forms.Label()
            installed = is_instantskp_installed()
            if installed:
                lbl_status.Text = u"✓ InstantSKP Plugin is installed & active in Rhino 8."
                lbl_status.TextColor = drawing.Color.FromArgb(0, 130, 0)
            else:
                lbl_status.Text = u"ℹ InstantSKP is available via Rhino Package Manager."
                lbl_status.TextColor = drawing.Color.FromArgb(180, 80, 0)

            btn_open_warehouse = forms.Button()
            btn_open_warehouse.Text = "Launch 3D Warehouse in Rhino"
            btn_open_warehouse.Size = drawing.Size(220, 32)
            btn_open_warehouse.BackgroundColor = drawing.Color.FromArgb(139, 0, 0)
            btn_open_warehouse.TextColor = drawing.Color.FromArgb(255, 255, 255)
            btn_open_warehouse.Click += self.OnLaunchWarehouse

            gb_layout.AddRow(lbl_status)
            gb_layout.AddRow(btn_open_warehouse)
            gb_warehouse.Content = gb_layout
            layout.AddRow(gb_warehouse)

            # Local SKP Library Group
            gb_local = forms.GroupBox()
            gb_local.Text = "Local .SKP Furniture Library"
            gb_local.Font = drawing.Font(drawing.FontFamilies.Sans, 9.5, drawing.FontStyle.Bold)
            gbl = forms.DynamicLayout()
            gbl.Padding = drawing.Padding(10, 8)
            gbl.Spacing = drawing.Size(8, 6)

            # Folder Bar
            self.lbl_folder = forms.Label()
            self.lbl_folder.Text = "Folder: " + self.current_folder
            self.lbl_folder.Font = drawing.Font(drawing.FontFamilies.Sans, 8.5)

            btn_browse_folder = forms.Button()
            btn_browse_folder.Text = "Change Folder..."
            btn_browse_folder.Size = drawing.Size(110, 24)
            btn_browse_folder.Click += self.OnChangeFolder

            folder_box = forms.DynamicLayout()
            folder_box.AddRow(self.lbl_folder, None, btn_browse_folder)
            gbl.AddRow(folder_box)

            # Listbox of SKP files
            self.list_box = forms.ListBox()
            self.list_box.Size = drawing.Size(-1, 160)
            gbl.AddRow(self.list_box)

            # Options Checkboxes
            self.cb_floor = forms.CheckBox()
            self.cb_floor.Text = "Drop model to floor level (Z = 0)"
            self.cb_floor.Checked = True

            self.cb_pick_pt = forms.CheckBox()
            self.cb_pick_pt.Text = "Prompt to pick placement point in viewport"
            self.cb_pick_pt.Checked = True

            gbl.AddRow(self.cb_floor)
            gbl.AddRow(self.cb_pick_pt)

            # Import Buttons
            btn_import_sel = forms.Button()
            btn_import_sel.Text = "Import Selected Model"
            btn_import_sel.Size = drawing.Size(180, 32)
            btn_import_sel.BackgroundColor = drawing.Color.FromArgb(139, 0, 0)
            btn_import_sel.TextColor = drawing.Color.FromArgb(255, 255, 255)
            btn_import_sel.Click += self.OnImportSelected

            btn_browse_file = forms.Button()
            btn_browse_file.Text = "Import Any .SKP File..."
            btn_browse_file.Size = drawing.Size(160, 32)
            btn_browse_file.Click += self.OnImportAnyFile

            btn_row = forms.DynamicLayout()
            btn_row.Spacing = drawing.Size(10, 0)
            btn_row.AddRow(btn_import_sel, btn_browse_file, None)
            gbl.AddRow(btn_row)

            gb_local.Content = gbl
            layout.AddRow(gb_local)

            # Footer
            btn_close = forms.Button()
            btn_close.Text = "Close"
            btn_close.Click += lambda s, e: self.Close(False)

            close_box = forms.DynamicLayout()
            close_box.AddRow(None, btn_close)
            layout.AddRow(close_box)

            self.Content = layout

        def RefreshFileList(self):
            self.skp_files = get_available_skp_files(self.current_folder)
            self.list_box.Items.Clear()
            for fn, fp, sz in self.skp_files:
                display_text = u"{}  ({:.1f} MB)".format(fn, sz)
                item = forms.ListItem()
                item.Text = display_text
                item.Key = fp
                self.list_box.Items.Add(item)

            if self.list_box.Items.Count > 0:
                self.list_box.SelectedIndex = 0
            self.lbl_folder.Text = "Folder: " + self.current_folder

        def OnChangeFolder(self, sender, args):
            dlg = forms.SelectFolderDialog()
            dlg.Directory = self.current_folder
            if dlg.ShowDialog(self) == forms.DialogResult.Ok:
                self.current_folder = dlg.Directory
                self.RefreshFileList()

        def OnLaunchWarehouse(self, sender, args):
            self.Close(True)
            launch_instantskp_warehouse()

        def OnImportSelected(self, sender, args):
            if self.list_box.SelectedIndex < 0 or self.list_box.SelectedIndex >= len(self.skp_files):
                forms.MessageBox.Show("Please select a .SKP file from the list.", "Select Model", forms.MessageBoxType.Warning)
                return

            selected_file = self.skp_files[self.list_box.SelectedIndex][1]
            self.Close(True)
            self.ExecuteImport(selected_file)

        def OnImportAnyFile(self, sender, args):
            dlg = forms.OpenFileDialog()
            dlg.Title = "Select SketchUp Model (.skp)"
            dlg.Filters.Add(forms.FileFilter("SketchUp Models (*.skp)", "*.skp"))
            if dlg.ShowDialog(self) == forms.DialogResult.Ok:
                self.Close(True)
                self.ExecuteImport(dlg.FileName)

        def ExecuteImport(self, path):
            pick_pt = None
            if self.cb_pick_pt.Checked:
                gp = Rhino.Input.Custom.GetPoint()
                gp.SetCommandPrompt("Pick insertion point for " + os.path.basename(path))
                if gp.Get() == Rhino.Input.GetResult.Point:
                    pick_pt = gp.Point()

            import_skp_file(path, insert_pt=pick_pt, drop_to_floor=bool(self.cb_floor.Checked))


def show_dialog():
    if not RHINO_AVAILABLE:
        print("Shalik Furniture - InstantSKP Integration")
        return
    dlg = InstantSKPDialog()
    dlg.ShowModal(Rhino.UI.RhinoEtoApp.MainWindow)


def run():
    show_dialog()


if __name__ in ["__main__", "ShalikImportSKP", "InstantSKP_Integration"]:
    show_dialog()
