[Setup]
AppName=ShieldSight
AppVersion=1.0
DefaultDirName={commonpf}\ShieldSight
DefaultGroupName=ShieldSight
OutputDir=C:\Users\Tanvir\Desktop\distructionOfDistraction\dist
OutputBaseFilename=ShieldSightSetup
SetupIconFile=dist\main\assets\logo.ico
Compression=lzma
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64

[Files]
; Include everything inside the dist/main folder (from --onedir build)
Source: "dist\main\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Start Menu Shortcut
Name: "{group}\ShieldSight"; Filename: "{app}\main.exe"; IconFilename: "{app}\assets\logo.ico"; WorkingDir: "{app}"

; Optional: Desktop Shortcut
Name: "{commondesktop}\ShieldSight"; Filename: "{app}\main.exe"; IconFilename: "{app}\assets\logo.ico"; WorkingDir: "{app}"

; Optional: Launch on Boot
Name: "{commonstartup}\ShieldSight"; Filename: "{app}\main.exe"; IconFilename: "{app}\assets\logo.ico"; WorkingDir: "{app}"
