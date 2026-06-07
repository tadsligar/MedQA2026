#!/usr/bin/env python3
"""
Paper 2 EXP1 (step 0) — download UMLS via the UTS download API.

Reads your UMLS API key from the environment (NEVER hardcode it):
    export UMLS_API_KEY=...            # from uts.nlm.nih.gov -> My Profile

Downloads the 2025AB Metathesaurus Full Subset (contains MRCONSO/MRSTY/MRDEF/MRREL) into
data/umls/ (gitignored). You can also just download the zip manually from the NLM site and
unzip it into data/umls/ — this script is a convenience wrapper around the documented API:
    https://documentation.uts.nlm.nih.gov/automating-downloads.html

Usage:
    export UMLS_API_KEY=xxxxxxxx-....
    python scripts/umls/download_umls.py --release 2025AB --out data/umls
"""
import os
import sys
import argparse
import subprocess
from pathlib import Path

# Default: the Metathesaurus Full Subset (has the .RRF files the pipeline needs).
DEFAULT_FILE_URL = ("https://download.nlm.nih.gov/umls/kss/"
                    "{release}/umls-{release}-metathesaurus-full.zip")
UTS_DOWNLOAD = "https://uts-ws.nlm.nih.gov/download"


def main():
    ap = argparse.ArgumentParser(description="Download UMLS via UTS API (key from $UMLS_API_KEY)")
    ap.add_argument("--release", default="2025AB")
    ap.add_argument("--out", default="data/umls")
    ap.add_argument("--file-url", default=None,
                    help="override the NLM file URL (default: metathesaurus full subset)")
    args = ap.parse_args()

    api_key = os.environ.get("UMLS_API_KEY")
    if not api_key:
        sys.exit("ERROR: set UMLS_API_KEY in your environment first "
                 "(export UMLS_API_KEY=...). Do NOT hardcode it.")

    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    file_url = args.file_url or DEFAULT_FILE_URL.format(release=args.release)
    zip_name = file_url.rsplit("/", 1)[-1]
    dest = out / zip_name

    # The UTS download API proxies the licensed file given the API key.
    url = f"{UTS_DOWNLOAD}?url={file_url}&apiKey={api_key}"
    print(f"Downloading {zip_name} -> {dest}")
    print("(key read from $UMLS_API_KEY; not printed)")
    # curl with resume; --fail to error on HTTP errors. Key passed via argument list only.
    rc = subprocess.call(["curl", "-L", "--fail", "-C", "-", "-o", str(dest), url])
    if rc != 0:
        sys.exit(f"curl failed (rc={rc}). You can also download {zip_name} manually from the "
                 f"NLM site and unzip into {out}/")
    print(f"Downloaded. Now unzip:\n  unzip -o {dest} -d {out}/")
    print("Then point build_umls_index.py at the extracted META/*.RRF files.")


if __name__ == "__main__":
    main()
