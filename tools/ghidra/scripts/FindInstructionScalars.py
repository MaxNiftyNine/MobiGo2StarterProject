# Find instructions whose operands contain selected scalar values.
# Arguments: one or more integer scalar values.
# @category MobiGo

from ghidra.program.model.scalar import Scalar

wanted = set(int(arg, 0) for arg in getScriptArgs())
listing = currentProgram.getListing()
manager = currentProgram.getFunctionManager()
count = 0

for insn in listing.getInstructions(True):
    matched = []
    for operand in range(insn.getNumOperands()):
        for obj in insn.getOpObjects(operand):
            if isinstance(obj, Scalar):
                value = obj.getUnsignedValue()
                if value in wanted:
                    matched.append(value)
    if matched:
        fn = manager.getFunctionContaining(insn.getAddress())
        fn_text = "none" if fn is None else "%s@%s" % (fn.getName(), fn.getEntryPoint())
        println("%s %s %s scalars=%s" % (
            insn.getAddress(), fn_text, insn,
            ",".join("0x%x" % value for value in sorted(set(matched)))))
        count += 1

println("count=%d" % count)
