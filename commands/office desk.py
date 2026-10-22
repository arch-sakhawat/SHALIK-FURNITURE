# -*- coding: utf-8 -*-
from __future__ import division
"""
Modern Parametric Office Desk, Computer Workstation & Ergonomic Chair Generator (Shalik / ArchTools)
Compatible with Rhino 7 & Rhino 8 (both IronPython 2.7 and CPython 3 / Python.NET).
Units: INCHES internally, auto-scaled via ArchUnits.
"""

import math
import os
import sys
import json
import codecs
import re
import System
import System.Drawing
from System.Collections.Generic import List
import Rhino
import Rhino.UI
import Rhino.Geometry as rg
import Rhino.Display as rd
import Rhino.Input.Custom as ric
import Rhino.DocObjects as rdo
import Eto.Forms as forms
import Eto.Drawing as drawing
import rhinoscriptsyntax as rs
import scriptcontext as sc

_this_dir = os.path.dirname(os.path.abspath(__file__)) if "__file__" in locals() else os.getcwd()
if _this_dir not in sys.path:
    sys.path.insert(0, _this_dir)
_parent_dir = os.path.dirname(_this_dir)
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

try:
    import ArchUnits
except ImportError:
    ArchUnits = None


# ============================================================
# UNIVERSAL UNIT HELPERS
# ============================================================
def get_doc_unit_info(doc=None):
    if ArchUnits:
        return ArchUnits.get_doc_unit_info(doc)
    d = doc or (sc.doc if sc else None) or Rhino.RhinoDoc.ActiveDoc
    if d and Rhino:
        try:
            us = d.ModelUnitSystem
            scale = Rhino.RhinoMath.UnitScale(Rhino.UnitSystem.Inches, us)
            abbrev = {
                Rhino.UnitSystem.Millimeters: "mm",
                Rhino.UnitSystem.Centimeters: "cm",
                Rhino.UnitSystem.Meters: "m",
                Rhino.UnitSystem.Feet: "ft",
                Rhino.UnitSystem.Inches: "in",
            }.get(us, str(us).lower())
            return us, abbrev, scale
        except Exception:
            pass
    return None, "in", 1.0


def parse_office_length(text, current_unit="in"):
    if ArchUnits:
        return ArchUnits.parse_length(text, current_unit)
    try:
        return float(text)
    except Exception:
        return 0.0


def format_office_length(v, unit_name="in", is_int=False):
    if ArchUnits:
        return ArchUnits.format_length(v, unit_name, is_int)
    if is_int:
        return str(int(round(v)))
    return ("%.3f" % v).rstrip("0").rstrip(".")


def update_label_unit(label, unit_name):
    if ArchUnits:
        return ArchUnits.update_label_unit(label, unit_name)
    return re.sub(r'\(in\b', '(' + unit_name, str(label), flags=re.IGNORECASE)


NON_LENGTH_KEYS = {"rot_deg", "chair_swivel"}


# ============================================================
# CONSTANTS & WORKSTATION PRESET SPECS (INCHES)
# ============================================================
STICKY_KEY = "ShalikOfficeDesk_Settings"
CONDUIT_KEY = "ShalikOfficeDesk_ActiveConduit"
METADATA_KEY = "ShalikOfficeDeskState"
ITEM_INDEX_KEY = "ShalikOfficeDeskItemIndex"
ITEM_CENTER_KEY = "ShalikOfficeDeskItemCenter"
PRESET_FOLDER_NAME = "ShalikTools"
PRESET_FILE_NAME = "ModernOfficeDeskPresets.json"

SIZE_PRESET_NAMES = [
    "0. Custom Manual Desk Dimensions",
    "1. Compact Home Office / Study Desk (48\" x 24\" - 1 Seat)",
    "2. Standard Computer Workstation (60\" x 30\" - 1 Seat)",
    "3. Wide Pro / Dual-Monitor Studio Desk (72\" x 30\" - 1 Seat)",
    "4. Executive Director Desk + Visitor (84\" x 36\" - 1 to 3 Seats)",
    "5. L-Shaped Corner Workstation (66\" x 30\" + 48\" Return)",
    "6. Double Face-to-Face Bench Pod (60\" x 60\" - 2 Seats)",
    "7. Quad 4-Person Open-Office Cluster (120\" x 60\" - 4 Seats)",
]

WORKSTATION_SPECS = {
    1: (48.0, 24.0, 42.0, None),
    2: (60.0, 30.0, 48.0, None),
    3: (72.0, 30.0, 48.0, None),
    4: (84.0, 36.0, 54.0, 1),
    5: (66.0, 30.0, 48.0, 3),
    6: (60.0, 30.0, 48.0, None),
    7: (60.0, 30.0, 48.0, None),
}

DESK_STYLE_NAMES = [
    "0. Motorized Sit-Stand Desk (Telescoping T-Legs + Controller)",
    "1. Executive Pedestal Desk (3-Drawer Credenza + Modesty Panel)",
    "2. Modern Open-Loop Steel Frame Desk",
    "3. L-Shaped Corner Executive / Studio Workstation",
    "4. Minimalist A-Frame / Splayed Architect Desk",
    "5. Acoustic Cubicle / Open-Office Privacy Desk",
]

TOP_SHAPE_NAMES = [
    "0. Crisp Rectangular Slab + Cable Grommets",
    "1. Ergonomic Front Cockpit Cutout + Rounded Corners",
    "2. Soft Squircle / Radiused Corners",
]

RETURN_SIDE_NAMES = [
    "0. Right-Hand Return Wing / Pedestal",
    "1. Left-Hand Return Wing / Pedestal",
]

TECH_SETUP_NAMES = [
    "0. None (Clean Desk Surface Only)",
    "1. Single Widescreen Monitor on Arm + Keyboard & Mouse",
    "2. Dual Pro Monitors on Dual Arm + PC Tower & Peripherals",
    "3. Laptop on Stand + Ultrawide Monitor + Desk Lamp",
]

CHAIR_STYLE_NAMES = [
    "0. Ergonomic Mesh Task Chair (Y-Spine + 3D Armrests)",
    "1. High-Back Executive Leather Chair (Ribbed Cushions)",
    "2. Modern Ribbed Mid-Back Conference Chair",
    "3. Pro Studio / Gaming Bucket Chair (Bolstered Wings)",
    "4. Bentwood & Upholstered Studio Swivel Chair",
]

SEATING_MODE_NAMES = [
    "0. Primary Operator Chair Only",
    "1. Operator Chair + 2 Front Visitor Chairs (Executive)",
    "2. Desk Only (No Chairs)",
]

TOP_FINISHES = [
    ("Natural White Oak Veneer", (205, 175, 138)),
    ("American Black Walnut", (92, 62, 44)),
    ("Matte Fenix Soft Black", (38, 40, 44)),
    ("Crisp Matte White Laminate", (240, 240, 236)),
    ("Warm Bamboo / Maple", (215, 182, 132)),
    ("Concrete / Slate Gray", (135, 138, 142)),
    ("Smoked Glass Executive Top", (85, 95, 102)),
]

FRAME_FINISHES = [
    ("Matte Jet Black Powdercoat", (32, 34, 38)),
    ("Anodized Brushed Silver", (192, 196, 202)),
    ("Crisp Architectural White", (238, 238, 235)),
    ("Dark Gunmetal / Charcoal", (62, 65, 70)),
    ("Warm Brushed Brass / Bronze", (175, 145, 88)),
    ("Matching Walnut Timber", (92, 62, 44)),
]

CHAIR_FABRIC_FINISHES = [
    ("Graphite Breathable Mesh / Fabric", (52, 55, 60)),
    ("Jet Black Italian Leather", (32, 32, 35)),
    ("Cognac Saddle Leather", (162, 92, 52)),
    ("Light Ash / Silver Gray Mesh", (168, 172, 176)),
    ("Navy Executive Wool", (45, 62, 85)),
    ("Warm Alabaster / Cream Leather", (232, 225, 212)),
]

SCREEN_FINISHES = [
    ("Heather Gray Acoustic Felt", (145, 148, 152)),
    ("Charcoal Acoustic Felt", (68, 72, 76)),
    ("Sage Green Acoustic Panel", (112, 128, 108)),
    ("Warm Oatmeal Felt", (198, 190, 176)),
    ("Matching Wood Modesty Panel", (145, 105, 72)),
]

TOP_FINISH_NAMES = ["%d. %s" % (i, n) for i, (n, c) in enumerate(TOP_FINISHES)]
FRAME_FINISH_NAMES = ["%d. %s" % (i, n) for i, (n, c) in enumerate(FRAME_FINISHES)]
CHAIR_FABRIC_NAMES = ["%d. %s" % (i, n) for i, (n, c) in enumerate(CHAIR_FABRIC_FINISHES)]
SCREEN_FINISH_NAMES = ["%d. %s" % (i, n) for i, (n, c) in enumerate(SCREEN_FINISHES)]

NUM_FIELDS = [
    ("desk_len", "Desk width / length (in):", 60.0, 30.0, 144.0, False),
    ("desk_d", "Desk depth (in):", 30.0, 18.0, 60.0, False),
    ("desk_h", "Desk surface height (in):", 29.5, 25.0, 48.0, False),
    ("top_t", "Desktop slab thickness (in):", 1.15, 0.5, 4.0, False),
    ("return_len", "L-Desk return wing length (in):", 48.0, 24.0, 96.0, False),
    ("return_w", "L-Desk return wing depth (in):", 24.0, 16.0, 42.0, False),
    ("screen_h", "Privacy screen height above desk (in):", 14.0, 0.0, 30.0, False),
    ("pull_out", "Chair pull-out distance (in):", 4.0, -8.0, 24.0, False),
    ("chair_w", "Chair seat width (in):", 20.0, 16.0, 28.0, False),
    ("chair_d", "Chair seat depth (in):", 19.0, 15.0, 26.0, False),
    ("seat_h", "Chair seat height (in):", 18.5, 15.0, 23.0, False),
    ("chair_h", "Chair backrest height (in):", 39.0, 28.0, 54.0, False),
]

DD_FIELDS = [
    ("size_preset", "Workstation size / pod preset:", 2, SIZE_PRESET_NAMES),
    ("desk_style", "Office desk typology:", 0, DESK_STYLE_NAMES),
    ("top_shape", "Desktop edge & cutout shape:", 0, TOP_SHAPE_NAMES),
    ("return_side", "Pedestal / L-return hand side:", 0, RETURN_SIDE_NAMES),
    ("tech_setup", "Desktop computer & monitor setup:", 1, TECH_SETUP_NAMES),
    ("chair_style", "Ergonomic office chair style:", 0, CHAIR_STYLE_NAMES),
    ("seating_mode", "Chair seating configuration:", 0, SEATING_MODE_NAMES),
    ("top_finish", "Desktop & wood cabinet material:", 0, TOP_FINISH_NAMES),
    ("frame_finish", "Desk frame & leg material:", 0, FRAME_FINISHES and FRAME_FINISH_NAMES),
    ("chair_finish", "Chair mesh / leather upholstery:", 0, CHAIR_FABRIC_NAMES),
    ("screen_finish", "Acoustic privacy screen finish:", 0, SCREEN_FINISH_NAMES),
]

TAB_LAYOUT = [
    ("1. Desk && Workstation", [
        "size_preset",
        "desk_style",
        "top_shape",
        "@height_row",
        "desk_len",
        "desk_d",
        "top_t",
        "return_side",
        "return_len",
        "return_w",
        "screen_h",
        "tech_setup",
        "@rot_row",
    ]),
    ("2. Ergonomic Chair", [
        "chair_style",
        "seating_mode",
        "@headrest",
        "@pull_row",
        "@swivel_row",
        "chair_w",
        "chair_d",
        "seat_h",
        "chair_h",
    ]),
    ("3. Finishes && Preview", [
        "top_finish",
        "frame_finish",
        "chair_finish",
        "screen_finish",
        "@fast",
    ]),
]


# ============================================================
# SETTINGS & ETO COMPATIBILITY HELPERS
# ============================================================
def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def to_float(v, default):
    try:
        return float(v)
    except Exception:
        return default


def default_settings():
    s = {}
    for key, label, dflt, mn, mx, is_int in NUM_FIELDS:
        s[key] = dflt
    for key, label, dflt, names in DD_FIELDS:
        s[key] = dflt
    s["rot_deg"] = 0
    s["chair_swivel"] = 0
    s["has_headrest"] = True
    s["fast_preview"] = False
    return s


def normalize_settings(settings):
    if not settings:
        return default_settings()
    out = {}
    for key, label, dflt, mn, mx, is_int in NUM_FIELDS:
        v = clamp(to_float(settings.get(key, dflt), dflt), mn, mx)
        out[key] = int(round(v)) if is_int else v
    for key, label, dflt, names in DD_FIELDS:
        try:
            i = int(float(settings.get(key, dflt)))
        except Exception:
            i = dflt
        out[key] = int(clamp(i, 0, len(names) - 1))
    out["rot_deg"] = int(clamp(int(round(to_float(settings.get("rot_deg", 0), 0))), -180, 180))
    out["chair_swivel"] = int(clamp(int(round(to_float(settings.get("chair_swivel", 0), 0))), -45, 45))
    out["has_headrest"] = bool(settings.get("has_headrest", True))
    out["fast_preview"] = bool(settings.get("fast_preview", False))
    return out


