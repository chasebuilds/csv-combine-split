"""Reading, writing, combining and splitting tables."""

from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass, field
from pathlib import Path

from openpyxl import Workbook, load_workbook

ENCODINGS = ("utf-8-sig", "utf-8", "cp1252")
DELIMITERS = ",;\t|"
TABLE_SUFFIXES = {".csv", ".tsv", ".txt", ".xlsx"}

Table = tuple[list[str], list[list[str]]]


def norm(name: str) -> str:
    """Lowercase, trim and collapse spaces, dashes and underscores."""
    return re.sub(r"[\s_\-]+", "_", name.strip().lower()).strip("_")


def decode(raw: bytes) -> tuple[str, str]:
    """Return (text, encoding) using the first encoding that decodes cleanly."""
    for enc in ENCODINGS:
        try:
            return raw.decode(enc), enc
        except UnicodeDecodeError:
            continue
    return raw.decode("cp1252", errors="replace"), "cp1252"


def sniff_delimiter(sample: str) -> str:
    first = sample.splitlines()[0] if sample else ""
    try:
        return csv.Sniffer().sniff(sample, delimiters=DELIMITERS).delimiter
    except csv.Error:
        return max(DELIMITERS, key=first.count) if first else ","


def read_table(path: Path) -> Table:
    """Read a CSV-like or .xlsx file into a header and string rows."""
    if path.suffix.lower() == ".xlsx":
        wb = load_workbook(path, read_only=True, data_only=True)
        values = [
            ["" if v is None else str(v) for v in row]
            for row in wb.worksheets[0].iter_rows(values_only=True)
        ]
        wb.close()
    else:
        text, _ = decode(path.read_bytes())
        values = list(csv.reader(io.StringIO(text), delimiter=sniff_delimiter(text[:20000])))
    values = [r for r in values if any(c.strip() for c in r)]
    if not values:
        return [], []
    return [h.strip() for h in values[0]], values[1:]


def write_table(path: Path, header: list[str], rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix.lower() == ".xlsx":
        wb = Workbook(write_only=True)
        ws = wb.create_sheet("data")
        ws.append(header)
        for r in rows:
            ws.append(r)
        wb.save(path)
        return
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


@dataclass
class CombineReport:
    files: int = 0
    rows: int = 0
    columns: list[str] = field(default_factory=list)
    differing: dict[str, list[str]] = field(default_factory=dict)


def combine(
    paths: list[Path], aliases: dict[str, str] | None = None, source_column: str = "source_file"
) -> tuple[list[str], list[list[str]], CombineReport]:
    """Stack files, aligning columns by normalized name after applying aliases."""
    alias_map = {norm(k): v for k, v in (aliases or {}).items()}
    order: list[str] = []
    display: dict[str, str] = {}
    loaded: list[tuple[Path, list[str], list[list[str]]]] = []
    for p in paths:
        header, rows = read_table(p)
        keys: list[str] = []
        for h in header:
            name = alias_map.get(norm(h), h)
            key = norm(name)
            if key not in display:
                order.append(key)
                display[key] = name
            keys.append(key)
        loaded.append((p, keys, rows))
    report = CombineReport(files=len(paths))
    full = set(order)
    out_rows: list[list[str]] = []
    for p, keys, rows in loaded:
        missing = sorted(full - set(keys))
        if missing:
            report.differing[p.name] = [display[k] for k in missing]
        idx = {k: i for i, k in enumerate(keys)}
        for r in rows:
            out_rows.append(
                [r[idx[k]] if k in idx and idx[k] < len(r) else "" for k in order] + [p.name]
            )
    header = [display[k] for k in order] + [source_column]
    report.rows = len(out_rows)
    report.columns = header
    return header, out_rows, report


def list_inputs(folder: Path) -> list[Path]:
    return sorted(
        p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in TABLE_SUFFIXES
    )


def _safe(value: str) -> str:
    return re.sub(r"[^\w\-]+", "_", value.strip()) or "blank"


def split_by_column(
    header: list[str], rows: list[list[str]], column: str
) -> dict[str, list[list[str]]]:
    wanted = norm(column)
    matches = [i for i, h in enumerate(header) if norm(h) == wanted]
    if not matches:
        raise KeyError(f"column not found: {column}")
    i = matches[0]
    groups: dict[str, list[list[str]]] = {}
    for r in rows:
        groups.setdefault(_safe(r[i] if i < len(r) else ""), []).append(r)
    return groups


def split_by_rows(rows: list[list[str]], size: int) -> dict[str, list[list[str]]]:
    if size < 1:
        raise ValueError("size must be at least 1")
    return {f"part{n + 1:04d}": rows[s : s + size] for n, s in enumerate(range(0, len(rows), size))}
