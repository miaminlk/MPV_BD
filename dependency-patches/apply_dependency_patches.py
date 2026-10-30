"""Apply an ordered patch series, including when sources come from a build cache."""

from glob import glob
from pathlib import Path
import argparse
import subprocess
import sys


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--replay", action="store_true", help="Reset build-owned dependency commits to their upstream base before replay.")
parser.add_argument("patch_patterns", nargs="+")
args = parser.parse_args()
patch_paths = []
for pattern in args.patch_patterns:
	matches = sorted(glob(pattern))
	if not matches:
		raise FileNotFoundError(f"No patches matched: {pattern}")
	patch_paths.extend(Path(match).resolve() for match in matches)
# These are build-owned checkouts. Cached patch commits must be replayed from
# their upstream base: later upstream edits can invalidate a reverse hunk check.
if args.replay:
	upstream = subprocess.run(["git", "rev-parse", "--verify", "@{upstream}"], capture_output=True, text=True)
	if upstream.returncode == 0:
		base = subprocess.run(
			["git", "merge-base", "HEAD", upstream.stdout.strip()],
			check=True, capture_output=True, text=True,
		).stdout.strip()
		subprocess.run(["git", "reset", "--hard", base], check=True)

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
	command = ["git", "am", "--3way", str(patch_path)]
	result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
	print(result.stdout, end="", flush=True)
	if result.returncode and "could not build fake ancestor" in result.stdout:
		# Abbreviated blob IDs cannot be fetched lazily from a partial clone.
		# Fetch history only when Git actually needs a missing patch preimage.
		subprocess.run(["git", "am", "--abort"], check=True)
		shallow = subprocess.run(
			["git", "rev-parse", "--is-shallow-repository"],
			check=True, capture_output=True, text=True,
		).stdout.strip() == "true"
		print("Fetching missing patch history for the three-way merge.", flush=True)
		subprocess.run(
			["git", "fetch", "--unshallow" if shallow else "--refetch", "--no-filter", "origin"],
			check=True,
		)
		result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
		print(result.stdout, end="", flush=True)
	if result.returncode:
		# Leave the checkout usable for the next run; never hide a real conflict.
		subprocess.run(["git", "am", "--abort"], check=True)
		sys.exit(result.returncode)