def get_initial_settings():
    saved = sc.sticky.get(STICKY_KEY)
    return normalize_settings(saved) if saved else default_settings()


def rgb_to_color(rgb, alpha=255):
    return System.Drawing.Color.FromArgb(int(alpha), int(rgb[0]), int(rgb[1]), int(rgb[2]))


def make_label(text, bold=False):
    lbl = forms.Label()
    lbl.Text = str(text)
    try:
        lbl.VerticalAlignment = forms.VerticalAlignment.Center
        if bold:
            lbl.Font = drawing.Font(lbl.Font.FamilyName, lbl.Font.Size, drawing.FontStyle.Bold)
    except Exception:
        pass
    return lbl


def make_button(text):
    btn = forms.Button()
    btn.Text = str(text)
    return btn


def make_textbox(text="", width=None):
    tb = forms.TextBox()
    tb.Text = str(text)
    if width is not None:
        tb.Width = int(width)
    return tb


def make_checkbox(text="", checked=False):
    cb = forms.CheckBox()
    cb.Text = str(text)
    set_checkbox_checked(cb, checked)
    return cb


def is_checkbox_checked(cb):
    val = cb.Checked
    if val is None:
        return False
    if hasattr(val, "HasValue"):
        return bool(val.HasValue and val.Value)
    return bool(val)


def set_checkbox_checked(cb, val):
    flag = bool(val)
    try:
        cb.Checked = flag
    except TypeError:
        cb.Checked = System.Nullable[System.Boolean](flag)


def dl_add(layout, ctrl, xscale=None, yscale=None):
    if xscale is None and yscale is None:
        return layout.Add(ctrl)
    try:
        if yscale is None:
            return layout.Add(ctrl, xscale)
        return layout.Add(ctrl, xscale, yscale)
    except TypeError:
        nx = System.Nullable[System.Boolean](bool(xscale)) if xscale is not None else None
        ny = System.Nullable[System.Boolean](bool(yscale)) if yscale is not None else None
        return layout.Add(ctrl, nx, ny)


def get_tolerance():
    try:
        doc = Rhino.RhinoDoc.ActiveDoc
        if doc is not None:
            return max(doc.ModelAbsoluteTolerance, 1e-4)
    except Exception:
        pass
    return 0.001


# ============================================================
# PRESETS MANAGEMENT
# ============================================================
def _get_preset_path():
    base = os.environ.get("APPDATA") or os.path.expanduser("~") or os.getcwd()
    folder = os.path.join(base, PRESET_FOLDER_NAME)
    try:
        if not os.path.isdir(folder):
            os.makedirs(folder)
    except Exception:
        pass
    return os.path.join(folder, PRESET_FILE_NAME)


