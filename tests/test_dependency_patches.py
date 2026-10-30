"""Exercise real Git repositories, including restored and conflicting sources."""

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


project_dir = Path(__file__).resolve().parents[1]
patcher = project_dir / "dependency-patches/apply_dependency_patches.py"
installer = project_dir / "dependency-patches/install_dependency_patch_command.py"


class dependency_patch_tests(unittest.TestCase):
	def setUp(self):
		self.temporary = tempfile.TemporaryDirectory()
		self.addCleanup(self.temporary.cleanup)
		self.root = Path(self.temporary.name)
		self.source = self.root / "source"
		self.source.mkdir()
		self.git("init", "--quiet")
		self.git("config", "user.name", "Patch tests")
		self.git("config", "user.email", "patch-tests@example.invalid")
		self.git("config", "core.autocrlf", "false")
		(self.source / "first.txt").write_text("before\n", newline="\n")
		(self.source / "second.txt").write_text("before\n", newline="\n")
		self.git("add", ".")
		self.git("commit", "--quiet", "-m", "base")
		self.base = self.git("rev-parse", "HEAD").stdout.strip()

	def git(self, *args):
		return subprocess.run(
			["git", *args], cwd=self.source, check=True, capture_output=True, text=True,
		)

	def make_patch(self, name, files):
		for filename, text in files.items():
			(self.source / filename).write_text(text, newline="\n")
		self.git("add", ".")
		self.git("commit", "--quiet", "-m", name)
		patch_path = self.root / name
		patch_path.write_text(self.git("format-patch", "-1", "--stdout", "--full-index").stdout, newline="\n")
		return patch_path

	def run_patcher(self, *patch_paths):
		return subprocess.run(
			[sys.executable, str(patcher), *(str(path) for path in patch_paths)],
			cwd=self.source, capture_output=True, text=True,
		)

	def test_fresh_and_repeated_series(self):
		self.make_patch("0001.patch", {"first.txt": "after\n"})
		self.make_patch("0002.patch", {"second.txt": "after\n"})
		self.git("reset", "--hard", self.base)
		result = self.run_patcher(self.root / "*.patch")
		self.assertEqual(result.returncode, 0, result.stderr)
		head = self.git("rev-parse", "HEAD").stdout
		result = self.run_patcher(self.root / "*.patch")
		self.assertEqual(result.returncode, 0, result.stderr)
		self.assertEqual(result.stdout.count("Already applied:"), 2)
		self.assertEqual(self.git("rev-parse", "HEAD").stdout, head)
		self.assertEqual((self.source / "second.txt").read_text(), "after\n")

	def test_cached_shallow_source_without_patch_ancestor(self):
		first = self.make_patch("0001.patch", {"first.txt": "after\n"})
		cached_head = self.git("rev-parse", "HEAD").stdout.strip()
		second = self.make_patch("0002.patch", {"second.txt": "after\n"})
		self.git("reset", "--hard", cached_head)
		cached_source = self.root / "cached_source"
		self.git("-c", "core.autocrlf=false", "clone", "--depth=1", self.source.as_uri(), str(cached_source))
		self.source = cached_source
		self.git("config", "user.name", "Patch tests")
		self.git("config", "user.email", "patch-tests@example.invalid")
		self.git("config", "core.autocrlf", "false")
		result = self.run_patcher(first, second)
		self.assertEqual(result.returncode, 0, result.stderr)
		self.assertIn("Already applied: 0001.patch", result.stdout)
		self.assertEqual((self.source / "second.txt").read_text(), "after\n")

	def test_conflict_aborts_without_discarding_previous_patch(self):
		first = self.make_patch("0001.patch", {"first.txt": "after\n"})
		second = self.make_patch("0002.patch", {"second.txt": "after\n"})
		self.git("reset", "--hard", self.base)
		(self.source / "second.txt").write_text("conflicting upstream change\n", newline="\n")
		self.git("commit", "-am", "upstream change")
		result = self.run_patcher(first, second)
		self.assertNotEqual(result.returncode, 0)
		self.assertFalse((self.source / ".git/rebase-apply").exists())
		self.assertEqual(self.git("status", "--porcelain").stdout, "")
		self.assertEqual((self.source / "first.txt").read_text(), "after\n")
		self.assertEqual((self.source / "second.txt").read_text(), "conflicting upstream change\n")

	def test_partially_present_patch_is_not_skipped(self):
		patch_path = self.make_patch("0001.patch", {"first.txt": "after\n", "second.txt": "after\n"})
		self.git("reset", "--hard", self.base)
		(self.source / "first.txt").write_text("after\n", newline="\n")
		(self.source / "second.txt").write_text("conflicting upstream change\n", newline="\n")
		self.git("commit", "-am", "partial upstream change")
		result = self.run_patcher(patch_path)
		self.assertNotEqual(result.returncode, 0)
		self.assertNotIn("Already applied:", result.stdout)
		self.assertEqual((self.source / "second.txt").read_text(), "conflicting upstream change\n")

	def test_three_way_merge_keeps_unrelated_upstream_changes(self):
		(self.source / "first.txt").write_text("one\ntwo\nthree\nfour\nfive\nsix\nseven\neight\n", newline="\n")
		self.git("commit", "-am", "context")
		base = self.git("rev-parse", "HEAD").stdout.strip()
		patch_path = self.make_patch("0001.patch", {"first.txt": "ONE\ntwo\nthree\nfour\nfive\nsix\nseven\neight\n"})
		self.git("reset", "--hard", base)
		(self.source / "first.txt").write_text("one\ntwo\nthree\nFOUR\nfive\nsix\nseven\neight\n", newline="\n")
		self.git("commit", "-am", "upstream context change")
		result = self.run_patcher(patch_path)
		self.assertEqual(result.returncode, 0, result.stderr)
		self.assertEqual((self.source / "first.txt").read_text(), "ONE\ntwo\nthree\nFOUR\nfive\nsix\nseven\neight\n")

	def test_installer_updates_recipes_and_can_run_twice(self):
		packages = self.source / "packages"
		packages.mkdir()
		for name in ("curl", "openssl", "fontconfig"):
			(packages / f"{name}.cmake").write_text(
				f"    PATCH_COMMAND ${{EXEC}} git am --3way ${{CMAKE_CURRENT_SOURCE_DIR}}/{name}-*.patch\n"
			)
		custom_command = "    PATCH_COMMAND ${EXEC} python custom_mpv_patch.py\n"
		(packages / "mpv.cmake").write_text(custom_command)
		for _ in range(2):
			subprocess.run([sys.executable, str(installer)], cwd=self.source, check=True, capture_output=True)
		for name in ("curl", "openssl", "fontconfig"):
			self.assertIn("apply_dependency_patches.py", (packages / f"{name}.cmake").read_text())
		self.assertEqual((packages / "mpv.cmake").read_text(), custom_command)
		self.assertEqual((packages / patcher.name).read_bytes(), patcher.read_bytes())


if __name__ == "__main__":
	unittest.main()
