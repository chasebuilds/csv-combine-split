# Limitations

- Encoding detection tries utf-8 with BOM, utf-8, then cp1252. A UTF-16 file or another legacy code page will be read wrongly (cp1252 accepts almost any bytes).
- Delimiter sniffing looks at the first 20,000 characters and only considers comma, semicolon, tab and pipe. A file with one column, or with quoted text full of another delimiter, can be misread.
- The first non-empty row is taken as the header. Title rows above the header, merged header cells or two-row headers are not handled.
- Only the first sheet of an .xlsx file is read. Legacy .xls is not supported.
- All values are kept as text. Excel dates and numbers are converted with `str()`, so a date cell becomes `2026-01-05 00:00:00` and a leading zero lost in Excel stays lost.
- Header matching is by normalized name plus your alias map. It does not guess that "Qty" means "quantity" unless you add the alias.
- Two columns in one file that normalize to the same name are merged into one output column; the later one wins.
- Everything is loaded into memory. Files larger than available RAM will fail.
- Split file names come from the column value with unsafe characters replaced, so "N/A" and "N A" land in the same file.
- The benchmark uses synthetic data; real exports will have problems it does not plant.
