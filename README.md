<div align="center">

<img src="author.png" width="180" height="180" style="border-radius: 50%; box-shadow: 0 4px 12px rgba(139,0,0,0.4); border: 4px solid #8B0000;" alt="Architect Sakhawat Hosen Sumon" />

# SHALIK FURNITURE GENERATOR SUITE
### Automated Parametric Architectural Furniture & BIM Suite for Rhinoceros 8 & 7

[![License: Proprietary](https://img.shields.io/badge/License-Commercial%20Proprietary-red.svg)](LICENSE.txt)
[![Rhino 8](https://img.shields.io/badge/Rhino-8%20%7C%207-darkred.svg)](https://www.rhino3d.com/)
[![Author](https://img.shields.io/badge/Architect-Sakhawat%20Hosen%20Sumon-8B0000.svg)](mailto:arch.sakhawat@gmail.com)
[![Status](https://img.shields.io/badge/Release-v1.0.0-green.svg)](https://github.com/arch-sakhawat/SHALIK-FURNITURE)

**Principal Architect & Computational Developer:** Sakhawat Hosen Sumon  
**Email:** [arch.sakhawat@gmail.com](mailto:arch.sakhawat@gmail.com)  
**Facebook Profile:** [https://www.facebook.com/sakhawat.sumon2](https://www.facebook.com/sakhawat.sumon2)  
**Official GitHub Repository:** [https://github.com/arch-sakhawat/SHALIK-FURNITURE](https://github.com/arch-sakhawat/SHALIK-FURNITURE)

</div>

---

> [!CAUTION]
> # ⚠️ CRITICAL LEGAL COPYRIGHT & OWNERSHIP NOTICE
> ### THIS SOFTWARE IS STRICTLY PROPRIETARY AND COMMERCIAL — THIS IS NOT FREE OR OPEN-SOURCE SOFTWARE.
>
> **Copyright © 2026 Sakhawat Hosen Sumon. All Rights Reserved.**
>
> All geometric algorithms, parametric solvers, source code (`.py`, `.cs`), compiled plug-in binaries (`.rhp`, `.dll`), Windows executables (`.exe`), Rhino toolbar definitions (`.rui`), vector/raster icons, branding, and documentation contained in this repository are the exclusive intellectual property of **Architect Sakhawat Hosen Sumon**.
>
> ### 🚨 STRICT PROHIBITION & LAWSUIT WARNING (ANTI-PIRACY):
> - **UNAUTHORIZED COPYING, CLONING, FORKING FOR REDISTRIBUTION, DECOMPILATION, RE-LICENSING, SHARING, OR COMMERCIAL EXPLOITATION IS STRICTLY PROHIBITED BY LAW.**
> - Accessing this repository **does NOT** grant public or private permission to distribute, copy, duplicate, resell, or include this software in any collection.
> - **LEGAL ACTION & COURT PROSECUTION:** Any individual, studio, corporation, or entity found copying, duplicating, redistributing, cracked-sharing, or infringing upon this intellectual property without an official written commercial license signed by **Sakhawat Hosen Sumon** will face **IMMEDIATE LEGAL PROSECUTION, COPYRIGHT INFRINGEMENT LAWSUITS (COURT CASES), CLAIMS FOR STATUTORY DAMAGES, AND CRIMINAL/CIVIL PENALTIES** under international and domestic intellectual property and digital copyright protection acts.

---

## 🏛️ Overview

**Shalik Furniture** is a high-performance, parametric BIM furniture generator for **Rhino 8** (and Rhino 7). Tailored specifically for architects, interior designers, and 3D visualizers, it generates production-ready, fully textured, unit-aware architectural furniture with real-time shaded 3D viewport previews.

All generators automatically adapt to the active Rhino document units (**millimeters, centimeters, meters, inches, feet**), enforce realistic joinery and board thicknesses, and generate organized layer structures with physical PBR materials.

---

## 🪑 Parametric Generators & Tools Included

| Icon | Tool | Rhino Command | Description & Typologies |
| :---: | :--- | :--- | :--- |
| <img src="icons/hub_64.png" width="32" height="32" /> | **Master Furniture Hub** | `ShalikFurniture` | Unified control dashboard to launch any generator, convert units, and manage settings |
| <img src="icons/bed_64.png" width="32" height="32" /> | **Modern Bed & Suite** | `ShalikBed` / `ArchBed` | Platform, Cantilever, Wingback, Hotel Wall-Panel, Canopy, Tatami & Daybeds |
| <img src="icons/sofa_64.png" width="32" height="32" /> | **Modern Sofa & Sectional** | `ShalikSofa` / `ArchSofa` | Linear, L-Chaise, U-Sectional, Tuxedo, Curved & Daybed Sectionals |
| <img src="icons/dining_64.png" width="32" height="32" /> | **Dining Sets & Chairs** | `ShalikDiningTable` / `ArchDiningTable` | Auto-Seated (2–12 Seats) Rectangular, Round, Oval & Boat Tables with Designer Chairs |
| <img src="icons/kitchen_64.png" width="32" height="32" /> | **Kitchen Millwork** | `ShalikKitchen` / `ArchKitchen` | Modular Base, Tall & Wall Millwork, Cooktops, Sinks & Emissive Warm LED Lighting |
| <img src="icons/desk_64.png" width="32" height="32" /> | **Executive Workstation** | `ShalikOfficeDesk` / `ArchOfficeDesk` | Executive Desks, Dual Monitor Computer Workstations, Modesty Panels & Ergonomic Chairs |
| <img src="icons/skp_64.png" width="32" height="32" /> | **InstantSKP 3D Warehouse** | `InstantSKP` / `ShalikInstantSKP` | Official InstantSKP v1.0.1 Integrated: Browse & Import Trimble 3D Warehouse SketchUp models directly inside Rhino with materials |
| <img src="icons/about_64.png" width="32" height="32" /> | **About & Legal License** | `ShalikFurnitureAbout` / `ShalikAbout` | Author credentials, legal ownership verification, and licensing dialog |

---

## 🌟 Key Features

1. **⚡ Interactive Live Viewport Previews:**
   - Shaded and wireframe 3D dynamic viewport previews respond instantaneously to slider inputs.
   - Non-destructive parametric re-editing: click any existing furniture group in Rhino to re-open its exact parameters.

2. **📐 Universal Unit Awareness (`ArchUnits`):**
   - Automatically adapts to document units (mm, cm, m, in, ft).
   - Seamlessly converts imperial architectural dimensions (e.g. `6'0"`, `36"`) and metric dimensions (e.g. `1800mm`, `2.4m`).

3. **🎨 Automated PBR Architectural Materials & Layers:**
   - Assigns physically-based materials: Velvet Headboards, High-Grade Leather, Walnut, White Oak, Polished Stainless Steel, Brushed Brass, Carrara Marble, and 2700K Warm LED strip lighting.
   - Structured layer hierarchy automatically created under `Shalik Furniture::[Category]`.

4. **🍷 Signature Dark-Red Interface & Custom Toolbar:**
   - Dark-red themed (`#8B0000`) 8-button Rhino toolbar (`ShalikFurniture.rui`) featuring multi-resolution vector and bitmap icons for light and dark Rhino UI modes.

5. **📦 InstantSKP 3D Warehouse Integration:**
   - Directly browse SketchUp 3D Warehouse models from inside Rhino and import `.skp` furniture models with full materials and textures via official InstantSKP v1.0.1 integration.

---

## 🚀 Installation & Deployment

### Method 1: Single-Click Windows Installer (`.exe`) — Recommended
1. Run [`ShalikFurniture-Setup.exe`](ShalikFurniture-Setup.exe).
2. The installer automatically registers:
   - The native C# Rhino plug-in (`ShalikFurniture.rhp`).
   - The dark-red Rhino 8 toolbar (`ShalikFurniture.rui`).
   - Rhino command aliases (`ShalikFurniture`, `ShalikBed`, `InstantSKP`, etc.).
   - Desktop control launcher (`ShalikFurnitureLauncher.exe`).

### Method 2: Rhino Package Manager (`Yak`)
Open Rhino 8 and run the command line or Windows command prompt:
```text
yak install shalikfurniture
```

### Method 3: Standalone Control Center
Run `ShalikFurnitureLauncher.exe` to check your Rhino installation status, verify plug-in registration, and launch any furniture generator directly into a new Rhino viewport.

---

## ⚖️ Legal & Commercial Licensing

This software is **NOT FREE**. For enterprise deployment, architectural studio multi-seat licenses, custom geometry algorithms, or purchase inquiries, contact the author directly:

- **Architect Sakhawat Hosen Sumon**
- **Email:** [arch.sakhawat@gmail.com](mailto:arch.sakhawat@gmail.com)
- **Facebook:** [https://www.facebook.com/sakhawat.sumon2](https://www.facebook.com/sakhawat.sumon2)
- **Repository:** [https://github.com/arch-sakhawat/SHALIK-FURNITURE](https://github.com/arch-sakhawat/SHALIK-FURNITURE)

*Copyright © 2026 Sakhawat Hosen Sumon. All Rights Reserved.*
