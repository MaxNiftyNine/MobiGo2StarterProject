# Claude repository guidance

Follow [`AGENTS.md`](AGENTS.md) as the canonical development contract. In
particular, use `python3 tools/mobigo.py`, keep new projects on the SY system
profile, respect the direct-MBA memory/startup restrictions, use SDK hardware
helpers instead of duplicated MMIO, preserve standard system controls, and run
the required emulator tests before reporting success.
