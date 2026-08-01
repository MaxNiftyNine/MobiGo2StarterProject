# Print references to selected resident-runtime addresses.
# Arguments are numeric word addresses.
# @category MobiGo

from ghidra.program.model.symbol import RefType


def word_address(value):
    return currentProgram.getAddressFactory().getAddress("%06x" % value)


for text in getScriptArgs():
    value = int(text, 0)
    addr = word_address(value)
    println("===== XREFS TO 0x%06x =====" % value)
    refs = getReferencesTo(addr)
    items = []
    for ref in refs:
        frm = ref.getFromAddress()
        fn = getFunctionContaining(frm)
        items.append((frm, fn.getName() if fn is not None else "<none>", str(ref.getReferenceType())))
    items.sort(key=lambda item: item[0].getOffset())
    for frm, name, kind in items:
        println("%s %-40s %s" % (frm, name, kind))
    println("count=%d" % len(items))
