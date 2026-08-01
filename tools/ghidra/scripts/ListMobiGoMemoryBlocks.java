// List MBA/GAM memory blocks and recovered loader metadata for headless checks.
// First argument: output file.
// @category MobiGo

import java.io.File;
import java.io.PrintWriter;

import ghidra.app.script.GhidraScript;
import ghidra.framework.options.Options;
import ghidra.program.model.listing.Program;
import ghidra.program.model.mem.MemoryBlock;

public class ListMobiGoMemoryBlocks extends GhidraScript {
    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 1) {
            throw new IllegalArgumentException("usage: OUTPUT");
        }
        try (PrintWriter output = new PrintWriter(new File(args[0]))) {
            for (MemoryBlock block : currentProgram.getMemory().getBlocks()) {
                output.printf(
                    "%s %s..%s bytes=%#x rwx=%d%d%d source=%s%n",
                    block.getName(), block.getStart(), block.getEnd(),
                    block.getSize(),
                    block.isRead() ? 1 : 0,
                    block.isWrite() ? 1 : 0,
                    block.isExecute() ? 1 : 0,
                    block.getSourceName());
            }
            Options info = currentProgram.getOptions(Program.PROGRAM_INFO);
            for (String name : info.getOptionNames()) {
                if (name.startsWith("MBA ")) {
                    output.printf("%s=%s%n", name, info.getString(name, ""));
                }
            }
        }
    }
}
