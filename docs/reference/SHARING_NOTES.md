# Sharing, licensing, and safety notes

This folder is intended to be shareable, but it is a reverse-engineering work
product rather than an official SDK.

- VTech and MobiGo are trademarks of their respective owner.
- Generalplus IDE/compiler files and confidential/proprietary datasheets are
  not redistributed here.
- Firmware dumps and NAND/SPI images are included at the user's request for
  emulator testing. They are vendor/device data; confirm redistribution rights
  before sharing.
- Homebrew MBA outputs are generated from source and profile constants.
- Bad Apple media is not included. Users must provide media they have permission
  to process.
- `tools/nand/nandfs.py` and some historical files arrived without
  a clearly declared license. Obtain permission or clarify licensing before
  republishing them in a formally licensed project.
- No blanket open-source license is asserted for the collection. Individual
  contributors should choose and document licenses for code they own.
- Flashing or editing storage can make a device unbootable. Keep verified,
  unmodified backups and test against copies first.

The release check intentionally rejects firmware/media-like binary extensions,
personal absolute paths, and macOS metadata. It cannot determine ownership or
license status automatically.
