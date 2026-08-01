# Seed MobiGo resident-service trampolines and their implementation targets.
# This Python version works in headless Ghidra installations where compiling
# the equivalent Java script is unavailable.
# @category MobiGo

from ghidra.program.model.symbol import SourceType


TABLE_BASE = 0x075c00
TABLE_END = 0x075fe0


def word_address(value):
    return currentProgram.getAddressFactory().getAddress("%06x" % value)


def read_word(address):
    return currentProgram.getMemory().getShort(address) & 0xffff


active = 0
placeholders = 0
for service in range(TABLE_BASE, TABLE_END, 2):
    entry = word_address(service)
    opcode = read_word(entry)
    low = read_word(entry.add(2))
    if opcode & 0xffc0 != 0xfe80:
        printerr("invalid resident trampoline at 0x%06x" % service)
        continue

    target_value = ((opcode & 0x3f) << 16) | low
    target = word_address(target_value)
    disassemble(entry)
    if getFunctionAt(entry) is None:
        createFunction(entry, "resident_service_%06x" % service)

    if target_value == service:
        placeholders += 1
        continue

    disassemble(target)
    if getFunctionAt(target) is None:
        createFunction(target, "resident_impl_%06x" % service)
    active += 1

println("resident services: active=%d placeholders=%d" % (active, placeholders))
