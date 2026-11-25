#ifndef UrlPainelPadrao
#define UrlPainelPadrao "https://riobrancodosul-saude.ids.inf.br/riobrancodosul/painel/idspaiele.dll"
#endif

#ifndef UrlExtensaoPadrao
#define UrlExtensaoPadrao "https://raw.githubusercontent.com/prefeitura-rio-branco-do-sul/extensao_painel_ids_estilo/main/updates.xml"
#endif

#ifndef IdExtensaoPadrao
#define IdExtensaoPadrao "gclbcjhjbpibjakacaakcgdomkkefmaj"
#endif

[Setup]
AppName={#NomeApp}
AppPublisher={#NomePublisher}
AppVersion={#Versao}
DefaultDirName={autopf}\{#NomePublisher} {#NomeApp}
DefaultGroupName={#NomeApp}
UninstallDisplayIcon={app}\{#NomeExe}.exe
OutputDir=..\releases\v{#Versao}
OutputBaseFilename=Instalador_{#NomeInstalador}_v{#Versao}
Compression=lzma
SolidCompression=yes
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
CloseApplications=yes
RestartApplications=no
CloseApplicationsTimeout=15

[Languages]
Name: "portuguesebr"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Dirs]
Name: "{commonappdata}\{#NomePublisher} {#NomeApp}"; Permissions: users-modify
Name: "{commonappdata}\{#NomePublisher} {#NomeApp}\credentials"; Permissions: users-modify
Name: "{commonappdata}\{#NomePublisher} {#NomeApp}\logs"; Permissions: users-modify
Name: "{commonappdata}\{#NomePublisher} {#NomeApp}\chrome_profile"; Permissions: users-modify
Name: "{commonappdata}\{#NomePublisher} {#NomeApp}\updates"; Permissions: users-modify

[Files]
Source: "..\dist\main.dist\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs
Source: "..\src\ui\static\images\icone.ico"; DestDir: "{app}"
Source: "..\bin\vdd\*"; DestDir: "{app}\bin\vdd"; Flags: ignoreversion recursesubdirs
Source: "..\bin\vdd\vdd_settings.xml"; DestDir: "C:\IddSampleDriver"; Flags: ignoreversion

[Tasks]
Name: "desktopicon"; Description: "Criar ícone na área de trabalho"; Flags: unchecked

[Icons]
Name: "{group}\{#NomeApp}"; Filename: "{app}\{#NomeExe}.exe"; IconFilename: "{app}\icone.ico"
Name: "{userdesktop}\{#NomeApp}"; Filename: "{app}\{#NomeExe}.exe"; IconFilename: "{app}\icone.ico"; Tasks: desktopicon

[Registry]
Root: HKLM64; Subkey: "Software\{#NomePublisher}\{#NomeInstalador}"; ValueType: string; ValueName: "UrlPainel"; ValueData: "{code:GetUrlPainel}"; Flags: uninsdeletekey
Root: HKLM64; Subkey: "Software\{#NomePublisher}\{#NomeInstalador}"; ValueType: string; ValueName: "UrlExtensao"; ValueData: "{code:GetUrlExtensao}"; Flags: uninsdeletekey
Root: HKLM64; Subkey: "Software\{#NomePublisher}\{#NomeInstalador}"; ValueType: string; ValueName: "IdExtensao"; ValueData: "{code:GetIdExtensao}"; Flags: uninsdeletekey

; Diretivas de política para o Google Chrome e Microsoft Edge carregarem a extensão automaticamente
Root: HKLM64; Subkey: "Software\Policies\Google\Chrome\ExtensionInstallForcelist"; ValueType: string; ValueName: "1"; ValueData: "{code:GetExtensionForcelistEntry}"; Flags: uninsdeletevalue; Check: HasExtensionConfigured
Root: HKLM64; Subkey: "Software\Policies\Microsoft\Edge\ExtensionInstallForcelist"; ValueType: string; ValueName: "1"; ValueData: "{code:GetExtensionForcelistEntry}"; Flags: uninsdeletevalue; Check: HasExtensionConfigured

[Run]
Filename: "certutil.exe"; Parameters: "-addstore ""TrustedPublisher"" ""{app}\bin\vdd\mttvdd.cat"""; WorkingDir: "{app}\bin\vdd"; StatusMsg: "Aprovando certificado de hardware..."; Flags: runhidden

Filename: "pnputil.exe"; Parameters: "/add-driver ""{app}\bin\vdd\MttVDD.inf"" /install"; WorkingDir: "{app}\bin\vdd"; StatusMsg: "Registrando arquivos do driver..."; Flags: runhidden

Filename: "powershell.exe"; Parameters: "-ExecutionPolicy Bypass -Command ""$status = & '{app}\bin\vdd\devcon.exe' status Root\MttVDD; if ($status -match 'No matching devices found') {{ & '{app}\bin\vdd\devcon.exe' install '{app}\bin\vdd\MttVDD.inf' Root\MttVDD }"""; WorkingDir: "{app}\bin\vdd"; StatusMsg: "Configurando monitor auxiliar..."; Flags: runhidden

[Code]
var
  ConfigPage: TInputQueryWizardPage;

procedure InitializeWizard;
begin
  ConfigPage := CreateInputQueryPage(wpSelectDir,
    'Configuração do Sistema', 'Defina os parâmetros globais do painel.',
    'Por favor, insira as configurações de destino.');

  ConfigPage.Add('URL do Painel:', False);
  ConfigPage.Add('URL da Extensão de Estilo (updates.xml):', False);

  ConfigPage.Values[0] := '{#UrlPainelPadrao}';
  ConfigPage.Values[1] := '{#UrlExtensaoPadrao}';
end;

function GetUrlPainel(Param: String): String;
begin
  Result := Trim(ConfigPage.Values[0]);
end;

function GetUrlExtensao(Param: String): String;
begin
  Result := Trim(ConfigPage.Values[1]);
end;

function GetIdExtensao(Param: String): String;
begin
  Result := '{#IdExtensaoPadrao}';
end;

function GetExtensionForcelistEntry(Param: String): String;
begin
  if Trim(ConfigPage.Values[1]) <> '' then
    Result := '{#IdExtensaoPadrao};' + Trim(ConfigPage.Values[1])
  else
    Result := '';
end;

function HasExtensionConfigured: Boolean;
begin
  Result := Trim(ConfigPage.Values[1]) <> '';
end;
