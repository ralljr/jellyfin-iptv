# Live program guide

Jellyfin XMLTV URL: https://raw.githubusercontent.com/ralljr/jellyfin-iptv/main/guide.xml

The hourly updater downloads Matt Huisman's public US Pluto XMLTV schedules,
keeps only channels present in our curated lineup, and rewrites channel IDs to
match the playlist's existing tvg-id values. No channel playback is required.

Source: https://github.com/matthuisman/i.mjh.nz/tree/master/PlutoTV

guide-report.json records coverage and the last scheduled programme time.
Channels outside this source (including local affiliates) remain in the playlist
but do not yet have programme listings. Short or stale guide downloads fail the
update before publishing, preserving the previous published files.
