"""Baut die statische Tracker-Seite aus data/tracker.json nach docs/.

Aufruf:  python build.py
Danach docs/ committen und pushen, GitHub Pages liefert docs/ aus.
"""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data" / "tracker.json"
OUT = ROOT / "docs"

TITLE = "GTA 6 PC Crack Tracker: PC-Version, DRM und Crack-Status"
DESC = ("Gibt es GTA 6 für PC, hat es Denuvo, ist es gecrackt? Der Live-Tracker sammelt den "
        "aktuellen Stand zu PC-Version, Kopierschutz und Crack-Status mit Quellen.")
TAGS = ["Alle", "PC-Version", "DRM", "Szene", "Rockstar", "Gerücht"]
STATES = {"ok", "warn", "bad", "idle"}
ID_RE = re.compile(r"^[a-z0-9-]{1,80}$")


def e(s):
    return html.escape(str(s), quote=True)


def fmt(ts):
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})(?:T(\d{2}):(\d{2}))?", ts)
    if not m:
        return ts, ""
    day = f"{m[3]}.{m[2]}.{m[1]}"
    return day, (f"{m[4]}:{m[5]} Uhr" if m[4] else "")


def conf_class(c):
    k = c.lower()
    if k.startswith("best"):
        return "conf-best"
    if k.startswith("ber"):
        return "conf-ber"
    return "conf-ger"


def safe_url(u):
    return u if re.match(r"^https?://", u or "", re.I) else None


def validate(t):
    assert t["siteUrl"].startswith("https://") and t["siteUrl"].endswith("/"), "siteUrl fehlt oder endet nicht auf /"
    for k in ("pc", "date", "drm", "crack"):
        s = t["status"][k]
        assert s["state"] in STATES, f"status.{k}.state ungültig"
    ids = set()
    for p in t["posts"]:
        assert ID_RE.match(p["id"]), f"ungültige id {p['id']}"
        assert p["id"] not in ids, f"doppelte id {p['id']}"
        ids.add(p["id"])
        for tag in p["tags"]:
            assert tag in TAGS[1:], f"unbekannter Tag {tag} in {p['id']}"
        for s in p.get("sources", []):
            assert safe_url(s["url"]), f"ungültige Quelle in {p['id']}"


