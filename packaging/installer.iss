; Inno Setup 6 script for the ZettelApp installer.
; Build with packaging/build.ps1, or: ISCC.exe /DAppVersion=1.0.0 packaging\installer.iss
;
; - Installs per user by default (no administrator rights; %LOCALAPPDATA%\Programs\ZettelApp),
;   with the standard option to install for all users instead.
; - Shows a language picker preselected with the Windows display language and stores the
;   choice in HKCU\Software\ZettelApp\ZettelApp\ui\language for the app.
; - User data (vaults in Documents, settings, backups) is never removed on uninstall.

#ifndef AppVersion
  #define AppVersion "1.0.0"
#endif

[Setup]
AppId={{6B1E3C2A-7D45-4F0B-9E3D-2C8A5F1B7E44}
AppName=ZettelApp
AppVersion={#AppVersion}
AppVerName=ZettelApp {#AppVersion}
AppPublisher=ZettelApp contributors
AppPublisherURL=https://dutrairs.github.io/ZettelApp/
AppSupportURL=https://github.com/DutraIRS/ZettelApp/issues
AppUpdatesURL=https://github.com/DutraIRS/ZettelApp/releases
VersionInfoVersion={#AppVersion}
VersionInfoDescription=ZettelApp Setup
DefaultDirName={autopf}\ZettelApp
DefaultGroupName=ZettelApp
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0.19044
OutputDir=..\dist
OutputBaseFilename=ZettelApp-Setup
SetupIconFile=..\zettelapp\resources\icon.ico
UninstallDisplayIcon={app}\ZettelApp.exe
UninstallDisplayName=ZettelApp
LicenseFile=..\LICENSE
WizardStyle=modern
Compression=lzma2/max
SolidCompression=yes
CloseApplications=yes
ShowLanguageDialog=yes
LanguageDetectionMethod=uilanguage

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"
Name: "portuguese"; MessagesFile: "compiler:Languages\Portuguese.isl"
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "french"; MessagesFile: "compiler:Languages\French.isl"
Name: "german"; MessagesFile: "compiler:Languages\German.isl"
Name: "italian"; MessagesFile: "compiler:Languages\Italian.isl"
Name: "dutch"; MessagesFile: "compiler:Languages\Dutch.isl"
Name: "catalan"; MessagesFile: "compiler:Languages\Catalan.isl"
Name: "czech"; MessagesFile: "compiler:Languages\Czech.isl"
Name: "danish"; MessagesFile: "compiler:Languages\Danish.isl"
Name: "finnish"; MessagesFile: "compiler:Languages\Finnish.isl"
Name: "hebrew"; MessagesFile: "compiler:Languages\Hebrew.isl"
Name: "japanese"; MessagesFile: "compiler:Languages\Japanese.isl"
Name: "norwegian"; MessagesFile: "compiler:Languages\Norwegian.isl"
Name: "polish"; MessagesFile: "compiler:Languages\Polish.isl"
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"
Name: "slovak"; MessagesFile: "compiler:Languages\Slovak.isl"
Name: "slovenian"; MessagesFile: "compiler:Languages\Slovenian.isl"
Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"
Name: "ukrainian"; MessagesFile: "compiler:Languages\Ukrainian.isl"

[CustomMessages]
RegisterLinks=Open zettelapp:// links (used on Anki cards) with ZettelApp
brazilianportuguese.RegisterLinks=Abrir links zettelapp:// (usados nos cartões do Anki) com o ZettelApp
portuguese.RegisterLinks=Abrir ligações zettelapp:// (usadas nos cartões do Anki) com o ZettelApp
spanish.RegisterLinks=Abrir enlaces zettelapp:// (usados en las tarjetas de Anki) con ZettelApp
french.RegisterLinks=Ouvrir les liens zettelapp:// (utilisés sur les cartes Anki) avec ZettelApp
german.RegisterLinks=zettelapp://-Links (auf Anki-Karten) mit ZettelApp öffnen
italian.RegisterLinks=Apri i link zettelapp:// (usati nelle schede di Anki) con ZettelApp
dutch.RegisterLinks=zettelapp://-koppelingen (op Anki-kaarten) openen met ZettelApp
Integration=Integration:
brazilianportuguese.Integration=Integração:
portuguese.Integration=Integração:
spanish.Integration=Integración:
french.Integration=Intégration :
german.Integration=Integration:
italian.Integration=Integrazione:
dutch.Integration=Integratie:

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "urlprotocol"; Description: "{cm:RegisterLinks}"; GroupDescription: "{cm:Integration}"

[Files]
Source: "..\dist\ZettelApp\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\LICENSE"; DestDir: "{app}"; DestName: "LICENSE.txt"; Flags: ignoreversion
Source: "..\THIRD_PARTY_NOTICES.md"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist

[Icons]
Name: "{autoprograms}\ZettelApp"; Filename: "{app}\ZettelApp.exe"; AppUserModelID: "ZettelApp.Desktop"
Name: "{autodesktop}\ZettelApp"; Filename: "{app}\ZettelApp.exe"; AppUserModelID: "ZettelApp.Desktop"; Tasks: desktopicon

[Registry]
; zettelapp:// links. HKA is HKCU for per-user installs and HKLM for all-users installs.
Root: HKA; Subkey: "Software\Classes\zettelapp"; ValueType: string; ValueName: ""; ValueData: "URL:ZettelApp note link"; Flags: uninsdeletekey; Tasks: urlprotocol
Root: HKA; Subkey: "Software\Classes\zettelapp"; ValueType: string; ValueName: "URL Protocol"; ValueData: ""; Tasks: urlprotocol
Root: HKA; Subkey: "Software\Classes\zettelapp\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: """{app}\ZettelApp.exe"",0"; Tasks: urlprotocol
Root: HKA; Subkey: "Software\Classes\zettelapp\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\ZettelApp.exe"" ""%1"""; Tasks: urlprotocol
; The language chosen in this installer, for the app's interface language.
Root: HKCU; Subkey: "Software\ZettelApp\ZettelApp\ui"; ValueType: string; ValueName: "language"; ValueData: "{language}"; Flags: uninsdeletevalue

[Run]
Filename: "{app}\ZettelApp.exe"; Description: "{cm:LaunchProgram,ZettelApp}"; Flags: nowait postinstall skipifsilent
