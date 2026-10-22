# ==============================================================================
# Shalik Furniture Suite - Parametric Generator
# Author & Architect: Sakhawat Hosen Sumon (arch.sakhawat@gmail.com)
# GitHub: https://github.com/arch-sakhawat/SHALIK-FURNITURE
# Copyright (c) 2026 Sakhawat Hosen Sumon. All Rights Reserved.
# THIS SOFTWARE IS STRICTLY PROPRIETARY AND COMMERCIAL — NOT FREE.
# Unauthorized copying, distribution, or reverse-engineering is strictly
# prohibited and subject to immediate legal court cases and prosecution.
# ==============================================================================
# -*- coding: utf-8 -*-
from __future__ import division
"""
Modern Architectural Sofa & Sectional Generator (units: INCHES internally, auto-scaled via ArchUnits)
Compatible with Rhino 7 & Rhino 8 (both IronPython 2.7 and CPython 3 / Python.NET).

Flow:
  1. Command prompt defaults to DrawFootprint with [DrawFootprint] and [SelectFootprint] options
     (D and S underlined; selectable via d/s + Enter or mouse click).
     - DrawFootprint: Pick start point -> end point (width & facing direction) -> optional depth point
       (or press ENTER for standard ergonomic sofa depth) with live 3D wireframe preview!
     - SelectFootprint: Select a closed rectangle/curve OR select an existing generated Sofa group
       to non-destructively edit its parameters in place.
  2. Settings Dialog -> Live shaded + wireframe preview in the viewport with:
     - 9 Sofa Typologies (Linear, L-Chaise Left/Right, U-Sectional, Curved Serpentine,
       Chesterfield, Modular Low-Slung, Mid-Century Tuxedo, Daybed Bench)
     - 5 Armrest Styles, 5 Base/Leg Systems, 4 Cushion Styles, Throw Pillows & Side Tables
     - Curated Upholstery, Frame/Wood & Metal Finishes + Presets.
  3. Press Create / Apply Edit -> Baked onto SOFA :: CUSHION / FRAME_BASE / LEGS_HARDWARE /
     PILLOWS / WOOD_TRIM layers with layer-based materials and grouped with editable metadata.
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


def parse_sofa_length(text, current_unit="in"):
    if ArchUnits:
        return ArchUnits.parse_length(text, current_unit)
    try:
        return float(text)
    except Exception:
        return 0.0


def format_sofa_length(v, unit_name="in", is_int=False):
    if ArchUnits:
        return ArchUnits.format_length(v, unit_name, is_int)
    if is_int:
        return str(int(round(v)))
    return ("%.3f" % v).rstrip("0").rstrip(".")


def update_label_unit(label, unit_name):
    if ArchUnits:
        return ArchUnits.update_label_unit(label, unit_name)
    return re.sub(r'\(in\b', '(' + unit_name, str(label), flags=re.IGNORECASE)


NON_LENGTH_KEYS = {"seat_bays", "back_angle_deg", "curve_sweep_deg", "channel_count", "pillow_count"}


# ============================================================
# CONSTANTS & DEFAULTS (INCHES)
# ============================================================
STICKY_KEY = "ShalikSofa_Settings_v1"
CONDUIT_KEY = "ShalikSofa_ActiveConduit"
METADATA_KEY = "ShalikSofaState"
ITEM_INDEX_KEY = "ShalikSofaItemIndex"
ITEM_CENTER_KEY = "ShalikSofaItemCenter"
PRESET_FOLDER_NAME = "ShalikTools"
PRESET_FILE_NAME = "ModernSofaPresets.json"

DEFAULT_SOFA_DEPTH_IN = 38.0   # ~965 mm standard architectural sofa depth

SOFA_TYPE_NAMES = [
    "0. Linear Modern Sofa (2 to 5 Seater)",
    "1. L-Shape Sectional (Left Chaise Lounge)",
    "2. L-Shape Sectional (Right Chaise Lounge)",
    "3. U-Shape Double-Chaise Pit Sectional",
    "4. Curved / Serpentine Organic Sofa",
    "5. Chesterfield / Deep-Channel Tufted Sofa",
    "6. Modular Low-Slung Lounge (Camaleonda / Togo Style)",
    "7. Mid-Century Tuxedo Box Sofa",
    "8. Architectural Daybed / Gallery Bench",
]

ARM_STYLE_NAMES = [
    "0. Wide Track / Box Armrest",
    "1. Slim Mid-Century Tapered Arm",
    "2. Rolled / Cylinder Bolster Arm",
    "3. Cantilevered Pillow /Flared Arm",
    "4. Armless (Open Modular Ends)",
]

BASE_STYLE_NAMES = [
    "0. Recessed Architectural Plinth Base",
    "1. Splayed Mid-Century Tapered Wood Legs",
    "2. Minimalist Tubular Metal Stiletto Legs",
    "3. Continuous Sled / Cantilever Bar Base",
    "4. Exposed Timber Platform Deck + Legs",
]

CUSHION_STYLE_NAMES = [
    "0. Soft Bullnose Chamfered Cushions",
    "1. Crisp Architectural Box Cushions",
    "2. Channel-Tufted / Ribbed Cushions",
    "3. Single Continuous Bench Cushion",
]

PILLOW_OPT_NAMES = [
    "0. Back Cushions + Corner Throw Pillows",
    "1. Back Cushions + Full Lumbar Pillows",
    "2. Back Cushions Only (Clean Minimalist)",
    "3. cylindrical Bolster Cushions",
]

SIDE_TABLE_OPT_NAMES = [
    "0. None",
    "1. Integrated Wood End Table (Left)",
    "2. Integrated Wood End Table (Right)",
    "3. Integrated Wood End Tables (Both Sides)",
    "4. Matching Front Ottoman / Pouf",
]

# Finishes: (Name, (R, G, B))
FABRIC_FINISHES = [
    ("Ivory Cream Boucle",       (238, 233, 224)),
    ("Warm Oatmeal Linen",       (214, 202, 186)),
    ("Architectural Charcoal",   ( 62,  65,  70)),
    ("Cognac Saddle Leather",    (162,  92,  52)),
    ("Espresso Full-Grain Leather", (72, 48, 36)),
    ("Sage Olive Velvet",        (115, 130, 108)),
    ("Terracotta Rust Chenille", (178,  88,  64)),
    ("Deep Navy Velvet",         ( 38,  54,  82)),
    (" Dove Pearl Gray",         (175, 178, 182)),
    ("Mustard Ochre Wool",       (198, 154,  58)),
]

PILLOW_FINISHES = [
    ("Contrast Warm Taupe",      (182, 168, 152)),
    ("Soft Cream Linen",         (242, 238, 230)),
    ("Terracotta Accent",        (185,  85,  60)),
    ("Charcoal Wool",            ( 52,  55,  60)),
    ("Forest Emerald Velvet",    ( 45,  82,  65)),
    ("Mustard Gold Accent",      (205, 160,  62)),
    ("Matching Main Upholstery", (214, 202, 186)),
]

WOOD_FINISHES = [
    ("American Black Walnut",    ( 92,  62,  42)),
    ("Natural White Oak",        (196, 162, 124)),
    ("Smoked Ash Timber",        ( 68,  58,  50)),
    ("Warm Teak Wood",           (165, 112,  68)),
    ("Matte Ebony Stained Oak",  ( 36,  34,  34)),
]

METAL_FINISHES = [
    ("Matte Jet Black Steel",    ( 32,  34,  36)),
    ("Satin Brushed Brass",      (198, 164,  88)),
    ("Polished Stainless Chrome",(210, 214, 218)),
    ("Anodized Dark Bronze",     ( 64,  54,  46)),
    ("Champagne Titanium",       (178, 168, 152)),
]

FABRIC_NAMES = ["%d. %s" % (i, n) for i, (n, c) in enumerate(FABRIC_FINISHES)]
PILLOW_NAMES = ["%d. %s" % (i, n) for i, (n, c) in enumerate(PILLOW_FINISHES)]
WOOD_NAMES   = ["%d. %s" % (i, n) for i, (n, c) in enumerate(WOOD_FINISHES)]
METAL_NAMES  = ["%d. %s" % (i, n) for i, (n, c) in enumerate(METAL_FINISHES)]

# Numeric fields: (key, label, default_in_inches, min_in, max_in, is_int)
NUM_FIELDS = [
    # Overall & Ergonomics
    ("total_h",          "Overall backrest height (in):",       32.0,  16.0,  60.0, False),
    ("seat_h",           "Seat top height from floor (in):",    17.5,  12.0,  26.0, False),
    ("seat_thick",       "Seat cushion thickness (in):",         6.5,   3.0,  14.0, False),
    ("seat_bays",        "Number of seat cushion bays:",         3,     1,     8,   True),
    ("cushion_gap",      "Seam / cushion gap (in):",             0.35,  0.05,  2.0, False),
    ("cushion_radius",   "Cushion edge softness radius (in):",   1.5,   0.1,   5.0, False),
    ("channel_count",    "Tufting / channel ribs per bay:",      5,     2,    12,   True),
    # Backrest & Arms
    ("back_thick",       "Backrest structural thickness (in):",  7.0,   3.0,  18.0, False),
    ("back_cushion_t",   "Back pillow thickness (in):",          5.5,   2.0,  12.0, False),
    ("back_angle_deg",   "Backrest recline angle (deg, 0-25):",  8.0,   0.0,  25.0, False),
    ("arm_w",            "Armrest width (in):",                  7.0,   2.0,  18.0, False),
    ("arm_h",            "Armrest height from floor (in):",     25.0,  16.0,  42.0, False),
    # Sectional & Curved Geometry
    ("chaise_depth",     "Sectional chaise total depth (in):",  64.0,  42.0, 110.0, False),
    ("chaise_w",         "Sectional chaise width (in):",        36.0,  24.0,  72.0, False),
    ("curve_sweep_deg",  "Curved sofa arc sweep (deg, 15-160):", 65.0, 15.0, 160.0, False),
    # Base, Legs & Accessories
    ("leg_h",            "Leg / plinth clearance height (in):",  5.5,   1.0,  14.0, False),
    ("leg_r",            "Leg radius / bar thickness (in):",     0.85,  0.3,   3.0, False),
    ("plinth_inset",     "Plinth / leg inset from edge (in):",   2.5,   0.5,   8.0, False),
    ("table_w",          "Integrated side table width (in):",   14.0,   8.0,  36.0, False),
]

DD_FIELDS = [
    ("sofa_type",        "Sofa typology:",               0, SOFA_TYPE_NAMES),
    ("arm_style",        "Armrest style:",               0, ARM_STYLE_NAMES),
    ("base_style",       "Base & leg system:",           1, BASE_STYLE_NAMES),
    ("cushion_style",    "Seat cushion profile:",        0, CUSHION_STYLE_NAMES),
    ("pillow_opt",       "Back & throw pillow layout:",  0, PILLOW_OPT_NAMES),
    ("side_table_opt",   "Integrated table / ottoman:",  0, SIDE_TABLE_OPT_NAMES),
    ("fabric_finish",    "Main upholstery material:",    0, FABRIC_NAMES),
    ("pillow_finish",    "Throw pillow material:",       0, PILLOW_NAMES),
    ("wood_finish",      "Timber / deck finish:",        0, WOOD_NAMES),
    ("metal_finish",     "Legs & hardware finish:",      0, METAL_NAMES),
]

TAB_LAYOUT = [
    ("1. Sofa Type && Size", [
        "sofa_type",
        "seat_bays",
        "total_h",
        "seat_h",
        "seat_thick",
        "chaise_depth",
        "chaise_w",
        "curve_sweep_deg",
        "side_table_opt",
        "table_w",
    ]),
    ("2. Cushions, Arms && Base", [
        "cushion_style",
        "cushion_radius",
        "cushion_gap",
        "channel_count",
        "arm_style",
        "arm_w",
        "arm_h",
        "back_thick",
        "back_cushion_t",
        "back_angle_deg",
        "pillow_opt",
        "base_style",
        "leg_h",
        "leg_r",
        "plinth_inset",
    ]),
    ("3. Upholstery && Finishes", [
        "fabric_finish",
        "pillow_finish",
        "wood_finish",
        "metal_finish",
        "@flip_cb",
        "@fast_cb",
    ]),
]


# ============================================================
# SETTINGS & ETO HELPERS
# ============================================================
def clamp(v, lo, hi):
    if v < lo:
        return lo
    if v > hi:
        return hi
    return v


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
    s["flip_facing"] = False
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
    out["flip_facing"] = bool(settings.get("flip_facing", False))
    out["fast_preview"] = bool(settings.get("fast_preview", False))
    return out


def get_initial_settings():
    saved = sc.sticky.get(STICKY_KEY)
    if saved:
        return normalize_settings(saved)
    return default_settings()


def rgb_to_color(rgb):
    return System.Drawing.Color.FromArgb(int(rgb[0]), int(rgb[1]), int(rgb[2]))


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
    base = os.environ.get("APPDATA")
    if not base:
        try:
            base = os.path.expanduser("~")
        except Exception:
            base = os.getcwd()
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
        presets = {}
        for name, settings in data.items():
            if name and isinstance(settings, dict):
                presets[str(name)] = normalize_settings(settings)
        return presets
    except Exception:
        return {}


def save_presets(presets):
    path = _get_preset_path()
    try:
        clean = {}
        for name, settings in presets.items():
            if name:
                clean[str(name)] = normalize_settings(settings)
        text = json.dumps(clean, ensure_ascii=False, indent=2, sort_keys=True)
        with codecs.open(path, "w", "utf-8") as f:
            f.write(text)
        return True
    except Exception:
        return False


# ============================================================
# METADATA & NON-DESTRUCTIVE EDITING HELPERS
# ============================================================
def _point_to_data(pt):
    return [float(pt.X), float(pt.Y), float(pt.Z)]


def _vector_to_data(vec):
    return [float(vec.X), float(vec.Y), float(vec.Z)]


def _point_from_data(data):
    return rg.Point3d(float(data[0]), float(data[1]), float(data[2]))


def _vector_from_data(data):
    return rg.Vector3d(float(data[0]), float(data[1]), float(data[2]))


def _safe_unitize(vec, fallback=None):
    v = rg.Vector3d(vec)
    if v.Length < 1e-6:
        v = rg.Vector3d(fallback) if fallback is not None else rg.Vector3d(1, 0, 0)
    v.Unitize()
    return v


def _dot(a, b):
    return a.X * b.X + a.Y * b.Y + a.Z * b.Z


def encode_state(center_in, width_vec, depth_vec, width_in, depth_in, settings):
    state = {
        "version": 1,
        "frame": {
            "center": _point_to_data(center_in),
            "width_vec": _vector_to_data(width_vec),
            "depth_vec": _vector_to_data(depth_vec),
            "width_in": float(width_in),
            "depth_in": float(depth_in),
        },
        "settings": normalize_settings(settings),
    }
    return json.dumps(state, ensure_ascii=False)


def decode_state(text):
    if not text:
        return None
    try:
        state = json.loads(text)
        frame = state["frame"]
        center_in = _point_from_data(frame["center"])
        width_vec = _safe_unitize(_vector_from_data(frame["width_vec"]), rg.Vector3d.XAxis)
        depth_vec = _safe_unitize(_vector_from_data(frame["depth_vec"]), rg.Vector3d.YAxis)
        width_in = float(frame["width_in"])
        depth_in = float(frame["depth_in"])
        settings = normalize_settings(state.get("settings", {}))
        return center_in, width_vec, depth_vec, width_in, depth_in, settings
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


def transform_frame_from_current_objects(doc, center_doc, width_vec, depth_vec, target_ids):
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

    if len(orig_pts) < 2:
        return center_doc, width_vec, depth_vec

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

    angle = math.atan2(cross_sum, dot_sum) if (abs(dot_sum) > 1e-6 or abs(cross_sum) > 1e-6) else 0.0
    ca, sa = math.cos(angle), math.sin(angle)

    dx = center_doc.X - ox
    dy = center_doc.Y - oy
    new_center = rg.Point3d(cx + ca * dx - sa * dy, cy + sa * dx + ca * dy, center_doc.Z + (cz - oz))
    new_w = _safe_unitize(rg.Vector3d(ca * width_vec.X - sa * width_vec.Y, sa * width_vec.X + ca * width_vec.Y, width_vec.Z), width_vec)
    new_d = _safe_unitize(rg.Vector3d(ca * depth_vec.X - sa * depth_vec.Y, sa * depth_vec.X + ca * depth_vec.Y, depth_vec.Z), depth_vec)
    return new_center, new_w, new_d


# ============================================================
# 3D SOFA GEOMETRY PRIMITIVES (LOCAL INCH COORDINATES)
# ============================================================
# Local Sofa Coordinate System:
#   X = Width  (-W/2 to +W/2, Left to Right)
#   Y = Depth  (-D/2 = Back wall of sofa, +D/2 = Front edge of seat, +Y = Forward lounge direction)
#   Z = Height (0 = Floor level, +Z = Upward)

def mk_box(x1, x2, y1, y2, z1, z2):
    if (x2 - x1) < 1e-4 or (y2 - y1) < 1e-4 or (z2 - z1) < 1e-4:
        return None
    b = rg.Box(
        rg.Plane.WorldXY,
        rg.Interval(x1, x2),
        rg.Interval(y1, y2),
        rg.Interval(z1, z2)
    )
    return b.ToBrep() if b.IsValid else None


def make_cyl(pt0, pt1, r):
    v = pt1 - pt0
    if v.Length < 1e-4 or r <= 1e-4:
        return None
    pl = rg.Plane(pt0, v)
    return rg.Cylinder(rg.Circle(pl, r), v.Length).ToBrep(True, True)


def make_tapered_leg(pt_top, pt_bot, r_top, r_bot, tol):
    v = pt_bot - pt_top
    if v.Length < 1e-4:
        return None
    pl_top = rg.Plane(pt_top, v)
    pl_bot = rg.Plane(pt_bot, v)
    c_top = rg.Circle(pl_top, max(0.1, r_top)).ToNurbsCurve()
    c_bot = rg.Circle(pl_bot, max(0.1, r_bot)).ToNurbsCurve()
    lofts = rg.Brep.CreateFromLoft([c_top, c_bot], rg.Point3d.Unset, rg.Point3d.Unset, rg.LoftType.Normal, False)
    if lofts and len(lofts) > 0:
        capped = lofts[0].CapPlanarHoles(max(tol, 0.01))
        return capped if capped else lofts[0]
    return make_cyl(pt_top, pt_bot, r_top)


def make_soft_cushion_box(x1, x2, y1, y2, z1, z2, rad, fast, tol):
    """
    Creates a soft architectural cushion with a rounded bullnose profile in the Y-Z plane
    extruded along X (or a filleted XY profile extruded along Z).
    """
    w = x2 - x1
    d = y2 - y1
    h = z2 - z1
    if w < 0.25 or d < 0.25 or h < 0.25:
        return None

    r = clamp(rad, 0.0, min(w, d, h) * 0.42)
    if fast or r < 0.15:
        return mk_box(x1, x2, y1, y2, z1, z2)

    # Create a rounded rectangle in the Y-Z cross-section plane at X = x1 and extrude along +X
    # This gives realistic soft top/bottom front & back bullnose edges on seat and back cushions!
    try:
        pl_yz = rg.Plane(rg.Point3d(x1, y1, z1), rg.Vector3d.YAxis, rg.Vector3d.ZAxis)
        rect = rg.Rectangle3d(pl_yz, rg.Interval(0.0, d), rg.Interval(0.0, h)).ToNurbsCurve()
        filleted = rg.Curve.CreateFilletCornersCurve(rect, r, 1e-3, 1e-3)
        prof = filleted if (filleted and filleted.IsClosed) else rect
        srf = rg.Surface.CreateExtrusion(prof, rg.Vector3d(w, 0.0, 0.0))
        if srf:
            b = srf.ToBrep()
            if b:
                capped = b.CapPlanarHoles(max(tol, 0.01))
                res = capped if capped else b
                if res.SolidOrientation == rg.BrepSolidOrientation.Inward:
                    res.Flip()
                return res
    except Exception:
        pass
    return mk_box(x1, x2, y1, y2, z1, z2)


def make_plan_rounded_box(x1, x2, y1, y2, z1, z2, r_plan, fast, tol):
    """Creates a vertical box with rounded corners in the XY plan plane."""
    w = x2 - x1
    d = y2 - y1
    h = z2 - z1
    if w < 0.25 or d < 0.25 or h < 0.25:
        return None
    r = clamp(r_plan, 0.0, min(w, d) * 0.42)
    if fast or r < 0.15:
        return mk_box(x1, x2, y1, y2, z1, z2)
    try:
        pl_xy = rg.Plane(rg.Point3d(x1, y1, z1), rg.Vector3d.XAxis, rg.Vector3d.YAxis)
        rect = rg.Rectangle3d(pl_xy, rg.Interval(0.0, w), rg.Interval(0.0, d)).ToNurbsCurve()
        filleted = rg.Curve.CreateFilletCornersCurve(rect, r, 1e-3, 1e-3)
        prof = filleted if (filleted and filleted.IsClosed) else rect
        srf = rg.Surface.CreateExtrusion(prof, rg.Vector3d(0.0, 0.0, h))
        if srf:
            b = srf.ToBrep()
            if b:
                capped = b.CapPlanarHoles(max(tol, 0.01))
                res = capped if capped else b
                if res.SolidOrientation == rg.BrepSolidOrientation.Inward:
                    res.Flip()
                return res
    except Exception:
        pass
    return mk_box(x1, x2, y1, y2, z1, z2)


def make_seat_cushion_unit(x1, x2, y1, y2, z1, z2, S, fast, tol):
    """Builds a single seat cushion bay according to S['cushion_style'] (Bullnose, Crisp, Channel-Tufted)."""
    c_style = int(S["cushion_style"])
    rad = float(S["cushion_radius"])
    ch_cnt = max(2, int(S["channel_count"]))

    if c_style == 1:
        # Crisp box cushion with subtle plan corner rounding
        b = make_plan_rounded_box(x1, x2, y1, y2, z1, z2, min(rad * 0.5, 0.6), fast, tol)
        return [b] if b else []

    if c_style == 2 and not fast:
        # Channel-tufted / ribbed cushion
        w = x2 - x1
        ch_w = w / float(ch_cnt)
        gap = 0.08
        ribs = []
        for k in range(ch_cnt):
            rx0 = x1 + k * ch_w + gap * 0.5
            rx1 = x1 + (k + 1) * ch_w - gap * 0.5
            rb = make_soft_cushion_box(rx0, rx1, y1, y2, z1, z2, min(rad, ch_w * 0.4), False, tol)
            if rb:
                ribs.append(rb)
        return ribs

    # Default 0 or 3: Soft Bullnose Chamfered Cushion
    b = make_soft_cushion_box(x1, x2, y1, y2, z1, z2, rad, fast, tol)
    return [b] if b else []


def make_reclined_back_pillow(x1, x2, y_front_bot, p_thick, z_bot, z_top, recline_deg, rad, fast, tol):
    """Builds an ergonomically reclined backrest pillow or lumbar cushion."""
    h = z_top - z_bot
    if (x2 - x1) < 1.0 or p_thick < 0.5 or h < 2.0:
        return None
    b = make_soft_cushion_box(x1, x2, y_front_bot - p_thick, y_front_bot, z_bot, z_top, rad, fast, tol)
    if b and abs(recline_deg) > 0.5:
        ang = math.radians(clamp(recline_deg, 0.0, 25.0))
        # Rotate backward (-Y) around XAxis at bottom front edge
        b.Rotate(ang, rg.Vector3d.XAxis, rg.Point3d(0.5 * (x1 + x2), y_front_bot, z_bot))
    return b


def build_base_and_legs_for_rect(x1, x2, y1, y2, z_deck_bot, z_deck_top, S, fast, tol):
    """
    Builds the base deck and leg system for a rectangular footprint [x1..x2, y1..y2]:
      0: Recessed Architectural Plinth Base
      1: Splayed Mid-Century Tapered Wood Legs
      2: Minimalist Tubular Metal Stiletto Legs
      3: Continuous Sled / Cantilever Bar Base
      4: Exposed Timber Platform Deck + Legs
    """
    parts = []
    b_style = int(S["base_style"])
    leg_r = max(0.25, float(S["leg_r"]))
    inset = clamp(float(S["plinth_inset"]), 0.5, min(x2 - x1, y2 - y1) * 0.25)

    # Structural upholstered or timber deck frame from z_deck_bot to z_deck_top
    deck_kind = "wood" if b_style == 4 else "frame"
    deck_b = make_plan_rounded_box(x1, x2, y1, y2, z_deck_bot, z_deck_top, 0.8, fast, tol)
    if deck_b:
        parts.append((deck_kind, deck_b))

    if z_deck_bot <= 0.25:
        return parts

    lx0 = x1 + inset
    lx1 = x2 - inset
    ly0 = y1 + inset
    ly1 = y2 - inset

    # Add central support leg if span is wide (> 68 in)
    x_positions = [lx0, lx1]
    if (lx1 - lx0) > 68.0:
        x_positions.append(0.5 * (lx0 + lx1))

    if b_style == 0:
        # 0. Recessed Architectural Plinth Base
        p_in = max(1.5, inset)
        plinth = make_plan_rounded_box(x1 + p_in, x2 - p_in, y1 + p_in, y2 - p_in, 0.0, z_deck_bot + 0.2, 0.6, fast, tol)
        if plinth:
            parts.append(("wood", plinth))

    elif b_style in (1, 4):
        # 1 & 4. Splayed Mid-Century Tapered Wood Legs
        splay = min(1.8, z_deck_bot * 0.25)
        for xp in x_positions:
            sx = -splay if xp < 0 else (splay if xp > 0 else 0.0)
            for yp, sy in ((ly0, -splay * 0.7), (ly1, splay * 0.7)):
                p_top = rg.Point3d(xp, yp, z_deck_bot + 0.3)
                p_bot = rg.Point3d(xp + sx, yp + sy, 0.0)
                leg = make_tapered_leg(p_top, p_bot, leg_r * 1.15, leg_r * 0.6, tol)
                if leg:
                    parts.append(("wood", leg))

    elif b_style == 2:
        # 2. Minimalist Tubular Metal Stiletto Legs
        for xp in x_positions:
            for yp in (ly0, ly1):
                p_top = rg.Point3d(xp, yp, z_deck_bot + 0.3)
                p_bot = rg.Point3d(xp, yp, 0.0)
                leg = make_cyl(p_bot, p_top, leg_r * 0.75)
                if leg:
                    parts.append(("metal", leg))

    elif b_style == 3:
        # 3. Continuous Sled / Cantilever Bar Base
        bar_w = leg_r * 1.4
        bar_t = leg_r * 0.65
        for xp in (lx0, lx1):
            # Vertical front & back posts + bottom runner bar
            v_front = mk_box(xp - bar_t * 0.5, xp + bar_t * 0.5, ly1 - bar_w, ly1, 0.0, z_deck_bot + 0.2)
            v_back  = mk_box(xp - bar_t * 0.5, xp + bar_t * 0.5, ly0, ly0 + bar_w, 0.0, z_deck_bot + 0.2)
            runner  = mk_box(xp - bar_t * 0.5, xp + bar_t * 0.5, ly0, ly1, 0.0, bar_t)
            for sb in (v_front, v_back, runner):
                if sb:
                    parts.append(("metal", sb))

    return parts


def build_armrest_unit(x0, x1, y0, y1, z_bot, z_arm_top, is_left, S, fast, tol):
    """Builds left or right armrest according to S['arm_style']."""
    parts = []
    a_style = int(S["arm_style"])
    if a_style == 4:
        return parts

    aw = x1 - x0
    ad = y1 - y0
    ah = z_arm_top - z_bot
    if aw < 0.5 or ad < 2.0 or ah < 2.0:
        return parts

    rad = float(S["cushion_radius"])

    if a_style == 0:
        # 0. Wide Track / Box Armrest
        b = make_soft_cushion_box(x0, x1, y0, y1, z_bot, z_arm_top, min(rad * 0.7, 1.2), fast, tol)
        if b:
            parts.append(("frame", b))

    elif a_style == 1:
        # 1. Slim Mid-Century Tapered Arm
        b = make_plan_rounded_box(x0, x1, y0, y1, z_bot, z_arm_top, min(aw * 0.4, 1.0), fast, tol)
        if b:
            parts.append(("frame", b))

    elif a_style == 2:
        # 2. Rolled / Cylinder Bolster Arm
        stem_h = max(2.0, ah - aw * 0.55)
        stem = mk_box(x0, x1, y0, y1, z_bot, z_bot + stem_h)
        if stem:
            parts.append(("frame", stem))
        roll_r = aw * 0.62
        cx = x0 + aw * 0.42 if is_left else x1 - aw * 0.42
        cz = z_arm_top - roll_r * 0.85
        roll = make_cyl(rg.Point3d(cx, y0, cz), rg.Point3d(cx, y1, cz), roll_r)
        if roll:
            parts.append(("frame", roll))

    elif a_style == 3:
        # 3. Cantilevered Pillow / Flared Arm
        base_arm = mk_box(x0, x1, y0, y1, z_bot, z_bot + ah * 0.65)
        if base_arm:
            parts.append(("frame", base_arm))
        pad = make_soft_cushion_box(x0 - 0.5, x1 + 0.5, y0 + 1.0, y1 - 0.5, z_bot + ah * 0.55, z_arm_top, rad, fast, tol)
        if pad:
             ang = math.radians(10.0 if is_left else -10.0)
             pad.Rotate(ang, rg.Vector3d.YAxis, rg.Point3d(0.5 * (x0 + x1), 0.5 * (y0 + y1), z_bot + ah * 0.6))
             parts.append(("pillow", pad))

    return parts


# ============================================================
# SPECIALIZED CURVED / SERPENTINE SOFA BUILDER (TYPE 4)
# ============================================================
def build_curved_serpentine_sofa(W, D, S, fast, tol):
    """
    TYPE 4 - Curved / Serpentine Organic Sofa (Vladimir Kagan / Boucle Lounge Style).
    Sweeps an organic arc footprint across width W and depth D with segmented cushions,
    swept curved backrest, and plinth/stiletto base.
    """
    parts = []
    preview_curves = []

    total_h = float(S["total_h"])
    seat_h = clamp(float(S["seat_h"]), 12.0, total_h - 6.0)
    seat_t = clamp(float(S["seat_thick"]), 3.0, seat_h - 1.5)
    leg_h = clamp(float(S["leg_h"]), 1.0, seat_h - seat_t - 1.0)
    z_deck_bot = leg_h
    z_seat_bot = seat_h - seat_t
    bays = max(2, int(S["seat_bays"]))
    back_t = clamp(float(S["back_thick"]), 4.0, D * 0.45)

    sweep_deg = clamp(float(S["curve_sweep_deg"]), 20.0, 150.0)
    sweep_rad = math.radians(sweep_deg)
    half_ang = sweep_rad * 0.5

    # Compute arc radius so chord span matches W
    R_mid = max(D * 1.1, (W * 0.5) / max(0.15, math.sin(half_ang)))
    R_back = R_mid + D * 0.5
    R_BackInner = R_back - back_t
    R_front = max(6.0, R_mid - D * 0.5)

    # Center of curvature placed forward (+Y) so sofa curves concave toward the viewer (+Y)
    sagitta = R_mid * (1.0 - math.cos(half_ang))
    cy = R_mid - sagitta * 0.5

    def make_annular_sector_solid(r_in, r_out, ang0, ang1, z0, z1):
        if r_out <= r_in + 0.2 or z1 <= z0 + 0.1 or abs(ang1 - ang0) < 1e-3:
            return None
        am = 0.5 * (ang0 + ang1)

        def pt_polar(r_val, a_val):
            return rg.Point3d(r_val * math.sin(a_val), cy - r_val * math.cos(a_val), z0)

        arc_in = rg.Arc(pt_polar(r_in, ang0), pt_polar(r_in, am), pt_polar(r_in, ang1))
        arc_out = rg.Arc(pt_polar(r_out, ang1), pt_polar(r_out, am), pt_polar(r_out, ang0))

        pc = rg.PolyCurve()
        pc.Append(rg.ArcCurve(arc_in))
        pc.Append(rg.LineCurve(pt_polar(r_in, ang1), pt_polar(r_out, ang1)))
        pc.Append(rg.ArcCurve(arc_out))
        pc.Append(rg.LineCurve(pt_polar(r_out, ang0), pt_polar(r_in, ang0)))

        srf = rg.Surface.CreateExtrusion(pc, rg.Vector3d(0, 0, z1 - z0))
        if srf:
            b = srf.ToBrep()
            if b:
                capped = b.CapPlanarHoles(max(tol, 0.01))
                res = capped if capped else b
                if res.SolidOrientation == rg.BrepSolidOrientation.Inward:
                    res.Flip()
                return res
        return None

    # 1. Recessed Curved Plinth & Deck
    plinth = make_annular_sector_solid(R_front + 2.0, R_back - 2.0, -half_ang * 0.94, half_ang * 0.94, 0.0, z_deck_bot)
    if plinth:
        parts.append(("wood", plinth))

    deck = make_annular_sector_solid(R_front, R_back, -half_ang, half_ang, z_deck_bot, z_seat_bot)
    if deck:
        parts.append(("frame", deck))

    # 2. Curved Swept Backrest
    back_solid = make_annular_sector_solid(R_BackInner, R_back, -half_ang, half_ang, z_seat_bot, total_h)
    if back_solid:
        parts.append(("frame", back_solid))

    # 3. Segmented Curved Seat Cushion Bays & Backrest Pillows
    d_ang = sweep_rad / float(bays)
    gap_ang = math.radians(0.6)
    for i in range(bays):
        a0 = -half_ang + i * d_ang + (gap_ang if i > 0 else 0.0)
        a1 = -half_ang + (i + 1) * d_ang - (gap_ang if i < bays - 1 else 0.0)
        c_seat = make_annular_sector_solid(R_front, R_BackInner + 0.5, a0, a1, z_seat_bot, seat_h)
        if c_seat:
            parts.append(("cushion", c_seat))

        if int(S["pillow_opt"]) in (0, 1, 2):
            p_t = clamp(float(S["back_cushion_t"]), 2.5, (R_BackInner - R_front) * 0.35)
            c_pil = make_annular_sector_solid(R_BackInner - p_t, R_BackInner, a0 + gap_ang, a1 - gap_ang, seat_h, total_h - 1.5)
            if c_pil:
                parts.append(("pillow", c_pil))

    return parts, preview_curves


# ============================================================
# MAIN SOFA ASSEMBLY BUILDER (ALL 9 SOFA TYPOLOGIES)
# ============================================================
def build_sofa_system(center_in, width_vec, depth_vec, width_in, depth_in, S, final=True, u=1.0):
    """
    Builds the complete 3D Sofa / Sectional in local inch space and transforms to world document space.
    Returns: (parts_list, preview_curves, info_dict)
    where parts_list = [(kind, brep), ...] with kind in ('cushion', 'frame', 'pillow', 'wood', 'metal').
    """
    tol = get_tolerance()
    fast = (not final) and bool(S["fast_preview"])

    sofa_type = int(S["sofa_type"])
    W = max(30.0, float(width_in))
    D = max(24.0, float(depth_in))

    # Apply typology-specific architectural overrides while respecting user customization
    total_h = float(S["total_h"])
    seat_h = clamp(float(S["seat_h"]), 12.0, total_h - 4.0)
    seat_t = clamp(float(S["seat_thick"]), 3.0, seat_h - 1.0)
    leg_h = clamp(float(S["leg_h"]), 0.5, seat_h - seat_t - 0.5)

    if sofa_type == 6:
        # Type 6: Modular Low-Slung Lounge (Camaleonda / Togo floor-hugging plinth)
        leg_h = min(leg_h, 1.5)
        seat_t = max(seat_t, 9.5)

    z_deck_bot = leg_h
    z_seat_bot = seat_h - seat_t
    z_seat_top = seat_h

    bays = max(1, int(S["seat_bays"]))
    gap = float(S["cushion_gap"])
    rad = float(S["cushion_radius"])
    arm_style = int(S["arm_style"])
    arm_w = 0.0 if (arm_style == 4 or sofa_type == 8) else clamp(float(S["arm_w"]), 2.0, W * 0.22)
    arm_h = clamp(float(S["arm_h"]), seat_h + 2.0, total_h + 4.0)

    if sofa_type in (5, 7):
        # Chesterfield (Type 5) & Mid-Century Tuxedo (Type 7) have equal-height arms and back!
        arm_h = total_h

    back_t = 0.0 if sofa_type == 8 else clamp(float(S["back_thick"]), 3.0, D * 0.45)
    back_pil_t = clamp(float(S["back_cushion_t"]), 2.0, D * 0.35)
    recline_deg = float(S["back_angle_deg"])
    pillow_opt = int(S["pillow_opt"])
    table_opt = int(S["side_table_opt"])
    table_w = clamp(float(S["table_w"]), 8.0, 36.0)

    # Delegate Type 4 (Curved / Serpentine Sofa) to polar builder
    if sofa_type == 4:
        local_parts, local_curves = build_curved_serpentine_sofa(W, D, S, fast, tol)
    else:
        local_parts = []
        local_curves = []

        # Deduct side table widths if integrated side tables are enabled
        x_left_outer  = -W * 0.5
        x_right_outer =  W * 0.5

        x_sofa_left  = x_left_outer + (table_w if table_opt in (1, 3) else 0.0)
        x_sofa_right = x_right_outer - (table_w if table_opt in (2, 3) else 0.0)
        if (x_sofa_right - x_sofa_left) < 24.0:
            x_sofa_left, x_sofa_right = x_left_outer, x_right_outer

        y_back  = -D * 0.5
        y_front =  D * 0.5

        # --------------------------------------------------------
        # 1. INTEGRATED TIMBER SIDE TABLES OR FRONT OTTOMAN
        # --------------------------------------------------------
        if table_opt in (1, 3) and x_sofa_left > x_left_outer + 1.0:
            tb_l = make_plan_rounded_box(x_left_outer, x_sofa_left, y_back, y_front, z_deck_bot, z_seat_bot + 1.5, 0.8, fast, tol)
            if tb_l:
                local_parts.append(("wood", tb_l))
        if table_opt in (2, 3) and x_right_outer > x_sofa_right + 1.0:
            tb_r = make_plan_rounded_box(x_sofa_right, x_right_outer, y_back, y_front, z_deck_bot, z_seat_bot + 1.5, 0.8, fast, tol)
            if tb_r:
                local_parts.append(("wood", tb_r))

        # --------------------------------------------------------
        # 2. BASE DECK & LEGS (MAIN SOFA + CHAISE WINGS)
        # --------------------------------------------------------
        local_parts.extend(build_base_and_legs_for_rect(
            x_left_outer, x_right_outer, y_back, y_front, z_deck_bot, z_seat_bot, S, fast, tol
        ))

        has_left_chaise  = sofa_type in (1, 3)
        has_right_chaise = sofa_type in (2, 3)
        chaise_d = max(D + 14.0, float(S["chaise_depth"]))
        chaise_w = clamp(float(S["chaise_w"]), 22.0, (x_sofa_right - x_sofa_left) * 0.45)
        y_chaise_front = y_back + chaise_d

        if has_left_chaise:
            local_parts.extend(build_base_and_legs_for_rect(
                x_sofa_left, x_sofa_left + chaise_w, y_front - 2.0, y_chaise_front, z_deck_bot, z_seat_bot, S, fast, tol
            ))
        if has_right_chaise:
            local_parts.extend(build_base_and_legs_for_rect(
                x_sofa_right - chaise_w, x_sofa_right, y_front - 2.0, y_chaise_front, z_deck_bot, z_seat_bot, S, fast, tol
            ))

        # Optional Front Ottoman (table_opt == 4)
        if table_opt == 4:
            ott_w = min(36.0, (x_sofa_right - x_sofa_left) * 0.45)
            ott_d = min(26.0, D * 0.65)
            ott_y0 = y_front + 14.0
            ott_y1 = ott_y0 + ott_d
            local_parts.extend(build_base_and_legs_for_rect(
                -ott_w * 0.5, ott_w * 0.5, ott_y0, ott_y1, z_deck_bot, z_seat_bot, S, fast, tol
            ))
            for cb in make_seat_cushion_unit(-ott_w * 0.5, ott_w * 0.5, ott_y0, ott_y1, z_seat_bot, z_seat_top, S, fast, tol):
                local_parts.append(("cushion", cb))

        # --------------------------------------------------------
        # 3. BACKREST SHELL & ARMRESTS
        # --------------------------------------------------------
        if sofa_type != 8:  # Not a backless daybed
            if sofa_type == 5 and not fast:
                # Chesterfield Deep-Channel / Tufted Backrest
                n_tufts = max(6, bays * 4)
                tw = (x_sofa_right - x_sofa_left - 2.0 * arm_w) / float(n_tufts)
                for ti in range(n_tufts):
                    tx0 = x_sofa_left + arm_w + ti * tw + 0.06
                    tx1 = tx0 + tw - 0.12
                    tb = make_soft_cushion_box(tx0, tx1, y_back, y_back + back_t, z_seat_bot, total_h, min(rad, tw * 0.4), False, tol)
                    if tb:
                        local_parts.append(("frame", tb))
            else:
                back_box = make_soft_cushion_box(
                    x_sofa_left + arm_w * 0.5, x_sofa_right - arm_w * 0.5,
                    y_back, y_back + back_t, z_seat_bot, total_h, min(rad * 0.6, 1.2), fast, tol
                )
                if back_box:
                    local_parts.append(("frame", back_box))

        # Left & Right Armrests
        if arm_w > 0.5:
            arm_style_eff = 2 if sofa_type == 5 else arm_style
            temp_s = dict(S)
            temp_s["arm_style"] = arm_style_eff
            local_parts.extend(build_armrest_unit(
                x_sofa_left, x_sofa_left + arm_w, y_back, y_front, z_seat_bot, arm_h, True, temp_s, fast, tol
            ))
            local_parts.extend(build_armrest_unit(
                x_sofa_right - arm_w, x_sofa_right, y_back, y_front, z_seat_bot, arm_h, False, temp_s, fast, tol
            ))

        # --------------------------------------------------------
        # 4. SEAT CUSHION BAYS & BACK / THROW PILLOWS
        # --------------------------------------------------------
        inner_x0 = x_sofa_left + arm_w
        inner_x1 = x_sofa_right - arm_w
        inner_w = max(12.0, inner_x1 - inner_x0)
        y_seat_start = y_back + back_t

        # Determine bay intervals along X
        if int(S["cushion_style"]) == 3 and not (has_left_chaise or has_right_chaise):
            # Single Continuous Bench Cushion
            bay_intervals = [(inner_x0, inner_x1, y_front)]
        else:
            bay_w = inner_w / float(bays)
            bay_intervals = []
            for i in range(bays):
                bx0 = inner_x0 + i * bay_w + (gap * 0.5 if i > 0 else 0.0)
                bx1 = inner_x0 + (i + 1) * bay_w - (gap * 0.5 if i < bays - 1 else 0.0)
                # Check if this bay is a chaise lounge extension
                by_front = y_front
                if has_left_chaise and i == 0:
                    bx0 = x_sofa_left + arm_w
                    bx1 = max(bx1, x_sofa_left + chaise_w)
                    by_front = y_chaise_front
                elif has_right_chaise and i == bays - 1:
                    bx0 = min(bx0, x_sofa_right - chaise_w)
                    bx1 = x_sofa_right - arm_w
                    by_front = y_chaise_front
                bay_intervals.append((bx0, bx1, by_front))

        for b_idx, (bx0, bx1, by_front) in enumerate(bay_intervals):
            for cb in make_seat_cushion_unit(bx0, bx1, y_seat_start, by_front, z_seat_bot, z_seat_top, S, fast, tol):
                local_parts.append(("cushion", cb))

            # Back Cushions & Lumbar / Throw Pillows
            if sofa_type == 8 or pillow_opt == 3:
                # Cylindrical Bolster Pillows (Daybed or Bolster option)
                bol_r = min(3.8, D * 0.14)
                if b_idx == 0 or b_idx == len(bay_intervals) - 1:
                    bx_bol = bx0 + bol_r * 1.2 if b_idx == 0 else bx1 - bol_r * 1.2
                    bol = make_cyl(
                        rg.Point3d(bx_bol, y_seat_start + 2.0, z_seat_top + bol_r),
                        rg.Point3d(bx_bol, y_front - 2.0, z_seat_top + bol_r),
                        bol_r
                    )
                    if bol:
                        local_parts.append(("pillow", bol))
            elif sofa_type != 5:
                # Backrest Pillow for this bay
                y_pil_front = y_seat_start + back_pil_t
                z_pil_top = total_h + 1.2
                bp = make_reclined_back_pillow(
                    bx0 + 0.2, bx1 - 0.2, y_pil_front, back_pil_t,
                    z_seat_top, z_pil_top, recline_deg, rad, fast, tol
                )
                if bp:
                    local_parts.append(("pillow", bp))

                # Full Lumbar Pillows (pillow_opt == 1)
                if pillow_opt == 1:
                    lum_t = back_pil_t * 0.65
                    lum_h = (z_pil_top - z_seat_top) * 0.52
                    lp = make_reclined_back_pillow(
                        bx0 + 1.8, bx1 - 1.8, y_pil_front + lum_t * 0.85, lum_t,
                        z_seat_top, z_seat_top + lum_h, recline_deg + 4.0, rad * 0.8, fast, tol
                    )
                    if lp:
                        local_parts.append(("pillow", lp))

        # Corner Decorative Throw Pillows (pillow_opt == 0 and not Daybed)
        if pillow_opt == 0 and sofa_type != 8 and inner_w > 28.0:
            pw_throw = min(16.0, inner_w * 0.25)
            pt_throw = 4.2
            ph_throw = min(15.0, (total_h - z_seat_top) * 0.95)
            y_th = y_seat_start + back_pil_t + pt_throw * 0.7

            for is_l, tx_c in ((True, inner_x0 + pw_throw * 0.55), (False, inner_x1 - pw_throw * 0.55)):
                th_b = make_soft_cushion_box(
                    tx_c - pw_throw * 0.5, tx_c + pw_throw * 0.5,
                    y_th - pt_throw, y_th,
                    z_seat_top, z_seat_top + ph_throw,
                    rad, fast, tol
                )
                if th_b:
                    yaw = math.radians(-22.0 if is_l else 22.0)
                    tilt = math.radians(12.0)
                    c_rot = rg.Point3d(tx_c, y_th - pt_throw * 0.5, z_seat_top + ph_throw * 0.3)
                    th_b.Rotate(tilt, rg.Vector3d.XAxis, c_rot)
                    th_b.Rotate(yaw, rg.Vector3d.ZAxis, c_rot)
                    local_parts.append(("pillow", th_b))

    # --------------------------------------------------------
    # 5. TRANSFORM FROM LOCAL INCH FRAME -> WORLD DOCUMENT SPACE
    # --------------------------------------------------------
    flip_sign = -1.0 if bool(S.get("flip_facing", False)) else 1.0
    w_dir = _safe_unitize(width_vec * flip_sign, rg.Vector3d.XAxis)
    d_dir = _safe_unitize(depth_vec * flip_sign, rg.Vector3d.YAxis)

    # Forward direction Indicator Arrow in local space (points along +Y front of sofa)
    arrow_pts = [
        rg.Point3d(-3.0, D * 0.5 + 2.0, 0.2),
        rg.Point3d( 3.0, D * 0.5 + 2.0, 0.2),
        rg.Point3d( 0.0, D * 0.5 + 9.0, 0.2),
        rg.Point3d(-3.0, D * 0.5 + 2.0, 0.2),
    ]
    local_curves.append(rg.Polyline(arrow_pts).ToNurbsCurve())

    target_plane_in = rg.Plane(center_in, w_dir, d_dir)
    plane_xform = rg.Transform.PlaneToPlane(rg.Plane.WorldXY, target_plane_in)
    scale_xform = rg.Transform.Scale(rg.Point3d.Origin, u) if abs(u - 1.0) > 1e-6 else None

    world_parts = []
    for kind, b in local_parts:
        if b and b.IsValid:
            nb = b.DuplicateBrep()
            nb.Transform(plane_xform)
            if scale_xform:
                nb.Transform(scale_xform)
            world_parts.append((kind, nb))

    world_curves = []
    for c in local_curves:
        if c and c.IsValid:
            nc = c.DuplicateCurve()
            nc.Transform(plane_xform)
            if scale_xform:
                nc.Transform(scale_xform)
            world_curves.append(nc)

    info = {
        "width_in": W,
        "depth_in": D,
        "height_in": total_h,
        "bays": bays,
    }
    return world_parts, world_curves, info


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


def bake_sofa(doc, center_in, width_vec, depth_vec, width_in, depth_in, S, u=1.0, edit_target_ids=None):
    parts, _, _ = build_sofa_system(center_in, width_vec, depth_vec, width_in, depth_in, S, True, u)

    fab_name, fab_rgb = FABRIC_FINISHES[S["fabric_finish"]]
    pil_name, pil_rgb = PILLOW_FINISHES[S["pillow_finish"]]
    if S["pillow_finish"] == len(PILLOW_FINISHES) - 1:
        pil_name, pil_rgb = fab_name, fab_rgb
    wd_name, wd_rgb   = WOOD_FINISHES[S["wood_finish"]]
    mt_name, mt_rgb   = METAL_FINISHES[S["metal_finish"]]

    colors = {
        "cushion": rgb_to_color(fab_rgb),
        "frame":   rgb_to_color(fab_rgb),
        "pillow":  rgb_to_color(pil_rgb),
        "wood":    rgb_to_color(wd_rgb),
        "metal":   rgb_to_color(mt_rgb),
    }

    main_layer_idx = get_or_create_layer(doc, "SOFA")
    parent_id = doc.Layers[main_layer_idx].Id

    layers = {
        "cushion": get_or_create_layer_with_material(doc, "CUSHION", parent_id, colors["cushion"], "Sofa Cushion " + fab_name, colors["cushion"]),
        "frame":   get_or_create_layer_with_material(doc, "FRAME_BASE", parent_id, colors["frame"], "Sofa Frame " + fab_name, colors["frame"]),
        "pillow":  get_or_create_layer_with_material(doc, "PILLOWS", parent_id, colors["pillow"], "Sofa Pillow " + pil_name, colors["pillow"]),
        "wood":    get_or_create_layer_with_material(doc, "WOOD_TRIM", parent_id, colors["wood"], "Sofa Wood " + wd_name, colors["wood"]),
        "metal":   get_or_create_layer_with_material(doc, "LEGS_HARDWARE", parent_id, colors["metal"], "Sofa Metal " + mt_name, colors["metal"]),
    }

    if edit_target_ids:
        for gid in edit_target_ids:
            try:
                doc.Objects.Delete(gid, True)
            except Exception:
                pass

    state_json = encode_state(center_in, width_vec, depth_vec, width_in, depth_in, S)
    ids = []
    for idx, (kind, brep) in enumerate(parts):
        if not brep or not brep.IsValid:
            continue
        c_pt = _brep_center(brep)
        attr = make_attributes(layers.get(kind, layers["cushion"]), "Sofa_" + kind, state_json, idx, c_pt)
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
# LIVE VIEWPORT PREVIEW CONDUIT & INTERACTIVE POINT GETTERS
# ============================================================
class SofaPreviewConduit(rd.DisplayConduit):
    def __init__(self, wireframe_only=False):
        super(SofaPreviewConduit, self).__init__()
        self.preview_breps = []
        self.preview_curves = []
        self.wireframe_only = wireframe_only
        self.materials = {}
        self.set_finishes(default_settings())

    def set_finishes(self, S):
        fab_rgb = FABRIC_FINISHES[S["fabric_finish"]][1]
        pil_rgb = PILLOW_FINISHES[S["pillow_finish"]][1]
        if S["pillow_finish"] == len(PILLOW_FINISHES) - 1:
            pil_rgb = fab_rgb
        wd_rgb  = WOOD_FINISHES[S["wood_finish"]][1]
        mt_rgb  = METAL_FINISHES[S["metal_finish"]][1]
        self.materials = {
            "cushion": rd.DisplayMaterial(rgb_to_color(fab_rgb)),
            "frame":   rd.DisplayMaterial(rgb_to_color(fab_rgb)),
            "pillow":  rd.DisplayMaterial(rgb_to_color(pil_rgb)),
            "wood":    rd.DisplayMaterial(rgb_to_color(wd_rgb)),
            "metal":   rd.DisplayMaterial(rgb_to_color(mt_rgb)),
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
                    col = System.Drawing.Color.DeepSkyBlue if kind in ("cushion", "pillow") else System.Drawing.Color.Gold
                    e.Display.DrawBrepWires(brep, col, 1)
                else:
                    mat = self.materials.get(kind, self.materials["cushion"])
                    if mat:
                        e.Display.DrawBrepShaded(brep, mat)
                    e.Display.DrawBrepWires(brep, System.Drawing.Color.FromArgb(45, 45, 50), 1)
            for crv in self.preview_curves:
                if crv and crv.IsValid:
                    e.Display.DrawCurve(crv, System.Drawing.Color.Gold, 2)
        except Exception:
            pass


class SofaWidthPointGetter(ric.GetPoint):
    """Live 3D sofa wireframe preview while picking the second point (width & orientation)."""
    def __init__(self, p0, settings, u, default_depth_in=DEFAULT_SOFA_DEPTH_IN):
        super(SofaWidthPointGetter, self).__init__()
        self.p0 = rg.Point3d(p0)
        self.u = u if u > 0 else 1.0
        self.default_depth_in = default_depth_in
        self.S = dict(settings)
        self.S["fast_preview"] = True

    def OnDynamicDraw(self, e):
        try:
            pt = e.CurrentPoint
            base_z = self.p0.Z
            a = rg.Point3d(self.p0.X, self.p0.Y, base_z)
            b = rg.Point3d(pt.X, pt.Y, base_z)
            v = b - a
            v.Z = 0.0
            w_in = v.Length / self.u
            if w_in < 30.0:
                e.Display.DrawLine(a, b, System.Drawing.Color.Gold, 2)
                return

            w_vec = _safe_unitize(v, rg.Vector3d.XAxis)
            d_vec = _safe_unitize(rg.Vector3d.CrossProduct(rg.Vector3d.ZAxis, w_vec), rg.Vector3d.YAxis)
            mid_back = 0.5 * (a + b)
            center_doc = mid_back + d_vec * (0.5 * self.default_depth_in * self.u)
            center_in = rg.Point3d(center_doc.X / self.u, center_doc.Y / self.u, center_doc.Z / self.u)

            parts, curves, _ = build_sofa_system(
                center_in, w_vec, d_vec, w_in, self.default_depth_in, self.S, False, self.u
            )
            for kind, brep in parts:
                if brep and brep.IsValid:
                    col = System.Drawing.Color.DeepSkyBlue if kind in ("cushion", "pillow") else System.Drawing.Color.Gold
                    e.Display.DrawBrepWires(brep, col, 1)
            for crv in curves:
                if crv and crv.IsValid:
                    e.Display.DrawCurve(crv, System.Drawing.Color.Gold, 2)
        except Exception:
            pass


class SofaDepthPointGetter(ric.GetPoint):
    """Live 3D sofa wireframe preview while picking the third point (depth & front direction)."""
    def __init__(self, p0, p1, settings, u):
        super(SofaDepthPointGetter, self).__init__()
        self.p0 = rg.Point3d(p0)
        self.p1 = rg.Point3d(p1)
        self.u = u if u > 0 else 1.0
        self.S = dict(settings)
        self.S["fast_preview"] = True

    def OnDynamicDraw(self, e):
        try:
            curr = e.CurrentPoint
            ok, c_doc, w_vec, d_vec, doc_w, doc_d = compute_sofa_frame_from_3pts(self.p0, self.p1, curr)
            if not ok or (doc_w / self.u) < 30.0 or (doc_d / self.u) < 24.0:
                return
            center_in = rg.Point3d(c_doc.X / self.u, c_doc.Y / self.u, c_doc.Z / self.u)
            parts, curves, _ = build_sofa_system(
                center_in, w_vec, d_vec, doc_w / self.u, doc_d / self.u, self.S, False, self.u
            )
            for kind, brep in parts:
                if brep and brep.IsValid:
                    col = System.Drawing.Color.DeepSkyBlue if kind in ("cushion", "pillow") else System.Drawing.Color.Gold
                    e.Display.DrawBrepWires(brep, col, 1)
            for crv in curves:
                if crv and crv.IsValid:
                    e.Display.DrawCurve(crv, System.Drawing.Color.Gold, 2)
        except Exception:
            pass


def compute_sofa_frame_from_3pts(p0, p1, p2):
    base_z = p0.Z
    a = rg.Point3d(p0.X, p0.Y, base_z)
    b = rg.Point3d(p1.X, p1.Y, base_z)
    c = rg.Point3d(p2.X, p2.Y, base_z)

    v_w = b - a
    v_w.Z = 0.0
    doc_w = v_w.Length
    if doc_w < 1e-3:
        return False, None, None, None, 0.0, 0.0

    w_vec = _safe_unitize(v_w, rg.Vector3d.XAxis)
    raw_d = c - b
    raw_d.Z = 0.0
    perp_d = raw_d - w_vec * _dot(raw_d, w_vec)
    if perp_d.Length < 1e-3:
        raw_d = c - a
        raw_d.Z = 0.0
        perp_d = raw_d - w_vec * _dot(raw_d, w_vec)
    if perp_d.Length < 1e-3:
        return False, None, None, None, 0.0, 0.0

    doc_d = perp_d.Length
    d_vec = _safe_unitize(perp_d, rg.Vector3d.YAxis)
    # Ensure right-handed coordinate frame (w_vec x d_vec points +Z)
    if rg.Vector3d.CrossProduct(w_vec, d_vec).Z < 0:
        w_vec.Reverse()

    mid_back = 0.5 * (a + b)
    center_doc = mid_back + d_vec * (0.5 * doc_d)
    return True, center_doc, w_vec, d_vec, doc_w, doc_d


def extract_rectangle_frame(crv):
    if not crv or not crv.IsClosed:
        return False, None, None, None, 0.0, 0.0, "Please select a closed rectangular polyline/curve."
    rc, pl = crv.TryGetPolyline()
    if not rc or pl.Count < 4:
        return False, None, None, None, 0.0, 0.0, "Could not extract 4 corners from rectangle curve."

    pts = [pl[i] for i in range(4)]
    cx = sum(p.X for p in pts) / 4.0
    cy = sum(p.Y for p in pts) / 4.0
    cz = min(p.Z for p in pts)
    center = rg.Point3d(cx, cy, cz)

    edges = []
    for i in range(4):
        v = pts[(i + 1) % 4] - pts[i]
        v.Z = 0.0
        edges.append((i, v.Length, v))
    edges.sort(key=lambda item: item[1], reverse=True)
    long_idx, doc_w, w_vec = edges[0]
    d_vec = pts[(long_idx + 2) % 4] - pts[(long_idx + 1) % 4]
    d_vec.Z = 0.0
    doc_d = d_vec.Length
    if doc_w < 1e-3 or doc_d < 1e-3:
        return False, None, None, None, 0.0, 0.0, "Rectangle dimensions are too small."

    w_vec = _safe_unitize(w_vec, rg.Vector3d.XAxis)
    d_vec = _safe_unitize(d_vec, rg.Vector3d.YAxis)
    if rg.Vector3d.CrossProduct(w_vec, d_vec).Z < 0:
        d_vec.Reverse()
    return True, center, w_vec, d_vec, doc_w, doc_d, ""


# ============================================================
# DIALOG UI
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
        self.textbox = make_textbox(format_sofa_length(disp_val, unit_name, is_int))

    def value(self):
        try:
            txt = self.textbox.Text.strip()
            if self.is_length:
                val_unit = parse_sofa_length(txt, self.unit_name)
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
        self.textbox.Text = format_sofa_length(disp_val, self.unit_name, self.is_int)


class SofaDialog(forms.Dialog[bool]):
    def __init__(self):
        super(SofaDialog, self).__init__()
        self._initialized = False
        self._preview_closed = False
        self._suppress_preview = True
        self.final_settings = None
        self.conduit = None

    def Initialize(self, center_in, width_vec, depth_vec, width_in, depth_in, initial_settings=None, is_edit=False):
        if self._initialized:
            return
        self._initialized = True

        unit_sys, unit_name, scale_from_inch = get_doc_unit_info()
        self.unit_name = unit_name
        self.scale_from_inch = scale_from_inch

        self.center_in = center_in
        self.width_vec = width_vec
        self.depth_vec = depth_vec
        self.width_in = width_in
        self.depth_in = depth_in
        self.is_edit = is_edit

        title_prefix = "Edit Modern Sofa & Sectional" if is_edit else "Modern Architectural Sofa & Sectional Generator"
        self.Title = "%s [%s]" % (title_prefix, unit_name)
        self.Padding = drawing.Padding(10)
        self.Resizable = True
        try:
            self.Topmost = True
        except Exception:
            pass
        self.ClientSize = drawing.Size(660, 760)

        prev_conduit = sc.sticky.get(CONDUIT_KEY)
        if prev_conduit is not None:
            try:
                prev_conduit.Enabled = False
            except Exception:
                pass

        self.conduit = SofaPreviewConduit(wireframe_only=False)
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

        self.cb_flip = make_checkbox("Flip front / back facing orientation (180 deg)", s["flip_facing"])
        self.cb_fast = make_checkbox("Fast preview (skip cushion edge fillets while editing)", s["fast_preview"])

        self.dd_preset = forms.DropDown()
        self.dd_preset.Width = 190
        self.txt_preset_name = make_textbox("", width=150)
        self.btn_preset_load = make_button("Load")
        self.btn_preset_save = make_button("Save")
        self.btn_preset_delete = make_button("Delete")
        self._refresh_preset_dropdown()

        main = forms.DynamicLayout()
        main.Spacing = drawing.Size(5, 5)

        disp_w = format_sofa_length(self.width_in * scale_from_inch, unit_name)
        disp_d = format_sofa_length(self.depth_in * scale_from_inch, unit_name)
        self.summary_lbl = make_label(
            "Footprint Width: %s %s   |   Base Depth: %s %s" % (disp_w, unit_name, disp_d, unit_name),
            bold=True
        )
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
                if key == "@flip_cb":
                    tab_layout.AddRow(make_label(""), self.cb_flip)
                elif key == "@fast_cb":
                    tab_layout.AddRow(make_label(""), self.cb_fast)
                elif key in self.dds:
                    tab_layout.AddRow(make_label(self.labels[key]), self.dds[key])
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

        btn_ok = make_button("Apply Edit" if is_edit else "Create")
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
            f.textbox.TextChanged += self.OnAnyChanged
        for key, dd in self.dds.items():
            dd.SelectedIndexChanged += self.OnAnyChanged
        self.cb_flip.CheckedChanged += self.OnAnyChanged
        self.cb_fast.CheckedChanged += self.OnAnyChanged

        self.dd_preset.SelectedIndexChanged += self.OnPresetSelectedChanged
        self.btn_preset_load.Click += self.OnPresetLoadClicked
        self.btn_preset_save.Click += self.OnPresetSaveClicked
        self.btn_preset_delete.Click += self.OnPresetDeleteClicked

        self.UpdateEnabling()
        self._suppress_preview = False
        self.UpdatePreview()

    def UpdateEnabling(self):
        st = int(self.dds["sofa_type"].SelectedIndex)
        has_chaise = st in (1, 2, 3)
        self.fields["chaise_depth"].textbox.Enabled = has_chaise
        self.fields["chaise_w"].textbox.Enabled = has_chaise
        self.fields["curve_sweep_deg"].textbox.Enabled = (st == 4)

        arm_on = (int(self.dds["arm_style"].SelectedIndex) != 4) and (st != 8)
        self.fields["arm_w"].textbox.Enabled = arm_on
        self.fields["arm_h"].textbox.Enabled = (arm_on and st not in (5, 7))

        c_style = int(self.dds["cushion_style"].SelectedIndex)
        self.fields["channel_count"].textbox.Enabled = (c_style == 2 or st == 5)

        tb_opt = int(self.dds["side_table_opt"].SelectedIndex)
        self.fields["table_w"].textbox.Enabled = (tb_opt in (1, 2, 3))

    def OnAnyChanged(self, sender, e):
        self.UpdateEnabling()
        self.UpdatePreview()

    def GetCurrentSettings(self):
        raw = {}
        for key, f in self.fields.items():
            raw[key] = f.value()
        for key, dd in self.dds.items():
            raw[key] = int(dd.SelectedIndex)
        raw["flip_facing"] = is_checkbox_checked(self.cb_flip)
        raw["fast_preview"] = is_checkbox_checked(self.cb_fast)
        return normalize_settings(raw)

    def ApplySettingsToUI(self, settings):
        s = normalize_settings(settings)
        self._suppress_preview = True
        try:
            for key, f in self.fields.items():
                f.set_value(s[key])
            for key, dd in self.dds.items():
                dd.SelectedIndex = int(s[key])
            set_checkbox_checked(self.cb_flip, s["flip_facing"])
            set_checkbox_checked(self.cb_fast, s["fast_preview"])
            self.UpdateEnabling()
        finally:
            self._suppress_preview = False
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
        if getattr(self, "_preview_closed", False) or getattr(self, "_suppress_preview", False):
            return
        try:
            S = self.GetCurrentSettings()
            self.conduit.set_finishes(S)
            parts, curves, info = build_sofa_system(
                self.center_in, self.width_vec, self.depth_vec,
                self.width_in, self.depth_in, S, False, self.scale_from_inch
            )
            self.conduit.preview_breps = parts
            self.conduit.preview_curves = curves

            st_short = SOFA_TYPE_NAMES[S["sofa_type"]].split(". ", 1)[-1]
            h_disp = format_sofa_length(S["total_h"] * self.scale_from_inch, self.unit_name)
            sh_disp = format_sofa_length(S["seat_h"] * self.scale_from_inch, self.unit_name)
            self.lbl_info.Text = "%s  |  Bays: %d  |  Back Height: %s %s  |  Seat Height: %s %s" % (
                st_short, S["seat_bays"], h_disp, self.unit_name, sh_disp, self.unit_name
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


def show_sofa_dialog(dlg, doc):
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
def create_modern_sofa():
    doc = Rhino.RhinoDoc.ActiveDoc or sc.doc
    unit_sys, unit_name, u = get_doc_unit_info(doc)
    init_s = get_initial_settings()

    # --------------------------------------------------------
    # STEP 1: DEFAULT DRAW FOOTPRINT OR SELECT FOOTPRINT (D / S)
    # --------------------------------------------------------
    mode = "draw"
    start_pt = None

    while True:
        initial_gp = ric.GetPoint()
        initial_gp.SetCommandPrompt("Start of sofa back-left corner")
        initial_gp.AcceptNothing(True)
        opt_draw = initial_gp.AddOption("DrawFootprint")
        opt_select = initial_gp.AddOption("SelectFootprint")

        rc = initial_gp.Get()
        if rc == Rhino.Input.GetResult.Point:
            start_pt = initial_gp.Point()
            mode = "draw"
            break
        elif rc == Rhino.Input.GetResult.Option:
            if initial_gp.OptionIndex() == opt_select:
                mode = "select"
                break
            elif initial_gp.OptionIndex() == opt_draw:
                p1 = rs.GetPoint("Pick back-left start point of sofa")
                if not p1:
                    return
                start_pt = rg.Point3d(p1.X, p1.Y, p1.Z)
                mode = "draw"
                break
        elif rc == Rhino.Input.GetResult.Nothing:
            p1 = rs.GetPoint("Pick back-left start point of sofa")
            if not p1:
                return
            start_pt = rg.Point3d(p1.X, p1.Y, p1.Z)
            mode = "draw"
            break
        else:
            return

    center_in = None
    width_vec = None
    depth_vec = None
    width_in = 0.0
    depth_in = DEFAULT_SOFA_DEPTH_IN
    edit_target_ids = []

    # --------------------------------------------------------
    # STEP 2A: SELECT RECTANGLE CURVE OR EXISTING SOFA TO EDIT
    # --------------------------------------------------------
    if mode == "select":
        go = ric.GetObject()
        go.SetCommandPrompt("Select closed rectangle curve or existing Sofa to edit")
        go.GeometryFilter = rdo.ObjectType.Curve | rdo.ObjectType.Brep | rdo.ObjectType.Extrusion
        go.SubObjectSelect = False
        go.EnablePreSelect(True, True)
        if go.Get() != Rhino.Input.GetResult.Object:
            return

        objref = go.Object(0)
        obj = objref.Object()
        state_txt = obj.Attributes.GetUserString(METADATA_KEY) if obj else None
        decoded = decode_state(state_txt) if state_txt else None

        if decoded:
            c_in, width_vec, depth_vec, width_in, depth_in, saved_s = decoded
            init_s = saved_s
            edit_target_ids = get_generated_group_member_ids(doc, obj)
            c_doc = rg.Point3d(c_in.X * u, c_in.Y * u, c_in.Z * u)
            c_doc, width_vec, depth_vec = transform_frame_from_current_objects(doc, c_doc, width_vec, depth_vec, edit_target_ids)
            center_in = rg.Point3d(c_doc.X / u, c_doc.Y / u, c_doc.Z / u)
        else:
            crv = objref.Curve()
            ok, c_doc, width_vec, depth_vec, doc_w, doc_d, err = extract_rectangle_frame(crv)
            if not ok:
                rs.MessageBox(err, 48, "Sofa Footprint Error")
                return
            center_in = rg.Point3d(c_doc.X / u, c_doc.Y / u, c_doc.Z / u)
            width_in = doc_w / u
            depth_in = doc_d / u

    # --------------------------------------------------------
    # STEP 2B: DRAW SOFA FOOTPRINT WITH LIVE 3D PREVIEW
    # --------------------------------------------------------
    else:
        gp_w = SofaWidthPointGetter(start_pt, init_s, u, DEFAULT_SOFA_DEPTH_IN)
        gp_w.SetCommandPrompt("Pick end point of sofa width (defines width & facing direction)")
        gp_w.SetBasePoint(start_pt, True)
        gp_w.DrawLineFromPoint(start_pt, True)
        if gp_w.Get() != Rhino.Input.GetResult.Point:
            return
        p1 = gp_w.Point()

        d_disp = format_sofa_length(DEFAULT_SOFA_DEPTH_IN * u, unit_name)
        gp_d = SofaDepthPointGetter(start_pt, p1, init_s, u)
        gp_d.SetCommandPrompt("Pick front depth point or press ENTER for standard depth <%s %s>" % (d_disp, unit_name))
        gp_d.SetBasePoint(p1, True)
        gp_d.DrawLineFromPoint(p1, True)
        gp_d.AcceptNothing(True)
        rc_d = gp_d.Get()

        if rc_d == Rhino.Input.GetResult.Point:
            p2 = gp_d.Point()
            ok, c_doc, width_vec, depth_vec, doc_w, doc_d = compute_sofa_frame_from_3pts(start_pt, p1, p2)
            if not ok or (doc_w / u) < 30.0 or (doc_d / u) < 24.0:
                rs.MessageBox("Sofa footprint dimensions are too small (min 30 x 24 in).", 48, "Sofa Error")
                return
            center_in = rg.Point3d(c_doc.X / u, c_doc.Y / u, c_doc.Z / u)
            width_in = doc_w / u
            depth_in = doc_d / u
        elif rc_d == Rhino.Input.GetResult.Nothing:
            base_z = start_pt.Z
            a = rg.Point3d(start_pt.X, start_pt.Y, base_z)
            b = rg.Point3d(p1.X, p1.Y, base_z)
            v = b - a
            v.Z = 0.0
            if (v.Length / u) < 30.0:
                rs.MessageBox("Sofa width is too short (minimum 30 in).", 48, "Sofa Error")
                return
            width_vec = _safe_unitize(v, rg.Vector3d.XAxis)
            depth_vec = _safe_unitize(rg.Vector3d.CrossProduct(rg.Vector3d.ZAxis, width_vec), rg.Vector3d.YAxis)
            mid_back = 0.5 * (a + b)
            c_doc = mid_back + depth_vec * (0.5 * DEFAULT_SOFA_DEPTH_IN * u)
            center_in = rg.Point3d(c_doc.X / u, c_doc.Y / u, c_doc.Z / u)
            width_in = v.Length / u
            depth_in = DEFAULT_SOFA_DEPTH_IN
        else:
            return

    # --------------------------------------------------------
    # STEP 3: SETTINGS DIALOG WITH LIVE SHADED PREVIEW
    # --------------------------------------------------------
    dlg = SofaDialog()
    dlg.Initialize(
        center_in, width_vec, depth_vec, width_in, depth_in,
        initial_settings=init_s,
        is_edit=bool(edit_target_ids),
    )
    dialog_result = False
    try:
        dialog_result = show_sofa_dialog(dlg, doc)
    finally:
        try:
            dlg.ClosePreview()
        except Exception:
            pass

    if not dialog_result or not dlg.final_settings:
        return

    S = dlg.final_settings

    # --------------------------------------------------------
    # STEP 4: BAKE TO DOCUMENT
    # --------------------------------------------------------
    sn = doc.BeginUndoRecord("Create Modern Sofa")
    rs.EnableRedraw(False)
    try:
        ids = bake_sofa(doc, center_in, width_vec, depth_vec, width_in, depth_in, S, u, edit_target_ids)
    except Exception as ex:
        ids = []
        import traceback
        traceback.print_exc()
        rs.MessageBox("Unexpected error creating sofa: {}".format(ex), 0, "Sofa Error")
    finally:
        rs.EnableRedraw(True)
        if sn > 0:
            doc.EndUndoRecord(sn)

    doc.Views.Redraw()
    if ids:
        st_name = SOFA_TYPE_NAMES[S["sofa_type"]].split(". ", 1)[-1]
        print("\nModern Sofa Created Successfully: {}".format(st_name))
        print("Width: {:.1f} {} | Depth: {:.1f} {} | Height: {:.1f} {}".format(
            width_in * u, unit_name, depth_in * u, unit_name, S["total_h"] * u, unit_name
        ))


def run():
    create_modern_sofa()


if __name__ in ["__main__", "ArchSofa", "Sofa", "__builtin__"]:
    create_modern_sofa()
