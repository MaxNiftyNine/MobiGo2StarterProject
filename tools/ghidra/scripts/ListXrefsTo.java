// List references to selected word addresses.
// First argument: output file. Remaining arguments: word addresses.
// @category MobiGo

import java.io.File;
import java.io.PrintWriter;

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceIterator;

public class ListXrefsTo extends GhidraScript {
    private Address wordAddress(long value) {
        return currentProgram.getAddressFactory()
            .getAddress(String.format("%06x", value));
    }

    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length < 2) {
            throw new IllegalArgumentException(
                "usage: OUTPUT WORD_ADDRESS [WORD_ADDRESS ...]");
        }
        try (PrintWriter output = new PrintWriter(new File(args[0]))) {
            for (int index = 1; index < args.length; index++) {
                monitor.checkCancelled();
                long value = Long.decode(args[index]);
                Address target = wordAddress(value);
                output.printf("=== references to 0x%06x ===%n", value);
                ReferenceIterator references =
                    currentProgram.getReferenceManager().getReferencesTo(target);
                while (references.hasNext()) {
                    Reference reference = references.next();
                    Function function =
                        getFunctionContaining(reference.getFromAddress());
                    output.printf(
                        "%s  %-24s  %s%n",
                        reference.getFromAddress(),
                        function == null ? "<no function>" : function.getName(),
                        reference.getReferenceType());
                }
                output.println();
            }
        }
    }
}
