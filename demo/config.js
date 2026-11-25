window.DEMO = {
  repo: "csv-combine-split",
  title: "csv-combine-split",
  tagline: "Drop in several CSV or Excel files with mismatched headers, delimiters and encodings. Get one file with the columns lined up and a source_file column, or split one big file by a column value or row count.",
  pkg: "csv_combine_split",
  packages: ["openpyxl"],
  inputs: [
    { id: "files", label: "CSV, TSV, TXT or XLSX files (pick several)", accept: ".csv,.tsv,.txt,.xlsx", multiple: true,
      sample: ["samples/orders_jan.csv", "samples/orders_feb.csv", "samples/orders_mar.xlsx"] },
  ],
  options: [
    { id: "mode", label: "Mode", type: "select", value: "combine",
      choices: [["combine", "combine all files into one"], ["split", "split the first file"]] },
    { id: "aliases", label: "Header aliases (JSON)", type: "text", value: '{"Client": "customer", "amount_usd": "amount"}' },
    { id: "by", label: "Split by column", type: "text", value: "Region" },
    { id: "rows", label: "or rows per file", type: "text", value: "", placeholder: "e.g. 5000" },
    { id: "format", label: "Output", type: "select", value: "xlsx", choices: [["xlsx", "Excel .xlsx"], ["csv", "CSV"]] },
  ],
  sampleNote: 'The sample is three synthetic order files: <a href="samples/orders_jan.csv">orders_jan.csv</a> (comma, UTF-8), <a href="samples/orders_feb.csv">orders_feb.csv</a> (semicolon, cp1252, headers "Order ID" and "Client" in another order) and <a href="samples/orders_mar.xlsx">orders_mar.xlsx</a> (no Region column, "amount_usd"). Split mode splits the first file.',
  python: `
import json as _json
from pathlib import Path
from csv_combine_split.cli import main as cli_main

def run(paths, opts):
    files = paths["files"]
    fmt = opts.get("format") or "xlsx"
    if opts.get("mode") == "split":
        out_dir = "/work/split"
        argv = ["split", files[0], "-o", out_dir, "--format", fmt]
        if opts.get("rows", "").strip():
            argv += ["--rows", opts["rows"].strip()]
        else:
            argv += ["--by", opts.get("by", "").strip() or "region"]
        code, log = run_cli(cli_main, argv)
        if code != 0 or not Path(out_dir).exists():
            return {"ok": False, "log": log, "sheets": [], "download": None}
        sheets = []
        for p in sorted(Path(out_dir).iterdir()):
            if p.suffix == ".xlsx":
                s = sheets_from_xlsx(str(p))[0]
                s["name"] = p.name
                sheets.append(s)
            else:
                sheets.append(sheet_from_csv(str(p), p.name))
        return {"ok": True, "log": log, "sheets": sheets, "download": zip_dir(out_dir, "/work/split.zip")}
    folder = Path("/work/in/files")
    argv = ["combine", str(folder), "-o", "/work/combined." + fmt]
    aliases = opts.get("aliases", "").strip()
    if aliases:
        _json.loads(aliases)  # show a clear error for bad JSON before the tool runs
        Path("/work/aliases.json").write_text(aliases, encoding="utf-8")
        argv += ["--aliases", "/work/aliases.json"]
    code, log = run_cli(cli_main, argv)
    out = "/work/combined." + fmt
    if code != 0 or not Path(out).exists():
        return {"ok": False, "log": log, "sheets": [], "download": None}
    sheets = sheets_from_xlsx(out) if fmt == "xlsx" else [sheet_from_csv(out, "combined.csv")]
    return {"ok": True, "log": log, "sheets": sheets, "download": out}
`,
};
