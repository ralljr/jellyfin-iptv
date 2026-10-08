"""Rebuild the curated lineup from iptv-org public metadata."""
import json
import re
from pathlib import Path
from urllib.request import urlopen
from collections import Counter
import base64
import time

ROOT = Path(__file__).resolve().parent
def fetch(url):
    with urlopen(url, timeout=60) as response:
        return response.read().decode('utf-8-sig')

def main():
    playlist = fetch('https://iptv-org.github.io/iptv/countries/us.m3u')
    feeds = json.loads(fetch('https://iptv-org.github.io/api/feeds.json'))
    cities = json.loads(fetch('https://iptv-org.github.io/api/cities.json'))
    pluto = fetch('https://raw.githubusercontent.com/OwnerPlugins/pluto-tv-m3u/main/pluto-live-US.m3u')
    pluto_urls = {}
    for block in re.split(r'(?=^#EXTINF:)', pluto, flags=re.M)[1:]:
        match = re.search(r'tvg-id="([a-f0-9]{24})"', block.splitlines()[0])
        urls = [line for line in block.splitlines() if line.startswith('https://')]
        if match and len(urls) == 1:
            token = re.search(r'[?&]jwt=([^&]+)', urls[0])
            if not token:
                raise ValueError('Pluto source lacks expected playback token')
            payload = token.group(1).split('.')[1]
            claims = json.loads(base64.urlsafe_b64decode(payload + '=' * (-len(payload) % 4)))
            if claims.get('exp', 0) < time.time() + 7200:
                raise ValueError('Pluto source token expired or expires within two hours; preserving published list')
            pluto_urls[match.group(1)] = urls[0]
    if len(pluto_urls) < 100:
        raise ValueError('Incomplete Pluto source; preserving published list')
    lookup = {f['channel'] + '@' + f['id']: f for f in feeds}
    local_areas = {'ct/' + c['code'] for c in cities if c.get('subdivision') == 'US-IA' or (c['country'] == 'US' and c['name'] == 'Kansas City')}
    local_areas.add('s/US-IA')
    # Non-English anime needs manually verified English subtitle evidence.
    subtitle_exceptions = set()
    major_affiliates = {'ABC.us', 'CBS.us', 'NBC.us', 'Fox.us', 'TheCW.us', 'TheCWPlus.us', 'PBS.us', 'MyNetworkTV.us'}
    blocks = re.split(r'(?=^#EXTINF:)', playlist, flags=re.M)[1:]
    kept, removed, stats, local, anime = [], [], Counter(), [], []
    refreshed_pluto, unmatched_pluto = 0, []
    for block in blocks:
        header = block.splitlines()[0]
        match = re.search(r'tvg-id="([^"]+)"', header)
        key = match.group(1) if match else ''
        name = header.rsplit(',', 1)[-1]
        feed = lookup.get(key)
        groups = re.search(r'group-title="([^"]*)"', header)
        religious = groups and 'religious' in groups.group(1).lower().split(';')
        reason = None
        if religious:
            reason = 'religious channel'
        elif not feed:
            reason = 'unknown language/location metadata'
        elif 'eng' not in feed.get('languages', []) and key not in subtitle_exceptions:
            reason = 'non-English; English subtitles unverified'
        else:
            areas = set(feed.get('broadcast_area', []))
            regional = any(a.startswith(('ct/', 's/')) for a in areas)
            affiliate = feed['channel'] in major_affiliates
            allowed = bool(areas & local_areas)
            if regional and not allowed:
                reason = 'local station outside Iowa/Kansas City'
            elif affiliate and not allowed:
                reason = 'affiliate location outside selection or unspecified'
            elif allowed:
                local.append(name)
        if reason:
            stats[reason] += 1
            removed.append({'id': key, 'name': name, 'reason': reason})
        else:
            old_url = re.search(r'https://jmp2\.uk/plu-([a-f0-9]{24})\.m3u8', block)
            if old_url:
                replacement = pluto_urls.get(old_url.group(1))
                if replacement:
                    block = block.replace(old_url.group(0), replacement)
                    refreshed_pluto += 1
                else:
                    unmatched_pluto.append(name)
            kept.append(block.strip() + '\n')
            if re.search(r'\banime\b|HIDIVE|Crunchyroll', name, re.I):
                anime.append(name)
    assert kept, 'Refusing to publish an empty playlist'
    assert not any('3ABNFrench.us' in b for b in kept)
    assert not any(re.search(r'group-title="[^"]*Religious', b, re.I) for b in kept)
    assert len(kept) >= 400, 'Refusing unexpectedly small lineup'
    (ROOT / 'us-curated.m3u').write_text('#EXTM3U\n' + ''.join(kept), encoding='utf-8')
    report = {'source_entries': len(blocks), 'kept_entries': len(kept), 'refreshed_pluto_entries': refreshed_pluto, 'unmatched_pluto_channels': unmatched_pluto, 'removed_by_reason': dict(stats), 'local_channels': local, 'anime_channels': anime, 'removed': removed}
    (ROOT / 'filter-report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k != 'removed'}, indent=2))

if __name__ == '__main__':
    main()
