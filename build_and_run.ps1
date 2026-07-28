param(
    [switch]$NoLaunch,
    [switch]$Audio,
    [switch]$NoAudio
)

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

function Find-Python {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        return @((Get-Command py).Source, '-3')
    }
    if (Get-Command python3 -ErrorAction SilentlyContinue) {
        return @((Get-Command python3).Source)
    }
    if (Get-Command python -ErrorAction SilentlyContinue) {
        return @((Get-Command python).Source)
    }
    throw 'Python 3 is required.'
}

function Invoke-ProjectPython([string[]]$Arguments) {
    $python = Find-Python
    $exe = $python[0]
    $prefix = @()
    if ($python.Count -gt 1) { $prefix = $python[1..($python.Count - 1)] }
    & $exe @prefix @Arguments
    if ($LASTEXITCODE) { throw "Python command failed: $($Arguments -join ' ')" }
}

& (Join-Path $Root 'tools\build_payload.ps1')

$mba = Join-Path $Root 'build\MobiGo2Starter.MBA'
$syDonor = Join-Path $Root 'build\SY-stock.MBA'
$editedNand = Join-Path $Root 'build\nand.edited.bin'
$sourceNand = Join-Path $Root 'firmware\nand.us-stitched.bin'
Invoke-ProjectPython @(
    (Join-Path $Root 'tools\assemble_nand.py'),
    '--output', $sourceNand
)
Invoke-ProjectPython @(
    (Join-Path $Root 'tools\extract_slot_mba.py'),
    $sourceNand,
    $syDonor,
    '--slot', 'SY',
    '--editor', (Join-Path $Root 'tools\mobigo2_nandfs_editor_v2.py')
)
Invoke-ProjectPython @(
    (Join-Path $Root 'tools\pack_g1_mba.py'),
    '--slot', 'SY',
    '--donor', $syDonor,
    '--payload', (Join-Path $Root 'build\app.bin'),
    '--output', $mba
)
Invoke-ProjectPython @(
    (Join-Path $Root 'tools\replace_g1_in_nand.py'),
    $sourceNand,
    $mba,
    $editedNand,
    '--slot', 'SY',
    '--editor', (Join-Path $Root 'tools\mobigo2_nandfs_editor_v2.py')
)

Write-Host "PASS SY MBA and edited NAND are ready in $Root\build"
if ($NoLaunch) { exit 0 }
if ($Audio -and $NoAudio) {
    throw 'Use either -Audio or -NoAudio, not both.'
}

$emulator = Join-Path $Root 'emulator\windows\mobigo2_emu.exe'
if (-not (Test-Path $emulator)) {
    throw "Windows emulator executable is missing: $emulator"
}
$arguments = @(
    '--rom', (Join-Path $Root 'firmware\internalrom.bin'),
    '--spi', (Join-Path $Root 'firmware\spi.bin'),
    '--nand', $editedNand,
    '--open-window-at', '220000000'
)
$audioEnabled = $false
if ($Audio) {
    $audioEnabled = $true
} elseif (-not $NoAudio) {
    $audioReply = Read-Host 'Emulate host audio? This makes the emulator run slower. [y/N]'
    $audioEnabled = $audioReply -match '^(?i:y|yes)$'
}
if ($audioEnabled) {
    $arguments += '--audio'
    Write-Host 'Host audio emulation enabled.'
} else {
    Write-Host 'Host audio emulation disabled for faster execution.'
}
Write-Host 'Starting Emulator2; the SY homebrew launches automatically during boot.'
Write-Host 'Press F12 in the emulator window to quit.'
$quotedArguments = foreach ($argument in $arguments) {
    if ($argument -match '[\s"]') {
        '"' + ($argument -replace '"', '\"') + '"'
    } else {
        $argument
    }
}
Start-Process -FilePath $emulator -WorkingDirectory $Root `
    -ArgumentList ($quotedArguments -join ' ')
