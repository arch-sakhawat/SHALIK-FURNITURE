# -*- coding: utf-8 -*-
# ==============================================================================
# Shalik Architectural Modeling Suite for Rhino 8 & 7
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
"""
ArchUnits - Universal Architectural Unit System for Shalik (ArchTools)
Supports seamless conversion between document model units (mm, cm, m, in, ft)
and user input parsing in any unit (e.g., 4'6", 36", 1200mm, 2.1m, 3.5ft, 1 1/2").
"""
import re
import math

try:
    import Rhino
except ImportError:
    Rhino = None

try:
    import scriptcontext as sc
except ImportError:
    sc = None


# Unit abbreviations
UNIT_ABBREVIATIONS = {
    "in": "in",
    "inch": "in",
    "inches": "in",
    '"': "in",
    "ft": "ft",
    "feet": "ft",
    "foot": "ft",
    "'": "ft",
    "mm": "mm",
    "millimeter": "mm",
    "millimeters": "mm",
    "cm": "cm",
    "centimeter": "cm",
    "centimeters": "cm",
    "m": "m",
    "meter": "m",
    "meters": "m",
}

# Scale factor: 1.0 unit = how many INCHES
TO_INCHES = {
    "in": 1.0,
    "inch": 1.0,
    "inches": 1.0,
    '"': 1.0,
    "ft": 12.0,
    "feet": 12.0,
    "foot": 12.0,
    "'": 12.0,
    "mm": 1.0 / 25.4,
    "millimeter": 1.0 / 25.4,
    "millimeters": 1.0 / 25.4,
    "cm": 1.0 / 2.54,
    "centimeter": 1.0 / 2.54,
    "centimeters": 1.0 / 2.54,
    "m": 1.0 / 0.0254,
    "meter": 1.0 / 0.0254,
    "meters": 1.0 / 0.0254,
}

# Scale factor: 1.0 INCH = how many units
FROM_INCHES = {
    "in": 1.0,
    "ft": 1.0 / 12.0,
    "mm": 25.4,
    "cm": 2.54,
    "m": 0.0254,
}


def get_doc_unit_info(doc=None):
    """
    Returns (unit_system_enum, unit_name, scale_from_inch)
    where scale_from_inch is how many model units equal 1.0 inch.
    e.g., for mm doc, scale_from_inch = 25.4, unit_name = 'mm'
    """
    if doc is None:
        if sc and hasattr(sc, "doc") and sc.doc is not None:
            doc = sc.doc
        elif Rhino and hasattr(Rhino, "RhinoDoc") and Rhino.RhinoDoc.ActiveDoc is not None:
            doc = Rhino.RhinoDoc.ActiveDoc

    if doc is not None and Rhino is not None:
        try:
            unit_sys = doc.ModelUnitSystem
            scale = Rhino.RhinoMath.UnitScale(Rhino.UnitSystem.Inches, unit_sys)
            if unit_sys == Rhino.UnitSystem.Millimeters:
                return unit_sys, "mm", scale
            elif unit_sys == Rhino.UnitSystem.Centimeters:
                return unit_sys, "cm", scale
            elif unit_sys == Rhino.UnitSystem.Meters:
                return unit_sys, "m", scale
            elif unit_sys == Rhino.UnitSystem.Feet:
                return unit_sys, "ft", scale
            elif unit_sys == Rhino.UnitSystem.Inches:
                return unit_sys, "in", scale
            else:
                return unit_sys, str(unit_sys).lower(), scale
        except Exception:
            pass

    return None, "in", 1.0


