# -*- coding: utf-8 -*-
# ==============================================================================
# Shalik Furniture Suite - Parametric Generator
# Author & Architect: Sakhawat Hosen Sumon (arch.sakhawat@gmail.com)
# GitHub: https://github.com/arch-sakhawat/SHALIK-FURNITURE
# Copyright (c) 2026 Sakhawat Hosen Sumon. All Rights Reserved.
# THIS SOFTWARE IS STRICTLY PROPRIETARY AND COMMERCIAL - NOT FREE.
# Unauthorized copying, distribution, or reverse-engineering is strictly
# prohibited and subject to immediate legal court cases and prosecution.
# ==============================================================================
from __future__ import division
"""
Modern Parametric Dining Table & Chair Set Generator (Shalik / ArchTools)
Compatible with Rhino 7 & Rhino 8 (both IronPython 2.7 and CPython 3 / Python.NET).
Units: INCHES internally, auto-scaled via ArchUnits.

Fixes & Features:
  - Fixed Chairs 0, 1, 2, 3 backrest orientation (no more 90-degree sideways backrests)
    and aligned Chair 0 Wishbone Y-splat and steam-bent top rail with the rear legs.
  - Added Seating Capacity Auto-Size Option (2, 3, 4, 5, 6, 7, 8, 9, 10, 12 Seats, or Custom)
    which automatically scales table length/diameter/width and places the exact number of chairs.
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

# Import universal unit system
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


def parse_dining_length(text, current_unit="in"):
    if ArchUnits:
        return ArchUnits.parse_length(text, current_unit)
    try:
        return float(text)
    except Exception:
        return 0.0


def format_dining_length(v, unit_name="in", is_int=False):
    if ArchUnits:
        return ArchUnits.format_length(v, unit_name, is_int)
    if is_int:
        return str(int(round(v)))
    return ("%.3f" % v).rstrip("0").rstrip(".")


def update_label_unit(label, unit_name):
    if ArchUnits:
        return ArchUnits.update_label_unit(label, unit_name)
    return re.sub(r'\(in\b', '(' + unit_name, str(label), flags=re.IGNORECASE)


NON_LENGTH_KEYS = {"total_seats", "rot_deg"}


# ============================================================
# CONSTANTS, ERGONOMIC TABLE SIZES & DEFAULTS (INCHES)
# ============================================================
STICKY_KEY = "ShalikDiningSet_Settings"
CONDUIT_KEY = "ShalikDiningSet_ActiveConduit"
METADATA_KEY = "ShalikDiningSetState"
ITEM_INDEX_KEY = "ShalikDiningSetItemIndex"
ITEM_CENTER_KEY = "ShalikDiningSetItemCenter"
PRESET_FOLDER_NAME = "ShalikTools"
PRESET_FILE_NAME = "ModernDiningSetPresets.json"

SEAT_CAPACITY_NAMES = [
    "0. Custom Manual Table Size & Chair Count",
    "1. 2-Seater Bistro / Compact (36\" L / 36\" Dia)",
    "2. 3-Seater Triangle / Cafe (42\" L / 42\" Dia)",
    "3. 4-Seater Standard Dining (60\" L / 48\" Dia)",
    "4. 5-Seater Family Dining (66\" L / 54\" Dia)",
    "5. 6-Seater Medium Dining (78\" L / 60\" Dia)",
    "6. 7-Seater Gathering Table (90\" L / 66\" Dia)",
    "7. 8-Seater Large Dining (102\" L / 72\" Dia)",
    "8. 9-Seater Banquet Table (114\" L / 78\" Dia)",
    "9. 10-Seater Grand Dining (126\" L / 84\" Dia)",
    "10. 12-Seater Conference / Feast (150\" L / 96\" Dia)",
]

# Mapping from capacity dropdown index -> (seat_count, rect_len_in, rect_w_in, round_dia_in)
CAPACITY_SPECS = {
    1:  (2,  36.0, 32.0, 36.0),
    2:  (3,  44.0, 36.0, 42.0),
    3:  (4,  60.0, 36.0, 48.0),
    4:  (5,  68.0, 38.0, 54.0),
    5:  (6,  78.0, 40.0, 60.0),
    6:  (7,  90.0, 40.0, 66.0),
    7:  (8,  102.0, 42.0, 72.0),
    8:  (9,  114.0, 44.0, 78.0),
    9:  (10, 126.0, 46.0, 84.0),
    10: (12, 150.0, 48.0, 96.0),
}

TABLE_SHAPE_NAMES = [
    "0. Rectangular Architectural Slab",
    "1. Soft Squircle / Rounded Rectangle",
    "2. Boat-Shape / Bowed Barrel Top",
    "3. Round / Circular Dining Table",
    "4. Oval / Elliptical Pill Table",
]

TABLE_BASE_NAMES = [
    "0. Four Tapered Post Legs + Recessed Apron",
    "1. Dual Sled / Loop Frame Legs",
    "2. Sculptural X-Cross Trestle + Stretcher",
    "3. Central Pedestal Cylinder + Plinth",
    "4. Twin V-Pillar Architectural Base",
    "5. Spider / Star Cross-Leg Base",
]

EDGE_STYLE_NAMES = [
    "0. Crisp Square Edge",
    "1. Chamfered Knife-Edge (Reverse Bevel)",
]

CHAIR_STYLE_NAMES = [
    "0. Scandinavian Wishbone / Curved-Back Chair",
    "1. Upholstered Parsons High-Back Chair",
    "2. Bauhaus Cantilever Tubular Steel Chair",
    "3. Modern Molded Shell + Dowel Base Chair",
    "4. Minimalist Metal Frame Armchair",
]

SEAT_LAYOUT_NAMES = [
    "0. Long Sides + Head Ends (Auto-Balanced)",
    "1. Long Sides Only (No End Chairs)",
    "2. One Side Chairs + One Side Dining Bench",
    "3. Radial / Circular Even Spacing",
    "4. Table Only (No Chairs)",
]

# Finishes: (Name, (R, G, B))
TOP_FINISHES = [
    ("American Black Walnut", (92, 62, 44)),
    ("Natural White Oak", (205, 175, 138)),
    ("Warm Teak / Smoked Ash", (152, 104, 66)),
    ("Carrara White Marble", (240, 240, 236)),
    ("Nero Marquina Black Stone", (42, 44, 48)),
    ("Travertine Warm Limestone", (218, 202, 178)),
    ("Clear Tempered Glass Top", (175, 212, 225)),
    ("Smoked Bronze Glass Top", (118, 102, 88)),
]

BASE_FINISHES = [
    ("Matte Jet Black Steel", (34, 36, 40)),
    ("Matching American Walnut", (92, 62, 44)),
    ("Matching White Oak", (205, 175, 138)),
    ("Brushed Champagne Brass", (185, 155, 95)),
    ("Satin Stainless Steel", (192, 196, 202)),
    ("Architectural Charcoal", (62, 65, 70)),
]

FABRIC_FINISHES = [
    ("Boucle Cream / Off-White", (236, 230, 218)),
    ("Charcoal Wool Tweed", (68, 72, 76)),
    ("Cognac Saddle Leather", (162, 92, 52)),
    ("Espresso Black Leather", (38, 36, 35)),
    ("Warm Taupe Linen", (182, 170, 155)),
    ("Olive Sage Velvet", (98, 112, 88)),
    ("Navy Slate Fabric", (52, 68, 88)),
]

TOP_FINISH_NAMES = ["%d. %s" % (i, n) for i, (n, c) in enumerate(TOP_FINISHES)]
BASE_FINISH_NAMES = ["%d. %s" % (i, n) for i, (n, c) in enumerate(BASE_FINISHES)]
FABRIC_FINISH_NAMES = ["%d. %s" % (i, n) for i, (n, c) in enumerate(FABRIC_FINISHES)]

# Numeric fields: (key, label, default_in_inches, min_in, max_in, is_int)
NUM_FIELDS = [
    # 1. Table Dimensions
    ("table_len", "Table length / diameter (in):", 78.0, 24.0, 240.0, False),    # 6'-6" (6-seater default)
    ("table_w", "Table width (in):", 40.0, 24.0, 96.0, False),                   # 3'-4"
    ("table_h", "Table height (in):", 30.0, 24.0, 42.0, False),                  # 30"
    ("top_t", "Table top slab thickness (in):", 1.5, 0.4, 6.0, False),           # 1.5"
    ("corner_r", "Corner fillet radius (in):", 4.0, 0.25, 36.0, False),
    ("leg_inset", "Base leg end inset (in):", 8.0, 1.0, 48.0, False),
    ("leg_size", "Table leg / tube thickness (in):", 2.5, 0.75, 12.0, False),
    # 2. Chairs & Layout
    ("total_seats", "Total number of chairs / seats:", 6, 1, 24, True),
    ("pull_out", "Chair pull-out distance (in):", 4.0, -8.0, 24.0, False),
    ("chair_w", "Chair seat width (in):", 19.0, 14.0, 28.0, False),              # 19"
    ("chair_d", "Chair seat depth (in):", 18.5, 14.0, 26.0, False),              # 18.5"
    ("seat_h", "Chair seat height (in):", 18.0, 14.0, 24.0, False),              # 18"
    ("chair_h", "Chair total back height (in):", 32.0, 24.0, 48.0, False),       # 32"
]

DD_FIELDS = [
    ("seat_capacity", "Seating capacity (Auto-size table):", 5, SEAT_CAPACITY_NAMES),
    ("table_shape", "Table top shape:", 0, TABLE_SHAPE_NAMES),
    ("table_base", "Table base structure:", 0, TABLE_BASE_NAMES),
    ("edge_style", "Table top edge profile:", 1, EDGE_STYLE_NAMES),
    ("chair_style", "Dining chair style:", 0, CHAIR_STYLE_NAMES),
    ("seat_layout", "Seating arrangement:", 0, SEAT_LAYOUT_NAMES),
    ("top_finish", "Table top material:", 0, TOP_FINISH_NAMES),
    ("base_finish", "Table base material:", 0, BASE_FINISH_NAMES),
    ("chair_frame_finish", "Chair frame material:", 1, BASE_FINISH_NAMES),
    ("cushion_finish", "Chair seat / fabric material:", 0, FABRIC_FINISH_NAMES),
]

TAB_LAYOUT = [
    ("1. Table Design && Size", [
        "seat_capacity",
        "table_shape",
        "table_base",
        "edge_style",
        "table_len",
        "table_w",
        "table_h",
        "top_t",
        "corner_r",
        "leg_inset",
        "leg_size",
        "@rot_row",
    ]),
    ("2. Chairs && Layout", [
        "chair_style",
        "seat_layout",
        "total_seats",
        "@pull_row",
        "chair_w",
        "chair_d",
        "seat_h",
        "chair_h",
    ]),
    ("3. Finishes && Preview", [
        "top_finish",
        "base_finish",
        "chair_frame_finish",
        "cushion_finish",
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
    s["fast_preview"] = False
    return s


def normalize_settings(settings):
    if not settings:
        return default_settings()
    out = {}
    if "total_seats" not in settings and "side_chairs" in settings:
        settings = dict(settings)
        settings["total_seats"] = int(settings["side_chairs"]) * 2
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
    """
    Creates a 3D box along spine p0 -> p1:
      - `width` is measured along `ay = CrossProduct(up_vec, spine_dir)`
      - `height` is measured along `az = up_vec`
    """
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
    Builds a properly oriented chair backrest spanning across the chair's width along X
    (`-back_width/2` to `+back_width/2`), rising from `(0, y_bot, z_bot)` to `(0, y_top, z_top)`.
    If `curve_depth > 0`, gently curves the backrest in plan to hug the sitter's back!
    Never rotates 90 degrees sideways!
    """
    hw = max(2.0, back_width * 0.5)
    ht = max(0.2, thickness * 0.5)
    p_bot = rg.Point3d(0.0, y_bot, z_bot)
    p_top = rg.Point3d(0.0, y_top, z_top)
    spine = p_top - p_bot
    spine_len = spine.Length
    if spine_len <= 0.5:
        return None

    if curve_depth <= 0.05:
        # Flat angled backrest: X is width (-hw to +hw), Y_local is spine, Z_local is thickness
        u_spine = _safe_unitize(spine, rg.Vector3d.ZAxis)
        pl = rg.Plane(0.5 * (p_bot + p_top), rg.Vector3d.XAxis, u_spine)
        box = rg.Box(
            pl,
            rg.Interval(-hw, hw),
            rg.Interval(-spine_len * 0.5, spine_len * 0.5),
            rg.Interval(-ht, ht),
        )
        return box.ToBrep() if box.IsValid else None

    # Gently curved ergonomic backrest (hugs the sitter's back along X)
    u_spine = _safe_unitize(spine, rg.Vector3d.ZAxis)
    n_depth = _safe_unitize(rg.Vector3d.CrossProduct(rg.Vector3d.XAxis, u_spine), rg.Vector3d.YAxis)
    # Build closed 2D curved profile in the (X, n_depth) plane at p_bot and extrude along spine
    pl_base = rg.Plane(p_bot, rg.Vector3d.XAxis, n_depth)
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


