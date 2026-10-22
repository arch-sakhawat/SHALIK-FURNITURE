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
Modern Architectural Bed & Master Suite Generator (units: INCHES internally, auto-scaled via ArchUnits)
Compatible with Rhino 7 & Rhino 8 (both IronPython 2.7 and CPython 3 / Python.NET).

Flow:
  1. Command prompt defaults to DrawFootprint with [DrawFootprint] and [SelectFootprint] options
     (D and S underlined; selectable via d/s + Enter or mouse click).
     - DrawFootprint: Pick back-left corner -> back-right corner (headboard width & facing direction)
       -> optional foot length point (or press ENTER for standard Queen/King length) with live 3D preview!
     - SelectFootprint: Select a closed rectangle curve OR select an existing generated Bed group
       to non-destructively edit its parameters in place.
  2. Settings Dialog -> Live shaded + wireframe preview in the viewport with:
     - 8 Bed Typologies (Modern Platform, Floating Cantilever, Wingback, Extended Hotel Wall-Panel,
       Four-Poster Canopy, Japanese Tatami Low-Profile, Upholstered Sleigh, Daybed)
     - 6 Mattress Size Presets (Custom Footprint, King, Queen, Cal King, Double/Full, Twin/Single)
     - 5 Headboard Styles (Channel-Tufted, Biscuit Grid, Split Cushion, Solid Timber, Cane Inlay)
     - Full Bedding & Pillow Stack (Fitted Sheet, Folded Duvet, Runner Throw, Sleeping & Euro Pillows)
     - Integrated Nightstands & End-of-Bed Ottoman Bench + Curated Finishes & Presets.
  3. Press Create / Apply Edit -> Baked onto BED :: MATTRESS_SHEET / DUVET_BEDDING / PILLOWS /
     HEADBOARD / FRAME_WOOD / METAL_HARDWARE layers with layer-based materials and grouped metadata.
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


def parse_bed_length(text, current_unit="in"):
    if ArchUnits:
        return ArchUnits.parse_length(text, current_unit)
    try:
        return float(text)
    except Exception:
        return 0.0


def format_bed_length(v, unit_name="in", is_int=False):
    if ArchUnits:
        return ArchUnits.format_length(v, unit_name, is_int)
    if is_int:
        return str(int(round(v)))
    return ("%.3f" % v).rstrip("0").rstrip(".")


def update_label_unit(label, unit_name):
    if ArchUnits:
        return ArchUnits.update_label_unit(label, unit_name)
    return re.sub(r'\(in\b', '(' + unit_name, str(label), flags=re.IGNORECASE)


NON_LENGTH_KEYS = {"hb_channels", "hb_rows", "duvet_cov_pct"}


# ============================================================
# CONSTANTS & DEFAULTS (INCHES)
# ============================================================
STICKY_KEY = "ShalikBed_Settings_v1"
CONDUIT_KEY = "ShalikBed_ActiveConduit"
METADATA_KEY = "ShalikBedState"
ITEM_INDEX_KEY = "ShalikBedItemIndex"
ITEM_CENTER_KEY = "ShalikBedItemCenter"
PRESET_FOLDER_NAME = "ShalikTools"
PRESET_FILE_NAME = "ModernBedPresets.json"

DEFAULT_BED_LENGTH_IN = 84.0   # ~2135 mm standard architectural bed length

BED_TYPE_NAMES = [
    "0. Modern Architectural Platform Bed",
    "1. Floating Cantilever Bed (Recessed Plinth)",
    "2. Upholstered Wingback / Shelter Bed",
    "3. Extended Wall-Panel Hotel Suite Bed",
    "4. Architectural Four-Poster Canopy Bed",
    "5. Japanese Low-Profile Tatami Platform Bed",
    "6. Upholstered Headboard + Footboard Sleigh Bed",
    "7. Minimalist Daybed / Divan Sleeper",
]

SIZE_PRESET_NAMES = [
    "0. Custom Drawn Footprint (Use Picked Size)",
    "1. King Size (76 x 80 in Mattress)",
    "2. Queen Size (60 x 80 in Mattress)",
    "3. California King (72 x 84 in Mattress)",
    "4. Double / Full Size (54 x 75 in Mattress)",
    "5. Twin / Single Size (38 x 75 in Mattress)",
]

# Standard mattress (width_in, length_in) lookup
MATTRESS_PRESET_DIMS = {
    1: (76.0, 80.0),
    2: (60.0, 80.0),
    3: (72.0, 84.0),
    4: (54.0, 75.0),
    5: (38.0, 75.0),
}

HEADBOARD_STYLE_NAMES = [
    "0. Vertical Channel-Tufted Upholstered",
    "1. Horizontal Panel / Biscuit Grid Tufted",
    "2. Split Dual-Cushion Padded Headboard",
    "3. Smooth Architectural Slab / Solid Wood",
    "4. Timber Frame with Recessed Cane / Fabric Inlay",
]

BASE_STYLE_NAMES = [
    "0. Recessed Floating Plinth Base",
    "1. Tapered Mid-Century Timber Legs",
    "2. Minimalist Cylindrical Metal Stiletto Legs",
    "3. Flush Floor-to-Rail Box Base (Storage Style)",
    "4. Sled / Cantilever Runner Bar Base",
]

PILLOW_LAYOUT_NAMES = [
    "0. Full Luxury Stack (Euro Shams + Sleeping + Lumbar)",
    "1. Standard Double Stack (4 Sleeping Pillows)",
    "2. Minimalist Single Row (2 Sleeping Pillows)",
    "3. Cylindrical Bolsters + Sleeping Pillows",
    "4. None (Mattress & Bedding Only)",
]

BEDDING_STYLE_NAMES = [
    "0. Folded Duvet Comforter + Foot Runner Throw",
    "1. Full Tailored Duvet Comforter Only",
    "2. Minimalist Crisp Fitted Sheet Only",
]

ACCESSORY_OPT_NAMES = [
    "0. None (Bed Only)",
    "1. Integrated Floating Nightstands (Both Sides)",
    "2. Freestanding Box Nightstands (Both Sides)",
    "3. End-of-Bed Upholstered Bench / Ottoman",
    "4. Full Master Suite (Nightstands + End Bench)",
]

# Finishes: (Name, (R, G, B))
SHEET_FINISHES = [
    ("Crisp Hotel White Percale", (245, 245, 242)),
    ("Warm Ivory Organic Cotton", (238, 232, 222)),
    ("Soft Dove Silver Linen",    (205, 208, 212)),
    ("Natural Flax Oatmeal",      (216, 206, 190)),
    ("Charcoal Slate Cotton",     ( 78,  82,  86)),
]

DUVET_FINISHES = [
    ("Warm Oatmeal Belgian Linen",(214, 204, 188)),
    ("Cloud White Down Duvet",    (242, 240, 236)),
    ("Sage Olive Washed Linen",   (128, 140, 120)),
    ("Terracotta Earth Duvet",    (176,  94,  72)),
    ("Deep Navy Velvet Quilt",    ( 42,  58,  84)),
    ("Architectural Charcoal",    ( 64,  68,  72)),
    ("Warm Caramel Cashmere",     (172, 132,  94)),
]

HEADBOARD_FINISHES = [
    ("Boucle Cream Ivory",        (235, 228, 218)),
    ("Warm Taupe Velvet",         (168, 154, 140)),
    ("Cognac Saddle Leather",     (158,  88,  48)),
    ("Charcoal Wool Felt",        ( 58,  62,  66)),
    ("Moss Green Velvet",         ( 72,  92,  74)),
    ("Matching Timber Wood",      (135,  95,  62)),
]

WOOD_FINISHES = [
    ("American Black Walnut",     ( 92,  62,  42)),
    ("Natural White Oak",         (198, 166, 128)),
    ("Smoked Espresso Ash",       ( 62,  52,  46)),
    ("Warm Burmese Teak",         (162, 108,  64)),
    ("Matte Ebony Stained Oak",   ( 36,  34,  34)),
]

METAL_FINISHES = [
    ("Matte Jet Black Steel",     ( 32,  34,  36)),
    ("Satin Brushed Brass",       (198, 164,  88)),
    ("Champagne Bronze",          (168, 148, 118)),
    ("Polished Chrome Steel",     (212, 216, 220)),
]

