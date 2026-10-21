---
name: date-math
description: Calendar arithmetic done by the calendar — days, weeks, months and business days between two dates; adding years, months, weeks, days or business days (with holidays); and a date's weekday, ISO week, quarter and day of the year. Use for schedules, deadlines and timelines instead of counting days yourself.
requires: json, calendar, datetime
network: no
---

Input, by `op` (dates are `YYYY-MM-DD`; `holidays` is an optional list of dates that aren't business days):

- `{"op": "between", "from", "to", "inclusive"?, "holidays"?}` → `{"days", "weeks": {"weeks", "days"}, "months": {"months", "days"}, "business_days", "counted", "holidays_skipped", "from", "to"}`. Counted from the first date up to but not including the second, as subtraction does, or with `"inclusive": true` both dates; `counted` says which, and `holidays_skipped` lists the holidays that fell on working days in the count. Negative when `to` is earlier.
- `{"op": "add", "date", "years"?, "months"?, "weeks"?, "days"?, "business_days"?, "holidays"?}` → `{"result", "start", "clamped_to_month_end"}`. Years and months first (31 January + 1 month is 28 or 29 February, and `clamped_to_month_end` says so), then weeks and days, then business days (Monday to Friday, less the holidays; negative counts back).
- `{"op": "info", "date", "holidays"?}` → weekday, `iso_week` (`2026-W53`), `iso_week_day`, `day_of_year`, `quarter`, `days_in_month`, `leap_year`, `business_day`.

Each date in a result comes as `{"date", "weekday", "iso_week"}`. Bad input prints `{"error": …}`.

`ops.json` gives each job its own form with every field required. A small model inside a Coureur agent shell is offered `date-math_between`, `date-math_add` and `date-math_info` instead of one form with optional fields.
