"""One-off: move Roland/portal text colours onto theme tokens and add a dark palette."""
import pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent / "roland"

DARK = """  --heading:#DCE8CC; --chip:#2A3A34;
  --bg:#121D1A; --surface:#1A2925; --surface-2:#1F302B; --line:#30443D; --line-soft:#26372F;
  --ink:#E6ECE2; --ink-2:#B9C5B8; --ink-3:#97A598; --link:#A9C55A; --link-hover:#C3DB7A;
  --sage-soft:#24372C; --sand-soft:#3A3724; --sand-ink:#E2DCA8;
  --alert-bg:#4A2A1C; --alert-ink:#F2B9A0; --info-bg:#233A36; --info-ink:#CFE3DD;
  --shadow:0 10px 28px rgba(0,0,0,.45); color-scheme:dark;"""

DARK_BLOCKS = (
    "@media (prefers-color-scheme:dark){:root:not([data-theme=\"light\"]){\n" + DARK + "\n}}\n"
    ":root[data-theme=\"dark\"]{\n" + DARK + "\n}\n"
)

# Shared replacements: forest used as *text* on page surfaces becomes --heading;
# the light neutral chip fill becomes --chip; white page surfaces become --surface.
COMMON = [
    ("h1,h2,h3{font-family:var(--cond);color:var(--nf-forest)", "h1,h2,h3{font-family:var(--cond);color:var(--heading)"),
    ("h1,h2{font-family:var(--cond);color:var(--nf-forest)", "h1,h2{font-family:var(--cond);color:var(--heading)"),
    (".kpi .v{font-family:var(--cond);font-weight:700;font-size:30px;color:var(--nf-forest)", ".kpi .v{font-family:var(--cond);font-weight:700;font-size:30px;color:var(--heading)"),
    ("font-size:17px;color:var(--nf-forest)}", "font-size:17px;color:var(--heading)}"),
    (".col .h{font-family:var(--cond);font-weight:600;font-size:16px;color:var(--nf-forest)}", ".col .h{font-family:var(--cond);font-weight:600;font-size:16px;color:var(--heading)}"),
    ("background:var(--surface);color:var(--nf-forest);font-size:13.5px", "background:var(--surface);color:var(--heading);font-size:13.5px"),
    ("font-weight:700;color:var(--nf-forest)\">", "font-weight:700;color:var(--heading)\">"),
    ("font-size:28px;color:var(--nf-forest)\">", "font-size:28px;color:var(--heading)\">"),
    ("background:#ECEFE6", "background:var(--chip)"),
    # portal
    (".tab:hover{color:var(--nf-forest)}", ".tab:hover{color:var(--heading)}"),
    (".tab.on{color:var(--nf-forest)", ".tab.on{color:var(--heading)"),
    (".btn-ghost{border:1px solid var(--nf-olive);background:#fff;color:var(--nf-forest)}", ".btn-ghost{border:1px solid var(--nf-olive);background:var(--surface);color:var(--heading)}"),
    (".top{background:#fff;", ".top{background:var(--surface);"),
    (".logo .w{font-family:var(--sans);font-weight:700;font-size:19px;line-height:1.02;color:var(--nf-olive)", ".logo .w{font-family:var(--sans);font-weight:700;font-size:19px;line-height:1.02;color:var(--wordmark)"),
    (".ok{margin:0;font-size:14.5px;color:var(--nf-forest)", ".ok{margin:0;font-size:14.5px;color:var(--heading)"),
    # fixed bottom elements clear the phone's safe area
    (".launch{position:fixed;right:20px;bottom:20px;", ".launch{position:fixed;right:20px;bottom:calc(20px + env(safe-area-inset-bottom,0px));"),
    (".chat{position:fixed;right:20px;bottom:20px;", ".chat{position:fixed;right:20px;bottom:calc(20px + env(safe-area-inset-bottom,0px));"),
]


def apply(path: pathlib.Path) -> None:
    s = path.read_text(encoding="utf-8")
    if "--heading" in s:
        print(f"{path.name}: already themed, skipped")
        return
    for old, new in COMMON:
        s = s.replace(old, new)
    # light values for the new tokens go on bare :root
    s = s.replace(":root{\n", ":root{\n  --heading:#1D332F; --chip:#ECEFE6; --wordmark:#66783C; color-scheme:light;\n", 1)
    dark = DARK_BLOCKS.replace("--heading:#DCE8CC;", "--heading:#DCE8CC; --wordmark:#A9C55A;")
    # insert the dark blocks right after the first :root block
    end = s.index("}\n", s.index(":root{")) + 2
    s = s[:end] + dark + s[end:]
    path.write_text(s, encoding="utf-8")
    print(f"{path.name}: themed")


for name in sys.argv[1:] or ["index.html", "portal.html"]:
    apply(ROOT / name)
