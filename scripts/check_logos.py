import os
import re

m3u = open('playlists/default_channels.m3u', encoding='utf-8').read()
logos = re.findall(r'tvg-logo="/static/logos/([^"]+)"', m3u)
missing = [l for l in set(logos) if not os.path.exists('static/logos/' + l)]
print("Total unique logos referenced:", len(set(logos)))
print("Missing logos:", missing)
