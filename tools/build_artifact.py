"""Build publishable artifact files from roland/.

Artifacts can't load fonts from relative files, so every
url(fonts/*.ttf) is inlined as a data URI. The main page is published without its
own doctype/head/body (the Artifact tool wraps it); the portal is a supporting page
and keeps its full document.

    python -I tools/build_artifact.py              # sample data only
    python -I tools/build_artifact.py --with-data  # embed data/snapshot.json (real customer data)
"""
import base64, json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "roland"
OUT = ROOT / "artifact"

FONT_URL = re.compile(r'url\(fonts/([\w\-]+\.ttf)\) format\("truetype"\)')


def inline_fonts(html: str) -> str:
    def repl(m):
        data = base64.b64encode((SRC / "fonts" / m.group(1)).read_bytes()).decode("ascii")
        return f'url(data:font/ttf;base64,{data}) format("truetype")'
    return FONT_URL.sub(repl, html)


def strip_document(html: str) -> str:
    """Keep <title>, <style> and body content; drop the doctype/html/head/body wrapper."""
    title = re.search(r"<title>.*?</title>", html, re.S).group(0)
    style = re.search(r"<style>.*?</style>", html, re.S).group(0)
    body = re.search(r"<body>(.*)</body>", html, re.S).group(1)
    return f"{title}\n{style}\n{body.strip()}\n"


def main() -> None:
    OUT.mkdir(exist_ok=True)

    page = (SRC / "index.html").read_text(encoding="utf-8")
    page = page.replace("<title>Roland · Nature's Flame CRM</title>", "<title>Roland CRM Mock</title>")
    page = strip_document(inline_fonts(page))
    if "--with-data" in sys.argv:
        snap = json.loads((ROOT / "data" / "snapshot.json").read_text(encoding="utf-8"))
        payload = json.dumps(snap, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
        page = page.replace("<script>", f"<script>window.ROLAND_SNAPSHOT={payload};</script>\n<script>", 1)
        print(f"embedded snapshot: {len(snap['accounts'])} accounts, data to {snap['meta']['asOf']}")
    (OUT / "roland.html").write_text(page, encoding="utf-8")

    portal = (SRC / "portal.html").read_text(encoding="utf-8")
    portal = portal.replace('content="width=device-width,initial-scale=1"', 'content="width=device-width,initial-scale=1,viewport-fit=cover"')
    portal = inline_fonts(portal)
    if "--with-data" in sys.argv:
        snap = json.loads((ROOT / "data" / "snapshot.json").read_text(encoding="utf-8"))
        keep = ("id", "name", "seg", "city", "island", "owner", "status")
        sub = {"meta": snap["meta"], "portal": snap.get("portal"),
               "accounts": [{k: a[k] for k in keep} for a in snap["accounts"]]}
        payload = json.dumps(sub, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
        portal = portal.replace("<script>", f"<script>window.ROLAND_PORTAL={payload};</script>\n<script>", 1)
        print(f"embedded portal data: {len(sub['accounts'])} customers")
    (OUT / "portal.html").write_text(portal, encoding="utf-8")

    for f in sorted(OUT.iterdir()):
        print(f"{f.name}: {f.stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    main()
