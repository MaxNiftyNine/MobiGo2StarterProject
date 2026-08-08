param(
    [switch]$NoLaunch,
    [switch]$Audio,
    [switch]$NoAudio,
    [ValidateSet('fast', 'accurate')]
    [string]$Mode = 'fast'
)

$ErrorActionPreference = 'Stop'
$ScriptDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
$Root = Split-Path -Parent $ScriptDirectory
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
    throw 'Python 3.10 or newer is required.'
}

if ($Audio -and $NoAudio) {
    throw 'Use either -Audio or -NoAudio, not both.'
}

$python = @(Find-Python)
$executable = $python[0]
$prefix = @()
if ($python.Count -gt 1) {
    $prefix = $python[1..($python.Count - 1)]
}
$arguments = @((Join-Path $Root 'tools\mobigo.py'))
if ($NoLaunch) {
    $arguments += 'build'
} else {
    $arguments += @('run', '--mode', $Mode)
    if ($Audio) { $arguments += '--audio' }
    if ($NoAudio) { $arguments += '--no-audio' }
}

& $executable @prefix @arguments
if ($LASTEXITCODE) {
    throw "MobiGo project command failed with status $LASTEXITCODE."
}
