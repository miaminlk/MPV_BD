"""Check mirror configuration across upstream archive updates."""

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


patcher = Path(__file__).resolve().parents[1] / "dependency-patches/add_libiconv_mirrors.py"


class libiconv_mirror_tests(unittest.TestCase):
	def test_upstream_version_hash_and_build_options_survive_repeated_setup(self):
		for version in ("1.18", "1.19.1"):
			with self.subTest(version=version), tempfile.TemporaryDirectory() as temporary:
				root = Path(temporary)
				recipe_path = root / "packages/libiconv.cmake"
				recipe_path.parent.mkdir()
				archive_name = f"libiconv-{version}.tar.gz"
				recipe = (
					f'set(VERSION "{version}")\n'
					"ExternalProject_Add(libiconv\n"
					f"    URL https://ftp.gnu.org/pub/gnu/libiconv/{archive_name}\n"
					"    URL_HASH SHA256=upstream_checksum\n"
					"    DOWNLOAD_DIR ${SOURCE_LOCATION}\n"
					"    CONFIGURE_COMMAND ${EXEC} CONF=1 <SOURCE_DIR>/configure --disable-shared\n"
					")\n"
				)
				recipe_path.write_text(recipe, encoding="utf-8", newline="\n")
				subprocess.run([sys.executable, str(patcher)], cwd=root, check=True, capture_output=True)
				configured = recipe_path.read_text(encoding="utf-8")
				self.assertIn(f"https://mirrors.kernel.org/gnu/libiconv/{archive_name}", configured)
				self.assertIn(f"https://mirrors.ocf.berkeley.edu/gnu/libiconv/{archive_name}", configured)
				self.assertEqual(configured.count(f"https://ftp.gnu.org/pub/gnu/libiconv/{archive_name}"), 1)
				self.assertIn(f'set(VERSION "{version}")', configured)
				self.assertIn("URL_HASH SHA256=upstream_checksum", configured)
				self.assertIn("CONFIGURE_COMMAND ${EXEC} CONF=1 <SOURCE_DIR>/configure --disable-shared", configured)
				self.assertIn("TIMEOUT 120", configured)
				self.assertIn("INACTIVITY_TIMEOUT 30", configured)
				subprocess.run([sys.executable, str(patcher)], cwd=root, check=True, capture_output=True)
				self.assertEqual(recipe_path.read_text(encoding="utf-8"), configured)


if __name__ == "__main__":
	unittest.main()
