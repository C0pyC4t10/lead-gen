#!/usr/bin/env python3
import csv
from datetime import date, timedelta

yesterday = (date.today() - timedelta(1)).isoformat()

with open('/home/skarbolt/kb/lead-gen/collected_leads/leads.csv', newline='') as f:
    reader = csv.reader(f)
    header = next(reader)
    rows = [r for r in reader if r and len(r) > 3 and r[0].strip() == yesterday]

print(f'Yesterday ({yesterday}) leads: {len(rows)}')
if not rows:
    exit()

plat = {}; cat = {}; scores = {}; hot = 0
for r in rows:
    p = r[1].strip() if len(r) > 1 else ''
    c = r[4].strip() if len(r) > 4 else ''
    s = r[12].strip() if len(r) > 12 else ''
    w = r[9].strip() if len(r) > 9 else ''
    plat[p] = plat.get(p, 0) + 1
    cat[c] = cat.get(c, 0) + 1
    scores[s] = scores.get(s, 0) + 1
    if w == 'false': hot += 1

print(f'Platforms: {dict(plat)}')
print(f'Categories: {dict(cat)}')
print(f'Scores: {dict(scores)}')
print(f'Hot (no website): {hot}')
