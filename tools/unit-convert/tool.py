"""unit-convert: exact unit conversion with a dimension check.

Reads input.json: {"value": "1.5", "from": "lbf", "to": "N", "difference"?: false}.
Units are symbols with SI prefixes (km, mA, µF, kWh, MiB …) and may be
compounds: km/h, N*m, N·m, m/s^2, W/m², kg*m^2/s^2 (left to right: a/b*c
is (a/b)·c). Factors are exact rationals from their definitions (1 in =
0.0254 m, 1 lb = 0.45359237 kg …), so a result is exact unless a
definition isn't (dBm). Temperatures in °C, °F and °R convert through
kelvin; with "difference": true they are differences (no offset).
"""
import json
import re
from decimal import Decimal, InvalidOperation, getcontext
from fractions import Fraction as Fr

getcontext().prec = 50
def dim(**p):
    """A dimension: the powers of m, kg, s, A, K, mol, cd and bit."""
    order = ["m", "kg", "s", "A", "K", "mol", "cd", "bit"]
    return tuple(p.get(k, 0) for k in order)


D = {
    "length": dim(m=1), "mass": dim(kg=1), "time": dim(s=1), "current": dim(A=1), "temperature": dim(K=1), "amount": dim(mol=1), "data": dim(bit=1),
    "force": dim(kg=1, m=1, s=-2), "energy or torque": dim(kg=1, m=2, s=-2), "power": dim(kg=1, m=2, s=-3), "pressure": dim(kg=1, m=-1, s=-2),
    "frequency": dim(s=-1), "voltage": dim(kg=1, m=2, s=-3, A=-1), "resistance": dim(kg=1, m=2, s=-3, A=-2), "charge": dim(A=1, s=1),
    "capacitance": dim(kg=-1, m=-2, s=4, A=2), "speed": dim(m=1, s=-1), "acceleration": dim(m=1, s=-2), "area": dim(m=2), "volume": dim(m=3),
    "data rate": dim(bit=1, s=-1), "energy density": dim(kg=1, m=-1, s=-2), "dimensionless": dim(),
}
# The same tuple can have two names (pressure, energy density): the first wins.
NAMES = {}
for k, v in D.items():
    NAMES.setdefault(v, k)

LBF = Fr("0.45359237") * Fr("9.80665")
UNITS = {
    # symbol: (factor to SI, dimension, takes SI prefixes)
    "m": (Fr(1), D["length"], True), "in": (Fr("0.0254"), D["length"], False), "ft": (Fr("0.3048"), D["length"], False),
    "yd": (Fr("0.9144"), D["length"], False), "mi": (Fr("1609.344"), D["length"], False), "nmi": (Fr(1852), D["length"], False), "mil": (Fr("0.0000254"), D["length"], False),
    "g": (Fr(1, 1000), D["mass"], True), "t": (Fr(1000), D["mass"], True), "lb": (Fr("0.45359237"), D["mass"], False), "oz": (Fr("0.45359237") / 16, D["mass"], False),
    "s": (Fr(1), D["time"], True), "min": (Fr(60), D["time"], False), "h": (Fr(3600), D["time"], False), "d": (Fr(86400), D["time"], False),
    "A": (Fr(1), D["current"], True), "K": (Fr(1), D["temperature"], True), "mol": (Fr(1), D["amount"], True),
    "N": (Fr(1), D["force"], True), "lbf": (LBF, D["force"], False), "kgf": (Fr("9.80665"), D["force"], False), "dyn": (Fr(1, 100000), D["force"], False),
    "J": (Fr(1), D["energy or torque"], True), "Wh": (Fr(3600), D["energy or torque"], True), "cal": (Fr("4.184"), D["energy or torque"], True),
    "eV": (Fr("1.602176634e-19"), D["energy or torque"], True), "BTU": (Fr("1055.05585262"), D["energy or torque"], False),
    "W": (Fr(1), D["power"], True), "hp": (LBF * Fr("0.3048") * 550, D["power"], False),
    "Pa": (Fr(1), D["pressure"], True), "bar": (Fr(100000), D["pressure"], True), "atm": (Fr(101325), D["pressure"], False),
    "psi": (LBF / Fr("0.0254") ** 2, D["pressure"], False), "torr": (Fr(101325, 760), D["pressure"], False), "mmHg": (Fr("133.322387415"), D["pressure"], False),
    "Hz": (Fr(1), D["frequency"], True), "V": (Fr(1), D["voltage"], True), "ohm": (Fr(1), D["resistance"], True), "Ω": (Fr(1), D["resistance"], True),
    "C": (Fr(1), D["charge"], True), "Ah": (Fr(3600), D["charge"], True), "F": (Fr(1), D["capacitance"], True),
    "L": (Fr(1, 1000), D["volume"], True), "l": (Fr(1, 1000), D["volume"], True), "gal": (Fr("3.785411784") / 1000, D["volume"], False),
    "floz": (Fr("3.785411784") / 1000 / 128, D["volume"], False),
    "mph": (Fr("1609.344") / 3600, D["speed"], False), "kph": (Fr(1000, 3600), D["speed"], False), "kn": (Fr(1852, 3600), D["speed"], False),
    "bit": (Fr(1), D["data"], True), "b": (Fr(1), D["data"], True), "B": (Fr(8), D["data"], True), "bps": (Fr(1), D["data rate"], True),
}
ALIASES = {"meter": "m", "metre": "m", "inch": "in", "foot": "ft", "feet": "ft", "mile": "mi", "gram": "g", "pound": "lb", "second": "s", "hour": "h",
           "minute": "min", "day": "d", "newton": "N", "joule": "J", "watt": "W", "volt": "V", "amp": "A", "ampere": "A", "byte": "B", "knot": "kn", "µ": "u", "μ": "u"}
