---
name: budget-check
description: Recomputes a budget table (CSV or Markdown) and reports every line total, subtotal and grand total that doesn't add up. Use before trusting or sending any budget a model wrote or edited.
requires: json, csv, decimal, re
network: no
---

Input `{"table": string, "tolerance"?: string}` (tolerance in currency units, default `"0.01"`).

Columns are found by their headers: an item/description column, optional `category`, `qty`/`quantity`/`hours` and `unit cost`/`rate`/`price`, and the line `total`/`amount`/`cost`. A row whose item starts with "subtotal" or "total" is a declared sum: a subtotal covers the items since the previous subtotal, or its category's items when the row names one; "grand total" (or "total" on the last row) covers every item. `$ € £`, thousands commas (`1,200`), decimal commas (`3,25`, `1.200,50`) and `(negative)` figures are read; the arithmetic is exact decimal.

Each sum is checked against the line totals as written, so one mistake is reported once, where it is. Prints `{"ok", "items", "sum_of_lines", "corrected_total" (every line recomputed from quantity × unit cost), "declared_total", "errors": [{"row", "what", "declared", "computed", …}]}`; `row` counts the header as row 1 (a Markdown table's `|---|` line isn't counted). A table it can't read prints `{"error": …}`.
