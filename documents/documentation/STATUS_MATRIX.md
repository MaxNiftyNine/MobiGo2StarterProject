# Project status matrix

| Component | Emulator | Real MobiGo 2 | Recommended use |
|---|---:|---:|---|
| Color-cycle G1 callback | Confirmed | Confirmed | First hardware test |
| Bad Apple video V4 path | Confirmed | Confirmed | Advanced video example |
| Bad Apple audio V5 | Modeled | Silent | Do not use |
| Bad Apple audio V6 retail gate sequence | Confirmed by emulator tests | Not yet retested | Experimental |
| MobiPong | Confirmed | Not confirmed | Emulator/input reference |
| G1 donor-preserving packer | Verified structurally | Used by confirmed demos | Recommended |
| G1 NAND replacement script | Read-back verified | Image operation only | Recommended on copies |
| `--mba` MM overlay | Confirmed | Not applicable | Fast MM-role testing |
| Experimental C/C++ API | Unit/emulator oriented | Not confirmed as a complete ABI | Reference/experiments |
| Open vbcc toolchain | Builds compiler locally | Not the final confirmed path | Research |

“Confirmed” means it was observed in the stated environment; it does not turn
reverse-engineered behavior into an official platform guarantee.
