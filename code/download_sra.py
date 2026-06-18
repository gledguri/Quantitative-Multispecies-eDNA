#!/usr/bin/env python3
"""
Download FASTQ files and metadata for NCBI BioProject PRJNA1426049.

Dependencies (auto-installed if missing):
  pip install requests pandas

Downloads:
  - metadata/metadata.csv        : run-level metadata from NCBI
  - fastq/<SRR_ID>/*.fastq.gz   : paired-end (or single) FASTQ files via ENA FTP
"""

import os
import sys
import csv
import time
import subprocess
import argparse
from pathlib import Path
from urllib.request import urlretrieve
from urllib.error import URLError

# ── auto-install lightweight deps ─────────────────────────────────────────────
def pip_install(*packages):
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", *packages])

try:
    import requests
except ImportError:
    print("Installing 'requests'...")
    pip_install("requests")
    import requests

try:
    import pandas as pd
except ImportError:
    print("Installing 'pandas'...")
    pip_install("pandas")
    import pandas as pd

# ── constants ─────────────────────────────────────────────────────────────────
BIOPROJECT   = "PRJNA1426049"
BASE_DIR     = Path(__file__).resolve().parent.parent / "SRA"
METADATA_DIR = BASE_DIR / "metadata"
FASTQ_DIR    = BASE_DIR / "fastq"

NCBI_ESEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
NCBI_EFETCH  = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
NCBI_ESUMMARY= "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"

ENA_PORTAL   = "https://www.ebi.ac.uk/ena/portal/api/filereport"
ENA_FTP_BASE = "ftp://ftp.sra.ebi.ac.uk"


# ── metadata helpers ──────────────────────────────────────────────────────────
def fetch_run_accessions(bioproject: str) -> list[str]:
    """Return all SRR accessions linked to the BioProject."""
    print(f"Querying NCBI SRA for runs in {bioproject}...")
    r = requests.get(NCBI_ESEARCH, params={
        "db": "sra", "term": f"{bioproject}[BioProject]",
        "retmax": 10000, "retmode": "json",
    })
    r.raise_for_status()
    ids = r.json()["esearchresult"]["idlist"]
    print(f"  Found {len(ids)} SRA entries.")
    return ids


def fetch_run_metadata_ncbi(sra_ids: list[str]) -> list[dict]:
    """Fetch run-level metadata from NCBI eSummary in batches."""
    rows = []
    batch = 200
    for i in range(0, len(sra_ids), batch):
        chunk = sra_ids[i:i+batch]
        r = requests.get(NCBI_ESUMMARY, params={
            "db": "sra", "id": ",".join(chunk), "retmode": "json",
        })
        r.raise_for_status()
        result = r.json().get("result", {})
        for uid in chunk:
            doc = result.get(uid, {})
            runs_raw = doc.get("runs", "")
            # runs_raw is an XML snippet: <Run acc="SRR..." ... />
            import re
            run_accs = re.findall(r'acc="(SRR\d+)"', runs_raw)
            for acc in run_accs:
                rows.append({
                    "uid": uid,
                    "run_accession": acc,
                    "experiment": doc.get("expxml", ""),
                    "title": doc.get("title", ""),
                    "spots": doc.get("spots", ""),
                    "bases": doc.get("bases", ""),
                    "platform": doc.get("platform", ""),
                    "create_date": doc.get("createdate", ""),
                })
        time.sleep(0.4)   # respect NCBI rate limit
    return rows


def fetch_run_metadata_ena(bioproject: str) -> pd.DataFrame | None:
    """Fetch comprehensive run metadata from ENA (richer fields)."""
    print("Fetching metadata from ENA portal...")
    r = requests.get(ENA_PORTAL, params={
        "accession": bioproject,
        "result": "read_run",
        "fields": (
            "run_accession,experiment_accession,sample_accession,"
            "secondary_sample_accession,study_accession,secondary_study_accession,"
            "submission_accession,tax_id,scientific_name,instrument_model,"
            "instrument_platform,library_name,library_layout,library_strategy,"
            "library_source,library_selection,read_count,base_count,"
            "sample_alias,sample_title,experiment_title,"
            "fastq_ftp,fastq_md5,fastq_bytes"
        ),
        "format": "tsv",
        "download": "true",
    }, timeout=60)
    if r.status_code == 200 and r.text.strip():
        from io import StringIO
        df = pd.read_csv(StringIO(r.text), sep="\t")
        print(f"  ENA returned {len(df)} runs.")
        return df
    print("  ENA returned no data; falling back to NCBI metadata.")
    return None


# ── download helpers ──────────────────────────────────────────────────────────
def wget_download(url: str, dest: Path) -> bool:
    """Download via system wget with progress."""
    cmd = ["wget", "-c", "-q", "--show-progress", "-O", str(dest), url]
    result = subprocess.run(cmd)
    return result.returncode == 0