def load_presets():
    path = _get_preset_path()
    if not os.path.exists(path):
        return {}
    try:
        with codecs.open(path, "r", "utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return {}
        return {str(k): normalize_settings(v) for k, v in data.items() if k and isinstance(v, dict)}
    except Exception:
        return {}


def save_presets(presets):
    path = _get_preset_path()
    try:
        clean = {str(k): normalize_settings(v) for k, v in presets.items() if k}
        with codecs.open(path, "w", "utf-8") as f:
            f.write(json.dumps(clean, ensure_ascii=False, indent=2, sort_keys=True))
        return True
    except Exception:
        return False


# ============================================================
# METADATA & NON-DESTRUCTIVE EDITING HELPERS
# ============================================================
def _point_to_data(pt):
    return [float(pt.X), float(pt.Y), float(pt.Z)]


def _point_from_data(data):
    return rg.Point3d(float(data[0]), float(data[1]), float(data[2]))


def _safe_unitize(vec, fallback=None):
    v = rg.Vector3d(vec)
    if v.Length < 1e-6:
        v = rg.Vector3d(fallback) if fallback is not None else rg.Vector3d(1, 0, 0)
    v.Unitize()
    return v


def encode_state(center_in, settings):
    state = {
        "version": 2,
        "center_in": _point_to_data(center_in),
        "settings": normalize_settings(settings),
    }
    return json.dumps(state, ensure_ascii=False)


def decode_state(text):
    if not text:
        return None
    try:
        state = json.loads(text)
        c_in = _point_from_data(state.get("center_in"))
        settings = normalize_settings(state.get("settings", {}))
        return c_in, settings
    except Exception:
        return None


def _brep_center(brep):
    if not brep:
        return None
    try:
        bbox = brep.GetBoundingBox(True)
        if bbox.IsValid:
            return bbox.Center
    except Exception:
        pass
    return None


def _find_doc_object(doc, gid):
    try:
        return doc.Objects.FindId(gid)
    except Exception:
        try:
            return doc.Objects.Find(gid)
        except Exception:
            return None


def get_generated_group_member_ids(doc, obj):
    ids = []
    if not doc or not obj:
        return ids
    try:
        group_indices = obj.Attributes.GetGroupList()
    except Exception:
        group_indices = None
    if group_indices:
        for group_index in group_indices:
            try:
                members = doc.Groups.GroupMembers(group_index)
            except Exception:
                members = None
            if not members:
                continue
            for member in members:
                try:
                    if member.Attributes.GetUserString(METADATA_KEY):
                        ids.append(member.Id)
                except Exception:
                    pass
    if not ids:
        try:
            ids.append(obj.Id)
        except Exception:
            pass
    unique = []
    seen = set()
    for gid in ids:
        k = str(gid)
        if k not in seen:
            unique.append(gid)
            seen.add(k)
    return unique


def transform_center_from_current_objects(doc, center_in, saved_s, target_ids, u_scale):
    orig_pts = []
    curr_pts = []
    for gid in target_ids:
        obj = _find_doc_object(doc, gid)
        if not obj or not obj.Geometry:
            continue
        try:
            txt = obj.Attributes.GetUserString(ITEM_CENTER_KEY)
            if not txt:
                continue
            sc_pt = _point_from_data(json.loads(txt))
            cc_pt = _brep_center(obj.Geometry)
            if sc_pt and cc_pt:
                orig_pts.append(sc_pt)
                curr_pts.append(cc_pt)
        except Exception:
            pass
    if len(orig_pts) < 1:
        return center_in, saved_s
    n = float(len(orig_pts))
    ox = sum(p.X for p in orig_pts) / n
    oy = sum(p.Y for p in orig_pts) / n
    oz = sum(p.Z for p in orig_pts) / n
    cx = sum(p.X for p in curr_pts) / n
    cy = sum(p.Y for p in curr_pts) / n
    cz = sum(p.Z for p in curr_pts) / n

    dot_sum = 0.0
    cross_sum = 0.0
    for op, cp in zip(orig_pts, curr_pts):
        ax, ay = op.X - ox, op.Y - oy
        bx, by = cp.X - cx, cp.Y - cy
        dot_sum += ax * bx + ay * by
        cross_sum += ax * by - ay * bx
    d_angle_deg = math.degrees(math.atan2(cross_sum, dot_sum)) if (abs(dot_sum) > 1e-6 or abs(cross_sum) > 1e-6) else 0.0

    new_c_in = rg.Point3d(
        center_in.X + (cx - ox) / u_scale,
        center_in.Y + (cy - oy) / u_scale,
        center_in.Z + (cz - oz) / u_scale,
    )
    new_s = dict(saved_s)
    if abs(d_angle_deg) > 0.5:
        rot = int(round(new_s.get("rot_deg", 0) + d_angle_deg))
        while rot > 180:
            rot -= 360
        while rot < -180:
            rot += 360
        new_s["rot_deg"] = rot
    return new_c_in, new_s


# ============================================================
# 3D SOLID GEOMETRY PRIMITIVES (LOCAL INCHES)
# ============================================================
def add_part(parts_list, kind, brep):
    if brep and brep.IsValid:
        parts_list.append((kind, brep))


def make_box_xy(x0, x1, y0, y1, z0, z1):
    if x1 - x0 <= 1e-5 or y1 - y0 <= 1e-5 or z1 - z0 <= 1e-5:
        return None
    box = rg.Box(rg.Plane.WorldXY, rg.Interval(x0, x1), rg.Interval(y0, y1), rg.Interval(z0, z1))
    return box.ToBrep() if box.IsValid else None


def make_cyl(base_pt, axis_vec, radius, length):
    if radius <= 1e-5 or length <= 1e-5:
        return None
    unit_axis = rg.Vector3d(axis_vec)
    if not unit_axis.Unitize():
        return None
    pl = rg.Plane(base_pt, unit_axis)
    cyl = rg.Cylinder(rg.Circle(pl, radius), length)
    return cyl.ToBrep(True, True)


def make_tapered_leg(p_bot, p_top, r_bot, r_top):
    vec = p_top - p_bot
    if vec.Length <= 1e-4:
        return None
    pl_b = rg.Plane(p_bot, vec)
    pl_t = rg.Plane(p_top, vec)
    c_b = rg.Circle(pl_b, max(0.08, r_bot)).ToNurbsCurve()
    c_t = rg.Circle(pl_t, max(0.08, r_top)).ToNurbsCurve()
    lofts = rg.Brep.CreateFromLoft([c_b, c_t], rg.Point3d.Unset, rg.Point3d.Unset, rg.LoftType.Straight, False)
    if lofts and len(lofts) > 0:
        capped = lofts[0].CapPlanarHoles(0.005)
        res = capped if (capped and capped.IsValid) else lofts[0]
        if res.SolidOrientation == rg.BrepSolidOrientation.Inward:
            res.Flip()
        return res
    return None


def make_member_between(p0, p1, up_vec, width, height):
    v = p1 - p0
    L = v.Length
    if L <= 1e-4 or width <= 1e-4 or height <= 1e-4:
        return None
    ax = _safe_unitize(v, rg.Vector3d.XAxis)
    az = _safe_unitize(up_vec, rg.Vector3d.ZAxis)
    ay = _safe_unitize(rg.Vector3d.CrossProduct(az, ax), rg.Vector3d.YAxis)
    az = _safe_unitize(rg.Vector3d.CrossProduct(ax, ay), rg.Vector3d.ZAxis)
    mid = 0.5 * (p0 + p1)
    pl = rg.Plane(mid, ax, ay)
    box = rg.Box(pl, rg.Interval(-L * 0.5, L * 0.5), rg.Interval(-width * 0.5, width * 0.5), rg.Interval(-height * 0.5, height * 0.5))
    return box.ToBrep() if box.IsValid else None


def make_angled_backrest(back_width, y_bot, z_bot, y_top, z_top, thickness, curve_depth=0.0):
    """
    Builds a chair backrest or curved monitor spanning across X (`-back_width/2` to `+back_width/2`),
    rising from `(0, y_bot, z_bot)` to `(0, y_top, z_top)`.
    Crucial Fix: `n_forward` is guaranteed to point toward `+Y` (toward the sitter/operator)
    so positive `curve_depth` always curves the left and right edges FORWARD (`+Y`) around the user!
    """
    hw = max(2.0, back_width * 0.5)
    ht = max(0.15, thickness * 0.5)
    p_bot = rg.Point3d(0.0, y_bot, z_bot)
    p_top = rg.Point3d(0.0, y_top, z_top)
    spine = p_top - p_bot
    spine_len = spine.Length
    if spine_len <= 0.4:
        return None

    u_spine = _safe_unitize(spine, rg.Vector3d.ZAxis)
    if abs(curve_depth) <= 0.05:
        pl = rg.Plane(0.5 * (p_bot + p_top), rg.Vector3d.XAxis, u_spine)
        box = rg.Box(pl, rg.Interval(-hw, hw), rg.Interval(-spine_len * 0.5, spine_len * 0.5), rg.Interval(-ht, ht))
        return box.ToBrep() if box.IsValid else None

    # Ensure n_forward always points toward +Y (front of chair / toward user)
    n_forward = _safe_unitize(rg.Vector3d.CrossProduct(u_spine, rg.Vector3d.XAxis), rg.Vector3d.YAxis)
    if n_forward.Y < 0.0:
        n_forward = -n_forward

    pl_base = rg.Plane(p_bot, rg.Vector3d.XAxis, n_forward)
    p_fl = pl_base.PointAt(-hw, curve_depth + ht)
    p_fm = pl_base.PointAt(0.0, ht)
    p_fr = pl_base.PointAt(hw, curve_depth + ht)
    p_br = pl_base.PointAt(hw, curve_depth - ht)
    p_bm = pl_base.PointAt(0.0, -ht)
    p_bl = pl_base.PointAt(-hw, curve_depth - ht)

    arc_f = rg.Arc(p_fl, p_fm, p_fr).ToNurbsCurve()
    line_r = rg.LineCurve(p_fr, p_br)
    arc_b = rg.Arc(p_br, p_bm, p_bl).ToNurbsCurve()
    line_l = rg.LineCurve(p_bl, p_fl)
    joined = rg.Curve.JoinCurves([arc_f, line_r, arc_b, line_l], 0.01)
    if joined and len(joined) > 0:
        srf = rg.Surface.CreateExtrusion(joined[0], spine)
        if srf:
            b = srf.ToBrep()
            if b:
                capped = b.CapPlanarHoles(0.01)
                res = capped if (capped and capped.IsValid) else b
                if res.SolidOrientation == rg.BrepSolidOrientation.Inward:
                    res.Flip()
                return res
    return None


def extrude_closed_curve_solid(crv, vec):
    if not crv or vec.Length <= 1e-5:
        return None
    srf = rg.Surface.CreateExtrusion(crv, vec)
    if srf:
        b = srf.ToBrep()
        if b:
            capped = b.CapPlanarHoles(0.01)
            res = capped if (capped and capped.IsValid) else b
            if res.SolidOrientation == rg.BrepSolidOrientation.Inward:
                res.Flip()
            return res
    return None


# ============================================================
# 5 ERGONOMIC SWIVEL OFFICE CHAIR BUILDERS (FACING +Y)
# ============================================================
def build_ergonomic_office_chair(S, fast=False):
    """
    Constructs a high-detail 3D Swivel Office Chair at (0, 0, 0) on the floor, facing +Y:
      1. 5-Star Swivel Base with 5 dual-wheel casters.
      2. Pneumatic gas-lift cylinder + under-seat synchro-tilt mechanism.
      3. 5 Distinct Ergonomic Chair Typologies (all curved concave toward +Y).
    """
    parts = []
    c_style = int(S["chair_style"])
    cw = float(S["chair_w"])
    cd = float(S["chair_d"])
    sh = float(S["seat_h"])
    ch = max(sh + 12.0, float(S["chair_h"]))
    has_headrest = bool(S.get("has_headrest", True))

    hw = cw * 0.5
    hd = cd * 0.5

    # 1. Universal 5-Star Swivel Base + Dual-Wheel Casters + Gas Lift Cylinder
    base_r = max(11.5, cw * 0.62)
    caster_r = 1.05
    z_hub = 3.2
    add_part(parts, "chair_frame", make_cyl(rg.Point3d(0, 0, 1.4), rg.Vector3d.ZAxis, 1.15, sh - 3.6))
    add_part(parts, "chair_frame", make_cyl(rg.Point3d(0, 0, 1.2), rg.Vector3d.ZAxis, 1.65, 2.5))

    for i in range(5):
        ang = (2.0 * math.pi * i) / 5.0 + math.pi * 0.1
        rx = base_r * math.cos(ang)
        ry = base_r * math.sin(ang)
        p_hub = rg.Point3d(0.0, 0.0, z_hub)
        p_tip = rg.Point3d(rx, ry, caster_r * 2.05)
        add_part(parts, "chair_frame", make_member_between(p_hub, p_tip, rg.Vector3d.ZAxis, 1.35, 0.95))
        if not fast:
            wheel_ax = rg.Vector3d(-math.sin(ang), math.cos(ang), 0.0)
            p_w = rg.Point3d(rx, ry, caster_r) - wheel_ax * 0.55
            add_part(parts, "chair_frame", make_cyl(p_w, wheel_ax, caster_r, 1.1))

    # Under-seat synchro-tilt mechanism housing
    add_part(parts, "chair_frame", make_box_xy(-3.2, 3.2, -3.5, 2.5, sh - 2.6, sh - 1.2))

    # 2. Style-Specific Seat, Spine, Backrest, Armrests & Headrest
    if c_style == 0:
        # 0. Ergonomic Mesh Task Chair (Y-Spine + Concave Mesh Back + 3D T-Armrests + Aligned Headrest)
        add_part(parts, "chair_cushion", make_box_xy(-hw, hw, -hd + 0.8, hd, sh - 1.4, sh + 0.3))

        y_back_bot = -hd + 1.0
        y_back_top = -hd - 1.4
        z_back_bot = sh - 0.2
        z_back_top = ch

        # Concave breathable mesh backrest curving forward around the sitter
        mesh_back = make_angled_backrest(cw - 0.8, y_back_bot, z_back_bot, y_back_top, z_back_top, 0.9, curve_depth=1.5)
        add_part(parts, "chair_cushion", mesh_back)

        # Rear L-spine & Y-lumbar arms attached directly to the back of the mesh backrest
        p_sp0 = rg.Point3d(0.0, -2.0, sh - 1.8)
        p_sp1 = rg.Point3d(0.0, y_back_bot - 0.5, z_back_bot)
        p_sp2 = rg.Point3d(0.0, 0.5 * (y_back_bot + y_back_top) - 0.65, sh + (ch - sh) * 0.55)
        add_part(parts, "chair_frame", make_member_between(p_sp0, p_sp1, rg.Vector3d.ZAxis, 1.8, 1.1))
        add_part(parts, "chair_frame", make_member_between(p_sp1, p_sp2, rg.Vector3d.YAxis, 1.8, 0.9))
        for sx in (-1.0, 1.0):
            p_y_end = rg.Point3d(sx * (hw - 1.0), y_back_top + 1.2, sh + (ch - sh) * 0.68)
            add_part(parts, "chair_frame", make_member_between(p_sp2, p_y_end, rg.Vector3d.YAxis, 1.1, 0.65))

        # 3D Adjustable T-Armrests
        arm_z = sh + 7.5
        for sx in (-1.0, 1.0):
            ax = sx * (hw + 0.9)
            add_part(parts, "chair_frame", make_box_xy(sx * (hw - 1.5), ax + sx * 0.4, -1.2, 1.2, sh - 1.2, sh - 0.4))
            add_part(parts, "chair_frame", make_box_xy(ax - 0.45, ax + 0.45, -1.1, 1.1, sh - 0.4, arm_z - 0.7))
            add_part(parts, "chair_cushion", make_box_xy(ax - 1.5, ax + 1.5, -4.2, 4.2, arm_z - 0.7, arm_z))

        # Aligned Ergonomic Headrest directly at the top edge of the backrest (`y_back_top`)
        if has_headrest:
            p_hr_base = rg.Point3d(0.0, y_back_top - 0.3, z_back_top - 1.0)
            p_hr_top = rg.Point3d(0.0, y_back_top + 0.3, z_back_top + 2.5)
            add_part(parts, "chair_frame", make_member_between(p_hr_base, p_hr_top, rg.Vector3d.YAxis, 1.5, 0.7))
            hr_pad = make_angled_backrest(cw * 0.48, y_back_top + 0.2, z_back_top + 1.2, y_back_top + 1.0, z_back_top + 5.6, 1.0, curve_depth=0.8)
            add_part(parts, "chair_cushion", hr_pad)

    elif c_style == 1:
        # 1. High-Back Executive Leather Chair (Plush Segmented Cushions + Loop Arms)
        add_part(parts, "chair_cushion", make_box_xy(-hw, hw, -hd + 0.8, hd, sh - 2.0, sh + 0.4))
        b_h = (ch - sh) + (4.5 if has_headrest else 0.0)
        z0 = sh
        add_part(parts, "chair_cushion", make_angled_backrest(cw, -hd + 1.4, z0, -hd - 0.2, z0 + b_h * 0.38, 2.5, curve_depth=1.3))
        add_part(parts, "chair_cushion", make_angled_backrest(cw, -hd - 0.15, z0 + b_h * 0.38, -hd - 1.2, z0 + b_h * 0.74, 2.4, curve_depth=1.3))
        add_part(parts, "chair_cushion", make_angled_backrest(cw * 0.94, -hd - 1.15, z0 + b_h * 0.74, -hd - 1.6, z0 + b_h, 2.5, curve_depth=1.0))

        arm_z = sh + 7.6
        for sx in (-1.0, 1.0):
            ax = sx * (hw + 0.55)
            add_part(parts, "chair_frame", make_member_between(rg.Point3d(ax, hd * 0.55, sh - 1.0), rg.Point3d(ax, hd * 0.45, arm_z), rg.Vector3d.XAxis, 1.2, 0.55))
            add_part(parts, "chair_frame", make_member_between(rg.Point3d(ax, hd * 0.45, arm_z), rg.Point3d(ax, -hd + 0.6, arm_z - 1.0), rg.Vector3d.XAxis, 1.3, 0.55))
            add_part(parts, "chair_cushion", make_box_xy(ax - 1.0, ax + 1.0, -hd * 0.38, hd * 0.38, arm_z, arm_z + 0.65))

    elif c_style == 2:
        # 2. Modern Ribbed Mid-Back Conference / Visitor Chair (Continuous Seat-to-Back Shell)
        add_part(parts, "chair_cushion", make_box_xy(-hw, hw, -hd + 0.8, hd, sh - 1.2, sh + 0.25))
        rib_back = make_angled_backrest(cw, -hd + 1.2, sh - 0.6, -hd - 1.4, ch - 1.5, 1.2, curve_depth=1.2)
        add_part(parts, "chair_cushion", rib_back)
        arm_z = sh + 7.4
        for sx in (-1.0, 1.0):
            ax = sx * (hw + 0.4)
            add_part(parts, "chair_frame", make_member_between(rg.Point3d(ax, -hd + 1.2, sh - 0.6), rg.Point3d(ax, -hd - 1.4, ch - 1.5), rg.Vector3d.XAxis, 1.1, 0.55))
            add_part(parts, "chair_frame", make_member_between(rg.Point3d(ax, hd * 0.55, sh - 0.6), rg.Point3d(ax, hd * 0.45, arm_z), rg.Vector3d.XAxis, 1.0, 0.5))
            add_part(parts, "chair_frame", make_member_between(rg.Point3d(ax, hd * 0.45, arm_z), rg.Point3d(ax, -hd + 0.3, arm_z - 0.8), rg.Vector3d.XAxis, 1.1, 0.5))

    elif c_style == 3:
        # 3. Pro Studio / Gaming Bucket Chair (Concave Bolstered Back + Front Lumbar & Neck Pillows)
        add_part(parts, "chair_cushion", make_box_xy(-hw + 1.4, hw - 1.4, -hd + 0.8, hd, sh - 1.8, sh + 0.2))
        for sx in (-1.0, 1.0):
            add_part(parts, "chair_cushion", make_box_xy(sx * (hw - 0.8) - 0.9, sx * (hw - 0.8) + 0.9, -hd + 0.8, hd - 0.4, sh - 1.5, sh + 1.3))
        top_z = ch + (4.5 if has_headrest else 1.0)
        # Main bucket backrest curving forward (`curve_depth = 2.2`) so side bolsters wrap around the user
        add_part(parts, "chair_cushion", make_angled_backrest(cw, -hd + 1.2, sh - 0.4, -hd - 1.6, top_z, 1.8, curve_depth=2.2))
        # Lumbar & Neck bolster pillows positioned on the FRONT (`+Y`) face of the backrest!
        add_part(parts, "chair_cushion", make_angled_backrest(cw * 0.52, -hd + 2.2, sh + 1.5, -hd + 1.7, sh + 6.0, 1.5, curve_depth=0.3))
        if has_headrest:
            add_part(parts, "chair_cushion", make_angled_backrest(cw * 0.46, -hd - 0.1, top_z - 6.0, -hd - 0.5, top_z - 1.8, 1.6, curve_depth=0.3))
        arm_z = sh + 7.5
        for sx in (-1.0, 1.0):
            ax = sx * (hw + 0.95)
            add_part(parts, "chair_frame", make_box_xy(ax - 0.5, ax + 0.5, -1.2, 1.2, sh - 1.2, arm_z - 0.7))
            add_part(parts, "chair_cushion", make_box_xy(ax - 1.5, ax + 1.5, -4.4, 4.4, arm_z - 0.7, arm_z))

    else:
        # 4. Bentwood & Upholstered Studio Swivel Chair (Warm Wood Outer Shell + Inner Leather Cushion + Arms)
        # Note: Outer wood shell is placed on "desk_top" layer so it renders in Walnut/Oak wood!
        add_part(parts, "desk_top", make_box_xy(-hw - 0.35, hw + 0.35, -hd + 0.6, hd + 0.2, sh - 1.6, sh - 0.4))
        add_part(parts, "chair_cushion", make_box_xy(-hw + 0.3, hw - 0.3, -hd + 1.4, hd - 0.2, sh - 0.4, sh + 0.65))
        # Outer bentwood backrest shell & inner upholstered backrest cushion separated cleanly by 0.75"
        wood_shell = make_angled_backrest(cw + 0.7, -hd + 0.9, sh - 0.8, -hd - 1.5, ch - 2.0, 0.65, curve_depth=1.8)
        inner_pad = make_angled_backrest(cw - 0.8, -hd + 1.75, sh, -hd - 0.65, ch - 2.6, 0.95, curve_depth=1.6)
        add_part(parts, "desk_top", wood_shell)
        add_part(parts, "chair_cushion", inner_pad)
        # Curved studio armrests
        arm_z = sh + 7.2
        for sx in (-1.0, 1.0):
            ax = sx * (hw + 0.45)
            add_part(parts, "chair_frame", make_member_between(rg.Point3d(ax, hd * 0.45, sh - 0.8), rg.Point3d(ax, hd * 0.35, arm_z), rg.Vector3d.XAxis, 1.1, 0.5))
            add_part(parts, "desk_top", make_box_xy(ax - 0.9, ax + 0.9, -hd * 0.35, hd * 0.45, arm_z, arm_z + 0.55))

    return parts


# ============================================================
# 3D DESKTOP COMPUTER, MONITOR ARM, KEYBOARD & TECH BUILDER
# ============================================================
def build_desktop_tech_equipment(S, z_desk_top, fast=False):
    """
    Generates realistic 3D computer equipment on the desk surface at `z_desk_top`
    (operator sits at `-Y` facing `+Y`):
      - Desk mat, low-profile mechanical keyboard, ergonomic mouse
      - Articulated monitor arm terminating on the BACK (`+Y`) of each monitor (never poking through!)
      - Curved ultrawide monitor curving concave toward the user (`-Y`)
    """
    parts = []
    tech_mode = int(S["tech_setup"])
    if tech_mode == 0:
        return parts

    D = float(S["desk_d"])
    hd = D * 0.5
    y_front = -hd
    y_back = hd

    # 1. Desk Mat + Keyboard + Mouse near operator edge (`-Y`)
    y_mat_c = y_front + 8.5
    add_part(parts, "tech", make_box_xy(-15.0, 15.0, y_mat_c - 6.0, y_mat_c + 6.0, z_desk_top, z_desk_top + 0.12))
    add_part(parts, "tech", make_box_xy(-8.5, 5.5, y_mat_c - 3.0, y_mat_c + 1.8, z_desk_top + 0.12, z_desk_top + 0.72))
    add_part(parts, "tech", make_box_xy(8.0, 10.6, y_mat_c - 2.2, y_mat_c + 1.8, z_desk_top + 0.12, z_desk_top + 1.25))

    # Rear desk clamp & vertical pole for monitor arm
    y_clamp = y_back - 1.4
    add_part(parts, "tech", make_box_xy(-1.6, 1.6, y_clamp - 1.0, y_back, z_desk_top - 1.2, z_desk_top + 0.5))
    add_part(parts, "tech", make_cyl(rg.Point3d(0.0, y_clamp, z_desk_top + 0.5), rg.Vector3d.ZAxis, 0.65, 13.0))

    z_mon_bot = z_desk_top + 5.2
    mon_h = 13.5

    if tech_mode == 1:
        # 1. Single 34" Curved Ultrawide Monitor curving CONCAVE toward the user (`-Y`)!
        mon_w = 31.0
        y_scr = y_back - 6.5
        # Arm connects from pole at `y_clamp` to the BACK of the monitor (`y_scr + 0.45`)
        add_part(parts, "tech", make_member_between(
            rg.Point3d(0.0, y_clamp, z_desk_top + 10.5),
            rg.Point3d(0.0, y_scr + 0.45, z_desk_top + 11.0),
            rg.Vector3d.ZAxis, 1.2, 0.9
        ))
        # Note: Operator is at `-Y`, so `curve_depth = -1.8` curves the left/right edges toward `-Y` (hugging the user)!
        scr = make_angled_backrest(mon_w, y_scr, z_mon_bot, y_scr + 0.25, z_mon_bot + mon_h, 0.7, curve_depth=-1.8)
        add_part(parts, "tech", scr)

    elif tech_mode == 2:
        # 2. Dual 27" Widescreen Monitors on Dual Articulated VESA Arms + Sleek PC Tower
        mon_w = 24.0
        y_scr = y_back - 6.8
        for sx in (-1.0, 1.0):
            mx = sx * (mon_w * 0.51)
            yaw = sx * math.radians(12.0)  # Angle outer edges toward the operator at (0, -hd)!
            # Arm terminates BEHIND the monitor at `y_scr + 1.2` so it never pokes through the screen!
            p_vesa_back = rg.Point3d(mx * 0.72, y_scr + 1.2, z_desk_top + 11.0)
            add_part(parts, "tech", make_member_between(
                rg.Point3d(0.0, y_clamp, z_desk_top + 10.5),
                p_vesa_back,
                rg.Vector3d.ZAxis, 1.0, 0.8
            ))
            panel = make_box_xy(-mon_w * 0.49, mon_w * 0.49, -0.35, 0.35, z_mon_bot, z_mon_bot + mon_h)
            vesa = make_box_xy(-2.0, 2.0, 0.35, 0.95, z_desk_top + 9.5, z_desk_top + 12.5)
            rot_m = rg.Transform.Rotation(yaw, rg.Vector3d.ZAxis, rg.Point3d.Origin)
            tr_m = rg.Transform.Translation(mx, y_scr, 0.0)
            for b_m in (panel, vesa):
                if b_m:
                    b_m.Transform(tr_m * rot_m)
                    add_part(parts, "tech", b_m)

        # Sleek Mid-Tower PC Workstation on right side of desk (proper proportions: 7.8" W x 16.5" D x 16.5" H)
        L = float(S["desk_len"])
        tx = L * 0.5 - 5.2
        if tx > mon_w * 0.85:
            y_pc = y_back - 9.5
            add_part(parts, "tech", make_box_xy(tx - 3.9, tx + 3.9, y_pc - 8.2, y_pc + 8.2, z_desk_top + 0.4, z_desk_top + 16.5))
            # 4 small feet under PC case
            for fx in (tx - 3.2, tx + 3.2):
                for fy in (y_pc - 7.0, y_pc + 7.0):
                    add_part(parts, "desk_frame", make_cyl(rg.Point3d(fx, fy, z_desk_top), rg.Vector3d.ZAxis, 0.45, 0.4))

    elif tech_mode == 3:
        # 3. Center 27" Monitor + Angled Laptop on Stand + Architect Task Lamp
        mon_w = 24.5
        y_scr = y_back - 6.2
        add_part(parts, "tech", make_member_between(
            rg.Point3d(0.0, y_clamp, z_desk_top + 10.5),
            rg.Point3d(0.0, y_scr + 0.45, z_desk_top + 11.0),
            rg.Vector3d.ZAxis, 1.1, 0.85
        ))
        add_part(parts, "tech", make_box_xy(-mon_w * 0.5, mon_w * 0.5, y_scr - 0.35, y_scr + 0.35, z_mon_bot, z_mon_bot + mon_h))
        # Laptop on stand on left side (-X)
        lx, ly = -16.5, y_front + 11.5
        add_part(parts, "tech", make_box_xy(lx - 4.5, lx + 4.5, ly - 4.0, ly + 4.0, z_desk_top, z_desk_top + 2.6))
        lap_base = make_angled_backrest(13.5, ly - 4.2, z_desk_top + 1.8, ly + 4.2, z_desk_top + 3.8, 0.35)
        lap_scr = make_angled_backrest(13.5, ly + 4.2, z_desk_top + 3.8, ly + 6.0, z_desk_top + 12.2, 0.28)
        rot_l = rg.Transform.Rotation(math.radians(-18.0), rg.Vector3d.ZAxis, rg.Point3d(lx, ly, z_desk_top))
        for lb in (lap_base, lap_scr):
            if lb:
                lb.Transform(rot_l)
                add_part(parts, "tech", lb)
        # Architect Desk Lamp on right side (+X)
        rx_l, ry_l = 18.0, y_back - 4.5
        add_part(parts, "tech", make_cyl(rg.Point3d(rx_l, ry_l, z_desk_top), rg.Vector3d.ZAxis, 3.0, 0.45))
        add_part(parts, "tech", make_cyl(rg.Point3d(rx_l, ry_l, z_desk_top + 0.45), rg.Vector3d.ZAxis, 0.32, 15.5))
        add_part(parts, "tech", make_member_between(rg.Point3d(rx_l, ry_l, z_desk_top + 15.9), rg.Point3d(rx_l - 5.5, ry_l - 3.5, z_desk_top + 17.5), rg.Vector3d.ZAxis, 0.6, 0.4))

    return parts


# ============================================================
# SINGLE DESK UNIT BUILDER (6 DESK TYPOLOGIES AT ORIGIN, USER AT -Y)
# ============================================================
def make_desk_top_slab(L, D, H, top_t, shape_idx):
    hl = L * 0.5
    hd = D * 0.5
    z_bot = H - top_t
    pl = rg.Plane(rg.Point3d(0, 0, z_bot), rg.Vector3d.XAxis, rg.Vector3d.YAxis)

    if shape_idx == 1:
        cut_w = min(L * 0.45, 28.0)
        cut_d = min(D * 0.14, 3.5)
        pts = [
            rg.Point3d(-hl, -hd, z_bot),
            rg.Point3d(-cut_w * 0.5, -hd, z_bot),
            rg.Point3d(-cut_w * 0.38, -hd + cut_d, z_bot),
            rg.Point3d(cut_w * 0.38, -hd + cut_d, z_bot),
            rg.Point3d(cut_w * 0.5, -hd, z_bot),
            rg.Point3d(hl, -hd, z_bot),
            rg.Point3d(hl, hd, z_bot),
            rg.Point3d(-hl, hd, z_bot),
            rg.Point3d(-hl, -hd, z_bot),
        ]
        poly = rg.Polyline(pts).ToNurbsCurve()
        crv = rg.Curve.CreateFilletCornersCurve(poly, 2.2, 0.01, 0.01) or poly
    else:
        rect = rg.Rectangle3d(pl, rg.Interval(-hl, hl), rg.Interval(-hd, hd)).ToNurbsCurve()
        if shape_idx == 2:
            crv = rg.Curve.CreateFilletCornersCurve(rect, 3.0, 0.01, 0.01) or rect
        else:
            crv = rect

    slab = extrude_closed_curve_solid(crv, rg.Vector3d(0, 0, top_t))
    top_preview = crv.DuplicateCurve()
    top_preview.Translate(rg.Vector3d(0, 0, top_t))
    return slab, top_preview


def build_single_workstation_unit(S, fast=False, include_visitors=True):
    parts = []
    preview_curves = []

    d_style = int(S["desk_style"])
    t_shape = int(S["top_shape"])
    L = float(S["desk_len"])
    D = float(S["desk_d"])
    H = float(S["desk_h"])
    top_t = float(S["top_t"])
    ret_side = 1.0 if int(S["return_side"]) == 0 else -1.0
    ret_l = float(S["return_len"])
    ret_w = float(S["return_w"])
    scr_h = float(S["screen_h"])

    hl = L * 0.5
    hd = D * 0.5
    z_under = H - top_t

    # 1. Main Desktop Slab + Cable Grommets
    slab, top_crv = make_desk_top_slab(L, D, H, top_t, t_shape)
    add_part(parts, "desk_top", slab)
    if top_crv:
        preview_curves.append(top_crv)
    if not fast:
        for gx in (-hl + 8.0, hl - 8.0):
            add_part(parts, "desk_frame", make_cyl(rg.Point3d(gx, hd - 4.5, H - 0.1), rg.Vector3d.ZAxis, 1.25, 0.18))

    # 2. Desk Base / Frame / Pedestal / L-Return by Style
    if d_style == 0:
        lx = hl - 6.5
        foot_l = D * 0.86
        foot_h = 1.25
        z_mid_col = max(foot_h + 10.0, z_under * 0.52)
        for sx in (-1.0, 1.0):
            xc = sx * lx
            add_part(parts, "desk_frame", make_box_xy(xc - 1.4, xc + 1.4, -foot_l * 0.5, foot_l * 0.5, 0.2, foot_h))
            add_part(parts, "desk_frame", make_box_xy(xc - 1.5, xc + 1.5, -1.5, 1.5, foot_h, z_mid_col))
            add_part(parts, "desk_frame", make_box_xy(xc - 1.2, xc + 1.2, -1.2, 1.2, z_mid_col - 1.0, z_under - 1.2))
            add_part(parts, "desk_frame", make_box_xy(xc - 1.3, xc + 1.3, -D * 0.38, D * 0.38, z_under - 1.2, z_under))
        add_part(parts, "desk_frame", make_box_xy(-lx, lx, -2.2, 2.2, z_under - 1.6, z_under))
        add_part(parts, "desk_frame", make_box_xy(-lx * 0.7, lx * 0.7, hd * 0.25, hd * 0.65, z_under - 4.2, z_under - 3.8))
        px = ret_side * (hl - 9.0)
        add_part(parts, "tech", make_box_xy(px - 1.4, px + 1.4, -hd - 0.6, -hd + 2.0, z_under - 0.6, z_under))

    elif d_style == 1:
        # 1. Executive Pedestal Desk (Wood Credenza on "desk_top" layer + Dark Plinth & Pulls on "desk_frame")
        ped_w = min(16.5, L * 0.28)
        ped_d = D - 3.0
        px0 = (hl - 2.0 - ped_w) if ret_side > 0 else (-hl + 2.0)
        px1 = px0 + ped_w
        add_part(parts, "desk_top", make_box_xy(px0, px1, -ped_d * 0.5, ped_d * 0.5, 2.0, z_under))
        add_part(parts, "desk_frame", make_box_xy(px0 + 0.4, px1 - 0.4, -ped_d * 0.48, ped_d * 0.48, 0.0, 2.0))
        dr_z0 = 2.2
        dr_avail = z_under - 2.4
        z_splits = [dr_z0, dr_z0 + dr_avail * 0.46, dr_z0 + dr_avail * 0.73, z_under - 0.2]
        for d_i in range(3):
            zb, zt = z_splits[d_i] + 0.12, z_splits[d_i + 1] - 0.12
            add_part(parts, "desk_top", make_box_xy(px0 + 0.2, px1 - 0.2, -ped_d * 0.5 - 0.65, -ped_d * 0.5, zb, zt))
            if not fast:
                zm = zt - 1.2
                add_part(parts, "desk_frame", make_box_xy(0.5 * (px0 + px1) - 2.5, 0.5 * (px0 + px1) + 2.5, -ped_d * 0.5 - 1.1, -ped_d * 0.5 - 0.65, zm - 0.2, zm + 0.2))

        opp_x = (-hl + 2.5) if ret_side > 0 else (hl - 2.5)
        bar_w, bar_t = 2.4, 1.0
        add_part(parts, "desk_frame", make_box_xy(opp_x - bar_w * 0.5, opp_x + bar_w * 0.5, -ped_d * 0.5, -ped_d * 0.5 + bar_t, bar_t, z_under - bar_t))
        add_part(parts, "desk_frame", make_box_xy(opp_x - bar_w * 0.5, opp_x + bar_w * 0.5, ped_d * 0.5 - bar_t, ped_d * 0.5, bar_t, z_under - bar_t))
        add_part(parts, "desk_frame", make_box_xy(opp_x - bar_w * 0.5, opp_x + bar_w * 0.5, -ped_d * 0.5, ped_d * 0.5, 0.0, bar_t))
        add_part(parts, "desk_frame", make_box_xy(opp_x - bar_w * 0.5, opp_x + bar_w * 0.5, -ped_d * 0.5, ped_d * 0.5, z_under - bar_t, z_under))
        m_x0 = opp_x if ret_side > 0 else px1
        m_x1 = px0 if ret_side > 0 else opp_x
        add_part(parts, "desk_top", make_box_xy(min(m_x0, m_x1), max(m_x0, m_x1), hd * 0.55 - 0.75, hd * 0.55, 8.0, z_under))

    elif d_style == 2:
        bar_w, bar_t = 2.5, 1.1
        for sx in (-1.0, 1.0):
            xc = sx * (hl - 2.5)
            add_part(parts, "desk_frame", make_box_xy(xc - bar_w * 0.5, xc + bar_w * 0.5, -hd + 1.0, -hd + 1.0 + bar_t, bar_t, z_under - bar_t))
            add_part(parts, "desk_frame", make_box_xy(xc - bar_w * 0.5, xc + bar_w * 0.5, hd - 1.0 - bar_t, hd - 1.0, bar_t, z_under - bar_t))
            add_part(parts, "desk_frame", make_box_xy(xc - bar_w * 0.5, xc + bar_w * 0.5, -hd + 1.0, hd - 1.0, 0.0, bar_t))
            add_part(parts, "desk_frame", make_box_xy(xc - bar_w * 0.5, xc + bar_w * 0.5, -hd + 1.0, hd - 1.0, z_under - bar_t, z_under))
        add_part(parts, "desk_frame", make_box_xy(-hl + 2.5, hl - 2.5, -1.5, 1.5, z_under - 2.0, z_under))
        add_part(parts, "desk_top", make_box_xy(-hl + 4.0, hl - 4.0, hd - 3.5, hd - 2.9, z_under - 12.0, z_under - 1.5))

    elif d_style == 3:
        bar_w, bar_t = 2.2, 1.0
        opp_x = -ret_side * (hl - 2.5)
        add_part(parts, "desk_frame", make_box_xy(opp_x - bar_w * 0.5, opp_x + bar_w * 0.5, -hd + 1.0, -hd + 1.0 + bar_t, bar_t, z_under - bar_t))
        add_part(parts, "desk_frame", make_box_xy(opp_x - bar_w * 0.5, opp_x + bar_w * 0.5, hd - 1.0 - bar_t, hd - 1.0, bar_t, z_under - bar_t))
        add_part(parts, "desk_frame", make_box_xy(opp_x - bar_w * 0.5, opp_x + bar_w * 0.5, -hd + 1.0, hd - 1.0, 0.0, bar_t))
        rx0 = (hl - ret_w) if ret_side > 0 else -hl
        rx1 = hl if ret_side > 0 else (-hl + ret_w)
        ry0 = -hd - ret_l
        ry1 = -hd + 0.05
        add_part(parts, "desk_top", make_box_xy(rx0, rx1, ry0, ry1, z_under, H))
        ped_d = min(16.0, ret_l * 0.45)
        add_part(parts, "desk_top", make_box_xy(rx0 + 0.5, rx1 - 0.5, ry0 + 1.0, ry0 + 1.0 + ped_d, 1.5, z_under))
        add_part(parts, "desk_frame", make_box_xy(rx0 + 1.0, rx1 - 1.0, hd - 3.5, hd - 1.5, 0.0, z_under))

    elif d_style == 4:
        for sx in (-1.0, 1.0):
            xc = sx * (hl - 5.0)
            for sy in (-1.0, 1.0):
                p_top = rg.Point3d(xc, sy * (hd - 4.0), z_under)
                p_bot = rg.Point3d(xc + sx * 2.5, sy * (hd - 1.0), 0.0)
                add_part(parts, "desk_frame", make_tapered_leg(p_bot, p_top, 0.75, 1.25))
            add_part(parts, "desk_frame", make_member_between(
                rg.Point3d(xc + sx * 1.6, -hd + 2.0, z_under * 0.35),
                rg.Point3d(xc + sx * 1.6, hd - 2.0, z_under * 0.35),
                rg.Vector3d.ZAxis, 1.1, 1.4
            ))
        add_part(parts, "desk_frame", make_box_xy(-hl + 5.0, hl - 5.0, -1.8, 1.8, z_under - 2.2, z_under))

    else:
        for sx in (-1.0, 1.0):
            xc = sx * (hl - 2.0)
            add_part(parts, "desk_frame", make_box_xy(xc - 1.0, xc + 1.0, -hd + 1.5, -hd + 2.5, 0.0, z_under))
            add_part(parts, "desk_frame", make_box_xy(xc - 1.0, xc + 1.0, hd - 2.5, hd - 1.5, 0.0, z_under))
            add_part(parts, "desk_frame", make_box_xy(xc - 1.0, xc + 1.0, -hd + 1.5, hd - 1.5, z_under - 1.5, z_under))
        if scr_h > 1.0:
            st = 1.1
            z_s0 = H - 4.0
            z_s1 = H + scr_h
            add_part(parts, "cabinet", make_box_xy(-hl - st, hl + st, hd, hd + st, z_s0, z_s1))
            wing_d = D * 0.65
            add_part(parts, "cabinet", make_box_xy(-hl - st, -hl, hd - wing_d, hd, z_s0, z_s1))
            add_part(parts, "cabinet", make_box_xy(hl, hl + st, hd - wing_d, hd, z_s0, z_s1))

    # 3. Desktop Computer, Monitor Arm & Peripherals
    parts.extend(build_desktop_tech_equipment(S, H, fast))

    # 4. Ergonomic Office Chair(s)
    seat_mode = int(S["seating_mode"])
    chair_cnt = 0
    if seat_mode != 2:
        unit_chair = build_ergonomic_office_chair(S, fast)
        pull = float(S["pull_out"])
        swivel_rad = math.radians(float(S["chair_swivel"]))
        cd = float(S["chair_d"])

        y_op = -(hd + cd * 0.28 + pull)
        x_op = (-ret_side * 6.0) if (d_style in (1, 3)) else 0.0
        rot_op = rg.Transform.Rotation(swivel_rad, rg.Vector3d.ZAxis, rg.Point3d.Origin)
        tr_op = rg.Transform.Translation(x_op, y_op, 0.0)
        xf_op = tr_op * rot_op
        for kind, b in unit_chair:
            dup = b.DuplicateBrep()
            dup.Transform(xf_op)
            add_part(parts, kind, dup)
        chair_cnt += 1

        if include_visitors and seat_mode == 1:
            S_vis = dict(S)
            S_vis["chair_style"] = 2
            S_vis["has_headrest"] = False
            vis_chair = build_ergonomic_office_chair(S_vis, fast)
            y_vis = hd + cd * 0.45 + max(2.0, pull * 0.5)
            vis_x_off = max(16.0, hl * 0.52)
            for vx in (-vis_x_off, vis_x_off):
                rot_v = rg.Transform.Rotation(math.pi, rg.Vector3d.ZAxis, rg.Point3d.Origin)
                tr_v = rg.Transform.Translation(vx, y_vis, 0.0)
                xf_v = tr_v * rot_v
                for kind, b in vis_chair:
                    dup = b.DuplicateBrep()
                    dup.Transform(xf_v)
                    add_part(parts, kind, dup)
                chair_cnt += 1

    return parts, preview_curves, chair_cnt


# ============================================================
# MASTER OFFICE WORKSTATION & POD ASSEMBLER
# ============================================================
def build_office_desk_system(center_in, S, final=True, u=1.0):
    fast = (not final) and S["fast_preview"]
    preset_idx = int(S["size_preset"])
    L = float(S["desk_len"])
    D = float(S["desk_d"])
    rot_rad = math.radians(float(S["rot_deg"]))

    parts = []
    preview_curves = []
    total_chairs = 0

    if preset_idx in (6, 7):
        S_unit = dict(S)
        if S_unit["desk_style"] == 3:
            S_unit["desk_style"] = 0
        unit_parts, unit_crvs, unit_ch = build_single_workstation_unit(S_unit, fast, include_visitors=False)

        x_offsets = [0.0] if preset_idx == 6 else [-L * 0.5 - 0.5, L * 0.5 + 0.5]
        gap_y = 1.2

        for xo in x_offsets:
            tr_f = rg.Transform.Translation(xo, -(D * 0.5 + gap_y * 0.5), 0.0)
            for kind, b in unit_parts:
                dup = b.DuplicateBrep()
                dup.Transform(tr_f)
                add_part(parts, kind, dup)
            for c in unit_crvs:
                dc = c.DuplicateCurve()
                dc.Transform(tr_f)
                preview_curves.append(dc)
            total_chairs += unit_ch

            rot_180 = rg.Transform.Rotation(math.pi, rg.Vector3d.ZAxis, rg.Point3d.Origin)
            tr_b = rg.Transform.Translation(xo, D * 0.5 + gap_y * 0.5, 0.0)
            xf_b = tr_b * rot_180
            for kind, b in unit_parts:
                dup = b.DuplicateBrep()
                dup.Transform(xf_b)
                add_part(parts, kind, dup)
            for c in unit_crvs:
                dc = c.DuplicateCurve()
                dc.Transform(xf_b)
                preview_curves.append(dc)
            total_chairs += unit_ch

        H = float(S["desk_h"])
        scr_h = max(12.0, float(S["screen_h"]))
        total_pod_w = L if preset_idx == 6 else (2.0 * L + 1.0)
        add_part(parts, "cabinet", make_box_xy(-total_pod_w * 0.5, total_pod_w * 0.5, -0.5, 0.5, H - 6.0, H + scr_h))
        total_w_in = total_pod_w
        total_d_in = 2.0 * D + gap_y
    else:
        parts, preview_curves, total_chairs = build_single_workstation_unit(S, fast, include_visitors=True)
        total_w_in = L
        total_d_in = D + (float(S["return_len"]) if int(S["desk_style"]) == 3 else 0.0)

    rot_set = rg.Transform.Rotation(rot_rad, rg.Vector3d.ZAxis, rg.Point3d.Origin)
    tr_set = rg.Transform.Translation(center_in.X, center_in.Y, center_in.Z)
    scale_set = rg.Transform.Scale(rg.Point3d.Origin, u)
    full_xform = scale_set * tr_set * rot_set

    for _, b in parts:
        if b:
            b.Transform(full_xform)
    for c in preview_curves:
        if c:
            c.Transform(full_xform)

    info = {
        "total_w_in": total_w_in,
        "total_d_in": total_d_in,
        "chair_count": total_chairs,
    }
    return parts, preview_curves, info


# ============================================================
# LAYER & MATERIAL HELPERS (BAKE)
# ============================================================
def get_or_create_layer(doc, layer_name, parent_id=None, color=None):
    for i in range(doc.Layers.Count):
        layer = doc.Layers[i]
        try:
            if layer.IsDeleted:
                continue
        except Exception:
            pass
        if layer.Name == layer_name:
            if (parent_id is None and layer.ParentLayerId == System.Guid.Empty) or (parent_id is not None and layer.ParentLayerId == parent_id):
                return layer.Index
    new_layer = rdo.Layer()
    new_layer.Name = layer_name
    if parent_id is not None:
        new_layer.ParentLayerId = parent_id
    if color is not None:
        new_layer.Color = color
    return doc.Layers.Add(new_layer)


def get_or_create_material(doc, name, diffuse_color, transparency=0.0):
    for i in range(doc.Materials.Count):
        mat = doc.Materials[i]
        if mat.Name == name:
            return i
    mat = rdo.Material()
    mat.Name = name
    mat.DiffuseColor = diffuse_color
    if transparency > 0:
        try:
            mat.Transparency = transparency
        except Exception:
            pass
    return doc.Materials.Add(mat)


def get_or_create_layer_with_material(doc, layer_name, parent_id=None, default_color=None, mat_name=None, diffuse_color=None, transparency=0.0):
    for i in range(doc.Layers.Count):
        layer = doc.Layers[i]
        try:
            if layer.IsDeleted:
                continue
        except Exception:
            pass
        if layer.Name == layer_name:
            if (parent_id is None and layer.ParentLayerId == System.Guid.Empty) or (parent_id is not None and layer.ParentLayerId == parent_id):
                return layer.Index
    new_layer = rdo.Layer()
    new_layer.Name = layer_name
    if parent_id is not None:
        new_layer.ParentLayerId = parent_id
    if default_color is not None:
        new_layer.Color = default_color
    if mat_name:
        mat_idx = get_or_create_material(doc, mat_name, diffuse_color or default_color, transparency)
        new_layer.RenderMaterialIndex = mat_idx
    return doc.Layers.Add(new_layer)


def make_attributes(layer_index, name=None, state_json=None, item_index=None, item_center=None):
    attr = rdo.ObjectAttributes()
    attr.LayerIndex = layer_index
    attr.MaterialSource = rdo.ObjectMaterialSource.MaterialFromLayer
    attr.ColorSource = rdo.ObjectColorSource.ColorFromLayer
    if name:
        attr.Name = name
    if state_json:
        try:
            attr.SetUserString(METADATA_KEY, state_json)
        except Exception:
            pass
    if item_index is not None:
        try:
            attr.SetUserString(ITEM_INDEX_KEY, str(int(item_index)))
        except Exception:
            pass
    if item_center is not None:
        try:
            attr.SetUserString(ITEM_CENTER_KEY, json.dumps(_point_to_data(item_center)))
        except Exception:
            pass
    return attr


def bake_office_desk(doc, center_in, S, u=1.0, edit_target_ids=None):
    parts, _, _ = build_office_desk_system(center_in, S, True, u)

    tp_name, tp_rgb = TOP_FINISHES[S["top_finish"]]
    fr_name, fr_rgb = FRAME_FINISHES[S["frame_finish"]]
    ch_name, ch_rgb = CHAIR_FABRIC_FINISHES[S["chair_finish"]]
    sc_name, sc_rgb = SCREEN_FINISHES[S["screen_finish"]]

    top_trans = 0.42 if int(S["top_finish"]) == 6 else 0.0

    colors = {
        "desk_top": rgb_to_color(tp_rgb),
        "desk_frame": rgb_to_color(fr_rgb),
        "cabinet": rgb_to_color(sc_rgb),
        "chair_frame": rgb_to_color(fr_rgb),
        "chair_cushion": rgb_to_color(ch_rgb),
        "tech": rgb_to_color((35, 38, 42)),
    }

    main_layer_idx = get_or_create_layer(doc, "OFFICE_DESK")
    parent_id = doc.Layers[main_layer_idx].Id

    layers = {
        "desk_top": get_or_create_layer_with_material(doc, "DESK_TOP", parent_id, colors["desk_top"], "Office Top " + tp_name, colors["desk_top"], top_trans),
        "desk_frame": get_or_create_layer_with_material(doc, "DESK_FRAME", parent_id, colors["desk_frame"], "Office Frame " + fr_name, colors["desk_frame"]),
        "cabinet": get_or_create_layer_with_material(doc, "CABINET_SCREEN", parent_id, colors["cabinet"], "Office Screen " + sc_name, colors["cabinet"]),
        "chair_frame": get_or_create_layer_with_material(doc, "CHAIR_FRAME", parent_id, colors["chair_frame"], "Office Chair Frame " + fr_name, colors["chair_frame"]),
        "chair_cushion": get_or_create_layer_with_material(doc, "CHAIR_CUSHION", parent_id, colors["chair_cushion"], "Office Chair " + ch_name, colors["chair_cushion"]),
        "tech": get_or_create_layer_with_material(doc, "TECH_EQUIPMENT", parent_id, colors["tech"], "Office Tech Matte Black", colors["tech"]),
    }

    if edit_target_ids:
        for gid in edit_target_ids:
            try:
                doc.Objects.Delete(gid, True)
            except Exception:
                pass

    state_json = encode_state(center_in, S)
    ids = []
    for idx, (kind, brep) in enumerate(parts):
        if not brep or not brep.IsValid:
            continue
        c_pt = _brep_center(brep)
        attr = make_attributes(layers.get(kind, layers["desk_top"]), "Office_" + kind, state_json, idx, c_pt)
        oid = doc.Objects.AddBrep(brep, attr)
        if oid and oid != System.Guid.Empty:
            ids.append(oid)

    if ids:
        try:
            group_idx = doc.Groups.Add()
            doc.Groups.AddToGroup(group_idx, ids)
        except Exception:
            try:
                gname = rs.AddGroup()
                rs.AddObjectsToGroup(ids, gname)
            except Exception:
                pass
    return ids


# ============================================================
# LIVE VIEWPORT PREVIEW CONDUIT & INTERACTIVE PLACEMENT GETTER
# ============================================================
class OfficeDeskPreviewConduit(rd.DisplayConduit):
    def __init__(self, wireframe_only=False):
        super(OfficeDeskPreviewConduit, self).__init__()
        self.preview_breps = []
        self.preview_curves = []
        self.wireframe_only = wireframe_only
        self.materials = {}
        self.set_finishes(default_settings())

    def set_finishes(self, S):
        tp_rgb = TOP_FINISHES[S["top_finish"]][1]
        fr_rgb = FRAME_FINISHES[S["frame_finish"]][1]
        ch_rgb = CHAIR_FABRIC_FINISHES[S["chair_finish"]][1]
        sc_rgb = SCREEN_FINISHES[S["screen_finish"]][1]
        top_trans = 0.42 if int(S["top_finish"]) == 6 else 0.0
        self.materials = {
            "desk_top": rd.DisplayMaterial(rgb_to_color(tp_rgb), top_trans),
            "desk_frame": rd.DisplayMaterial(rgb_to_color(fr_rgb)),
            "cabinet": rd.DisplayMaterial(rgb_to_color(sc_rgb)),
            "chair_frame": rd.DisplayMaterial(rgb_to_color(fr_rgb)),
            "chair_cushion": rd.DisplayMaterial(rgb_to_color(ch_rgb)),
            "tech": rd.DisplayMaterial(rgb_to_color((35, 38, 42))),
        }

    def CalculateBoundingBox(self, e):
        try:
            bbox = rg.BoundingBox.Empty
            for kind, brep in self.preview_breps:
                if brep and brep.IsValid:
                    bbox = rg.BoundingBox.Union(bbox, brep.GetBoundingBox(False))
            for crv in self.preview_curves:
                if crv and crv.IsValid:
                    bbox = rg.BoundingBox.Union(bbox, crv.GetBoundingBox(False))
            if bbox.IsValid:
                e.IncludeBoundingBox(bbox)
        except Exception:
            pass

    def PostDrawObjects(self, e):
        try:
            for kind, brep in self.preview_breps:
                if not brep or not brep.IsValid:
                    continue
                if self.wireframe_only:
                    col = System.Drawing.Color.Gold if kind == "desk_top" else System.Drawing.Color.DeepSkyBlue
                    e.Display.DrawBrepWires(brep, col, 1)
                else:
                    mat = self.materials.get(kind, self.materials["desk_top"])
                    if mat:
                        e.Display.DrawBrepShaded(brep, mat)
                    e.Display.DrawBrepWires(brep, System.Drawing.Color.FromArgb(40, 40, 45), 1)
            for crv in self.preview_curves:
                if crv and crv.IsValid:
                    e.Display.DrawCurve(crv, System.Drawing.Color.Gold, 2)
        except Exception:
            pass


class OfficeSpanPointGetter(ric.GetPoint):
    def __init__(self, p0_doc, settings, u_scale, fixed_length=False):
        super(OfficeSpanPointGetter, self).__init__()
        self.p0_doc = rg.Point3d(p0_doc)
        self.u = u_scale if u_scale > 0 else 1.0
        self.fixed_length = fixed_length
        self.S = dict(settings)
        self.S["fast_preview"] = True

    def OnDynamicDraw(self, e):
        try:
            curr = e.CurrentPoint
            dx = curr.X - self.p0_doc.X
            dy = curr.Y - self.p0_doc.Y
            dist_doc = math.sqrt(dx * dx + dy * dy)
            if dist_doc < 2.0 * self.u:
                return
            ang_deg = int(round(math.degrees(math.atan2(dy, dx))))
            temp_s = dict(self.S)
            temp_s["rot_deg"] = ang_deg
            if not self.fixed_length and (dist_doc / self.u) >= 30.0:
                temp_s["desk_len"] = clamp(dist_doc / self.u, 30.0, 144.0)
                mid_doc = 0.5 * (self.p0_doc + rg.Point3d(curr.X, curr.Y, self.p0_doc.Z))
            else:
                mid_doc = self.p0_doc

            c_in = rg.Point3d(mid_doc.X / self.u, mid_doc.Y / self.u, mid_doc.Z / self.u)
            parts, _, _ = build_office_desk_system(c_in, temp_s, False, self.u)
            for kind, brep in parts:
                if brep and brep.IsValid:
                    col = System.Drawing.Color.Gold if kind in ("desk_top", "desk_frame") else System.Drawing.Color.DeepSkyBlue
                    e.Display.DrawBrepWires(brep, col, 1)
        except Exception:
            pass


# ============================================================
# DIALOG UI (3 TABS + SIT-STAND / PULL-OUT / SWIVEL / ROTATION SLIDERS)
# ============================================================
class NumField(object):
    def __init__(self, key, label, default, mn, mx, is_int, value, unit_name="in", scale_from_inch=1.0):
        self.key = key
        self.label = label
        self.mn = mn
        self.mx = mx
        self.is_int = is_int
        self.unit_name = unit_name
        self.scale_from_inch = scale_from_inch
        self.is_length = (key not in NON_LENGTH_KEYS and not is_int)
        self.last_inch = value
        disp_val = value * (scale_from_inch if self.is_length else 1.0)
        self.textbox = make_textbox(format_office_length(disp_val, unit_name, is_int))

    def value(self):
        try:
            txt = self.textbox.Text.strip()
            if self.is_length:
                val_unit = parse_office_length(txt, self.unit_name)
                val_inch = val_unit / self.scale_from_inch
            else:
                val_inch = float(txt)
            val_inch = clamp(val_inch, self.mn, self.mx)
            if self.is_int:
                val_inch = int(round(val_inch))
            self.last_inch = val_inch
        except Exception:
            pass
        return self.last_inch

    def set_value(self, v):
        v = clamp(v, self.mn, self.mx)
        if self.is_int:
            v = int(round(v))
        self.last_inch = v
        disp_val = v * (self.scale_from_inch if self.is_length else 1.0)
        self.textbox.Text = format_office_length(disp_val, self.unit_name, self.is_int)


class OfficeDeskDialog(forms.Dialog[bool]):
    def __init__(self):
        super(OfficeDeskDialog, self).__init__()
        self._initialized = False
        self._preview_closed = False
        self._suppress_preview_update = True
        self._syncing_h = False
        self._syncing_rot = False
        self._syncing_pull = False
        self._syncing_swiv = False
        self.final_settings = None
        self.conduit = None

    def Initialize(self, center_in, initial_settings=None, is_edit=False):
        if self._initialized:
            return
        self._initialized = True

        unit_sys, unit_name, scale_from_inch = get_doc_unit_info()
        self.unit_name = unit_name
        self.scale_from_inch = scale_from_inch
        self.center_in = rg.Point3d(center_in)
        self.is_edit = is_edit

        title_prefix = "Edit Office Workstation & Chair" if is_edit else "Modern Office Desk & Ergonomic Chair Generator"
        self.Title = "%s [%s]" % (title_prefix, unit_name)
        self.Padding = drawing.Padding(10)
        self.Resizable = True
        try:
            self.Topmost = True
        except Exception:
            pass
        self.ClientSize = drawing.Size(670, 760)

        prev_conduit = sc.sticky.get(CONDUIT_KEY)
        if prev_conduit is not None:
            try:
                prev_conduit.Enabled = False
            except Exception:
                pass

        self.conduit = OfficeDeskPreviewConduit(wireframe_only=False)
        self.conduit.Enabled = True
        sc.sticky[CONDUIT_KEY] = self.conduit

        s = normalize_settings(initial_settings) if initial_settings else get_initial_settings()
        self.presets = load_presets()
        self._preset_items = ["<Select preset>"]

        self.fields = {}
        self.labels = {}
        for key, label, dflt, mn, mx, is_int in NUM_FIELDS:
            disp_label = update_label_unit(label, unit_name)
            self.fields[key] = NumField(key, disp_label, dflt, mn, mx, is_int, s[key], unit_name, scale_from_inch)
            self.labels[key] = disp_label

        self.dds = {}
        for key, label, dflt, names in DD_FIELDS:
            dd = forms.DropDown()
            dd.DataStore = list(names)
            dd.SelectedIndex = int(s[key])
            self.dds[key] = dd
            self.labels[key] = label

        h_init_in = clamp(s["desk_h"], 27.0, 46.0)
        self.sli_h = forms.Slider()
        self.sli_h.MinValue = 270
        self.sli_h.MaxValue = 460
        self.sli_h.Value = int(round(h_init_in * 10.0))

        h_layout = forms.DynamicLayout()
        h_layout.Spacing = drawing.Size(4, 0)
        h_layout.BeginHorizontal()
        dl_add(h_layout, self.sli_h, True, False)
        dl_add(h_layout, self.fields["desk_h"].textbox, False, False)
        h_layout.EndHorizontal()

        rot_init = int(clamp(s["rot_deg"], -180, 180))
        self.sli_rot = forms.Slider()
        self.sli_rot.MinValue = -180
        self.sli_rot.MaxValue = 180
        self.sli_rot.Value = rot_init
        self.txt_rot_val = make_textbox(str(rot_init), width=55)

        rot_layout = forms.DynamicLayout()
        rot_layout.Spacing = drawing.Size(4, 0)
        rot_layout.BeginHorizontal()
        dl_add(rot_layout, self.sli_rot, True, False)
        dl_add(rot_layout, self.txt_rot_val, False, False)
        dl_add(rot_layout, make_label("deg"), False, False)
        rot_layout.EndHorizontal()

        pull_init_in = clamp(s["pull_out"], -8.0, 24.0)
        self.sli_pull = forms.Slider()
        self.sli_pull.MinValue = -80
        self.sli_pull.MaxValue = 240
        self.sli_pull.Value = int(round(pull_init_in * 10.0))

        pull_layout = forms.DynamicLayout()
        pull_layout.Spacing = drawing.Size(4, 0)
        pull_layout.BeginHorizontal()
        dl_add(pull_layout, self.sli_pull, True, False)
        dl_add(pull_layout, self.fields["pull_out"].textbox, False, False)
        pull_layout.EndHorizontal()

        swiv_init = int(clamp(s["chair_swivel"], -45, 45))
        self.sli_swiv = forms.Slider()
        self.sli_swiv.MinValue = -45
        self.sli_swiv.MaxValue = 45
        self.sli_swiv.Value = swiv_init
        self.txt_swiv_val = make_textbox(str(swiv_init), width=55)

        swiv_layout = forms.DynamicLayout()
        swiv_layout.Spacing = drawing.Size(4, 0)
        swiv_layout.BeginHorizontal()
        dl_add(swiv_layout, self.sli_swiv, True, False)
        dl_add(swiv_layout, self.txt_swiv_val, False, False)
        dl_add(swiv_layout, make_label("deg"), False, False)
        swiv_layout.EndHorizontal()

        self.cb_headrest = make_checkbox("Include ergonomic headrest / high-back bolster", s["has_headrest"])
        self.cb_fast = make_checkbox("Fast preview while dragging sliders", s["fast_preview"])

        self.dd_preset = forms.DropDown()
        self.dd_preset.Width = 190
        self.txt_preset_name = make_textbox("", width=150)
        self.btn_preset_load = make_button("Load")
        self.btn_preset_save = make_button("Save")
        self.btn_preset_delete = make_button("Delete")
        self._refresh_preset_dropdown()

        main = forms.DynamicLayout()
        main.Spacing = drawing.Size(5, 5)

        self.summary_lbl = make_label("", bold=True)
        main.AddRow(self.summary_lbl)

        preset_load_layout = forms.DynamicLayout()
        preset_load_layout.BeginHorizontal()
        dl_add(preset_load_layout, self.dd_preset, True, False)
        dl_add(preset_load_layout, self.btn_preset_load, False, False)
        preset_load_layout.EndHorizontal()
        main.AddRow(make_label("Preset list:"), preset_load_layout)

        preset_save_layout = forms.DynamicLayout()
        preset_save_layout.BeginHorizontal()
        dl_add(preset_save_layout, self.txt_preset_name, True, False)
        dl_add(preset_save_layout, self.btn_preset_save, False, False)
        dl_add(preset_save_layout, self.btn_preset_delete, False, False)
        preset_save_layout.EndHorizontal()
        main.AddRow(make_label("Preset name:"), preset_save_layout)

        self.tabs = forms.TabControl()
        for title, keys in TAB_LAYOUT:
            tab_layout = forms.DynamicLayout()
            tab_layout.Padding = drawing.Padding(10)
            tab_layout.Spacing = drawing.Size(5, 5)
            for key in keys:
                if key == "@height_row":
                    tab_layout.AddRow(make_label(self.labels["desk_h"], bold=True), h_layout)
                elif key == "@rot_row":
                    tab_layout.AddRow(make_label("Workstation rotation (-180 to +180):", bold=True), rot_layout)
                elif key == "@pull_row":
                    tab_layout.AddRow(make_label(self.labels["pull_out"], bold=True), pull_layout)
                elif key == "@swivel_row":
                    tab_layout.AddRow(make_label("Chair swivel angle (-45 to +45):", bold=True), swiv_layout)
                elif key == "@headrest":
                    tab_layout.AddRow(make_label(""), self.cb_headrest)
                elif key == "@fast":
                    tab_layout.AddRow(make_label(""), self.cb_fast)
                elif key in self.dds:
                    is_bold = (key == "size_preset")
                    tab_layout.AddRow(make_label(self.labels[key], bold=is_bold), self.dds[key])
                elif key in self.fields:
                    tab_layout.AddRow(make_label(self.labels[key]), self.fields[key].textbox)
            dl_add(tab_layout, make_label(""), False, True)

            scrollable = forms.Scrollable()
            try:
                scrollable.Border = getattr(forms.BorderType, "None")
            except Exception:
                pass
            scrollable.ExpandContentWidth = True
            scrollable.Content = tab_layout

            page = forms.TabPage()
            page.Text = title.replace("&&", "&")
            page.Content = scrollable
            self.tabs.Pages.Add(page)
        dl_add(main, self.tabs, True, True)

        self.lbl_info = make_label("", bold=True)
        main.AddRow(self.lbl_info)

        self.lbl_status = make_label("")
        try:
            self.lbl_status.TextColor = drawing.Colors.Red
        except Exception:
            pass
        main.AddRow(self.lbl_status)

        btn_ok = make_button("Apply Edit" if is_edit else "Create Office Desk")
        btn_ok.Click += self.OnOkClicked
        btn_cancel = make_button("Cancel")
        btn_cancel.Click += self.OnCancelClicked
        self.DefaultButton = btn_ok
        self.AbortButton = btn_cancel

        btn_layout = forms.DynamicLayout()
        btn_layout.BeginHorizontal()
        dl_add(btn_layout, btn_ok, True, False)
        dl_add(btn_layout, btn_cancel, False, False)
        btn_layout.EndHorizontal()
        main.AddRow(btn_layout)
        self.Content = main

        self.Closed += self.OnDialogClosed
        for key, f in self.fields.items():
            if key == "desk_h":
                f.textbox.TextChanged += self.OnHeightTextChanged
            elif key == "pull_out":
                f.textbox.TextChanged += self.OnPullTextChanged
            else:
                f.textbox.TextChanged += self.OnAnyChanged
        for key, dd in self.dds.items():
            if key == "size_preset":
                dd.SelectedIndexChanged += self.OnSizePresetChanged
            else:
                dd.SelectedIndexChanged += self.OnAnyChanged

        self.sli_h.ValueChanged += self.OnHeightSliderChanged
        self.sli_rot.ValueChanged += self.OnRotSliderChanged
        self.txt_rot_val.TextChanged += self.OnRotTextChanged
        self.sli_pull.ValueChanged += self.OnPullSliderChanged
        self.sli_swiv.ValueChanged += self.OnSwivSliderChanged
        self.txt_swiv_val.TextChanged += self.OnSwivTextChanged
        self.cb_headrest.CheckedChanged += self.OnAnyChanged
        self.cb_fast.CheckedChanged += self.OnAnyChanged

        self.dd_preset.SelectedIndexChanged += self.OnPresetSelectedChanged
        self.btn_preset_load.Click += self.OnPresetLoadClicked
        self.btn_preset_save.Click += self.OnPresetSaveClicked
        self.btn_preset_delete.Click += self.OnPresetDeleteClicked

        self.UpdateEnabling()
        self._suppress_preview_update = False
        self.UpdatePreview()

    def OnSizePresetChanged(self, sender, e):
        if getattr(self, "_suppress_preview_update", False):
            return
        p_idx = int(self.dds["size_preset"].SelectedIndex)
        if p_idx in WORKSTATION_SPECS:
            dl, dd, rl, f_style = WORKSTATION_SPECS[p_idx]
            self._suppress_preview_update = True
            try:
                self.fields["desk_len"].set_value(dl)
                self.fields["desk_d"].set_value(dd)
                self.fields["return_len"].set_value(rl)
                if f_style is not None:
                    self.dds["desk_style"].SelectedIndex = f_style
                if p_idx == 4:
                    self.dds["seating_mode"].SelectedIndex = 1
            finally:
                self._suppress_preview_update = False
        self.UpdateEnabling()
        self.UpdatePreview()

    def OnHeightSliderChanged(self, sender, e):
        if self._syncing_h:
            return
        v_in = clamp(self.sli_h.Value / 10.0, 25.0, 48.0)
        self._syncing_h = True
        self.fields["desk_h"].set_value(v_in)
        self._syncing_h = False
        self.UpdatePreview()

    def OnHeightTextChanged(self, sender, e):
        if self._syncing_h:
            return
        v_in = self.fields["desk_h"].value()
        self._syncing_h = True
        sli_v = int(clamp(round(v_in * 10.0), 270, 460))
        if self.sli_h.Value != sli_v:
            self.sli_h.Value = sli_v
        self._syncing_h = False
        self.UpdatePreview()

    def OnRotSliderChanged(self, sender, e):
        if self._syncing_rot:
            return
        v = int(clamp(self.sli_rot.Value, -180, 180))
        self._syncing_rot = True
        self.txt_rot_val.Text = str(v)
        self._syncing_rot = False
        self.UpdatePreview()

    def OnRotTextChanged(self, sender, e):
        if self._syncing_rot:
            return
        txt = self.txt_rot_val.Text.strip()
        if txt in ("", "-", "+"):
            return
        try:
            v = int(clamp(round(float(txt)), -180, 180))
        except Exception:
            return
        self._syncing_rot = True
        if self.sli_rot.Value != v:
            self.sli_rot.Value = v
        self._syncing_rot = False
        self.UpdatePreview()

    def OnPullSliderChanged(self, sender, e):
        if self._syncing_pull:
            return
        v_in = clamp(self.sli_pull.Value / 10.0, -8.0, 24.0)
        self._syncing_pull = True
        self.fields["pull_out"].set_value(v_in)
        self._syncing_pull = False
        self.UpdatePreview()

    def OnPullTextChanged(self, sender, e):
        if self._syncing_pull:
            return
        v_in = self.fields["pull_out"].value()
        self._syncing_pull = True
        sli_v = int(round(v_in * 10.0))
        if self.sli_pull.Value != sli_v:
            self.sli_pull.Value = sli_v
        self._syncing_pull = False
        self.UpdatePreview()

    def OnSwivSliderChanged(self, sender, e):
        if self._syncing_swiv:
            return
        v = int(clamp(self.sli_swiv.Value, -45, 45))
        self._syncing_swiv = True
        self.txt_swiv_val.Text = str(v)
        self._syncing_swiv = False
        self.UpdatePreview()

    def OnSwivTextChanged(self, sender, e):
        if self._syncing_swiv:
            return
        txt = self.txt_swiv_val.Text.strip()
        if txt in ("", "-", "+"):
            return
        try:
            v = int(clamp(round(float(txt)), -45, 45))
        except Exception:
            return
        self._syncing_swiv = True
        if self.sli_swiv.Value != v:
            self.sli_swiv.Value = v
        self._syncing_swiv = False
        self.UpdatePreview()

    def UpdateEnabling(self):
        d_style = int(self.dds["desk_style"].SelectedIndex)
        p_idx = int(self.dds["size_preset"].SelectedIndex)
        is_l_desk = (d_style == 3) and (p_idx not in (6, 7))
        self.fields["return_len"].textbox.Enabled = is_l_desk
        self.fields["return_w"].textbox.Enabled = is_l_desk
        self.fields["screen_h"].textbox.Enabled = (d_style == 5) or (p_idx in (6, 7))

        has_chairs = (int(self.dds["seating_mode"].SelectedIndex) != 2)
        self.dds["chair_style"].Enabled = has_chairs
        self.cb_headrest.Enabled = has_chairs
        self.sli_pull.Enabled = has_chairs
        self.sli_swiv.Enabled = has_chairs
        self.txt_swiv_val.Enabled = has_chairs
        for k in ("pull_out", "chair_w", "chair_d", "seat_h", "chair_h"):
            self.fields[k].textbox.Enabled = has_chairs

    def OnAnyChanged(self, sender, e):
        self.UpdateEnabling()
        self.UpdatePreview()

    def GetCurrentSettings(self):
        raw = {}
        for key, f in self.fields.items():
            raw[key] = f.value()
        for key, dd in self.dds.items():
            raw[key] = int(dd.SelectedIndex)
        raw["rot_deg"] = int(clamp(self.sli_rot.Value, -180, 180))
        raw["chair_swivel"] = int(clamp(self.sli_swiv.Value, -45, 45))
        raw["has_headrest"] = is_checkbox_checked(self.cb_headrest)
        raw["fast_preview"] = is_checkbox_checked(self.cb_fast)
        return normalize_settings(raw)

    def ApplySettingsToUI(self, settings):
        s = normalize_settings(settings)
        self._suppress_preview_update = True
        try:
            for key, f in self.fields.items():
                f.set_value(s[key])
            for key, dd in self.dds.items():
                dd.SelectedIndex = int(s[key])
            self._syncing_h = True
            self.sli_h.Value = int(clamp(round(s["desk_h"] * 10.0), 270, 460))
            self._syncing_h = False
            self._syncing_rot = True
            self.sli_rot.Value = int(s["rot_deg"])
            self.txt_rot_val.Text = str(int(s["rot_deg"]))
            self._syncing_rot = False
            self._syncing_pull = True
            self.sli_pull.Value = int(round(s["pull_out"] * 10.0))
            self._syncing_pull = False
            self._syncing_swiv = True
            self.sli_swiv.Value = int(s["chair_swivel"])
            self.txt_swiv_val.Text = str(int(s["chair_swivel"]))
            self._syncing_swiv = False
            set_checkbox_checked(self.cb_headrest, s["has_headrest"])
            set_checkbox_checked(self.cb_fast, s["fast_preview"])
            self.UpdateEnabling()
        finally:
            self._suppress_preview_update = False
        self.UpdatePreview()

    def _refresh_preset_dropdown(self, selected_name=None):
        names = sorted(self.presets.keys()) if self.presets else []
        self._preset_items = ["<Select preset>"] + names
        self.dd_preset.DataStore = list(self._preset_items)
        if selected_name and selected_name in names:
            self.dd_preset.SelectedIndex = names.index(selected_name) + 1
            self.txt_preset_name.Text = selected_name
        else:
            self.dd_preset.SelectedIndex = 0

    def _selected_preset_name(self):
        try:
            idx = int(self.dd_preset.SelectedIndex)
        except Exception:
            idx = 0
        if idx <= 0 or idx >= len(self._preset_items):
            return None
        return str(self._preset_items[idx])

    def OnPresetSelectedChanged(self, sender, e):
        name = self._selected_preset_name()
        if name:
            self.txt_preset_name.Text = name

    def OnPresetLoadClicked(self, sender, e):
        name = self._selected_preset_name() or str(self.txt_preset_name.Text).strip()
        if not name or name not in self.presets:
            rs.MessageBox("Select a preset to load.", 0, "Preset")
            return
        self.ApplySettingsToUI(self.presets[name])

    def OnPresetSaveClicked(self, sender, e):
        name = str(self.txt_preset_name.Text).strip()
        if not name:
            rs.MessageBox("Enter a preset name.", 0, "Save Preset")
            return
        if name in self.presets:
            rc = rs.MessageBox("Overwrite existing preset '%s'?" % name, 4, "Save Preset")
            if rc != 6:
                return
        self.presets[name] = self.GetCurrentSettings()
        if save_presets(self.presets):
            self._refresh_preset_dropdown(name)

    def OnPresetDeleteClicked(self, sender, e):
        name = self._selected_preset_name() or str(self.txt_preset_name.Text).strip()
        if not name or name not in self.presets:
            return
        rc = rs.MessageBox("Delete preset '%s'?" % name, 4, "Delete Preset")
        if rc != 6:
            return
        del self.presets[name]
        if save_presets(self.presets):
            self.txt_preset_name.Text = ""
            self._refresh_preset_dropdown()

    def UpdatePreview(self):
        if getattr(self, "_preview_closed", False) or getattr(self, "_suppress_preview_update", False):
            return
        try:
            S = self.GetCurrentSettings()
            self.conduit.set_finishes(S)
            parts, curves, info = build_office_desk_system(
                self.center_in, S, False, self.scale_from_inch
            )
            self.conduit.preview_breps = parts
            self.conduit.preview_curves = curves

            disp_w = format_office_length(info.get("total_w_in", 0.0) * self.scale_from_inch, self.unit_name)
            disp_d = format_office_length(info.get("total_d_in", 0.0) * self.scale_from_inch, self.unit_name)
            disp_h = format_office_length(S["desk_h"] * self.scale_from_inch, self.unit_name)
            self.summary_lbl.Text = "Footprint: %s x %s %s   |   Desk Height: %s %s   |   Chairs: %d" % (
                disp_w, disp_d, self.unit_name, disp_h, self.unit_name, info.get("chair_count", 0)
            )
            self.lbl_info.Text = "Chairs: %d  |  Swivel: %d deg  |  Rotation: %d deg  |  3D Parts: %d" % (
                info.get("chair_count", 0), S["chair_swivel"], S["rot_deg"], len(parts)
            )
            self.lbl_status.Text = ""
        except Exception as ex:
            self.conduit.preview_breps = []
            self.conduit.preview_curves = []
            self.lbl_status.Text = str(ex)

        try:
            Rhino.RhinoDoc.ActiveDoc.Views.Redraw()
        except Exception:
            pass

    def OnOkClicked(self, sender, e):
        settings = self.GetCurrentSettings()
        sc.sticky[STICKY_KEY] = settings
        self.final_settings = settings
        self.ClosePreview()
        self.Close(True)

    def OnCancelClicked(self, sender, e):
        self.ClosePreview()
        self.Close(False)

    def OnDialogClosed(self, sender, e):
        self.ClosePreview()

    def ClosePreview(self):
        if getattr(self, "_preview_closed", False):
            return
        self._preview_closed = True
        if self.conduit is not None:
            try:
                self.conduit.Enabled = False
                self.conduit.preview_breps = []
                self.conduit.preview_curves = []
            except Exception:
                pass
        if sc.sticky.get(CONDUIT_KEY) is self.conduit:
            try:
                del sc.sticky[CONDUIT_KEY]
            except Exception:
                pass
        try:
            Rhino.RhinoDoc.ActiveDoc.Views.Redraw()
        except Exception:
            pass


def show_office_dialog(dlg, doc):
    parent = None
    try:
        parent = Rhino.UI.RhinoEtoApp.MainWindowForDocument(doc)
    except Exception:
        parent = None
    if parent is None:
        try:
            parent = Rhino.UI.RhinoEtoApp.MainWindow
        except Exception:
            parent = None
    try:
        Rhino.UI.EtoExtensions.ShowSemiModal(dlg, doc, parent)
        return dlg.final_settings is not None
    except Exception:
        try:
            if parent is not None:
                dlg.ShowModal(parent)
            else:
                dlg.ShowModal()
            return dlg.final_settings is not None
        except Exception:
            return dlg.final_settings is not None


# ============================================================
# MAIN COMMAND ENTRY POINT
# ============================================================
def create_modern_office_desk():
    doc = Rhino.RhinoDoc.ActiveDoc or sc.doc
    unit_sys, unit_name, u = get_doc_unit_info(doc)
    init_s = get_initial_settings()

    mode = "center"
    first_pt_doc = None

    while True:
        initial_gp = ric.GetPoint()
        initial_gp.SetCommandPrompt("Pick center point of office desk")
        initial_gp.AcceptNothing(True)
        opt_center = initial_gp.AddOption("PickCenter")
        opt_span = initial_gp.AddOption("DrawSpan")
        opt_select = initial_gp.AddOption("SelectExisting")

        rc = initial_gp.Get()
        if rc == Rhino.Input.GetResult.Point:
            first_pt_doc = initial_gp.Point()
            break
        elif rc == Rhino.Input.GetResult.Option:
            idx = initial_gp.OptionIndex()
            if idx == opt_select:
                mode = "select"
                break
            elif idx == opt_span:
                mode = "span"
                p1 = rs.GetPoint("Pick start point of office desk span")
                if not p1:
                    return
                first_pt_doc = rg.Point3d(p1.X, p1.Y, p1.Z)
                break
            elif idx == opt_center:
                mode = "center"
                p1 = rs.GetPoint("Pick center point of office desk")
                if not p1:
                    return
                first_pt_doc = rg.Point3d(p1.X, p1.Y, p1.Z)
                break
        elif rc == Rhino.Input.GetResult.Nothing:
            p1 = rs.GetPoint("Pick center point of office desk")
            if not p1:
                return
            first_pt_doc = rg.Point3d(p1.X, p1.Y, p1.Z)
            break
        else:
            return

    center_in = None
    edit_target_ids = []

    if mode == "select":
        go = ric.GetObject()
        go.SetCommandPrompt("Select an existing Office Desk or Chair from a generated workstation to edit")
        go.GeometryFilter = rdo.ObjectType.Brep | rdo.ObjectType.Extrusion
        go.SubObjectSelect = False
        go.EnablePreSelect(True, True)
        if go.Get() != Rhino.Input.GetResult.Object:
            return
        obj = go.Object(0).Object()
        state_txt = obj.Attributes.GetUserString(METADATA_KEY) if obj else None
        decoded = decode_state(state_txt) if state_txt else None
        if not decoded:
            rs.MessageBox("Selected object is not a valid ArchTools Office Desk.", 48, "Office Desk Edit")
            return
        saved_c_in, saved_s = decoded
        edit_target_ids = get_generated_group_member_ids(doc, obj)
        center_in, init_s = transform_center_from_current_objects(doc, saved_c_in, saved_s, edit_target_ids, u)

    elif mode == "span":
        gp_s = OfficeSpanPointGetter(first_pt_doc, init_s, u, fixed_length=False)
        gp_s.SetCommandPrompt("Pick end point of office desk width & orientation")
        gp_s.SetBasePoint(first_pt_doc, True)
        gp_s.DrawLineFromPoint(first_pt_doc, True)
        if gp_s.Get() != Rhino.Input.GetResult.Point:
            return
        p2 = gp_s.Point()
        dx = p2.X - first_pt_doc.X
        dy = p2.Y - first_pt_doc.Y
        dist_doc = math.sqrt(dx * dx + dy * dy)
        if (dist_doc / u) >= 30.0:
            init_s["desk_len"] = clamp(dist_doc / u, 30.0, 144.0)
            init_s["size_preset"] = 0
        init_s["rot_deg"] = int(round(math.degrees(math.atan2(dy, dx))))
        mid_doc = 0.5 * (first_pt_doc + rg.Point3d(p2.X, p2.Y, first_pt_doc.Z))
        center_in = rg.Point3d(mid_doc.X / u, mid_doc.Y / u, mid_doc.Z / u)

    else:
        gp_r = OfficeSpanPointGetter(first_pt_doc, init_s, u, fixed_length=True)
        gp_r.SetCommandPrompt("Pick direction to orient office desk (or press ENTER for 0 deg)")
        gp_r.SetBasePoint(first_pt_doc, True)
        gp_r.DrawLineFromPoint(first_pt_doc, True)
        gp_r.AcceptNothing(True)
        rc_r = gp_r.Get()
        if rc_r == Rhino.Input.GetResult.Point:
            p2 = gp_r.Point()
            dx = p2.X - first_pt_doc.X
            dy = p2.Y - first_pt_doc.Y
            if math.sqrt(dx * dx + dy * dy) > 1.0 * u:
                init_s["rot_deg"] = int(round(math.degrees(math.atan2(dy, dx))))
        elif rc_r != Rhino.Input.GetResult.Nothing:
            return
        center_in = rg.Point3d(first_pt_doc.X / u, first_pt_doc.Y / u, first_pt_doc.Z / u)

    dlg = OfficeDeskDialog()
    dlg.Initialize(
        center_in,
        initial_settings=init_s,
        is_edit=bool(edit_target_ids),
    )
    dialog_result = False
    try:
        dialog_result = show_office_dialog(dlg, doc)
    finally:
        try:
            dlg.ClosePreview()
        except Exception:
            pass

    if not dialog_result or not dlg.final_settings:
        return

    S = dlg.final_settings

    sn = doc.BeginUndoRecord("Create Modern Office Desk & Chair")
    rs.EnableRedraw(False)
    try:
        ids = bake_office_desk(doc, center_in, S, u, edit_target_ids)
    except Exception as ex:
        ids = []
        import traceback
        traceback.print_exc()
        rs.MessageBox("Unexpected error creating office desk: {}".format(ex), 0, "Office Desk Error")
    finally:
        rs.EnableRedraw(True)
        if sn > 0:
            doc.EndUndoRecord(sn)

    doc.Views.Redraw()
    if ids:
        print("\nModern Office Desk & Ergonomic Chair Created Successfully!")
        print("Desk: {:.1f} x {:.1f} {} | Height: {:.1f} {}".format(
            S["desk_len"] * u, S["desk_d"] * u, unit_name, S["desk_h"] * u, unit_name
        ))


def run():
    create_modern_office_desk()


if __name__ in ["__main__", "ArchOfficeDesk", "OfficeDesk", "__builtin__"]:
    create_modern_office_desk()