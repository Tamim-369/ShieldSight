[Setup]
AppName=ShieldSight
AppVersion=1.0
DefaultDirName={commonpf}\ShieldSight
DefaultGroupName=ShieldSight
OutputDir=C:\Users\Tanvir\Desktop\distructionOfDistraction\dist
OutputBaseFilename=ShieldSightSetup
SetupIconFile=assets\logo.ico
Compression=lzma
SolidCompression=yes

[Files]
Source: "C:\Users\Tanvir\Desktop\distructionOfDistraction\dist\main.exe"; DestDir: "{app}"
Source: "C:\Users\Tanvir\Desktop\distructionOfDistraction\assets\logo.ico"; DestDir: "{app}\assets"; Flags: ignoreversion


[Icons]
Name: "{group}\ShieldSight"; Filename: "{app}\main.exe"; WorkingDir: "{app}"
Name: "{commonstartup}\ShieldSight"; Filename: "{app}\main.exe"; WorkingDir: "{app}"