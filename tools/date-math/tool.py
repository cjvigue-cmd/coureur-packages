"""date-math: calendar arithmetic, done by the calendar.

Reads input.json with an "op":
  between  {"from", "to", "inclusive"?, "holidays"?}  days, weeks, calendar months, business days
  add      {"date", "years"?, "months"?, "weeks"?, "days"?, "business_days"?, "holidays"?}
  info     {"date"}  weekday, ISO week, day of the year, quarter, days in the month, leap year
Dates are ISO (YYYY-MM-DD). Business days are Monday to Friday, less the
given holidays. "between" counts from the first date up to but not
including the second, as subtraction does; with "inclusive": true it
counts both dates. Its result says which ("counted") and which holidays
it skipped.
"""
import calendar
import json
from datetime import date, timedelta

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


class Bad(Exception):
    pass


def day(s, what):
    try:
        return date.fromisoformat(str(s).strip())
    except (TypeError, ValueError):
        raise Bad(f"{what}: {s!r} isn't a date (YYYY-MM-DD)")


def whole(v, what):
    if v is None:
        return 0
    if isinstance(v, bool) or not isinstance(v, int):
        raise Bad(f"{what}: a whole number")
    return v


def business(d, holidays):
    return d.weekday() < 5 and d not in holidays


def add_months(d, n):
    m = d.month - 1 + n
    y, m = d.year + m // 12, m % 12 + 1
    last = calendar.monthrange(y, m)[1]
    return date(y, m, min(d.day, last)), d.day > last


def describe(d):
    iso = d.isocalendar()
    return {"date": d.isoformat(), "weekday": DAYS[d.weekday()], "iso_week": f"{iso[0]}-W{iso[1]:02d}"}


def main():
    d = json.load(open("input.json"))
    op = d.get("op")
    try:
        holidays = {day(h, "holidays") for h in d.get("holidays", [])}
        if op == "between":
            a, b = day(d.get("from"), "from"), day(d.get("to"), "to")
            inclusive = d.get("inclusive", False)
            if not isinstance(inclusive, bool):
                raise Bad("inclusive: true or false")
            lo, hi, sign = (a, b, 1) if a <= b else (b, a, -1)
            if inclusive:
                hi += timedelta(days=1)
            n = (hi - lo).days
            months = (hi.year - lo.year) * 12 + hi.month - lo.month
            while months > 0 and add_months(lo, months)[0] > hi:
                months -= 1
            rest = (hi - add_months(lo, months)[0]).days
            work = sum(1 for i in range(n) if business(lo + timedelta(days=i), holidays))
            out = {
                "days": sign * n,
                "weeks": {"weeks": n // 7, "days": n % 7},
                "months": {"months": months, "days": rest},
                "business_days": sign * work,
                "counted": ("both dates and every day between" if inclusive else "from the first date up to, not including, the second"),
                "holidays_skipped": sorted(h.isoformat() for h in holidays if lo <= h < hi and h.weekday() < 5),
                "from": describe(a), "to": describe(b),
            }
        elif op == "add":
            start = day(d.get("date"), "date")
            y, mo, w, dd, bd = (whole(d.get(k), k) for k in ("years", "months", "weeks", "days", "business_days"))
            r, clamped = add_months(start, 12 * y + mo)
            r += timedelta(weeks=w, days=dd)
            step = 1 if bd >= 0 else -1
            left = abs(bd)
            while left:
                r += timedelta(days=step)
                if business(r, holidays):
                    left -= 1
            out = {"result": describe(r), "start": describe(start), "clamped_to_month_end": clamped}
        elif op == "info":
            x = day(d.get("date"), "date")
            iso = x.isocalendar()
            out = describe(x) | {
                "iso_week_day": iso[2],
                "day_of_year": x.timetuple().tm_yday,
                "quarter": (x.month - 1) // 3 + 1,
                "days_in_month": calendar.monthrange(x.year, x.month)[1],
                "leap_year": calendar.isleap(x.year),
                "business_day": business(x, holidays),
            }
        else:
            raise Bad("op: between, add or info")
    except Bad as e:
        print(json.dumps({"error": str(e)}))
        return
    except OverflowError:
        print(json.dumps({"error": "the result is outside the years 1 to 9999"}))
        return
    print(json.dumps(out))


main()
