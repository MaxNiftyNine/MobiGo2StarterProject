# Read u'nSP 16-bit words from a Ghidra program.
# Arguments: ADDRESS COUNT [ADDRESS COUNT ...]
# @category MobiGo

args = getScriptArgs()
if len(args) % 2:
    raise ValueError("expected ADDRESS COUNT pairs")

memory = currentProgram.getMemory()
for index in range(0, len(args), 2):
    value = int(args[index], 0)
    count = int(args[index + 1], 0)
    address = currentProgram.getAddressFactory().getAddress("%06x" % value)
    println("===== WORDS 0x%06x count=%d =====" % (value, count))
    row = []
    for offset in range(count):
        addr = address.add(offset)
        try:
            word = memory.getShort(addr) & 0xffff
            row.append("%04x" % word)
        except Exception as exc:
            row.append("????")
        if len(row) == 8 or offset + 1 == count:
            println("0x%06x: %s" % (value + offset + 1 - len(row), " ".join(row)))
            row = []
