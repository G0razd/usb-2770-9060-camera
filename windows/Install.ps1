param(
    [string]$Distro
)

$ErrorActionPreference = 'Stop'
$wslArgs = @()
if ($Distro) { $wslArgs = @('-d', $Distro) }

if (-not (Get-Command wsl.exe -ErrorAction SilentlyContinue)) {
    throw 'WSL is not installed. Run "wsl --install", restart Windows, then run this script again.'
}

$usbipd = Join-Path $env:ProgramFiles 'usbipd-win\usbipd.exe'
if (-not (Test-Path $usbipd)) {
    winget install --id dorssel.usbipd-win --exact --accept-package-agreements --accept-source-agreements
    if ($LASTEXITCODE -ne 0) { throw "winget could not install usbipd-win (exit code $LASTEXITCODE)." }
}

$repoWindows = Split-Path -Parent $PSScriptRoot
$repoWsl = (& wsl.exe @wslArgs -- wslpath -a ($repoWindows -replace '\\', '/')).Trim()
& wsl.exe @wslArgs -u root -- bash "$repoWsl/linux/build.sh"
if ($LASTEXITCODE -ne 0) { throw "The build inside WSL failed (exit code $LASTEXITCODE)." }

Write-Host 'Done. Plug the camera in and run windows\Pull-CameraPhotos.ps1'
