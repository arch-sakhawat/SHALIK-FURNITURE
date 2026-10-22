; ==============================================================================
; Inno Setup Script: Shalik Furniture Generator Suite for Rhino 8 & 7
; Single-click Windows Installer by Sakhawat Hosen Sumon
; ==============================================================================

#define MyAppName "Shalik Furniture for Rhino 8"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Sakhawat Hosen Sumon"
#define MyAppURL "https://www.facebook.com/sakhawat.sumon2"
#define MyAppGuid "0ce7337f-ec52-45da-9fd3-cc40db64b2fa"
#define MyYakFile "shalikfurniture-1.0.0-rh8_35-any.yak"

[Setup]
AppId={{{#MyAppGuid}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={userappdata}\ShalikFurniture
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
LicenseFile=payload\LICENSE.txt
InfoBeforeFile=payload\USER_README.txt
OutputDir=..\dist
OutputBaseFilename=ShalikFurniture-Setup
SetupIconFile=payload\setup.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\setup.ico
UninstallDisplayName={#MyAppName}
VersionInfoVersion=1.0.0.0
VersionInfoTextVersion=1.0.0
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription=Shalik Furniture for Rhino 8 Setup - Created by Sakhawat Hosen Sumon
VersionInfoCopyright=Copyright © 2026 Sakhawat Hosen Sumon. Commercial Proprietary Software. All Rights Reserved.
VersionInfoProductName={#MyAppName}
VersionInfoProductVersion=1.0.0.0

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
; 1. Application folder payload
Source: "payload\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "register_furniture_plugin.ps1"; DestDir: "{app}"; Flags: ignoreversion
Source: "unregister_furniture_plugin.ps1"; DestDir: "{app}"; Flags: ignoreversion

; 2. Target Rhino 8 packages folder (1.0.0)
Source: "payload\*"; DestDir: "{userappdata}\McNeel\Rhinoceros\packages\8.0\ShalikFurniture\1.0.0"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\Shalik Furniture Hub"; Filename: "{app}\ShalikFurnitureLauncher.exe"; IconFilename: "{app}\setup.ico"
Name: "{autoprograms}\Uninstall Shalik Furniture"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Shalik Furniture Hub"; Filename: "{app}\ShalikFurnitureLauncher.exe"; IconFilename: "{app}\setup.ico"; Tasks: desktopicon

[Registry]
Root: HKCU; Subkey: "SOFTWARE\McNeel\Rhinoceros\8.0\Plug-Ins\{#MyAppGuid}"; Flags: uninsdeletekey
Root: HKCU; Subkey: "SOFTWARE\McNeel\Rhinoceros\8.0\Plug-Ins\{#MyAppGuid}"; ValueType: dword; ValueName: "LoadMode"; ValueData: "1"
Root: HKCU; Subkey: "SOFTWARE\McNeel\Rhinoceros\8.0\Plug-Ins\{#MyAppGuid}"; ValueType: string; ValueName: "EnglishName"; ValueData: "Shalik Furniture"
Root: HKCU; Subkey: "SOFTWARE\McNeel\Rhinoceros\8.0\Plug-Ins\{#MyAppGuid}"; ValueType: string; ValueName: "Name"; ValueData: "Shalik Furniture"
Root: HKCU; Subkey: "SOFTWARE\McNeel\Rhinoceros\8.0\Plug-Ins\{#MyAppGuid}"; ValueType: dword; ValueName: "Type"; ValueData: "16"
Root: HKCU; Subkey: "SOFTWARE\McNeel\Rhinoceros\8.0\Plug-Ins\{#MyAppGuid}"; ValueType: dword; ValueName: "IsDotNETPlugIn"; ValueData: "1"
Root: HKCU; Subkey: "SOFTWARE\McNeel\Rhinoceros\8.0\Plug-Ins\{#MyAppGuid}"; ValueType: string; ValueName: "RuiFile"; ValueData: "{userappdata}\McNeel\Rhinoceros\packages\8.0\ShalikFurniture\1.0.0\ShalikFurniture.rui"
Root: HKCU; Subkey: "SOFTWARE\McNeel\Rhinoceros\8.0\Plug-Ins\{#MyAppGuid}\PlugIn"; ValueType: string; ValueName: "FileName"; ValueData: "{userappdata}\McNeel\Rhinoceros\packages\8.0\ShalikFurniture\1.0.0\ShalikFurniture.rhp"

; Command List Registration
Root: HKCU; Subkey: "SOFTWARE\McNeel\Rhinoceros\8.0\Plug-Ins\{#MyAppGuid}\CommandList"; ValueType: string; ValueName: "ShalikFurniture"; ValueData: "66;ShalikFurniture"
Root: HKCU; Subkey: "SOFTWARE\McNeel\Rhinoceros\8.0\Plug-Ins\{#MyAppGuid}\CommandList"; ValueType: string; ValueName: "ArchFurniture"; ValueData: "66;ArchFurniture"
Root: HKCU; Subkey: "SOFTWARE\McNeel\Rhinoceros\8.0\Plug-Ins\{#MyAppGuid}\CommandList"; ValueType: string; ValueName: "ShalikBed"; ValueData: "66;ShalikBed"
Root: HKCU; Subkey: "SOFTWARE\McNeel\Rhinoceros\8.0\Plug-Ins\{#MyAppGuid}\CommandList"; ValueType: string; ValueName: "ArchBed"; ValueData: "66;ArchBed"
Root: HKCU; Subkey: "SOFTWARE\McNeel\Rhinoceros\8.0\Plug-Ins\{#MyAppGuid}\CommandList"; ValueType: string; ValueName: "FurnitureBed"; ValueData: "66;FurnitureBed"
Root: HKCU; Subkey: "SOFTWARE\McNeel\Rhinoceros\8.0\Plug-Ins\{#MyAppGuid}\CommandList"; ValueType: string; ValueName: "ShalikSofa"; ValueData: "66;ShalikSofa"
Root: HKCU; Subkey: "SOFTWARE\McNeel\Rhinoceros\8.0\Plug-Ins\{#MyAppGuid}\CommandList"; ValueType: string; ValueName: "ArchSofa"; ValueData: "66;ArchSofa"
Root: HKCU; Subkey: "SOFTWARE\McNeel\Rhinoceros\8.0\Plug-Ins\{#MyAppGuid}\CommandList"; ValueType: string; ValueName: "FurnitureSofa"; ValueData: "66;FurnitureSofa"
Root: HKCU; Subkey: "SOFTWARE\McNeel\Rhinoceros\8.0\Plug-Ins\{#MyAppGuid}\CommandList"; ValueType: string; ValueName: "ShalikDiningTable"; ValueData: "66;ShalikDiningTable"
Root: HKCU; Subkey: "SOFTWARE\McNeel\Rhinoceros\8.0\Plug-Ins\{#MyAppGuid}\CommandList"; ValueType: string; ValueName: "ArchDiningTable"; ValueData: "66;ArchDiningTable"
Root: HKCU; Subkey: "SOFTWARE\McNeel\Rhinoceros\8.0\Plug-Ins\{#MyAppGuid}\CommandList"; ValueType: string; ValueName: "FurnitureDiningTable"; ValueData: "66;FurnitureDiningTable"
Root: HKCU; Subkey: "SOFTWARE\McNeel\Rhinoceros\8.0\Plug-Ins\{#MyAppGuid}\CommandList"; ValueType: string; ValueName: "ShalikDiningSet"; ValueData: "66;ShalikDiningSet"
Root: HKCU; Subkey: "SOFTWARE\McNeel\Rhinoceros\8.0\Plug-Ins\{#MyAppGuid}\CommandList"; ValueType: string; ValueName: "ShalikKitchen"; ValueData: "66;ShalikKitchen"
Root: HKCU; Subkey: "SOFTWARE\McNeel\Rhinoceros\8.0\Plug-Ins\{#MyAppGuid}\CommandList"; ValueType: string; ValueName: "ArchKitchen"; ValueData: "66;ArchKitchen"
Root: HKCU; Subkey: "SOFTWARE\McNeel\Rhinoceros\8.0\Plug-Ins\{#MyAppGuid}\CommandList"; ValueType: string; ValueName: "FurnitureKitchen"; ValueData: "66;FurnitureKitchen"
Root: HKCU; Subkey: "SOFTWARE\McNeel\Rhinoceros\8.0\Plug-Ins\{#MyAppGuid}\CommandList"; ValueType: string; ValueName: "KitchenCabinet"; ValueData: "66;KitchenCabinet"
Root: HKCU; Subkey: "SOFTWARE\McNeel\Rhinoceros\8.0\Plug-Ins\{#MyAppGuid}\CommandList"; ValueType: string; ValueName: "ShalikOfficeDesk"; ValueData: "66;ShalikOfficeDesk"
Root: HKCU; Subkey: "SOFTWARE\McNeel\Rhinoceros\8.0\Plug-Ins\{#MyAppGuid}\CommandList"; ValueType: string; ValueName: "ArchOfficeDesk"; ValueData: "66;ArchOfficeDesk"
Root: HKCU; Subkey: "SOFTWARE\McNeel\Rhinoceros\8.0\Plug-Ins\{#MyAppGuid}\CommandList"; ValueType: string; ValueName: "FurnitureOfficeDesk"; ValueData: "66;FurnitureOfficeDesk"
Root: HKCU; Subkey: "SOFTWARE\McNeel\Rhinoceros\8.0\Plug-Ins\{#MyAppGuid}\CommandList"; ValueType: string; ValueName: "ShalikDesk"; ValueData: "66;ShalikDesk"
Root: HKCU; Subkey: "SOFTWARE\McNeel\Rhinoceros\8.0\Plug-Ins\{#MyAppGuid}\CommandList"; ValueType: string; ValueName: "ShalikImportSKP"; ValueData: "66;ShalikImportSKP"
Root: HKCU; Subkey: "SOFTWARE\McNeel\Rhinoceros\8.0\Plug-Ins\{#MyAppGuid}\CommandList"; ValueType: string; ValueName: "ShalikInstantSKP"; ValueData: "66;ShalikInstantSKP"
Root: HKCU; Subkey: "SOFTWARE\McNeel\Rhinoceros\8.0\Plug-Ins\{#MyAppGuid}\CommandList"; ValueType: string; ValueName: "ShalikFurnitureAbout"; ValueData: "66;ShalikFurnitureAbout"
Root: HKCU; Subkey: "SOFTWARE\McNeel\Rhinoceros\8.0\Plug-Ins\{#MyAppGuid}\CommandList"; ValueType: string; ValueName: "ShalikFurnitureLicense"; ValueData: "66;ShalikFurnitureLicense"

[Run]
; Auto-register aliases and toolbar in Rhino
Filename: "powershell.exe"; Parameters: "-ExecutionPolicy Bypass -File ""{app}\register_furniture_plugin.ps1"" -InstallDir ""{userappdata}\McNeel\Rhinoceros\packages\8.0\ShalikFurniture\1.0.0"""; StatusMsg: "Configuring Rhino 8 settings and command aliases..."; Flags: runhidden

; Optional launch options
Filename: "{app}\ShalikFurnitureLauncher.exe"; Description: "Launch Shalik Furniture Control Center"; Flags: nowait postinstall skipifsilent
Filename: "C:\Program Files\Rhino 8\System\Rhino.exe"; Description: "Launch Rhino 8"; Flags: nowait postinstall skipifsilent unchecked

[UninstallRun]
Filename: "powershell.exe"; Parameters: "-ExecutionPolicy Bypass -File ""{app}\unregister_furniture_plugin.ps1"""; Flags: runhidden
