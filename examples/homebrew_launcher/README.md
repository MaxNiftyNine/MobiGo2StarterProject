# Homebrew Launcher

`HomebrewLauncher.MBA` is an SY-profile replacement menu for homebrew stored in
`A:\HB`. Homebrew Manager owns `A:\HB\INDEX.HB`; the target firmware does not
expose a verified directory-enumeration service to applications, so the index
is the transactional bridge between the USB manager and this launcher.

Build it from the repository root:

```sh
python3 examples/homebrew_launcher/build.py
```

The resulting MBA is `build/homebrew-launcher/HomebrewLauncher.MBA`. Do not
install it over a physical system menu until that exact system MBA has been
downloaded and verified. Homebrew Manager performs that backup-first flow.

Controls:

- Up/Down: select an application
- Primary/Enter: launch it
- Left/Right: previous/next page
- Volume, Brightness, and Off retain standard system behavior

