[Setup]
AppName=Guard
AppVersion=1.0
DefaultDirName={commonpf}\Guard
DefaultGroupName=Guard
OutputDir=C:\Users\Tanvir\Desktop\distructionOfDistraction\dist
OutputBaseFilename=GuardSetup
SetupIconFile=assets\logo.ico
Compression=lzma
SolidCompression=yes

[Files]
; Include everything inside the dist/main folder (from --onedir build)
Source: "dist\main\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Start Menu Shortcut
Name: "{group}\Guard"; Filename: "{app}\main.exe"; IconFilename: "{app}\assets\logo.ico"; WorkingDir: "{app}"

; Optional: Desktop Shortcut
Name: "{commondesktop}\Guard"; Filename: "{app}\main.exe"; IconFilename: "{app}\assets\logo.ico"; WorkingDir: "{app}"

; Optional: Launch on Boot
Name: "{commonstartup}\Guard"; Filename: "{app}\main.exe"; IconFilename: "{app}\assets\logo.ico"; WorkingDir: "{app}"
