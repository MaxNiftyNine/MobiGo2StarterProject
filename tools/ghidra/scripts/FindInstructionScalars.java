// Find instructions whose operands contain selected scalar values.
// First argument: output file. Remaining arguments: integer scalar values.
// @category MobiGo

import java.io.File;
import java.io.PrintWriter;
import java.util.LinkedHashSet;
import java.util.Set;

import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.scalar.Scalar;

public class FindInstructionScalars extends GhidraScript {
    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length < 2) {
            throw new IllegalArgumentException(
                "usage: OUTPUT SCALAR [SCALAR ...]");
        }
        Set<Long> wanted = new LinkedHashSet<>();
        for (int index = 1; index < args.length; index++) {
            wanted.add(Long.decode(args[index]) & 0xffffffffL);
        }
        try (PrintWriter output = new PrintWriter(new File(args[0]))) {
            for (Instruction instruction :
                    currentProgram.getListing().getInstructions(true)) {
                monitor.checkCancelled();
                boolean match = false;
                for (int operand = 0;
                        operand < instruction.getNumOperands() && !match;
                        operand++) {
                    for (Object object : instruction.getOpObjects(operand)) {
                        if (object instanceof Scalar) {
                            long value =
                                ((Scalar)object).getUnsignedValue() & 0xffffffffL;
                            if (wanted.contains(value)) {
                                match = true;
                                break;
                            }
                        }
                    }
                }
                if (!match) {
                    continue;
                }
                Function function =
                    getFunctionContaining(instruction.getAddress());
                output.printf(
                    "%s  %-24s  %s%n",
                    instruction.getAddress(),
                    function == null ? "<no function>" : function.getName(),
                    instruction);
            }
        }
    }
}
