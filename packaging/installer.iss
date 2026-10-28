; Inno Setup 6 script for the ZettelApp installer.
; Build with packaging/build.ps1, or: ISCC.exe /DAppVersion=1.0.0 packaging\installer.iss
;
; - Installs per user by default (no administrator rights; %LOCALAPPDATA%\Programs\ZettelApp),
;   with the standard option to install for all users instead.
; - Shows a language picker preselected with the Windows display language and stores the
;   choice in HKCU\Software\ZettelApp\ZettelApp\ui\language for the app.
; - Notes (vault folders such as Documents\ZettelApp) are never removed on uninstall. The
;   uninstaller offers, unticked, to delete settings, saved API keys, logs, cache and backups.

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
; The uninstaller's "delete my data" question (other languages use the English text).
DeleteDataTitle=Uninstall ZettelApp
brazilianportuguese.DeleteDataTitle=Desinstalar o ZettelApp
portuguese.DeleteDataTitle=Desinstalar o ZettelApp
spanish.DeleteDataTitle=Desinstalar ZettelApp
french.DeleteDataTitle=Désinstaller ZettelApp
german.DeleteDataTitle=ZettelApp deinstallieren
italian.DeleteDataTitle=Disinstalla ZettelApp
dutch.DeleteDataTitle=ZettelApp verwijderen
DeleteDataCheck=Also &delete my ZettelApp settings and data
brazilianportuguese.DeleteDataCheck=&Apagar também minhas configurações e dados do ZettelApp
portuguese.DeleteDataCheck=&Eliminar também as minhas definições e dados do ZettelApp
spanish.DeleteDataCheck=&Eliminar también mi configuración y datos de ZettelApp
french.DeleteDataCheck=&Supprimer aussi mes paramètres et données ZettelApp
german.DeleteDataCheck=Auch meine ZettelApp-Einstellungen und -Daten &löschen
italian.DeleteDataCheck=&Elimina anche le mie impostazioni e i miei dati di ZettelApp
dutch.DeleteDataCheck=Ook mijn ZettelApp-instellingen en -gegevens &verwijderen
DeleteDataNote=Removes settings, saved API keys, logs and automatic backups. Your notes are never deleted: vault folders such as Documents\ZettelApp stay where they are.
brazilianportuguese.DeleteDataNote=Remove configurações, chaves de API salvas, registros e backups automáticos. Suas notas nunca são apagadas: pastas de cofre como Documentos\ZettelApp continuam onde estão.
portuguese.DeleteDataNote=Remove definições, chaves de API guardadas, registos e cópias de segurança automáticas. As suas notas nunca são eliminadas: pastas de cofre como Documentos\ZettelApp ficam onde estão.
spanish.DeleteDataNote=Elimina la configuración, las claves de API guardadas, los registros y las copias de seguridad automáticas. Tus notas nunca se eliminan: las carpetas de bóveda como Documentos\ZettelApp se quedan donde están.
french.DeleteDataNote=Supprime les paramètres, les clés d'API enregistrées, les journaux et les sauvegardes automatiques. Vos notes ne sont jamais supprimées : les dossiers de coffre comme Documents\ZettelApp restent en place.
german.DeleteDataNote=Entfernt Einstellungen, gespeicherte API-Schlüssel, Protokolle und automatische Sicherungen. Ihre Notizen werden nie gelöscht: Tresorordner wie Dokumente\ZettelApp bleiben erhalten.
italian.DeleteDataNote=Rimuove impostazioni, chiavi API salvate, log e backup automatici. Le tue note non vengono mai eliminate: le cartelle dei vault come Documenti\ZettelApp restano dove sono.
dutch.DeleteDataNote=Verwijdert instellingen, opgeslagen API-sleutels, logboeken en automatische back-ups. Je notities worden nooit verwijderd: kluismappen zoals Documenten\ZettelApp blijven staan.
DeleteDataContinue=&Continue
brazilianportuguese.DeleteDataContinue=&Continuar
portuguese.DeleteDataContinue=&Continuar
spanish.DeleteDataContinue=&Continuar
french.DeleteDataContinue=&Continuer
german.DeleteDataContinue=&Weiter
italian.DeleteDataContinue=&Continua
dutch.DeleteDataContinue=&Doorgaan

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

