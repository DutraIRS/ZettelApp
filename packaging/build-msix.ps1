<#
.SYNOPSIS
    Packs the built app (dist\ZettelApp\) as an MSIX package for the Microsoft Store.

.DESCRIPTION
    Run after packaging/build.ps1 (which calls this at its end). Produces dist\ZettelApp.msix,
    unsigned, for uploading to Partner Center: the Store signs it.

    The package identity must match the one Partner Center reserves for the app (Product
    management > Product identity): pass -IdentityName and -Publisher with those values for a
    Store upload. The defaults are for local testing only.

    Needs the Windows SDK (makeappx.exe, makepri.exe); skipped with a warning
    when it is missing.

.EXAMPLE
    pwsh packaging/build-msix.ps1 -IdentityName 12345DutraIRS.ZettelApp -Publisher "CN=ABCD-1234"
#>
param(
    [string]$IdentityName = "DutraIRS.ZettelApp",
    [string]$Publisher = "CN=DutraIRS",
    [string]$PublisherDisplayName = "DutraIRS"
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$python = "python"
if (Test-Path ".venv\Scripts\python.exe") { $python = ".venv\Scripts\python.exe" }
$appVersion = (& $python -c "import zettelapp; print(zettelapp.__version__)").Trim()
# MSIX versions have four numbers and the Store wants the last one to be 0; a pre-release
# suffix (1.4.0-rc1) can't be expressed, so it is dropped.
$version = (($appVersion -split "-")[0] + ".0")

$sdk = Get-ChildItem "${env:ProgramFiles(x86)}\Windows Kits\10\bin" -Directory -ErrorAction SilentlyContinue |
    Where-Object { Test-Path (Join-Path $_.FullName "x64\makeappx.exe") } |
    Sort-Object Name | Select-Object -Last 1
if (-not $sdk) {
    Write-Warning "Windows SDK not found (makeappx.exe): MSIX package skipped."
    return
}
$tools = Join-Path $sdk.FullName "x64"
if (-not (Test-Path "dist\ZettelApp\ZettelApp.exe")) { throw "Build the app first: pwsh packaging/build.ps1" }
Write-Host "Packing ZettelApp $version as MSIX (SDK $($sdk.Name))"

$stage = "build\msix"
Remove-Item -Recurse -Force $stage -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force $stage | Out-Null
Copy-Item -Recurse "dist\ZettelApp\*" $stage
& $python packaging\make_msix_assets.py "$stage\Assets"
if ($LASTEXITCODE -ne 0) { throw "Drawing the MSIX logos failed." }

$languages = "en-us", "pt-br", "es", "fr", "de", "it", "ru", "ja", "ko", "zh-cn", "ar"
$resources = ($languages | ForEach-Object { "    <Resource Language=`"$_`" />" }) -join "`r`n"
$manifest = @"
<?xml version="1.0" encoding="utf-8"?>
<Package
  xmlns="http://schemas.microsoft.com/appx/manifest/foundation/windows10"
  xmlns:uap="http://schemas.microsoft.com/appx/manifest/uap/windows10"
  xmlns:uap3="http://schemas.microsoft.com/appx/manifest/uap/windows10/3"
  xmlns:desktop="http://schemas.microsoft.com/appx/manifest/desktop/windows10"
  xmlns:rescap="http://schemas.microsoft.com/appx/manifest/foundation/windows10/restrictedcapabilities"
  IgnorableNamespaces="uap uap3 desktop rescap">
  <Identity Name="$IdentityName" Publisher="$Publisher" Version="$version" ProcessorArchitecture="x64" />
  <Properties>
    <DisplayName>ZettelApp</DisplayName>
    <PublisherDisplayName>$PublisherDisplayName</PublisherDisplayName>
    <Logo>Assets\StoreLogo.png</Logo>
    <Description>A Zettelkasten: small linked notes, link suggestions, a knowledge graph and flashcards.</Description>
  </Properties>
  <Dependencies>
    <TargetDeviceFamily Name="Windows.Desktop" MinVersion="10.0.19044.0" MaxVersionTested="10.0.26100.0" />
  </Dependencies>
  <Resources>
$resources
  </Resources>
  <Applications>
    <Application Id="ZettelApp" Executable="ZettelApp.exe" EntryPoint="Windows.FullTrustApplication">
      <uap:VisualElements DisplayName="ZettelApp"
        Description="A Zettelkasten: small linked notes, link suggestions, a knowledge graph and flashcards."
        BackgroundColor="transparent" Square150x150Logo="Assets\Square150x150Logo.png"
        Square44x44Logo="Assets\Square44x44Logo.png">
        <uap:DefaultTile Wide310x150Logo="Assets\Wide310x150Logo.png" ShortName="ZettelApp" />
      </uap:VisualElements>
      <Extensions>
        <uap:Extension Category="windows.protocol">
          <uap:Protocol Name="zettelapp">
            <uap:DisplayName>ZettelApp note link</uap:DisplayName>
          </uap:Protocol>
        </uap:Extension>
        <uap3:Extension Category="windows.appExecutionAlias" Executable="zettelapp-mcp.exe"
          EntryPoint="Windows.FullTrustApplication">
          <uap3:AppExecutionAlias>
            <desktop:ExecutionAlias Alias="zettelapp-mcp.exe" />
          </uap3:AppExecutionAlias>
        </uap3:Extension>
      </Extensions>
    </Application>
  </Applications>
  <Capabilities>
    <Capability Name="internetClient" />
    <rescap:Capability Name="runFullTrust" />
  </Capabilities>
</Package>
"@
Set-Content -Path "$stage\AppxManifest.xml" -Value $manifest -Encoding utf8

# Index the logos' scale and size variants, so Windows picks the right one.
& "$tools\makepri.exe" createconfig /cf "build\priconfig.xml" /dq en-US /pv 10.0.0 /o | Out-Null
if ($LASTEXITCODE -ne 0) { throw "makepri createconfig failed." }
& "$tools\makepri.exe" new /pr $stage /cf "build\priconfig.xml" /mn "$stage\AppxManifest.xml" `
    /of "$stage\resources.pri" /o | Out-Null
if ($LASTEXITCODE -ne 0) { throw "makepri new failed." }

New-Item -ItemType Directory -Force dist | Out-Null
& "$tools\makeappx.exe" pack /d $stage /p "dist\ZettelApp.msix" /o /h SHA256 | Out-Null
if ($LASTEXITCODE -ne 0) { throw "makeappx failed." }
Write-Host "Wrote dist\ZettelApp.msix (unsigned, for Partner Center)"

