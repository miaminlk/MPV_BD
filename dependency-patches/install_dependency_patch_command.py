"""Install cache-aware patch commands in the checked-out build recipes."""

from pathlib import Path
import shutil


script_dir = Path(__file__).resolve().parent
packages_dir = Path.cwd() / "packages"
source_patcher = script_dir / "apply_dependency_patches.py"
old_command = "PATCH_COMMAND ${EXEC} git am --3way "
new_command = "PATCH_COMMAND ${EXEC} python ${CMAKE_CURRENT_SOURCE_DIR}/apply_dependency_patches.py "

for cmake_path in packages_dir.glob("*.cmake"):
	text = cmake_path.read_text(encoding="utf-8")
	if old_command in text:
		cmake_path.write_text(text.replace(old_command, new_command), encoding="utf-8", newline="\n")
		print(f"Installed cache-aware patch command: {cmake_path.name}")
shutil.copyfile(source_patcher, packages_dir / source_patcher.name)
