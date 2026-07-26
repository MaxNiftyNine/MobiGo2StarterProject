$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Ide = if ($env:UNSP_IDE) {
    $env:UNSP_IDE
} else {
    'C:\Program Files (x86)\Generalplus\unSPIDE_4.1.1'
}
$Toolchain = Join-Path $Ide 'toolchain'
$Build = Join-Path $Root 'build'
$Assets = Join-Path $Root 'assets'
$PlayerBase = [uint32]0x0E1A55
$Body = Join-Path $Root 'MaxFunG1.bdy'
New-Item -ItemType Directory -Force $Build, $Assets | Out-Null

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

$source = Join-Path $Assets 'source.mp4'
if (-not (Test-Path $source)) {
    throw "Missing video asset: $source. Supply media you have permission to use."
}

$movie = Join-Path $Build 'movie.dat'
$stats = python (Join-Path $Root 'tools\encode_video.py') $source $movie --fps 10
if ($stats -notmatch 'frames=(\d+)') { throw "Could not read encoder stats: $stats" }
$frames = [int]$Matches[1]

$library = Join-Path $Ide 'library\CMacro\CMacro1232.lib'
$ary = Join-Path $Build 'MaxFun.ary'
@"
Obj: "$Build\main.obj"
Lib: "$library"
PrjPath: "$Root\"
LibPath: "$Ide\"
LibPath: "$Ide\library\CMacro"
LibPath: "$Ide\library\CLib32\lib"
IDE_Version: "4.1.1"
"@ | Set-Content $ary -Encoding Ascii

function Build-Player([uint32]$movieAddress, [uint32]$audioAddress) {
    $include = "-I$Root"
    $movieAddr = ('0x{0:X}UL' -f $movieAddress)
    $audioAddr = ('0x{0:X}UL' -f $audioAddress)
    $env:PATH = "$Toolchain;$env:PATH"
    Invoke-Native (Join-Path $Toolchain 'udocc.exe') @('-S','-O1','-Wall','-mglobal-var-iram','-mISA=2.0',"-DMOVIE_ADDR=$movieAddr","-DMOVIE_FRAMES=$frames","-DAUDIO_ADDR=$audioAddr",$include,'-o',(Join-Path $Build 'main.asm'),(Join-Path $Root 'main.c'))
    Invoke-Native (Join-Path $Toolchain 'xasm16.exe') @('-t4','-sr','-wpop',$include,'-o',(Join-Path $Build 'main.obj'),(Join-Path $Build 'main.asm'))
    Invoke-Native (Join-Path $Toolchain 'xlink16.exe') @('-as',$ary,(Join-Path $Build 'player.s37'),'-initdata','-body','GPL16250VA_CS0SRAM','-nobdy','-bfile',$Body,'-undefined-opt','__TgP190708CM','-undefined-opt','__TgP190708CL','-undefined-opt','__TgP190708M')
    $vectorStart = [uint32]($PlayerBase + 0xFFF0)
    python (Join-Path $Root 'tools\srec_to_bin.py') (Join-Path $Build 'player.s37') (Join-Path $Build 'player.bin') ('0x{0:X}' -f $PlayerBase) ('0x{0:X}' -f $vectorStart)
}

$audio = Join-Path $Assets 'badapple.pcm'
if (-not (Test-Path $audio)) {
    throw "Missing encoded audio asset: $audio (run tools\encode_audio.py first)"
}
$audioBytes = [IO.File]::ReadAllBytes($audio)

Build-Player ([uint32]($PlayerBase + 0x800)) ([uint32]($PlayerBase + 0x1000))
$program = Get-Item (Join-Path $Build 'player.bin')
$movieByteOffset = [Math]::Max(0x2000, [Math]::Floor(($program.Length + 31) / 32) * 32)
$movieAddress = [uint32]($PlayerBase + ($movieByteOffset / 2))
$movieBytes = [IO.File]::ReadAllBytes($movie)
$audioByteOffset = [Math]::Floor(($movieByteOffset + $movieBytes.Length + 31) / 32) * 32
$audioAddress = [uint32]($PlayerBase + ($audioByteOffset / 2))
Build-Player $movieAddress $audioAddress
$programBytes = [IO.File]::ReadAllBytes((Join-Path $Build 'player.bin'))
$mainLine = Select-String -Path (Join-Path $Build 'MaxFun.map') -Pattern '^_main\s+([0-9A-F]+)'
if (-not $mainLine) { throw 'Could not find _main in linker map' }
$mainAddress = [Convert]::ToUInt32($mainLine.Matches[0].Groups[1].Value, 16)
# This MBA entry is an LD application callback, not a reset vector. Jump
# directly to the self-contained player while preserving inherited IRQ/FIQ.
# The player services the loader watchdog immediately and throughout playback.
$gotoOpcode = [uint16](0xfe80 -bor (($mainAddress -shr 16) -band 0x3f))
$stubWords = [uint16[]]@(
    $gotoOpcode,
    [uint16]($mainAddress -band 0xffff)
)
for ($i = 0; $i -lt $stubWords.Length; $i++) {
    $programBytes[$i * 2] = [byte]($stubWords[$i] -band 0xff)
    $programBytes[$i * 2 + 1] = [byte]($stubWords[$i] -shr 8)
}
[IO.File]::WriteAllBytes((Join-Path $Build 'player.bin'), $programBytes)
$padding = New-Object byte[] ($movieByteOffset - $programBytes.Length)
$audioPadding = New-Object byte[] ($audioByteOffset - $movieByteOffset - $movieBytes.Length)
$out = [IO.File]::Create((Join-Path $Build 'bad_apple.bin'))
try {
    $out.Write($programBytes, 0, $programBytes.Length)
    $out.Write($padding, 0, $padding.Length)
    $out.Write($movieBytes, 0, $movieBytes.Length)
    $out.Write($audioPadding, 0, $audioPadding.Length)
    $out.Write($audioBytes, 0, $audioBytes.Length)
} finally { $out.Dispose() }
Set-Content (Join-Path $Build 'entry.txt') ('0x{0:X}' -f $PlayerBase) -Encoding Ascii
Write-Host "$stats movie_address=0x$($movieAddress.ToString('X')) audio_address=0x$($audioAddress.ToString('X')) audio_bytes=$($audioBytes.Length) final_bytes=$((Get-Item (Join-Path $Build 'bad_apple.bin')).Length)"
