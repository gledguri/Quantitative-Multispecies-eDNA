#!/usr/bin/env python3
"""
Concatenate all _2.fastq.gz files from fastq/<SRR>/ subdirectories
into a single output file.

Usage:
  python3 concatenate_fastq.py
  python3 concatenate_fastq.py --output combined_R2.fastq.gz
  python3 concatenate_fastq.py --dry-run
"""

import argparse
import gzip
import sys
from pathlib import Path

BASE_DIR  = Path(__file__).parent
FASTQ_DIR = BASE_DIR / "fastq"
DEFAULT_OUT = BASE_DIR / "combined_R2.fastq.gz"


def find_r2_files(fastq_dir: Path) -> list[Path]:
    """Return sorted list of all _2.fastq.gz files under fastq_dir."""
    files = sorted(fastq_dir.rglob("*_2.fastq.gz"))
    return files


def concatenate(files: list[Path], output: Path, dry_run: bool = False):
    total = len(files)
    total_bytes = sum(f.stat().st_size for f in files)
    total_gb = total_bytes / 1e9

    print(f"Files to concatenate : {total}")
    print(f"Total size           : {total_gb:.2f} GB")
    print(f"Output               : {output}")
    print()

    if dry_run:
        print("-- dry run: files that would be concatenated --")
        for f in files:
            print(f"  {f}")
        return

    print("Concatenating... (this may take a while for large datasets)")
    # Decompress each file and write into a single gzip stream so the output
    # is a standard single-stream .fastq.gz that all tools can open normally.
    corrupt = []
    written = 0
    with gzip.open(output, "wb", compresslevel=1) as out_fh:
        for i, f in enumerate(files, 1):
            print(f"  [{i}/{total}] {f.name}", end="\r", flush=True)
            try:
                with gzip.open(f, "rb") as in_fh:
                    while chunk := in_fh.read(4 * 1024 * 1024):  # 4 MB chunks
                        out_fh.write(chunk)
                written += 1
            except (EOFError, gzip.BadGzipFile, OSError) as e:
                print(f"\n  WARNING: skipping corrupt file {f.name} ({e})")
                corrupt.append(f)

    final_size = output.stat().st_size / 1e9
    print(f"\nDone. Written {written}/{total} files. Output size: {final_size:.2f} GB → {output}")
    if corrupt:
        print(f"\nCorrupt/incomplete files ({len(corrupt)}) — re-download these:")
        for f in corrupt:
            print(f"  {f}")
        corrupt_log = output.parent / "corrupt_files.txt"
        corrupt_log.write_text("\n".join(str(f) for f in corrupt))
        print(f"\nList saved to {corrupt_log}")
        print("\nTo re-download, run:")
        srr_ids = " ".join(f.parent.name for f in corrupt)
        print(f"  python3 download_sra.py --runs {srr_ids}")


def main():
    parser = argparse.ArgumentParser(description="Concatenate all _2.fastq.gz files into one.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT,
                        help=f"Output file path (default: {DEFAULT_OUT})")
    parser.add_argument("--dry-run", action="store_true",
                        help="List files that would be concatenated without writing")
    args = parser.parse_args()

    if not FASTQ_DIR.exists():
        print(f"ERROR: fastq directory not found at {FASTQ_DIR}")
        print("Run download_sra.py first to download the files.")
        sys.exit(1)

    files = find_r2_files(FASTQ_DIR)
    if not files:
        print(f"No *_2.fastq.gz files found under {FASTQ_DIR}")
        sys.exit(1)

    if args.output.exists() and not args.dry_run:
        answer = input(f"\n{args.output} already exists. Overwrite? [y/N] ").strip().lower()
        if answer != "y":
            print("Aborted.")
            sys.exit(0)

    concatenate(files, args.output, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
