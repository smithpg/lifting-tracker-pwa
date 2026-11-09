"""Build an installable PWA folder + zip from the artifact's index.html."""
import hashlib, json, os, shutil, sys, zipfile
from PIL import Image, ImageDraw, ImageFont

src, out_root = sys.argv[1], sys.argv[2]
app = os.path.join(out_root, "lifting")
shutil.rmtree(app, ignore_errors=True)
os.makedirs(os.path.join(app, "icons"))

html = open(src, encoding="utf-8").read()
version = hashlib.sha256(html.encode()).hexdigest()[:10]

head = """<link rel="manifest" href="manifest.webmanifest">
<meta name="theme-color" media="(prefers-color-scheme: light)" content="#e7eaed">
<meta name="theme-color" media="(prefers-color-scheme: dark)" content="#101214">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta name="apple-mobile-web-app-title" content="Lifting">
<link rel="apple-touch-icon" href="icons/apple-touch-icon.png">
<link rel="icon" type="image/png" href="icons/icon-192.png">"""
body = """<script>
if ("serviceWorker" in navigator) window.addEventListener("load", function(){ navigator.serviceWorker.register("sw.js").catch(function(){}); });
if (navigator.storage && navigator.storage.persist) navigator.storage.persist().catch(function(){});
</script>"""
assert "<!--PWA-HEAD-->" in html and "<!--PWA-BODY-->" in html
vp_old = '<meta name="viewport" content="width=device-width, initial-scale=1">'
assert vp_old in html
html = (html.replace("<!--PWA-HEAD-->", head).replace("<!--PWA-BODY-->", body)
            .replace(vp_old, '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">'))
open(os.path.join(app, "index.html"), "w", encoding="utf-8").write(html)

manifest = {
    "name": "Lifting", "short_name": "Lifting",
    "description": "5/3/1 Boring But Big planner, logbook and plate calculator.",
    "start_url": "./", "scope": "./", "display": "standalone", "orientation": "portrait",
    "background_color": "#101214", "theme_color": "#101214",
    "icons": [
        {"src": "icons/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any"},
        {"src": "icons/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any"},
        {"src": "icons/icon-maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
    ],
}
json.dump(manifest, open(os.path.join(app, "manifest.webmanifest"), "w"), indent=2)

sw = """// Service worker: works offline, picks up new versions when online.
const VERSION = "%s";
const CORE = "core-" + VERSION, RUNTIME = "runtime-" + VERSION;
const ASSETS = ["./", "./index.html", "./manifest.webmanifest", "./icons/icon-192.png", "./icons/icon-512.png", "./icons/apple-touch-icon.png"];
self.addEventListener("install", e => { e.waitUntil(caches.open(CORE).then(c => c.addAll(ASSETS)).then(() => self.skipWaiting())); });
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k !== CORE && k !== RUNTIME).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener("fetch", e => {
  const req = e.request; if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (req.mode === "navigate") {            // page: network first, cached copy offline
    e.respondWith(fetch(req).then(res => { const copy = res.clone(); caches.open(CORE).then(c => c.put("./index.html", copy)); return res; })
      .catch(() => caches.match("./index.html")));
    return;
  }
  if (url.origin === location.origin) {     // own files: cache first
    e.respondWith(caches.match(req).then(hit => hit || fetch(req)));
    return;
  }
  if (/fonts\\.(googleapis|gstatic)\\.com$/.test(url.hostname)) {   // fonts: stale-while-revalidate
    e.respondWith(caches.open(RUNTIME).then(c => c.match(req).then(hit => {
      const net = fetch(req).then(res => { c.put(req, res.clone()); return res; }).catch(() => hit);
      return hit || net;
    })));
  }
});
""" % version
open(os.path.join(app, "sw.js"), "w").write(sw)

# Icons: a red plate with 5/3/1 on the app's dark background, content inside the maskable safe zone.
font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf"
def icon(size, plate_r):
    im = Image.new("RGB", (size, size), "#101214")
    d = ImageDraw.Draw(im); c = size / 2; r = size * plate_r
    d.ellipse([c - r, c - r, c + r, c + r], fill="#c62828")
    d.ellipse([c - r * .86, c - r * .86, c + r * .86, c + r * .86], outline="#8e1c1c", width=max(2, size // 128))
    f = ImageFont.truetype(font_path, int(r * .62))
    d.text((c, c), "5/3/1", font=f, fill="#ffffff", anchor="mm")
    return im
icon(512, .40).save(os.path.join(app, "icons/icon-512.png"))
icon(192, .40).resize((192, 192)).save(os.path.join(app, "icons/icon-192.png"))
icon(512, .32).save(os.path.join(app, "icons/icon-maskable-512.png"))
icon(180, .40).save(os.path.join(app, "icons/apple-touch-icon.png"))

open(os.path.join(app, "README.md"), "w").write("""# Lifting (PWA)

A phone app needs to be served over HTTPS before it can be installed.
Opening index.html straight from your phone's files won't install it.

## Host it (pick one, all free)
- **Netlify Drop:** go to https://app.netlify.com/drop and drag this whole `lifting` folder onto the page.
- **GitHub Pages:** push this folder's contents to a repo, then Settings → Pages → deploy from the main branch.
- **Cloudflare Pages:** Workers & Pages → Create → Pages → Upload assets → pick this folder.

## Install on your phone
- **iPhone (Safari):** open the URL → Share → Add to Home Screen.
- **Android (Chrome):** open the URL → ⋮ menu → Install app (or Add to Home screen).

After the first load it works offline. When you're online it picks up new versions.

## Your data
Data is saved in the installed app's own storage. Each app or site has its own
storage, so nothing from the Claude artifact carries over: in the artifact go to
Setup → Copy backup, then in the installed app go to Setup → Restore and paste it.
Make a backup now and then. Uninstalling the app deletes its data.

## Updating
Replace index.html with a new build and redeploy. sw.js carries a version stamp,
so phones refresh their cache the next time they open the app online.
""")

zpath = os.path.join(out_root, "lifting-pwa.zip")
with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
    for root, _, files in os.walk(app):
        for fn in files:
            p = os.path.join(root, fn); z.write(p, os.path.relpath(p, out_root))
print("built", version, zpath)
