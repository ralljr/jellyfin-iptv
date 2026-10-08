"""Rebuild the curated lineup from iptv-org public metadata."""
import json
import re
from pathlib import Path
from urllib.request import urlopen
from collections import Counter
import base64
import time
import copy
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

def build_guide(kept, mappings):
    source = ET.fromstring(fetch('https://raw.githubusercontent.com/matthuisman/i.mjh.nz/master/PlutoTV/us.xml'))
    output = ET.Element('tv', {'generator-info-name': 'jellyfin-iptv curated from matthuisman/i.mjh.nz'})
    available = {c.get('id'): c for c in source.findall('channel')}
    matched = {key: ids for key, ids in mappings.items() if key in available}
    for key, ids in matched.items():
        for channel_id in sorted(ids):
            channel = copy.deepcopy(available[key])
            channel.set('id', channel_id)
            output.append(channel)
    programmes = 0
    future = 0
    latest = datetime.now(timezone.utc)
    for programme in source.findall('programme'):
        ids = matched.get(programme.get('channel'), ())
        if not ids:
            continue
        stop = datetime.strptime(programme.get('stop'), '%Y%m%d%H%M%S %z')
        if stop <= datetime.now(timezone.utc):
            continue
        latest = max(latest, stop)
        future += 1
        for channel_id in sorted(ids):
            item = copy.deepcopy(programme)
            item.set('channel', channel_id)
            output.append(item)
            programmes += 1
    if len(matched) < 50 or future < 100 or (latest - datetime.now(timezone.utc)).total_seconds() < 3600:
        raise ValueError('Guide incomplete or stale; preserving published files')
    ET.indent(output)
    xml = ET.tostring(output, encoding='utf-8', xml_declaration=True)
    return xml, {'matched_playlist_ids': sum(map(len, matched.values())), 'programmes': programmes, 'schedule_through_utc': latest.isoformat(), 'source': 'https://raw.githubusercontent.com/matthuisman/i.mjh.nz/master/PlutoTV/us.xml'}

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
    guide_mappings = {}
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
                guide_mappings.setdefault(old_url.group(1), set()).add(key)
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
    guide, guide_report = build_guide(kept, guide_mappings)
    (ROOT / 'guide.xml').write_bytes(guide)
    (ROOT / 'guide-report.json').write_text(json.dumps(guide_report, indent=2) + '\n', encoding='utf-8')
    (ROOT / 'us-curated.m3u').write_text('#EXTM3U\n' + ''.join(kept), encoding='utf-8')
    report = {'source_entries': len(blocks), 'kept_entries': len(kept), 'refreshed_pluto_entries': refreshed_pluto, 'unmatched_pluto_channels': unmatched_pluto, 'removed_by_reason': dict(stats), 'local_channels': local, 'anime_channels': anime, 'removed': removed}
    (ROOT / 'filter-report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k != 'removed'}, indent=2))

if __name__ == '__main__':
    main()
