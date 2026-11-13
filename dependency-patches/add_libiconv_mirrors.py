"""Add download mirrors using the archive selected by the upstream recipe."""

from pathlib import Path
import re


recipe_path = Path.cwd() / "packages/libiconv.cmake"
text = recipe_path.read_text(encoding="utf-8")
primary_prefix = "https://ftp.gnu.org/pub/gnu/libiconv/"
mirror_prefixes = (
	"https://mirrors.kernel.org/gnu/libiconv/",
	"https://mirrors.ocf.berkeley.edu/gnu/libiconv/",
)
match = re.search(r"(?m)^([ \t]*)URL[ \t]+(" + re.escape(primary_prefix) + r"[^\s]+)[ \t]*$", text)
if match:
	indent, primary_url = match.groups()
	archive_name = primary_url.removeprefix(primary_prefix)
	urls = [prefix + archive_name for prefix in mirror_prefixes] + [primary_url]
	replacement = indent + "URL\n" + "\n".join(indent + "    " + url for url in urls)
	replacement += "\n" + indent + "TIMEOUT 120\n" + indent + "INACTIVITY_TIMEOUT 30"
	text = text[:match.start()] + replacement + text[match.end():]
	recipe_path.write_text(text, encoding="utf-8", newline="\n")
	print(f"Added libiconv mirrors for {archive_name}.")
elif mirror_prefixes[0] not in text:
	raise RuntimeError("Could not locate the upstream libiconv archive URL.")
