#!/usr/bin/env bash
set -euo pipefail
export PATH="/home/fuck_ms/.local/share/mise/installs/gh/2.102.0/gh_2.102.0_linux_amd64/bin:/usr/local/bin:/usr/bin:/bin"
cd -- "$(dirname -- "$0")"
exec 9> /tmp/jellyfin-iptv-refresh.lock
flock -n 9 || exit 0
echo "$(date -Is) Starting IPTV guide refresh"
git pull --ff-only
python3 update.py
git add us-curated.m3u filter-report.json guide.xml guide-report.json
if ! git diff --cached --quiet; then
    git commit -m 'Refresh curated IPTV and guide'
    git push
fi
echo "$(date -Is) IPTV guide refresh complete"
