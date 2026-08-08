# Generated metadata reports

The JSON files in this directory are reproducible catalogs of hashes, offsets,
sizes, descriptors, and call targets. They must not contain copied retail code,
artwork, audio, private identifiers, or firmware dumps.

| Reports | Generator under `tools/re/` |
| --- | --- |
| `g1-vs-sy-exact.json`, `g1-vs-all-exact.json` | `find_exact_shared_blocks.py` |
| `g1-shared-spf2alp-bank.json`, `shared-spf2alp-instances.json` | `inspect_spf2alp_bank.py` |
| `system-control-data-fingerprints.json` | `find_system_control_tables.py` |
| `g1-common-runtime-function-candidates.json`, `g1-vs-sy-runtime-functions.json` | `locate_relocated_functions.py` |
| `resident-service-calls.json` | `catalog_resident_calls.py` |
| `resident-service-targets.json` | `decode_resident_trampolines.py` |
| `g1-vs-sy-asset-bundle.json` | `inspect_asset_bundle.py` |
| `asset-bundle-catalog.json` | `catalog_asset_bundles.py` |
| `audio-resource-catalog.json` | `catalog_audio_resources.py` |
| `family-a-catalog.json`, `g1-family-a-poweroff.json` | `catalog_family_a.py` |
| `family-b-catalog.json` | `catalog_family_b.py` |
| `mba-page-load-map.json` | `inspect_mba_page_map.py` |

Run generators from the repository root so their project-relative paths are
stable. Ghidra helpers live under `tools/ghidra/`; large temporary imports,
decompiler listings, and firmware captures stay outside this clean-room tree.
