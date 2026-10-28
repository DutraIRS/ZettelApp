<#
.SYNOPSIS
    Builds ZettelApp for Windows.

.DESCRIPTION
    Produces, in dist\:
      ZettelApp\               the app folder (ZettelApp.exe + zettelapp-mcp.exe)
      ZettelApp-Portable.zip   the same folder, zipped
      ZettelApp-Setup.exe      the installer (needs Inno Setup 6; skipped otherwise)
      SHA256SUMS.txt           checksums for the downloads

    Code signing is optional: set ZETTELAPP_SIGN_PFX (path to a .pfx certificate) and
    ZETTELAPP_SIGN_PASSWORD to sign the executables and the installer with signtool.

.EXAMPLE
    pwsh packaging/build.ps1
#>
param([switch]$SkipInstaller)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$python = "python"
if (Test-Path ".venv\Scripts\python.exe") { $python = ".venv\Scripts\python.exe" }
$version = (& $python -c "import zettelapp; print(zettelapp.__version__)").Trim()
Write-Host "Building ZettelApp $version"

function Invoke-Sign([string[]]$Files) {
    if (-not $env:ZETTELAPP_SIGN_PFX) { return }
    $signtool = Get-ChildItem "${env:ProgramFiles(x86)}\Windows Kits\10\bin" -Recurse -Filter signtool.exe -ErrorAction SilentlyContinue |
        Where-Object { $_.FullName -match "x64" } | Select-Object -Last 1
    if (-not $signtool) { throw "signtool.exe not found (install the Windows SDK)." }
    & $signtool.FullName sign /fd SHA256 /tr http://timestamp.digicert.com /td SHA256 `
        /f $env:ZETTELAPP_SIGN_PFX /p $env:ZETTELAPP_SIGN_PASSWORD $Files
    if ($LASTEXITCODE -ne 0) { throw "Signing failed." }
}

Remove-Item -Recurse -Force dist, build -ErrorAction SilentlyContinue
& $python packaging\make_version_info.py $version build\version_info.txt
& $python -m PyInstaller --noconfirm --clean --distpath dist --workpath build\pyinstaller packaging\zettelapp.spec
if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed." }

# The packaged app must import every module and build its window (offscreen, no UI shown).
$test = Start-Process -FilePath "dist\ZettelApp\ZettelApp.exe" -ArgumentList "--self-test" -Wait -PassThru
if ($test.ExitCode -ne 0) { throw "Self-test of the packaged app failed (exit code $($test.ExitCode))." }
$mcpVersion = & "dist\ZettelApp\zettelapp-mcp.exe" --version
if ($LASTEXITCODE -ne 0) { throw "Self-test of the packaged MCP server failed." }
Write-Host "Self-tests passed ($mcpVersion)"

Invoke-Sign @("dist\ZettelApp\ZettelApp.exe", "dist\ZettelApp\zettelapp-mcp.exe")
Compress-Archive -Path "dist\ZettelApp" -DestinationPath "dist\ZettelApp-Portable.zip" -Force

# Inno Setup on PATH, installed for the current user (its default since 6.3) or for everyone.
$isccPath = @(
    (Get-Command iscc.exe -ErrorAction SilentlyContinue).Source,
    "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe",
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
) | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1
if ($SkipInstaller) {
    Write-Host "Skipping the installer (-SkipInstaller)."
} elseif ($isccPath) {
    & $isccPath "/DAppVersion=$version" "packaging\installer.iss"
    if ($LASTEXITCODE -ne 0) { throw "Inno Setup failed." }
    Invoke-Sign @("dist\ZettelApp-Setup.exe")
} else {
    Write-Warning "Inno Setup 6 not found; skipping the installer. Install it from https://jrsoftware.org/isinfo.php"
}

Get-ChildItem dist -File | Where-Object { $_.Extension -in ".zip", ".exe" } | ForEach-Object {
    "$((Get-FileHash $_.FullName -Algorithm SHA256).Hash.ToLower())  $($_.Name)"
} | Set-Content -Encoding ascii "dist\SHA256SUMS.txt"
Get-Content "dist\SHA256SUMS.txt"
Write-Host "Done: $(Resolve-Path dist)"