PREFIX = {"Y": 24, "Z": 21, "E": 18, "P": 15, "T": 12, "G": 9, "M": 6, "k": 3, "h": 2, "da": 1, "d": -1, "c": -2, "m": -3, "u": -6, "µ": -6, "μ": -6, "n": -9, "p": -12, "f": -15, "a": -18}
BINARY = {"Ki": 10, "Mi": 20, "Gi": 30, "Ti": 40, "Pi": 50}
TEMPS = {"°C": "C", "degC": "C", "celsius": "C", "°F": "F", "degF": "F", "fahrenheit": "F", "°R": "R", "degR": "R", "rankine": "R", "kelvin": "K"}
LOGS = {"dBm": Fr(1, 1000), "dBW": Fr(1)}
SUPER = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹⁻", "0123456789-")


class Bad(Exception):
    pass


def one(sym):
    """A single unit symbol (with any prefix): (factor, dimension)."""
    sym = ALIASES.get(sym, sym)
    if sym in UNITS:
        return UNITS[sym][:2]
    for p, e in BINARY.items():
        if sym.startswith(p) and sym[len(p):] in ("B", "b", "bit"):
            f, d, _ = UNITS[sym[len(p):]]
            return f * 2 ** e, d
    for p in sorted(PREFIX, key=len, reverse=True):
        base = sym[len(p):]
        if sym.startswith(p) and base in UNITS and UNITS[base][2]:
            f, d, _ = UNITS[base]
            return f * Fr(10) ** PREFIX[p], d
    raise Bad(f"unknown unit {sym!r}")


def parse(expr):
    """A unit expression: (factor, dimension)."""
    s = expr.strip().translate(SUPER).replace("·", "*").replace("×", "*").replace(" ", "")
    if not s:
        raise Bad("no unit")
    tokens = re.findall(r"[*/]|[^*/]+", s)
    factor, dims, op = Fr(1), [0] * 8, "*"
    for t in tokens:
        if t in "*/":
            op = t
            continue
        m = re.fullmatch(r"(.+?)(?:\^?(-?\d+))?", t)
        name, power = m.group(1), int(m.group(2)) if m.group(2) else 1
        if re.fullmatch(r"\d+", name):
            raise Bad(f"{t!r} isn't a unit")
        if op == "/":
            power = -power
        f, d = one(name)
        factor *= f ** power
        dims = [a + b * power for a, b in zip(dims, d)]
        op = "*"
    return factor, tuple(dims)


