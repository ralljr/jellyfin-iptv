# Live program guide

Jellyfin XMLTV URL: https://raw.githubusercontent.com/ralljr/jellyfin-iptv/main/guide.xml

The hourly updater downloads Matt Huisman's public US Pluto XMLTV schedules,
keeps only channels present in our curated lineup, and rewrites channel IDs to
match the playlist's existing tvg-id values. No channel playback is required.

Source: https://github.com/matthuisman/i.mjh.nz/tree/master/PlutoTV

guide-report.json records coverage and the last scheduled programme time.
Channels outside this source (including local affiliates) receive placeholders
rather than real programme listings. Short or stale guide downloads fail the
update before publishing, preserving the previous published files.

Every curated channel receives clearly labeled "Live programming" placeholders
in hourly blocks wherever real schedules are absent, covering the next 48 hours.
These blocks never overlap real programmes and make no claims about show titles.

The WSL user crontab runs run-refresh.sh at minute 23 of every hour. Cron is
enabled under systemd. WSL and the Windows computer must remain running and
online for scheduled updates. GitHub Actions remains available for manual runs
but no longer has a recurring schedule. Jellyfin reloads the guide hourly.

Toonami Aftermath East and West use real show and episode listings from
https://api.toonamiaftermath.com, covering up to three days. West is delayed
three hours, following the iptv-org schedule configuration. Schedule gaps
still receive placeholders. An incomplete Toonami download preserves the
previous published guide. No images, media files, or server paths are copied.
