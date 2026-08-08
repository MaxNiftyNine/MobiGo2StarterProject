from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]


def load_cli():
    path = ROOT / "tools" / "mobigo.py"
    spec = importlib.util.spec_from_file_location("mobigo_project_cli", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ProjectCliTests(unittest.TestCase):
    @staticmethod
    def profile_bytes(profile) -> bytes:
        data = bytearray(profile.file_size)
        data[:8] = b"bM_gbMQa"
        struct.pack_into(
            "<6I",
            data,
            0x08,
            profile.file_size // 2,
            profile.field_0c,
            profile.compatibility_address,
            profile.entry_address,
            profile.body_load_address,
            0,
        )
        return bytes(data)

    def test_checked_in_project_uses_system_target(self) -> None:
        raw = json.loads((ROOT / "mobigo.project.json").read_text(encoding="utf-8"))
        self.assertEqual(raw["target"], "system")
        self.assertTrue((ROOT / raw["$schema"]).is_file())

    def test_target_aliases_never_make_g1_the_default(self) -> None:
        cli = load_cli()
        project = cli.load_project()
        self.assertEqual(project.target, "system")
        self.assertEqual(project.slot, "SY")
        self.assertEqual(cli.TARGETS["game1"], "G1")

    def test_project_paths_remain_inside_repository(self) -> None:
        cli = load_cli()
        with self.assertRaises(SystemExit):
            cli.resolve_project_path("../outside.c", "source")

    def test_default_test_gate_covers_target_and_emulator(self) -> None:
        cli = load_cli()
        self.assertIn("target-check", cli.QUICK_TEST_TARGETS)
        self.assertIn("emulator-test", cli.QUICK_TEST_TARGETS)
        self.assertIn("usb-test", cli.QUICK_TEST_TARGETS)

    def test_windows_no_make_baseline_still_runs_target_and_firmware(self) -> None:
        cli = load_cli()
        flattened = [" ".join(command) for command in cli.WINDOWS_NO_MAKE_TEST_SCRIPTS]
        self.assertTrue(any("build_target_objects.py" in command for command in flattened))
        self.assertTrue(
            any("verify_homebrew_input_emulator.py" in command for command in flattened)
        )

    def test_windows_no_make_full_test_fails_instead_of_skipping(self) -> None:
        cli = load_cli()
        with (
            mock.patch.object(sys, "argv", ["mobigo.py", "test", "--full"]),
            mock.patch.object(cli.shutil, "which", return_value=None),
            mock.patch.object(cli.platform, "system", return_value="Windows"),
        ):
            with self.assertRaisesRegex(SystemExit, "requires Make"):
                cli.main()

    def test_powershell_python_discovery_is_forced_to_an_array(self) -> None:
        launcher = (ROOT / "scripts" / "build_and_run.ps1").read_text(encoding="utf-8")
        self.assertIn("$python = @(Find-Python)", launcher)

    def test_no_build_artifact_must_match_configured_target(self) -> None:
        cli = load_cli()
        project = cli.load_project()
        with tempfile.TemporaryDirectory() as temporary:
            mba = Path(temporary) / "stale.MBA"
            mba.write_bytes(self.profile_bytes(cli.MBA_PROFILES["G1"]))
            with self.assertRaisesRegex(SystemExit, "does not match configured SY"):
                cli.validate_project_mba(project, mba)

    def test_host_emulator_cache_tracks_source_timestamps(self) -> None:
        cli = load_cli()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "emulator" / "src" / "main.cpp"
            cmake = root / "emulator" / "CMakeLists.txt"
            executable = root / "build" / "emulator-host" / "mobigo2_emu"
            for path in (source, cmake, executable):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("test", encoding="ascii")
            os.utime(source, ns=(1, 1))
            os.utime(cmake, ns=(1, 1))
            os.utime(executable, ns=(2, 2))
            original_root = cli.ROOT
            try:
                cli.ROOT = root
                self.assertFalse(cli.emulator_build_is_stale(executable))
                os.utime(source, ns=(3, 3))
                self.assertTrue(cli.emulator_build_is_stale(executable))
            finally:
                cli.ROOT = original_root


if __name__ == "__main__":
    unittest.main()