CSS = r"""
:root{--bg:#f3f5f8;--surface:#fff;--fg:#141a24;--muted:#545e70;--line:#d9dee7;--accent:#c92a62;--accent-soft:#fbe3ec;--teal:#0d6f75;--ok:#1f7a4a;--ok-bg:#e2f3e9;--warn:#8a5100;--warn-bg:#fbefd9;--bad:#b42335;--bad-bg:#fbe2e5;--idle:#4f5a6d;--idle-bg:#e7ebf1;--f-display:"Archivo","Arial Narrow",system-ui,sans-serif;--f-body:"IBM Plex Sans",system-ui,-apple-system,"Segoe UI",sans-serif;--f-mono:"IBM Plex Mono",ui-monospace,"Cascadia Mono",Consolas,monospace;color-scheme:light}
@media (prefers-color-scheme:dark){:root{--bg:#0f131a;--surface:#171c25;--fg:#e8ecf3;--muted:#a3adbf;--line:#2a3140;--accent:#ff6b9a;--accent-soft:#3a1c29;--teal:#4cc3c9;--ok:#6fd39c;--ok-bg:#16301f;--warn:#f0b860;--warn-bg:#33270f;--bad:#ff7a87;--bad-bg:#3a1a1f;--idle:#b3bccb;--idle-bg:#222937;color-scheme:dark}}
*,*::before,*::after{box-sizing:border-box}
html,body{background:var(--bg);color:var(--fg)}
body{margin:0;font-family:var(--f-body);font-size:16px;line-height:1.6}
.wrap{max-width:980px;margin:0 auto;padding-block:32px 64px;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));display:flex;flex-direction:column;gap:28px}
header.top{display:flex;flex-direction:column;gap:10px}
.live{display:inline-flex;align-items:center;gap:8px;align-self:flex-start;font-family:var(--f-mono);font-size:12px;letter-spacing:.06em;color:var(--accent);text-transform:uppercase}
.live::before{content:"";width:8px;height:8px;border-radius:50%;background:var(--accent)}
@media (prefers-reduced-motion:no-preference){.live::before{animation:blink 2.4s ease-in-out infinite}}
@keyframes blink{50%{opacity:.25}}
h1{font-family:var(--f-display);font-stretch:78%;font-weight:800;font-size:clamp(34px,7vw,60px);line-height:.98;margin:0;letter-spacing:-.01em;text-wrap:balance}
h1 .hl{color:var(--accent)}
.lede{margin:0;color:var(--muted);max-width:62ch}
.meta{font-family:var(--f-mono);font-size:13px;color:var(--muted)}
.board{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));border:1px solid var(--line);background:var(--surface);border-radius:10px;overflow:hidden}
.cell{padding:16px 18px 18px;display:flex;flex-direction:column;gap:8px;min-width:0}
.cell+.cell{border-left:1px solid var(--line)}
.cell h2{margin:0;font-family:var(--f-mono);font-weight:500;font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
.pill{align-self:flex-start;font-family:var(--f-display);font-stretch:85%;font-weight:700;font-size:15px;padding:3px 10px;border-radius:999px;white-space:nowrap}
.pill[data-s=ok]{color:var(--ok);background:var(--ok-bg)}.pill[data-s=warn]{color:var(--warn);background:var(--warn-bg)}.pill[data-s=bad]{color:var(--bad);background:var(--bad-bg)}.pill[data-s=idle]{color:var(--idle);background:var(--idle-bg)}
.cell p{margin:0;font-size:14px;color:var(--muted)}
@media (max-width:760px){.board{grid-template-columns:repeat(2,minmax(0,1fr))}.cell:nth-child(3){border-left:0}.cell:nth-child(n+3){border-top:1px solid var(--line)}}
@media (max-width:420px){.board{grid-template-columns:1fr}.cell+.cell{border-left:0;border-top:1px solid var(--line)}}
.clock{display:flex;flex-wrap:wrap;gap:8px 28px;align-items:baseline;padding:14px 18px;border-radius:10px;background:var(--accent-soft)}
.clock b{font-family:var(--f-display);font-stretch:75%;font-weight:800;font-size:40px;line-height:1;color:var(--accent);font-variant-numeric:tabular-nums}
.clock .lbl{font-size:15px}.clock .ref{font-family:var(--f-mono);font-size:13px;color:var(--muted)}
.section{display:flex;flex-direction:column;gap:14px}
.feed-head{display:flex;flex-wrap:wrap;gap:12px;align-items:center;justify-content:space-between}
.section>h2,.feed-head h2{font-family:var(--f-display);font-stretch:85%;font-weight:800;font-size:26px;margin:0;line-height:1.2;text-wrap:balance}
.chips{display:flex;flex-wrap:wrap;gap:6px}
.chip{font:500 14px var(--f-body);color:var(--fg);background:var(--surface);border:1px solid var(--line);border-radius:999px;padding:5px 12px;cursor:pointer}
.chip[aria-pressed=true]{background:var(--fg);color:var(--bg);border-color:var(--fg)}
.chip:focus-visible,a:focus-visible,.faq summary:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.feed{list-style:none;margin:0;padding:0;display:flex;flex-direction:column}
.post{display:grid;grid-template-columns:128px minmax(0,1fr);gap:18px;padding:18px 0;border-top:1px solid var(--line);scroll-margin-top:16px}
.post[hidden]{display:none}
.when{font-family:var(--f-mono);font-size:13px;color:var(--muted);font-variant-numeric:tabular-nums}
.when strong{display:block;color:var(--fg);font-weight:500;font-size:14px}
.post h3{margin:0 0 6px;font-family:var(--f-display);font-stretch:88%;font-weight:700;font-size:20px;line-height:1.25;text-wrap:balance}
.post p{margin:0 0 10px;max-width:66ch}
.tags{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:8px}
.tag{font-family:var(--f-mono);font-size:11px;letter-spacing:.06em;text-transform:uppercase;padding:2px 7px;border-radius:4px;border:1px solid var(--line);color:var(--muted)}
.tag.conf-best{color:var(--ok);border-color:currentColor}.tag.conf-ber{color:var(--teal);border-color:currentColor}.tag.conf-ger{color:var(--warn);border-color:currentColor}
.src{font-size:14px;color:var(--muted);display:flex;flex-wrap:wrap;gap:4px 12px}
.src a{color:var(--teal);text-underline-offset:2px}
@media (max-width:560px){.post{grid-template-columns:1fr;gap:6px}.when strong{display:inline;margin-right:8px}}
.empty{padding:28px 0;border-top:1px solid var(--line);color:var(--muted)}
.faq{display:flex;flex-direction:column;border-top:1px solid var(--line)}
.faq details{border-bottom:1px solid var(--line);padding:14px 0}
.faq summary{cursor:pointer;font-family:var(--f-display);font-stretch:88%;font-weight:700;font-size:18px}
.faq details p{margin:8px 0 0;max-width:68ch;color:var(--muted)}
.warnbox{border:1px solid var(--line);border-radius:10px;padding:16px 18px;background:var(--surface);display:flex;flex-direction:column;gap:6px}
.warnbox strong{font-family:var(--f-display);font-stretch:88%;font-size:17px}
.warnbox p{margin:0;color:var(--muted);max-width:70ch}
.foot{font-size:13px;color:var(--muted);border-top:1px solid var(--line);padding-top:16px}
.foot p{margin:0;max-width:72ch}
"""

