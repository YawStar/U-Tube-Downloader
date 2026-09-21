#define MyAppName "YawStar U-Tube Downloader"
#define MyAppVersion "1.0.0.29"
#define MyAppPublisher "YawStar"
#define MyAppURL "https://github.com/YawStar/U-Tube-Downloader"
#define MyAppExeName "YawStar U-Tube Downloader.exe"

[Setup]
AppId={{0B96A0EF-20B8-4FD5-B4A4-692861D4D5FC}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={localappdata}\Programs\YawStar\{#MyAppName}
DisableDirPage=yes
UninstallDisplayIcon={app}\{#MyAppExeName}
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
DisableProgramGroupPage=yes
LicenseFile=License Agreement.txt
InfoAfterFile=YawStar U-Tube Downloader\Changelog.txt
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=commandline
OutputDir=YawStar U-Tube Downloader_v1.0.0.29_x64_Setup
OutputBaseFilename=YawStar U-Tube Downloader_v1.0.0.29_x64_Setup
SetupIconFile=setup_icon.ico
SolidCompression=yes
VersionInfoVersion={#MyAppVersion}
VersionInfoProductVersion={#MyAppVersion}
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription={#MyAppName} Setup
VersionInfoTextVersion={#MyAppVersion}
WizardStyle=modern dynamic

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "YawStar U-Tube Downloader\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "YawStar U-Tube Downloader\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; YawStar U-Tube Downloader Folder ထဲသို့ ရောက်ရှိမည်
Name: "{autoprograms}\{#MyAppName}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autoprograms}\{#MyAppName}\Uninstall"; Filename: "{uninstallexe}"; IconFilename: "{sys}\shell32.dll"; IconIndex: 31
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
// YawStar U-Tube Downloader.exe run နေသလား စစ်ဆေး
function IsAppRunning(const FileName: String): Boolean;
var
  ResultCode: Integer;
begin
  Exec('cmd.exe', '/c tasklist /FI "IMAGENAME eq ' + FileName + '" | find /I "' + FileName + '"', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  Result := (ResultCode = 0);
end;

// YawStar U-Tube Downloader.exe ကို ပိတ်ပေး
procedure KillApp(const FileName: String);
var
  ResultCode: Integer;
begin
  Exec('cmd.exe', '/c taskkill /f /im "' + FileName + '"', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
end;

// ==========================================
// 1. Install စတင်ချိန် စစ်ဆေးခြင်း
// ==========================================
function InitializeSetup(): Boolean;
var
  PromptResult: Integer;
  AppIsRunning: Boolean;
begin
  Result := True;
  AppIsRunning := IsAppRunning('{#MyAppExeName}');

  while AppIsRunning do
  begin
    PromptResult := MsgBox('"' + '{#MyAppName}' + '" က လတ်တလော Run နေပါသည်။' #13#10#13#10 +
                           'Installation ဆက်လက်ပြုလုပ်ရန် Process ကို ပိတ်လိုပါသလား?', 
                           mbConfirmation, MB_YESNO);
    
    if PromptResult = idYes then
    begin
      KillApp('{#MyAppExeName}');
      Sleep(1000);
      AppIsRunning := IsAppRunning('{#MyAppExeName}');
    end
    else
    begin
      Result := False;
      Break;
    end;
  end;
end;

// ==========================================
// 2. Uninstall မစတင်မီ စစ်ဆေးခြင်း
// ==========================================
function InitializeUninstall(): Boolean;
var
  PromptResult: Integer;
  AppIsRunning: Boolean;
begin
  Result := True;
  AppIsRunning := IsAppRunning('{#MyAppExeName}');

  while AppIsRunning do
  begin
    PromptResult := MsgBox('"' + '{#MyAppName}' + '" က လတ်တလော Run နေပါသည်။' #13#10#13#10 +
                           'Uninstall ဆက်လက်ပြုလုပ်ရန် Process ကို ပိတ်လိုပါသလား?', 
                           mbConfirmation, MB_YESNO);
    
    if PromptResult = idYes then
    begin
      KillApp('{#MyAppExeName}');
      Sleep(1000);
      AppIsRunning := IsAppRunning('{#MyAppExeName}');
    end
    else
    begin
      Result := False;
      Break;
    end;
  end;
end;

// ==========================================
// 3. Uninstall ပြီးသွားချိန် AppData/Cache ဖျက်မလား မေးခြင်း
// ==========================================
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  AppDataDir: String;
begin
  if CurUninstallStep = usPostUninstall then
  begin
    if MsgBox('Application ၏ AppData / Cache ဖိုင်များကိုပါ လုံးဝ ဖျက်ဆီးလိုပါသလား?', 
              mbConfirmation, MB_YESNO) = idYes then
    begin
      AppDataDir := ExpandConstant('{userappdata}\YawStar\{#MyAppName}');
      if DirExists(AppDataDir) then
      begin
        DelTree(AppDataDir, True, True, True);
      end;
    end;
  end;
end;