using System;
using System.IO;
using System.Reflection;
using System.Runtime.InteropServices;
using System.Collections.Generic;
using Rhino;
using Rhino.Commands;
using Rhino.PlugIns;
using Rhino.UI;

[assembly: AssemblyTitle("Shalik Furniture")]
[assembly: AssemblyDescription("Shalik Automatic Furniture Generator Suite for Rhino 8 by Sakhawat Hosen Sumon - Bed, Sofa, Dining Table, Kitchen Cabinets, Office Desk Workstations")]
[assembly: AssemblyCompany("Sakhawat Hosen Sumon")]
[assembly: AssemblyProduct("Shalik Furniture")]
[assembly: AssemblyCopyright("Copyright © 2026 Sakhawat Hosen Sumon. Commercial Proprietary Software. All Rights Reserved.")]
[assembly: AssemblyVersion("1.0.0")]
[assembly: AssemblyFileVersion("1.0.0")]
[assembly: Guid("0ce7337f-ec52-45da-9fd3-cc40db64b2fa")]

[assembly: PlugInDescription(DescriptionType.Organization, "Sakhawat Hosen Sumon")]
[assembly: PlugInDescription(DescriptionType.Email, "arch.sakhawat@gmail.com")]
[assembly: PlugInDescription(DescriptionType.WebSite, "https://github.com/arch-sakhawat/SHALIK-FURNITURE")]
[assembly: PlugInDescription(DescriptionType.Address, "Facebook: https://www.facebook.com/sakhawat.sumon2")]

namespace ShalikFurniture
{
    public class ShalikFurniturePlugin : PlugIn
    {
        public static ShalikFurniturePlugin Instance { get; private set; }

        public ShalikFurniturePlugin()
        {
            Instance = this;
        }

        public string GetPluginDirectory()
        {
            try
            {
                string loc = Assembly.GetExecutingAssembly().Location;
                if (!string.IsNullOrEmpty(loc))
                {
                    string dir = Path.GetDirectoryName(loc);
                    if (!string.IsNullOrEmpty(dir) && Directory.Exists(dir))
                        return dir;
                }
            }
            catch { }

            // Fallback search locations in Application Data
            string appData = Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData);
            string[] searchBases = {
                Path.Combine(appData, @"McNeel\Rhinoceros\packages\8.0\ShalikFurniture\1.0.0"),
                Path.Combine(appData, @"ShalikFurniture"),
                Path.Combine(appData, @"McNeel\Rhinoceros\packages\8.0\Shalik\1.0.4"),
                @"E:\antigravity\Shalik Furniture"
            };

            foreach (string b in searchBases)
            {
                if (Directory.Exists(b))
                    return b;
            }

            return AppDomain.CurrentDomain.BaseDirectory;
        }

        /// <summary>Resolves a python script by file name in known search folders.</summary>
        public string ResolveScriptPath(string scriptName)
        {
            string dir = GetPluginDirectory();

            string[] searchSubDirs = {
                dir,
                Path.Combine(dir, "commands"),
                Path.Combine(dir, "Code"),
                Path.Combine(dir, "scripts")
            };

            foreach (string d in searchSubDirs)
            {
                if (Directory.Exists(d))
                {
                    string p = Path.Combine(d, scriptName);
                    if (File.Exists(p)) return p;
                }
            }

            string root = @"E:\antigravity\Shalik Furniture";
            if (Directory.Exists(root))
            {
                string p = Path.Combine(root, scriptName);
                if (File.Exists(p)) return p;
                p = Path.Combine(root, "commands", scriptName);
                if (File.Exists(p)) return p;
                p = Path.Combine(root, "Code", scriptName);
                if (File.Exists(p)) return p;
            }

            return null;
        }

        public void RunPython(string scriptFileName)
        {
            string fullPath = ResolveScriptPath(scriptFileName);
            if (string.IsNullOrEmpty(fullPath) || !File.Exists(fullPath))
            {
                RhinoApp.WriteLine(string.Format(
                    "Shalik Furniture Error: Could not locate '{0}' in plugin directory: {1}",
                    scriptFileName, GetPluginDirectory()));
                return;
            }

            string cmd = string.Format("! _-RunPythonScript \"{0}\"", fullPath.Replace('\\', '/'));
            RhinoApp.RunScript(cmd, false);
        }

