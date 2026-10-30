"""Apply an ordered patch series, including when sources come from a build cache."""

from glob import glob
from pathlib import Path
import subprocess
import sys


patch_paths = []
for pattern in sys.argv[1:]:
	matches = sorted(glob(pattern))
	if not matches:
		raise FileNotFoundError(f"No patches matched: {pattern}")
	patch_paths.extend(Path(match).resolve() for match in matches)
if not patch_paths:
	raise RuntimeError("Pass patch files or a patch glob.")

for patch_path in patch_paths:
	# Context whitespace may differ after Git normalizes a cached checkout.
	already_applied = subprocess.run(
		["git", "apply", "--reverse", "--check", "--ignore-space-change", str(patch_path)],
		capture_output=True,
	).returncode == 0
	if already_applied:
		print(f"Already applied: {patch_path.name}", flush=True)
		continue
	print(f"Applying: {patch_path.name}", flush=True)
	result = subprocess.run(["git", "am", "--3way", str(patch_path)])
	if result.returncode:
		# Leave the checkout usable for the next run; never hide a real conflict.
		subprocess.run(["git", "am", "--abort"], check=True)
		sys.exit(result.returncode)
