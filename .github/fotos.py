"""Haalt alle AI-foto's (image.pollinations.ai) één keer op en zet ze als bestand in media/.

Daarna verwijzen de pagina's naar die bestanden, zodat de foto's altijd en
meteen laden, in plaats van bij elke bezoeker opnieuw door de AI gemaakt te worden.
"""
import glob, hashlib, html, re, sys, time, urllib.request

PAT = re.compile(r'src="(https://image\.pollinations\.ai/prompt/[^"]+)"')
pages = sorted(glob.glob("*.html"))
urls = []
for p in pages:
    for m in PAT.finditer(open(p, encoding="utf-8").read()):
        u = html.unescape(m.group(1))
        if u not in urls:
            urls.append(u)
print(f"{len(urls)} AI-foto's gevonden")

done = {}
for i, u in enumerate(urls, 1):
    name = f"media/ai-{hashlib.sha1(u.encode()).hexdigest()[:12]}.jpg"
    for attempt in range(1, 6):
        try:
            req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0 (prestige-taxi-site)", "Accept": "image/*"})
            with urllib.request.urlopen(req, timeout=240) as r:
                body = r.read()
                ctype = r.headers.get("Content-Type", "")
            ok = len(body) > 5000 and (body[:2] == b"\xff\xd8" or body[:4] == b"\x89PNG" or body[8:12] == b"WEBP")
            print(f"[{i}/{len(urls)}] poging {attempt}: HTTP 200, {ctype}, {len(body)} bytes, foto={ok}")
            if ok:
                open(name, "wb").write(body)
                done[u] = name
                break
            print("   begin van het antwoord:", body[:200])
        except Exception as e:
            print(f"[{i}/{len(urls)}] poging {attempt}: FOUT {e}")
            try:
                print("   antwoord:", e.read()[:300])
            except Exception:
                pass
        time.sleep(20 * attempt)
    time.sleep(5)

for p in pages:
    s = open(p, encoding="utf-8").read()
    def sub(m):
        u = html.unescape(m.group(1))
        return f'src="{done[u]}"' if u in done else m.group(0)
    open(p, "w", encoding="utf-8").write(PAT.sub(sub, s))

print(f"Klaar: {len(done)} van {len(urls)} foto's opgehaald")
sys.exit(0 if done else 1)
