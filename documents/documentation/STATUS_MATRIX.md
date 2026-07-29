# Project status matrix

| Component | Emulator | Real MobiGo 2 | Recommended use |
|---|---:|---:|---|
| Color-cycle G1 callback | Confirmed | Confirmed | First hardware test |
| From-scratch SY MBA and color-cycle callback | Confirmed, normal automatic boot | Not yet confirmed | Default starter/emulator target |
| Bad Apple video V4 path | Confirmed | Confirmed | Advanced video example |
| Bad Apple audio V5 | Modeled | Silent | Do not use |
| Bad Apple audio V6 retail gate sequence | Confirmed by emulator tests | Not yet retested | Experimental |
| MobiPong | Confirmed | Not confirmed | Emulator/input reference |
| From-scratch G1 profile | Structurally/Ghidra verified; menu launch pending | Not yet confirmed | Experimental |
| G1/SY MBA generator | SY normal-boot verified | Not yet confirmed | Recommended for SY |
| G1/SY NAND installer | Read-back verified | Image operation only | Recommended on copies |
| `--mba` MM overlay | Confirmed | Not applicable | Fast MM-role testing |
| Experimental C/C++ API | Unit/emulator oriented | Not confirmed as a complete ABI | Reference/experiments |
| Open vbcc toolchain | Builds compiler locally | Not the final confirmed path | Research |

“Confirmed” means it was observed in the stated environment; it does not turn
reverse-engineered behavior into an official platform guarantee.
