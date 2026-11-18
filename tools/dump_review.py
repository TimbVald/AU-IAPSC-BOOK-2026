import json
import glob

for f in sorted(glob.glob('data/raw/2026-*.json')):
    d = json.load(open(f, encoding='utf-8'))
    print('=' * 10, d['month_title'], '=' * 10)
    for i, a in enumerate(d['activities'], 1):
        act = a['activity'][:100].replace('\n', ' ')
        ven = a['venue'][:45]
        print(f"{i:2d}. [{a['date'][:40]}] {ven:45s} | {act}")
    if d.get('trailing_notes'):
        print('  NOTES:', ' /// '.join(d['trailing_notes'])[:300])
    print()
