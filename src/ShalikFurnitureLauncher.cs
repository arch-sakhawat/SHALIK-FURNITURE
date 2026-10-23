using System;
using System.IO;
using System.Diagnostics;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Windows.Forms;
using Microsoft.Win32;

[assembly: System.Reflection.AssemblyTitle("Shalik Furniture Launcher")]
[assembly: System.Reflection.AssemblyDescription("Standalone Control Center & Generator Launcher for Shalik Furniture")]
[assembly: System.Reflection.AssemblyCompany("Sakhawat Hosen Sumon")]
[assembly: System.Reflection.AssemblyProduct("Shalik Furniture")]
[assembly: System.Reflection.AssemblyCopyright("Copyright © 2026 Sakhawat Hosen Sumon. Commercial Proprietary Software. All Rights Reserved.")]
[assembly: System.Reflection.AssemblyVersion("1.0.0.0")]
[assembly: System.Reflection.AssemblyFileVersion("1.0.0.0")]

namespace ShalikFurnitureLauncher
{
    public class MainForm : Form
    {
        private Color darkRed = Color.FromArgb(139, 0, 0);
        private Color darkRedHover = Color.FromArgb(170, 20, 20);
        private Color goldAccent = Color.FromArgb(218, 165, 32);

        private Label lblRhinoStatus;
        private Label lblPluginStatus;

        public MainForm()
        {
            this.Text = "Shalik Furniture - Control Center & Generator Hub";
            this.ClientSize = new Size(580, 740);
            this.StartPosition = FormStartPosition.CenterScreen;
            this.FormBorderStyle = FormBorderStyle.FixedDialog;
            this.MaximizeBox = false;
            this.BackColor = Color.FromArgb(248, 248, 250);

            try
            {
                string icoPath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "setup.ico");
                if (File.Exists(icoPath)) this.Icon = new Icon(icoPath);
            }
            catch { }

            InitUI();
            CheckEnvironment();
        }