JS = r"""
(function(){
  var launch = document.getElementById('clock').getAttribute('data-launch').split('-').map(Number);
  function tick(){
    var n=new Date(), today=Date.UTC(n.getFullYear(),n.getMonth(),n.getDate());
    var diff=Math.round((Date.UTC(launch[0],launch[1]-1,launch[2])-today)/86400000);
    var num=document.getElementById('clockNum'), lbl=document.getElementById('clockLbl');
    if(diff>0){num.textContent=diff;lbl.textContent=diff===1?'Tag bis zum Konsolen-Launch':'Tage bis zum Konsolen-Launch';}
    else if(diff===0){num.textContent='Heute';lbl.textContent='erscheint GTA 6 auf Konsole';}
    else{num.textContent=-diff;lbl.textContent=(diff===-1?'Tag':'Tage')+' seit Konsolen-Launch, ohne PC-Version';}
  }
  tick(); setInterval(tick,60000);
  var chips=[].slice.call(document.querySelectorAll('.chip')), posts=[].slice.call(document.querySelectorAll('.post'));
  var empty=document.getElementById('emptyFilter');
  function apply(t){
    var shown=0;
    chips.forEach(function(c){c.setAttribute('aria-pressed',String(c.getAttribute('data-tag')===t));});
    posts.forEach(function(p){var ok=t==='Alle'||(' '+p.getAttribute('data-tags')+' ').indexOf(' '+t+' ')>-1;p.hidden=!ok;if(ok)shown++;});
    empty.hidden=shown>0;
  }
  var start='Alle'; try{var s=localStorage.getItem('gta6-filter'); if(s&&chips.some(function(c){return c.getAttribute('data-tag')===s;}))start=s;}catch(e){}
  apply(start);
  chips.forEach(function(c){c.addEventListener('click',function(){var t=c.getAttribute('data-tag');apply(t);try{localStorage.setItem('gta6-filter',t);}catch(e){}});});
})();
"""