# ============================================================
# TABLE TOP & BASE BUILDERS (CENTERED AT ORIGIN IN INCHES)
# ============================================================
def make_table_top_curve_2d(shape_idx, L, W, corner_r, z_level):
    hl = max(6.0, L * 0.5)
    hw = max(6.0, W * 0.5)
    pl = rg.Plane(rg.Point3d(0, 0, z_level), rg.Vector3d.XAxis, rg.Vector3d.YAxis)

    if shape_idx == 3:
        return rg.Circle(pl, hl).ToNurbsCurve()
    elif shape_idx == 4:
        return rg.Ellipse(pl, hl, hw).ToNurbsCurve()
    elif shape_idx == 2:
        end_hw = hw * 0.78
        arc_top = rg.Arc(rg.Point3d(-hl, end_hw, z_level), rg.Point3d(0.0, hw, z_level), rg.Point3d(hl, end_hw, z_level)).ToNurbsCurve()
        line_r = rg.LineCurve(rg.Point3d(hl, end_hw, z_level), rg.Point3d(hl, -end_hw, z_level))
        arc_bot = rg.Arc(rg.Point3d(hl, -end_hw, z_level), rg.Point3d(0.0, -hw, z_level), rg.Point3d(-hl, -end_hw, z_level)).ToNurbsCurve()
        line_l = rg.LineCurve(rg.Point3d(-hl, -end_hw, z_level), rg.Point3d(-hl, end_hw, z_level))
        joined = rg.Curve.JoinCurves([arc_top, line_r, arc_bot, line_l], 0.01)
        if joined and len(joined) > 0:
            r_fil = min(corner_r, end_hw * 0.45)
            if r_fil > 0.25:
                fil = rg.Curve.CreateFilletCornersCurve(joined[0], r_fil, 0.005, 0.005)
                if fil and fil.IsClosed:
                    return fil
            return joined[0]

    rect = rg.Rectangle3d(pl, rg.Interval(-hl, hl), rg.Interval(-hw, hw)).ToNurbsCurve()
    if shape_idx == 1:
        rad = min(corner_r, min(hl, hw) * 0.48)
        if rad > 0.2:
            fil = rg.Curve.CreateFilletCornersCurve(rect, rad, 0.005, 0.005)
            if fil and fil.IsClosed:
                return fil
    return rect


