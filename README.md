# Lifting

A planner, logbook and plate calculator for Jim Wendler's 5/3/1 with Boring But Big supplemental work.
It's an installable web app (PWA) and works offline once loaded.

## Install on your phone
Open https://smithpg.github.io/lifting-tracker-pwa/ and then:
- **iPhone (Safari):** Share → Add to Home Screen
- **Android (Chrome):** ⋮ menu → Install app

## Layout
- `index.html`, `sw.js`, `manifest.webmanifest`, `icons/` are the built app that Pages serves.
- `source/index.html` is the source page.
- `source/build_pwa.py` builds the app files from the source.

## Rebuild after editing the source
```sh
pip install pillow
python3 source/build_pwa.py source/index.html /tmp/out
rsync -a --exclude README.md /tmp/out/lifting/ ./
```
Each build stamps a new version into `sw.js`, so installed copies update the next time they open online.

## Data
Everything is stored on the device (localStorage) behind a small storage interface
(`KVBackend` in the source) that can be swapped for SQLite. To move data between devices, use Setup → Copy backup, then Setup → Restore on the other device.
