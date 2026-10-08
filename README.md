# Curated US IPTV for Jellyfin

Personal selection from [iptv-org](https://github.com/iptv-org/iptv), retaining feeds whose metadata includes English, with local stations restricted to Iowa and Kansas City. Major broadcast affiliates with unspecified locations are excluded. Other English-language national channels remain included.

Use `us-curated.m3u` as the Jellyfin M3U tuner source via its raw GitHub URL.

## Current lineup

864 stream entries from 1,457 source entries. Local streams currently available in the source: CBS KCCI, NBC KSHB-TV, and Ace TV KCKS-LD. The source does not currently provide a complete set of Iowa/Kansas City affiliates.

Anime x HIDIVE, Crunchyroll, Pluto TV Anime, and Pluto TV Anime Movies are retained because their feed metadata includes English. Playback, program audio, and subtitle availability have not been verified. Non-English anime is included only when English subtitles have been manually verified; there are currently no such exceptions.

## Update

Run `python3 update.py`, review `filter-report.json` and the playlist diff, then commit and push. This downloads the current US playlist plus iptv-org feed and city metadata. Updates are manual; this repository does not promise continuous synchronization or stream availability.

The playlist contains public stream references, not hosted media. Source data comes from iptv-org; the upstream playlist license is included in LICENSE. The report records every excluded entry and its reason.
