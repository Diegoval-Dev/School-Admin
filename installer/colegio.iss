; Script de Inno Setup. Se compila con: iscc /DAppVersion=X.Y.Z installer\colegio.iss
#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif

[Setup]
AppId={{B92B15FA-4860-45A5-A599-031892BB7ADA}
AppName=Sistema del Colegio
AppVersion={#AppVersion}
AppPublisher=Colegio Mixto Presbítero "Julio González Celis"
DefaultDirName=C:\ColegioJGC\app
DisableDirPage=yes
DisableProgramGroupPage=yes
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\dist
OutputBaseFilename=Setup_ColegioJGC_v{#AppVersion}
SetupIconFile=..\assets\icono.ico
UninstallDisplayIcon={app}\ColegioJGC.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Dirs]
Name: "C:\ColegioJGC\datos"; Permissions: users-modify; Flags: uninsneveruninstall
Name: "C:\ColegioJGC\respaldos"; Permissions: users-modify; Flags: uninsneveruninstall

[Files]
Source: "..\dist\ColegioJGC\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autodesktop}\Sistema del Colegio"; Filename: "{app}\ColegioJGC.exe"; IconFilename: "{app}\ColegioJGC.exe"
Name: "{group}\Sistema del Colegio"; Filename: "{app}\ColegioJGC.exe"; IconFilename: "{app}\ColegioJGC.exe"
Name: "{group}\Restaurar respaldo"; Filename: "{app}\ColegioJGC.exe"; Parameters: "--restaurar"

[Run]
Filename: "{app}\ColegioJGC.exe"; Description: "Abrir el sistema ahora"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"
