// Dump analyzed instructions around selected u'nSP word addresses.
// First argument: output file. Remaining arguments: center addresses.
// @category MobiGo

import java.io.File;
import java.io.PrintWriter;

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.address.AddressSet;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;

public class DumpInstructions extends GhidraScript {
    private static final long RADIUS_WORDS = 0x80;

    private Address wordAddress(long value) {
        return currentProgram.getAddressFactory()
            .getAddress(String.format("%06x", value));
    }

    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length < 2) {
            throw new IllegalArgumentException(
                "usage: OUTPUT CENTER_ADDRESS [CENTER_ADDRESS ...]");
        }

        try (PrintWriter output = new PrintWriter(new File(args[0]))) {
            for (int i = 1; i < args.length; i++) {
                monitor.checkCancelled();
                long centerValue = Long.decode(args[i]);
                Address center = wordAddress(centerValue);
                Function containing = getFunctionContaining(center);
                output.printf(
                    "=== center 0x%06x function %s ===%n",
                    centerValue,
                    containing == null
                        ? "none"
                        : containing.getName() + "@" +
                            containing.getEntryPoint());
                AddressSet range = new AddressSet(
                    wordAddress(centerValue - RADIUS_WORDS),
                    wordAddress(centerValue + RADIUS_WORDS));
                InstructionIterator instructions =
                    currentProgram.getListing().getInstructions(range, true);
                while (instructions.hasNext()) {
                    Instruction instruction = instructions.next();
                    output.printf(
                        "%s: %s%n",
                        instruction.getAddress(),
                        instruction.toString());
                }
                output.println();
            }
        }
    }
}