        public bool ShowToolbar()
        {
            try
            {
                string ruiPath = Path.Combine(GetPluginDirectory(), "ShalikFurniture.rui");
                if (!File.Exists(ruiPath))
                {
                    string appData = Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData);
                    ruiPath = Path.Combine(appData, @"McNeel\Rhinoceros\packages\8.0\ShalikFurniture\1.0.0\ShalikFurniture.rui");
                }
                if (!File.Exists(ruiPath))
                {
                    ruiPath = @"E:\antigravity\Shalik Furniture\ShalikFurniture.rui";
                }

                if (File.Exists(ruiPath))
                {
                    ToolbarFile tf = RhinoApp.ToolbarFiles.FindByPath(ruiPath);
                    if (tf == null)
                    {
                        tf = RhinoApp.ToolbarFiles.Open(ruiPath);
                    }
                    if (tf != null)
                    {
                        for (int i = 0; i < tf.GroupCount; i++)
                        {
                            var grp = tf.GetGroup(i);
                            if (grp != null)
                            {
                                grp.Visible = true;
                            }
                        }
                        return true;
                    }
                }
            }
            catch (Exception ex)
            {
                RhinoApp.WriteLine("Shalik Furniture Toolbar Notification: " + ex.Message);
            }
            return false;
        }

        protected override LoadReturnCode OnLoad(ref string errorMessage)
        {
            RhinoApp.WriteLine("Loading Shalik Furniture Suite v1.0.0 by Sakhawat Hosen Sumon...");

            var toolMap = new Dictionary<string, string> {
                { "ShalikFurniture",       "ShalikFurniture.py" },
                { "ArchFurniture",         "ShalikFurniture.py" },
                { "FurnitureHub",          "ShalikFurniture.py" },

                { "ShalikBed",             "ShalikBed.py" },
                { "ArchBed",               "ShalikBed.py" },
                { "FurnitureBed",          "ShalikBed.py" },
                { "Bed",                   "ShalikBed.py" },

                { "ShalikSofa",            "ShalikSofa.py" },
                { "ArchSofa",              "ShalikSofa.py" },
                { "FurnitureSofa",         "ShalikSofa.py" },
                { "Sofa",                  "ShalikSofa.py" },

                { "ShalikDiningTable",     "ShalikDiningTable.py" },
                { "ArchDiningTable",       "ShalikDiningTable.py" },
                { "FurnitureDiningTable",  "ShalikDiningTable.py" },
                { "ShalikDiningSet",       "ShalikDiningTable.py" },
                { "DiningTable",           "ShalikDiningTable.py" },
                { "DiningSet",             "ShalikDiningTable.py" },

                { "ShalikKitchen",         "ShalikKitchen.py" },
                { "ArchKitchen",           "ShalikKitchen.py" },
                { "FurnitureKitchen",      "ShalikKitchen.py" },
                { "KitchenCabinet",        "ShalikKitchen.py" },
                { "Kitchen",               "ShalikKitchen.py" },

                { "ShalikOfficeDesk",      "ShalikOfficeDesk.py" },
                { "ArchOfficeDesk",        "ShalikOfficeDesk.py" },
                { "FurnitureOfficeDesk",   "ShalikOfficeDesk.py" },
                { "ShalikDesk",            "ShalikOfficeDesk.py" },
                { "OfficeDesk",            "ShalikOfficeDesk.py" },
                { "Desk",                  "ShalikOfficeDesk.py" },

                { "ShalikImportSKP",       "ShalikImportSKP.py" },
                { "ArchImportSKP",         "ShalikImportSKP.py" },
                { "ImportSKP",             "ShalikImportSKP.py" },
                { "SKPImport",             "ShalikImportSKP.py" },

                { "ShalikFurnitureAbout",   "ShalikAbout.py" },
                { "ShalikFurnitureLicense", "ShalikAbout.py" },
                { "ArchFurnitureAbout",     "ShalikAbout.py" },
                { "ArchFurnitureLicense",   "ShalikAbout.py" }
            };

            foreach (var kvp in toolMap)
            {
                try
                {
                    string path = ResolveScriptPath(kvp.Value);
                    if (!string.IsNullOrEmpty(path) && File.Exists(path))
                    {
                        string macro = string.Format("! _-RunPythonScript \"{0}\"", path.Replace('\\', '/'));
                        Rhino.ApplicationSettings.CommandAliasList.SetMacro(kvp.Key, macro);
                    }
                }
                catch (Exception ex)
                {
                    RhinoApp.WriteLine(string.Format("Shalik Furniture: Could not register alias '{0}': {1}", kvp.Key, ex.Message));
                }
            }

            // Ensure Toolbar is loaded and visible
            ShowToolbar();

            RhinoApp.WriteLine("Shalik Furniture Suite loaded successfully. Type 'ShalikFurniture' to open the Master Hub.");
            return LoadReturnCode.Success;
        }
    }

    // ─────────────────────────────────────────────────────────────
    //  Master Furniture Suite Hub Command
    // ─────────────────────────────────────────────────────────────
    [CommandStyle(Style.ScriptRunner)]
    public class ShalikFurnitureCommand : Command
    {
        public override string EnglishName { get { return "ShalikFurniture"; } }
        protected override Result RunCommand(RhinoDoc doc, RunMode mode)
        {
            ShalikFurniturePlugin.Instance.ShowToolbar();
            ShalikFurniturePlugin.Instance.RunPython("ShalikFurniture.py");
            return Result.Success;
        }
    }

    [CommandStyle(Style.ScriptRunner)]
    public class ArchFurnitureCommand : Command
    {
        public override string EnglishName { get { return "ArchFurniture"; } }
        protected override Result RunCommand(RhinoDoc doc, RunMode mode)
        {
            ShalikFurniturePlugin.Instance.ShowToolbar();
            ShalikFurniturePlugin.Instance.RunPython("ShalikFurniture.py");
            return Result.Success;
        }
    }

    // ─────────────────────────────────────────────────────────────
    //  Toolbar Explicit Command
    // ─────────────────────────────────────────────────────────────
    [CommandStyle(Style.ScriptRunner)]
    public class ShalikToolbarCommand : Command
    {
        public override string EnglishName { get { return "ShalikToolbar"; } }
        protected override Result RunCommand(RhinoDoc doc, RunMode mode)
        {
            if (ShalikFurniturePlugin.Instance.ShowToolbar())
            {
                RhinoApp.WriteLine("Shalik Furniture Toolbar is now visible.");
                return Result.Success;
            }
            RhinoApp.RunScript("! _Toolbar", false);
            return Result.Success;
        }
    }

    [CommandStyle(Style.ScriptRunner)]
    public class ShalikShowToolbarCommand : Command
    {
        public override string EnglishName { get { return "ShalikShowToolbar"; } }
        protected override Result RunCommand(RhinoDoc doc, RunMode mode)
        {
            ShalikFurniturePlugin.Instance.ShowToolbar();
            return Result.Success;
        }
    }

    // ─────────────────────────────────────────────────────────────
    //  Bed Commands
    // ─────────────────────────────────────────────────────────────
    [CommandStyle(Style.ScriptRunner)]
    public class ShalikBedCommand : Command
    {
        public override string EnglishName { get { return "ShalikBed"; } }
        protected override Result RunCommand(RhinoDoc doc, RunMode mode)
        {
            ShalikFurniturePlugin.Instance.RunPython("ShalikBed.py");
            return Result.Success;
        }
    }

    [CommandStyle(Style.ScriptRunner)]
    public class ArchBedCommand : Command
    {
        public override string EnglishName { get { return "ArchBed"; } }
        protected override Result RunCommand(RhinoDoc doc, RunMode mode)
        {
            ShalikFurniturePlugin.Instance.RunPython("ShalikBed.py");
            return Result.Success;
        }
    }

    // ─────────────────────────────────────────────────────────────
    //  Sofa Commands
    // ─────────────────────────────────────────────────────────────
    [CommandStyle(Style.ScriptRunner)]
    public class ShalikSofaCommand : Command
    {
        public override string EnglishName { get { return "ShalikSofa"; } }
        protected override Result RunCommand(RhinoDoc doc, RunMode mode)
        {
            ShalikFurniturePlugin.Instance.RunPython("ShalikSofa.py");
            return Result.Success;
        }
    }

    [CommandStyle(Style.ScriptRunner)]
    public class ArchSofaCommand : Command
    {
        public override string EnglishName { get { return "ArchSofa"; } }
        protected override Result RunCommand(RhinoDoc doc, RunMode mode)
        {
            ShalikFurniturePlugin.Instance.RunPython("ShalikSofa.py");
            return Result.Success;
        }
    }

    // ─────────────────────────────────────────────────────────────
    //  Dining Table Commands
    // ─────────────────────────────────────────────────────────────
    [CommandStyle(Style.ScriptRunner)]
    public class ShalikDiningTableCommand : Command
    {
        public override string EnglishName { get { return "ShalikDiningTable"; } }
        protected override Result RunCommand(RhinoDoc doc, RunMode mode)
        {
            ShalikFurniturePlugin.Instance.RunPython("ShalikDiningTable.py");
            return Result.Success;
        }
    }

    [CommandStyle(Style.ScriptRunner)]
    public class ArchDiningTableCommand : Command
    {
        public override string EnglishName { get { return "ArchDiningTable"; } }
        protected override Result RunCommand(RhinoDoc doc, RunMode mode)
        {
            ShalikFurniturePlugin.Instance.RunPython("ShalikDiningTable.py");
            return Result.Success;
        }
    }

    // ─────────────────────────────────────────────────────────────
    //  Kitchen Commands
    // ─────────────────────────────────────────────────────────────
    [CommandStyle(Style.ScriptRunner)]
    public class ShalikKitchenCommand : Command
    {
        public override string EnglishName { get { return "ShalikKitchen"; } }
        protected override Result RunCommand(RhinoDoc doc, RunMode mode)
        {
            ShalikFurniturePlugin.Instance.RunPython("ShalikKitchen.py");
            return Result.Success;
        }
    }

    [CommandStyle(Style.ScriptRunner)]
    public class ArchKitchenCommand : Command
    {
        public override string EnglishName { get { return "ArchKitchen"; } }
        protected override Result RunCommand(RhinoDoc doc, RunMode mode)
        {
            ShalikFurniturePlugin.Instance.RunPython("ShalikKitchen.py");
            return Result.Success;
        }
    }

    // ─────────────────────────────────────────────────────────────
    //  Office Desk Commands
    // ─────────────────────────────────────────────────────────────
    [CommandStyle(Style.ScriptRunner)]
    public class ShalikOfficeDeskCommand : Command
    {
        public override string EnglishName { get { return "ShalikOfficeDesk"; } }
        protected override Result RunCommand(RhinoDoc doc, RunMode mode)
        {
            ShalikFurniturePlugin.Instance.RunPython("ShalikOfficeDesk.py");
            return Result.Success;
        }
    }

    [CommandStyle(Style.ScriptRunner)]
    public class ArchOfficeDeskCommand : Command
    {
        public override string EnglishName { get { return "ArchOfficeDesk"; } }
        protected override Result RunCommand(RhinoDoc doc, RunMode mode)
        {
            ShalikFurniturePlugin.Instance.RunPython("ShalikOfficeDesk.py");
            return Result.Success;
        }
    }

    // ─────────────────────────────────────────────────────────────
    //  InstantSKP & 3D Warehouse Commands
    // ─────────────────────────────────────────────────────────────
    [CommandStyle(Style.ScriptRunner)]
    public class InstantSKPCommand : Command
    {
        public override string EnglishName { get { return "InstantSKP"; } }
        protected override Result RunCommand(RhinoDoc doc, RunMode mode)
        {
            ShalikFurniturePlugin.Instance.RunPython("ShalikImportSKP.py");
            return Result.Success;
        }
    }

    [CommandStyle(Style.ScriptRunner)]
    public class ShalikInstantSKPCommand : Command
    {
        public override string EnglishName { get { return "ShalikInstantSKP"; } }
        protected override Result RunCommand(RhinoDoc doc, RunMode mode)
        {
            ShalikFurniturePlugin.Instance.RunPython("ShalikImportSKP.py");
            return Result.Success;
        }
    }

    [CommandStyle(Style.ScriptRunner)]
    public class ShalikImportSKPCommand : Command
    {
        public override string EnglishName { get { return "ShalikImportSKP"; } }
        protected override Result RunCommand(RhinoDoc doc, RunMode mode)
        {
            ShalikFurniturePlugin.Instance.RunPython("ShalikImportSKP.py");
            return Result.Success;
        }
    }

    [CommandStyle(Style.ScriptRunner)]
    public class ArchImportSKPCommand : Command
    {
        public override string EnglishName { get { return "ArchImportSKP"; } }
        protected override Result RunCommand(RhinoDoc doc, RunMode mode)
        {
            ShalikFurniturePlugin.Instance.RunPython("ShalikImportSKP.py");
            return Result.Success;
        }
    }

    [CommandStyle(Style.ScriptRunner)]
    public class ShalikWarehouseCommand : Command
    {
        public override string EnglishName { get { return "ShalikWarehouse"; } }
        protected override Result RunCommand(RhinoDoc doc, RunMode mode)
        {
            ShalikFurniturePlugin.Instance.RunPython("ShalikImportSKP.py");
            return Result.Success;
        }
    }

    // ─────────────────────────────────────────────────────────────
    //  About & License Commands
    // ─────────────────────────────────────────────────────────────
    [CommandStyle(Style.ScriptRunner)]
    public class ShalikFurnitureAboutCommand : Command
    {
        public override string EnglishName { get { return "ShalikFurnitureAbout"; } }
        protected override Result RunCommand(RhinoDoc doc, RunMode mode)
        {
            ShalikFurniturePlugin.Instance.RunPython("ShalikAbout.py");
            return Result.Success;
        }
    }

    [CommandStyle(Style.ScriptRunner)]
    public class ShalikFurnitureLicenseCommand : Command
    {
        public override string EnglishName { get { return "ShalikFurnitureLicense"; } }
        protected override Result RunCommand(RhinoDoc doc, RunMode mode)
        {
            ShalikFurniturePlugin.Instance.RunPython("ShalikAbout.py");
            return Result.Success;
        }
    }
}