SHEET_NAMES     = ["%d. %s" % (i, n) for i, (n, c) in enumerate(SHEET_FINISHES)]
DUVET_NAMES     = ["%d. %s" % (i, n) for i, (n, c) in enumerate(DUVET_FINISHES)]
HEADBOARD_NAMES = ["%d. %s" % (i, n) for i, (n, c) in enumerate(HEADBOARD_FINISHES)]
WOOD_NAMES      = ["%d. %s" % (i, n) for i, (n, c) in enumerate(WOOD_FINISHES)]
METAL_NAMES     = ["%d. %s" % (i, n) for i, (n, c) in enumerate(METAL_FINISHES)]

# Numeric fields: (key, label, default_in_inches, min_in, max_in, is_int)
NUM_FIELDS = [
    # Frame, Base & Mattress
    ("leg_h",            "Base / leg clearance height (in):",    6.0,   0.0,  18.0, False),
    ("rail_h",           "Platform side rail height (in):",      8.0,   3.0,  20.0, False),
    ("side_margin",      "Platform side deck reveal (in):",      3.0,   0.5,  16.0, False),
    ("foot_margin",      "Platform foot deck reveal (in):",      3.5,   0.5,  18.0, False),
    ("mattress_h",       "Mattress thickness (in):",            11.0,   5.0,  22.0, False),
    ("mattress_inset",   "Mattress recess into frame (in):",     2.0,   0.0,   6.0, False),
    ("edge_rad",         "Mattress & cushion softness (in):",    1.8,   0.1,   5.0, False),
    # Headboard & Canopy
    ("hb_h",             "Headboard total height (in):",        46.0,  24.0,  96.0, False),
    ("hb_thick",         "Headboard thickness (in):",            4.5,   1.5,  14.0, False),
    ("hb_ext_w",         "Hotel headboard side extension (in):",22.0,   0.0,  48.0, False),
    ("wing_depth",       "Wingback side cheek depth (in):",     12.0,   4.0,  28.0, False),
    ("canopy_h",         "Four-poster canopy height (in):",     84.0,  64.0, 110.0, False),
    ("post_w",           "Canopy post thickness (in):",          2.2,   1.0,   6.0, False),
    ("hb_channels",      "Headboard vertical channels:",         8,     2,    24,   True),
    ("hb_rows",          "Headboard horizontal rows:",           2,     1,     8,   True),
    # Bedding & Accessories
    ("duvet_cov_pct",    "Duvet coverage (% of bed length):",   72.0,  35.0,  92.0, False),
    ("duvet_drape",      "Duvet side overhang drop (in):",       5.5,   1.0,  14.0, False),
    ("ns_w",             "Nightstand width (in):",              20.0,  12.0,  36.0, False),
    ("ns_d",             "Nightstand depth (in):",              16.0,  10.0,  28.0, False),
    ("ns_h",             "Nightstand top height (in):",         22.0,  12.0,  34.0, False),
    ("bench_d",          "End-of-bed bench depth (in):",        18.0,  12.0,  30.0, False),
    ("bench_h",          "End-of-bed bench height (in):",       17.5,  12.0,  24.0, False),
]

DD_FIELDS = [
    ("bed_type",         "Bed typology / style:",        0, BED_TYPE_NAMES),
    ("size_preset",      "Mattress size preset:",        0, SIZE_PRESET_NAMES),
    ("hb_style",         "Headboard design style:",      0, HEADBOARD_STYLE_NAMES),
    ("base_style",       "Base & leg support:",          0, BASE_STYLE_NAMES),
    ("pillow_layout",    "Pillow arrangement:",          0, PILLOW_LAYOUT_NAMES),
    ("bedding_style",    "Bedding & duvet style:",       0, BEDDING_STYLE_NAMES),
    ("accessory_opt",    "Suite nightstands & bench:",   0, ACCESSORY_OPT_NAMES),
    ("sheet_finish",     "Mattress & sheet fabric:",     0, SHEET_NAMES),
    ("duvet_finish",     "Duvet & throw fabric:",        0, DUVET_NAMES),
    ("hb_finish",        "Headboard upholstery:",        0, HEADBOARD_NAMES),
    ("wood_finish",      "Platform & timber finish:",    0, WOOD_NAMES),
    ("metal_finish",     "Canopy & hardware finish:",    0, METAL_NAMES),
]

