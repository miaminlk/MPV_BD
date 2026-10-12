from pathlib import Path
import re
import subprocess


def find_function_span(text, function_name):
	pattern = re.compile(
		rf"(?m)^(?:static\s+)?(?:[A-Za-z_][A-Za-z0-9_]*[\s*]+)+{re.escape(function_name)}"
		r"\s*\([^;{}]*\)\s*\{"
	)
	matches = list(pattern.finditer(text))
	if len(matches) != 1:
		raise RuntimeError(
			f"Expected exactly one definition of {function_name}, found {len(matches)}."
		)
	opening_brace = text.find("{", matches[0].start(), matches[0].end())
	depth = 0
	index = opening_brace
	state = "code"
	while index < len(text):
		char = text[index]
		next_char = text[index + 1] if index + 1 < len(text) else ""
		if state == "code":
			if char == '"':
				state = "string"
			elif char == "'":
				state = "character"
			elif char == "/" and next_char == "/":
				state = "line_comment"
				index += 1
			elif char == "/" and next_char == "*":
				state = "block_comment"
				index += 1
			elif char == "{":
				depth += 1
			elif char == "}":
				depth -= 1
				if depth == 0:
					return matches[0].start(), index + 1, opening_brace
		elif state in ("string", "character"):
			if char == "\\":
				index += 1
			elif (state == "string" and char == '"') or (state == "character" and char == "'"):
				state = "code"
		elif state == "line_comment":
			if char == "\n":
				state = "code"
		elif state == "block_comment" and char == "*" and next_char == "/":
			state = "code"
			index += 1
		index += 1
	raise RuntimeError(f"Unbalanced braces while parsing {function_name}.")


def replace_once(text, pattern, replacement, description, flags=0):
	compiled = re.compile(pattern, flags)
	matches = list(compiled.finditer(text))
	if len(matches) != 1:
		raise RuntimeError(
			f"Expected exactly one {description}, found {len(matches)}. Upstream mpv changed semantically."
		)
	return compiled.sub(replacement, text, count=1)


def replace_in_function(text, function_name, pattern, replacement, description, flags=0):
	start, end, _ = find_function_span(text, function_name)
	function_text = text[start:end]
	function_text = replace_once(function_text, pattern, replacement, description, flags)
	return text[:start] + function_text + text[end:]


def insert_function_start(text, function_name, snippet):
	_, _, opening_brace = find_function_span(text, function_name)
	return text[:opening_brace + 1] + "\n" + snippet + text[opening_brace + 1:]


def write_changed(source_path, text):
	old_text = source_path.read_text(encoding="utf-8")
	if old_text == text:
		raise RuntimeError(f"{source_path} was expected to change but did not.")
	source_path.write_text(text, encoding="utf-8", newline="\n")


script_dir = Path(__file__).resolve().parent
source_dir = Path.cwd()
core_path = source_dir / "player" / "core.h"
loadfile_path = source_dir / "player" / "loadfile.c"
playloop_path = source_dir / "player" / "playloop.c"

for source_path in (core_path, loadfile_path, playloop_path):
	if not source_path.is_file():
		raise RuntimeError(f"Run this patcher from the root of an mpv source tree: missing {source_path}.")

initial_text = {
	core_path: core_path.read_text(encoding="utf-8"),
	loadfile_path: loadfile_path.read_text(encoding="utf-8"),
	playloop_path: playloop_path.read_text(encoding="utf-8"),
}
presence = {
	core_path: "struct track *delayed_audio_seek;" in initial_text[core_path],
	loadfile_path: "cancel_delayed_audio_seek(mpctx);" in initial_text[loadfile_path],
	playloop_path: "aligning external aid=" in initial_text[playloop_path],
}
if any(presence.values()):
	if not all(presence.values()):
		raise RuntimeError("The external-audio seek patch is only partially present.")
	if initial_text[core_path].count("struct track *delayed_audio_seek;") != 1:
		raise RuntimeError("The delayed external-audio state field is duplicated.")
	if initial_text[core_path].count("void cancel_delayed_audio_seek(") != 1:
		raise RuntimeError("The delayed external-audio cancellation declaration is duplicated.")
	if initial_text[loadfile_path].count("cancel_delayed_audio_seek(mpctx);") != 2:
		raise RuntimeError("The delayed external-audio cleanup hooks are incomplete or duplicated.")
	if initial_text[playloop_path].count("void cancel_delayed_audio_seek(") != 1:
		raise RuntimeError("The delayed external-audio cancellation function is duplicated.")
	if initial_text[playloop_path].count("delaying external audio seek for aid=") != 1:
		raise RuntimeError("The delayed external-audio seek hook is incomplete or duplicated.")
	if initial_text[playloop_path].count("aligning external aid=") != 1:
		raise RuntimeError("The delayed external-audio alignment hook is incomplete or duplicated.")
	print("External-audio seek patch is already applied and complete.")
	raise SystemExit(0)

