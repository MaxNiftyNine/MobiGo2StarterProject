$ErrorActionPreference = 'Stop'

$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$ToolkitRoot = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $Root))
$BundledIde = Join-Path $ToolkitRoot 'compiler\windows\unSPIDE_4.1.1'
$Ide = if ($env:UNSP_IDE) {
    $env:UNSP_IDE
} elseif (Test-Path (Join-Path $BundledIde 'toolchain\udocc.exe')) {
    $BundledIde
} else {
    'C:\Program Files (x86)\Generalplus\unSPIDE_4.1.1'
}
$Toolchain = Join-Path $Ide 'toolchain'
$Library = Join-Path $Ide 'library\CMacro\CMacro1232.lib'
$Build = Join-Path $Root 'build'
$ProgramBase = [uint32]0x0E1A55
$Body = Join-Path $Root 'CelestePico8G1.bdy'

foreach ($required in @(
    (Join-Path $Toolchain 'udocc.exe'),
    (Join-Path $Toolchain 'xasm16.exe'),
    (Join-Path $Toolchain 'xlink16.exe'),
    $Library,
    $Body,
    (Join-Path $Root 'src\main.c'),
    (Join-Path $Root 'src\celeste.c'),
    (Join-Path $Root 'src\scaler.asm')
)) {
    if (-not (Test-Path $required)) {
        throw "Required build file is missing: $required"
    }
}
New-Item -ItemType Directory -Force $Build | Out-Null

function Invoke-Native([string]$File, [string[]]$Arguments) {
    $psi = [Diagnostics.ProcessStartInfo]::new($File)
    $psi.UseShellExecute = $false
    $quoted = foreach ($argument in $Arguments) {
        if ($argument -match '[\s"]') {
            '"' + ($argument -replace '"', '\"') + '"'
        } else {
            $argument
        }
    }
    $psi.Arguments = $quoted -join ' '
    $process = [Diagnostics.Process]::Start($psi)
    $process.WaitForExit()
    if ($process.ExitCode) {
        throw "$File failed with exit code $($process.ExitCode)"
    }
}

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

$ary = Join-Path $Build 'CelestePico8.ary'
@"
Obj: "$Build\main.obj"
Obj: "$Build\celeste.obj"
Obj: "$Build\scaler.obj"
Lib: "$Library"
PrjPath: "$Root\"
LibPath: "$Ide\"
LibPath: "$Ide\library\CMacro"
IDE_Version: "4.1.1"
"@ | Set-Content $ary -Encoding Ascii

$include = "-I$Root\src"
$env:PATH = "$Toolchain;$env:PATH"
foreach ($name in @('main', 'celeste')) {
    Invoke-Native (Join-Path $Toolchain 'udocc.exe') @(
        '-S', '-O2', '-ffast-math', '-fomit-frame-pointer',
        '-funsigned-char', '-Wall', '-mglobal-var-iram', '-mISA=2.0',
        $include, '-o', (Join-Path $Build "$name.asm"),
        (Join-Path $Root "src\$name.c")
    )
    Invoke-Native (Join-Path $Toolchain 'xasm16.exe') @(
        '-t4', '-sr', '-wpop', $include,
        '-o', (Join-Path $Build "$name.obj"),
        (Join-Path $Build "$name.asm")
    )
}
Invoke-Native (Join-Path $Toolchain 'xasm16.exe') @(
    '-t4', '-sr', '-wpop', $include,
    '-o', (Join-Path $Build 'scaler.obj'),
    (Join-Path $Root 'src\scaler.asm')
)
Invoke-Native (Join-Path $Toolchain 'xlink16.exe') @(
    '-as', $ary, (Join-Path $Build 'app.s37'), '-initdata', '-body',
    'GPL16250VA_CS0SRAM', '-nobdy', '-bfile', $Body,
    '-undefined-opt', '__TgP190708CM',
    '-undefined-opt', '__TgP190708CL',
    '-undefined-opt', '__TgP190708M'
)

$python = Find-Python
$pythonExe = $python[0]
$pythonPrefix = @()
if ($python.Count -gt 1) { $pythonPrefix = $python[1..($python.Count - 1)] }
$vectorStart = [uint32]($ProgramBase + 0xFFF0)
& $pythonExe @pythonPrefix (Join-Path $Root 'tools\srec_to_bin.py') `
    (Join-Path $Build 'app.s37') `
    (Join-Path $Build 'app.bin') `
    ('0x{0:X}' -f $ProgramBase) `
    ('0x{0:X}' -f $vectorStart)
if ($LASTEXITCODE) { throw 'srec_to_bin.py failed' }

$programBytes = [IO.File]::ReadAllBytes((Join-Path $Build 'app.bin'))
$map = Join-Path $Build 'CelestePico8.map'
$mainLine = Select-String -Path $map -Pattern '^_main\s+([0-9A-F]+)'
if (-not $mainLine) { throw 'Could not find _main in linker map' }
$mainAddress = [Convert]::ToUInt32($mainLine.Matches[0].Groups[1].Value, 16)

# The G1 handoff is an application callback, not a reset vector. Preserve
# inherited interrupts and jump directly into the hardware-safe resident main.
$gotoOpcode = [uint16](0xfe80 -bor (($mainAddress -shr 16) -band 0x3f))
$stubWords = [uint16[]]@(
    $gotoOpcode,
    [uint16]($mainAddress -band 0xffff)
)
for ($i = 0; $i -lt $stubWords.Length; $i++) {
    $programBytes[$i * 2] = [byte]($stubWords[$i] -band 0xff)
    $programBytes[$i * 2 + 1] = [byte]($stubWords[$i] -shr 8)
}
[IO.File]::WriteAllBytes((Join-Path $Build 'app.bin'), $programBytes)
Set-Content (Join-Path $Build 'entry.txt') ('0x{0:X}' -f $ProgramBase) -Encoding Ascii
Write-Host "PASS main=0x$($mainAddress.ToString('X')) payload_bytes=$($programBytes.Length)"
