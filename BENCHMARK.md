# Benchmark

Written by `python -m benchmark.run` from a real run. Seeded synthetic orders (seed 7) are split over 20 files with shuffled column order, renamed headers, mixed encodings and delimiters, one .xlsx in five, and every third file missing the date column. The combined output is checked cell by cell against the planted records.

| Measure | Result |
|---|---|
| Input files (CSV utf-8, utf-8-sig, cp1252; comma, semicolon, tab, pipe; .xlsx) | 20 |
| Rows in / rows out | 100,000 / 100,000 |
| Rows with every column aligned to truth | **100.0%** (100,000 of 100,000) |
| Output columns | 6 (Date, Order ID, amount, customer, Region, source_file) |
| Files reported with differing columns | 6 of 6 planted |
| Split by region: rows kept | 100,000 in 4 files |
| Split by 7,000 rows: rows kept | 100,000 in 15 files |
| Combine speed | 56,088 rows/sec (1.78 s) |

Speed is from one run on a desktop PC and will vary.