for patch_path in sorted(script_dir.glob("mpv-*.patch")):
	try:
		subprocess.run(
			["git", "am", "--3way", str(patch_path)],
			cwd=source_dir,
			check=True,
		)
	except subprocess.CalledProcessError:
		subprocess.run(["git", "am", "--abort"], cwd=source_dir, check=False)
		raise

core_text = core_path.read_text(encoding="utf-8")
loadfile_text = loadfile_path.read_text(encoding="utf-8")
playloop_text = playloop_path.read_text(encoding="utf-8")

core_text = replace_once(
	core_text,
	r"(?m)^([ \t]*struct seek_params seek;)[ \t]*$",
	r"\1\n\n    // External audio waiting for the actual video position after a keyframe seek.\n    struct track *delayed_audio_seek;",
	"MPContext seek state field",
)
core_text = replace_once(
	core_text,
	r"(?m)^([ \t]*)void reset_playback_state\(struct MPContext \*mpctx\);$",
	r"\1void cancel_delayed_audio_seek(struct MPContext *mpctx);\n\1void reset_playback_state(struct MPContext *mpctx);",
	"reset_playback_state declaration",
)

loadfile_text = insert_function_start(
	loadfile_text,
	"uninit_demuxer",
	"    cancel_delayed_audio_seek(mpctx);\n",
)
loadfile_text = insert_function_start(
	loadfile_text,
	"reselect_demux_stream",
	"    if (mpctx->delayed_audio_seek &&\n"
	"        track->demuxer == mpctx->delayed_audio_seek->demuxer)\n"
	"        cancel_delayed_audio_seek(mpctx);\n",
)

reset_start, _, _ = find_function_span(playloop_text, "reset_playback_state")
reset_comment = "// Clear some playback-related fields on file loading or after seeks."
comment_start = playloop_text.rfind(reset_comment, max(0, reset_start - 256), reset_start)
if comment_start >= 0 and not playloop_text[comment_start + len(reset_comment):reset_start].strip():
	reset_start = comment_start
cancel_function = (
	"void cancel_delayed_audio_seek(struct MPContext *mpctx)\n"
	"{\n"
	"    struct track *track = mpctx->delayed_audio_seek;\n"
	"    if (!track)\n"
	"        return;\n\n"
	"    if (track->demuxer)\n"
	"        demux_block_reading(track->demuxer, false);\n"
	"    mpctx->delayed_audio_seek = NULL;\n"
	"}\n\n"
)
playloop_text = playloop_text[:reset_start] + cancel_function + playloop_text[reset_start:]
playloop_text = insert_function_start(
	playloop_text,
	"reset_playback_state",
	"    cancel_delayed_audio_seek(mpctx);\n",
)
playloop_text = replace_in_function(
	playloop_text,
	"mp_seek",
	r"(if[ \t]*\([ \t]*!mpctx->demuxer[ \t]*\|\|[ \t]*!seek\.type[ \t]*\|\|[ \t]*seek\.amount[ \t]*==[ \t]*MP_NOPTS_VALUE[ \t]*\)[ \t]*\n[ \t]*return[ \t]*;)",
	r"\1\n\n    cancel_delayed_audio_seek(mpctx);",
	"initial seek validity guard",
)
delay_setup = (
	"\n\n    struct track *video_track = mpctx->current_track[0][STREAM_VIDEO];\n"
	"    struct track *audio_track = mpctx->current_track[0][STREAM_AUDIO];\n"
	"    bool delay_external_audio = video_track && audio_track &&\n"
	"        video_track->selected && !video_track->is_external && video_track->stream &&\n"
	"        !video_track->image && !video_track->attached_picture &&\n"
	"        video_track->demuxer == mpctx->demuxer &&\n"
	"        audio_track->selected && audio_track->is_external && audio_track->demuxer &&\n"
	"        audio_track->demuxer != video_track->demuxer &&\n"
	"        !hr_seek && play_dir > 0 && !(demux_flags & SEEK_FORWARD);\n"
	"    struct track *delayed_audio_seek = delay_external_audio ? audio_track : NULL;"
)
playloop_text = replace_in_function(
	playloop_text,
	"mp_seek",
	r"(?m)^([ \t]*mpctx->play_dir[ \t]*=[ \t]*play_dir[ \t]*;)$",
	r"\1" + delay_setup,
	"play direction assignment",
)

