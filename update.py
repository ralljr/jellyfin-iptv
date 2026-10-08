"""Rebuild the curated lineup from iptv-org public metadata."""
import json
import re
from pathlib import Path
from urllib.request import urlopen
from collections import Counter

ROOT = Path(__file__).resolve().parent
def fetch(url):
    with urlopen(url, timeout=60) as response:
        return response.read().decode('utf-8-sig')

def main():
    playlist = fetch('https://iptv-org.github.io/iptv/countries/us.m3u')
    feeds = json.loads(fetch('https://iptv-org.github.io/api/feeds.json'))
    cities = json.loads(fetch('https://iptv-org.github.io/api/cities.json'))
    lookup = {f['channel'] + '@' + f['id']: f for f in feeds}
    local_areas = {'ct/' + c['code'] for c in cities if c.get('subdivision') == 'US-IA' or (c['country'] == 'US' and c['name'] == 'Kansas City')}
    local_areas.add('s/US-IA')
    # Non-English anime needs manually verified English subtitle evidence.
    subtitle_exceptions = set()
    major_affiliates = {'ABC.us', 'CBS.us', 'NBC.us', 'Fox.us', 'TheCW.us', 'TheCWPlus.us', 'PBS.us', 'MyNetworkTV.us'}
    blocks = re.split(r'(?=^#EXTINF:)', playlist, flags=re.M)[1:]
    kept, removed, stats, local, anime = [], [], Counter(), [], []
    for block in blocks:
        header = block.splitlines()[0]
        match = re.search(r'tvg-id="([^"]+)"', header)
        key = match.group(1) if match else ''
        name = header.rsplit(',', 1)[-1]
        feed = lookup.get(key)
        reason = None
        if not feed:
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
            kept.append(block.strip() + '\n')
            if re.search(r'\banime\b|HIDIVE|Crunchyroll', name, re.I):
                anime.append(name)
    assert kept, 'Refusing to publish an empty playlist'
    assert not any('3ABNFrench.us' in b for b in kept)
    (ROOT / 'us-curated.m3u').write_text('#EXTM3U\n' + ''.join(kept), encoding='utf-8')
    report = {'source_entries': len(blocks), 'kept_entries': len(kept), 'removed_by_reason': dict(stats), 'local_channels': local, 'anime_channels': anime, 'removed': removed}
    (ROOT / 'filter-report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k != 'removed'}, indent=2))

if __name__ == '__main__':
    main()
