# List analyzed resident-runtime functions in a word-address range.
# Arguments: START END.
# @category MobiGo

start = int(getScriptArgs()[0], 0)
end = int(getScriptArgs()[1], 0)
manager = currentProgram.getFunctionManager()
it = manager.getFunctions(True)
seen = 0
matched = 0
while it.hasNext():
    fn = it.next()
    seen += 1
    off = fn.getEntryPoint().getOffset()
    if start <= off < end:
        matched += 1
        println("0x%06x %s %s" % (off, fn.getName(), fn.getBody()))
println("seen=%d matched=%d range=0x%06x..0x%06x" % (seen, matched, start, end))
