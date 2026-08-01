# Decompile selected resident-runtime functions from an emulator memory dump.
# Arguments are ADDRESS[:NAME], e.g. 0x056a68:resident_ui_a_create.
# @category MobiGo

from ghidra.app.decompiler import DecompInterface
from ghidra.program.model.symbol import SourceType


def parse_spec(spec):
    if ":" in spec:
        address_text, name = spec.split(":", 1)
    else:
        address_text, name = spec, ""
    return int(address_text, 0), name


def word_address(value):
    return currentProgram.getAddressFactory().getAddress("%06x" % value)


iface = DecompInterface()
iface.openProgram(currentProgram)

for spec in getScriptArgs():
    value, name = parse_spec(spec)
    addr = word_address(value)
    disassemble(addr)
    fn = getFunctionAt(addr)
    if fn is None:
        fn = createFunction(addr, name if name else None)
    elif name:
        fn.setName(name, SourceType.USER_DEFINED)

    if fn is None:
        printerr("FAILED create function at 0x%06x" % value)
        continue

    result = iface.decompileFunction(fn, 60, monitor)
    println("===== 0x%06x %s =====" % (value, fn.getName()))
    if result is None or not result.decompileCompleted():
        printerr("FAILED decompile 0x%06x: %s" % (
            value,
            "no result" if result is None else result.getErrorMessage(),
        ))
        continue
    println(result.getDecompiledFunction().getC())
