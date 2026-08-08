# Source confidence and claim labels

This project documents reverse-engineered behavior. Every important claim
should make its evidence boundary visible instead of presenting all findings
as equally certain.

## Labels

| Label | Meaning | Appropriate wording |
| --- | --- | --- |
| **Verified** | Reproduced by a named automated test or observed on physical hardware. | State the environment and the behavior actually observed. |
| **Emulator-inferred** | Consistent with firmware analysis and the emulator model, but not yet isolated on hardware. | Safe for emulator work; keep physical claims conditional. |
| **Firmware-derived** | Recovered from callers, tables, disassembly, or runtime captures. | Describe the evidence and avoid claiming an official ABI. |
| **Unknown** | Evidence is incomplete, conflicting, or limited to one revision. | State the missing experiment and design conservatively. |
| **Historical** | Useful earlier research whose status or recommended workflow is superseded. | Link to the current page before the archived material. |

“Supported” in the [capability matrix](../testing/capability-matrix.md) means the
repository has an implemented and tested path within the stated boundary. It
does not mean VTech or Generalplus published or guarantees the interface.

## Evidence hierarchy

Prefer evidence in this order when changing public guidance:

1. a reproducible physical-console result, with hardware/firmware context;
2. an automated emulator integration test that exercises the actual target
   binary and firmware path;
3. a target compile/link check plus a focused host unit test;
4. independent firmware callers or runtime captures;
5. a single disassembly pattern, data-table resemblance, or analogy.

Lower-ranked evidence can still be valuable, but it should not silently
become a physical-hardware guarantee.

## Recording a new finding

Record the exact command, input artifact hash when relevant, observed result,
and the environment. Add or update a regression before changing the
[capability matrix](../testing/capability-matrix.md). Keep raw notes under
`research/`; promote only stable developer guidance into the main site.

Do not include retail executable bodies, extracted artwork, private device
identifiers, or firmware dumps in metadata reports. See
[Licensing and safety](licensing-safety.md).
