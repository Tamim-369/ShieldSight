[Setup]
AppName=mindWallX
AppVersion=1.0
DefaultDirName={pf}\mindWallX
DefaultGroupName=mindWallX
OutputDir=C:\Users\Tanvir\Desktop\distruction\dist
OutputBaseFilename=mindWallXSetup
SetupIconFile=assets\logo.ico
Compression=lzma
SolidCompression=yes

[Files]
Source: "C:\Users\Tanvir\Desktop\distruction\dist\main.exe"; DestDir: "{app}"
Source: "C:\Users\Tanvir\Desktop\distruction\assets\logo.ico"; DestDir: "{app}\assets"; Flags: ignoreversion


[Icons]
Name: "{group}\mindWallX"; Filename: "{app}\main.exe"; WorkingDir: "{app}"
Name: "{commonstartup}\mindWallX"; Filename: "{app}\main.exe"; WorkingDir: "{app}"