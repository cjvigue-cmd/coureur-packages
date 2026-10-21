---
name: unit-convert
description: Converts a quantity between units exactly, refusing a conversion between different dimensions. SI prefixes, imperial units, compounds (km/h, N*m, m/s^2), temperatures (°C, °F, °R, K, as values or differences), data sizes (kB, MiB) and radio power levels (dBm, dBW). Use instead of converting in your head, especially for specifications.
requires: json, re, decimal, fractions
network: no
---

Input `{"value": "1.5" (a decimal string keeps it exact; a number works), "from": unit, "to": unit, "difference"?: true}`.

Prints `{"value", "unit", "from": {"value", "unit"}, "dimension", "exact"}`. `value` has at most 12 significant digits; `exact` says whether that is the whole answer. Factors come from the units' definitions (1 in = 0.0254 m, 1 lb = 0.45359237 kg, g = 9.80665 m/s², 1 BTU = 1055.05585262 J (IT), 1 cal = 4.184 J, 1 hp = 550 ft·lbf/s, 1 gal = 3.785411784 L (US)) and are exact rationals; dBm and dBW go through logarithms, so they're never exact.

Units: SI prefixes (`k`, `M`, `m`, `u`/`µ`, `n` …) on m, g, t, s, A, K, mol, N, J, Wh, cal, eV, W, Pa, bar, Hz, V, ohm/Ω, C, Ah, F, L, bit/b, B, bps; binary prefixes (`Ki`, `Mi`, `Gi`) on B and bit; and in, ft, yd, mi, nmi, mil, lb, oz, min, h, d, lbf, kgf, dyn, BTU, hp, atm, psi, torr, mmHg, gal, floz, mph, kph, kn. Compounds read left to right (`a/b*c` is (a/b)·c), with powers as `^2` or `²`. Temperatures use `°C`/`degC`, `°F`/`degF`, `°R`, `K` (plain `C` is the coulomb, `F` the farad); `"difference": true` converts a temperature difference (10 °C of rise is 18 °F). A unit it doesn't know, a mismatch or a temperature below absolute zero prints `{"error": …}`.