TAB_LAYOUT = [
    ("1. Bed Type && Size", [
        "bed_type",
        "size_preset",
        "base_style",
        "leg_h",
        "rail_h",
        "side_margin",
        "foot_margin",
        "mattress_h",
        "mattress_inset",
        "edge_rad",
    ]),
    ("2. Headboard, Bedding && Suite", [
        "hb_style",
        "hb_h",
        "hb_thick",
        "hb_ext_w",
        "wing_depth",
        "canopy_h",
        "post_w",
        "hb_channels",
        "hb_rows",
        "pillow_layout",
        "bedding_style",
        "duvet_cov_pct",
        "duvet_drape",
        "accessory_opt",
        "ns_w",
        "ns_d",
        "ns_h",
        "bench_d",
        "bench_h",
    ]),
    ("3. Materials && Finishes", [
        "sheet_finish",
        "duvet_finish",
        "hb_finish",
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


def encode_state(center_in, width_vec, length_vec, width_in, length_in, settings):
    state = {
        "version": 1,
        "frame": {
            "center": _point_to_data(center_in),
            "width_vec": _vector_to_data(width_vec),
            "length_vec": _vector_to_data(length_vec),
            "width_in": float(width_in),
            "length_in": float(length_in),
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
        length_vec = _safe_unitize(_vector_from_data(frame["length_vec"]), rg.Vector3d.YAxis)
        width_in = float(frame["width_in"])
        length_in = float(frame["length_in"])
        settings = normalize_settings(state.get("settings", {}))
        return center_in, width_vec, length_vec, width_in, length_in, settings
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


def transform_frame_from_current_objects(doc, center_doc, width_vec, length_vec, target_ids):
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
        return center_doc, width_vec, length_vec

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
    new_l = _safe_unitize(rg.Vector3d(ca * length_vec.X - sa * length_vec.Y, sa * length_vec.X + ca * length_vec.Y, length_vec.Z), length_vec)
    return new_center, new_w, new_l


# ============================================================
# 3D BED GEOMETRY PRIMITIVES (LOCAL INCH COORDINATES)
# ============================================================
# Local Bed Coordinate System:
#   X = Width  (-W/2 to +W/2, Left to Right along headboard wall)
#   Y = Length (-L/2 = Headboard wall, +L/2 = Foot of bed, +Y = Forward direction)
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


def make_soft_rounded_box_yz(x1, x2, y1, y2, z1, z2, rad, fast, tol):
    """Creates a box filleted in the Y-Z profile plane and extruded along X (ideal for pillows, cushions, duvets)."""
    w = x2 - x1
    d = y2 - y1
    h = z2 - z1
    if w < 0.2 or d < 0.2 or h < 0.2:
        return None
    r = clamp(rad, 0.0, min(w, d, h) * 0.42)
    if fast or r < 0.15:
        return mk_box(x1, x2, y1, y2, z1, z2)
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


def make_soft_rounded_box_xz(x1, x2, y1, y2, z1, z2, rad, fast, tol):
    """Creates a box filleted in the X-Z profile plane and extruded along Y (ideal for draped blankets & headboards)."""
    w = x2 - x1
    d = y2 - y1
    h = z2 - z1
    if w < 0.2 or d < 0.2 or h < 0.2:
        return None
    r = clamp(rad, 0.0, min(w, d, h) * 0.42)
    if fast or r < 0.15:
        return mk_box(x1, x2, y1, y2, z1, z2)
    try:
        pl_xz = rg.Plane(rg.Point3d(x1, y1, z1), rg.Vector3d.XAxis, rg.Vector3d.ZAxis)
        rect = rg.Rectangle3d(pl_xz, rg.Interval(0.0, w), rg.Interval(0.0, h)).ToNurbsCurve()
        filleted = rg.Curve.CreateFilletCornersCurve(rect, r, 1e-3, 1e-3)
        prof = filleted if (filleted and filleted.IsClosed) else rect
        srf = rg.Surface.CreateExtrusion(prof, rg.Vector3d(0.0, d, 0.0))
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
    if w < 0.2 or d < 0.2 or h < 0.2:
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


def make_draped_duvet_brep(mx0, mx1, y0, y1, z_mat_top, drape_drop, LoftThick, rad, fast, tol):
    """
    Creates an architectural draped duvet / comforter or bed runner that wraps smoothly over the
    top of the mattress and drapes down both left and right sides by `drape_drop`.
    """
    if (mx1 - mx0) < 4.0 or (y1 - y0) < 2.0:
        return None
    if fast:
        return mk_box(mx0 - LoftThick, mx1 + LoftThick, y0, y1, z_mat_top - drape_drop * 0.5, z_mat_top + LoftThick)

    # Build a closed U-shaped inverted saddle cross-section in the X-Z plane at y = y0 and extrude along +Y to y1
    t = max(0.6, LoftThick)
    dr = max(1.0, drape_drop)
    ox0 = mx0 - t
    ox1 = mx1 + t
    z_top = z_mat_top + t
    z_bot = z_mat_top - dr

    pts_outer = [
        rg.Point3d(ox0, y0, z_bot),
        rg.Point3d(ox0, y0, z_top),
        rg.Point3d(ox1, y0, z_top),
        rg.Point3d(ox1, y0, z_bot),
        rg.Point3d(mx1, y0, z_bot),
        rg.Point3d(mx1, y0, z_mat_top),
        rg.Point3d(mx0, y0, z_mat_top),
        rg.Point3d(mx0, y0, z_bot),
        rg.Point3d(ox0, y0, z_bot),
    ]
    poly_crv = rg.Polyline(pts_outer).ToNurbsCurve()
    r_fil = min(rad, t * 0.75, dr * 0.35)
    if r_fil > 0.15:
        fil = rg.Curve.CreateFilletCornersCurve(poly_crv, r_fil, 1e-3, 1e-3)
        if fil and fil.IsClosed:
            poly_crv = fil

    srf = rg.Surface.CreateExtrusion(poly_crv, rg.Vector3d(0.0, y1 - y0, 0.0))
    if srf:
        b = srf.ToBrep()
        if b:
            capped = b.CapPlanarHoles(max(tol, 0.01))
            res = capped if capped else b
            if res.SolidOrientation == rg.BrepSolidOrientation.Inward:
                res.Flip()
            return res
    return mk_box(ox0, ox1, y0, y1, z_mat_top, z_top)


# ============================================================
# HEADBOARD, CANOPY, PILLOWS & ACCESSORIES BUILDERS
# ============================================================
def build_headboard_assembly(x0, x1, y_hb_back, hb_t, z_bot, z_top, S, fast, tol):
    """
    Builds the headboard assembly according to S['hb_style']:
      0: Vertical Channel-Tufted Upholstered
      1: Horizontal Panel / Biscuit Grid Tufted
      2: Split Dual-Cushion Padded Headboard
      3: Smooth Architectural Slab / Solid Wood
      4: Timber Frame with Recessed Cane / Fabric Inlay
    """
    parts = []
    hb_style = int(S["hb_style"])
    rad = float(S["edge_rad"])
    y_hb_front = y_hb_back + hb_t
    w_tot = x1 - x0
    h_tot = z_top - z_bot
    if w_tot < 6.0 or h_tot < 4.0 or hb_t < 0.5:
        return parts

    # Structural backing board
    back_board_t = min(1.2, hb_t * 0.35)
    if hb_style in (0, 1, 2):
        bb = mk_box(x0, x1, y_hb_back, y_hb_back + back_board_t, z_bot, z_top)
        if bb:
            parts.append(("headboard", bb))

    y_pad0 = y_hb_back + back_board_t
    y_pad1 = y_hb_front

    if hb_style == 0 and not fast:
        # 0. Vertical Channel-Tufted Upholstered
        n_ch = max(2, int(S["hb_channels"]))
        cw = w_tot / float(n_ch)
        for i in range(n_ch):
            cx0 = x0 + i * cw + 0.06
            cx1 = x0 + (i + 1) * cw - 0.06
            cb = make_soft_rounded_box_xz(cx0, cx1, y_pad0, y_pad1, z_bot, z_top, min(rad, cw * 0.42), False, tol)
            if cb:
                parts.append(("headboard", cb))

    elif hb_style == 1 and not fast:
        # 1. Horizontal Panel / Biscuit Grid Tufted
        n_cols = max(1, int(S["hb_channels"]) // 2)
        n_rows = max(2, int(S["hb_rows"]))
        cw = w_tot / float(n_cols)
        rh = h_tot / float(n_rows)
        for r_i in range(n_rows):
            rz0 = z_bot + r_i * rh + 0.08
            rz1 = z_bot + (r_i + 1) * rh - 0.08
            for c_i in range(n_cols):
                cx0 = x0 + c_i * cw + 0.08
                cx1 = x0 + (c_i + 1) * cw - 0.08
                pb = make_soft_rounded_box_yz(cx0, cx1, y_pad0, y_pad1, rz0, rz1, min(rad, rh * 0.35), False, tol)
                if pb:
                    parts.append(("headboard", pb))

    elif hb_style == 2:
        # 2. Split Dual-Cushion Padded Headboard
        n_pads = 1 if w_tot < 46.0 else 2
        pw = (w_tot - 2.0) / float(n_pads)
        for i in range(n_pads):
            px0 = x0 + 1.0 + i * pw + 0.3
            px1 = px0 + pw - 0.6
            pad = make_soft_rounded_box_yz(px0, px1, y_pad0, y_pad1 + 1.0, z_bot + 2.0, z_top - 1.0, rad, fast, tol)
            if pad:
                parts.append(("headboard", pad))

    elif hb_style == 3:
        # 3. Smooth Architectural Slab / Solid Wood
        kind = "wood" if S["hb_finish"] == len(HEADBOARD_FINISHES) - 1 else "headboard"
        slab = make_plan_rounded_box(x0, x1, y_hb_back, y_hb_front, z_bot, z_top, min(rad * 0.6, 1.0), fast, tol)
        if slab:
            parts.append((kind, slab))

    elif hb_style == 4:
        # 4. Timber Perimeter Frame + Recessed Cane / Fabric Inlay
        fw = min(3.2, w_tot * 0.08, h_tot * 0.12)
        # Outer timber frame rails & stiles
        parts.append(("wood", mk_box(x0, x0 + fw, y_hb_back, y_hb_front, z_bot, z_top)))
        parts.append(("wood", mk_box(x1 - fw, x1, y_hb_back, y_hb_front, z_bot, z_top)))
        parts.append(("wood", mk_box(x0 + fw, x1 - fw, y_hb_back, y_hb_front, z_bot, z_bot + fw)))
        parts.append(("wood", mk_box(x0 + fw, x1 - fw, y_hb_back, y_hb_front, z_top - fw, z_top)))
        # Recessed inlay panel
        inlay_t = hb_t * 0.5
        yc = 0.5 * (y_hb_back + y_hb_front)
        inlay = mk_box(x0 + fw, x1 - fw, yc - inlay_t * 0.5, yc + inlay_t * 0.5, z_bot + fw, z_top - fw)
        if inlay:
            parts.append(("headboard", inlay))

    else:
        slab = make_plan_rounded_box(x0, x1, y_hb_back, y_hb_front, z_bot, z_top, 0.8, fast, tol)
        if slab:
            parts.append(("headboard", slab))

    return parts


def build_pillows_and_bedding(mx0, mx1, my0, my1, z_mat_bot, z_mat_top, S, fast, tol):
    """Builds the Mattress, Fitted Sheet, Duvet Comforter, Foot Runner Throw, and Pillow Stack."""
    parts = []
    rad = float(S["edge_rad"])
    mw = mx1 - mx0
    ml = my1 - my0

    # 1. Mattress with soft bullnose top/bottom edges
    mat_brep = make_plan_rounded_box(mx0, mx1, my0, my1, z_mat_bot, z_mat_top, min(rad * 1.4, 3.0), fast, tol)
    if mat_brep:
        parts.append(("mattress", mat_brep))

    # Subtle mattress plush topper layer
    if not fast and (z_mat_top - z_mat_bot) > 6.0:
        topper = make_soft_rounded_box_yz(mx0 + 0.3, mx1 - 0.3, my0 + 0.3, my1 - 0.3, z_mat_top - 2.2, z_mat_top + 0.4, rad, False, tol)
        if topper:
            parts.append(("mattress", topper))

    # 2. Duvet Comforter & Foot Runner Throw
    bedding_style = int(S["bedding_style"])
    cov_pct = clamp(float(S["duvet_cov_pct"]), 35.0, 92.0) / 100.0
    drape = clamp(float(S["duvet_drape"]), 1.0, 14.0)

    if bedding_style in (0, 1):
        y_duvet_start = my1 - ml * cov_pct
        duvet_t = 2.2
        duvet_b = make_draped_duvet_brep(mx0, mx1, y_duvet_start, my1 + 1.2, z_mat_top + 0.3, drape, duvet_t, rad, fast, tol)
        if duvet_b:
            parts.append(("duvet", duvet_b))

        # Folded top collar turn-down of duvet
        if bedding_style == 0:
            fold_len = min(11.0, ml * 0.14)
            fold_b = make_draped_duvet_brep(
                mx0 - 0.2, mx1 + 0.2, y_duvet_start, y_duvet_start + fold_len,
                z_mat_top + duvet_t + 0.2, drape * 0.6, 1.4, rad * 0.8, fast, tol
            )
            if fold_b:
                parts.append(("mattress", fold_b))

            # Foot-of-bed decorative runner throw blanket
            run_len = min(20.0, ml * 0.24)
            run_y1 = my1 - 2.0
            run_y0 = run_y1 - run_len
            runner_b = make_draped_duvet_brep(
                mx0 - 0.3, mx1 + 0.3, run_y0, run_y1,
                z_mat_top + duvet_t + 0.3, drape + 1.2, 0.9, rad * 0.7, fast, tol
            )
            if runner_b:
                parts.append(("pillow", runner_b))

    # 3. Pillow Arrangement (Single column for Twin/Narrow beds, Dual columns for Double/Queen/King)
    p_layout = int(S["pillow_layout"])
    if p_layout == 4:
        return parts

    n_cols = 1 if mw < 46.0 else 2
    col_margin = 2.2
    avail_w = mw - 2.0 * col_margin
    col_w = avail_w / float(n_cols)
    pil_w = min(28.0, col_w - 1.5)

    for c_i in range(n_cols):
        cx = mx0 + col_margin + (c_i + 0.5) * col_w
        px0 = cx - pil_w * 0.5
        px1 = cx + pil_w * 0.5

        if p_layout == 0:
            # 0. Full Luxury Stack: Upright Euro Sham + Reclined Sleeping Pillow + Front Lumbar Cushion
            # A. Upright Euro Sham against headboard
            euro_w = min(24.0, pil_w * 0.9)
            euro_b = make_soft_rounded_box_yz(
                cx - euro_w * 0.5, cx + euro_w * 0.5,
                my0 + 1.0, my0 + 5.5,
                z_mat_top, z_mat_top + 18.0,
                rad, fast, tol
            )
            if euro_b:
                euro_b.Rotate(math.radians(8.0), rg.Vector3d.XAxis, rg.Point3d(cx, my0 + 5.5, z_mat_top))
                parts.append(("pillow", euro_b))

            # B. Reclined Sleeping Pillow in front of Euro Sham
            slp_b = make_soft_rounded_box_yz(
                px0, px1, my0 + 5.8, my0 + 15.5, z_mat_top, z_mat_top + 6.5, rad, fast, tol
            )
            if slp_b:
                slp_b.Rotate(math.radians(18.0), rg.Vector3d.XAxis, rg.Point3d(cx, my0 + 15.5, z_mat_top))
                parts.append(("mattress", slp_b))

            # C. Front Decorative Accent Lumbar Pillow
            lum_w = pil_w * 0.68
            lum_b = make_soft_rounded_box_yz(
                cx - lum_w * 0.5, cx + lum_w * 0.5,
                my0 + 14.5, my0 + 19.5,
                z_mat_top, z_mat_top + 8.5,
                rad * 0.8, fast, tol
            )
            if lum_b:
                lum_b.Rotate(math.radians(15.0), rg.Vector3d.XAxis, rg.Point3d(cx, my0 + 19.5, z_mat_top))
                parts.append(("pillow", lum_b))

        elif p_layout == 1:
            # 1. Standard Double Stack (Bottom Flat Pillow + Top Angled Pillow)
            p_bot = make_soft_rounded_box_yz(px0, px1, my0 + 1.5, my0 + 14.5, z_mat_top, z_mat_top + 4.5, rad, fast, tol)
            p_top = make_soft_rounded_box_yz(px0 + 0.5, px1 - 0.5, my0 + 2.5, my0 + 15.5, z_mat_top + 4.2, z_mat_top + 8.8, rad, fast, tol)
            if p_bot:
                parts.append(("mattress", p_bot))
            if p_top:
                p_top.Rotate(math.radians(8.0), rg.Vector3d.XAxis, rg.Point3d(cx, my0 + 15.5, z_mat_top + 4.2))
                parts.append(("pillow", p_top))

        elif p_layout == 2:
            # 2. Minimalist Single Row
            p_single = make_soft_rounded_box_yz(px0, px1, my0 + 2.0, my0 + 15.0, z_mat_top, z_mat_top + 5.2, rad, fast, tol)
            if p_single:
                parts.append(("mattress", p_single))

        elif p_layout == 3:
            # 3. Cylindrical Bolster + Sleeping Pillow
            p_slp = make_soft_rounded_box_yz(px0, px1, my0 + 1.5, my0 + 13.5, z_mat_top, z_mat_top + 4.8, rad, fast, tol)
            if p_slp:
                parts.append(("mattress", p_slp))
            bol_r = 3.6
            bol = make_cyl(
                rg.Point3d(px0 + 1.5, my0 + 15.5, z_mat_top + bol_r),
                rg.Point3d(px1 - 1.5, my0 + 15.5, z_mat_top + bol_r),
                bol_r
            )
            if bol:
                parts.append(("pillow", bol))

    return parts


# ============================================================
# MAIN BED SYSTEM BUILDER (ALL 8 TYPOLOGIES)
# ============================================================
def build_bed_system(center_in, width_vec, length_vec, footprint_w_in, footprint_l_in, S, final=True, u=1.0):
    """
    Builds the complete 3D Bed & Suite Assembly in local inch coordinates and transforms to world space.
    Returns: (parts_list, preview_curves, info_dict)
    where parts_list = [(kind, brep), ...] with kind in ('mattress', 'duvet', 'pillow', 'headboard', 'wood', 'metal').
    """
    tol = get_tolerance()
    fast = (not final) and bool(S["fast_preview"])

    bed_type = int(S["bed_type"])
    size_preset = int(S["size_preset"])
    base_style = int(S["base_style"])
    acc_opt = int(S["accessory_opt"])

    side_m = float(S["side_margin"])
    foot_m = float(S["foot_margin"])
    hb_t   = float(S["hb_thick"])
    hb_h   = float(S["hb_h"])
    leg_h  = float(S["leg_h"])
    rail_h = float(S["rail_h"])
    mat_h  = float(S["mattress_h"])
    mat_in = clamp(float(S["mattress_inset"]), 0.0, rail_h - 1.0)
    rad    = float(S["edge_rad"])

    # Typology-specific refinements
    if bed_type == 1:
        # 1. Floating Cantilever Bed (deeply recessed dark plinth)
        base_style = 0
        leg_h = max(leg_h, 5.5)
    elif bed_type == 5:
        # 5. Japanese Low-Profile Tatami Platform Bed (wide timber deck, low floor clearance)
        leg_h = min(leg_h, 2.0)
        rail_h = min(rail_h, 4.5)
        side_m = max(side_m, 7.0)
        foot_m = max(foot_m, 7.0)

    # Resolve Mattress & Outer Frame Dimensions
    if size_preset in MATTRESS_PRESET_DIMS:
        mat_w, mat_l = MATTRESS_PRESET_DIMS[size_preset]
        frame_w = mat_w + 2.0 * side_m
        frame_l = hb_t + mat_l + foot_m
    else:
        frame_w = max(36.0, float(footprint_w_in))
        frame_l = max(60.0, float(footprint_l_in))
        mat_w = max(28.0, frame_w - 2.0 * side_m)
        mat_l = max(48.0, frame_l - hb_t - foot_m)

    z_rail_bot = leg_h if base_style != 3 else 0.0
    z_rail_top = leg_h + rail_h
    z_mat_bot  = z_rail_top - mat_in
    z_mat_top  = z_mat_bot + mat_h

    fx0, fx1 = -frame_w * 0.5, frame_w * 0.5
    fy0, fy1 = -frame_l * 0.5, frame_l * 0.5

    mx0, mx1 = -mat_w * 0.5, mat_w * 0.5
    my0 = fy0 + hb_t
    my1 = my0 + mat_l

    local_parts = []
    local_curves = []

    # --------------------------------------------------------
    # 1. PLATFORM FRAME DECK & BASE / LEGS
    # --------------------------------------------------------
    deck_box = make_plan_rounded_box(fx0, fx1, my0 - 0.5, fy1, z_rail_bot, z_rail_top, min(rad * 0.6, 1.2), fast, tol)
    if deck_box:
        local_parts.append(("wood", deck_box))

    if z_rail_bot > 0.25:
        inset = 9.0 if bed_type == 1 else 3.5
        lx0, lx1 = fx0 + inset, fx1 - inset
        ly0, ly1 = my0 + inset, fy1 - inset

        if base_style == 0:
            # Recessed Floating Plinth Base
            plinth = make_plan_rounded_box(lx0, lx1, ly0, ly1, 0.0, z_rail_bot + 0.2, 0.8, fast, tol)
            if plinth:
                local_parts.append(("wood", plinth))
        elif base_style == 1:
            # Tapered Mid-Century Timber Legs
            splay = min(1.5, z_rail_bot * 0.22)
            for xp, sx in ((lx0, -splay), (lx1, splay)):
                for yp, sy in ((ly0, -splay * 0.5), (ly1, splay * 0.5)):
                    leg = make_tapered_leg(rg.Point3d(xp, yp, z_rail_bot + 0.2), rg.Point3d(xp + sx, yp + sy, 0.0), 1.2, 0.65, tol)
                    if leg:
                        local_parts.append(("wood", leg))
        elif base_style == 2:
            # Cylindrical Metal Stiletto Legs
            for xp in (lx0, lx1):
                for yp in (ly0, ly1):
                    leg = make_cyl(rg.Point3d(xp, yp, 0.0), rg.Point3d(xp, yp, z_rail_bot + 0.2), 0.75)
                    if leg:
                        local_parts.append(("metal", leg))
        elif base_style == 4:
            # Sled / Cantilever Runner Bar Base
            bw, bt = 1.6, 0.6
            for xp in (lx0, lx1):
                local_parts.append(("metal", mk_box(xp - bt * 0.5, xp + bt * 0.5, ly0, ly0 + bw, 0.0, z_rail_bot + 0.2)))
                local_parts.append(("metal", mk_box(xp - bt * 0.5, xp + bt * 0.5, ly1 - bw, ly1, 0.0, z_rail_bot + 0.2)))
                local_parts.append(("metal", mk_box(xp - bt * 0.5, xp + bt * 0.5, ly0, ly1, 0.0, bt)))

    # --------------------------------------------------------
    # 2. HEADBOARD, WINGBACK, CANOPY OR SLEIGH FOOTBOARD
    # --------------------------------------------------------
    hb_x0, hb_x1 = fx0, fx1
    if bed_type == 3:
        # Type 3: Extended Wall-Panel Hotel Suite Bed
        ext_w = max(12.0, float(S["hb_ext_w"]))
        hb_x0 -= ext_w
        hb_x1 += ext_w

    if bed_type == 7:
        # Type 7: Minimalist Daybed / Divan (low backrest + two side bolster arms)
        arm_h = z_mat_top + 6.0
        local_parts.extend(build_headboard_assembly(fx0, fx1, fy0, hb_t, z_rail_bot, arm_h + 4.0, S, fast, tol))
        side_t = max(3.5, side_m)
        arm_l = make_soft_rounded_box_yz(fx0, fx0 + side_t, my0, fy1, z_rail_bot, arm_h, rad, fast, tol)
        arm_r = make_soft_rounded_box_yz(fx1 - side_t, fx1, my0, fy1, z_rail_bot, arm_h, rad, fast, tol)
        if arm_l:
            local_parts.append(("headboard", arm_l))
        if arm_r:
            local_parts.append(("headboard", arm_r))
    else:
        z_hb_bot = 0.0 if bed_type in (2, 3, 6) else z_rail_bot
        local_parts.extend(build_headboard_assembly(hb_x0, hb_x1, fy0, hb_t, z_hb_bot, hb_h, S, fast, tol))

    # Type 2: Upholstered Wingback Side Cheeks
    if bed_type == 2:
        wing_d = clamp(float(S["wing_depth"]), 4.0, mat_l * 0.4)
        wing_t = min(3.5, hb_t * 0.8)
        w_left  = make_soft_rounded_box_yz(fx0 - wing_t * 0.5, fx0 + wing_t * 0.5, fy0, fy0 + hb_t + wing_d, 0.0, hb_h, rad, fast, tol)
        w_right = make_soft_rounded_box_yz(fx1 - wing_t * 0.5, fx1 + wing_t * 0.5, fy0, fy0 + hb_t + wing_d, 0.0, hb_h, rad, fast, tol)
        if w_left:
            local_parts.append(("headboard", w_left))
        if w_right:
            local_parts.append(("headboard", w_right))

    # Type 4: Architectural Four-Poster Canopy Frame
    if bed_type == 4:
        can_h = max(hb_h + 16.0, float(S["canopy_h"]))
        pw = clamp(float(S["post_w"]), 1.0, 6.0)
        can_kind = "wood" if int(S["base_style"]) == 1 else "metal"
        # 4 Vertical corner posts
        post_coords = [
            (fx0, fy0),
            (fx1 - pw, fy0),
            (fx0, fy1 - pw),
            (fx1 - pw, fy1 - pw),
        ]
        for px, py in post_coords:
            pb = mk_box(px, px + pw, py, py + pw, 0.0, can_h)
            if pb:
                local_parts.append((can_kind, pb))
        # Upper perimeter canopy rails
        r_top0 = can_h - pw
        local_parts.append((can_kind, mk_box(fx0 + pw, fx1 - pw, fy0, fy0 + pw, r_top0, can_h)))
        local_parts.append((can_kind, mk_box(fx0 + pw, fx1 - pw, fy1 - pw, fy1, r_top0, can_h)))
        local_parts.append((can_kind, mk_box(fx0, fx0 + pw, fy0 + pw, fy1 - pw, r_top0, can_h)))
        local_parts.append((can_kind, mk_box(fx1 - pw, fx1, fy0 + pw, fy1 - pw, r_top0, can_h)))

    # Type 6: Upholstered Footboard Sleigh Bed
    if bed_type == 6:
        fb_h = z_mat_top + 4.5
        fb_t = max(3.0, foot_m)
        fb = make_soft_rounded_box_xz(fx0, fx1, fy1 - fb_t, fy1 + 1.0, z_rail_bot, fb_h, rad, fast, tol)
        if fb:
            local_parts.append(("headboard", fb))

    # --------------------------------------------------------
    # 3. MATTRESS, DUVET, RUNNER & PILLOW STACK
    # --------------------------------------------------------
    local_parts.extend(build_pillows_and_bedding(mx0, mx1, my0, my1, z_mat_bot, z_mat_top, S, fast, tol))

    # --------------------------------------------------------
    # 4. SUITE ACCESSORIES (NIGHTSTANDS & END-OF-BED BENCH)
    # --------------------------------------------------------
    has_floating_ns = (acc_opt == 1) or (bed_type == 3 and acc_opt == 0)
    has_box_ns      = acc_opt in (2, 4)
    has_end_bench   = acc_opt in (3, 4)

    ns_w = float(S["ns_w"])
    ns_d = float(S["ns_d"])
    ns_h = float(S["ns_h"])
    ns_gap = 2.0

    if has_floating_ns or has_box_ns:
        z_ns_bot = (ns_h - 6.5) if has_floating_ns else 0.0
        for sign_x in (-1.0, 1.0):
            if sign_x < 0:
                nx1 = fx0 - ns_gap
                nx0 = nx1 - ns_w
            else:
                nx0 = fx1 + ns_gap
                nx1 = nx0 + ns_w
            ny0 = my0
            ny1 = ny0 + ns_d
            ns_body = make_plan_rounded_box(nx0, nx1, ny0, ny1, z_ns_bot, ns_h, 0.6, fast, tol)
            if ns_body:
                local_parts.append(("wood", ns_body))
            # Drawer handle bar
            hw_y = ny1 + 0.4
            hw_z = ns_h - 2.5
            hw_bar = mk_box(0.5 * (nx0 + nx1) - 3.0, 0.5 * (nx0 + nx1) + 3.0, ny1, hw_y, hw_z - 0.2, hw_z + 0.2)
            if hw_bar:
                local_parts.append(("metal", hw_bar))

    if has_end_bench:
        bench_d = float(S["bench_d"])
        bench_h = float(S["bench_h"])
        bench_w = mat_w * 0.82
        by0 = fy1 + 4.0
        by1 = by0 + bench_d
        bx0, bx1 = -bench_w * 0.5, bench_w * 0.5
        b_cush_t = 5.0
        z_b_frame = bench_h - b_cush_t
        # Bench cushion
        bc = make_soft_rounded_box_yz(bx0, bx1, by0, by1, z_b_frame, bench_h, rad, fast, tol)
        if bc:
            local_parts.append(("headboard", bc))
        # Bench timber base & legs
        b_rail = mk_box(bx0 + 0.5, bx1 - 0.5, by0 + 0.5, by1 - 0.5, z_b_frame - 2.0, z_b_frame)
        if b_rail:
            local_parts.append(("wood", b_rail))
        for lx in (bx0 + 2.5, bx1 - 2.5):
            for ly in (by0 + 2.5, by1 - 2.5):
                bl = make_tapered_leg(rg.Point3d(lx, ly, z_b_frame - 1.8), rg.Point3d(lx, ly, 0.0), 0.95, 0.55, tol)
                if bl:
                    local_parts.append(("wood", bl))

    # --------------------------------------------------------
    # 5. TRANSFORM FROM LOCAL INCH FRAME -> WORLD DOCUMENT SPACE
    # --------------------------------------------------------
    flip_sign = -1.0 if bool(S.get("flip_facing", False)) else 1.0
    w_dir = _safe_unitize(width_vec * flip_sign, rg.Vector3d.XAxis)
    l_dir = _safe_unitize(length_vec * flip_sign, rg.Vector3d.YAxis)

    # Foot direction indicator arrow
    arrow_pts = [
        rg.Point3d(-3.5, fy1 + 2.0, 0.2),
        rg.Point3d( 3.5, fy1 + 2.0, 0.2),
        rg.Point3d( 0.0, fy1 + 9.0, 0.2),
        rg.Point3d(-3.5, fy1 + 2.0, 0.2),
    ]
    local_curves.append(rg.Polyline(arrow_pts).ToNurbsCurve())

    target_plane_in = rg.Plane(center_in, w_dir, l_dir)
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
        "frame_w_in": frame_w,
        "frame_l_in": frame_l,
        "mat_w_in": mat_w,
        "mat_l_in": mat_l,
        "hb_h_in": hb_h,
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


def bake_bed(doc, center_in, width_vec, length_vec, width_in, length_in, S, u=1.0, edit_target_ids=None):
    parts, _, _ = build_bed_system(center_in, width_vec, length_vec, width_in, length_in, S, True, u)

    sh_name, sh_rgb = SHEET_FINISHES[S["sheet_finish"]]
    dv_name, dv_rgb = DUVET_FINISHES[S["duvet_finish"]]
    hb_name, hb_rgb = HEADBOARD_FINISHES[S["hb_finish"]]
    wd_name, wd_rgb = WOOD_FINISHES[S["wood_finish"]]
    mt_name, mt_rgb = METAL_FINISHES[S["metal_finish"]]

    if S["hb_finish"] == len(HEADBOARD_FINISHES) - 1:
        hb_name, hb_rgb = wd_name, wd_rgb

    colors = {
        "mattress":  rgb_to_color(sh_rgb),
        "duvet":     rgb_to_color(dv_rgb),
        "pillow":    rgb_to_color(dv_rgb),
        "headboard": rgb_to_color(hb_rgb),
        "wood":      rgb_to_color(wd_rgb),
        "metal":     rgb_to_color(mt_rgb),
    }

    main_layer_idx = get_or_create_layer(doc, "BED")
    parent_id = doc.Layers[main_layer_idx].Id

    layers = {
        "mattress":  get_or_create_layer_with_material(doc, "MATTRESS_SHEET", parent_id, colors["mattress"], "Bed Sheet " + sh_name, colors["mattress"]),
        "duvet":     get_or_create_layer_with_material(doc, "DUVET_BEDDING", parent_id, colors["duvet"], "Bed Duvet " + dv_name, colors["duvet"]),
        "pillow":    get_or_create_layer_with_material(doc, "PILLOWS", parent_id, colors["pillow"], "Bed Pillow " + dv_name, colors["pillow"]),
        "headboard": get_or_create_layer_with_material(doc, "HEADBOARD", parent_id, colors["headboard"], "Bed Headboard " + hb_name, colors["headboard"]),
        "wood":      get_or_create_layer_with_material(doc, "FRAME_WOOD", parent_id, colors["wood"], "Bed Wood " + wd_name, colors["wood"]),
        "metal":     get_or_create_layer_with_material(doc, "METAL_HARDWARE", parent_id, colors["metal"], "Bed Metal " + mt_name, colors["metal"]),
    }

    if edit_target_ids:
        for gid in edit_target_ids:
            try:
                doc.Objects.Delete(gid, True)
            except Exception:
                pass

    state_json = encode_state(center_in, width_vec, length_vec, width_in, length_in, S)
    ids = []
    for idx, (kind, brep) in enumerate(parts):
        if not brep or not brep.IsValid:
            continue
        c_pt = _brep_center(brep)
        attr = make_attributes(layers.get(kind, layers["mattress"]), "Bed_" + kind, state_json, idx, c_pt)
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
class BedPreviewConduit(rd.DisplayConduit):
    def __init__(self, wireframe_only=False):
        super(BedPreviewConduit, self).__init__()
        self.preview_breps = []
        self.preview_curves = []
        self.wireframe_only = wireframe_only
        self.materials = {}
        self.set_finishes(default_settings())

    def set_finishes(self, S):
        sh_rgb = SHEET_FINISHES[S["sheet_finish"]][1]
        dv_rgb = DUVET_FINISHES[S["duvet_finish"]][1]
        hb_rgb = HEADBOARD_FINISHES[S["hb_finish"]][1]
        wd_rgb = WOOD_FINISHES[S["wood_finish"]][1]
        mt_rgb = METAL_FINISHES[S["metal_finish"]][1]
        if S["hb_finish"] == len(HEADBOARD_FINISHES) - 1:
            hb_rgb = wd_rgb
        self.materials = {
            "mattress":  rd.DisplayMaterial(rgb_to_color(sh_rgb)),
            "duvet":     rd.DisplayMaterial(rgb_to_color(dv_rgb)),
            "pillow":    rd.DisplayMaterial(rgb_to_color(dv_rgb)),
            "headboard": rd.DisplayMaterial(rgb_to_color(hb_rgb)),
            "wood":      rd.DisplayMaterial(rgb_to_color(wd_rgb)),
            "metal":     rd.DisplayMaterial(rgb_to_color(mt_rgb)),
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
                    col = System.Drawing.Color.DeepSkyBlue if kind in ("mattress", "duvet", "pillow") else System.Drawing.Color.Gold
                    e.Display.DrawBrepWires(brep, col, 1)
                else:
                    mat = self.materials.get(kind, self.materials["mattress"])
                    if mat:
                        e.Display.DrawBrepShaded(brep, mat)
                    e.Display.DrawBrepWires(brep, System.Drawing.Color.FromArgb(45, 45, 50), 1)
            for crv in self.preview_curves:
                if crv and crv.IsValid:
                    e.Display.DrawCurve(crv, System.Drawing.Color.Gold, 2)
        except Exception:
            pass


class BedWidthPointGetter(ric.GetPoint):
    """Live 3D bed wireframe preview while picking the second point (headboard width & direction)."""
    def __init__(self, p0, settings, u, default_len_in=DEFAULT_BED_LENGTH_IN):
        super(BedWidthPointGetter, self).__init__()
        self.p0 = rg.Point3d(p0)
        self.u = u if u > 0 else 1.0
        self.default_len_in = default_len_in
        self.S = dict(settings)
        self.S["fast_preview"] = True
        self.S["size_preset"] = 0

    def OnDynamicDraw(self, e):
        try:
            pt = e.CurrentPoint
            base_z = self.p0.Z
            a = rg.Point3d(self.p0.X, self.p0.Y, base_z)
            b = rg.Point3d(pt.X, pt.Y, base_z)
            v = b - a
            v.Z = 0.0
            w_in = v.Length / self.u
            if w_in < 36.0:
                e.Display.DrawLine(a, b, System.Drawing.Color.Gold, 2)
                return

            w_vec = _safe_unitize(v, rg.Vector3d.XAxis)
            l_vec = _safe_unitize(rg.Vector3d.CrossProduct(rg.Vector3d.ZAxis, w_vec), rg.Vector3d.YAxis)
            mid_head = 0.5 * (a + b)
            center_doc = mid_head + l_vec * (0.5 * self.default_len_in * self.u)
            center_in = rg.Point3d(center_doc.X / self.u, center_doc.Y / self.u, center_doc.Z / self.u)

            parts, curves, _ = build_bed_system(
                center_in, w_vec, l_vec, w_in, self.default_len_in, self.S, False, self.u
            )
            for kind, brep in parts:
                if brep and brep.IsValid:
                    col = System.Drawing.Color.DeepSkyBlue if kind in ("mattress", "duvet", "pillow") else System.Drawing.Color.Gold
                    e.Display.DrawBrepWires(brep, col, 1)
            for crv in curves:
                if crv and crv.IsValid:
                    e.Display.DrawCurve(crv, System.Drawing.Color.Gold, 2)
        except Exception:
            pass


class BedLengthPointGetter(ric.GetPoint):
    """Live 3D bed wireframe preview while picking the third point (bed length & foot direction)."""
    def __init__(self, p0, p1, settings, u):
        super(BedLengthPointGetter, self).__init__()
        self.p0 = rg.Point3d(p0)
        self.p1 = rg.Point3d(p1)
        self.u = u if u > 0 else 1.0
        self.S = dict(settings)
        self.S["fast_preview"] = True
        self.S["size_preset"] = 0

    def OnDynamicDraw(self, e):
        try:
            curr = e.CurrentPoint
            ok, c_doc, w_vec, l_vec, doc_w, doc_l = compute_bed_frame_from_3pts(self.p0, self.p1, curr)
            if not ok or (doc_w / self.u) < 36.0 or (doc_l / self.u) < 60.0:
                return
            center_in = rg.Point3d(c_doc.X / self.u, c_doc.Y / self.u, c_doc.Z / self.u)
            parts, curves, _ = build_bed_system(
                center_in, w_vec, l_vec, doc_w / self.u, doc_l / self.u, self.S, False, self.u
            )
            for kind, brep in parts:
                if brep and brep.IsValid:
                    col = System.Drawing.Color.DeepSkyBlue if kind in ("mattress", "duvet", "pillow") else System.Drawing.Color.Gold
                    e.Display.DrawBrepWires(brep, col, 1)
            for crv in curves:
                if crv and crv.IsValid:
                    e.Display.DrawCurve(crv, System.Drawing.Color.Gold, 2)
        except Exception:
            pass


def compute_bed_frame_from_3pts(p0, p1, p2):
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
    raw_l = c - b
    raw_l.Z = 0.0
    perp_l = raw_l - w_vec * _dot(raw_l, w_vec)
    if perp_l.Length < 1e-3:
        raw_l = c - a
        raw_l.Z = 0.0
        perp_l = raw_l - w_vec * _dot(raw_l, w_vec)
    if perp_l.Length < 1e-3:
        return False, None, None, None, 0.0, 0.0

    doc_l = perp_l.Length
    l_vec = _safe_unitize(perp_l, rg.Vector3d.YAxis)
    if rg.Vector3d.CrossProduct(w_vec, l_vec).Z < 0:
        w_vec.Reverse()

    mid_head = 0.5 * (a + b)
    center_doc = mid_head + l_vec * (0.5 * doc_l)
    return True, center_doc, w_vec, l_vec, doc_w, doc_l


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

    v0 = pts[1] - pts[0]
    v0.Z = 0.0
    v1 = pts[2] - pts[1]
    v1.Z = 0.0
    if v0.Length < 1e-3 or v1.Length < 1e-3:
        return False, None, None, None, 0.0, 0.0, "Rectangle dimensions are too small."

    w_vec = _safe_unitize(v0, rg.Vector3d.XAxis)
    l_vec = _safe_unitize(v1, rg.Vector3d.YAxis)
    if rg.Vector3d.CrossProduct(w_vec, l_vec).Z < 0:
        l_vec.Reverse()
    return True, center, w_vec, l_vec, v0.Length, v1.Length, ""


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
        self.textbox = make_textbox(format_bed_length(disp_val, unit_name, is_int))

    def value(self):
        try:
            txt = self.textbox.Text.strip()
            if self.is_length:
                val_unit = parse_bed_length(txt, self.unit_name)
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
        self.textbox.Text = format_bed_length(disp_val, self.unit_name, self.is_int)


class BedDialog(forms.Dialog[bool]):
    def __init__(self):
        super(BedDialog, self).__init__()
        self._initialized = False
        self._preview_closed = False
        self._suppress_preview = True
        self.final_settings = None
        self.conduit = None

    def Initialize(self, center_in, width_vec, length_vec, width_in, length_in, initial_settings=None, is_edit=False):
        if self._initialized:
            return
        self._initialized = True

        unit_sys, unit_name, scale_from_inch = get_doc_unit_info()
        self.unit_name = unit_name
        self.scale_from_inch = scale_from_inch

        self.center_in = center_in
        self.width_vec = width_vec
        self.length_vec = length_vec
        self.width_in = width_in
        self.length_in = length_in
        self.is_edit = is_edit

        title_prefix = "Edit Modern Bed & Suite" if is_edit else "Modern Architectural Bed & Suite Generator"
        self.Title = "%s [%s]" % (title_prefix, unit_name)
        self.Padding = drawing.Padding(10)
        self.Resizable = True
        try:
            self.Topmost = True
        except Exception:
            pass
        self.ClientSize = drawing.Size(660, 780)

        prev_conduit = sc.sticky.get(CONDUIT_KEY)
        if prev_conduit is not None:
            try:
                prev_conduit.Enabled = False
            except Exception:
                pass

        self.conduit = BedPreviewConduit(wireframe_only=False)
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

        self.cb_flip = make_checkbox("Flip headboard / footboard orientation (180 deg)", s["flip_facing"])
        self.cb_fast = make_checkbox("Fast preview (simplified fillets while editing)", s["fast_preview"])

        self.dd_preset = forms.DropDown()
        self.dd_preset.Width = 190
        self.txt_preset_name = make_textbox("", width=150)
        self.btn_preset_load = make_button("Load")
        self.btn_preset_save = make_button("Save")
        self.btn_preset_delete = make_button("Delete")
        self._refresh_preset_dropdown()

        main = forms.DynamicLayout()
        main.Spacing = drawing.Size(5, 5)

        disp_w = format_bed_length(self.width_in * scale_from_inch, unit_name)
        disp_l = format_bed_length(self.length_in * scale_from_inch, unit_name)
        self.summary_lbl = make_label(
            "Footprint Width: %s %s   |   Footprint Length: %s %s" % (disp_w, unit_name, disp_l, unit_name),
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
        bt = int(self.dds["bed_type"].SelectedIndex)
        hbs = int(self.dds["hb_style"].SelectedIndex)
        acc = int(self.dds["accessory_opt"].SelectedIndex)
        bedding = int(self.dds["bedding_style"].SelectedIndex)

        self.fields["hb_ext_w"].textbox.Enabled = (bt == 3)
        self.fields["wing_depth"].textbox.Enabled = (bt == 2)
        self.fields["canopy_h"].textbox.Enabled = (bt == 4)
        self.fields["post_w"].textbox.Enabled = (bt == 4)

        self.fields["hb_channels"].textbox.Enabled = (hbs in (0, 1))
        self.fields["hb_rows"].textbox.Enabled = (hbs == 1)

        self.fields["duvet_cov_pct"].textbox.Enabled = (bedding in (0, 1))
        self.fields["duvet_drape"].textbox.Enabled = (bedding in (0, 1))

        has_ns = acc in (1, 2, 4) or (bt == 3 and acc == 0)
        self.fields["ns_w"].textbox.Enabled = has_ns
        self.fields["ns_d"].textbox.Enabled = has_ns
        self.fields["ns_h"].textbox.Enabled = has_ns

        has_bench = acc in (3, 4)
        self.fields["bench_d"].textbox.Enabled = has_bench
        self.fields["bench_h"].textbox.Enabled = has_bench

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
            parts, curves, info = build_bed_system(
                self.center_in, self.width_vec, self.length_vec,
                self.width_in, self.length_in, S, False, self.scale_from_inch
            )
            self.conduit.preview_breps = parts
            self.conduit.preview_curves = curves

            bt_short = BED_TYPE_NAMES[S["bed_type"]].split(". ", 1)[-1]
            mw_disp = format_bed_length(info.get("mat_w_in", 0.0) * self.scale_from_inch, self.unit_name)
            ml_disp = format_bed_length(info.get("mat_l_in", 0.0) * self.scale_from_inch, self.unit_name)
            h_disp  = format_bed_length(info.get("hb_h_in", 0.0) * self.scale_from_inch, self.unit_name)
            self.lbl_info.Text = "%s  |  Mattress: %s x %s %s  |  Headboard Height: %s %s" % (
                bt_short, mw_disp, ml_disp, self.unit_name, h_disp, self.unit_name
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


def show_bed_dialog(dlg, doc):
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
def create_modern_bed():
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
        initial_gp.SetCommandPrompt("Start of bed headboard back-left corner")
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
                p1 = rs.GetPoint("Pick back-left corner of bed headboard")
                if not p1:
                    return
                start_pt = rg.Point3d(p1.X, p1.Y, p1.Z)
                mode = "draw"
                break
        elif rc == Rhino.Input.GetResult.Nothing:
            p1 = rs.GetPoint("Pick back-left corner of bed headboard")
            if not p1:
                return
            start_pt = rg.Point3d(p1.X, p1.Y, p1.Z)
            mode = "draw"
            break
        else:
            return

    center_in = None
    width_vec = None
    length_vec = None
    width_in = 0.0
    length_in = DEFAULT_BED_LENGTH_IN
    edit_target_ids = []

    # --------------------------------------------------------
    # STEP 2A: SELECT RECTANGLE CURVE OR EXISTING BED TO EDIT
    # --------------------------------------------------------
    if mode == "select":
        go = ric.GetObject()
        go.SetCommandPrompt("Select closed rectangle curve or existing Bed to edit")
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
            c_in, width_vec, length_vec, width_in, length_in, saved_s = decoded
            init_s = saved_s
            edit_target_ids = get_generated_group_member_ids(doc, obj)
            c_doc = rg.Point3d(c_in.X * u, c_in.Y * u, c_in.Z * u)
            c_doc, width_vec, length_vec = transform_frame_from_current_objects(doc, c_doc, width_vec, length_vec, edit_target_ids)
            center_in = rg.Point3d(c_doc.X / u, c_doc.Y / u, c_doc.Z / u)
        else:
            crv = objref.Curve()
            ok, c_doc, width_vec, length_vec, doc_w, doc_l, err = extract_rectangle_frame(crv)
            if not ok:
                rs.MessageBox(err, 48, "Bed Footprint Error")
                return
            center_in = rg.Point3d(c_doc.X / u, c_doc.Y / u, c_doc.Z / u)
            width_in = doc_w / u
            length_in = doc_l / u

    # --------------------------------------------------------
    # STEP 2B: DRAW BED FOOTPRINT WITH LIVE 3D PREVIEW
    # --------------------------------------------------------
    else:
        gp_w = BedWidthPointGetter(start_pt, init_s, u, DEFAULT_BED_LENGTH_IN)
        gp_w.SetCommandPrompt("Pick back-right corner of bed headboard (defines width & facing direction)")
        gp_w.SetBasePoint(start_pt, True)
        gp_w.DrawLineFromPoint(start_pt, True)
        if gp_w.Get() != Rhino.Input.GetResult.Point:
            return
        p1 = gp_w.Point()

        l_disp = format_bed_length(DEFAULT_BED_LENGTH_IN * u, unit_name)
        gp_l = BedLengthPointGetter(start_pt, p1, init_s, u)
        gp_l.SetCommandPrompt("Pick foot-of-bed length point or press ENTER for standard length <%s %s>" % (l_disp, unit_name))
        gp_l.SetBasePoint(p1, True)
        gp_l.DrawLineFromPoint(p1, True)
        gp_l.AcceptNothing(True)
        rc_l = gp_l.Get()

        if rc_l == Rhino.Input.GetResult.Point:
            p2 = gp_l.Point()
            ok, c_doc, width_vec, length_vec, doc_w, doc_l = compute_bed_frame_from_3pts(start_pt, p1, p2)
            if not ok or (doc_w / u) < 36.0 or (doc_l / u) < 60.0:
                rs.MessageBox("Bed footprint dimensions are too small (min 36 x 60 in).", 48, "Bed Error")
                return
            center_in = rg.Point3d(c_doc.X / u, c_doc.Y / u, c_doc.Z / u)
            width_in = doc_w / u
            length_in = doc_l / u
        elif rc_l == Rhino.Input.GetResult.Nothing:
            base_z = start_pt.Z
            a = rg.Point3d(start_pt.X, start_pt.Y, base_z)
            b = rg.Point3d(p1.X, p1.Y, base_z)
            v = b - a
            v.Z = 0.0
            if (v.Length / u) < 36.0:
                rs.MessageBox("Bed width is too narrow (minimum 36 in).", 48, "Bed Error")
                return
            width_vec = _safe_unitize(v, rg.Vector3d.XAxis)
            length_vec = _safe_unitize(rg.Vector3d.CrossProduct(rg.Vector3d.ZAxis, width_vec), rg.Vector3d.YAxis)
            mid_head = 0.5 * (a + b)
            c_doc = mid_head + length_vec * (0.5 * DEFAULT_BED_LENGTH_IN * u)
            center_in = rg.Point3d(c_doc.X / u, c_doc.Y / u, c_doc.Z / u)
            width_in = v.Length / u
            length_in = DEFAULT_BED_LENGTH_IN
        else:
            return

    # --------------------------------------------------------
    # STEP 3: SETTINGS DIALOG WITH LIVE SHADED PREVIEW
    # --------------------------------------------------------
    dlg = BedDialog()
    dlg.Initialize(
        center_in, width_vec, length_vec, width_in, length_in,
        initial_settings=init_s,
        is_edit=bool(edit_target_ids),
    )
    dialog_result = False
    try:
        dialog_result = show_bed_dialog(dlg, doc)
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
    sn = doc.BeginUndoRecord("Create Modern Bed")
    rs.EnableRedraw(False)
    try:
        ids = bake_bed(doc, center_in, width_vec, length_vec, width_in, length_in, S, u, edit_target_ids)
    except Exception as ex:
        ids = []
        import traceback
        traceback.print_exc()
        rs.MessageBox("Unexpected error creating bed: {}".format(ex), 0, "Bed Error")
    finally:
        rs.EnableRedraw(True)
        if sn > 0:
            doc.EndUndoRecord(sn)

    doc.Views.Redraw()
    if ids:
        bt_name = BED_TYPE_NAMES[S["bed_type"]].split(". ", 1)[-1]
        print("\nModern Bed Created Successfully: {}".format(bt_name))
        print("Footprint: {:.1f} {} x {:.1f} {} | Headboard Height: {:.1f} {}".format(
            width_in * u, unit_name, length_in * u, unit_name, S["hb_h"] * u, unit_name
        ))


def run():
    create_modern_bed()


if __name__ in ["__main__", "ArchBed", "Bed", "__builtin__"]:
    create_modern_bed()
