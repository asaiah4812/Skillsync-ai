import re
import pathlib

classes = set()
root = pathlib.Path(__file__).resolve().parent.parent / "templates"
for p in root.rglob("*.html"):
    text = p.read_text(encoding="utf-8", errors="ignore")
    for m in re.finditer(r'class="([^"]*)"', text):
        raw = m.group(1)
        if "{%" in raw or "{{" in raw:
            continue
        for c in raw.split():
            if c and not c.startswith("{%"):
                classes.add(c)

print("count", len(classes))
for c in sorted(classes):
    print(c)
