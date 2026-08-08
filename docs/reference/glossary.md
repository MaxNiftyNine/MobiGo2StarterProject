# Glossary

| Term | Meaning in this project |
| --- | --- |
| **MBA** | MobiGo application container loaded into a firmware-defined slot. |
| **GAM** | Executable/resource form carried inside or alongside the application format. |
| **SY** | System-application target profile. It is the default for new projects in this repository. |
| **G1** | First game-slot profile. Retained as a legacy, explicit compatibility target. |
| **Resident firmware/runtime** | Firmware code and state that remain available while an application runs, including lifecycle, input, resource, audio, and storage services. |
| **Resident lifecycle** | Setup/step/finalize callback contract driven by the firmware-owned frame pump. |
| **Title RAM** | Application-owned RAM range used for mutable state and resource graphs. |
| **Word address** | u'nSP address measured in 16-bit words rather than bytes. Convert only with SDK helpers. |
| **Linked resource bundle** | Mutable graph of relative/tagged references registered with resident resource services. |
| **Family A / Family B** | Two recovered resident UI/graphics object families with different descriptors and rendering behavior. |
| **W / S / M audio** | Recovered effect, sequence, and music resource classes used by the resident audio engine. |
| **ADPCM36** | Recovered compressed sample encoding supported by the asset writer and emulator. |
| **PPU** | Graphics/display engine used for tile, sprite, and framebuffer presentation. |
| **SPU** | Sound processing unit used for effects and sequenced music. |
| **FTL** | Flash translation/filesystem behavior between logical files and NAND pages. |
| **Role-aware boot** | Emulator launch that overlays an MBA at the slot implied by its target metadata rather than replacing a fixed regional pathname. |
| **Copied NAND** | Disposable edited copy of a source NAND image; never the only recovery copy. |
| **Direct loop** | Application loop that owns the framebuffer and does not step resident rendering/lifecycle each frame. |
| **Clean-room** | Original implementation based on behavioral evidence and metadata, without copying retail executable code or assets. |

For current support status, use the
[capability matrix](../testing/capability-matrix.md), not historical research
notes.
