"""Download source PDFs and pin them by SHA-256. First run records hashes; later runs verify."""
import hashlib, json, sys, time
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "data" / "sources.json"
RAW_DIR = ROOT / "data" / "raw"
HEADERS = {"User-Agent": "hybrid-rag-eval/0.1 (personal portfolio project)"}

def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()

def main() -> int:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    sources = json.loads(MANIFEST.read_text())
    failed = False
    for s in sources:
        path = RAW_DIR / f"{s['doc_id']}.pdf"
        if not path.exists():
            print(f"downloading {s['doc_id']} ...")
            r = requests.get(s["url"], headers=HEADERS, timeout=60)
            r.raise_for_status()
            path.write_bytes(r.content)
            time.sleep(3)  # be polite to the host
        digest = sha256_of(path)
        if s["sha256"] is None:
            s["sha256"] = digest
            print(f"  recorded hash for {s['doc_id']}: {digest[:12]}...")
        elif s["sha256"] != digest:
            print(f"  HASH MISMATCH for {s['doc_id']}: source changed or file corrupted")
            failed = True
        else:
            print(f"  ok {s['doc_id']} ({path.stat().st_size // 1024} KB)")
    MANIFEST.write_text(json.dumps(sources, indent=2) + "\n")
    return 1 if failed else 0

if __name__ == "__main__":
    sys.exit(main())