def build_table_top_slab(S):
    shape_idx = int(S["table_shape"])
    edge_style = int(S["edge_style"])
    L = float(S["table_len"])
    W = L if shape_idx == 3 else float(S["table_w"])
    H = float(S["table_h"])
    top_t = float(S["top_t"])
    corner_r = float(S["corner_r"])

    z_top = H
    z_bot = H - top_t
    top_crv = make_table_top_curve_2d(shape_idx, L, W, corner_r, z_top)

    if edge_style == 1 and top_t >= 0.75:
        rim_t = top_t * 0.35
        z_mid = z_top - rim_t
        mid_crv = make_table_top_curve_2d(shape_idx, L, W, corner_r, z_mid)
        inset = min(top_t * 1.4, min(L, W) * 0.08)
        bot_crv = make_table_top_curve_2d(shape_idx, L - 2.0 * inset, W - 2.0 * inset, max(0.2, corner_r - inset * 0.5), z_bot)
        lofts = rg.Brep.CreateFromLoft([bot_crv, mid_crv, top_crv], rg.Point3d.Unset, rg.Point3d.Unset, rg.LoftType.Straight, False)
        if lofts and len(lofts) > 0:
            capped = lofts[0].CapPlanarHoles(0.01)
            if capped and capped.IsValid:
                if capped.SolidOrientation == rg.BrepSolidOrientation.Inward:
                    capped.Flip()
                return capped, top_crv

    bot_crv = make_table_top_curve_2d(shape_idx, L, W, corner_r, z_bot)
    srf = rg.Surface.CreateExtrusion(bot_crv, rg.Vector3d(0, 0, top_t))
    if srf:
        b = srf.ToBrep()
        if b:
            capped = b.CapPlanarHoles(0.01)
            res = capped if (capped and capped.IsValid) else b
            if res.SolidOrientation == rg.BrepSolidOrientation.Inward:
                res.Flip()
            return res, top_crv
    return None, top_crv


def build_table_base_structure(S):
    parts = []
    shape_idx = int(S["table_shape"])
    base_idx = int(S["table_base"])
    L = float(S["table_len"])
    W = L if shape_idx == 3 else float(S["table_w"])
    H = float(S["table_h"])
    top_t = float(S["top_t"])
    inset_x = min(float(S["leg_inset"]), L * 0.35)
    leg_sz = float(S["leg_size"])

    z_under = H - top_t
    hl = max(4.0, L * 0.5 - inset_x)
    hw = max(4.0, W * 0.5 - min(inset_x * 0.65, W * 0.25))
    r_leg = leg_sz * 0.5

    if base_idx == 0:
        apron_h = min(3.2, z_under * 0.12)
        apron_t = max(0.85, leg_sz * 0.4)
        splay = 1.5
        for sx in (-1.0, 1.0):
            for sy in (-1.0, 1.0):
                p_top = rg.Point3d(sx * hl, sy * hw, z_under)
                p_bot = rg.Point3d(sx * (hl + splay), sy * (hw + splay * 0.6), 0.0)
                add_part(parts, "table_base", make_tapered_leg(p_bot, p_top, r_leg * 0.62, r_leg))
        add_part(parts, "table_base", make_box_xy(-hl, hl, hw - apron_t, hw, z_under - apron_h, z_under))
        add_part(parts, "table_base", make_box_xy(-hl, hl, -hw, -hw + apron_t, z_under - apron_h, z_under))
        add_part(parts, "table_base", make_box_xy(-hl, -hl + apron_t, -hw, hw, z_under - apron_h, z_under))
        add_part(parts, "table_base", make_box_xy(hl - apron_t, hl, -hw, hw, z_under - apron_h, z_under))

    elif base_idx == 1:
        bar_w = leg_sz
        bar_t = max(0.75, leg_sz * 0.45)
        for sx in (-1.0, 1.0):
            x0 = sx * hl - bar_w * 0.5
            x1 = sx * hl + bar_w * 0.5
            add_part(parts, "table_base", make_box_xy(x0, x1, -hw, -hw + bar_t, bar_t, z_under - bar_t))
            add_part(parts, "table_base", make_box_xy(x0, x1, hw - bar_t, hw, bar_t, z_under - bar_t))
            add_part(parts, "table_base", make_box_xy(x0, x1, -hw, hw, 0.0, bar_t))
            add_part(parts, "table_base", make_box_xy(x0, x1, -hw, hw, z_under - bar_t, z_under))
        add_part(parts, "table_base", make_box_xy(-hl, hl, -bar_w * 0.4, bar_w * 0.4, z_under - bar_t * 1.6, z_under))

    elif base_idx == 2:
        bw = leg_sz
        bt = max(1.25, leg_sz * 0.65)
        for sx in (-1.0, 1.0):
            xc = sx * hl
            p1 = rg.Point3d(xc - bt * 0.3, -hw, 0.0)
            p2 = rg.Point3d(xc - bt * 0.3, hw, z_under)
            p3 = rg.Point3d(xc + bt * 0.3, hw, 0.0)
            p4 = rg.Point3d(xc + bt * 0.3, -hw, z_under)
            add_part(parts, "table_base", make_member_between(p1, p2, rg.Vector3d.XAxis, bw, bt))
            add_part(parts, "table_base", make_member_between(p3, p4, rg.Vector3d.XAxis, bw, bt))
        z_mid = z_under * 0.48
        add_part(parts, "table_base", make_box_xy(-hl - bt, hl + bt, -bt * 0.45, bt * 0.45, z_mid - bw * 0.45, z_mid + bw * 0.45))

    elif base_idx == 3:
        is_double = (shape_idx != 3) and (L >= 88.0)
        x_centers = [-L * 0.24, L * 0.24] if is_double else [0.0]
        col_r = min(W * 0.22, max(4.5, leg_sz * 2.4))
        plinth_r = min(W * 0.38, col_r * 1.75)
        plinth_h = 1.25
        for xc in x_centers:
            p_b = rg.Point3d(xc, 0.0, 0.0)
            p_m = rg.Point3d(xc, 0.0, plinth_h)
            p_t = rg.Point3d(xc, 0.0, z_under)
            add_part(parts, "table_base", make_tapered_leg(p_b, p_m, plinth_r, plinth_r * 0.92))
            add_part(parts, "table_base", make_tapered_leg(p_m, p_t, col_r, col_r * 0.78))
            add_part(parts, "table_base", make_tapered_leg(rg.Point3d(xc, 0.0, z_under - 1.0), p_t, plinth_r * 0.85, plinth_r * 0.85))

    elif base_idx == 4:
        plate_l = min(L * 0.58, max(24.0, L - 2.0 * inset_x))
        plate_w = min(W * 0.52, max(16.0, W * 0.45))
        plate_h = 0.75
        add_part(parts, "table_base", make_box_xy(-plate_l * 0.5, plate_l * 0.5, -plate_w * 0.5, plate_w * 0.5, 0.0, plate_h))
        v_bot_x = plate_l * 0.22
        v_top_x = plate_l * 0.46
        col_w = max(3.5, leg_sz * 1.6)
        col_d = min(plate_w * 0.75, max(8.0, W * 0.3))
        for sx in (-1.0, 1.0):
            pb = rg.Point3d(sx * v_bot_x, 0.0, plate_h)
            pt = rg.Point3d(sx * v_top_x, 0.0, z_under)
            add_part(parts, "table_base", make_member_between(pb, pt, rg.Vector3d.YAxis, col_w, col_d))

    else:
        bw = leg_sz
        bt = leg_sz * 0.75
        for sx, sy in ((-1.0, -1.0), (1.0, -1.0), (1.0, 1.0), (-1.0, 1.0)):
            p_foot = rg.Point3d(sx * hl * 0.92, sy * hw * 0.92, 0.0)
            p_top = rg.Point3d(-sx * hl * 0.35, -sy * hw * 0.35, z_under)
            add_part(parts, "table_base", make_member_between(p_foot, p_top, rg.Vector3d.ZAxis, bt, bw))

    return parts


