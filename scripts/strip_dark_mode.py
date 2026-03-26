"""
Remove dark: utility classes from template class attributes (plain CSS has no dark variants).
"""
import re
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent / "templates"


def strip_dark_in_classes(html: str) -> str:
    def repl(match: re.Match) -> str:
        inner = match.group(1)
        parts = inner.split()
        parts = [p for p in parts if p and not p.startswith("dark:")]
        return 'class="' + " ".join(parts) + '"'

    return re.sub(r'class="([^"]*)"', repl, html)


def main() -> None:
    for p in ROOT.rglob("*.html"):
        text = p.read_text(encoding="utf-8")
        new = strip_dark_in_classes(text)
        if new != text:
            p.write_text(new, encoding="utf-8")
            print("updated", p)


if __name__ == "__main__":
    main()
