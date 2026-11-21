"""Command line: csvcs combine / csvcs split."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from csv_combine_split.core import (
    combine,
    list_inputs,
    read_table,
    split_by_column,
    split_by_rows,
    write_table,
)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="csvcs")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("combine", help="combine a folder of CSV/Excel files into one")
    c.add_argument("folder", type=Path)
    c.add_argument("-o", "--output", type=Path, required=True)
    c.add_argument("--aliases", type=Path, help="JSON map of header variant to canonical name")
    s = sub.add_parser("split", help="split one file by a column value or by row count")
    s.add_argument("file", type=Path)
    g = s.add_mutually_exclusive_group(required=True)
    g.add_argument("--by", help="column whose value picks the output file")
    g.add_argument("--rows", type=int, help="rows per output file")
    s.add_argument("-o", "--output", type=Path, required=True, help="output folder")
    s.add_argument("--format", choices=["csv", "xlsx"], default="csv")
    a = ap.parse_args(argv)

    if a.cmd == "combine":
        aliases = json.loads(a.aliases.read_text(encoding="utf-8")) if a.aliases else None
        header, rows, report = combine(list_inputs(a.folder), aliases)
        write_table(a.output, header, rows)
        print(f"combined {report.files} files, {report.rows} rows -> {a.output}")
        for name, missing in report.differing.items():
            print(f"  {name}: missing {', '.join(missing)}")
        return 0

    header, rows = read_table(a.file)
    groups = split_by_column(header, rows, a.by) if a.by else split_by_rows(rows, a.rows)
    for key, part in groups.items():
        write_table(a.output / f"{a.file.stem}_{key}.{a.format}", header, part)
    print(f"split {len(rows)} rows into {len(groups)} files -> {a.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
