$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Ide = if ($env:UNSP_IDE) {
    $env:UNSP_IDE
} else {
    'C:\Program Files (x86)\Generalplus\unSPIDE_4.1.1'
}
$Toolchain = Join-Path $Ide 'toolchain'
$Build = Join-Path $Root 'build'
$PlayerBase = [uint32]0x0E1A55
$Body = Join-Path $Root 'ColorCycleG1.bdy'
New-Item -ItemType Directory -Force $Build | Out-Null

function Invoke-Native([string]$File, [string[]]$Arguments) {
    $psi = [Diagnostics.ProcessStartInfo]::new($File)
    $psi.UseShellExecute = $false
    $quoted = foreach ($arg in $Arguments) {
        if ($arg -match '[\s"]') { '"' + ($arg -replace '"', '\"') + '"' } else { $arg }
    }
    $psi.Arguments = $quoted -join ' '
    $process = [Diagnostics.Process]::Start($psi)
    $process.WaitForExit()
    if ($process.ExitCode) { throw "$File failed with exit code $($process.ExitCode)" }
}

$library = Join-Path $Ide 'library\CMacro\CMacro1232.lib'
$ary = Join-Path $Build 'ColorCycle.ary'
@"
Obj: "$Build\main.obj"
Lib: "$library"
PrjPath: "$Root\"
LibPath: "$Ide\"
LibPath: "$Ide\library\CMacro"
LibPath: "$Ide\library\CLib32\lib"
IDE_Version: "4.1.1"
"@ | Set-Content $ary -Encoding Ascii

$include = "-I$Root"
$env:PATH = "$Toolchain;$env:PATH"
Invoke-Native (Join-Path $Toolchain 'udocc.exe') @('-S','-O1','-Wall','-mglobal-var-iram','-mISA=2.0',$include,'-o',(Join-Path $Build 'main.asm'),(Join-Path $Root 'src\main.c'))
Invoke-Native (Join-Path $Toolchain 'xasm16.exe') @('-t4','-sr','-wpop',$include,'-o',(Join-Path $Build 'main.obj'),(Join-Path $Build 'main.asm'))
Invoke-Native (Join-Path $Toolchain 'xlink16.exe') @('-as',$ary,(Join-Path $Build 'color_cycle.s37'),'-initdata','-body','GPL16250VA_CS0SRAM','-nobdy','-bfile',$Body,'-undefined-opt','__TgP190708CM','-undefined-opt','__TgP190708CL','-undefined-opt','__TgP190708M')

$vectorStart = [uint32]($PlayerBase + 0xFFF0)
python (Join-Path $Root 'tools\srec_to_bin.py') (Join-Path $Build 'color_cycle.s37') (Join-Path $Build 'color_cycle.bin') ('0x{0:X}' -f $PlayerBase) ('0x{0:X}' -f $vectorStart)

$programBytes = [IO.File]::ReadAllBytes((Join-Path $Build 'color_cycle.bin'))
$mainLine = Select-String -Path (Join-Path $Build 'ColorCycle.map') -Pattern '^_main\s+([0-9A-F]+)'
if (-not $mainLine) { throw 'Could not find _main in linker map' }
$mainAddress = [Convert]::ToUInt32($mainLine.Matches[0].Groups[1].Value, 16)

# The MBA entry is an OS callback, not a standalone reset vector. Jump into
# main without running C startup; main performs one update and RETFs back to
# the retail caller.
$gotoOpcode = [uint16](0xfe80 -bor (($mainAddress -shr 16) -band 0x3f))
$stubWords = [uint16[]]@(
    $gotoOpcode,
    [uint16]($mainAddress -band 0xffff)
)
for ($i = 0; $i -lt $stubWords.Length; $i++) {
    $programBytes[$i * 2] = [byte]($stubWords[$i] -band 0xff)
    $programBytes[$i * 2 + 1] = [byte]($stubWords[$i] -shr 8)
}
[IO.File]::WriteAllBytes((Join-Path $Build 'color_cycle.bin'), $programBytes)
Set-Content (Join-Path $Build 'entry.txt') ('0x{0:X}' -f $PlayerBase) -Encoding Ascii
Write-Host "main=0x$($mainAddress.ToString('X')) program_bytes=$($programBytes.Length)"
