# Curated US IPTV for Jellyfin

Personal selection from [iptv-org](https://github.com/iptv-org/iptv), retaining feeds whose metadata includes English, with local stations restricted to Iowa and Kansas City. Religious channels are excluded, including mixed religious/kids/movie categories. Cartoons, sci-fi, decade channels, and movies remain included. Major broadcast affiliates with unspecified locations are excluded. Other English-language national channels remain included.

Use `us-curated.m3u` as the Jellyfin M3U tuner source via its raw GitHub URL.

RetroStrange is a personal addition using its public Owncast HLS stream. The updater preserves it on every run and generates hourly placeholder guide entries; these do not identify the actual show airing.

## Current lineup

802 stream entries from 1,457 source entries. Local streams currently available in the source: CBS KCCI, NBC KSHB-TV, and Ace TV KCKS-LD. The source does not currently provide a complete set of Iowa/Kansas City affiliates.

Anime x HIDIVE, Crunchyroll, Pluto TV Anime, and Pluto TV Anime Movies are retained because their feed metadata includes English. Playback, program audio, and subtitle availability have not been verified. Non-English anime is included only when English subtitles have been manually verified; there are currently no such exceptions.

## Update

Run `python3 update.py`, review `filter-report.json` and the playlist diff, then commit and push. This downloads the current US playlist plus iptv-org feed and city metadata. GitHub Actions checks hourly at minute 23 and commits changed output. It also supports a manual run from the Actions page. GitHub may delay scheduled jobs and may disable schedules after prolonged repository inactivity. The updater retains the last published version on source errors, incomplete data, or Pluto tokens with less than two hours remaining. Stream availability is not guaranteed.

The playlist contains public stream references, not hosted media. Source data comes from iptv-org; the upstream playlist license is included in LICENSE. The report records every excluded entry and its reason.

## Pluto playback check (2026-10-08)

00s Replay, 80s Rewind, and Pluto TV Anime returned HTTP 403 with channel not permitted for partner through the current jmp2.uk links. 00s Replay also failed in Jellyfin. These channels are retained pending a working source; changing Jellyfin tuner settings cannot fix that upstream refusal. This does not establish that every Pluto channel is unavailable.


## Refreshed Pluto sources

Matching Pluto channel IDs are refreshed from OwnerPlugins/pluto-tv-m3u public US playlist. No personal login, cookies, or account credentials are used. Original channel IDs, names and filtering are preserved. Unmatched Pluto entries retain their existing source and are listed in filter-report.json. Jellyfin must refresh its guide/channel data regularly to ingest refreshed URLs.

