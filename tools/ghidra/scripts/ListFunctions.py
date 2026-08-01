# List functions whose entry points fall in an inclusive word-address range.
# Arguments: START END, for example 0x21d000 0x21e000.
# @category MobiGo


args = getScriptArgs()
if len(args) != 2:
    printerr("usage: ListFunctions.py START END")
    exit()

start = int(args[0], 0)
end = int(args[1], 0)
manager = currentProgram.getFunctionManager()

for function in manager.getFunctions(True):
    entry = function.getEntryPoint().getOffset()
    if start <= entry <= end:
        println("0x%06x %s" % (entry, function.getName()))
