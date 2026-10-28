param(
    [string]$OutputDir = (Join-Path ([Environment]::GetFolderPath('MyPictures')) 'OldCamera'),
    [string]$Distro
)

$ErrorActionPreference = 'Stop'
$wslArgs = @()
if ($Distro) { $wslArgs = @('-d', $Distro) }

$usbipd = Join-Path $env:ProgramFiles 'usbipd-win\usbipd.exe'
if (-not (Test-Path $usbipd)) { throw 'usbipd-win is missing. Run windows\Install.ps1 first.' }

$row = & $usbipd list | Select-String '2770:9060' | Select-Object -First 1
if (-not $row) { throw 'No camera with USB ID 2770:9060 is connected. Plug it in, switch it on and try again.' }
$busId = ($row.Line.Trim() -split '\s+')[0]

if ($row.Line -match 'Not shared') {
    $bind = Start-Process -FilePath $usbipd -ArgumentList 'bind', '--busid', $busId -Verb RunAs -Wait -PassThru
    if ($bind.ExitCode -ne 0) { throw "usbipd bind failed (exit code $($bind.ExitCode))." }
}

if ($row.Line -notmatch 'Attached') {
    & $usbipd attach --wsl --busid $busId
    if ($LASTEXITCODE -ne 0) { throw "usbipd attach failed (exit code $LASTEXITCODE)." }
    Start-Sleep -Seconds 3
}

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
$outputWsl = (& wsl.exe @wslArgs -- wslpath -a ($OutputDir -replace '\\', '/')).Trim()
& wsl.exe @wslArgs -u root -- /opt/gphoto2-sq9060/bin/sq9060-pull $outputWsl
if ($LASTEXITCODE -ne 0) { throw "Downloading from the camera failed (exit code $LASTEXITCODE)." }
