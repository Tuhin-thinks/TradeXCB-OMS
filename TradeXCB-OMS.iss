; Script generated by the Inno Setup Script Wizard.
; SEE THE DOCUMENTATION FOR DETAILS ON CREATING INNO SETUP SCRIPT FILES!

#define MyAppName "TradeXCB-OMS"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "AlgoBeacon Technologies"
#define MyAppURL "http://trendmyfriend.co.in"
#define MyAppExeName "TradeXCB-OMS.exe"
#define InputBase "C:\Users\tuhin\Desktop\Python_Codes\TradeXCB-OMS-Zerodha\dist"
[Setup]
; NOTE: The value of AppId uniquely identifies this application. Do not use the same AppId value in installers for other applications.
; (To generate a new GUID, click Tools | Generate GUID inside the IDE.)
AppId={{C7D824D0-7095-42DA-84E6-9B14C00349C9}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DiskSpanning=no
DefaultDirName={autopf}\{#MyAppName}
DisableDirPage=yes
DisableProgramGroupPage=yes
; LicenseFile=C:\Users\tuhin\Desktop\Python_Codes\TrendmyFriend - SIGNALS\dist\TrendmyFriend-OIS\License.txt
InfoBeforeFile=C:\Users\tuhin\Desktop\Python_Codes\TradeXCB-OMS\Disclaimer.rtf
; Uncomment the following line to run in non administrative install mode (install for current user only.)
;PrivilegesRequired=lowest
OutputDir=C:\Users\tuhin\Documents\ISS_Compiled-TradeXCB-OMS
OutputBaseFilename={#MyAppName}_v{#MyAppVersion} (Zerodha)
SetupIconFile={#InputBase}\{#MyAppName}\app.ico
UninstallDisplayIcon={#InputBase}\{#MyAppName}\app.ico
Compression=lzma2/ultra64
SolidCompression=yes
LZMAUseSeparateProcess=yes
LZMANumBlockThreads=4
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: StartAfterInstall; Description: Launch {#MyAppName} after install

[Files]
Source: "{#InputBase}\{#MyAppName}\app.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#InputBase}\{#MyAppName}\{#MyAppExeName}"; DestDir: "{userappdata}\{#MyAppName}"; Flags: ignoreversion
Source: "{#InputBase}\{#MyAppName}\*"; DestDir: "{userappdata}\{#MyAppName}"; Flags: ignoreversion recursesubdirs createallsubdirs; Permissions: users-modify
; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{userappdata}\{#MyAppName}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{userappdata}\{#MyAppName}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{userappdata}\{#MyAppName}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait runascurrentuser skipifsilent; Tasks: StartAfterInstall

[InstallDelete]
; Delete complete folder of previously installed app before installing new version
Type: filesandordirs; Name: "{userappdata}\{#MyAppName}"

[UninstallDelete]
Type: filesandordirs; Name: "{userappdata}\{#MyAppName}"