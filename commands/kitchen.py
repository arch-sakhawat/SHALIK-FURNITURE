# -*- coding: utf-8 -*-
from __future__ import division
"""
Modern Ergonomic Kitchen Cabinet, Millwork & Warm-Yellow LED Lighting Generator
(units: INCHES internally, auto-scaled via ArchUnits)
Compatible with Rhino 7 & Rhino 8 (both IronPython 2.7 and CPython 3 / Python.NET).

Ergonomic & Standard Board Reference:
  - Counter Height  : 36 in (915 mm)  | Base Depth : 24 in (600 mm)
  - Toe-Kick Plinth : 4 in H x 3 in D | Backsplash : 18 in (450 mm)
  - Upper Depth     : 13 in (330 mm)  | Tall Unit  : 84 in (2135 mm)
  - Standard Boards : 18 mm (0.71 in) Carcass/Door | 6 mm (0.24 in) Back Panel

Flow:
  1. Command prompt defaults to DrawKitchen with [DrawKitchen] and [SelectKitchen] options
     (D and S underlined; selectable via d/s + Enter or mouse click).
     - DrawKitchen: Pick Start Point -> Move mouse to preview 3D Kitchen dynamically!
       Click 2nd point to set run length & wall direction, OR press ENTER for default 120 in (10 ft).
     - SelectKitchen: Select an existing generated Kitchen group to non-destructively edit in place,
       OR select a wall baseline curve.
  2. Settings Dialog -> Tall single-column UI (540 x 820) with Upper Ergonomic & Standard Board
     Reference Banner, 8 Kitchen Typologies, 5 Door Styles, 5 Warm-Yellow LED Lighting Styles,
     Appliances (Sink, Faucet, Hob, Hood, Oven), Finishes & Presets.
  3. Press Create -> Baked onto ARCH_KITCHEN :: CARCASS_BOARD / SHUTTER_FRONT / COUNTERTOP_STONE /
                     BACKSPLASH / GLASS_INSERT / HARDWARE_SINK / TOE_KICK / LED_YELLOW_LIGHT
                     layers with materials and grouped with editable metadata.
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


def parse_cab_length(text, current_unit="in"):
    if ArchUnits:
        return ArchUnits.parse_length(text, current_unit)
    txt = str(text).strip().lower()
    if txt.endswith("ft") or txt.endswith("'"):
        num_str = txt.replace("ft", "").replace("'", "").strip()
        try:
            val_ft = float(num_str)
            _, _, scale = get_doc_unit_info()
            return val_ft * 12.0 * scale
        except Exception:
            pass
    if txt.endswith("mm"):
        num_str = txt.replace("mm", "").strip()
        try:
            val_mm = float(num_str)
            _, _, scale = get_doc_unit_info()
            return (val_mm / 25.4) * scale
        except Exception:
            pass
    try:
        return float(txt)
    except Exception:
        return 0.0


def format_cab_length(v, unit_name="in", is_int=False):
    if ArchUnits:
        return ArchUnits.format_length(v, unit_name, is_int)
    if is_int:
        return str(int(round(v)))
    return ("%.3f" % v).rstrip("0").rstrip(".")


def update_label_unit(label, unit_name):
    if ArchUnits:
        return ArchUnits.update_label_unit(label, unit_name)
    return re.sub(r'\(in\b', '(' + unit_name, str(label), flags=re.IGNORECASE)


NON_LENGTH_KEYS = {"base_shelves", "wall_shelves", "drawer_count", "tall_count"}


# ============================================================
# PERSISTENCE, METADATA & CONDUIT KEYS
# ============================================================
STICKY_KEY = "SHALIKTOOLS_KITCHEN_CABINET_SETTINGS_V1"
CONDUIT_KEY = "SHALIKTOOLS_KITCHEN_CABINET_CONDUIT_V1"
METADATA_KEY = "ShalikKitchenCabinetState"
ITEM_INDEX_KEY = "ShalikKitchenCabinetItemIndex"
ITEM_CENTER_KEY = "ShalikKitchenCabinetItemCenter"
PRESET_FOLDER_NAME = "ShalikTools"
PRESET_FILE_NAME = "ModernKitchenCabinetPresets.json"

DEFAULT_RUN_LENGTH_IN = 144.0  # 12'-0" (3658 mm)
WARM_YELLOW_LED_RGB = (255, 215, 65)  # Warm 2700K-3000K Golden-Yellow LED


# ============================================================
# CABINET TYPOLOGIES, BOARD STANDARDS, DOORS & LED LIGHTING
# ============================================================
CABINET_TYPES = [
    "0. Full Ergonomic Kitchen (Base + Wall Uppers + Tall Pantry)",
    "1. L-Shape Corner Kitchen Run (Main Wall + 90 deg Return Wing)",
    "2. Base Cabinets + Countertop + Sink & Cooktop Only",
    "3. Wall Upper Cabinets Only (Solid + Glass Display Mix)",
    "4. Kitchen Island with Breakfast Bar Overhang & Waterfall",
    "5. Tall Pantry & Built-In Oven/Microwave Tower Run",
    "6. Galley / Parallel Kitchen (Main Wall Assembly + Island)",
    "7. Full Floor-to-Ceiling Architectural Millwork Wall",
]

BOARD_STD_NAMES = [
    "0. Standard 18 mm (0.71 in) Carcass/Door + 6 mm Back",
    "1. Standard 16 mm (0.63 in) Moisture-Resistant + 6 mm Back",
    "2. Heavy 19 mm (3/4 in) Plywood Carcass + 12 mm Back",
    "3. Heavy 25 mm (1.0 in) Commercial Millwork + 12 mm Back",
    "4. Custom Board Thickness (User-Defined Below)",
]

DOOR_STYLE_NAMES = [
    "0. Modern Flat Minimalist Slab Door",
    "1. Classic Shaker 5-Piece Framed Recessed Panel",
    "2. Contemporary Fluted / Vertical Ribbed Slat Door",
    "3. Aluminum-Framed Glass Display Upper Doors",
    "4. Handleless J-Pull / Chamfered Finger-Groove Door",
]

HANDLE_STYLE_NAMES = [
    "0. Modern Architectural Bar Pull (Vertical/Horizontal)",
    "1. Concealed Gola Aluminum J-Channel Profile",
    "2. Minimalist Top-Edge Lip Pull",
    "3. Cylindrical Satin Knob",
    "4. Push-to-Open Latch (No Visible Handle)",
]

LIGHT_STYLE_NAMES = [
    "0. Full Warm-Yellow LED Package (Under-Cab + Toe-Kick + Interior + Cove)",
    "1. Under-Cabinet Linear Warm-Yellow LED Strip Channel",
    "2. Under-Cabinet Warm-Yellow Recessed Puck Downlights",
    "3. Illuminated Glass Cabinet Interior Vertical Yellow LED Strips",
    "4. Floating Toe-Kick Plinth Warm-Yellow LED Strip Only",
    "5. None (Disable LED Lighting)",
]

CORNER_TURN_NAMES = [
    "0. Right Corner Return (+Y Forward on Right End)",
    "1. Left Corner Return (+Y Forward on Left End)",
]

# Finishes: (Name, (R, G, B))
CARCASS_FINISHES = [
    ("White Melamine Birch Core",   (238, 236, 230)),
    ("Warm Natural Oak Veneer",     (198, 158, 112)),
    ("Smoked Walnut Veneer",        (92, 64, 46)),
    ("Anthracite Linen Melamine",   (62, 65, 70)),
]

SHUTTER_FINISHES = [
    ("Matte Cashmere Warm Gray",    (205, 198, 188)),
    ("Matte Charcoal Graphite",     (52, 55, 60)),
    ("Nordic Natural White Oak",    (212, 178, 135)),
    ("Deep Sage Architectural Green",(92, 115, 98)),
    ("Midnight Navy Matte Lacquer", (38, 52, 74)),
    ("Pure Satin White Lacquer",    (242, 242, 240)),
    ("Rich American Walnut",        (105, 70, 48)),
]

COUNTER_FINISHES = [
    ("Calacatta Gold Quartz",       (236, 234, 228)),
    ("Nero Marquina Black Marble",  (38, 40, 44)),
    ("Honed Concrete Gray Stone",   (152, 155, 158)),
    ("Solid Butcher-Block Teak",    (175, 122, 76)),
    ("Brushed Stainless Chef Top",  (192, 196, 202)),
]

HARDWARE_FINISHES = [
    ("Satin Brushed Brass / Gold",  (195, 160, 82)),
    ("Matte Black Anodized",        (30, 32, 35)),
    ("Brushed Stainless Chrome",    (202, 206, 212)),
    ("Champagne Bronze",            (168, 142, 108)),
]


# ============================================================
# PARAMETER DEFINITIONS (STRICT INCHES - ERGONOMIC DEFAULTS)
# ============================================================
NUM_FIELDS = [
    # 1. Overall Run & Ergonomic Heights
    ("total_length",    "Main kitchen run length (in):",    144.0, 24.0, 600.0, False), # 12'-0" (3658 mm)
    ("return_length",   "L-Corner / Island length (in):",    84.0, 24.0, 360.0, False), # 7'-0" (2134 mm)
    ("module_w",        "Standard module bay width (in):",   24.0, 12.0,  48.0, False), # 24" (600 mm)
    ("counter_h",       "Ergonomic counter height (in):",    36.0, 28.0,  44.0, False), # 36" (915 mm)
    ("base_depth",      "Base cabinet carcass depth (in):",  24.0, 14.0,  36.0, False), # 24" (600 mm)
    ("toekick_h",       "Toe-kick plinth height (in):",       4.0,  2.0,   8.0, False), # 4" (100 mm)
    ("toekick_recess",  "Toe-kick front recess (in):",        3.0,  1.0,   6.0, False), # 3" (75 mm)
    ("backsplash_h",    "Ergonomic backsplash gap (in):",    18.0, 12.0,  30.0, False), # 18" (450 mm)
    ("wall_cab_h",      "Wall upper cabinet height (in):",   30.0, 12.0,  60.0, False), # 30" (760 mm)
    ("wall_cab_d",      "Wall upper cabinet depth (in):",    13.0,  8.0,  24.0, False), # 13" (330 mm)
    ("tall_cab_h",      "Tall pantry total height (in):",    84.0, 60.0, 120.0, False), # 84" (2135 mm)
    ("tall_count",      "Number of tall pantry bays (0-4):",  1,    0,     4,   True),
    # 2. Standard Board Thicknesses & Countertop Details
    ("carcass_t",       "Carcass board thickness (in):",     0.71, 0.45,  1.5,  False), # 18 mm
    ("shutter_t",       "Door / shutter thickness (in):",    0.75, 0.50,  1.5,  False), # 19 mm
    ("back_t",          "Grooved back panel thick (in):",    0.24, 0.12,  0.75, False), # 6 mm
    ("reveal_gap",      "Door shadow reveal gap (in):",      0.12, 0.04,  0.35, False), # 3 mm
    ("counter_t",       "Stone countertop thickness (in):",  1.50, 0.50,  4.0,  False), # 38 mm
    ("counter_overhang","Counter front overhang (in):",      1.00, 0.0,   4.0,  False), # 25 mm
    ("bar_overhang",    "Island breakfast overhang (in):",  12.00, 0.0,  24.0,  False), # 300 mm
    ("loft_h",          "Top loft / crown soffit h (in):",  12.00, 0.0,  36.0,  False), # 300 mm
    # 3. Internal Shelving, Drawers & LED Strip Sizing
    ("base_shelves",    "Adjustable shelves per base bay:",   1,    0,     4,   True),
    ("wall_shelves",    "Adjustable shelves per wall bay:",   2,    0,     5,   True),
    ("drawer_count",    "Drawers per drawer-bank bay:",       3,    2,     5,   True),
    ("led_strip_w",     "Warm-yellow LED strip width (in):", 0.65, 0.25,  2.5,  False),
]

DD_FIELDS = [
    ("cabinet_type",    "Kitchen layout & typology:",   0, CABINET_TYPES),
    ("board_std",       "Standard board size preset:",  0, BOARD_STD_NAMES),
    ("door_style",      "Door / shutter profile:",      1, DOOR_STYLE_NAMES),
    ("handle_style",    "Handle / pull hardware:",      0, HANDLE_STYLE_NAMES),
    ("light_style",     "Warm-yellow LED light style:", 0, LIGHT_STYLE_NAMES),
    ("corner_turn",     "L-Corner return direction:",   0, CORNER_TURN_NAMES),
    ("carcass_finish",  "Interior carcass board finish:",0,[n for n, c in CARCASS_FINISHES]),
    ("shutter_finish",  "Exterior door/shutter finish:",0, [n for n, c in SHUTTER_FINISHES]),
    ("counter_finish",  "Countertop & splash stone:",   0, [n for n, c in COUNTER_FINISHES]),
    ("hw_finish",       "Handles, sink & faucet finish:",0,[n for n, c in HARDWARE_FINISHES]),
]

CB_FIELDS = [
    ("include_sink",      "Include undermount sink + gooseneck faucet bay",    True),
    ("include_cooktop",   "Include 4-zone induction cooktop + range hood bay", True),
    ("include_drawers",   "Include 3-drawer cutlery/pot bank bays",            True),
    ("include_backsplash","Include full-height stone backsplash slab",         True),
    ("include_loft",      "Include top ceiling loft / crown bulkhead",         True),
    ("waterfall_edges",   "Include waterfall stone end-panels on island/ends", False),
    ("open_doors_30",     "Open cabinet doors 30 deg to reveal interior/LEDs", False),
    ("fast_preview",      "Fast preview (simplified hardware during drag)",    False),
]

TAB_LAYOUT = [
    ("1. Layout && Ergonomics", [
        "cabinet_type",
        "corner_turn",
        "@calc_info",
        "total_length",
        "return_length",
        "module_w",
        "counter_h",
        "base_depth",
        "toekick_h",
        "toekick_recess",
        "backsplash_h",
        "wall_cab_h",
        "wall_cab_d",
        "tall_cab_h",
        "tall_count",
        "loft_h",
    ]),
    ("2. Boards, Doors && LEDs", [
        "board_std",
        "carcass_t",
        "shutter_t",
        "back_t",
        "reveal_gap",
        "door_style",
        "handle_style",
        "light_style",
        "led_strip_w",
        "counter_t",
        "counter_overhang",
        "bar_overhang",
        "base_shelves",
        "wall_shelves",
        "drawer_count",
        "include_sink",
        "include_cooktop",
        "include_drawers",
        "include_backsplash",
        "include_loft",
        "waterfall_edges",
        "open_doors_30",
    ]),
    ("3. Finishes && Presets", [
        "carcass_finish",
        "shutter_finish",
        "counter_finish",
        "hw_finish",
        "fast_preview",
    ]),
]


# ============================================================
# UTILITIES & METADATA HELPERS
# ============================================================
def clamp(val, mn, mx):
    return max(mn, min(mx, val))


def unit_scale(doc=None):
    _, _, scale = get_doc_unit_info(doc)
    return scale


def default_settings():
    s = {}
    for k, l, d, mn, mx, ii in NUM_FIELDS:
        s[k] = d
    for k, l, d, n in DD_FIELDS:
        s[k] = d
    for k, l, d in CB_FIELDS:
        s[k] = d
    return s


def normalize_settings(raw):
    clean = default_settings()
    if not isinstance(raw, dict):
        return clean
    for k, l, d, mn, mx, ii in NUM_FIELDS:
        if k in raw:
            try:
                v = clamp(float(raw[k]), mn, mx)
                clean[k] = int(round(v)) if ii else v
            except Exception:
                clean[k] = d
    for k, l, d, n in DD_FIELDS:
        if k in raw:
            try:
                clean[k] = clamp(int(raw[k]), 0, len(n) - 1)
            except Exception:
                clean[k] = d
    for k, l, d in CB_FIELDS:
        if k in raw:
            clean[k] = bool(raw[k])
    return clean


def get_initial_settings():
    stored = sc.sticky.get(STICKY_KEY)
    if isinstance(stored, dict):
        return normalize_settings(stored)
    return default_settings()


def rgb_to_color(rgb):
    return System.Drawing.Color.FromArgb(int(rgb[0]), int(rgb[1]), int(rgb[2]))


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


def encode_state(base_plane_in, settings):
    state = {
        "version": 1,
        "plane": {
            "origin_in": _point_to_data(base_plane_in.Origin),
            "x_axis": _vector_to_data(base_plane_in.XAxis),
            "y_axis": _vector_to_data(base_plane_in.YAxis),
        },
        "settings": normalize_settings(settings),
    }
    return json.dumps(state, ensure_ascii=False)


def decode_state(text):
    if not text:
        return None
    try:
        state = json.loads(text)
        pl_data = state["plane"]
        orig_in = _point_from_data(pl_data["origin_in"])
        x_ax = _safe_unitize(_vector_from_data(pl_data["x_axis"]), rg.Vector3d.XAxis)
        y_ax = _safe_unitize(_vector_from_data(pl_data["y_axis"]), rg.Vector3d.YAxis)
        settings = normalize_settings(state.get("settings", {}))
        return rg.Plane(orig_in, x_ax, y_ax), settings
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


def transform_plane_from_current_objects(doc, base_plane_doc, target_ids):
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
        return base_plane_doc

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

    p0 = base_plane_doc.Origin
    dx, dy = p0.X - ox, p0.Y - oy
    new_orig = rg.Point3d(cx + ca * dx - sa * dy, cy + sa * dx + ca * dy, p0.Z + (cz - oz))
    vx = base_plane_doc.XAxis
    vy = base_plane_doc.YAxis
    new_x = _safe_unitize(rg.Vector3d(ca * vx.X - sa * vx.Y, sa * vx.X + ca * vx.Y, vx.Z), vx)
    new_y = _safe_unitize(rg.Vector3d(ca * vy.X - sa * vy.Y, sa * vy.X + ca * vy.Y, vy.Z), vy)
    return rg.Plane(new_orig, new_x, new_y)


# ============================================================
# 3D MILLWORK, SHUTTER, APPLIANCE & WARM-YELLOW LED ENGINE
# (Local Space: X = Run Length [0..L], Y = Depth Forward from Wall [0..D], Z = Height [0..H])
# ============================================================
def add_part(parts_list, kind, brep):
    if brep and brep.IsValid:
        parts_list.append((kind, brep))


def mk_box(x0, x1, y0, y1, z0, z1):
    if x1 - x0 <= 1e-5 or y1 - y0 <= 1e-5 or z1 - z0 <= 1e-5:
        return None
    box = rg.Box(
        rg.Plane.WorldXY,
        rg.Interval(x0, x1),
        rg.Interval(y0, y1),
        rg.Interval(z0, z1),
    )
    return box.ToBrep() if box.IsValid else None


def make_cyl(base_pt, axis_vec, radius, length):
    if radius <= 1e-4 or length <= 1e-4:
        return None
    uv = _safe_unitize(axis_vec, rg.Vector3d.ZAxis)
    pl = rg.Plane(base_pt, uv)
    return rg.Cylinder(rg.Circle(pl, radius), length).ToBrep(True, True)


def build_single_carcass_box(x0, x1, y0, y1, z0, z1, tc, tb, n_shelves, is_glass_door, light_style, led_w, fast):
    """
    Builds a true 3D Millwork Carcass Box with standard board thicknesses:
      - Left & Right Side Gables (thickness `tc`)
      - Bottom Deck & Top Panel / Stretchers (thickness `tc`)
      - Grooved Back Panel (thickness `tb`, inset 0.5" from rear wall)
      - Adjustable Interior Shelves (or Glass Shelves if `is_glass_door`)
      - Optional Interior Warm-Yellow Vertical LED Side Strips (when `light_style` in (0, 3))
    """
    parts = []
    W = x1 - x0
    D = y1 - y0
    H = z1 - z0
    if W <= 2.0 * tc + 1.0 or D <= tc + tb + 1.0 or H <= 2.0 * tc + 1.0:
        return parts

    # 1. Left & Right Gables
    add_part(parts, "carcass", mk_box(x0, x0 + tc, y0, y1, z0, z1))
    add_part(parts, "carcass", mk_box(x1 - tc, x1, y0, y1, z0, z1))

    # 2. Bottom Deck & Top Panel
    ix0 = x0 + tc
    ix1 = x1 - tc
    add_part(parts, "carcass", mk_box(ix0, ix1, y0, y1, z0, z0 + tc))
    add_part(parts, "carcass", mk_box(ix0, ix1, y0, y1, z1 - tc, z1))

    # 3. Grooved Back Panel (thickness tb)
    back_inset = min(0.4, D * 0.05)
    y_back_front = y0 + back_inset + tb
    add_part(parts, "carcass", mk_box(ix0, ix1, y0 + back_inset, y_back_front, z0 + tc, z1 - tc))

    # 4. Adjustable Interior Shelves
    if n_shelves > 0:
        clear_h = H - 2.0 * tc
        step_z = clear_h / float(n_shelves + 1)
        shelf_t = tc * 0.45 if is_glass_door else tc
        shelf_kind = "glass" if is_glass_door else "carcass"
        for s_i in range(1, n_shelves + 1):
            zs = z0 + tc + s_i * step_z - shelf_t * 0.5
            add_part(parts, shelf_kind, mk_box(ix0 + 0.04, ix1 - 0.04, y_back_front, y1 - 0.6, zs, zs + shelf_t))

    # 5. Interior Vertical Warm-Yellow LED Strips along Left & Right Gables
    if light_style in (0, 3) and (is_glass_door or light_style == 3):
        lw = max(0.35, led_w * 0.75)
        ld = 0.25
        y_led = y1 - 2.2
        if y_led > y_back_front + 1.0:
            add_part(parts, "led_yellow", mk_box(ix0, ix0 + ld, y_led - lw * 0.5, y_led + lw * 0.5, z0 + tc + 0.2, z1 - tc - 0.2))
            add_part(parts, "led_yellow", mk_box(ix1 - ld, ix1, y_led - lw * 0.5, y_led + lw * 0.5, z0 + tc + 0.2, z1 - tc - 0.2))

    return parts


def build_handle_hardware(x0, x1, y_front, z0, z1, is_horizontal, hinge_left, is_upper, handle_style, fast):
    """Builds 3D cabinet door/drawer pull hardware on the front face (`y_front`)."""
    parts = []
    if handle_style in (1, 4):
        return parts

    W = x1 - x0
    H = z1 - z0
    if W < 3.0 or H < 3.0:
        return parts

    proj = 1.25
    bar_t = 0.38

    if is_horizontal:
        # Centered horizontal drawer pull near top of drawer face
        pull_len = min(W * 0.45, 7.5)
        xc = 0.5 * (x0 + x1)
        zp = z1 - min(2.2, H * 0.32)
        if handle_style == 0:
            add_part(parts, "hardware", mk_box(xc - pull_len * 0.5, xc + pull_len * 0.5, y_front + proj - bar_t, y_front + proj, zp - bar_t * 0.5, zp + bar_t * 0.5))
            if not fast:
                add_part(parts, "hardware", mk_box(xc - pull_len * 0.38, xc - pull_len * 0.38 + bar_t, y_front, y_front + proj - bar_t, zp - bar_t * 0.5, zp + bar_t * 0.5))
                add_part(parts, "hardware", mk_box(xc + pull_len * 0.38 - bar_t, xc + pull_len * 0.38, y_front, y_front + proj - bar_t, zp - bar_t * 0.5, zp + bar_t * 0.5))
        elif handle_style == 2:
            # Top-edge lip pull
            add_part(parts, "hardware", mk_box(xc - pull_len * 0.5, xc + pull_len * 0.5, y_front, y_front + 0.85, z1 - 0.18, z1 + 0.05))
        elif handle_style == 3:
            # Cylindrical knob
            add_part(parts, "hardware", make_cyl(rg.Point3d(xc, y_front, zp), rg.Vector3d.YAxis, 0.55, 1.0))
    else:
        # Vertical door pull on opposite side of hinge
        xp = (x1 - 1.65) if hinge_left else (x0 + 1.65)
        pull_len = min(H * 0.28, 8.0)
        z_anchor = (z0 + 2.0) if is_upper else (z1 - 2.0 - pull_len)
        if handle_style == 0:
            add_part(parts, "hardware", mk_box(xp - bar_t * 0.5, xp + bar_t * 0.5, y_front + proj - bar_t, y_front + proj, z_anchor, z_anchor + pull_len))
            if not fast:
                add_part(parts, "hardware", mk_box(xp - bar_t * 0.5, xp + bar_t * 0.5, y_front, y_front + proj - bar_t, z_anchor + 0.6, z_anchor + 0.6 + bar_t))
                add_part(parts, "hardware", mk_box(xp - bar_t * 0.5, xp + bar_t * 0.5, y_front, y_front + proj - bar_t, z_anchor + pull_len - 0.6 - bar_t, z_anchor + pull_len - 0.6))
        elif handle_style == 2:
            z_lip = z0 if is_upper else (z1 - 0.2)
            add_part(parts, "hardware", mk_box(xp - 2.0, xp + 2.0, y_front, y_front + 0.85, z_lip, z_lip + 0.2))
        elif handle_style == 3:
            zk = (z0 + 2.5) if is_upper else (z1 - 2.5)
            add_part(parts, "hardware", make_cyl(rg.Point3d(xp, y_front, zk), rg.Vector3d.YAxis, 0.55, 1.0))

    return parts


def build_shutter_panel(x0, x1, y0, y1, z0, z1, door_style, handle_style, is_drawer, hinge_left, is_upper, open_30, fast):
    """
    Builds a single 3D Cabinet Door or Drawer Front Panel (`shutter`, `glass`, `hardware`):
      - Style 0: Flat Minimalist Slab
      - Style 1: Shaker 5-Piece Frame (Stiles + Rails + Recessed Center Panel)
      - Style 2: Fluted / Ribbed Vertical Slat Door
      - Style 3: Aluminum-Framed Glass Display Door (for Uppers/Tall)
      - Style 4: Handleless J-Pull Finger-Groove Door
    """
    parts = []
    W = x1 - x0
    T = y1 - y0
    H = z1 - z0
    if W <= 1.0 or T <= 0.1 or H <= 1.0:
        return parts

    # Apply Gola / J-Pull top recess if selected
    eff_z1 = (z1 - 0.65) if (door_style == 4 or handle_style == 1) and not is_upper else z1

    if door_style == 1 and W > 6.5 and (eff_z1 - z0) > 6.5 and not fast:
        # Shaker 5-Piece Door: 2.25" Stiles & Rails + Recessed Center Panel
        stile_w = min(2.25, W * 0.24)
        rail_h = min(2.25, (eff_z1 - z0) * 0.24)
        panel_t = T * 0.55
        add_part(parts, "shutter", mk_box(x0, x0 + stile_w, y0, y1, z0, eff_z1))
        add_part(parts, "shutter", mk_box(x1 - stile_w, x1, y0, y1, z0, eff_z1))
        add_part(parts, "shutter", mk_box(x0 + stile_w, x1 - stile_w, y0, y1, z0, z0 + rail_h))
        add_part(parts, "shutter", mk_box(x0 + stile_w, x1 - stile_w, y0, y1, eff_z1 - rail_h, eff_z1))
        add_part(parts, "shutter", mk_box(x0 + stile_w, x1 - stile_w, y0, y0 + panel_t, z0 + rail_h, eff_z1 - rail_h))

    elif door_style == 2 and not fast:
        # Fluted / Vertical Ribbed Slat Door
        base_t = T * 0.55
        add_part(parts, "shutter", mk_box(x0, x1, y0, y0 + base_t, z0, eff_z1))
        slat_pitch = 1.25
        n_slats = max(3, int(round(W / slat_pitch)))
        dx = W / float(n_slats)
        slat_w = dx * 0.62
        for k in range(n_slats):
            sx = x0 + (k + 0.5) * dx
            add_part(parts, "shutter", mk_box(sx - slat_w * 0.5, sx + slat_w * 0.5, y0 + base_t, y1, z0, eff_z1))

    elif door_style == 3 and not is_drawer and W > 6.0 and (eff_z1 - z0) > 6.0:
        # Aluminum-Framed Glass Display Door
        fw = min(1.6, W * 0.18)
        gt = min(0.25, T * 0.35)
        add_part(parts, "hardware", mk_box(x0, x0 + fw, y0, y1, z0, eff_z1))
        add_part(parts, "hardware", mk_box(x1 - fw, x1, y0, y1, z0, eff_z1))
        add_part(parts, "hardware", mk_box(x0 + fw, x1 - fw, y0, y1, z0, z0 + fw))
        add_part(parts, "hardware", mk_box(x0 + fw, x1 - fw, y0, y1, eff_z1 - fw, eff_z1))
        yc = 0.5 * (y0 + y1)
        add_part(parts, "glass", mk_box(x0 + fw, x1 - fw, yc - gt * 0.5, yc + gt * 0.5, z0 + fw, eff_z1 - fw))

    else:
        # Flat Minimalist Slab / J-Pull Door
        add_part(parts, "shutter", mk_box(x0, x1, y0, y1, z0, eff_z1))
        if door_style == 4 and not is_upper:
            add_part(parts, "shutter", mk_box(x0, x1, y0, y0 + T * 0.45, eff_z1, z1))

    # Add Handle / Pull Hardware
    parts.extend(build_handle_hardware(x0, x1, y1, z0, eff_z1, is_drawer, hinge_left, is_upper, handle_style, fast))

    # Optional 30-degree swing open preview for hinged doors
    if open_30 and not is_drawer:
        pivot_x = x0 if hinge_left else x1
        ang_rad = math.radians(-30.0 if hinge_left else 30.0)
        rot_xform = rg.Transform.Rotation(ang_rad, rg.Vector3d.ZAxis, rg.Point3d(pivot_x, y0, z0))
        rotated_parts = []
        for k_name, b_geom in parts:
            nb = b_geom.DuplicateBrep()
            nb.Transform(rot_xform)
            rotated_parts.append((k_name, nb))
        return rotated_parts

    return parts


def build_sink_and_faucet_assembly(xc, yc, z_counter_top, bay_w, base_d, fast):
    """
    Builds a 3D Undermount Stainless Steel Sink Basin, Drain Strainer, and High-Arc Gooseneck Mixer Faucet
    at `(xc, yc, z_counter_top)`, and returns `(parts_list, cutout_bounds_xy)`.
    """
    parts = []
    sink_w = min(bay_w - 4.0, 26.0)
    sink_d = min(base_d - 6.5, 16.5)
    sink_h = 8.5
    wall_t = 0.6

    sx0, sx1 = xc - sink_w * 0.5, xc + sink_w * 0.5
    sy0, sy1 = yc - sink_d * 0.5, yc + sink_d * 0.5
    z_top = z_counter_top - 0.15
    z_bot = z_top - sink_h

    # Sink Basin Walls & Bottom Tray
    add_part(parts, "hardware", mk_box(sx0 - wall_t, sx1 + wall_t, sy0 - wall_t, sy1 + wall_t, z_bot, z_bot + wall_t))
    add_part(parts, "hardware", mk_box(sx0 - wall_t, sx0, sy0 - wall_t, sy1 + wall_t, z_bot + wall_t, z_top))
    add_part(parts, "hardware", mk_box(sx1, sx1 + wall_t, sy0 - wall_t, sy1 + wall_t, z_bot + wall_t, z_top))
    add_part(parts, "hardware", mk_box(sx0, sx1, sy0 - wall_t, sy0, z_bot + wall_t, z_top))
    add_part(parts, "hardware", mk_box(sx0, sx1, sy1, sy1 + wall_t, z_bot + wall_t, z_top))

    # High-Arc Gooseneck Faucet mounted behind sink basin
    f_y = sy0 - 2.0
    p_f0 = rg.Point3d(xc, f_y, z_counter_top)
    add_part(parts, "hardware", make_cyl(p_f0, rg.Vector3d.ZAxis, 1.0, 1.2))
    add_part(parts, "hardware", make_cyl(p_f0 + rg.Vector3d(0, 0, 1.2), rg.Vector3d.ZAxis, 0.55, 8.5))
    # Side mixer lever
    add_part(parts, "hardware", make_cyl(p_f0 + rg.Vector3d(1.0, 0, 2.5), rg.Vector3d.XAxis, 0.22, 2.8))

    if not fast:
        # Curved Gooseneck Spout
        p_a = p_f0 + rg.Vector3d(0, 0, 9.7)
        p_b = p_f0 + rg.Vector3d(0, 3.8, 13.5)
        p_c = p_f0 + rg.Vector3d(0, 7.8, 9.2)
        spout_crv = rg.Curve.CreateInterpolatedCurve([p_a, p_b, p_c], 3)
        if spout_crv:
            try:
                pipes = rg.Brep.CreatePipe(spout_crv, 0.52, False, rg.PipeCapMode.Flat, True, 0.05, 0.02)
                if pipes:
                    for pb in pipes:
                        add_part(parts, "hardware", pb)
            except Exception:
                pass
    else:
        add_part(parts, "hardware", mk_box(xc - 0.5, xc + 0.5, f_y, f_y + 7.5, z_counter_top + 9.0, z_counter_top + 10.2))

    return parts, (sx0, sx1, sy0, sy1)


def build_cooktop_and_hood_assembly(xc, yc, z_counter_top, z_upper_bot, z_upper_top, bay_w, base_d, wall_d, light_style, fast):
    """Builds a 4-Zone Glass Induction Cooktop on the counter + Architectural Chimney Range Hood above."""
    parts = []
    hob_w = min(bay_w - 3.0, 28.0)
    hob_d = min(base_d - 5.0, 19.0)
    hx0, hx1 = xc - hob_w * 0.5, xc + hob_w * 0.5
    hy0, hy1 = yc - hob_d * 0.5, yc + hob_d * 0.5

    # Ceramic Black Glass Cooktop Plate + 4 Induction Burner Rings
    add_part(parts, "glass", mk_box(hx0, hx1, hy0, hy1, z_counter_top, z_counter_top + 0.32))
    if not fast:
        for bx in (-hob_w * 0.24, hob_w * 0.24):
            for by in (-hob_d * 0.24, hob_d * 0.24):
                add_part(parts, "hardware", make_cyl(rg.Point3d(xc + bx, yc + by, z_counter_top + 0.32), rg.Vector3d.ZAxis, 3.2, 0.06))

    # Overhead Extractor Range Hood Canopy + Flue Chimney
    if z_upper_top > z_upper_bot + 4.0:
        canopy_h = 3.5
        hood_d = min(base_d * 0.82, max(wall_d + 4.0, 18.0))
        add_part(parts, "hardware", mk_box(xc - bay_w * 0.49, xc + bay_w * 0.49, 0.0, hood_d, z_upper_bot, z_upper_bot + canopy_h))
        flue_w = min(11.0, bay_w * 0.42)
        flue_d = min(10.0, hood_d * 0.65)
        add_part(parts, "hardware", mk_box(xc - flue_w * 0.5, xc + flue_w * 0.5, 0.0, flue_d, z_upper_bot + canopy_h, z_upper_top))
        # Warm-Yellow LED Strip under Range Hood Canopy
        if light_style != 5:
            add_part(parts, "led_yellow", mk_box(xc - bay_w * 0.42, xc + bay_w * 0.42, hood_d - 2.5, hood_d - 1.2, z_upper_bot - 0.25, z_upper_bot))

    return parts


def build_countertop_with_sink_cutout(x0, x1, y0, y1, z0, z1, sink_cutout, waterfall_left, waterfall_right, z_floor):
    """Builds the stone countertop slab (with an exact rectangular cutout around the undermount sink if present) and optional waterfall end legs."""
    parts = []
    ct_t = z1 - z0
    if sink_cutout is None:
        add_part(parts, "counter", mk_box(x0, x1, y0, y1, z0, z1))
    else:
        sx0, sx1, sy0, sy1 = sink_cutout
        # Left of sink, Right of sink, Back of sink, Front of sink
        if sx0 > x0:
            add_part(parts, "counter", mk_box(x0, sx0, y0, y1, z0, z1))
        if x1 > sx1:
            add_part(parts, "counter", mk_box(sx1, x1, y0, y1, z0, z1))
        if sy0 > y0:
            add_part(parts, "counter", mk_box(sx0, sx1, y0, sy0, z0, z1))
        if y1 > sy1:
            add_part(parts, "counter", mk_box(sx0, sx1, sy1, y1, z0, z1))

    if waterfall_left:
        add_part(parts, "counter", mk_box(x0 - ct_t, x0, y0, y1, z_floor, z1))
    if waterfall_right:
        add_part(parts, "counter", mk_box(x1, x1 + ct_t, y0, y1, z_floor, z1))

    return parts


def build_kitchen_run_segment(run_len, S, is_island=False, include_tall=True, fast=False):
    """
    Builds a complete straight modular kitchen run of length `run_len` along +X (Y = 0 at back wall, +Y forward).
    Includes Tall Pantry/Oven Towers, Base Cabinets, Toe-Kick Plinth + Yellow LED, Stone Countertop,
    Sink/Cooktop, Backsplash, Wall Upper Cabinets, Loft Bulkhead, and Warm-Yellow LED Lighting.
    """
    parts = []
    c_type = int(S["cabinet_type"])

    mod_w = max(12.0, float(S["module_w"]))
    counter_h = float(S["counter_h"])
    base_d = float(S["base_depth"])
    tk_h = float(S["toekick_h"])
    tk_rec = float(S["toekick_recess"])
    splash_h = float(S["backsplash_h"])
    wall_h = float(S["wall_cab_h"])
    wall_d = float(S["wall_cab_d"])
    tall_h = float(S["tall_cab_h"])
    loft_h = float(S["loft_h"]) if S["include_loft"] else 0.0

    tc = float(S["carcass_t"])
    ts = float(S["shutter_t"])
    tb = float(S["back_t"])
    gap = float(S["reveal_gap"])
    ct_t = float(S["counter_t"])
    ct_over = float(S["counter_overhang"])
    bar_over = float(S["bar_overhang"]) if is_island else 0.0
    led_w = float(S["led_strip_w"])

    door_style = int(S["door_style"])
    handle_style = int(S["handle_style"])
    light_style = int(S["light_style"])
    open_30 = bool(S["open_doors_30"])
    wf_edges = bool(S["waterfall_edges"])

    has_base = is_island or (c_type in (0, 1, 2, 4, 6, 7))
    has_uppers = (not is_island) and (c_type in (0, 1, 3, 6, 7))
    has_tall_only = (c_type == 5)

    n_total_bays = max(1, int(round(run_len / mod_w)))
    bay_w = run_len / float(n_total_bays)

    # Determine how many bays on the right end are Tall Pantry / Oven Towers
    if has_tall_only:
        n_tall = n_total_bays
    elif is_island or not include_tall or c_type in (2, 3, 4):
        n_tall = 0
    else:
        n_tall = min(int(S["tall_count"]), max(0, n_total_bays - 2))

    n_work_bays = n_total_bays - n_tall
    x_work_end = n_work_bays * bay_w

    z_carcass_bot = tk_h
    z_carcass_top = counter_h - ct_t
    z_counter_top = counter_h
    z_upper_bot = counter_h + splash_h
    z_upper_top = max(z_upper_bot + wall_h, tall_h) if c_type == 7 else (z_upper_bot + wall_h)
    z_tall_top = max(tall_h, z_upper_top)

    # 1. RECESSED TOE-KICK PLINTH & WARM-YELLOW PLINTH LED STRIP
    if (has_base or n_tall > 0) and tk_h > 0.5:
        y_tk_front = base_d - tk_rec
        add_part(parts, "toekick", mk_box(0.0, run_len, 0.0, y_tk_front, 0.0, tk_h))
        if light_style in (0, 4):
            add_part(parts, "led_yellow", mk_box(0.0, run_len, y_tk_front, y_tk_front + led_w, tk_h - 0.55, tk_h))

    # 2. BASE CABINETS, DRAWER BANKS, SINK & COOKTOP
    sink_cutout = None
    sink_bay_idx = -1
    hob_bay_idx = -1

    if has_base and n_work_bays > 0:
        if S["include_sink"] and n_work_bays >= 1:
            sink_bay_idx = min(1, n_work_bays - 1)
        if S["include_cooktop"] and n_work_bays >= 3:
            hob_bay_idx = min(n_work_bays - 2, max(2, n_work_bays // 2 + 1))
        elif S["include_cooktop"] and n_work_bays == 2 and sink_bay_idx != 1:
            hob_bay_idx = 1

        # Gola horizontal J-channel recess bar across base cabinets
        if handle_style == 1:
            add_part(parts, "hardware", mk_box(0.0, x_work_end, base_d - 0.8, base_d, z_carcass_top - 1.1, z_carcass_top))

        for b_i in range(n_work_bays):
            bx0 = b_i * bay_w
            bx1 = (b_i + 1) * bay_w
            is_sink = (b_i == sink_bay_idx)
            is_hob = (b_i == hob_bay_idx)
            is_drawer_bay = (S["include_drawers"] and not is_sink and ((b_i % 2 == 0) or is_hob))

            n_sh = 0 if (is_sink or is_drawer_bay) else int(S["base_shelves"])
            parts.extend(build_single_carcass_box(
                bx0, bx1, 0.0, base_d, z_carcass_bot, z_carcass_top,
                tc, tb, n_sh, False, light_style, led_w, fast
            ))

            # Shutters / Drawer Fronts occupy y in [base_d, base_d + ts]
            dx0 = bx0 + gap
            dx1 = bx1 - gap
            dz0 = z_carcass_bot + gap
            dz1 = z_carcass_top - gap

            if is_drawer_bay:
                n_drw = clamp(int(S["drawer_count"]), 2, 5)
                # Top cutlery drawer is shallower (22%), lower pot drawers share remaining height
                h_tot_d = dz1 - dz0
                z_curr = dz1
                for d_idx in range(n_drw):
                    frac = 0.22 if d_idx == 0 else (0.78 / float(n_drw - 1))
                    d_h = h_tot_d * frac
                    z_next = z_curr - d_h
                    parts.extend(build_shutter_panel(
                        dx0, dx1, base_d, base_d + ts, z_next + gap * 0.5, z_curr - gap * 0.5,
                        door_style if door_style != 3 else 0, handle_style, True, True, False, False, fast
                    ))
                    z_curr = z_next
            else:
                # Double doors if bay_w >= 21", else single door
                if bay_w >= 21.0:
                    xm = 0.5 * (bx0 + bx1)
                    parts.extend(build_shutter_panel(
                        dx0, xm - gap * 0.5, base_d, base_d + ts, dz0, dz1,
                        door_style if door_style != 3 else 0, handle_style, False, True, False, open_30, fast
                    ))
                    parts.extend(build_shutter_panel(
                        xm + gap * 0.5, dx1, base_d, base_d + ts, dz0, dz1,
                        door_style if door_style != 3 else 0, handle_style, False, False, False, open_30, fast
                    ))
                else:
                    parts.extend(build_shutter_panel(
                        dx0, dx1, base_d, base_d + ts, dz0, dz1,
                        door_style if door_style != 3 else 0, handle_style, False, (b_i % 2 == 0), False, open_30, fast
                    ))

            # Undermount Sink + Faucet
            if is_sink:
                s_parts, sink_cutout = build_sink_and_faucet_assembly(
                    0.5 * (bx0 + bx1), base_d * 0.52, z_counter_top, bay_w, base_d, fast
                )
                parts.extend(s_parts)

            # Induction Cooktop + Range Hood
            if is_hob:
                parts.extend(build_cooktop_and_hood_assembly(
                    0.5 * (bx0 + bx1), base_d * 0.52, z_counter_top,
                    z_upper_bot, z_upper_top, bay_w, base_d, wall_d, light_style, fast
                ))

        # 3. STONE COUNTERTOP (With Breakfast Overhang on Back if Island, and Waterfall Edges if Checked)
        y_ct_0 = -bar_over if is_island else 0.0
        y_ct_1 = base_d + ts + ct_over
        parts.extend(build_countertop_with_sink_cutout(
            0.0, x_work_end, y_ct_0, y_ct_1, z_carcass_top, z_counter_top,
            sink_cutout, wf_edges, wf_edges and (n_tall == 0), 0.0
        ))

        # Island back knee-wall panel & support brackets
        if is_island:
            add_part(parts, "shutter", mk_box(0.0, x_work_end, -ts, 0.0, tk_h, z_carcass_top))

        # 4. FULL-HEIGHT STONE BACKSPLASH SLAB
        if (not is_island) and S["include_backsplash"] and splash_h > 1.0:
            add_part(parts, "backsplash", mk_box(0.0, x_work_end, 0.0, 0.75, z_counter_top, z_upper_bot))

    # 5. WALL UPPER CABINETS & UNDER-CABINET WARM-YELLOW LED LIGHTING
    if has_uppers and n_work_bays > 0:
        eff_wall_d = base_d if c_type == 7 else wall_d
        for b_i in range(n_work_bays):
            if b_i == hob_bay_idx and has_base and S["include_cooktop"]:
                # Range hood occupies this upper bay
                continue
            bx0 = b_i * bay_w
            bx1 = (b_i + 1) * bay_w
            # Use glass display doors on alternating upper bays if door_style == 3 (or middle bays)
            use_glass = (door_style == 3) or (door_style in (0, 1) and (b_i % 2 == 1) and n_work_bays >= 3)
            u_dstyle = 3 if use_glass else door_style

            parts.extend(build_single_carcass_box(
                bx0, bx1, 0.0, eff_wall_d, z_upper_bot, z_upper_top,
                tc, tb, int(S["wall_shelves"]), use_glass, light_style, led_w, fast
            ))

            dx0 = bx0 + gap
            dx1 = bx1 - gap
            dz0 = z_upper_bot + gap
            dz1 = z_upper_top - gap

            if bay_w >= 21.0:
                xm = 0.5 * (bx0 + bx1)
                parts.extend(build_shutter_panel(
                    dx0, xm - gap * 0.5, eff_wall_d, eff_wall_d + ts, dz0, dz1,
                    u_dstyle, handle_style, False, True, True, open_30, fast
                ))
                parts.extend(build_shutter_panel(
                    xm + gap * 0.5, dx1, eff_wall_d, eff_wall_d + ts, dz0, dz1,
                    u_dstyle, handle_style, False, False, True, open_30, fast
                ))
            else:
                parts.extend(build_shutter_panel(
                    dx0, dx1, eff_wall_d, eff_wall_d + ts, dz0, dz1,
                    u_dstyle, handle_style, False, (b_i % 2 == 0), True, open_30, fast
                ))

            # Warm-Yellow Under-Cabinet LED Lighting (Linear Channel or Recessed Puck Downlights)
            if light_style in (0, 1):
                y_led = eff_wall_d * 0.68
                add_part(parts, "led_yellow", mk_box(bx0 + 0.5, bx1 - 0.5, y_led - led_w * 0.5, y_led + led_w * 0.5, z_upper_bot - 0.32, z_upper_bot))
            elif light_style == 2:
                xc_b = 0.5 * (bx0 + bx1)
                add_part(parts, "led_yellow", make_cyl(rg.Point3d(xc_b, eff_wall_d * 0.55, z_upper_bot - 0.25), rg.Vector3d.ZAxis, 1.6, 0.25))

    # 6. TALL PANTRY & BUILT-IN OVEN / MICROWAVE TOWER UNITS
    if n_tall > 0:
        for t_i in range(n_tall):
            tx0 = x_work_end + t_i * bay_w
            tx1 = tx0 + bay_w
            parts.extend(build_single_carcass_box(
                tx0, tx1, 0.0, base_d, z_carcass_bot, z_tall_top,
                tc, tb, 4, (door_style == 3), light_style, led_w, fast
            ))

            dx0 = tx0 + gap
            dx1 = tx1 - gap
            # First tall unit includes built-in eye-level Oven & Microwave appliance stack!
            if t_i == 0 and c_type in (0, 1, 5, 6):
                z_bot_d1 = z_carcass_bot + gap
                z_oven_0 = counter_h - 8.0
                z_oven_1 = z_oven_0 + 24.0
                z_micro_1 = z_oven_1 + 15.0
                z_top_d2 = z_tall_top - gap

                # Lower pot drawer below oven
                parts.extend(build_shutter_panel(
                    dx0, dx1, base_d, base_d + ts, z_bot_d1, z_oven_0 - gap,
                    door_style if door_style != 3 else 0, handle_style, True, True, False, False, fast
                ))
                # Built-in Oven stainless frame + dark glass window + handle
                add_part(parts, "hardware", mk_box(dx0, dx1, base_d, base_d + ts, z_oven_0, z_oven_1))
                add_part(parts, "glass", mk_box(dx0 + 2.0, dx1 - 2.0, base_d + ts, base_d + ts + 0.15, z_oven_0 + 2.5, z_oven_1 - 4.0))
                add_part(parts, "hardware", mk_box(dx0 + 2.5, dx1 - 2.5, base_d + ts + 0.8, base_d + ts + 1.4, z_oven_1 - 2.2, z_oven_1 - 1.6))

                # Built-in Microwave above oven
                add_part(parts, "hardware", mk_box(dx0, dx1, base_d, base_d + ts, z_oven_1 + gap, z_micro_1))
                add_part(parts, "glass", mk_box(dx0 + 2.0, dx1 - 5.0, base_d + ts, base_d + ts + 0.15, z_oven_1 + 2.0, z_micro_1 - 2.0))

                # Upper pantry door above microwave
                if z_top_d2 > z_micro_1 + 4.0:
                    parts.extend(build_shutter_panel(
                        dx0, dx1, base_d, base_d + ts, z_micro_1 + gap, z_top_d2,
                        door_style, handle_style, False, True, True, open_30, fast
                    ))
            else:
                # Full-height larder pantry doors (split at counter_h)
                parts.extend(build_shutter_panel(
                    dx0, dx1, base_d, base_d + ts, z_carcass_bot + gap, counter_h - gap * 0.5,
                    door_style, handle_style, False, True, False, open_30, fast
                ))
                parts.extend(build_shutter_panel(
                    dx0, dx1, base_d, base_d + ts, counter_h + gap * 0.5, z_tall_top - gap,
                    door_style, handle_style, False, True, True, open_30, fast
                ))

    # 7. TOP LOFT / CEILING SOFFIT BULKHEAD & WARM-YELLOW CROWN COVE LED
    if (not is_island) and loft_h > 1.0 and (has_uppers or n_tall > 0):
        z_loft_0 = z_upper_top
        z_loft_1 = z_loft_0 + loft_h
        loft_d = base_d if n_tall == n_total_bays else (wall_d + 2.0)
        add_part(parts, "carcass", mk_box(0.0, run_len, 0.0, loft_d, z_loft_0, z_loft_1))
        add_part(parts, "shutter", mk_box(0.0, run_len, loft_d, loft_d + ts, z_loft_0 + 0.5, z_loft_1))
        if light_style == 0:
            # Warm-Yellow Crown Cove LED Strip along the soffit lip
            add_part(parts, "led_yellow", mk_box(0.0, run_len, loft_d - 0.5, loft_d + ts, z_loft_0, z_loft_0 + 0.45))

    return parts


def build_kitchen_system(base_plane_doc, S, doc=None, fast=False):
    """
    Constructs the complete 3D Modular Kitchen System (Straight, L-Shape Corner, Island, or Galley)
    in inch space and transforms it to `base_plane_doc` in document units.
    """
    if doc is None:
        doc = Rhino.RhinoDoc.ActiveDoc
    u = unit_scale(doc)

    c_type = int(S.get("cabinet_type", 0))
    main_len = max(24.0, float(S["total_length"]))
    ret_len = max(24.0, float(S["return_length"]))
    base_d = float(S["base_depth"])

    local_parts = []

    if c_type == 4:
        # Standalone Kitchen Island
        local_parts.extend(build_kitchen_run_segment(main_len, S, is_island=True, include_tall=False, fast=fast))

    elif c_type == 1:
        # L-Shape Corner Kitchen Run: Main Wall Run + 90-degree Return Wing
        local_parts.extend(build_kitchen_run_segment(main_len, S, is_island=False, include_tall=True, fast=fast))
        wing_s = dict(S)
        wing_s["include_sink"] = False
        wing_s["include_cooktop"] = False
        wing_len = max(24.0, ret_len - base_d)
        wing_raw = build_kitchen_run_segment(wing_len, wing_s, is_island=False, include_tall=False, fast=fast)

        turn_right = (int(S.get("corner_turn", 0)) == 0)
        if turn_right:
            # Wing starts at (main_len, base_d) and runs +Y along the right wall (inward is -X)
            wing_pl = rg.Plane(rg.Point3d(main_len, base_d, 0.0), rg.Vector3d.YAxis, -rg.Vector3d.XAxis)
        else:
            # Wing starts at (0, base_d + wing_len) and runs -Y back to (0, base_d) (inward is +X)
            wing_pl = rg.Plane(rg.Point3d(0.0, base_d + wing_len, 0.0), -rg.Vector3d.YAxis, rg.Vector3d.XAxis)

        xform_w = rg.Transform.PlaneToPlane(rg.Plane.WorldXY, wing_pl)
        for kind, b in wing_raw:
            nb = b.DuplicateBrep()
            nb.Transform(xform_w)
            local_parts.append((kind, nb))

    elif c_type == 6:
        # Galley / Parallel Kitchen: Main Wall Assembly + Parallel Front Island (48" aisle clearance)
        local_parts.extend(build_kitchen_run_segment(main_len, S, is_island=False, include_tall=True, fast=fast))
        isl_s = dict(S)
        isl_s["include_cooktop"] = False
        isl_raw = build_kitchen_run_segment(ret_len, isl_s, is_island=True, include_tall=False, fast=fast)
        x_isl_0 = (main_len - ret_len) * 0.5
        y_isl_0 = base_d + 48.0 + base_d
        # Rotate island 180 deg so working drawers/sink face the main kitchen wall across the 48" aisle
        isl_pl = rg.Plane(rg.Point3d(x_isl_0 + ret_len, y_isl_0, 0.0), -rg.Vector3d.XAxis, -rg.Vector3d.YAxis)
        xform_i = rg.Transform.PlaneToPlane(rg.Plane.WorldXY, isl_pl)
        for kind, b in isl_raw:
            nb = b.DuplicateBrep()
            nb.Transform(xform_i)
            local_parts.append((kind, nb))

    else:
        # Modes 0, 2, 3, 5, 7
        local_parts.extend(build_kitchen_run_segment(main_len, S, is_island=False, include_tall=True, fast=fast))

    # Scale from internal inches to active document units and map to base_plane_doc
    scale_xform = rg.Transform.Scale(rg.Point3d.Origin, u)
    plane_xform = rg.Transform.PlaneToPlane(rg.Plane.WorldXY, base_plane_doc)
    full_xform = plane_xform * scale_xform

    world_parts = []
    for kind, b in local_parts:
        if b and b.IsValid:
            nb = b.DuplicateBrep()
            nb.Transform(full_xform)
            world_parts.append((kind, nb))

    return world_parts


# ============================================================
# BAKING, LAYERS, MATERIALS & NON-DESTRUCTIVE METADATA
# ============================================================
def get_or_create_material(doc, name, diffuse_color, transparency=0.0, emission_color=None):
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
    if emission_color is not None:
        try:
            mat.EmissionColor = emission_color
        except Exception:
            pass
    return doc.Materials.Add(mat)


def bake_kitchen_cabinet(doc, base_plane_doc, S, u=1.0, edit_target_ids=None):
    parts = build_kitchen_system(base_plane_doc, S, doc=doc, fast=False)
    if not parts:
        return []

    c_mat = CARCASS_FINISHES[S.get("carcass_finish", 0)]
    s_mat = SHUTTER_FINISHES[S.get("shutter_finish", 0)]
    t_mat = COUNTER_FINISHES[S.get("counter_finish", 0)]
    h_mat = HARDWARE_FINISHES[S.get("hw_finish", 0)]
    led_col = rgb_to_color(WARM_YELLOW_LED_RGB)

    root_name = "ARCH_KITCHEN"
    sublayers = [
        "CARCASS_BOARD",
        "SHUTTER_FRONT",
        "COUNTERTOP_STONE",
        "BACKSPLASH",
        "GLASS_INSERT",
        "HARDWARE_SINK",
        "TOE_KICK",
        "LED_YELLOW_LIGHT",
    ]
    layer_indices = {}

    root_idx = doc.Layers.FindByFullPath(root_name, -1)
    if root_idx < 0:
        root_layer = rdo.Layer()
        root_layer.Name = root_name
        root_idx = doc.Layers.Add(root_layer)
    root_id = doc.Layers[root_idx].Id

    kind_to_sub = {
        "carcass":    "CARCASS_BOARD",
        "shutter":    "SHUTTER_FRONT",
        "counter":    "COUNTERTOP_STONE",
        "backsplash": "BACKSPLASH",
        "glass":      "GLASS_INSERT",
        "hardware":   "HARDWARE_SINK",
        "toekick":    "TOE_KICK",
        "led_yellow": "LED_YELLOW_LIGHT",
    }

    sub_configs = {
        "CARCASS_BOARD":    ("Kitchen Carcass " + c_mat[0], rgb_to_color(c_mat[1]), 0.0, None),
        "SHUTTER_FRONT":    ("Kitchen Shutter " + s_mat[0], rgb_to_color(s_mat[1]), 0.0, None),
        "COUNTERTOP_STONE": ("Kitchen Counter " + t_mat[0], rgb_to_color(t_mat[1]), 0.0, None),
        "BACKSPLASH":       ("Kitchen Backsplash " + t_mat[0], rgb_to_color(t_mat[1]), 0.0, None),
        "GLASS_INSERT":     ("Kitchen Tempered Glass", System.Drawing.Color.FromArgb(175, 220, 238), 0.55, None),
        "HARDWARE_SINK":    ("Kitchen Hardware " + h_mat[0], rgb_to_color(h_mat[1]), 0.0, None),
        "TOE_KICK":         ("Kitchen ToeKick Plinth", System.Drawing.Color.FromArgb(40, 42, 46), 0.0, None),
        "LED_YELLOW_LIGHT": ("Kitchen Warm Yellow LED 3000K", led_col, 0.0, led_col),
    }

    for sub in sublayers:
        path = "{}::{}".format(root_name, sub)
        idx = doc.Layers.FindByFullPath(path, -1)
        if idx < 0:
            nl = rdo.Layer()
            nl.Name = sub
            nl.ParentLayerId = root_id
            m_name, m_col, trans, emis = sub_configs[sub]
            nl.Color = m_col
            mat_idx = get_or_create_material(doc, m_name, m_col, trans, emis)
            nl.RenderMaterialIndex = mat_idx
            idx = doc.Layers.Add(nl)
        layer_indices[sub] = idx

    if edit_target_ids:
        for gid in edit_target_ids:
            try:
                doc.Objects.Delete(gid, True)
            except Exception:
                pass

    orig_in = rg.Point3d(
        base_plane_doc.Origin.X / u,
        base_plane_doc.Origin.Y / u,
        base_plane_doc.Origin.Z / u,
    )
    base_plane_in = rg.Plane(orig_in, base_plane_doc.XAxis, base_plane_doc.YAxis)
    state_json = encode_state(base_plane_in, S)

    ids = []
    for idx, (kind, brep) in enumerate(parts):
        if not brep or not brep.IsValid:
            continue
        sub_name = kind_to_sub.get(kind, "CARCASS_BOARD")
        l_idx = layer_indices.get(sub_name, root_idx)
        c_pt = _brep_center(brep)

        attr = rdo.ObjectAttributes()
        attr.LayerIndex = l_idx
        attr.ColorSource = rdo.ObjectColorSource.ColorFromLayer
        attr.MaterialSource = rdo.ObjectMaterialSource.MaterialFromLayer
        attr.Name = "Kitchen_{}".format(sub_name)
        try:
            attr.SetUserString(METADATA_KEY, state_json)
            attr.SetUserString(ITEM_INDEX_KEY, str(int(idx)))
            if c_pt:
                attr.SetUserString(ITEM_CENTER_KEY, json.dumps(_point_to_data(c_pt)))
        except Exception:
            pass

        oid = doc.Objects.AddBrep(brep, attr)
        if oid and oid != System.Guid.Empty:
            ids.append(oid)

    if ids:
        try:
            g_idx = doc.Groups.Add()
            doc.Groups.AddToGroup(g_idx, ids)
        except Exception:
            pass

    return ids


# ============================================================
# PRESETS SYSTEM
# ============================================================
def _get_preset_path():
    base = os.environ.get("APPDATA") or os.path.expanduser("~") or os.getcwd()
    folder = os.path.join(base, PRESET_FOLDER_NAME)
    if not os.path.isdir(folder):
        try:
            os.makedirs(folder)
        except Exception:
            pass
    return os.path.join(folder, PRESET_FILE_NAME)


def load_presets():
    p = _get_preset_path()
    if not os.path.exists(p):
        return {}
    try:
        with codecs.open(p, "r", "utf-8") as f:
            data = json.load(f)
        return {str(k): normalize_settings(v) for k, v in data.items() if isinstance(v, dict)}
    except Exception:
        return {}


def save_presets(presets):
    p = _get_preset_path()
    try:
        clean = {str(k): normalize_settings(v) for k, v in presets.items()}
        with codecs.open(p, "w", "utf-8") as f:
            f.write(json.dumps(clean, indent=2, sort_keys=True))
        return True
    except Exception:
        return False


# ============================================================
# LIVE DISPLAY CONDUIT & INTERACTIVE VIEWPORT GETTER
# ============================================================
class KitchenPreviewConduit(rd.DisplayConduit):
    def __init__(self, wireframe_only=False):
        super(KitchenPreviewConduit, self).__init__()
        self.preview_breps = []
        self.wireframe_only = wireframe_only
        self.materials = {}
        self._update_materials(default_settings())

    def _update_materials(self, S):
        c_col = rgb_to_color(CARCASS_FINISHES[S.get("carcass_finish", 0)][1])
        s_col = rgb_to_color(SHUTTER_FINISHES[S.get("shutter_finish", 0)][1])
        t_col = rgb_to_color(COUNTER_FINISHES[S.get("counter_finish", 0)][1])
        h_col = rgb_to_color(HARDWARE_FINISHES[S.get("hw_finish", 0)][1])
        led_col = rgb_to_color(WARM_YELLOW_LED_RGB)
        led_mat = rd.DisplayMaterial(led_col)
        try:
            led_mat.Emission = led_col
        except Exception:
            pass

        self.materials = {
            "carcass":    rd.DisplayMaterial(c_col),
            "shutter":    rd.DisplayMaterial(s_col),
            "counter":    rd.DisplayMaterial(t_col),
            "backsplash": rd.DisplayMaterial(t_col),
            "glass":      rd.DisplayMaterial(System.Drawing.Color.FromArgb(175, 220, 238), 0.55),
            "hardware":   rd.DisplayMaterial(h_col),
            "toekick":    rd.DisplayMaterial(System.Drawing.Color.FromArgb(40, 42, 46)),
            "led_yellow": led_mat,
        }

    def set_finishes(self, S):
        self._update_materials(S)

    def CalculateBoundingBox(self, e):
        try:
            bbox = rg.BoundingBox.Empty
            for kind, b in self.preview_breps:
                if b and b.IsValid:
                    bbox = rg.BoundingBox.Union(bbox, b.GetBoundingBox(False))
            if bbox.IsValid:
                e.IncludeBoundingBox(bbox)
        except Exception:
            pass

    def PostDrawObjects(self, e):
        try:
            for kind, b in self.preview_breps:
                if not b or not b.IsValid:
                    continue
                if kind == "led_yellow":
                    e.Display.DrawBrepShaded(b, self.materials["led_yellow"])
                    e.Display.DrawBrepWires(b, System.Drawing.Color.Gold, 2)
                elif self.wireframe_only:
                    col = System.Drawing.Color.Gold if kind == "counter" else System.Drawing.Color.DeepSkyBlue
                    e.Display.DrawBrepWires(b, col, 1)
                else:
                    mat = self.materials.get(kind, self.materials["carcass"])
                    e.Display.DrawBrepShaded(b, mat)
                    e.Display.DrawBrepWires(b, System.Drawing.Color.FromArgb(45, 45, 50), 1)
        except Exception:
            pass


class KitchenRunPointGetter(ric.GetPoint):
    """Live 3D Kitchen wireframe preview + front direction arrow while picking the 2nd wall point."""
    def __init__(self, p1_doc, settings, u):
        super(KitchenRunPointGetter, self).__init__()
        self.p1 = rg.Point3d(p1_doc)
        self.u = u if u > 0 else 1.0
        self.S = dict(settings)
        self.S["fast_preview"] = True

    def OnDynamicDraw(self, e):
        try:
            pt = e.CurrentPoint
            p2 = rg.Point3d(pt.X, pt.Y, self.p1.Z)
            dist_doc = self.p1.DistanceTo(p2)
            len_in = dist_doc / self.u
            if len_in < 24.0:
                e.Display.DrawLine(self.p1, p2, System.Drawing.Color.Gold, 2)
                return

            x_axis = _safe_unitize(p2 - self.p1, rg.Vector3d.XAxis)
            y_axis = _safe_unitize(rg.Vector3d.CrossProduct(rg.Vector3d.ZAxis, x_axis), rg.Vector3d.YAxis)
            pl = rg.Plane(self.p1, x_axis, y_axis)

            e.Display.DrawLine(self.p1, p2, System.Drawing.Color.Gold, 3)
            mid_pt = 0.5 * (self.p1 + p2)
            e.Display.DrawDirectionArrow(mid_pt, y_axis * (30.0 * self.u), System.Drawing.Color.LimeGreen)

            temp_s = dict(self.S)
            temp_s["total_length"] = clamp(len_in, 24.0, 600.0)
            parts = build_kitchen_system(pl, temp_s, fast=True)
            for kind, brep in parts:
                if brep and brep.IsValid:
                    col = System.Drawing.Color.Gold if kind in ("led_yellow", "counter") else System.Drawing.Color.DeepSkyBlue
                    e.Display.DrawBrepWires(brep, col, 1)
        except Exception:
            pass


# ============================================================
# ETO NUMERIC FIELD WRAPPER
# ============================================================
class NumField(object):
    def __init__(self, key, label, default, mn, mx, is_int, value, unit_name="in", scale_from_inch=1.0):
        self.key = key
        self.mn = mn
        self.mx = mx
        self.is_int = is_int
        self.unit_name = unit_name
        self.scale_from_inch = scale_from_inch
        self.is_length = (key not in NON_LENGTH_KEYS and not is_int)
        self.last_inch = value
        disp_val = value * (scale_from_inch if self.is_length else 1.0)
        self.textbox = forms.TextBox()
        self.textbox.Text = format_cab_length(disp_val, unit_name, is_int)

    def value(self):
        try:
            txt = self.textbox.Text.strip()
            if self.is_length:
                val_in_unit = parse_cab_length(txt, self.unit_name)
                val_inch = val_in_unit / self.scale_from_inch
            else:
                val_inch = float(txt)
            val_inch = clamp(val_inch, self.mn, self.mx)
            self.last_inch = int(round(val_inch)) if self.is_int else val_inch
        except Exception:
            pass
        return self.last_inch

    def set_value(self, v):
        v = clamp(v, self.mn, self.mx)
        self.last_inch = int(round(v)) if self.is_int else v
        disp_val = self.last_inch * (self.scale_from_inch if self.is_length else 1.0)
        self.textbox.Text = format_cab_length(disp_val, self.unit_name, self.is_int)


def dl_add(layout, control, x_expand=False, y_expand=False):
    try:
        layout.Add(control, x_expand, y_expand)
    except TypeError:
        layout.Add(control, System.Nullable[bool](x_expand), System.Nullable[bool](y_expand))


# ============================================================
# TALL SINGLE-COLUMN ETO DIALOG WITH UPPER ERGONOMIC BANNER
# ============================================================
class ModernKitchenDialog(forms.Dialog[bool]):
    def __init__(self):
        super(ModernKitchenDialog, self).__init__()
        self._initialized = False
        self._preview_closed = False
        self._suppress_preview = True
        self.final_settings = None
        self.conduit = None

    def Initialize(self, base_plane_doc, initial_settings=None, is_edit=False):
        if self._initialized:
            return
        self._initialized = True

        unit_sys, unit_name, scale_from_inch = get_doc_unit_info()
        self.unit_name = unit_name
        self.scale_from_inch = scale_from_inch

        title_prefix = "Edit Ergonomic Kitchen Cabinet" if is_edit else "Modern Kitchen Cabinet & Millwork Generator"
        self.Title = "%s [%s]" % (title_prefix, unit_name)
        self.Padding = drawing.Padding(10)
        self.Resizable = True
        try:
            self.Topmost = True
        except Exception:
            pass
        self.ClientSize = drawing.Size(540, 820)
        self.base_plane_doc = base_plane_doc
        self.is_edit = is_edit
        self._preview_closed = False
        self._suppress_preview = True

        prev = sc.sticky.get(CONDUIT_KEY)
        if prev is not None:
            try:
                prev.Enabled = False
            except Exception:
                pass
        self.conduit = KitchenPreviewConduit()
        self.conduit.Enabled = True
        sc.sticky[CONDUIT_KEY] = self.conduit

        s = normalize_settings(initial_settings) if initial_settings else get_initial_settings()
        self.presets = load_presets()

        self.fields = {}
        self.labels = {}
        for k, l, d, mn, mx, ii in NUM_FIELDS:
            disp_label = update_label_unit(l, unit_name)
            self.fields[k] = NumField(k, disp_label, d, mn, mx, ii, s[k], unit_name, scale_from_inch)
            self.labels[k] = disp_label

        self.dds = {}
        for k, l, d, names in DD_FIELDS:
            dd = forms.DropDown()
            dd.DataStore = list(names)
            dd.SelectedIndex = int(s[k])
            self.dds[k] = dd
            self.labels[k] = l

        self.cbs = {}
        for k, l, d in CB_FIELDS:
            cb = forms.CheckBox()
            cb.Text = l
            cb.Checked = bool(s[k])
            self.cbs[k] = cb

        self.lbl_calc_info = forms.Label(Text="")
        try:
            self.lbl_calc_info.TextColor = drawing.Colors.DarkBlue
        except Exception:
            pass

        self.dd_preset = forms.DropDown()
        self.dd_preset.Width = 170
        self.txt_preset_name = forms.TextBox()
        self.txt_preset_name.Width = 130
        self.btn_load = forms.Button(Text="Load")
        self.btn_save = forms.Button(Text="Save")
        self.btn_delete = forms.Button(Text="Delete")
        self._refresh_presets()

        main = forms.DynamicLayout()
        main.Spacing = drawing.Size(5, 4)

        # UPPER HEADING: ERGONOMIC STANDARDS & STANDARD BOARD SIZES BANNER
        self.lbl_std_ergo = forms.Label(
            Text="ERGONOMIC STANDARDS: Counter 36\" (915mm) | Base Depth 24\" (600mm) | Toe-Kick 4\"x3\" | Splash 18\" (450mm) | Upper 30\"H x 13\"D | Tall 84\""
        )
        self.lbl_std_board = forms.Label(
            Text="STANDARD BOARDS: 18mm (0.71\") Carcass/Shutter | 16mm (0.63\") MR Board | 6mm (0.24\") Back Panel | LED: 3000K Warm Yellow"
        )
        self.lbl_live_summary = forms.Label(Text="")
        try:
            self.lbl_std_ergo.Font = drawing.Font(drawing.FontFamilies.Sans, 8.2, drawing.FontStyles.Bold)
            self.lbl_std_board.Font = drawing.Font(drawing.FontFamilies.Sans, 8.2, drawing.FontStyles.Bold)
            self.lbl_live_summary.Font = drawing.Font(drawing.FontFamilies.Sans, 9.0, drawing.FontStyles.Bold)
            self.lbl_std_ergo.TextColor = drawing.Colors.DarkSlateGray
            self.lbl_std_board.TextColor = drawing.Colors.SaddleBrown
        except Exception:
            pass
        main.AddRow(self.lbl_std_ergo)
        main.AddRow(self.lbl_std_board)
        main.AddRow(self.lbl_live_summary)

        preset_load_layout = forms.DynamicLayout()
        preset_load_layout.BeginHorizontal()
        dl_add(preset_load_layout, self.dd_preset, True, False)
        dl_add(preset_load_layout, self.btn_load, False, False)
        preset_load_layout.EndHorizontal()
        main.AddRow(forms.Label(Text="Preset list:"), preset_load_layout)

        preset_save_layout = forms.DynamicLayout()
        preset_save_layout.BeginHorizontal()
        dl_add(preset_save_layout, self.txt_preset_name, True, False)
        dl_add(preset_save_layout, self.btn_save, False, False)
        dl_add(preset_save_layout, self.btn_delete, False, False)
        preset_save_layout.EndHorizontal()
        main.AddRow(forms.Label(Text="Preset name:"), preset_save_layout)

        self.tabs = forms.TabControl()

        for title, keys in TAB_LAYOUT:
            tab_layout = forms.DynamicLayout()
            tab_layout.Padding = drawing.Padding(10)
            tab_layout.Spacing = drawing.Size(5, 5)

            for key in keys:
                if key == "@calc_info":
                    tab_layout.AddRow(self.lbl_calc_info)
                elif key in self.cbs:
                    tab_layout.AddRow(self.cbs[key])
                elif key in self.dds:
                    tab_layout.AddRow(forms.Label(Text=self.labels[key]), self.dds[key])
                elif key in self.fields:
                    tab_layout.AddRow(forms.Label(Text=self.labels[key]), self.fields[key].textbox)

            dl_add(tab_layout, forms.Label(Text=""), False, True)

            scr = forms.Scrollable()
            try:
                scr.Border = getattr(forms.BorderType, "None")
            except Exception:
                pass
            scr.ExpandContentWidth = True
            scr.Content = tab_layout
            page = forms.TabPage(Text=title.replace("&&", "&"), Content=scr)
            self.tabs.Pages.Add(page)

        dl_add(main, self.tabs, True, True)

        self.lbl_status = forms.Label(Text="")
        try:
            self.lbl_status.TextColor = drawing.Colors.Red
        except Exception:
            pass
        main.AddRow(self.lbl_status)

        btn_ok = forms.Button(Text="Apply Edit" if is_edit else "Create Kitchen Cabinets")
        btn_ok.Click += self.OnOkClicked
        btn_cancel = forms.Button(Text="Cancel")
        btn_cancel.Click += self.OnCancelClicked
        self.DefaultButton = btn_ok
        self.AbortButton = btn_cancel

        b_row = forms.DynamicLayout()
        b_row.BeginHorizontal()
        dl_add(b_row, btn_ok, True, False)
        dl_add(b_row, btn_cancel, False, False)
        b_row.EndHorizontal()
        main.AddRow(b_row)

        self.Content = main

        self.Closed += self.OnDialogClosed
        for f in self.fields.values():
            f.textbox.TextChanged += self.OnAnyChanged
        for k, dd in self.dds.items():
            if k == "board_std":
                dd.SelectedIndexChanged += self.OnBoardStdChanged
            else:
                dd.SelectedIndexChanged += self.OnAnyChanged
        for cb in self.cbs.values():
            cb.CheckedChanged += self.OnAnyChanged

        self.dd_preset.SelectedIndexChanged += self.OnPresetSelected
        self.btn_load.Click += self.OnPresetLoad
        self.btn_save.Click += self.OnPresetSave
        self.btn_delete.Click += self.OnPresetDelete

        self.UpdateEnabling()
        self._suppress_preview = False
        self.UpdatePreview()

    def OnBoardStdChanged(self, sender, e):
        b_std = int(self.dds["board_std"].SelectedIndex)
        self._suppress_preview = True
        try:
            if b_std == 0:
                # 18 mm (0.71") carcass/door + 6 mm (0.24") back
                self.fields["carcass_t"].set_value(0.71)
                self.fields["shutter_t"].set_value(0.71)
                self.fields["back_t"].set_value(0.24)
            elif b_std == 1:
                # 16 mm (0.63") carcass/door + 6 mm (0.24") back
                self.fields["carcass_t"].set_value(0.63)
                self.fields["shutter_t"].set_value(0.63)
                self.fields["back_t"].set_value(0.24)
            elif b_std == 2:
                # 19 mm (0.75") plywood + 12 mm (0.47") back
                self.fields["carcass_t"].set_value(0.75)
                self.fields["shutter_t"].set_value(0.75)
                self.fields["back_t"].set_value(0.47)
            elif b_std == 3:
                # 25 mm (1.0") commercial millwork + 12 mm back
                self.fields["carcass_t"].set_value(1.00)
                self.fields["shutter_t"].set_value(0.87)
                self.fields["back_t"].set_value(0.47)
            self.UpdateEnabling()
        finally:
            self._suppress_preview = False
        self.UpdatePreview()

    def UpdateEnabling(self):
        ct = int(self.dds["cabinet_type"].SelectedIndex)
        b_std = int(self.dds["board_std"].SelectedIndex)
        ls = int(self.dds["light_style"].SelectedIndex)

        self.dds["corner_turn"].Enabled = (ct == 1)
        self.fields["return_length"].textbox.Enabled = (ct in (1, 6))
        self.fields["bar_overhang"].textbox.Enabled = (ct in (4, 6))
        self.fields["tall_count"].textbox.Enabled = (ct in (0, 1, 6, 7))

        custom_board = (b_std == 4)
        self.fields["carcass_t"].textbox.Enabled = custom_board
        self.fields["shutter_t"].textbox.Enabled = custom_board
        self.fields["back_t"].textbox.Enabled = custom_board
        self.fields["led_strip_w"].textbox.Enabled = (ls != 5)

        run_l = self.fields["total_length"].value()
        mod_w = max(12.0, self.fields["module_w"].value())
        n_bays = max(1, int(round(run_l / mod_w)))
        actual_bay = run_l / float(n_bays)
        c_h = self.fields["counter_h"].value()
        b_t = self.fields["carcass_t"].value()

        disp_l = format_cab_length(run_l * self.scale_from_inch, self.unit_name)
        disp_ch = format_cab_length(c_h * self.scale_from_inch, self.unit_name)
        disp_bt = format_cab_length(b_t * self.scale_from_inch, self.unit_name)

        self.lbl_live_summary.Text = "Active Run: {} {} ({} Bays)  |  Counter H: {} {}  |  Board: {} {}".format(
            disp_l, self.unit_name, n_bays, disp_ch, self.unit_name, disp_bt, self.unit_name
        )
        self.lbl_calc_info.Text = "Modules: {} bays @ {:.1f}\" o.c. | Work Triangle Ergonomics & Warm-Yellow 3000K LED Active".format(
            n_bays, actual_bay
        )

    def OnAnyChanged(self, sender, e):
        self.UpdateEnabling()
        self.UpdatePreview()

    def GetCurrentSettings(self):
        raw = {}
        for k, f in self.fields.items():
            raw[k] = f.value()
        for k, dd in self.dds.items():
            raw[k] = int(dd.SelectedIndex)
        for k, cb in self.cbs.items():
            raw[k] = bool(cb.Checked)
        return normalize_settings(raw)

    def ApplySettings(self, s):
        self._suppress_preview = True
        try:
            for k, f in self.fields.items():
                if k in s:
                    f.set_value(s[k])
            for k, dd in self.dds.items():
                if k in s:
                    dd.SelectedIndex = int(s[k])
            for k, cb in self.cbs.items():
                if k in s:
                    cb.Checked = bool(s[k])
            self.UpdateEnabling()
        finally:
            self._suppress_preview = False
        self.UpdatePreview()

    def UpdatePreview(self):
        if getattr(self, "_preview_closed", False) or getattr(self, "_suppress_preview", False):
            return
        try:
            S = self.GetCurrentSettings()
            self.conduit.set_finishes(S)
            self.conduit.preview_breps = build_kitchen_system(
                self.base_plane_doc, S, doc=None, fast=S["fast_preview"]
            )
            self.lbl_status.Text = ""
        except Exception as ex:
            self.conduit.preview_breps = []
            self.lbl_status.Text = str(ex)
        try:
            Rhino.RhinoDoc.ActiveDoc.Views.Redraw()
        except Exception:
            pass

    def ClosePreview(self):
        if getattr(self, "_preview_closed", False):
            return
        self._preview_closed = True
        if self.conduit:
            try:
                self.conduit.Enabled = False
            except Exception:
                pass
            self.conduit.preview_breps = []
        if sc.sticky.get(CONDUIT_KEY) is self.conduit:
            try:
                del sc.sticky[CONDUIT_KEY]
            except Exception:
                pass
        try:
            Rhino.RhinoDoc.ActiveDoc.Views.Redraw()
        except Exception:
            pass

    def OnOkClicked(self, sender, e):
        s = self.GetCurrentSettings()
        sc.sticky[STICKY_KEY] = s
        self.final_settings = s
        self.ClosePreview()
        self.Close(True)

    def OnCancelClicked(self, sender, e):
        self.ClosePreview()
        self.Close(False)

    def OnDialogClosed(self, sender, e):
        self.ClosePreview()

    def _refresh_presets(self, sel=None):
        names = sorted(self.presets.keys()) if self.presets else []
        items = ["<Select preset>"] + names
        self.dd_preset.DataStore = list(items)
        if sel and sel in names:
            self.dd_preset.SelectedIndex = names.index(sel) + 1
            self.txt_preset_name.Text = sel
        else:
            self.dd_preset.SelectedIndex = 0

    def OnPresetSelected(self, sender, e):
        idx = int(self.dd_preset.SelectedIndex)
        if idx > 0:
            name = str(self.dd_preset.DataStore[idx])
            self.txt_preset_name.Text = name

    def OnPresetLoad(self, sender, e):
        idx = int(self.dd_preset.SelectedIndex)
        if idx <= 0:
            return
        name = str(self.dd_preset.DataStore[idx])
        if name in self.presets:
            self.ApplySettings(self.presets[name])

    def OnPresetSave(self, sender, e):
        name = self.txt_preset_name.Text.strip()
        if not name:
            rs.MessageBox("Enter a preset name.", 0, "Preset Save")
            return
        self.presets[name] = self.GetCurrentSettings()
        if save_presets(self.presets):
            self._refresh_presets(name)

    def OnPresetDelete(self, sender, e):
        idx = int(self.dd_preset.SelectedIndex)
        if idx <= 0:
            return
        name = str(self.dd_preset.DataStore[idx])
        if name in self.presets:
            del self.presets[name]
            save_presets(self.presets)
            self._refresh_presets()


# ============================================================
# DIALOG LAUNCHER & MAIN COMMAND ENTRY POINT
# ============================================================
def show_kitchen_dialog(dlg, doc):
    parent = None
    try:
        parent = Rhino.UI.RhinoEtoApp.MainWindowForDocument(doc)
    except Exception:
        pass
    if not parent:
        try:
            parent = Rhino.UI.RhinoEtoApp.MainWindow
        except Exception:
            pass
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


def create_modern_kitchen_cabinet():
    doc = Rhino.RhinoDoc.ActiveDoc or sc.doc
    unit_sys, unit_name, u = get_doc_unit_info(doc)
    init_s = get_initial_settings()

    mode = "draw"
    start_pt = None

    while True:
        initial_gp = ric.GetPoint()
        initial_gp.SetCommandPrompt("Pick start corner of kitchen wall run (or select option)")
        initial_gp.AcceptNothing(True)
        opt_draw = initial_gp.AddOption("DrawKitchen")
        opt_select = initial_gp.AddOption("SelectKitchen")

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
                p1 = rs.GetPoint("Pick start corner of kitchen wall run")
                if not p1:
                    return
                start_pt = rg.Point3d(p1.X, p1.Y, p1.Z)
                mode = "draw"
                break
        elif rc == Rhino.Input.GetResult.Nothing:
            p1 = rs.GetPoint("Pick start corner of kitchen wall run")
            if not p1:
                return
            start_pt = rg.Point3d(p1.X, p1.Y, p1.Z)
            mode = "draw"
            break
        else:
            return

    base_plane_doc = None
    edit_target_ids = []

    if mode == "select":
        go = ric.GetObject()
        go.SetCommandPrompt("Select existing Kitchen Cabinet to edit, or select wall baseline curve")
        go.GeometryFilter = rdo.ObjectType.Brep | rdo.ObjectType.Extrusion | rdo.ObjectType.Curve
        go.SubObjectSelect = False
        go.EnablePreSelect(True, True)
        if go.Get() != Rhino.Input.GetResult.Object:
            return

        objref = go.Object(0)
        obj = objref.Object()
        state_txt = obj.Attributes.GetUserString(METADATA_KEY) if obj else None
        decoded = decode_state(state_txt) if state_txt else None

        if decoded:
            plane_in, saved_s = decoded
            init_s = saved_s
            edit_target_ids = get_generated_group_member_ids(doc, obj)
            orig_doc = rg.Point3d(plane_in.Origin.X * u, plane_in.Origin.Y * u, plane_in.Origin.Z * u)
            pl_doc = rg.Plane(orig_doc, plane_in.XAxis, plane_in.YAxis)
            base_plane_doc = transform_plane_from_current_objects(doc, pl_doc, edit_target_ids)
        else:
            crv = objref.Curve()
            if not crv:
                rs.MessageBox("Please select a valid Kitchen Cabinet object or a wall baseline curve.", 48, "Kitchen Selection")
                return
            rc_pl, pl = crv.TryGetPolyline()
            if rc_pl and pl.Count >= 3:
                # L-shape 2-segment polyline selected!
                p0, p1, p2 = pl[0], pl[1], pl[2]
                len1_in = p0.DistanceTo(p1) / u
                len2_in = p1.DistanceTo(p2) / u
                init_s["cabinet_type"] = 1
                init_s["total_length"] = clamp(round(len1_in, 2), 24.0, 600.0)
                init_s["return_length"] = clamp(round(len2_in, 2), 24.0, 360.0)
                x_ax = _safe_unitize(rg.Point3d(p1.X, p1.Y, p0.Z) - p0, rg.Vector3d.XAxis)
                y_ax = _safe_unitize(rg.Vector3d.CrossProduct(rg.Vector3d.ZAxis, x_ax), rg.Vector3d.YAxis)
                base_plane_doc = rg.Plane(p0, x_ax, y_ax)
            else:
                p1 = crv.PointAtStart
                p2 = rg.Point3d(crv.PointAtEnd.X, crv.PointAtEnd.Y, p1.Z)
                dist_doc = p1.DistanceTo(p2)
                if (dist_doc / u) < 20.0:
                    rs.MessageBox("Wall baseline curve is too short.", 48, "Kitchen Error")
                    return
                init_s["total_length"] = clamp(round(dist_doc / u, 2), 24.0, 600.0)
                x_ax = _safe_unitize(p2 - p1, rg.Vector3d.XAxis)
                y_ax = _safe_unitize(rg.Vector3d.CrossProduct(rg.Vector3d.ZAxis, x_ax), rg.Vector3d.YAxis)
                base_plane_doc = rg.Plane(p1, x_ax, y_ax)

    else:
        len_disp = format_cab_length(init_s["total_length"] * u, unit_name)
        gp_len = KitchenRunPointGetter(start_pt, init_s, u)
        gp_len.SetCommandPrompt("Pick 2nd point along wall (sets kitchen length & orientation) or press ENTER for <%s %s>" % (len_disp, unit_name))
        gp_len.SetBasePoint(start_pt, True)
        gp_len.DrawLineFromPoint(start_pt, True)
        gp_len.AcceptNothing(True)
        rc_l = gp_len.Get()

        if rc_l == Rhino.Input.GetResult.Point:
            p2_raw = gp_len.Point()
            p2 = rg.Point3d(p2_raw.X, p2_raw.Y, start_pt.Z)
            dist_doc = start_pt.DistanceTo(p2)
            if (dist_doc / u) < 20.0:
                rs.MessageBox("Kitchen run length is too short.", 48, "Kitchen Error")
                return
            init_s["total_length"] = clamp(round(dist_doc / u, 2), 24.0, 600.0)
            x_ax = _safe_unitize(p2 - start_pt, rg.Vector3d.XAxis)
            y_ax = _safe_unitize(rg.Vector3d.CrossProduct(rg.Vector3d.ZAxis, x_ax), rg.Vector3d.YAxis)
            base_plane_doc = rg.Plane(start_pt, x_ax, y_ax)
        elif rc_l == Rhino.Input.GetResult.Nothing:
            base_plane_doc = rg.Plane(start_pt, rg.Vector3d.XAxis, rg.Vector3d.YAxis)
        else:
            return

    dlg = ModernKitchenDialog()
    dlg.Initialize(
        base_plane_doc,
        initial_settings=init_s,
        is_edit=bool(edit_target_ids),
    )
    ok = False
    try:
        ok = show_kitchen_dialog(dlg, doc)
    finally:
        dlg.ClosePreview()

    if not ok or not dlg.final_settings:
        return

    S = dlg.final_settings

    undo_record = doc.BeginUndoRecord("Create Modern Kitchen Cabinets")
    rs.EnableRedraw(False)
    try:
        ids = bake_kitchen_cabinet(doc, base_plane_doc, S, u, edit_target_ids)
    except Exception as ex:
        ids = []
        import traceback
        traceback.print_exc()
        rs.MessageBox("Unexpected error creating kitchen cabinets: {}".format(ex), 0, "Kitchen Error")
    finally:
        rs.EnableRedraw(True)
        if undo_record > 0:
            doc.EndUndoRecord(undo_record)

    doc.Views.Redraw()
    if ids:
        print("\nModern Ergonomic Kitchen Cabinets & Warm-Yellow LEDs Created Successfully! ({} components)".format(len(ids)))
        print("Run Length: {:.1f} {} | Counter Height: {:.1f} {} | Board Thickness: {:.2f} {}".format(
            S["total_length"] * u, unit_name, S["counter_h"] * u, unit_name, S["carcass_t"] * u, unit_name
        ))


def run():
    create_modern_kitchen_cabinet()


if __name__ in ["__main__", "ArchKitchen", "KitchenCabinetMaker", "Kitchen", "__builtin__"]:
    create_modern_kitchen_cabinet()