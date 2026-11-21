"""Seeded benchmark: plant files with mixed encodings, delimiters and header variants,
combine them, check every cell against the truth, split back, write BENCHMARK.md."""

from __future__ import annotations

import random
import re
import tempfile
import time
from pathlib import Path

from csv_combine_split.core import (
    combine,
    list_inputs,
    norm,
    split_by_column,
    split_by_rows,
    write_table,
)

ROOT = Path(__file__).resolve().parent.parent
CANON = ["order_id", "customer", "region", "amount", "date"]
VARIANTS = {
    "order_id": ["Order ID", "order-id", "ORDER_ID", "OrderNo"],
    "customer": ["Customer", "customer name", "Client"],
    "region": ["Region", "REGION", "sales region"],
    "amount": ["Amount", "amount_usd", "Total"],
    "date": ["Date", "order date", "DATE"],
}
ALIASES = {"OrderNo": "order_id", "customer name": "customer", "Client": "customer",
           "sales region": "region", "amount_usd": "amount", "Total": "amount",
           "order date": "date"}
NAMES = ["Zoe", "Andre", "Muller", "Jose", "Chloe", "Bjorn", "Renee", "Li"]
REGIONS = ["North", "South", "East", "West"]
FORMATS = [("utf-8", ","), ("utf-8-sig", ";"), ("cp1252", "\t"), ("utf-8", "|"), ("xlsx", "")]


def make(folder: Path, files: int, rows_per: int, seed: int = 7) -> dict[str, list[str]]:
    rng = random.Random(seed)
    truth: dict[str, list[str]] = {}
    oid = 0
    for f in range(files):
        enc, delim = FORMATS[f % len(FORMATS)]
        cols = list(CANON)
        if f % 3 == 2:
            cols.remove("date")
        rng.shuffle(cols)
        header = [rng.choice(VARIANTS[c]) for c in cols]
        rows = []
        for _ in range(rows_per):
            oid += 1
            rec = {"order_id": f"A{oid:07d}", "customer": rng.choice(NAMES) + rng.choice(["", "é"]),
                   "region": rng.choice(REGIONS), "amount": f"{rng.uniform(1, 999):.2f}",
                   "date": f"2026-{rng.randint(1, 12):02d}-{rng.randint(1, 28):02d}"}
            truth[rec["order_id"]] = [rec[c] if c in cols else "" for c in CANON]
            rows.append([rec[c] for c in cols])
        if enc == "xlsx":
            write_table(folder / f"f{f:02d}.xlsx", header, rows)
            continue
        text = "\n".join(delim.join(r) for r in [header, *rows]) + "\n"
        (folder / f"f{f:02d}.csv").write_bytes(text.encode(enc))
    return truth


def run(files: int = 20, rows_per: int = 5000) -> dict[str, str]:
    with tempfile.TemporaryDirectory() as tmp:
        folder = Path(tmp)
        truth = make(folder, files, rows_per)
        t0 = time.perf_counter()
        header, rows, report = combine(list_inputs(folder), ALIASES)
        secs = time.perf_counter() - t0
    col = {norm(h): i for i, h in enumerate(header)}
    right = sum(
        1 for r in rows
        if [r[col[c]] for c in CANON] == truth.get(r[col["order_id"]])
    )
    by_region = split_by_column(header, rows, "region")
    parts = split_by_rows(rows, 7000)
    expected_missing = sum(1 for f in range(files) if f % 3 == 2)
    return {
        "Input files (CSV utf-8, utf-8-sig, cp1252; comma, semicolon, tab, pipe; .xlsx)": f"{files}",
        "Rows in / rows out": f"{len(truth):,} / {len(rows):,}",
        "Rows with every column aligned to truth": f"**{right / len(truth):.1%}** ({right:,} of {len(truth):,})",
        "Output columns": f"{len(header)} ({', '.join(header)})",
        "Files reported with differing columns": f"{len(report.differing)} of {expected_missing} planted",
        "Split by region: rows kept": f"{sum(map(len, by_region.values())):,} in {len(by_region)} files",
        "Split by 7,000 rows: rows kept": f"{sum(map(len, parts.values())):,} in {len(parts)} files",
        "Combine speed": f"{len(rows) / secs:,.0f} rows/sec ({secs:.2f} s)",
    }


def table(result: dict[str, str]) -> str:
    lines = ["| Measure | Result |", "|---|---|"]
    lines += [f"| {k} | {v} |" for k, v in result.items()]
    return "\n".join(lines)


def main() -> None:
    t = table(run())
    (ROOT / "BENCHMARK.md").write_text(
        "# Benchmark\n\nWritten by `python -m benchmark.run` from a real run. Seeded synthetic "
        "orders (seed 7) are split over 20 files with shuffled column order, renamed headers, "
        "mixed encodings and delimiters, one .xlsx in five, and every third file missing the "
        "date column. The combined output is checked cell by cell against the planted records.\n\n"
        f"{t}\n\nSpeed is from one run on a desktop PC and will vary.\n",
        encoding="utf-8",
    )
    readme = ROOT / "README.md"
    text = readme.read_text(encoding="utf-8")
    text = re.sub(r"<!-- benchmark:start -->.*<!-- benchmark:end -->",
                  f"<!-- benchmark:start -->\n{t}\n<!-- benchmark:end -->", text, flags=re.S)
    readme.write_text(text, encoding="utf-8")
    print(t)


if __name__ == "__main__":
    main()
