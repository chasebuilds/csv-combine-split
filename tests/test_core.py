from pathlib import Path

import pytest

from benchmark.run import run
from csv_combine_split.cli import main
from csv_combine_split.core import combine, read_table, split_by_column, split_by_rows


def test_encodings_delimiters_and_aliases(tmp_path: Path) -> None:
    (tmp_path / "a.csv").write_bytes("Order ID;Client;Region\n1;Renée;North\n".encode("cp1252"))
    (tmp_path / "b.csv").write_bytes("﻿order_id,customer,region,amount\n2,Bo,South,5\n".encode())
    header, rows, report = combine(
        [tmp_path / "a.csv", tmp_path / "b.csv"], {"Client": "customer"}
    )
    assert header == ["Order ID", "customer", "Region", "amount", "source_file"]
    assert rows == [["1", "Renée", "North", "", "a.csv"], ["2", "Bo", "South", "5", "b.csv"]]
    assert report.differing == {"a.csv": ["amount"]}


def test_split(tmp_path: Path) -> None:
    rows = [["1", "N"], ["2", "S"], ["3", "N"]]
    assert {k: len(v) for k, v in split_by_column(["id", "Region"], rows, "region").items()} == {
        "N": 2, "S": 1}
    assert list(split_by_rows(rows, 2)) == ["part0001", "part0002"]
    with pytest.raises(KeyError):
        split_by_column(["id"], rows, "nope")
    with pytest.raises(ValueError):
        split_by_rows(rows, 0)


def test_cli_roundtrip(tmp_path: Path) -> None:
    src = tmp_path / "in"
    src.mkdir()
    (src / "x.csv").write_text("id|region\n1|N\n2|S\n", encoding="utf-8")
    (src / "y.tsv").write_text("ID\tRegion\tnote\n3\tN\thi\n", encoding="utf-8")
    assert main(["combine", str(src), "-o", str(tmp_path / "all.xlsx")]) == 0
    header, rows = read_table(tmp_path / "all.xlsx")
    assert header == ["id", "region", "note", "source_file"] and len(rows) == 3
    assert main(["split", str(tmp_path / "all.xlsx"), "--by", "region", "-o", str(tmp_path / "o")]) == 0
    assert sorted(p.name for p in (tmp_path / "o").iterdir()) == ["all_N.csv", "all_S.csv"]
    assert main(["split", str(tmp_path / "all.xlsx"), "--rows", "2", "-o", str(tmp_path / "p"),
                 "--format", "xlsx"]) == 0


def test_benchmark_small() -> None:
    result = run(files=6, rows_per=50)
    assert result["Rows in / rows out"] == "300 / 300"
    assert "**100.0%**" in result["Rows with every column aligned to truth"]
