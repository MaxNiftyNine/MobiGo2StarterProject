# Sharing, licensing, and safety notes

This folder is intended to be shareable, but it is a reverse-engineering work
product rather than an official SDK.

- VTech and MobiGo are trademarks of their respective owner.
- Generalplus IDE/compiler files and confidential/proprietary datasheets are
  not redistributed here.
- Firmware dumps, NAND/SPI images, and one retail MBA donor are included at the
  user's request because they are needed for the documented development flow.
  They are vendor/device data; confirm redistribution rights before sharing.
- Donor-derived patched homebrew MBA outputs are still excluded.
- Bad Apple media is not included. Users must provide media they have permission
  to process.
- `tools/mobigo2_nandfs_editor_v2.py` and some historical files arrived without
  a clearly declared license. Obtain permission or clarify licensing before
  republishing them in a formally licensed project.
- No blanket open-source license is asserted for the collection. Individual
  contributors should choose and document licenses for code they own.
- Flashing or editing storage can make a device unbootable. Keep verified,
  unmodified backups and test against copies first.

The release check intentionally rejects firmware/media-like binary extensions,
personal absolute paths, and macOS metadata. It cannot determine ownership or
license status automatically.