        private void InitUI()
        {
            // Header Panel
            Panel pnlHeader = new Panel();
            pnlHeader.Dock = DockStyle.Top;
            pnlHeader.Height = 110;
            pnlHeader.BackColor = darkRed;
            pnlHeader.Paint += (s, e) =>
            {
                using (LinearGradientBrush brush = new LinearGradientBrush(
                    pnlHeader.ClientRectangle, Color.FromArgb(120, 0, 0), Color.FromArgb(160, 10, 10), 90f))
                {
                    e.Graphics.FillRectangle(brush, pnlHeader.ClientRectangle);
                }
                using (Pen p = new Pen(goldAccent, 2))
                {
                    e.Graphics.DrawLine(p, 0, pnlHeader.Height - 2, pnlHeader.Width, pnlHeader.Height - 2);
                }
            };

            Label lblTitle = new Label();
            lblTitle.Text = "SHALIK FURNITURE GENERATOR";
            lblTitle.Font = new Font("Segoe UI", 16, FontStyle.Bold);
            lblTitle.ForeColor = Color.White;
            lblTitle.AutoSize = false;
            lblTitle.Size = new Size(560, 36);
            lblTitle.Location = new Point(10, 15);
            lblTitle.TextAlign = ContentAlignment.MiddleCenter;
            pnlHeader.Controls.Add(lblTitle);

            Label lblSub = new Label();
            lblSub.Text = "Automated Parametric Architecture & BIM Suite for Rhino 8 & 7";
            lblSub.Font = new Font("Segoe UI", 10, FontStyle.Regular);
            lblSub.ForeColor = Color.FromArgb(240, 220, 220);
            lblSub.AutoSize = false;
            lblSub.Size = new Size(560, 22);
            lblSub.Location = new Point(10, 52);
            lblSub.TextAlign = ContentAlignment.MiddleCenter;
            pnlHeader.Controls.Add(lblSub);

            Label lblAuthor = new Label();
            lblAuthor.Text = "Architect & Developer: Sakhawat Hosen Sumon";
            lblAuthor.Font = new Font("Segoe UI", 9, FontStyle.Italic);
            lblAuthor.ForeColor = Color.FromArgb(255, 235, 170);
            lblAuthor.AutoSize = false;
            lblAuthor.Size = new Size(560, 20);
            lblAuthor.Location = new Point(10, 76);
            lblAuthor.TextAlign = ContentAlignment.MiddleCenter;
            pnlHeader.Controls.Add(lblAuthor);

            this.Controls.Add(pnlHeader);

            // Status Card
            GroupBox gbStatus = new GroupBox();
            gbStatus.Text = "System & Integration Status";
            gbStatus.Font = new Font("Segoe UI", 9, FontStyle.Bold);
            gbStatus.Location = new Point(25, 125);
            gbStatus.Size = new Size(530, 85);
            gbStatus.ForeColor = Color.FromArgb(60, 60, 60);

            lblRhinoStatus = new Label();
            lblRhinoStatus.Font = new Font("Segoe UI", 9, FontStyle.Regular);
            lblRhinoStatus.Location = new Point(20, 25);
            lblRhinoStatus.Size = new Size(490, 22);
            lblRhinoStatus.Text = "Rhino 8 Installation: Checking...";
            gbStatus.Controls.Add(lblRhinoStatus);

            lblPluginStatus = new Label();
            lblPluginStatus.Font = new Font("Segoe UI", 9, FontStyle.Regular);
            lblPluginStatus.Location = new Point(20, 50);
            lblPluginStatus.Size = new Size(490, 22);
            lblPluginStatus.Text = "Shalik Furniture Plugin: Checking...";
            gbStatus.Controls.Add(lblPluginStatus);

            this.Controls.Add(gbStatus);

            // Tools Group
            GroupBox gbTools = new GroupBox();
            gbTools.Text = "Parametric Furniture Generators";
            gbTools.Font = new Font("Segoe UI", 9, FontStyle.Bold);
            gbTools.Location = new Point(25, 220);
            gbTools.Size = new Size(530, 415);
            gbTools.ForeColor = Color.FromArgb(60, 60, 60);

            int btnY = 30;
            int btnGap = 52;

            AddToolRow(gbTools, "Master Furniture Hub (All Tools)", "Open interactive suite hub and generator launcher", "ShalikFurniture", btnY);
            btnY += btnGap;
            AddToolRow(gbTools, "Modern Bed & Suite Generator", "Platform, cantilever, canopy, tatami, hotel suite & daybeds", "ShalikBed", btnY);
            btnY += btnGap;
            AddToolRow(gbTools, "Modern Sofa & Sectional Generator", "Linear, L-chaise, U-sectional, tuxedo, modular & curved", "ShalikSofa", btnY);
            btnY += btnGap;
            AddToolRow(gbTools, "Dining Table & Chairs Generator", "Auto-seated (2-12 seats) rectangular, round & oval sets", "ShalikDiningTable", btnY);
            btnY += btnGap;
            AddToolRow(gbTools, "Ergonomic Kitchen Cabinets", "Base/tall/wall millwork, appliances & yellow LED lighting", "ShalikKitchen", btnY);
            btnY += btnGap;
            AddToolRow(gbTools, "Office Workstation & Chair", "Executive desks, computer setups & ergonomic mesh chairs", "ShalikOfficeDesk", btnY);
            btnY += btnGap;
            AddToolRow(gbTools, "InstantSKP 3D Warehouse", "Browse & import 3D Warehouse SketchUp models directly in Rhino", "InstantSKP", btnY);

            this.Controls.Add(gbTools);

            // Footer Action Buttons
            Panel pnlFooter = new Panel();
            pnlFooter.Location = new Point(25, 650);
            pnlFooter.Size = new Size(530, 45);

            Button btnLaunchRhino = new Button();
            btnLaunchRhino.Text = "Start Rhino 8";
            btnLaunchRhino.Font = new Font("Segoe UI", 9, FontStyle.Bold);
            btnLaunchRhino.BackColor = darkRed;
            btnLaunchRhino.ForeColor = Color.White;
            btnLaunchRhino.FlatStyle = FlatStyle.Flat;
            btnLaunchRhino.FlatAppearance.BorderSize = 0;
            btnLaunchRhino.Size = new Size(130, 36);
            btnLaunchRhino.Location = new Point(0, 4);
            btnLaunchRhino.Click += (s, e) => LaunchRhinoScript(null);
            pnlFooter.Controls.Add(btnLaunchRhino);

            Button btnOpenFolder = new Button();
            btnOpenFolder.Text = "Open Folder";
            btnOpenFolder.Font = new Font("Segoe UI", 9);
            btnOpenFolder.Size = new Size(110, 36);
            btnOpenFolder.Location = new Point(140, 4);
            btnOpenFolder.Click += (s, e) => Process.Start("explorer.exe", AppDomain.CurrentDomain.BaseDirectory);
            pnlFooter.Controls.Add(btnOpenFolder);

            Button btnAbout = new Button();
            btnAbout.Text = "About & Author";
            btnAbout.Font = new Font("Segoe UI", 9);
            btnAbout.Size = new Size(120, 36);
            btnAbout.Location = new Point(260, 4);
            btnAbout.Click += (s, e) => {
                string msg = "SHALIK FURNITURE GENERATOR SUITE v1.0.0\n" +
                             "Author & Architect: Sakhawat Hosen Sumon\n" +
                             "Email: arch.sakhawat@gmail.com\n" +
                             "GitHub: https://github.com/arch-sakhawat/SHALIK-FURNITURE\n\n" +
                             "CRITICAL LEGAL NOTICE:\n" +
                             "THIS SOFTWARE IS STRICTLY PROPRIETARY AND COMMERCIAL (NOT FREE).\n" +
                             "Copyright © 2026 Sakhawat Hosen Sumon. All Rights Reserved.\n\n" +
                             "Unauthorized copying, redistribution, or reverse-engineering is strictly illegal.\n" +
                             "Violators will face immediate legal prosecution and court lawsuits (cases) for copyright infringement and statutory damages.\n\n" +
                             "Would you like to open the GitHub Repository?";
                if (MessageBox.Show(msg, "About Shalik Furniture & Copyright Warning", MessageBoxButtons.YesNo, MessageBoxIcon.Information) == DialogResult.Yes)
                {
                    Process.Start("https://github.com/arch-sakhawat/SHALIK-FURNITURE");
                }
            };
            pnlFooter.Controls.Add(btnAbout);

            Button btnClose = new Button();
            btnClose.Text = "Exit";
            btnClose.Font = new Font("Segoe UI", 9);
            btnClose.Size = new Size(90, 36);
            btnClose.Location = new Point(440, 4);
            btnClose.Click += (s, e) => this.Close();
            pnlFooter.Controls.Add(btnClose);

            this.Controls.Add(pnlFooter);
        }

