// Decompile selected MobiGo resident-service implementation targets.
// Run headless scripts with a Ghidra-supported JDK (JDK 21 for Ghidra 11.3).
// First argument: output file. Remaining arguments: service addresses.
// Prefix an implementation address with '@' to decompile it directly.
// @category MobiGo

import java.io.File;
import java.io.PrintWriter;

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;

public class DecompileResidentServices extends GhidraScript {
    private int word(Address address) throws Exception {
        return getShort(address) & 0xffff;
    }

    private Address wordAddress(long value) {
        return currentProgram.getAddressFactory()
            .getAddress(String.format("%06x", value));
    }

    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length < 2) {
            throw new IllegalArgumentException(
                "usage: OUTPUT SERVICE_ADDRESS [SERVICE_ADDRESS ...]");
        }

        DecompInterface decompiler = new DecompInterface();
        decompiler.openProgram(currentProgram);
        try (PrintWriter output = new PrintWriter(new File(args[0]))) {
            for (int i = 1; i < args.length; i++) {
                monitor.checkCancelled();
                boolean direct = args[i].startsWith("@");
                String valueText = direct ? args[i].substring(1) : args[i];
                long serviceValue = Long.decode(valueText);
                if (direct) {
                    long targetValue = serviceValue;
                    Address target = wordAddress(targetValue);
                    Function function = getFunctionContaining(target);
                    if (function == null) {
                        disassemble(target);
                        function = createFunction(target, null);
                    }
                    output.printf(
                        "=== implementation 0x%06x ===%n", targetValue);
                    writeFunction(output, decompiler, function);
                    continue;
                }
                Address service = wordAddress(serviceValue);
                int opcode = word(service);
                int low = word(service.add(2));
                if ((opcode & 0xffc0) != 0xfe80) {
                    output.printf(
                        "=== 0x%06x: invalid trampoline ===%n%n",
                        serviceValue);
                    continue;
                }
                long targetValue = ((long)(opcode & 0x3f) << 16) | low;
                Function function = getFunctionAt(wordAddress(targetValue));
                output.printf(
                    "=== service 0x%06x -> 0x%06x ===%n",
                    serviceValue, targetValue);
                writeFunction(output, decompiler, function);
            }
        }
        decompiler.dispose();
    }

    private void writeFunction(
            PrintWriter output,
            DecompInterface decompiler,
            Function function) throws Exception {
        if (function == null) {
            output.println("No implementation function.");
            output.println();
            return;
        }
        DecompileResults result =
            decompiler.decompileFunction(function, 60, monitor);
        if (!result.decompileCompleted() ||
            result.getDecompiledFunction() == null) {
            output.println("Decompilation failed: " +
                result.getErrorMessage());
        }
        else {
            output.println(result.getDecompiledFunction().getC());
        }
        output.println();
    }
}
