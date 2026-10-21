"""budget-check: recompute a budget table and report every figure that doesn't add up.

Reads input.json: {"table": "<CSV or Markdown table>", "tolerance": "0.01"?}.
Columns are found by their header (case-insensitive): an item/description
column, optional category, quantity and unit-cost columns, and the line
total (total/amount/cost). Rows whose item starts with "subtotal" or
"total" are declared sums: a subtotal covers the items since the previous
subtotal (or its category's items when a category is given); "grand total",
or a "total" on the last row, covers every item. All arithmetic is exact
decimal; money is shown to the cent.
"""
import csv
import io
import json
import re
from decimal import Decimal, InvalidOperation

LABEL = ("item", "description", "line item", "name", "expense", "line")
CATEGORY = ("category", "section", "group")
QTY = ("qty", "quantity", "units", "count", "hours", "number")
UNIT = ("unit cost", "unit price", "rate", "cost per unit", "price", "unit")
TOTAL = ("total", "amount", "line total", "cost", "subtotal", "budget")
CENT = Decimal("0.01")


def money(d):
    return str(d.quantize(CENT))


def number(cell):
    """A figure as written: $ € £ and spaces ignored; (x) is negative; blank is None.
    A comma before three digits groups thousands (1,200); one before one or
    two final digits is a decimal comma (3,25), as is the last of "1.200,50"."""
    s = cell.strip().replace(" ", "").replace("\u00a0", "")
    for sym in "$€£¥":
        s = s.replace(sym, "")
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".") if s.rfind(",") > s.rfind(".") else s.replace(",", "")
    elif re.fullmatch(r"\(?-?\d+,\d{1,2}\)?", s):
        s = s.replace(",", ".")
    else:
        s = s.replace(",", "")
    neg = s.startswith("(") and s.endswith(")")
    s = s.strip("()")
    if s in ("", "-", "—", "–"):
        return None
    try:
        d = Decimal(s)
    except InvalidOperation:
        return "bad"
    return -d if neg else d


def rows_of(table):
    lines = [l for l in table.strip().splitlines() if l.strip()]
    if lines and lines[0].lstrip().startswith("|"):
        out = []
        for l in lines:
            cells = [c.strip() for c in l.strip().strip("|").split("|")]
            if all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
                continue
            out.append(cells)
        return out
    text = "\n".join(lines)
    try:
        dialect = csv.Sniffer().sniff(text.splitlines()[0], delimiters=",;\t")
    except csv.Error:
        dialect = csv.excel
    return [[c.strip() for c in r] for r in csv.reader(io.StringIO(text), dialect)]


def column(header, names, taken=()):
    """The first header (not already taken) that is one of `names`, in their
    order, else the first that starts with one of them, in their order."""
    h = [c.lower().strip() for c in header]
    free = [i for i in range(len(h)) if i not in taken]
    for n in names:
        for i in free:
            if h[i] == n:
                return i
    for n in names:
        for i in free:
            if h[i].startswith(n):
                return i
    return None


def main():
    d = json.load(open("input.json"))
    try:
        tol = Decimal(str(d.get("tolerance", "0.01")))
    except InvalidOperation:
        print(json.dumps({"error": "tolerance must be a number"}))
        return
    rows = rows_of(d.get("table", ""))
    if len(rows) < 2:
        print(json.dumps({"error": "give a table with a header row and at least one row"}))
        return
    header, body = rows[0], rows[1:]
    total_col = column(header, TOTAL)
    if total_col is None:
        print(json.dumps({"error": "no total column: name one total, amount or cost"}))
        return
    qty_col = column(header, QTY, {total_col})
    unit_col = column(header, UNIT, {total_col, qty_col})
    cat_col = column(header, CATEGORY, {total_col, qty_col, unit_col})
    label_col = column(header, LABEL, {total_col, qty_col, unit_col, cat_col})
    if label_col is None:
        label_col = next((i for i in range(len(header)) if i not in {total_col, qty_col, unit_col, cat_col}), None)

    def cell(r, i):
        return r[i] if i is not None and i < len(r) else ""

    errors, items = [], []  # items: (row number, category, line total as written)
    corrected = []  # each line recomputed where quantity and unit cost are given
    since = []  # item totals since the last subtotal
    declared_total = None
    for n, r in enumerate(body, start=2):
        label = cell(r, label_col)
        low = label.lower().strip()
        total = number(cell(r, total_col))
        if total == "bad":
            errors.append({"row": n, "what": "unreadable total", "cell": cell(r, total_col)})
            continue
        is_sum = re.match(r"(grand\s+)?(sub)?\s*total\b", low) is not None
        if is_sum:
            grand = low.startswith("grand") or (low.startswith("total") and n == len(body) + 1)
            cat = cell(r, cat_col).strip()
            if grand:
                computed = sum((t for _, _, t in items), Decimal(0))
                declared_total = total
                what = "grand total"
            elif cat:
                computed = sum((t for _, c, t in items if c == cat), Decimal(0))
                what = f"subtotal ({cat})"
            else:
                computed = sum(since, Decimal(0))
                what = "subtotal"
            since = []
            if total is None or abs(total - computed) > tol:
                errors.append({"row": n, "what": what, "declared": None if total is None else money(total), "computed": money(computed)})
            continue
        qty, unit = number(cell(r, qty_col)), number(cell(r, unit_col))
        if "bad" in (qty, unit):
            errors.append({"row": n, "what": "unreadable quantity or unit cost", "item": label})
            continue
        right = total
        if qty is not None and unit is not None:
            right = qty * unit
            if total is None or abs(total - right) > tol:
                errors.append({"row": n, "what": "line total", "item": label, "declared": None if total is None else money(total), "computed": money(right)})
            total = right if total is None else total
        if total is None:
            continue
        items.append((n, cell(r, cat_col).strip(), total))
        corrected.append(right)
        since.append(total)
    print(json.dumps({
        "ok": not errors,
        "items": len(items),
        "sum_of_lines": money(sum((t for _, _, t in items), Decimal(0))),
        "corrected_total": money(sum(corrected, Decimal(0))),
        "declared_total": None if declared_total is None else money(declared_total),
        "errors": errors,
    }))


main()