def build():
    t = json.loads(DATA.read_text(encoding="utf-8"))
    validate(t)
    site = t["siteUrl"]
    posts = sorted(t["posts"], key=lambda p: p["ts"], reverse=True)
    upd_day, upd_time = fmt(t["updatedAt"])
    launch_day, _ = fmt(t["consoleLaunch"])

    def cell(title, v):
        return (f'<div class="cell"><h2>{e(title)}</h2>'
                f'<span class="pill" data-s="{e(v["state"])}">{e(v["label"])}</span>'
                f'<p>{e(v["note"])}</p></div>')

    board = "".join([cell("PC-Version", t["status"]["pc"]), cell("PC-Termin", t["status"]["date"]),
                     cell("Kopierschutz", t["status"]["drm"]), cell("Crack-Status", t["status"]["crack"])])

    items = []
    for p in posts:
        day, time = fmt(p["ts"])
        tags = "".join(f'<span class="tag">{e(x)}</span>' for x in p["tags"])
        if p.get("confidence"):
            tags += f'<span class="tag {conf_class(p["confidence"])}">{e(p["confidence"])}</span>'
        src = ""
        links = [f'<a href="{e(s["url"])}" target="_blank" rel="noopener noreferrer nofollow">{e(s["label"])}</a>'
                 for s in p.get("sources", []) if safe_url(s["url"])]
        if links:
            src = '<div class="src">Quellen:' + "".join(links) + "</div>"
        items.append(
            f'<li class="post" id="{e(p["id"])}" data-tags="{e(" ".join(p["tags"]))}">'
            f'<div class="when"><strong>{e(day)}</strong>{e(time)}</div>'
            f'<article style="min-width:0"><div class="tags">{tags}</div>'
            f'<h3>{e(p["title"])}</h3><p>{e(p["body"])}</p>{src}</article></li>')
    feed = "".join(items) + '<li class="empty" id="emptyFilter" hidden>Zu diesem Thema gibt es noch keinen Eintrag.</li>'

    chips = "".join(f'<button type="button" class="chip" data-tag="{e(x)}" aria-pressed="{"true" if x == "Alle" else "false"}">{e(x)}</button>' for x in TAGS)
    faq = "".join(f'<details><summary>{e(f["q"])}</summary><p>{e(f["a"])}</p></details>' for f in t["faq"])

    ld = json.dumps({
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "WebSite", "@id": site + "#website", "name": "GTA 6 PC Crack Tracker", "url": site, "inLanguage": "de"},
            {"@type": "LiveBlogPosting", "@id": site + "#liveblog", "headline": TITLE, "description": DESC, "url": site,
             "inLanguage": "de", "datePublished": "2026-11-18", "dateModified": t["updatedAt"], "coverageStartTime": "2023-12-05",
             "author": {"@type": "Organization", "name": "GTA 6 PC Crack Tracker", "url": site},
             "publisher": {"@type": "Organization", "name": "GTA 6 PC Crack Tracker", "url": site},
             "image": site + "og.png",
             "about": {"@type": "VideoGame", "name": "Grand Theft Auto VI", "publisher": {"@type": "Organization", "name": "Rockstar Games"}},
             "liveBlogUpdate": [{"@type": "BlogPosting", "headline": p["title"], "articleBody": p["body"],
                                 "datePublished": p["ts"], "url": site + "#" + p["id"]} for p in posts]},
            {"@type": "FAQPage", "@id": site + "#faq", "mainEntity": [
                {"@type": "Question", "name": f["q"], "acceptedAnswer": {"@type": "Answer", "text": f["a"]}} for f in t["faq"]]},
        ],
    }, ensure_ascii=False).replace("<", "\\u003c")

    verify = "".join(f'<meta name="google-site-verification" content="{e(v)}">' for v in t.get("googleVerification", []))

    page = f"""<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(TITLE)}</title>
<meta name="description" content="{e(DESC)}">
<meta name="robots" content="index, follow, max-image-preview:large">
{verify}
<link rel="canonical" href="{e(site)}">
<meta property="og:type" content="website">
<meta property="og:locale" content="de_DE">
<meta property="og:site_name" content="GTA 6 PC Crack Tracker">
<meta property="og:title" content="{e(TITLE)}">
<meta property="og:description" content="{e(DESC)}">
<meta property="og:url" content="{e(site)}">
<meta property="og:image" content="{e(site)}og.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{e(TITLE)}">
<meta name="twitter:description" content="{e(DESC)}">
<meta name="twitter:image" content="{e(site)}og.png">
<meta name="theme-color" content="#141a24">
<link rel="icon" href="favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@75..100,500..800&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>{CSS}</style>
<script type="application/ld+json">{ld}</script>
</head>
<body>
<main class="wrap">
<header class="top">
<span class="live">Live-Blog · wird täglich ergänzt</span>
<h1>GTA 6 <span class="hl">PC</span> Crack-Tracker</h1>
<p class="lede">Der GTA 6 PC Crack Tracker beantwortet drei Fragen: Gibt es GTA 6 für PC, welcher Kopierschutz steckt drin, und ist die PC-Version schon geknackt? Hier steht der aktuelle Stand mit Quellen, die neueste Meldung oben. Download-Links gibt es hier keine.</p>
<div class="meta">Zuletzt aktualisiert: {e(upd_day)}{(", " + e(upd_time)) if upd_time else ""}</div>
</header>
<section class="board" aria-label="Aktueller Status von GTA 6 auf PC">{board}</section>
<div class="clock" id="clock" data-launch="{e(t["consoleLaunch"])}" aria-live="polite"><b id="clockNum">{e(launch_day)}</b><span class="lbl" id="clockLbl">Konsolen-Launch von GTA 6</span><span class="ref">PS5 und Xbox Series X|S · {e(launch_day)}</span></div>
<section class="section" aria-labelledby="feed-title">
<div class="feed-head"><h2 id="feed-title">Live-Feed: GTA 6 PC, DRM und Crack-News</h2><div class="chips" role="group" aria-label="Nach Thema filtern">{chips}</div></div>
<ol class="feed">{feed}</ol>
</section>
<section class="section" aria-labelledby="faq-title">
<h2 id="faq-title">Häufige Fragen zu GTA 6 auf PC</h2>
<div class="faq">{faq}</div>
</section>
<aside class="warnbox"><strong>Vorsicht vor „GTA 6 PC Download“-Seiten</strong><p>Solange Rockstar keine PC-Version veröffentlicht hat, gibt es keinen echten PC-Build und damit auch keinen Crack. Seiten, Videos oder GitHub-Projekte, die einen „geleakten“ oder „gecrackten“ PC-Download anbieten und verlangen, den Virenschutz abzuschalten, verteilen fast immer Schadsoftware.</p></aside>
<footer class="foot"><p>Inoffizieller Fan-Tracker ohne Verbindung zu Rockstar Games oder Take-Two Interactive. Grand Theft Auto ist eine Marke von Take-Two Interactive. Hier stehen nur Nachrichten und Status, keine Downloads und keine Anleitungen.</p></footer>
</main>
<script>{JS}</script>
</body>
</html>
"""
    OUT.mkdir(exist_ok=True)
    (OUT / "index.html").write_text(page, encoding="utf-8")
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {site}sitemap.xml\n", encoding="utf-8")
    (OUT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"  <url>\n    <loc>{e(site)}</loc>\n    <lastmod>{t['updatedAt'][:10]}</lastmod>\n"
        "    <changefreq>daily</changefreq>\n    <priority>1.0</priority>\n  </url>\n</urlset>\n", encoding="utf-8")
    (OUT / ".nojekyll").write_text("", encoding="utf-8")
    print(f"OK: {len(posts)} Einträge, Stand {t['updatedAt']}, {site}")


if __name__ == "__main__":
    build()
