# Generated reports

Files in this directory are produced by tools in `../tools`. Reports may
contain hashes, offsets, sizes, and recovered metadata, but should not contain
copied retail executable bodies or extracted copyrighted artwork.

Current reports:

- `g1-vs-sy-exact.json`: exact relocated blocks between G1 and SY.
- `g1-vs-all-exact.json`: exact relocated blocks between G1 and all samples.
- `g1-shared-spf2alp-bank.json`: parsed metadata for the shared sound-patch
  bank in G1.
- `shared-spf2alp-instances.json`: locations and hashes of exact bank copies
  across the sample set.
- `system-control-data-fingerprints.json`: exact volume/backlight lookup-table
  locations in every sample.
- `g1-common-runtime-function-candidates.json`: relocated common-function
  candidates found with short instruction-word anchors.
- `g1-vs-sy-runtime-functions.json`: expanded relocated-function candidates
  for the verified G1/SY SDK comparison.
- `resident-service-calls.json`: direct far-call candidates into the fixed
  `0x075c00..0x075fff` resident-service bank across all inspected samples.
- `resident-service-targets.json`: decoded trampoline destinations from a
  runtime memory capture; contains addresses and names, not resident code.
- `g1-vs-sy-asset-bundle.json`: recovered linked-bundle addresses, counts,
  descriptor indices, and common settings-object metadata for G1 and SY.
- `asset-bundle-catalog.json`: automatic asset-bundle and standard-settings
  census across all MBA/GAM samples. Schema 3 recursively records every
  brightness/volume bitmap chunk and groups shared pixel payloads by SHA-256.
- `mba-page-load-map.json`: decoded MobiGo 2 physical page runs and compacted
  file offsets from the launcher-footer bitmap.

Generators:

- `find_exact_shared_blocks.py`
- `inspect_spf2alp_bank.py`
- `find_system_control_tables.py`
- `locate_relocated_functions.py`
- `catalog_resident_calls.py`
- `decode_resident_trampolines.py`
- `inspect_asset_bundle.py`
- `catalog_asset_bundles.py`
- `inspect_mba_page_map.py`

The Ghidra scripts under `../tools/ghidra` seed trampoline and implementation
functions in a temporary raw resident-memory import and decompile selected
targets for analysis. Generated firmware dumps and decompiler listings must
remain outside this clean-room tree.
