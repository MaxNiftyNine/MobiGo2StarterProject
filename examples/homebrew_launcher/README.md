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

- Left/Right: select the previous or next application
- Touch a side icon: select it
- Touch the center icon: launch it
- Primary/Enter: launch it
- Volume, Brightness, and Off retain standard system behavior

The current launcher shows only names and a three-item horizontal carousel over
a fast light-blue wave background. It reads every icon directly from the
palette and 64×104 menu-art fields baked into that `.MBA`; no built-in launcher
icons are used. It accepts `HB02` and legacy `HB01` catalogs and loops the
checked-in low-rate PCM8 menu music. Starter builds bake menu artwork into the
MBA and emit a same-stem `.HBI` companion carrying its display title. The
special `/HB/System.MBA` recovery entry is text-only by design.
