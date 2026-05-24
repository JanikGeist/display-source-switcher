; Inno Setup script for ScreenSwitchWidget
; Build: iscc /DAppVersion=0.1.0 installer.iss

#ifndef AppVersion
  #define AppVersion "0.1.0"
#endif

[Setup]
AppName=ScreenSwitchWidget
AppVersion={#AppVersion}
AppPublisher=Janik Geist
AppPublisherURL=https://github.com/janik-geist/ScreenSwitchWidget
DefaultDirName={localappdata}\ScreenSwitchWidget
DefaultGroupName=ScreenSwitchWidget
OutputDir=Output
OutputBaseFilename=ScreenSwitchWidget-{#AppVersion}-Setup
Compression=lzma2
SolidCompression=yes
DisableProgramGroupPage=yes
; No admin rights needed — installs per-user
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=commandline

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "dist\ScreenSwitchWidget.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{userstartmenu}\ScreenSwitchWidget"; Filename: "{app}\ScreenSwitchWidget.exe"

[Tasks]
Name: "startup"; \
  Description: "Start ScreenSwitchWidget automatically when Windows starts"; \
  GroupDescription: "Startup:"; \
  Flags: unchecked

[Registry]
; Optional startup entry (only created if user selects the task above)
Root: HKCU; \
  Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; \
  ValueType: string; \
  ValueName: "ScreenSwitchWidget"; \
  ValueData: """{app}\ScreenSwitchWidget.exe"""; \
  Flags: uninsdeletevalue; \
  Tasks: startup

[UninstallDelete]
Type: dirifempty; Name: "{app}"

[Run]
Filename: "{app}\ScreenSwitchWidget.exe"; \
  Description: "Launch ScreenSwitchWidget now"; \
  Flags: nowait postinstall skipifsilent
