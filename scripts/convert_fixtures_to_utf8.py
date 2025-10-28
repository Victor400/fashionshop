
from pathlib import Path
import sys

def read_text_smart(p: Path) -> str:
    # try utf-8 first
    for enc in ("utf-8", "utf-16", "utf-16-le", "utf-16-be"):
        try:
            return p.read_text(encoding=enc)
        except UnicodeDecodeError:
            continue
    raise RuntimeError(f"Could not decode {p} as utf-8/utf-16")

def convert(path: Path):
    txt = read_text_smart(path)
    # basic sanity check: should look like JSON (array or object)
    if not txt.lstrip().startswith(("[", "{")):
        print(f"WARNING: {path} doesn't look like JSON at the start.")
    # write UTF-8 (no BOM)
    path.write_text(txt, encoding="utf-8", newline="\n")
    print(f"Converted -> UTF-8: {path}")

if __name__ == "__main__":
    root = Path("fixtures")
    files = [root / "brands.json", root / "categories.json", root / "products.json"]
    for f in files:
        if not f.exists():
            print(f"Missing: {f}")
            continue
        convert(f)
