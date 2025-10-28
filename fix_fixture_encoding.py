from pathlib import Path

files = ["fixtures/brands.json", "fixtures/categories.json", "fixtures/products.json"]
for f in files:
    p = Path(f)
    raw = p.read_bytes()
    text = None
    for enc in ("utf-16", "utf-16-le", "utf-16-be", "utf-8-sig", "utf-8"):
        try:
            text = raw.decode(enc)
            print(f"{f}: decoded as {enc}")
            break
        except Exception:
            pass
    if text is None:
        raise SystemExit(f"Could not decode {f}")
    p.write_text(text, encoding="utf-8")
    print(f"{f}: re-encoded to utf-8")