# ============================================================
# 5 MODERN DINING CHAIR BUILDERS (FIXED BACKRESTS & WISHBONE FRAME)
# ============================================================
def build_unit_dining_chair(S, fast=False):
    """
    Constructs a single high-detail 3D Dining Chair centered at (0, 0, 0) on the floor,
    facing toward +Y (toward the dining table center).
    """
    parts = []
    c_style = int(S["chair_style"])
    cw = float(S["chair_w"])
    cd = float(S["chair_d"])
    sh = float(S["seat_h"])
    ch = max(sh + 8.0, float(S["chair_h"]))

    hw = cw * 0.5
    hd = cd * 0.5
    cush_t = 1.6

    if c_style == 0:
        # 0. Scandinavian Wishbone / Curved-Back Timber Chair (FIXED GEOMETRY)
        leg_r = 0.58
        x_rear_top = hw - 0.85
        y_rear_seat = -hd + 1.2
        y_rear_top = -hd - 0.3
        z_rail = ch - 0.75

        for sx in (-1.0, 1.0):
            # Front legs
            p_fb = rg.Point3d(sx * (hw - 0.9), hd - 1.1, 0.0)
            p_ft = rg.Point3d(sx * (hw - 1.1), hd - 1.4, sh - 0.6)
            add_part(parts, "chair_frame", make_tapered_leg(p_fb, p_ft, leg_r * 0.75, leg_r))

            # Rear legs rising smoothly to the curved steam-bent rail
            p_rb = rg.Point3d(sx * (hw - 1.0), -hd + 0.6, 0.0)
            p_rm = rg.Point3d(sx * (hw - 1.0), y_rear_seat, sh - 0.5)
            p_rt = rg.Point3d(sx * x_rear_top, y_rear_top, z_rail)
            add_part(parts, "chair_frame", make_tapered_leg(p_rb, p_rm, leg_r * 0.75, leg_r * 1.05))
            add_part(parts, "chair_frame", make_tapered_leg(p_rm, p_rt, leg_r * 1.05, leg_r * 0.88))

            # Side stretcher spindle
            add_part(parts, "chair_frame", make_tapered_leg(
                rg.Point3d(sx * (hw - 1.0), -hd + 0.9, sh * 0.38),
                rg.Point3d(sx * (hw - 1.0), hd - 1.25, sh * 0.38),
                0.38, 0.38
            ))

        # Front & rear seat rails + cross stretchers
        add_part(parts, "chair_frame", make_box_xy(-hw + 0.9, hw - 0.9, -hd + 1.0, hd - 1.1, sh - 1.6, sh - 0.6))
        add_part(parts, "chair_cushion", make_box_xy(-hw + 0.6, hw - 0.6, -hd + 0.9, hd - 0.7, sh - 0.6, sh + 0.35))

        # Steam-Bent Semicircular Top Arm/Back Rail passing EXACTLY through both rear leg tops!
        # Starts at forward arm tips -> passes through p_rt -> arches back to center (-hd - 1.5)
        arm_pts = [
            rg.Point3d(-(hw + 0.1), 0.5, z_rail - 1.2),
            rg.Point3d(-x_rear_top, y_rear_top, z_rail),
            rg.Point3d(0.0, -hd - 1.5, z_rail + 0.35),
            rg.Point3d(x_rear_top, y_rear_top, z_rail),
            rg.Point3d(hw + 0.1, 0.5, z_rail - 1.2),
        ]
        rail_crv = rg.Curve.CreateInterpolatedCurve(arm_pts, 3)
        if rail_crv:
            pipes = rg.Brep.CreatePipe(rail_crv, leg_r * 1.12, False, rg.PipeCapMode.Round, True, 0.01, 0.02)
            if pipes:
                for pb in pipes:
                    add_part(parts, "chair_frame", pb)

        # Signature Y-Wishbone Back Splat connecting rear seat rail to the exact center of the top arch
        p_y_bot = rg.Point3d(0.0, y_rear_seat, sh - 0.8)
        p_y_split = rg.Point3d(0.0, -hd - 0.75, sh + (z_rail - sh) * 0.58)
        add_part(parts, "chair_frame", make_member_between(p_y_bot, p_y_split, rg.Vector3d.YAxis, 1.15, 0.32))
        for sx in (-1.0, 1.0):
            p_y_top = rg.Point3d(sx * 2.4, -hd - 1.42, z_rail + 0.25)
            add_part(parts, "chair_frame", make_member_between(p_y_split, p_y_top, rg.Vector3d.YAxis, 0.95, 0.32))

    elif c_style == 1:
        # 1. Upholstered Parsons / High-Back Side Chair (FIXED BACKREST ORIENTATION)
        for sx in (-1.0, 1.0):
            add_part(parts, "chair_frame", make_tapered_leg(
                rg.Point3d(sx * (hw - 1.2), hd - 1.2, 0.0),
                rg.Point3d(sx * (hw - 1.2), hd - 1.2, sh - cush_t),
                0.55, 0.85
            ))
            add_part(parts, "chair_frame", make_tapered_leg(
                rg.Point3d(sx * (hw - 1.2), -hd + 0.6, 0.0),
                rg.Point3d(sx * (hw - 1.2), -hd + 1.2, sh - cush_t),
                0.55, 0.85
            ))
        # Thick plush seat cushion
        add_part(parts, "chair_cushion", make_box_xy(-hw, hw, -hd + 0.8, hd, sh - cush_t - 1.0, sh))
        # Wide, gently curved upholstered high backrest spanning across X (-hw to +hw)
        back_brep = make_angled_backrest(cw, -hd + 1.4, sh - 0.6, -hd - 1.5, ch, 2.1, curve_depth=1.1)
        add_part(parts, "chair_cushion", back_brep)

    elif c_style == 2:
        # 2. Bauhaus Cantilever Tubular Steel Chair (FIXED BACKREST ORIENTATION)
        tube_r = 0.48
        for sx in (-1.0, 1.0):
            x_c = sx * (hw - 0.65)
            loop_pts = [
                rg.Point3d(x_c, -hd + 1.5, 0.48),
                rg.Point3d(x_c, hd - 1.0, 0.48),
                rg.Point3d(x_c, hd - 1.0, sh - 0.9),
                rg.Point3d(x_c, -hd + 1.1, sh - 0.9),
                rg.Point3d(x_c, -hd - 1.2, ch - 0.8),
            ]
            poly_c = rg.Polyline(loop_pts).ToNurbsCurve()
            fil_c = rg.Curve.CreateFilletCornersCurve(poly_c, 1.8, 0.01, 0.01) or poly_c
            pipes = rg.Brep.CreatePipe(fil_c, tube_r, False, rg.PipeCapMode.Round, True, 0.01, 0.02)
            if pipes:
                for pb in pipes:
                    add_part(parts, "chair_frame", pb)
        # Front & Top tubular crossbars
        add_part(parts, "chair_frame", make_tapered_leg(rg.Point3d(-hw + 0.65, hd - 1.0, sh - 0.9), rg.Point3d(hw - 0.65, hd - 1.0, sh - 0.9), tube_r, tube_r))
        add_part(parts, "chair_frame", make_tapered_leg(rg.Point3d(-hw + 0.65, -hd - 1.2, ch - 0.8), rg.Point3d(hw - 0.65, -hd - 1.2, ch - 0.8), tube_r, tube_r))
        # Floating upholstered seat & wide backrest pad spanning between the side tubes
        add_part(parts, "chair_cushion", make_box_xy(-hw + 1.1, hw - 1.1, -hd + 1.3, hd - 0.5, sh - 0.9, sh + 0.4))
        back_brep = make_angled_backrest(cw - 2.2, -hd - 0.15, sh + (ch - sh) * 0.35, -hd - 1.15, ch - 1.1, 1.35, curve_depth=0.6)
        add_part(parts, "chair_cushion", back_brep)

    elif c_style == 3:
        # 3. Modern Molded Shell Chair + Eiffel Dowel Base (FIXED SHELL BACKREST ORIENTATION)
        for sx in (-1.0, 1.0):
            for sy in (-1.0, 1.0):
                p_top = rg.Point3d(sx * (hw * 0.52), sy * (hd * 0.52), sh - 1.1)
                p_bot = rg.Point3d(sx * (hw - 0.8), sy * (hd - 0.8), 0.0)
                add_part(parts, "chair_frame", make_tapered_leg(p_bot, p_top, 0.45, 0.68))
                if not fast:
                    add_part(parts, "chair_frame", make_member_between(
                        rg.Point3d(0.0, 0.0, sh * 0.65),
                        rg.Point3d(sx * (hw * 0.72), sy * (hd * 0.72), sh * 0.55),
                        rg.Vector3d.ZAxis, 0.2, 0.2
                    ))
        # Contoured bucket seat + curved molded shell backrest spanning across X
        add_part(parts, "chair_cushion", make_box_xy(-hw, hw, -hd + 1.2, hd, sh - 1.1, sh + 0.25))
        shell_back = make_angled_backrest(cw, -hd + 1.4, sh - 0.6, -hd - 1.6, ch, 1.15, curve_depth=1.8)
        add_part(parts, "chair_cushion", shell_back)

    else:
        # 4. Minimalist Metal Frame Armchair
        bar = 0.75
        arm_h = sh + 7.5
        for sx in (-1.0, 1.0):
            x0 = sx * (hw - bar * 0.5) - bar * 0.5
            x1 = x0 + bar
            add_part(parts, "chair_frame", make_box_xy(x0, x1, hd - bar, hd, 0.0, arm_h))
            add_part(parts, "chair_frame", make_box_xy(x0, x1, -hd, -hd + bar, 0.0, ch))
            add_part(parts, "chair_frame", make_box_xy(x0, x1, -hd, hd, arm_h - bar, arm_h))
            add_part(parts, "chair_frame", make_box_xy(x0, x1, -hd, hd, sh - 1.6, sh - 1.6 + bar))
        add_part(parts, "chair_cushion", make_box_xy(-hw + bar, hw - bar, -hd + bar, hd - 0.4, sh - 1.2, sh + 0.4))
        add_part(parts, "chair_cushion", make_box_xy(-hw + bar, hw - bar, -hd, -hd + 1.6, ch - 8.5, ch - 0.4))

    return parts