def show(x):
    """A value as a decimal string, 12 significant digits at most; and whether nothing was rounded."""
    d = Decimal(x.numerator) / Decimal(x.denominator) if isinstance(x, Fr) else x
    r = Decimal(format(d, ".12g"))
    exact = isinstance(x, Fr) and Fr(r) == x
    if r == 0:
        return "0", exact
    if Decimal("1e-6") <= abs(r) < Decimal("1e15"):
        txt = format(r, "f")
        if "." in txt:
            txt = txt.rstrip("0").rstrip(".")
    else:
        txt = format(r.normalize(), "E")
    return txt, exact


def describe(d):
    if d in NAMES:
        return NAMES[d]
    order = ["m", "kg", "s", "A", "K", "mol", "cd", "bit"]
    return "·".join(f"{u}^{p}" if p != 1 else u for u, p in zip(order, d) if p)


def convert(value, src, dst, difference):
    src_t, dst_t = TEMPS.get(src), TEMPS.get(dst)
    if src in LOGS or dst in LOGS:
        # Power levels: dBm = 10·log10(P / 1 mW).
        if src in LOGS:
            w = (Decimal(10) ** (Decimal(value.numerator) / Decimal(value.denominator) / 10)) * (Decimal(LOGS[src].numerator) / Decimal(LOGS[src].denominator))
        else:
            f, d = parse(src)
            if d != D["power"]:
                raise Bad(f"{src} is {describe(d)}, not power: only power converts to {dst}")
            w = Decimal((value * f).numerator) / Decimal((value * f).denominator)
        if dst in LOGS:
            if w <= 0:
                raise Bad("a power level needs a power above zero")
            ref = Decimal(LOGS[dst].numerator) / Decimal(LOGS[dst].denominator)
            return 10 * (w / ref).log10(), "power level"
        f, d = parse(dst)
        if d != D["power"]:
            raise Bad(f"{dst} is {describe(d)}, not power: {src} converts only to power")
        return w / (Decimal(f.numerator) / Decimal(f.denominator)), "power"
    if src_t or dst_t:
        def to_k(v, u):
            if u in ("C",):
                return v if difference else v + Fr("273.15")
            if u == "F":
                return v * Fr(5, 9) if difference else (v + Fr("459.67")) * Fr(5, 9)
            if u == "R":
                return v * Fr(5, 9)
            f, d = parse(u)
            if d != D["temperature"]:
                raise Bad(f"{u} is {describe(d)}, not temperature")
            return v * f

        def from_k(k, u):
            if u == "C":
                return k if difference else k - Fr("273.15")
            if u == "F":
                return k * Fr(9, 5) if difference else k * Fr(9, 5) - Fr("459.67")
            if u == "R":
                return k * Fr(9, 5)
            f, d = parse(u)
            if d != D["temperature"]:
                raise Bad(f"{u} is {describe(d)}, not temperature")
            return k / f

        k = to_k(value, src_t or src)
        if not difference and k < 0:
            raise Bad("below absolute zero")
        return from_k(k, dst_t or dst), "temperature"
    f1, d1 = parse(src)
    f2, d2 = parse(dst)
    if d1 != d2:
        raise Bad(f"{src} is {describe(d1)} and {dst} is {describe(d2)}: they don't convert")
    return value * f1 / f2, describe(d1)


def main():
    d = json.load(open("input.json"))
    try:
        raw = d.get("value")
        if isinstance(raw, bool) or raw is None:
            raise Bad("value: a number")
        try:
            value = Fr(Decimal(str(raw).strip()))
        except (InvalidOperation, ValueError):
            raise Bad(f"value: {raw!r} isn't a number")
        src, dst = str(d.get("from", "")).strip(), str(d.get("to", "")).strip()
        result, dimension = convert(value, src, dst, bool(d.get("difference", False)))
    except Bad as e:
        print(json.dumps({"error": str(e)}))
        return
    text, exact = show(result)
    print(json.dumps({"value": text, "unit": dst, "from": {"value": format(Decimal(str(raw).strip()), "f"), "unit": src}, "dimension": dimension, "exact": exact}, ensure_ascii=False))


main()
