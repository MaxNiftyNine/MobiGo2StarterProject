#!/usr/bin/env python3
"""Insert a compiled payload into the verified code window of a retail G1 MBA.

This does not create an MBA from nothing. It preserves the donor's header,
loader tables, callbacks, and overall length, replacing only the code window
between the G1 entry point and the next protected callback.
"""

from __future__ import annotations

import argparse
import hashlib
import struct
from pathlib import Path


MAGIC = b"bM_gbMQa"
RUNTIME_FILE_BIAS = 0x0C8000
EXPECTED_G1_ENTRY = 0x0E1A55
EXPECTED_G1_FILE_OFFSET = 0x334AA


def u32(data: bytes | bytearray, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Place an unSP payload in a verified retail G1 MBA donor"
    )
    parser.add_argument("--donor", type=Path, required=True)
    parser.add_argument("--payload", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    donor_path = args.donor.expanduser().resolve()
    payload_path = args.payload.expanduser().resolve()
    output_path = args.output.expanduser().resolve()
    if output_path in (donor_path, payload_path):
        parser.error("output must not overwrite the donor or payload")

    donor = donor_path.read_bytes()
    payload = payload_path.read_bytes()
    if donor[:8] != MAGIC:
        raise SystemExit("donor does not have the expected bM_gbMQa magic")
    if len(donor) < 0x18:
        raise SystemExit("donor is too short")
    declared_bytes = u32(donor, 8) * 2
    if declared_bytes != len(donor):
        raise SystemExit(
            f"donor length mismatch: header={declared_bytes:#x}, "
            f"actual={len(donor):#x}"
        )
    if not payload:
        raise SystemExit("payload is empty")
    if len(payload) & 1:
        raise SystemExit("payload length must be even (unSP words are 16-bit)")

    callback = u32(donor, 0x10)
    entry = u32(donor, 0x14)
    start = (entry - RUNTIME_FILE_BIAS) * 2
    safe_end = (callback - RUNTIME_FILE_BIAS) * 2
    if entry != EXPECTED_G1_ENTRY or start != EXPECTED_G1_FILE_OFFSET:
        raise SystemExit(
            "donor does not match the verified 135804G1 layout: "
            f"entry={entry:#x}, file offset={start:#x}"
        )
    if not (start < safe_end <= len(donor)):
        raise SystemExit(
            f"invalid protected window: start={start:#x}, end={safe_end:#x}"
        )
    if start + len(payload) > safe_end:
        raise SystemExit(
            f"payload exceeds the {safe_end - start}-byte safe window by "
            f"{start + len(payload) - safe_end} bytes"
        )

    result = bytearray(donor)
    result[start : start + len(payload)] = payload
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(result)

    check = output_path.read_bytes()
    if len(check) != len(donor):
        raise SystemExit("output MBA length changed")
    if check[:start] != donor[:start] or check[safe_end:] != donor[safe_end:]:
        raise SystemExit("protected donor bytes changed")
    if check[start : start + len(payload)] != payload:
        raise SystemExit("payload read-back verification failed")

    print(f"PASS G1 entry: {entry:#x} (file offset {start:#x})")
    print(f"PASS payload: {len(payload)} / {safe_end - start} safe bytes")
    print(f"PASS donor length retained: {len(check)} bytes")
    print(f"Wrote {output_path}")
    print(f"SHA-256 {hashlib.sha256(check).hexdigest()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