[Code]
var
  DeleteUserData: Boolean;

{ Asked after the user confirmed the uninstall. Unticked by default; closing the window
  with its X button keeps the data too. }
function AskToDeleteUserData(): Boolean;
var
  Form: TSetupForm;
  Check: TNewCheckBox;
  Note: TNewStaticText;
  ContinueButton: TNewButton;
begin
  Form := CreateCustomForm(ScaleX(460), ScaleY(150), False, True);
  try
    Form.Caption := CustomMessage('DeleteDataTitle');

    Check := TNewCheckBox.Create(Form);
    Check.Parent := Form;
    Check.Left := ScaleX(16);
    Check.Top := ScaleY(16);
    Check.Width := Form.ClientWidth - ScaleX(32);
    Check.Height := ScaleY(17);
    Check.Caption := CustomMessage('DeleteDataCheck');
    Check.Checked := False;

    Note := TNewStaticText.Create(Form);
    Note.Parent := Form;
    Note.AutoSize := False;
    Note.WordWrap := True;
    Note.Left := ScaleX(34);
    Note.Top := Check.Top + Check.Height + ScaleY(6);
    Note.Width := Form.ClientWidth - Note.Left - ScaleX(16);
    Note.Height := ScaleY(52);
    Note.Caption := CustomMessage('DeleteDataNote');

    ContinueButton := TNewButton.Create(Form);
    ContinueButton.Parent := Form;
    ContinueButton.Caption := CustomMessage('DeleteDataContinue');
    ContinueButton.Width := Form.CalculateButtonWidth([ContinueButton.Caption]);
    ContinueButton.Height := ScaleY(23);
    ContinueButton.Left := Form.ClientWidth - ContinueButton.Width - ScaleX(16);
    ContinueButton.Top := Form.ClientHeight - ContinueButton.Height - ScaleY(12);
    ContinueButton.ModalResult := mrOk;
    ContinueButton.Default := True;

    Form.ActiveControl := ContinueButton;
    Form.FlipAndCenterIfNeeded(True, UninstallProgressForm, False);
    Result := (Form.ShowModal() = mrOk) and Check.Checked;
  finally
    Form.Free();
  end;
end;

{ ZettelApp can register zettelapp:// links itself (Options > Windows integration); remove
  that registration when it points at this installation, since the program is gone. }
procedure RemoveOwnLinkHandler();
var
  Command: String;
begin
  if RegQueryStringValue(HKCU, 'Software\Classes\zettelapp\shell\open\command', '', Command) and
     (Pos(Lowercase(ExpandConstant('{app}')), Lowercase(Command)) > 0) then
    RegDeleteKeyIncludingSubkeys(HKCU, 'Software\Classes\zettelapp');
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  ResultCode: Integer;
begin
  case CurUninstallStep of
    usUninstall:
      begin
        DeleteUserData := (not UninstallSilent()) and AskToDeleteUserData();
        if DeleteUserData then
          { Before the files go: the app also removes its API keys from Credential Manager. }
          Exec(ExpandConstant('{app}\ZettelApp.exe'), '--remove-user-data', '', SW_HIDE,
            ewWaitUntilTerminated, ResultCode);
      end;
    usPostUninstall:
      begin
        RemoveOwnLinkHandler();
        if DeleteUserData then
        begin
          { Whatever the app could not remove itself. Notes are never touched. }
          DelTree(ExpandConstant('{localappdata}\ZettelApp'), True, True, True);
          RegDeleteKeyIncludingSubkeys(HKCU, 'Software\ZettelApp');
        end;
      end;
  end;
end;