def curl_download(url: str, dest: Path) -> bool:
    """Download via curl with progress (fallback)."""
    cmd = ["curl", "-L", "-C", "-", "-o", str(dest), url]
    result = subprocess.run(cmd)
    return result.returncode == 0


def ena_ftp_to_https(ftp_url: str) -> str:
    """Convert ENA FTP URL to HTTPS for environments without FTP support."""
    return ftp_url.replace("ftp://ftp.sra.ebi.ac.uk", "https://ftp.sra.ebi.ac.uk")


def download_run(run_acc: str, ftp_urls: list[str], out_dir: Path) -> bool:
    """Download all FASTQ files for a single run."""
    out_dir.mkdir(parents=True, exist_ok=True)
    all_ok = True
    for ftp_url in ftp_urls:
        if not ftp_url:
            continue
        fname = Path(ftp_url).name
        dest  = out_dir / fname
        if dest.exists() and dest.stat().st_size > 0:
            print(f"    [skip] {fname} already exists.")
            continue
        https_url = ena_ftp_to_https(ftp_url)
        print(f"    Downloading {fname}...")
        ok = wget_download(https_url, dest)
        if not ok:
            print(f"    wget failed, trying curl...")
            ok = curl_download(https_url, dest)
        if not ok:
            print(f"    ERROR: failed to download {fname}")
            all_ok = False
    return all_ok


# ── main ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description=f"Download SRA data for {BIOPROJECT}")
    parser.add_argument("--metadata-only", action="store_true",
                        help="Only fetch metadata, skip FASTQ download")
    parser.add_argument("--runs", nargs="+", metavar="SRR",
                        help="Download only these run accessions (default: all)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print what would be downloaded without downloading")
    args = parser.parse_args()

    METADATA_DIR.mkdir(exist_ok=True)
    FASTQ_DIR.mkdir(exist_ok=True)

    # ── 1. fetch metadata ──────────────────────────────────────────────────
    meta_csv = METADATA_DIR / "metadata.csv"
    df = fetch_run_metadata_ena(BIOPROJECT)

    if df is not None:
        df.to_csv(meta_csv, index=False)
        print(f"Metadata saved to {meta_csv}")
    else:
        # NCBI fallback
        sra_ids = fetch_run_accessions(BIOPROJECT)
        rows = fetch_run_metadata_ncbi(sra_ids)
        df = pd.DataFrame(rows)
        df.to_csv(meta_csv, index=False)
        print(f"Metadata (NCBI fallback) saved to {meta_csv}")

    print("\n── Metadata summary ─────────────────────────────────────────────")
    if "run_accession" in df.columns:
        print(f"  Total runs   : {len(df)}")
    if "instrument_model" in df.columns:
        print(f"  Instruments  : {df['instrument_model'].value_counts().to_dict()}")
    if "library_layout" in df.columns:
        print(f"  Layout       : {df['library_layout'].value_counts().to_dict()}")
    print()

    if args.metadata_only:
        print("--metadata-only flag set. Done.")
        return

    # ── 2. download FASTQs ─────────────────────────────────────────────────
    if "fastq_ftp" not in df.columns:
        print("ERROR: ENA metadata did not include fastq_ftp column.")
        print("Re-run with --metadata-only and check metadata/metadata.csv.")
        sys.exit(1)

    runs_to_download = args.runs if args.runs else df["run_accession"].tolist()
    total = len(runs_to_download)
    failed = []

    for i, run_acc in enumerate(runs_to_download, 1):
        row = df[df["run_accession"] == run_acc]
        if row.empty:
            print(f"[{i}/{total}] {run_acc}: not found in metadata, skipping.")
            continue

        ftp_field = row.iloc[0].get("fastq_ftp", "")
        ftp_urls  = [u.strip() for u in str(ftp_field).split(";")
                     if u.strip() and u.strip().endswith("_2.fastq.gz")]

        print(f"[{i}/{total}] {run_acc}: {len(ftp_urls)} file(s)")
        if args.dry_run:
            for u in ftp_urls:
                print(f"    would download: {ena_ftp_to_https(u)}")
            continue

        ok = download_run(run_acc, ftp_urls, FASTQ_DIR / run_acc)
        if not ok:
            failed.append(run_acc)

    # ── 3. summary ─────────────────────────────────────────────────────────
    print("\n── Download complete ─────────────────────────────────────────────")
    print(f"  Downloaded : {total - len(failed)}/{total} runs")
    if failed:
        print(f"  Failed     : {failed}")
        fail_log = METADATA_DIR / "failed_runs.txt"
        fail_log.write_text("\n".join(failed))
        print(f"  Retry list : {fail_log}")


if __name__ == "__main__":
    main()
