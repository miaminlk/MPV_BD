#!/bin/bash
# source: https://github.com/BtbN/FFmpeg-Builds/blob/master/util/prunetags.sh
# Copyright 2020-2021 BtbN <btbn@btbn.de>
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

set -euo pipefail

cutoff=$(date -u -d '48 hours ago' +%Y-%m-%dT%H:%M:%SZ)
# Enumerate all pages before deleting so pagination cannot skip releases.
release_ids=$(gh api --paginate 'repos/{owner}/{repo}/releases' \
	--jq ".[] | select(.draft == false and .published_at != null and .published_at < \"$cutoff\") | .id")

while IFS= read -r release_id; do
	[[ -n "$release_id" ]] || continue
	echo "Deleting release $release_id published before $cutoff"
	gh api --method DELETE "repos/{owner}/{repo}/releases/$release_id"
done <<< "$release_ids"