def parse_length(text, current_unit="in"):
    """
    Parses any length text into the target current_unit (default 'in').
    Accepts:
      - 1200 or 1200.5 (plain number -> interpreted in current_unit)
      - 4' (feet)
      - 4ft, 3.5ft
      - 4'6", 4'-6", 4' 6", 4ft 6in, 4' 6 1/2" (compound feet & inches)
      - 36", 36in, 36.5"
      - 1200mm, 150cm, 1.5m
      - Fractions: 1/2", 3/4", 1 1/2"
    """
    text = str(text).strip()
    if not text:
        return 0.0

    target = current_unit.lower()
    if target not in FROM_INCHES:
        target = "in"

    # 1. Compound feet & inches: e.g. 4'6", 4'-6", 4' 6", 4ft 6in, 4'6, 4' 6 1/2"
    compound_pattern = r'''^([+-]?\d+(?:\.\d+)?)\s*(?:'|ft|feet)\s*[- ]*\s*(\d+(?:\.\d+)?(?:\s+\d+\/\d+)?|\d+\/\d+)?\s*(?:"|in|inch|inches)?$'''
    m = re.match(compound_pattern, text, re.IGNORECASE)
    if m:
        ft_val = float(m.group(1))
        inch_str = m.group(2)
        inch_val = 0.0
        if inch_str:
            inch_str = inch_str.strip()
            if ' ' in inch_str:
                parts = inch_str.split()
                whole = float(parts[0])
                num, denom = parts[1].split('/')
                inch_val = whole + float(num) / float(denom)
            elif '/' in inch_str:
                num, denom = inch_str.split('/')
                inch_val = float(num) / float(denom)
            else:
                inch_val = float(inch_str)
        sign = -1.0 if ft_val < 0 else 1.0
        total_inches = (abs(ft_val) * 12.0 + inch_val) * sign
        return total_inches * FROM_INCHES[target]

    # 2. Single unit or fraction or plain number: 1200, 1200mm, 36", 3.5ft, 1 1/2"
    unit_pattern = r'''^([+-]?\d+(?:\.\d+)?(?:\s+\d+\/\d+)?|[+-]?\d+\/\d+)\s*(mm|cm|m|meter|meters|in|inch|inches|"|ft|feet|foot|')?$'''
    m = re.match(unit_pattern, text, re.IGNORECASE)
    if m:
        num_str = m.group(1).strip()
        unit_str = m.group(2)

        # Parse fraction if present
        if ' ' in num_str:
            parts = num_str.split()
            whole = float(parts[0])
            num, denom = parts[1].split('/')
            val = (abs(whole) + float(num) / float(denom)) * (-1.0 if whole < 0 else 1.0)
        elif '/' in num_str:
            num, denom = num_str.split('/')
            val = float(num) / float(denom)
        else:
            val = float(num_str)

        if not unit_str:
            # Plain number: interpreted directly in target current_unit!
            return val

        u_low = unit_str.lower()
        if u_low in TO_INCHES:
            val_in_inches = val * TO_INCHES[u_low]
            return val_in_inches * FROM_INCHES[target]

    # Fallback to direct float
    return float(text)


def format_length(v, unit_name="in", is_int=False):
    """
    Format length value nicely for textboxes.
    e.g. for mm: 2134 or 2133.6
    for m: 2.134
    for in: 84 or 84.5
    """
    if is_int:
        return str(int(round(v)))
    
    unit_name = unit_name.lower()
    if unit_name in ("mm", "cm"):
        decimals = 1
    elif unit_name in ("m", "ft"):
        decimals = 3
    else:  # in
        decimals = 2

    fmt = "{:." + str(decimals) + "f}"
    s = fmt.format(v).rstrip("0").rstrip(".")
    return s if s else "0"


def unit_scale(doc=None):
    """Returns scale factor from inches to model units."""
    _, _, scale = get_doc_unit_info(doc)
    return scale


def update_label_unit(label, unit_name):
    """Replaces (in) or (in, with the current unit name."""
    s = str(label)
    s = re.sub(r'\(in\b', '(' + unit_name, s, flags=re.IGNORECASE)
    return s


def adapt_num_fields(num_fields, non_length_keys, scale_from_inch, unit_name):
    """
    Adapts NUM_FIELDS tuples for the current document unit system.
    Length fields are scaled by scale_from_inch and have labels updated to (unit_name).
    Non-length fields (counts, angles, %) are preserved as-is.
    """
    adapted = []
    for item in num_fields:
        key = item[0]
        label = item[1]
        default = item[2]
        mn = item[3]
        mx = item[4]
        is_int = item[5]
        if key in non_length_keys or is_int:
            adapted.append((key, label, default, mn, mx, is_int))
        else:
            new_label = update_label_unit(label, unit_name)
            new_dflt = round(default * scale_from_inch, 3)
            new_mn = round(mn * scale_from_inch, 3)
            new_mx = round(mx * scale_from_inch, 3)
            adapted.append((key, new_label, new_dflt, new_mn, new_mx, is_int))
    return adapted