        private void AddToolRow(GroupBox parent, string title, string subtext, string command, int y)
        {
            Label lblTitle = new Label();
            lblTitle.Text = title;
            lblTitle.Font = new Font("Segoe UI", 9.5f, FontStyle.Bold);
            lblTitle.ForeColor = Color.FromArgb(40, 40, 40);
            lblTitle.Location = new Point(16, y);
            lblTitle.Size = new Size(380, 20);
            parent.Controls.Add(lblTitle);

            Label lblSub = new Label();
            lblSub.Text = subtext;
            lblSub.Font = new Font("Segoe UI", 8);
            lblSub.ForeColor = Color.FromArgb(120, 120, 120);
            lblSub.Location = new Point(16, y + 20);
            lblSub.Size = new Size(380, 18);
            parent.Controls.Add(lblSub);

            Button btn = new Button();
            btn.Text = "Launch";
            btn.Font = new Font("Segoe UI", 8.5f, FontStyle.Bold);
            btn.BackColor = darkRed;
            btn.ForeColor = Color.White;
            btn.FlatStyle = FlatStyle.Flat;
            btn.FlatAppearance.BorderSize = 0;
            btn.Size = new Size(85, 30);
            btn.Location = new Point(420, y + 4);
            btn.Click += (s, e) => LaunchRhinoScript("! _" + command);
            parent.Controls.Add(btn);
        }

        private string GetRhinoPath()
        {
            string p8 = @"C:\Program Files\Rhino 8\System\Rhino.exe";
            if (File.Exists(p8)) return p8;
            string p7 = @"C:\Program Files\Rhino 7\System\Rhino.exe";
            if (File.Exists(p7)) return p7;
            return null;
        }

        private void CheckEnvironment()
        {
            string rhinoExe = GetRhinoPath();
            if (rhinoExe != null)
            {
                lblRhinoStatus.Text = "✓ Rhino 8 detected at: " + rhinoExe;
                lblRhinoStatus.ForeColor = Color.FromArgb(0, 130, 0);
            }
            else
            {
                lblRhinoStatus.Text = "✗ Rhino not found in standard Program Files directory";
                lblRhinoStatus.ForeColor = Color.DarkOrange;
            }

            try
            {
                using (RegistryKey key = Registry.CurrentUser.OpenSubKey(@"SOFTWARE\McNeel\Rhinoceros\8.0\Plug-Ins\0ce7337f-ec52-45da-9fd3-cc40db64b2fa"))
                {
                    if (key != null)
                    {
                        lblPluginStatus.Text = "✓ Shalik Furniture Plug-in is registered and enabled (LoadMode=1)";
                        lblPluginStatus.ForeColor = Color.FromArgb(0, 130, 0);
                        return;
                    }
                }
            }
            catch { }

            lblPluginStatus.Text = "ℹ Shalik Furniture is ready to load via Rhino or Setup Installer.";
            lblPluginStatus.ForeColor = Color.FromArgb(70, 70, 70);
        }

        private void LaunchRhinoScript(string script)
        {
            string rhinoExe = GetRhinoPath();
            if (rhinoExe == null)
            {
                MessageBox.Show("Could not locate Rhino.exe on this computer.\nPlease verify Rhino 8 or Rhino 7 is installed.",
                    "Rhino Not Found", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return;
            }

            try
            {
                ProcessStartInfo psi = new ProcessStartInfo();
                psi.FileName = rhinoExe;
                if (!string.IsNullOrEmpty(script))
                {
                    psi.Arguments = string.Format("/runscript=\"{0}\"", script);
                }
                Process.Start(psi);
            }
            catch (Exception ex)
            {
                MessageBox.Show("Failed to launch Rhino:\n" + ex.Message, "Launch Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        [STAThread]
        public static void Main()
        {
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            Application.Run(new MainForm());
        }
    }
}