playloop_text = replace_in_function(
	playloop_text,
	"mp_seek",
	r"(?m)^([ \t]*)demux_seek\(\s*track->demuxer\s*,\s*main_new_pos\s*,\s*demux_flags\s*&\s*\(\s*SEEK_SATAN\s*\|\s*SEEK_BLOCK\s*\)\s*\)\s*;",
	r"\1int seek_result = demux_seek(track->demuxer, main_new_pos,\n"
	r"\1                             demux_flags & (SEEK_SATAN | SEEK_BLOCK));\n"
	r"\1if (track == delayed_audio_seek && !seek_result)\n"
	r"\1    delayed_audio_seek = NULL;",
	"external-track demux_seek call",
)
delayed_assignment = (
	"\n\n    if (delayed_audio_seek) {\n"
	"        MP_VERBOSE(mpctx, \"delaying external audio seek for aid=%d until video position is known\\n\",\n"
	"                   delayed_audio_seek->user_tid);\n"
	"        mpctx->delayed_audio_seek = delayed_audio_seek;\n"
	"    }"
)
playloop_text = replace_in_function(
	playloop_text,
	"mp_seek",
	r"(?m)^([ \t]*reset_playback_state\(mpctx\);)$",
	lambda match: match.group(1) + delayed_assignment,
	"post-seek playback reset",
)

playloop_text = replace_in_function(
	playloop_text,
	"mp_seek",
	r"(?m)^([ \t]*)if\s*\(\s*track->selected\s*&&\s*track->demuxer\s*\)\s*\n([ \t]*)demux_block_reading\(track->demuxer\s*,\s*false\);",
	r"\1if (track->selected && track->demuxer &&\n"
	r"\1    (!delayed_audio_seek || track->demuxer != delayed_audio_seek->demuxer))\n"
	r"\2demux_block_reading(track->demuxer, false);",
	"selected-track demux unblock condition",
)
alignment_block = (
	"    if (mpctx->delayed_audio_seek) {\n"
	"        struct track *track = mpctx->delayed_audio_seek;\n"
	"        if (mpctx->video_pts != MP_NOPTS_VALUE) {\n"
	"            double pts = mpctx->video_pts + get_track_seek_offset(mpctx, track);\n"
	"            MP_VERBOSE(mpctx, \"aligning external aid=%d to video position %f\\n\",\n"
	"                       track->user_tid, pts);\n"
	"            if (!demux_seek(track->demuxer, pts, 0))\n"
	"                MP_WARN(mpctx, \"Failed to align external audio after seek.\\n\");\n"
	"            cancel_delayed_audio_seek(mpctx);\n"
	"        } else if (mpctx->video_status >= STATUS_EOF) {\n"
	"            cancel_delayed_audio_seek(mpctx);\n"
	"        }\n"
	"    }\n\n"
)
playloop_text = replace_in_function(
	playloop_text,
	"run_playloop",
	r"(?m)^([ \t]*handle_playback_restart\(mpctx\);)$",
	lambda match: alignment_block + match.group(1),
	"handle_playback_restart call",
)

write_changed(core_path, core_text)
write_changed(loadfile_path, loadfile_text)
write_changed(playloop_path, playloop_text)

subprocess.run(["git", "diff", "--check"], cwd=source_dir, check=True)
subprocess.run(["git", "diff", "--stat"], cwd=source_dir, check=True)
print("Applied semantic external-audio backward-seek alignment patch.")
