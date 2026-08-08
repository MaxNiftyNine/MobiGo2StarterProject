import os
import shlex
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class SdkTargetSurfaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        candidates: list[list[str]] = []
        configured = os.environ.get("CC")
        if configured:
            candidates.append(shlex.split(configured, posix=os.name != "nt"))
        candidates.extend(([name] for name in ("cc", "clang", "gcc")))
        cls.compiler = next(
            (
                command
                for command in candidates
                if command
                and Path(command[0]).name.lower() not in ("cl", "cl.exe")
                and shutil.which(command[0]) is not None
            ),
            None,
        )
        if cls.compiler is None:
            raise unittest.SkipTest(
                "no GCC-compatible host C compiler; target-check covers u'nSP"
            )

    def compile_and_run(self, name: str, sources: list[Path]) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            executable = Path(temporary) / (
                name + (".exe" if os.name == "nt" else "")
            )
            subprocess.run(
                [
                    *self.compiler,
                    "-I",
                    str(ROOT / "include"),
                    "-std=c99",
                    "-Wall",
                    "-Wextra",
                    "-Werror",
                    *(str(source) for source in sources),
                    "-o",
                    str(executable),
                ],
                check=True,
            )
            subprocess.run([str(executable)], check=True)

    def test_hardware_matrix_mapping_is_pure_and_complete(self):
        self.compile_and_run(
            "hardware",
            [ROOT / "src" / "hardware.c", ROOT / "tests" / "test_hardware.c"],
        )

    def test_standard_controls_delegate_real_policy_and_ui(self):
        self.compile_and_run(
            "standard_controls",
            [
                ROOT / "src" / "system_controls.c",
                ROOT / "src" / "standard_controls.c",
                ROOT / "tests" / "test_standard_controls.c",
            ],
        )

    def test_direct_controls_edge_detect_and_apply_resident_settings(self):
        self.compile_and_run(
            "direct_controls",
            [
                ROOT / "src" / "system_controls.c",
                ROOT / "src" / "direct_controls.c",
                ROOT / "tests" / "test_direct_controls.c",
            ],
        )

    def test_launch_path_uses_full_launch_specific_buffer(self):
        self.compile_and_run(
            "application",
            [
                ROOT / "src" / "application.c",
                ROOT / "tests" / "test_application.c",
            ],
        )


if __name__ == "__main__":
    unittest.main()
