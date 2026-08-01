# Print the containing function for selected word addresses.
# Arguments: ADDRESS [ADDRESS ...]
# @category MobiGo


def word_address(value):
    return currentProgram.getAddressFactory().getAddress("%06x" % value)


for spec in getScriptArgs():
    value = int(spec, 0)
    addr = word_address(value)
    fn = getFunctionContaining(addr)
    if fn is None:
        println("0x%06x <no function>" % value)
    else:
        println(
            "0x%06x -> 0x%06x %s %s" % (
                value,
                fn.getEntryPoint().getOffset() // 2,
                fn.getName(),
                fn.getBody(),
            )
        )