def build_dining_bench(bench_len, bench_d, seat_h):
    parts = []
    hl = bench_len * 0.5
    hd = bench_d * 0.5
    cush_t = 2.2
    leg_in = min(6.0, hl * 0.25)
    bar_w = 1.6
    bar_t = 0.75
    z_under = seat_h - cush_t
    add_part(parts, "chair_cushion", make_box_xy(-hl, hl, -hd, hd, z_under, seat_h))
    for sx in (-1.0, 1.0):
        x0 = sx * (hl - leg_in) - bar_w * 0.5
        x1 = x0 + bar_w
        add_part(parts, "chair_frame", make_box_xy(x0, x1, -hd + 0.5, -hd + 0.5 + bar_t, bar_t, z_under))
        add_part(parts, "chair_frame", make_box_xy(x0, x1, hd - 0.5 - bar_t, hd - 0.5, bar_t, z_under))
        add_part(parts, "chair_frame", make_box_xy(x0, x1, -hd + 0.5, hd - 0.5, 0.0, bar_t))
        add_part(parts, "chair_frame", make_box_xy(x0, x1, -hd + 0.5, hd - 0.5, z_under - bar_t, z_under))
    return parts


# ============================================================
# MASTER DINING SET BUILDER (EXACT 2..12 SEAT PLACEMENT)
# ============================================================
def build_dining_set_system(center_in, S, final=True, u=1.0):
    fast = (not final) and S["fast_preview"]
    shape_idx = int(S["table_shape"])
    layout_idx = int(S["seat_layout"])
    L = float(S["table_len"])
    W = L if shape_idx == 3 else float(S["table_w"])
    total_seats = max(1, int(S["total_seats"]))
    pull_out = float(S["pull_out"])
    cw = float(S["chair_w"])
    cd = float(S["chair_d"])
    sh = float(S["seat_h"])
    rot_rad = math.radians(float(S["rot_deg"]))

    parts = []
    preview_curves = []

    # 1. Build Table Top & Base at local origin (0, 0, 0)
    top_brep, top_crv = build_table_top_slab(S)
    add_part(parts, "table_top", top_brep)
    if top_crv:
        preview_curves.append(top_crv)
    parts.extend(build_table_base_structure(S))

    # 2. Build & Place Exact Number of Chairs (2, 3, 4, 5, 6, 7, 8, 9, 10, 12, etc.)
    placed_chairs = 0
    if layout_idx != 4:
        unit_chair = build_unit_dining_chair(S, fast)

        def place_chair_at(pos_xy, angle_rad):
            rot_c = rg.Transform.Rotation(angle_rad, rg.Vector3d.ZAxis, rg.Point3d.Origin)
            tr_c = rg.Transform.Translation(pos_xy.X, pos_xy.Y, 0.0)
            xf = tr_c * rot_c
            for kind, b in unit_chair:
                dup = b.DuplicateBrep()
                dup.Transform(xf)
                add_part(parts, kind, dup)

        def place_row_along_side(n_side, y_coord, facing_angle):
            if n_side <= 0:
                return
            usable_l = max(cw, L - max(14.0, cw * 0.8))
            step_x = usable_l / float(n_side)
            x_start = -usable_l * 0.5 + step_x * 0.5
            for i in range(n_side):
                cx = x_start + i * step_x
                place_chair_at(rg.Point3d(cx, y_coord, 0.0), facing_angle)

        hl = L * 0.5
        hw = W * 0.5
        edge_dist = cd * 0.35 + pull_out

        if shape_idx == 3 or layout_idx == 3:
            # Radial / Circular Even Spacing around Round/Oval/Rectangular Table
            for i in range(total_seats):
                theta = (2.0 * math.pi * i) / float(total_seats)
                rx = (hl + edge_dist) * math.cos(theta)
                ry = (hw + edge_dist) * math.sin(theta)
                place_chair_at(rg.Point3d(rx, ry, 0.0), theta + math.pi * 0.5)
                placed_chairs += 1

        elif layout_idx == 2:
            # One Side Chairs + One Side Dining Bench (+ optional head ends if total_seats >= 5)
            has_ends = (total_seats >= 6)
            n_ch_side = max(1, (total_seats - 2) // 2 if has_ends else max(1, total_seats // 2))
            place_row_along_side(n_ch_side, -(hw + edge_dist), 0.0)
            placed_chairs += n_ch_side

            usable_l = max(cw, L - 16.0)
            bench_len = max(24.0, usable_l * 0.92)
            bench_parts = build_dining_bench(bench_len, min(16.0, cd * 0.85), sh)
            tr_b = rg.Transform.Translation(0.0, hw + edge_dist * 0.85, 0.0)
            for kind, b in bench_parts:
                dup = b.DuplicateBrep()
                dup.Transform(tr_b)
                add_part(parts, kind, dup)
            placed_chairs += 1

            if has_ends:
                place_chair_at(rg.Point3d(-(hl + edge_dist), 0.0, 0.0), -math.pi * 0.5)
                place_chair_at(rg.Point3d(hl + edge_dist, 0.0, 0.0), math.pi * 0.5)
                placed_chairs += 2

        elif layout_idx == 1:
            # Long Sides Only (No End Chairs) - supports both even and odd total_seats
            n_bot = (total_seats + 1) // 2
            n_top = total_seats - n_bot
            place_row_along_side(n_bot, -(hw + edge_dist), 0.0)
            place_row_along_side(n_top, hw + edge_dist, math.pi)
            placed_chairs = total_seats

        else:
            # Layout 0: Long Sides + Head Ends (Auto-Balanced for 2, 3, 4, 5, 6, 7, 8, 9, 10, 12 seats!)
            if total_seats == 1:
                place_row_along_side(1, -(hw + edge_dist), 0.0)
            elif total_seats == 2:
                # 1 on each long side (or opposite ends)
                place_row_along_side(1, -(hw + edge_dist), 0.0)
                place_row_along_side(1, hw + edge_dist, math.pi)
            elif total_seats == 3:
                # 1 on bottom side, 1 on top side, 1 at head end
                place_row_along_side(1, -(hw + edge_dist), 0.0)
                place_row_along_side(1, hw + edge_dist, math.pi)
                place_chair_at(rg.Point3d(-(hl + edge_dist), 0.0, 0.0), -math.pi * 0.5)
            else:
                # For 4+ seats: 1 at left head end + (1 at right head end if even, or 1 if odd)
                rem = total_seats - 2
                if rem % 2 == 0:
                    # Even total (4, 6, 8, 10, 12): 2 end chairs + equal chairs on both long sides
                    n_side = rem // 2
                    place_row_along_side(n_side, -(hw + edge_dist), 0.0)
                    place_row_along_side(n_side, hw + edge_dist, math.pi)
                    place_chair_at(rg.Point3d(-(hl + edge_dist), 0.0, 0.0), -math.pi * 0.5)
                    place_chair_at(rg.Point3d(hl + edge_dist, 0.0, 0.0), math.pi * 0.5)
                else:
                    # Odd total (5, 7, 9, 11): 1 head chair + equal chairs on both long sides
                    n_side = (total_seats - 1) // 2
                    place_row_along_side(n_side, -(hw + edge_dist), 0.0)
                    place_row_along_side(n_side, hw + edge_dist, math.pi)
                    place_chair_at(rg.Point3d(-(hl + edge_dist), 0.0, 0.0), -math.pi * 0.5)
            placed_chairs = total_seats

    # 3. Rotate around Z, Translate to center_in, and Scale by u
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
        "table_len_in": L,
        "table_w_in": W,
        "chair_count": placed_chairs,
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


def bake_dining_set(doc, center_in, S, u=1.0, edit_target_ids=None):
    parts, _, _ = build_dining_set_system(center_in, S, True, u)

    tp_name, tp_rgb = TOP_FINISHES[S["top_finish"]]
    bs_name, bs_rgb = BASE_FINISHES[S["base_finish"]]
    cf_name, cf_rgb = BASE_FINISHES[S["chair_frame_finish"]]
    cu_name, cu_rgb = FABRIC_FINISHES[S["cushion_finish"]]

    is_glass_top = S["top_finish"] in (6, 7)
    top_trans = 0.45 if is_glass_top else 0.0

    colors = {
        "table_top": rgb_to_color(tp_rgb),
        "table_base": rgb_to_color(bs_rgb),
        "chair_frame": rgb_to_color(cf_rgb),
        "chair_cushion": rgb_to_color(cu_rgb),
    }

    main_layer_idx = get_or_create_layer(doc, "DINING_SET")
    parent_id = doc.Layers[main_layer_idx].Id

    layers = {
        "table_top": get_or_create_layer_with_material(doc, "TABLE_TOP", parent_id, colors["table_top"], "Dining Top " + tp_name, colors["table_top"], top_trans),
        "table_base": get_or_create_layer_with_material(doc, "TABLE_BASE", parent_id, colors["table_base"], "Dining Base " + bs_name, colors["table_base"]),
        "chair_frame": get_or_create_layer_with_material(doc, "CHAIR_FRAME", parent_id, colors["chair_frame"], "Chair Frame " + cf_name, colors["chair_frame"]),
        "chair_cushion": get_or_create_layer_with_material(doc, "CHAIR_CUSHION", parent_id, colors["chair_cushion"], "Chair Fabric " + cu_name, colors["chair_cushion"]),
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
        attr = make_attributes(layers.get(kind, layers["table_top"]), "Dining_" + kind, state_json, idx, c_pt)
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
class DiningSetPreviewConduit(rd.DisplayConduit):
    def __init__(self, wireframe_only=False):
        super(DiningSetPreviewConduit, self).__init__()
        self.preview_breps = []
        self.preview_curves = []
        self.wireframe_only = wireframe_only
        self.materials = {}
        self.set_finishes(default_settings())

    def set_finishes(self, S):
        tp_rgb = TOP_FINISHES[S["top_finish"]][1]
        bs_rgb = BASE_FINISHES[S["base_finish"]][1]
        cf_rgb = BASE_FINISHES[S["chair_frame_finish"]][1]
        cu_rgb = FABRIC_FINISHES[S["cushion_finish"]][1]
        top_trans = 0.45 if S["top_finish"] in (6, 7) else 0.0
        self.materials = {
            "table_top": rd.DisplayMaterial(rgb_to_color(tp_rgb), top_trans),
            "table_base": rd.DisplayMaterial(rgb_to_color(bs_rgb)),
            "chair_frame": rd.DisplayMaterial(rgb_to_color(cf_rgb)),
            "chair_cushion": rd.DisplayMaterial(rgb_to_color(cu_rgb)),
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
                    col = System.Drawing.Color.Gold if kind == "table_top" else System.Drawing.Color.DeepSkyBlue
                    e.Display.DrawBrepWires(brep, col, 1)
                else:
                    mat = self.materials.get(kind, self.materials["table_top"])
                    if mat:
                        e.Display.DrawBrepShaded(brep, mat)
                    e.Display.DrawBrepWires(brep, System.Drawing.Color.FromArgb(40, 40, 45), 1)
            for crv in self.preview_curves:
                if crv and crv.IsValid:
                    e.Display.DrawCurve(crv, System.Drawing.Color.Gold, 2)
        except Exception:
            pass


class DiningSpanPointGetter(ric.GetPoint):
    def __init__(self, p0_doc, settings, u_scale, fixed_length=False):
        super(DiningSpanPointGetter, self).__init__()
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
                temp_s["table_len"] = clamp(dist_doc / self.u, 24.0, 240.0)
                mid_doc = 0.5 * (self.p0_doc + rg.Point3d(curr.X, curr.Y, self.p0_doc.Z))
            else:
                mid_doc = self.p0_doc

            c_in = rg.Point3d(mid_doc.X / self.u, mid_doc.Y / self.u, mid_doc.Z / self.u)
            parts, _, _ = build_dining_set_system(c_in, temp_s, False, self.u)
            for kind, brep in parts:
                if brep and brep.IsValid:
                    col = System.Drawing.Color.Gold if kind in ("table_top", "table_base") else System.Drawing.Color.DeepSkyBlue
                    e.Display.DrawBrepWires(brep, col, 1)
        except Exception:
            pass


# ============================================================
# DIALOG UI (3 TABS + CAPACITY AUTO-SIZER + SLIDERS)
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
        self.textbox = make_textbox(format_dining_length(disp_val, unit_name, is_int))

    def value(self):
        try:
            txt = self.textbox.Text.strip()
            if self.is_length:
                val_unit = parse_dining_length(txt, self.unit_name)
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
        self.textbox.Text = format_dining_length(disp_val, self.unit_name, self.is_int)


class DiningSetDialog(forms.Dialog[bool]):
    def __init__(self):
        super(DiningSetDialog, self).__init__()
        self._initialized = False
        self._preview_closed = False
        self._suppress_preview_update = True
        self._syncing_rot = False
        self._syncing_pull = False
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

        title_prefix = "Edit Modern Dining Set" if is_edit else "Modern Dining Table & Chair Set Generator"
        self.Title = "%s [%s]" % (title_prefix, unit_name)
        self.Padding = drawing.Padding(10)
        self.Resizable = True
        try:
            self.Topmost = True
        except Exception:
            pass
        self.ClientSize = drawing.Size(660, 740)

        prev_conduit = sc.sticky.get(CONDUIT_KEY)
        if prev_conduit is not None:
            try:
                prev_conduit.Enabled = False
            except Exception:
                pass

        self.conduit = DiningSetPreviewConduit(wireframe_only=False)
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

        # 1. Set Rotation Angle Slider (-180 to +180 deg)
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

        # 2. Chair Pull-Out Distance Slider (-8 in to +24 in, scaled by x10)
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

        disp_l = format_dining_length(s["table_len"] * scale_from_inch, unit_name)
        disp_w = format_dining_length(s["table_w"] * scale_from_inch, unit_name)
        self.summary_lbl = make_label("Table Size: %s x %s %s" % (disp_l, disp_w, unit_name), bold=True)
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
                if key == "@rot_row":
                    tab_layout.AddRow(make_label("Set rotation angle (-180 to +180):", bold=True), rot_layout)
                elif key == "@pull_row":
                    tab_layout.AddRow(make_label(self.labels["pull_out"], bold=True), pull_layout)
                elif key == "@fast":
                    tab_layout.AddRow(make_label(""), self.cb_fast)
                elif key in self.dds:
                    is_bold = (key == "seat_capacity")
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

        btn_ok = make_button("Apply Edit" if is_edit else "Create Dining Set")
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

        # Events
        self.Closed += self.OnDialogClosed
        for key, f in self.fields.items():
            if key == "pull_out":
                f.textbox.TextChanged += self.OnPullTextChanged
            else:
                f.textbox.TextChanged += self.OnAnyChanged
        for key, dd in self.dds.items():
            if key in ("seat_capacity", "table_shape"):
                dd.SelectedIndexChanged += self.OnCapacityOrShapeChanged
            else:
                dd.SelectedIndexChanged += self.OnAnyChanged
        self.sli_rot.ValueChanged += self.OnRotSliderChanged
        self.txt_rot_val.TextChanged += self.OnRotTextChanged
        self.sli_pull.ValueChanged += self.OnPullSliderChanged
        self.cb_fast.CheckedChanged += self.OnAnyChanged

        self.dd_preset.SelectedIndexChanged += self.OnPresetSelectedChanged
        self.btn_preset_load.Click += self.OnPresetLoadClicked
        self.btn_preset_save.Click += self.OnPresetSaveClicked
        self.btn_preset_delete.Click += self.OnPresetDeleteClicked

        self.UpdateEnabling()
        self._suppress_preview_update = False
        self.UpdatePreview()

    def OnCapacityOrShapeChanged(self, sender, e):
        if getattr(self, "_suppress_preview_update", False):
            return
        cap_idx = int(self.dds["seat_capacity"].SelectedIndex)
        sh_idx = int(self.dds["table_shape"].SelectedIndex)
        if cap_idx in CAPACITY_SPECS:
            seats, rect_l, rect_w, round_dia = CAPACITY_SPECS[cap_idx]
            self._suppress_preview_update = True
            try:
                self.fields["total_seats"].set_value(seats)
                if sh_idx == 3:
                    self.fields["table_len"].set_value(round_dia)
                    self.fields["table_w"].set_value(round_dia)
                else:
                    self.fields["table_len"].set_value(rect_l)
                    self.fields["table_w"].set_value(rect_w)
            finally:
                self._suppress_preview_update = False
        self.UpdateEnabling()
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

    def UpdateEnabling(self):
        sh_idx = int(self.dds["table_shape"].SelectedIndex)
        self.fields["table_w"].textbox.Enabled = (sh_idx != 3)
        self.fields["corner_r"].textbox.Enabled = sh_idx in (1, 2)

        ly_idx = int(self.dds["seat_layout"].SelectedIndex)
        has_chairs = (ly_idx != 4)
        self.dds["chair_style"].Enabled = has_chairs
        self.fields["total_seats"].textbox.Enabled = has_chairs
        self.sli_pull.Enabled = has_chairs
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
            self._syncing_rot = True
            self.sli_rot.Value = int(s["rot_deg"])
            self.txt_rot_val.Text = str(int(s["rot_deg"]))
            self._syncing_rot = False
            self._syncing_pull = True
            self.sli_pull.Value = int(round(s["pull_out"] * 10.0))
            self._syncing_pull = False
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
            parts, curves, info = build_dining_set_system(
                self.center_in, S, False, self.scale_from_inch
            )
            self.conduit.preview_breps = parts
            self.conduit.preview_curves = curves

            disp_l = format_dining_length(info.get("table_len_in", 0.0) * self.scale_from_inch, self.unit_name)
            disp_w = format_dining_length(info.get("table_w_in", 0.0) * self.scale_from_inch, self.unit_name)
            disp_h = format_dining_length(S["table_h"] * self.scale_from_inch, self.unit_name)
            self.summary_lbl.Text = "Table Dimensions: %s x %s %s   |   Height: %s %s   |   Seats: %d" % (
                disp_l, disp_w, self.unit_name, disp_h, self.unit_name, info.get("chair_count", 0)
            )
            self.lbl_info.Text = "Chairs / Seats: %d  |  Rotation: %d deg  |  3D Components: %d" % (
                info.get("chair_count", 0), S["rot_deg"], len(parts)
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


def show_dining_dialog(dlg, doc):
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
def create_modern_dining_set():
    doc = Rhino.RhinoDoc.ActiveDoc or sc.doc
    unit_sys, unit_name, u = get_doc_unit_info(doc)
    init_s = get_initial_settings()

    mode = "center"
    first_pt_doc = None

    while True:
        initial_gp = ric.GetPoint()
        initial_gp.SetCommandPrompt("Pick center point of dining table")
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
                p1 = rs.GetPoint("Pick start point of dining table span")
                if not p1:
                    return
                first_pt_doc = rg.Point3d(p1.X, p1.Y, p1.Z)
                break
            elif idx == opt_center:
                mode = "center"
                p1 = rs.GetPoint("Pick center point of dining table")
                if not p1:
                    return
                first_pt_doc = rg.Point3d(p1.X, p1.Y, p1.Z)
                break
        elif rc == Rhino.Input.GetResult.Nothing:
            p1 = rs.GetPoint("Pick center point of dining table")
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
        go.SetCommandPrompt("Select an existing Dining Table or Chair from a generated Dining Set to edit")
        go.GeometryFilter = rdo.ObjectType.Brep | rdo.ObjectType.Extrusion
        go.SubObjectSelect = False
        go.EnablePreSelect(True, True)
        if go.Get() != Rhino.Input.GetResult.Object:
            return
        obj = go.Object(0).Object()
        state_txt = obj.Attributes.GetUserString(METADATA_KEY) if obj else None
        decoded = decode_state(state_txt) if state_txt else None
        if not decoded:
            rs.MessageBox("Selected object is not a valid ArchTools Dining Set.", 48, "Dining Set Edit")
            return
        saved_c_in, saved_s = decoded
        edit_target_ids = get_generated_group_member_ids(doc, obj)
        center_in, init_s = transform_center_from_current_objects(doc, saved_c_in, saved_s, edit_target_ids, u)

    elif mode == "span":
        gp_s = DiningSpanPointGetter(first_pt_doc, init_s, u, fixed_length=False)
        gp_s.SetCommandPrompt("Pick end point of dining table length & orientation")
        gp_s.SetBasePoint(first_pt_doc, True)
        gp_s.DrawLineFromPoint(first_pt_doc, True)
        if gp_s.Get() != Rhino.Input.GetResult.Point:
            return
        p2 = gp_s.Point()
        dx = p2.X - first_pt_doc.X
        dy = p2.Y - first_pt_doc.Y
        dist_doc = math.sqrt(dx * dx + dy * dy)
        if (dist_doc / u) >= 30.0:
            init_s["table_len"] = clamp(dist_doc / u, 24.0, 240.0)
            init_s["seat_capacity"] = 0  # Custom size
        init_s["rot_deg"] = int(round(math.degrees(math.atan2(dy, dx))))
        mid_doc = 0.5 * (first_pt_doc + rg.Point3d(p2.X, p2.Y, first_pt_doc.Z))
        center_in = rg.Point3d(mid_doc.X / u, mid_doc.Y / u, mid_doc.Z / u)

    else:
        gp_r = DiningSpanPointGetter(first_pt_doc, init_s, u, fixed_length=True)
        gp_r.SetCommandPrompt("Pick direction to orient dining table (or press ENTER for 0 deg)")
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

    dlg = DiningSetDialog()
    dlg.Initialize(
        center_in,
        initial_settings=init_s,
        is_edit=bool(edit_target_ids),
    )
    dialog_result = False
    try:
        dialog_result = show_dining_dialog(dlg, doc)
    finally:
        try:
            dlg.ClosePreview()
        except Exception:
            pass

    if not dialog_result or not dlg.final_settings:
        return

    S = dlg.final_settings

    sn = doc.BeginUndoRecord("Create Modern Dining Table & Chairs")
    rs.EnableRedraw(False)
    try:
        ids = bake_dining_set(doc, center_in, S, u, edit_target_ids)
    except Exception as ex:
        ids = []
        import traceback
        traceback.print_exc()
        rs.MessageBox("Unexpected error creating dining set: {}".format(ex), 0, "Dining Set Error")
    finally:
        rs.EnableRedraw(True)
        if sn > 0:
            doc.EndUndoRecord(sn)

    doc.Views.Redraw()
    if ids:
        print("\nModern Dining Table & Chair Set Created Successfully!")
        print("Table: {:.1f} x {:.1f} {} | Height: {:.1f} {} | Seats: {}".format(
            S["table_len"] * u, S["table_w"] * u, unit_name, S["table_h"] * u, unit_name, S["total_seats"]
        ))


def run():
    create_modern_dining_set()


if __name__ in ["__main__", "ArchDiningSet", "DiningSet", "__builtin__"]:
    create_modern_dining_set()

