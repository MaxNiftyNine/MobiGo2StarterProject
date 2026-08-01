# Dump instructions in one or more inclusive word-address ranges.
# Arguments: START END [START END ...]
# @category MobiGo

from ghidra.program.model.address import AddressSet

args = getScriptArgs()
if len(args) < 2 or len(args) % 2:
    raise Exception("usage: START END [START END ...]")

factory = currentProgram.getAddressFactory()
listing = currentProgram.getListing()
manager = currentProgram.getFunctionManager()
for i in range(0, len(args), 2):
    start = int(args[i], 0)
    end = int(args[i + 1], 0)
    # The u'nSP loader exposes word addresses through Ghidra's textual address
    # parser; the raw address-space offsets are byte-scaled.
    first = factory.getAddress("%06x" % start)
    last = factory.getAddress("%06x" % end)
    aset = AddressSet(first, last)
    println("===== 0x%06x..0x%06x =====" % (start, end))
    for insn in listing.getInstructions(aset, True):
        fn = manager.getFunctionContaining(insn.getAddress())
        name = "none" if fn is None else fn.getName()
        println("%s %-32s %s" % (insn.getAddress(), name, insn))
