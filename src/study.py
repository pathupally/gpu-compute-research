#!/usr/bin/env python3
"""Reproduce the paper's settlement audit, path-wedge bounds, and robustness study.

The analysis deliberately avoids fitting a latent-price or measurement-error
model.  It reports model-free payoff relations and deterministic sparse-error
robustness radii from a frozen 2026-08-29 vintage.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import statistics as stats
from collections import defaultdict
from pathlib import Path


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
DATA = ROOT / "data"
OUTPUT = ROOT / "outputs"
GENERATED = ROOT / "paper/generated"
FIGURES = ROOT / "paper/figures"

SERIES = {
    "KXA100W": ("a100-sxm4", "terminal"), "KXB200W": ("b200", "terminal"),
    "KXH100W": ("h100-sxm", "terminal"), "KXH200W": ("h200", "terminal"),
    "KXRTX5090W": ("rtx-5090", "terminal"),
    "KXB200MON": ("b200", "terminal"), "KXH100MON": ("h100-sxm", "terminal"),
    "KXH200MON": ("h200", "terminal"), "KXRTX5090MON": ("rtx-5090", "terminal"),
    "KXA100MAX": ("a100-sxm4", "touch"), "KXB200MAX": ("b200", "touch"),
    "KXH100MAX": ("h100-sxm", "touch"), "KXH200MAX": ("h200", "touch"),
    "KXRTX5090MAX": ("rtx-5090", "touch"),
    "KXB200Q": ("b200", "touch"), "KXH100Q": ("h100-sxm", "touch"),
    "KXH200Q": ("h200", "touch"),
}

MONTHS = {name: i for i, name in enumerate(
    ("JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"), 1)}
EPSILON_PCT = (0.5, 1.0, 2.0, 5.0, 10.0)


def load_json(path: Path):
    return json.loads(path.read_text())


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def quantile(values: list[float], p: float) -> float | None:
    if not values:
        return None
    x = sorted(values)
    position = (len(x) - 1) * p
    lo = int(math.floor(position))
    hi = int(math.ceil(position))
    if lo == hi:
        return x[lo]
    return x[lo] * (hi - position) + x[hi] * (position - lo)


def settlement_date(ticker: str) -> str | None:
    parts = ticker.split("-")
    if len(parts) < 2 or len(parts[1]) != 7:
        return None
    tag = parts[1]
    if tag[2:5] not in MONTHS or not (tag[:2] + tag[5:]).isdigit():
        return None
    return f"20{tag[:2]}-{MONTHS[tag[2:5]]:02d}-{int(tag[5:]):02d}"


def event_ticker(contract_ticker: str) -> str:
    return contract_ticker.rsplit("-", 1)[0]


def window(rows: list[tuple[str, float]], start: str, end: str) -> list[tuple[str, float]]:
    return [(date, value) for date, value in rows if start <= date <= end]


def functional(rows: list[tuple[str, float]], rule: str, settle_date: str) -> float | None:
    if not rows:
        return None
    if rule == "terminal":
        matches = [value for date, value in rows if date == settle_date]
        return matches[-1] if matches else None
    values = [value for _, value in rows]
    if rule == "touch":
        return max(values)
    if rule == "mean5":
        return stats.mean(values[-5:]) if len(values) >= 5 else None
    if rule == "median7":
        return stats.median(values[-7:]) if len(values) >= 7 else None
    if rule == "month_mean":
        month = settle_date[:7]
        month_values = [value for date, value in rows if date[:7] == month]
        return stats.mean(month_values) if month_values else None
    raise KeyError(rule)


def binary_outcome(value: float | None, strike: float) -> str | None:
    return None if value is None else ("yes" if value > strike else "no")


def collect_contracts(paths: dict[str, list[tuple[str, float]]], kalshi: dict) -> list[dict]:
    contracts: list[dict] = []
    for series_ticker, (gpu, actual_rule) in SERIES.items():
        doc = kalshi["series"][series_ticker]
        opens = {market["event_ticker"]: str(market.get("open_time", ""))[:10]
                 for market in doc["markets"]}
        for settled in doc["settlements"]:
            if settled.get("result") not in ("yes", "no"):
                continue
            ticker = settled["ticker"]
            date = settlement_date(ticker) or str(settled.get("close_time", ""))[:10]
            rows = paths[gpu]
            if not rows or date < rows[0][0] or date > rows[-1][0]:
                continue
            event = event_ticker(ticker)
            start = max(opens.get(event, rows[0][0]), rows[0][0])
            segment = window(rows, start, date)
            strike = float(settled["floor_strike"])
            values = {rule: functional(segment, rule, date)
                      for rule in ("terminal", "mean5", "median7", "month_mean", "touch")}
            outcomes = {rule: binary_outcome(value, strike) for rule, value in values.items()}
            contracts.append({
                "ticker": ticker, "event": event, "series": series_ticker, "gpu": gpu,
                "actual_rule": actual_rule, "settle_date": date, "window_start": start,
                "n_observations": len(segment), "strike": strike,
                "recorded_result": settled["result"], "settled_value": settled.get("settled_value"),
                "values": values, "outcomes": outcomes,
            })
    return contracts


def audit_settlements(contracts: list[dict]) -> dict:
    outcome_failures = []
    numeric_failures = []
    numeric_checked = 0
    rule_counts: dict[str, int] = defaultdict(int)
    for contract in contracts:
        rule = contract["actual_rule"]
        rule_counts[rule] += 1
        if contract["outcomes"][rule] != contract["recorded_result"]:
            outcome_failures.append(contract["ticker"])
        settled_value = contract["settled_value"]
        if settled_value is not None:
            numeric_checked += 1
            if abs(float(settled_value) - float(contract["values"][rule])) >= 0.005:
                numeric_failures.append(contract["ticker"])
    events = sorted({contract["event"] for contract in contracts})
    return {
        "n_strike_contracts": len(contracts), "n_events": len(events),
        "rule_counts": dict(rule_counts),
        "outcome_reproduced": len(contracts) - len(outcome_failures),
        "outcome_failures": outcome_failures,
        "numeric_checked": numeric_checked,
        "numeric_reproduced": numeric_checked - len(numeric_failures),
        "numeric_failures": numeric_failures,
    }


def perturb(rows: list[tuple[str, float]], index: int, signed_log_change: float) -> list[tuple[str, float]]:
    factor = math.exp(signed_log_change)
    return [(date, value * factor if i == index else value)
            for i, (date, value) in enumerate(rows)]


def sparse_radius(rows: list[tuple[str, float]], rule: str, settle_date: str,
                  strike: float, direction: int, maximum_log_change: float = math.log(100.0)) -> float:
    """Smallest one-print log perturbation that changes the binary payoff.

    ``direction`` is +1 for an upward perturbation and -1 for a downward one.
    Infinity means no one-print perturbation in that direction can change the
    payoff, even when that print is multiplied/divided by 100.
    """
    base_value = functional(rows, rule, settle_date)
    base = binary_outcome(base_value, strike)
    if base is None:
        return math.inf

    def flips(epsilon: float) -> bool:
        return any(binary_outcome(functional(perturb(rows, i, direction * epsilon), rule, settle_date), strike) != base
                   for i in range(len(rows)))

    if not flips(maximum_log_change):
        return math.inf
    lo, hi = 0.0, maximum_log_change
    for _ in range(52):
        mid = (lo + hi) / 2
        if flips(mid):
            hi = mid
        else:
            lo = mid
    return hi


def compute_radii(contracts: list[dict], paths: dict[str, list[tuple[str, float]]]) -> list[dict]:
    rows_out = []
    for contract in contracts:
        segment = window(paths[contract["gpu"]], contract["window_start"], contract["settle_date"])
        for rule in ("terminal", "mean5", "median7", "month_mean", "touch"):
            base = contract["outcomes"].get(rule)
            if base is None:
                continue
            for direction in (+1, -1):
                radius = sparse_radius(segment, rule, contract["settle_date"], contract["strike"], direction)
                rows_out.append({
                    "ticker": contract["ticker"], "event": contract["event"], "gpu": contract["gpu"],
                    "rule": rule, "actual_rule": contract["actual_rule"], "base_outcome": base,
                    "direction": "up" if direction > 0 else "down",
                    "radius_log": None if math.isinf(radius) else radius,
                    "radius_pct": None if math.isinf(radius) else 100.0 * math.expm1(radius),
                })
    return rows_out


def event_weighted_frontier(radii: list[dict]) -> list[dict]:
    result = []
    for rule in ("terminal", "mean5", "median7", "month_mean", "touch"):
        for direction, base_outcome, interpretation in (
            ("up", "no", "false_positive"), ("down", "yes", "false_negative")):
            eligible = [row for row in radii if row["rule"] == rule and row["direction"] == direction
                        and row["base_outcome"] == base_outcome]
            by_event: dict[str, list[dict]] = defaultdict(list)
            for row in eligible:
                by_event[row["event"]].append(row)
            for epsilon in EPSILON_PCT:
                event_shares = []
                strike_total = strike_vulnerable = 0
                for rows in by_event.values():
                    indicators = [row["radius_pct"] is not None and row["radius_pct"] <= epsilon + 1e-9
                                  for row in rows]
                    event_shares.append(sum(indicators) / len(indicators))
                    strike_vulnerable += sum(indicators)
                    strike_total += len(indicators)
                result.append({
                    "rule": rule, "direction": direction, "interpretation": interpretation,
                    "epsilon_pct": epsilon, "n_events": len(by_event), "n_strikes": strike_total,
                    "event_weighted_vulnerable_share": stats.mean(event_shares) if event_shares else None,
                    "strike_weighted_vulnerable_share": strike_vulnerable / strike_total if strike_total else None,
                })
    return result


BUCKET_RE = re.compile(r"^\$(?P<low>[0-9.]+)-\$(?P<high>[0-9.]+)$")
TOUCH_RE = re.compile(r"^↑ \$(?P<strike>[0-9.]+)$")


def parse_bucket(label: str) -> tuple[float, float]:
    if label.startswith("<$"):
        return -math.inf, float(label[2:])
    if label.endswith("+"):
        return float(label[1:-1]), math.inf
    match = BUCKET_RE.match(label)
    if not match:
        raise ValueError(f"unrecognized bucket: {label}")
    return float(match.group("low")), float(match.group("high"))


def hourly(history: list[dict]) -> dict[int, float]:
    out = {}
    for point in history:
        out[int(point["t"]) // 3600] = float(point["p"])
    return out


def surface_events(poly: dict) -> dict[tuple[str, str], dict]:
    out = {}
    for event in poly["events"]:
        gpu_match = re.search(r"\((B200|H100|H200)\)", event["title"])
        if not gpu_match:
            continue
        kind = "terminal" if "end of 2026" in event["title"] else "touch"
        out[(gpu_match.group(1), kind)] = event
    return out


def matched_surface_bounds(poly: dict) -> tuple[list[dict], list[dict]]:
    events = surface_events(poly)
    bounds, histories = [], []
    for gpu in ("B200", "H100", "H200"):
        terminal = events[(gpu, "terminal")]
        touch = events[(gpu, "touch")]
        buckets = []
        for market in terminal["markets"]:
            low, high = parse_bucket(market["group_item_title"])
            buckets.append({**market, "low": low, "high": high, "hourly": hourly(market["yes_history"])})
        snapshot_total = sum(market["yes_price"] for market in buckets)
        for market in touch["markets"]:
            match = TOUCH_RE.match(market["group_item_title"])
            if not match:
                continue
            strike = float(match.group("strike"))
            touch_price = float(market["yes_price"])
            # Already resolved or effectively resolved contracts no longer carry
            # forward first-passage uncertainty and are excluded from the primary set.
            if not (0.01 < touch_price < 0.99) or not market["yes_history"]:
                continue
            overlapping = [bucket for bucket in buckets if bucket["high"] > strike]
            tail_raw = sum(bucket["yes_price"] for bucket in overlapping)
            tail_normalized = tail_raw / snapshot_total
            exact_boundary = any(abs(bucket["low"] - strike) < 1e-12 for bucket in buckets)
            row = {
                "gpu": gpu, "strike": strike, "touch_price": touch_price,
                "terminal_tail_upper_raw": tail_raw,
                "terminal_bucket_sum": snapshot_total,
                "terminal_tail_upper_normalized": tail_normalized,
                "crossing_reversal_lower_bound_raw": max(0.0, touch_price - tail_raw),
                "crossing_reversal_lower_bound_normalized": max(0.0, touch_price - tail_normalized),
                "terminal_tail_is_exact": exact_boundary,
                "terminal_event_liquidity": terminal.get("liquidity"),
                "touch_event_liquidity": touch.get("liquidity"),
            }

            touch_hourly = hourly(market["yes_history"])
            common_hours = set(touch_hourly)
            for bucket in buckets:
                common_hours &= set(bucket["hourly"])
            wedge_values = []
            for hour in sorted(common_hours):
                total = sum(bucket["hourly"][hour] for bucket in buckets)
                tail = sum(bucket["hourly"][hour] for bucket in overlapping)
                if total <= 0:
                    continue
                tail_norm = tail / total
                wedge = touch_hourly[hour] - tail_norm
                histories.append({
                    "gpu": gpu, "strike": strike, "hour": hour,
                    "touch_price": touch_hourly[hour], "terminal_tail_upper_normalized": tail_norm,
                    "wedge_lower_bound": wedge,
                })
                wedge_values.append(wedge)
            row["history"] = {
                "n_hours": len(wedge_values), "minimum": min(wedge_values),
                "q25": quantile(wedge_values, 0.25), "median": quantile(wedge_values, 0.5),
                "q75": quantile(wedge_values, 0.75), "maximum": max(wedge_values),
                "share_positive": sum(value > 0 for value in wedge_values) / len(wedge_values),
            }
            bounds.append(row)
    return bounds, histories


def write_csv(path: Path, rows: list[dict], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("")
        return
    fields = fields or list(rows[0])
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fields,
            extrasaction="ignore",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def svg_escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def write_surface_svg(bounds: list[dict]) -> None:
    width, height = 1080, 560
    left, right, top, bottom = 90, 35, 50, 80
    plot_w, plot_h = width - left - right, height - top - bottom
    colors = {"B200": "#2563eb", "H100": "#d97706", "H200": "#059669"}
    x_positions = list(range(len(bounds)))
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
             '<rect width="100%" height="100%" fill="white"/>',
             '<style>text{font-family:Helvetica,Arial,sans-serif;fill:#172033}.axis{stroke:#64748b;stroke-width:1}.grid{stroke:#dbe3ee;stroke-width:1}.touch{fill:#334155}.tail{fill:#cbd5e1}</style>']
    for tick in range(0, 11, 2):
        y = top + plot_h * (1 - tick / 10)
        parts.append(f'<line class="grid" x1="{left}" y1="{y:.1f}" x2="{left+plot_w}" y2="{y:.1f}"/>')
        parts.append(f'<text x="{left-12}" y="{y+5:.1f}" font-size="15" text-anchor="end">{tick*10}%</text>')
    group_w = plot_w / max(1, len(bounds))
    for i, row in enumerate(bounds):
        cx = left + group_w * (i + 0.5)
        for offset, key, cls in ((-17, "touch_price", "touch"), (17, "terminal_tail_upper_normalized", "tail")):
            value = row[key]
            h = value * plot_h
            parts.append(f'<rect class="{cls}" x="{cx+offset-13:.1f}" y="{top+plot_h-h:.1f}" width="26" height="{h:.1f}" rx="2"/>')
        label = f'{row["gpu"]} ${row["strike"]:g}'
        parts.append(f'<text x="{cx:.1f}" y="{top+plot_h+28}" font-size="15" text-anchor="middle">{svg_escape(label)}</text>')
        wedge = row["crossing_reversal_lower_bound_normalized"]
        parts.append(f'<text x="{cx:.1f}" y="{top+plot_h+49}" font-size="13" text-anchor="middle" fill="{colors[row["gpu"]]}">gap {wedge:.1%}</text>')
    parts.extend([
        f'<line class="axis" x1="{left}" y1="{top+plot_h}" x2="{left+plot_w}" y2="{top+plot_h}"/>',
        f'<line class="axis" x1="{left}" y1="{top}" x2="{left}" y2="{top+plot_h}"/>',
        '<rect class="touch" x="760" y="18" width="20" height="14"/><text x="788" y="30" font-size="15">one-touch YES</text>',
        '<rect class="tail" x="905" y="18" width="20" height="14"/><text x="933" y="30" font-size="15">terminal tail upper bound</text>',
        '</svg>'])
    FIGURES.mkdir(parents=True, exist_ok=True)
    (FIGURES / "surface_bounds.svg").write_text("\n".join(parts) + "\n")


def ps_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def write_bar_eps(path: Path, labels: list[str], first: list[float], second: list[float],
                  first_label: str, second_label: str, annotations: list[str] | None = None) -> None:
    """Write a compact vector bar chart without third-party plotting packages."""
    width, height = 540, 285
    left, right, top, bottom = 52, 16, 32, 48
    plot_w, plot_h = width - left - right, height - top - bottom
    group_w = plot_w / len(labels)
    lines = [
        "%!PS-Adobe-3.0 EPSF-3.0", f"%%BoundingBox: 0 0 {width} {height}",
        "%%LanguageLevel: 2", "/Helvetica findfont 8 scalefont setfont",
        "1 1 1 setrgbcolor", f"0 0 {width} {height} rectfill",
    ]
    for tick in range(0, 11, 2):
        y = bottom + plot_h * tick / 10
        lines += ["0.86 0.89 0.93 setrgbcolor", "0.5 setlinewidth",
                  f"newpath {left} {y:.2f} moveto {left+plot_w} {y:.2f} lineto stroke",
                  "0.25 0.3 0.38 setrgbcolor", f"{left-6} {y-2:.2f} moveto ({tick*10}%) dup stringwidth pop neg 0 rmoveto show"]
    for i, (label, a, b) in enumerate(zip(labels, first, second)):
        cx = left + group_w * (i + 0.5)
        for offset, value, color in ((-9, a, "0.20 0.27 0.35"), (9, b, "0.78 0.82 0.88")):
            bar_h = max(0.0, min(1.0, value)) * plot_h
            lines += [f"{color} setrgbcolor", f"{cx+offset-7:.2f} {bottom:.2f} 14 {bar_h:.2f} rectfill"]
        lines += ["0.15 0.18 0.24 setrgbcolor", f"{cx:.2f} {bottom-15} moveto ({ps_escape(label)}) dup stringwidth pop -2 div 0 rmoveto show"]
        if annotations:
            lines += ["0.15 0.18 0.24 setrgbcolor", "/Helvetica findfont 7 scalefont setfont",
                      f"{cx:.2f} {bottom-28} moveto ({ps_escape(annotations[i])}) dup stringwidth pop -2 div 0 rmoveto show",
                      "/Helvetica findfont 8 scalefont setfont"]
    lines += [
        "0.20 0.27 0.35 setrgbcolor", f"{width-190} {height-18} 10 8 rectfill",
        f"{width-176} {height-16} moveto ({ps_escape(first_label)}) show",
        "0.78 0.82 0.88 setrgbcolor", f"{width-92} {height-18} 10 8 rectfill",
        "0.15 0.18 0.24 setrgbcolor", f"{width-78} {height-16} moveto ({ps_escape(second_label)}) show",
        "0.25 0.3 0.38 setrgbcolor", "0.8 setlinewidth",
        f"newpath {left} {bottom} moveto {left+plot_w} {bottom} lineto stroke",
        f"newpath {left} {bottom} moveto {left} {bottom+plot_h} lineto stroke",
        "showpage", "%%EOF",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n")


def write_eps_figures(bounds: list[dict], frontier: list[dict]) -> None:
    labels = [f'{row["gpu"]} {row["strike"]:g}' for row in bounds]
    write_bar_eps(
        FIGURES / "surface_bounds.eps", labels,
        [row["touch_price"] for row in bounds],
        [row["terminal_tail_upper_normalized"] for row in bounds],
        "one-touch", "terminal tail",
        [f'gap {row["crossing_reversal_lower_bound_normalized"]:.0%}' for row in bounds],
    )


def tex_escape(text: str) -> str:
    return (text.replace("\\", "\\textbackslash{}")
            .replace("%", "\\%").replace("$", "\\$")
            .replace("_", "\\_"))


def write_picture_chart(path: Path, labels: list[str], first: list[float], second: list[float],
                        first_label: str, second_label: str, annotations: list[str] | None,
                        width: int, height: int) -> None:
    """Write a dependency-free LaTeX picture chart."""
    left, right, top, bottom = (42, 8, 28, 42) if width > 300 else (30, 5, 25, 38)
    plot_w, plot_h = width - left - right, height - top - bottom
    group_w = plot_w / len(labels)
    bar_w = 11 if width > 300 else 7
    offset = 8 if width > 300 else 5
    font = "\\scriptsize" if width > 300 else "\\tiny"
    lines = ["% Generated by src/study.py; do not edit.",
             "\\begingroup", "\\setlength{\\unitlength}{1pt}",
             f"\\begin{{picture}}({width},{height})"]
    for tick in range(0, 11, 2):
        y = bottom + plot_h * tick / 10
        lines += [f"\\color{{gray!25}}\\put({left},{y:.2f}){{\\rule{{{plot_w}pt}}{{0.4pt}}}}",
                  f"\\color{{black!70}}\\put({left-5},{y-2:.2f}){{\\makebox(0,0)[r]{{{font} {tick*10}\\%}}}}"]
    for i, (label, a, b) in enumerate(zip(labels, first, second)):
        cx = left + group_w * (i + 0.5)
        for dx, value, color in ((-offset, a, "black!75"), (offset, b, "gray!45")):
            bar_h = max(0.0, min(1.0, value)) * plot_h
            lines.append(f"\\color{{{color}}}\\put({cx+dx-bar_w/2:.2f},{bottom}){{\\rule{{{bar_w}pt}}{{{bar_h:.2f}pt}}}}")
        lines.append(f"\\color{{black}}\\put({cx:.2f},{bottom-13}){{\\makebox(0,0){{{font} {tex_escape(label)}}}}}")
        if annotations:
            lines.append(f"\\put({cx:.2f},{bottom-25}){{\\makebox(0,0){{\\tiny {tex_escape(annotations[i])}}}}}")
    legend_x = max(left + 10, width - (175 if width > 300 else 150))
    lines += [
        f"\\color{{black!75}}\\put({legend_x},{height-15}){{\\rule{{9pt}}{{6pt}}}}",
        f"\\color{{black}}\\put({legend_x+13},{height-13}){{\\makebox(0,0)[l]{{\\tiny {tex_escape(first_label)}}}}}",
        f"\\color{{gray!45}}\\put({legend_x+(92 if width > 300 else 76)},{height-15}){{\\rule{{9pt}}{{6pt}}}}",
        f"\\color{{black}}\\put({legend_x+(105 if width > 300 else 89)},{height-13}){{\\makebox(0,0)[l]{{\\tiny {tex_escape(second_label)}}}}}",
        f"\\color{{black!60}}\\put({left},{bottom}){{\\rule{{{plot_w}pt}}{{0.7pt}}}}",
        f"\\put({left},{bottom}){{\\rule{{0.7pt}}{{{plot_h}pt}}}}",
        "\\end{picture}", "\\endgroup",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n")


def write_picture_figures(bounds: list[dict], frontier: list[dict]) -> None:
    write_picture_chart(
        GENERATED / "surface_bounds_picture.tex",
        [f'{row["gpu"]} {row["strike"]:g}' for row in bounds],
        [row["touch_price"] for row in bounds],
        [row["terminal_tail_upper_normalized"] for row in bounds],
        "one-touch", "terminal tail",
        [f'gap {row["crossing_reversal_lower_bound_normalized"]:.0%}' for row in bounds],
        490, 250,
    )
    rules = ("terminal", "mean5", "median7", "month_mean", "touch")
    lookup = {(row["rule"], row["interpretation"], row["epsilon_pct"]): row for row in frontier}
    write_picture_chart(
        GENERATED / "fragility_frontier_picture.tex",
        ["terminal", "mean-5", "median-7", "month", "touch"],
        [lookup[(rule, "false_positive", 5.0)]["event_weighted_vulnerable_share"] for rule in rules],
        [lookup[(rule, "false_negative", 5.0)]["event_weighted_vulnerable_share"] for rule in rules],
        "up / false +", "down / false -", None, 230, 185,
    )
    rules = ("terminal", "mean5", "median7", "month_mean", "touch")
    lookup = {(row["rule"], row["interpretation"], row["epsilon_pct"]): row for row in frontier}
    write_bar_eps(
        FIGURES / "fragility_frontier.eps",
        ["terminal", "mean-5", "median-7", "month avg", "one-touch"],
        [lookup[(rule, "false_positive", 5.0)]["event_weighted_vulnerable_share"] for rule in rules],
        [lookup[(rule, "false_negative", 5.0)]["event_weighted_vulnerable_share"] for rule in rules],
        "upward / false +", "downward / false -",
    )


def write_macros(audit: dict, bounds: list[dict], frontier: list[dict],
                  core_frontier: list[dict], actual_frontier: list[dict]) -> None:
    primary = [row["crossing_reversal_lower_bound_normalized"] for row in bounds]
    histories = [row["history"] for row in bounds]
    touch_false_positive_5 = next(row for row in frontier if row["rule"] == "touch"
                                  and row["interpretation"] == "false_positive" and row["epsilon_pct"] == 5.0)
    mean_false_positive_5 = next(row for row in frontier if row["rule"] == "month_mean"
                                 and row["interpretation"] == "false_positive" and row["epsilon_pct"] == 5.0)
    core_touch_5 = next(row for row in core_frontier if row["rule"] == "touch"
                        and row["interpretation"] == "false_positive" and row["epsilon_pct"] == 5.0)
    core_mean_5 = next(row for row in core_frontier if row["rule"] == "month_mean"
                       and row["interpretation"] == "false_positive" and row["epsilon_pct"] == 5.0)
    # Actual-rule subsets are composition-dependent descriptive summaries.
    actual_touch_fp_5 = next((row for row in actual_frontier
                              if row["rule"] == "touch"
                              and row["interpretation"] == "false_positive"
                              and row["epsilon_pct"] == 5.0), None)
    actual_touch_fn_5 = next((row for row in actual_frontier
                              if row["rule"] == "touch"
                              and row["interpretation"] == "false_negative"
                              and row["epsilon_pct"] == 5.0), None)
    actual_terminal_fp_5 = next((row for row in actual_frontier
                                 if row["rule"] == "terminal"
                                 and row["interpretation"] == "false_positive"
                                 and row["epsilon_pct"] == 5.0), None)
    actual_terminal_fn_5 = next((row for row in actual_frontier
                                 if row["rule"] == "terminal"
                                 and row["interpretation"] == "false_negative"
                                 and row["epsilon_pct"] == 5.0), None)
    pct = lambda value: (f"{value:.1%}".replace("%", "\\%") if value is not None else "---")
    all_lookup = {(row["rule"], row["interpretation"], row["epsilon_pct"]): row for row in frontier}
    actual_lookup = {
        (row["rule"], row["interpretation"], row["epsilon_pct"]): row
        for row in actual_frontier
    }
    lines = [
        "% Generated by src/study.py; do not edit.",
        f"\\newcommand{{\\NContracts}}{{{audit['n_strike_contracts']}}}",
        f"\\newcommand{{\\NNumericContracts}}{{{audit['numeric_checked']}}}",
        f"\\newcommand{{\\NEvents}}{{{audit['n_events']}}}",
        f"\\newcommand{{\\NBounds}}{{{len(bounds)}}}",
        f"\\newcommand{{\\MinBound}}{{{pct(min(primary))}}}",
        f"\\newcommand{{\\MaxBound}}{{{pct(max(primary))}}}",
        f"\\newcommand{{\\MedianBound}}{{{pct(stats.median(primary))}}}",
        f"\\newcommand{{\\MeanBound}}{{{pct(stats.mean(primary))}}}",
        f"\\newcommand{{\\MinHours}}{{{min(row['n_hours'] for row in histories)}}}",
        f"\\newcommand{{\\MaxHours}}{{{max(row['n_hours'] for row in histories)}}}",
        f"\\newcommand{{\\MinPositiveShare}}{{{pct(min(row['share_positive'] for row in histories))}}}",
        f"\\newcommand{{\\MinHistoricalBound}}{{{pct(min(row['minimum'] for row in histories))}}}",
        f"\\newcommand{{\\MinHistoricalMedian}}{{{pct(min(row['median'] for row in histories))}}}",
        f"\\newcommand{{\\MaxHistoricalMedian}}{{{pct(max(row['median'] for row in histories))}}}",
        # Actual-rule-subset sparse-print 5%% results.
        f"\\newcommand{{\\TouchFiveFPActual}}{{{pct(actual_touch_fp_5['event_weighted_vulnerable_share'] if actual_touch_fp_5 else None)}}}",
        f"\\newcommand{{\\TouchFiveFNActual}}{{{pct(actual_touch_fn_5['event_weighted_vulnerable_share'] if actual_touch_fn_5 else None)}}}",
        f"\\newcommand{{\\TerminalFiveFPActual}}{{{pct(actual_terminal_fp_5['event_weighted_vulnerable_share'] if actual_terminal_fp_5 else None)}}}",
        f"\\newcommand{{\\TerminalFiveFNActual}}{{{pct(actual_terminal_fn_5['event_weighted_vulnerable_share'] if actual_terminal_fn_5 else None)}}}",
        # All-rules (strike-selection contaminated) sensitivity numbers
        f"\\newcommand{{\\TouchFiveFPAll}}{{{pct(touch_false_positive_5['event_weighted_vulnerable_share'])}}}",
        f"\\newcommand{{\\TouchFiveFNAll}}{{{pct(all_lookup[('touch', 'false_negative', 5.0)]['event_weighted_vulnerable_share'])}}}",
        f"\\newcommand{{\\MeanFiveFPAll}}{{{pct(mean_false_positive_5['event_weighted_vulnerable_share'])}}}",
        f"\\newcommand{{\\MeanFiveFNAll}}{{{pct(all_lookup[('month_mean', 'false_negative', 5.0)]['event_weighted_vulnerable_share'])}}}",
        # Legacy macros (kept for backward compatibility with prior text)
        f"\\newcommand{{\\TouchFiveFP}}{{{pct(touch_false_positive_5['event_weighted_vulnerable_share'])}}}",
        f"\\newcommand{{\\MeanFiveFP}}{{{pct(mean_false_positive_5['event_weighted_vulnerable_share'])}}}",
        f"\\newcommand{{\\CoreTouchFiveFP}}{{{pct(core_touch_5['event_weighted_vulnerable_share'])}}}",
        f"\\newcommand{{\\CoreMeanFiveFP}}{{{pct(core_mean_5['event_weighted_vulnerable_share'])}}}",
    ]
    GENERATED.mkdir(parents=True, exist_ok=True)
    (GENERATED / "results_macros.tex").write_text("\n".join(lines) + "\n")

    surface_lines = [
        "% Generated by src/study.py; do not edit.",
        "\\begin{table*}[t]",
        "\\centering",
        "\\caption{Matched one-touch and terminal-tail prices on August 29, 2026. Prices are dollars per \\$1 payoff. ``Bound'' is the normalized lower bound from Equation~\\eqref{eq:lower}. History columns summarize the same bound over aligned hourly observations. B200 terminal tails are conservative upper bounds because the barrier lies inside the \\$7+ bucket.}",
        "\\label{tab:bounds}",
        "\\small",
        "\\begin{tabular}{lrrrrrrrr}",
        "\\toprule",
        "GPU & $K$ & Touch & Terminal tail & Bound & Hours & Hist. min & Hist. median & Positive \\\\",
        "\\midrule",
    ]
    for row in bounds:
        history = row["history"]
        surface_lines.append(
            f"{row['gpu']} & {row['strike']:.2f} & {row['touch_price']:.3f} & "
            f"{row['terminal_tail_upper_normalized']:.3f} & "
            f"{row['crossing_reversal_lower_bound_normalized']:.3f} & "
            f"{history['n_hours']} & {history['minimum']:.3f} & "
            f"{history['median']:.3f} & {pct(history['share_positive'])} \\\\"
        )
    surface_lines.extend(["\\bottomrule", "\\end{tabular}", "\\end{table*}"])
    (GENERATED / "surface_bounds_table.tex").write_text("\n".join(surface_lines) + "\n")

    labels = {
        "terminal": "Terminal",
        "mean5": "Mean, 5 days",
        "median7": "Median, 7 days",
        "month_mean": "Calendar-month mean",
        "touch": "One-touch maximum",
    }
    fragility_lines = [
        "% Generated by src/study.py; do not edit.",
        "\\begin{table}[t]",
        "\\centering",
        "\\caption{Event-weighted share of strike decisions vulnerable to one 5\\% print perturbation. The all-rules columns apply each rule counterfactually to the archived paths and strikes. The stated-rule columns retain only contracts whose listed rule matches the row; they are composition-dependent descriptive subsets.}",
        "\\label{tab:fragility}",
        "\\scriptsize",
        "\\setlength{\\tabcolsep}{2.5pt}",
        "\\begin{tabular}{lrrrr}",
        "\\toprule",
        "& \\multicolumn{2}{c}{All rules} & \\multicolumn{2}{c}{Stated-rule subset} \\\\",
        "\\cmidrule(lr){2-3}\\cmidrule(lr){4-5}",
        "Rule & Up / FP & Down / FN & Up / FP & Down / FN \\\\",
        "\\midrule",
    ]
    for rule in ("terminal", "mean5", "median7", "month_mean", "touch"):
        all_fp = all_lookup[(rule, "false_positive", 5.0)]["event_weighted_vulnerable_share"]
        all_fn = all_lookup[(rule, "false_negative", 5.0)]["event_weighted_vulnerable_share"]
        actual_fp_row = actual_lookup.get((rule, "false_positive", 5.0))
        actual_fn_row = actual_lookup.get((rule, "false_negative", 5.0))
        actual_fp = actual_fp_row["event_weighted_vulnerable_share"] if actual_fp_row else None
        actual_fn = actual_fn_row["event_weighted_vulnerable_share"] if actual_fn_row else None
        fragility_lines.append(
            f"{labels[rule]} & {pct(all_fp)} & {pct(all_fn)} & "
            f"{pct(actual_fp)} & {pct(actual_fn)} \\\\"
        )
    fragility_lines.extend(["\\bottomrule", "\\end{tabular}", "\\end{table}"])
    (GENERATED / "fragility_table.tex").write_text("\n".join(fragility_lines) + "\n")


def verify_frozen_manifest() -> None:
    manifest = load_json(DATA / "source_manifest.json")
    failures = []
    for entry in manifest["artifacts"]:
        artifact = entry["artifact"]
        actual = sha256(ROOT / artifact)
        if actual != entry["sha256"]:
            failures.append({"artifact": artifact, "expected": entry["sha256"], "actual": actual})
    for source in manifest["sources"]:
        required = {
            "source_id", "publisher", "upstream_uri", "retrieved_on",
            "source_record_locator", "source_fingerprint", "frozen_as",
            "raw_artifact_redistributed", "redistribution_status",
        }
        missing = sorted(required - source.keys())
        if missing:
            failures.append({"source_id": source.get("source_id"), "missing": missing})
        if source.get("raw_artifact_redistributed") is not False:
            failures.append({"source_id": source.get("source_id"), "raw_artifact_redistributed": True})
    if failures:
        raise RuntimeError(f"frozen input integrity failure: {failures}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUTPUT / "results.json")
    args = parser.parse_args()

    verify_frozen_manifest()
    path_doc = load_json(DATA / "index_paths.json")
    paths = {slug: [(row["date"], float(row["value"])) for row in rows]
             for slug, rows in path_doc["series"].items()}
    kalshi = load_json(DATA / "settlement_sample.json")
    poly = load_json(DATA / "market_surface_sample.json")

    contracts = collect_contracts(paths, kalshi)
    audit = audit_settlements(contracts)
    if audit["outcome_failures"] or audit["numeric_failures"]:
        raise RuntimeError(f"settlement reproduction gate failed: {audit}")
    radii = compute_radii(contracts, paths)
    frontier = event_weighted_frontier(radii)
    core_frontier = event_weighted_frontier(
        [row for row in radii if row["gpu"] not in ("a100-sxm4", "rtx-5090")])
    actual_frontier = event_weighted_frontier(
        [row for row in radii if row["rule"] == row["actual_rule"]])
    bounds, histories = matched_surface_bounds(poly)
    if len(bounds) != 5:
        raise RuntimeError(f"expected five unresolved matched high barriers, found {len(bounds)}")

    payload = {
        "vintage": "2026-08-29", "generated_by": "src/study.py",
        "definitions": {
            "price_bound": "one-touch YES price minus an upper bound on the normalized terminal-tail price",
            "robustness_radius": "minimum absolute one-print log perturbation that changes a binary payoff",
            "inference_unit": "GPU-event; strike-weighted results are descriptive only",
        },
        "settlement_audit": audit,
        "surface_bounds": bounds,
        "sparse_error_frontier": frontier,
        "sparse_error_frontier_core_gpus": core_frontier,
        "sparse_error_frontier_actual_rules_only": actual_frontier,
        "limitations": [
            "Archived Polymarket histories are prices, not executable bid/ask or depth histories.",
            "A price wedge is a state-price diagnostic, not an objective crossing probability.",
            "Sparse-error radii are deterministic sensitivity measures; they do not estimate actual benchmark error.",
            "Actual-rule subsets contain different events, strikes, moneyness distributions, and denominators; they are descriptive rather than paired rule comparisons.",
            "The 208 strikes represent 56 events and are not independent observations.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    write_csv(OUTPUT / "surface_bounds.csv", bounds,
              ["gpu", "strike", "touch_price", "terminal_tail_upper_raw", "terminal_bucket_sum",
               "terminal_tail_upper_normalized", "crossing_reversal_lower_bound_raw",
               "crossing_reversal_lower_bound_normalized", "terminal_tail_is_exact",
               "terminal_event_liquidity", "touch_event_liquidity"])
    write_csv(OUTPUT / "surface_history.csv", histories)
    write_csv(OUTPUT / "sparse_error_frontier.csv", frontier)
    write_csv(OUTPUT / "sparse_error_frontier_core_gpus.csv", core_frontier)
    write_csv(OUTPUT / "sparse_error_frontier_actual_rules.csv", actual_frontier)
    write_csv(OUTPUT / "robustness_radii.csv", radii)
    write_surface_svg(bounds)
    write_eps_figures(bounds, frontier)
    write_picture_figures(bounds, frontier)
    write_macros(audit, bounds, frontier, core_frontier, actual_frontier)
    print(json.dumps({"audit": audit, "surface_bounds": bounds}, indent=2))


if __name__ == "__main__":
    main()
