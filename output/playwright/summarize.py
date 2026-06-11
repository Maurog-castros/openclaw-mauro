import json
from pathlib import Path

d = json.loads(Path(r"c:\DEV\openclaw-mauro\output\playwright\hl_comparison.json").read_text(encoding="utf-8"))
print("=== ANTIGUO (h-l.cl) ===")
for m in d["old"]:
    if m.get("error"):
        print(f"  {m['label']}: ERROR {m['error']}")
        continue
    btns = ", ".join(m.get("buttons_sample", [])[:5])
    print(
        f"  {m['label']:20} | {m['title'][:48]:48} | "
        f"T={m['tables']} F={m['forms']} I={m['inputs']} | {btns}"
    )

print("\n=== DEV (dev.h-l.cl) ===")
dev = d.get("dev", {})
if dev.get("login_error"):
    print("LOGIN ERROR:", dev["login_error"])
else:
    for m in dev.get("modules", []):
        if m.get("error"):
            print(f"  {m.get('label')}: ERROR {m['error']}")
            continue
        print(f"  {str(m.get('label','?'))[:28]:28} | {str(m.get('title',''))[:40]:40} | {m.get('url','')}")
    print("\nNAV (primeros 40):")
    for n in dev.get("dashboard_nav", [])[:40]:
        print(f"  - {n.get('text','')[:50]:50} -> {n.get('href','')}")
