from pathlib import Path
import re
import shutil


script_dir = Path(__file__).resolve().parent
project_dir = script_dir.parent
toolchain_packages = project_dir / "mpv-winbuild-cmake" / "packages"
mpv_cmake_path = toolchain_packages / "mpv.cmake"
source_patcher = script_dir / "apply_external_audio_seek_patch.py"
installed_patcher = toolchain_packages / source_patcher.name

if not mpv_cmake_path.is_file():
	raise RuntimeError(f"Missing checked-out toolchain file: {mpv_cmake_path}")
if not source_patcher.is_file():
	raise RuntimeError(f"Missing semantic mpv patcher: {source_patcher}")

text = mpv_cmake_path.read_text(encoding="utf-8")
mpv_block_match = re.search(r"(?ms)^ExternalProject_Add\(mpv\s*\n.*?^\)\s*$", text)
if not mpv_block_match:
	raise RuntimeError("Could not locate the ExternalProject_Add(mpv) block.")

mpv_block = mpv_block_match.group(0)
patch_command = "    PATCH_COMMAND ${EXEC} python ${CMAKE_CURRENT_SOURCE_DIR}/apply_external_audio_seek_patch.py"
old_patch_command = "PATCH_COMMAND ${EXEC} git am --3way ${CMAKE_CURRENT_SOURCE_DIR}/mpv-*.patch"
patch_lines = list(re.finditer(r"(?m)^\s*PATCH_COMMAND[^\n]*$", mpv_block))
if len(patch_lines) > 1:
	raise RuntimeError(f"Expected at most one mpv PATCH_COMMAND, found {len(patch_lines)}.")
if patch_lines:
	existing_patch_command = patch_lines[0].group(0).strip()
	if existing_patch_command not in (patch_command.strip(), old_patch_command):
		raise RuntimeError(
			"Upstream mpv already defines an unknown PATCH_COMMAND; refusing to overwrite it."
		)
	mpv_block = re.sub(r"(?m)^\s*PATCH_COMMAND[^\n]*$", patch_command, mpv_block, count=1)
else:
	update_lines = list(re.finditer(r'(?m)^\s*UPDATE_COMMAND\s+""\s*$', mpv_block))
	if len(update_lines) != 1:
		raise RuntimeError(f"Expected exactly one mpv UPDATE_COMMAND, found {len(update_lines)}.")
	insert_at = update_lines[0].end()
	mpv_block = mpv_block[:insert_at] + "\n" + patch_command + mpv_block[insert_at:]

text = text[:mpv_block_match.start()] + mpv_block + text[mpv_block_match.end():]
mpv_cmake_path.write_text(text, encoding="utf-8", newline="\n")
shutil.copyfile(source_patcher, installed_patcher)

if mpv_cmake_path.read_text(encoding="utf-8").count(patch_command) != 1:
	raise RuntimeError("The semantic mpv PATCH_COMMAND was not installed exactly once.")
if installed_patcher.read_bytes() != source_patcher.read_bytes():
	raise RuntimeError("The installed semantic mpv patcher differs from its source.")

print(f"Installed semantic mpv patch command in {mpv_cmake_path}.")
