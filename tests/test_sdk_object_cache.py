import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "build" / "build_sdk_app.py"
SPEC = importlib.util.spec_from_file_location("build_sdk_app_tool", TOOL)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class SdkObjectCacheTests(unittest.TestCase):
    def make_tree(self, temporary: str):
        root = Path(temporary) / "repo"
        source_root = root / "src"
        include_root = root / "include"
        source_root.mkdir(parents=True)
        (include_root / "sdk").mkdir(parents=True)
        source = source_root / "core.c"
        header = include_root / "sdk" / "core.h"
        transitive = include_root / "sdk" / "types.h"
        source.write_text('#include "sdk/core.h"\nint core(void) { return VALUE; }\n')
        header.write_text('#include "sdk/types.h"\n#define VALUE SDK_VALUE\n')
        transitive.write_text("#define SDK_VALUE 7\n")
        return root, source_root, include_root, source, header, transitive

    def make_context(self, root: Path, include_root: Path) -> str:
        compiler = root / "compiler.exe"
        assembler = root / "assembler.exe"
        compiler.write_bytes(b"compiler-v1")
        assembler.write_bytes(b"assembler-v1")
        return MODULE.sdk_cache_context_digest(
            compiler=compiler,
            assembler=assembler,
            include_root=include_root,
            compiler_flags=MODULE.C_COMPILE_FLAGS,
            assembler_flags=MODULE.ASSEMBLER_FLAGS,
            runner_identity="test-runner-1",
        )

    def test_transitive_source_and_header_content_invalidate_keys(self):
        with tempfile.TemporaryDirectory() as temporary:
            root, source_root, include_root, source, _, transitive = self.make_tree(
                temporary
            )
            context = self.make_context(root, include_root)
            dependencies = MODULE.cacheable_sdk_dependencies(
                source,
                sdk_sources={source},
                include_root=include_root,
                source_root=source_root,
            )
            self.assertIsNotNone(dependencies)
            self.assertIn(transitive.resolve(), dependencies)

            def key():
                current = MODULE.cacheable_sdk_dependencies(
                    source,
                    sdk_sources={source},
                    include_root=include_root,
                    source_root=source_root,
                )
                self.assertIsNotNone(current)
                return MODULE.sdk_object_cache_key(
                    source,
                    current,
                    root=root,
                    stem="core",
                    context_digest=context,
                    source_argument="Z:\\repo\\src\\core.c",
                    include_arguments=("-IZ:\\repo\\include",),
                )

            original = key()
            transitive.write_text("#define SDK_VALUE 8\n")
            after_header = key()
            self.assertNotEqual(original, after_header)
            source.write_text(
                '#include "sdk/core.h"\nint core(void) { return VALUE + 1; }\n'
            )
            self.assertNotEqual(after_header, key())

    def test_toolchain_flags_and_runner_are_part_of_context(self):
        with tempfile.TemporaryDirectory() as temporary:
            root, _, include_root, _, _, _ = self.make_tree(temporary)
            compiler = root / "compiler.exe"
            assembler = root / "assembler.exe"
            compiler.write_bytes(b"compiler-v1")
            assembler.write_bytes(b"assembler-v1")

            def context(flags=MODULE.C_COMPILE_FLAGS, runner="wine-1"):
                return MODULE.sdk_cache_context_digest(
                    compiler=compiler,
                    assembler=assembler,
                    include_root=include_root,
                    compiler_flags=flags,
                    assembler_flags=MODULE.ASSEMBLER_FLAGS,
                    runner_identity=runner,
                )

            original = context()
            compiler.write_bytes(b"compiler-v2")
            self.assertNotEqual(original, context())
            compiler.write_bytes(b"compiler-v1")
            assembler.write_bytes(b"assembler-v2")
            self.assertNotEqual(original, context())
            assembler.write_bytes(b"assembler-v1")
            self.assertNotEqual(original, context((*MODULE.C_COMPILE_FLAGS, "-g")))
            self.assertNotEqual(original, context(runner="wine-2"))

    def test_project_generated_and_unresolved_sources_are_not_cacheable(self):
        with tempfile.TemporaryDirectory() as temporary:
            root, source_root, include_root, source, _, _ = self.make_tree(temporary)
            generated = root / "build" / "generated.c"
            generated.parent.mkdir(parents=True)
            generated.write_text("int generated(void) { return 1; }\n")
            project = root / "app" / "main.c"
            project.parent.mkdir(parents=True)
            project.write_text("int main(void) { return 0; }\n")

            for candidate in (generated, project):
                self.assertIsNone(
                    MODULE.cacheable_sdk_dependencies(
                        candidate,
                        sdk_sources={source},
                        include_root=include_root,
                        source_root=source_root,
                    )
                )

            source.write_text("#include SDK_SELECTED_HEADER\n")
            self.assertIsNone(
                MODULE.cacheable_sdk_dependencies(
                    source,
                    sdk_sources={source},
                    include_root=include_root,
                    source_root=source_root,
                )
            )

    def test_current_sdk_sources_have_closed_local_dependency_graphs(self):
        source_root = ROOT / "src"
        include_root = ROOT / "include"
        sdk_sources = {
            *(source_root / name for name in MODULE.CORE_SOURCES),
            source_root / "standard_controls.c",
        }
        for source in sorted(sdk_sources):
            with self.subTest(source=source.name):
                dependencies = MODULE.cacheable_sdk_dependencies(
                    source,
                    sdk_sources=sdk_sources,
                    include_root=include_root,
                    source_root=source_root,
                )
                self.assertIsNotNone(dependencies)
                self.assertIn(source.resolve(), dependencies)

    def test_atomic_round_trip_across_outputs_and_corruption_repair(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            cache = directory / "cache"
            cold = directory / "cold"
            warm = directory / "warm"
            cold.mkdir()
            key = "a1" * 32
            cold_asm = cold / "core.asm"
            cold_obj = cold / "core.obj"
            cold_asm.write_bytes(b"assembly bytes")
            cold_obj.write_bytes(b"object bytes")
            MODULE.store_sdk_object(
                cache,
                key,
                assembly_output=cold_asm,
                object_output=cold_obj,
            )

            self.assertTrue(
                MODULE.restore_sdk_object(
                    cache,
                    key,
                    assembly_output=warm / "core.asm",
                    object_output=warm / "core.obj",
                )
            )
            self.assertEqual((warm / "core.asm").read_bytes(), cold_asm.read_bytes())
            self.assertEqual((warm / "core.obj").read_bytes(), cold_obj.read_bytes())

            entry = MODULE._cache_entry(cache, key)
            (entry / "object.obj").write_bytes(b"corrupt")
            self.assertFalse(
                MODULE.restore_sdk_object(
                    cache,
                    key,
                    assembly_output=warm / "again.asm",
                    object_output=warm / "again.obj",
                )
            )
            MODULE.store_sdk_object(
                cache,
                key,
                assembly_output=cold_asm,
                object_output=cold_obj,
            )
            self.assertTrue(
                MODULE.restore_sdk_object(
                    cache,
                    key,
                    assembly_output=warm / "repaired.asm",
                    object_output=warm / "repaired.obj",
                )
            )


if __name__ == "__main__":
    unittest.main()
