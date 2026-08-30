#!/usr/bin/env python3
"""Freeze the minimal source vintage used by the paper.

This command is intentionally separate from the analysis.  Reproduction reads
only the committed files under ``novelty/data``; it never fetches live data and
never silently adopts a newer parent-repository snapshot.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve()
NOVELTY = HERE.parents[1]
PARENT = NOVELTY.parent
OUT = NOVELTY / "data"

ORNN = {
    "a100-sxm4": PARENT / "data/snapshots/ornn/a100-sxm4/2026-08-29.json",
    "b200": PARENT / "data/snapshots/ornn/b200/2026-08-29.json",
    "h100-sxm": PARENT / "data/snapshots/ornn/h100-sxm/2026-08-29.json",
    "h200": PARENT / "data/snapshots/ornn/h200/2026-08-29.json",
    "rtx-5090": PARENT / "data/snapshots/ornn/rtx-5090/2026-08-29.json",
}

KALSHI_SERIES = (
    "KXA100W", "KXB200W", "KXH100W", "KXH200W", "KXRTX5090W",
    "KXB200MON", "KXH100MON", "KXH200MON", "KXRTX5090MON",
    "KXA100MAX", "KXB200MAX", "KXH100MAX", "KXH200MAX", "KXRTX5090MAX",
    "KXB200Q", "KXH100Q", "KXH200Q",
)

POLYMARKET_TITLES = {
    f"GPU rental prices ({gpu}) {kind}"
    for gpu in ("B200", "H100", "H200")
    for kind in ("end of 2026?", "hit___ in 2026?")
}

MARKET_FIELDS = (
    "ticker", "event_ticker", "open_time", "close_time",
    "expected_expiration_time", "expiration_time", "occurrence_datetime",
    "status", "result", "floor_strike", "cap_strike", "strike_type",
    "rules_primary", "rules_secondary", "settlement_ts",
    "expiration_value", "settlement_value_dollars", "can_close_early",
    "yes_bid_dollars", "yes_ask_dollars", "no_bid_dollars", "no_ask_dollars",
    "yes_bid_size_fp", "yes_ask_size_fp", "open_interest_fp", "volume_fp",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n")


def freeze_ornn(manifest: list[dict]) -> None:
    payload = {"as_of": "2026-08-29", "series": {}}
    for slug, path in ORNN.items():
        rows = json.loads(path.read_text())
        payload["series"][slug] = [
            {"date": str(row["timestamp"])[:10], "value": float(row["index_value"])}
            for row in rows
        ]
        manifest.append({"frozen_as": "data/index_paths.json", "source": str(path.relative_to(PARENT)),
                         "sha256": sha256(path)})
    dump(OUT / "index_paths.json", payload)


def freeze_kalshi(manifest: list[dict]) -> None:
    payload = {"as_of": "2026-08-29", "series": {}}
    for ticker in KALSHI_SERIES:
        path = PARENT / f"data/snapshots/kalshi/{ticker}/2026-08-29.json"
        doc = json.loads(path.read_text())
        payload["series"][ticker] = {
            "series_ticker": ticker,
            "markets": [
                {key: market.get(key) for key in MARKET_FIELDS if key in market}
                for market in doc.get("markets", [])
            ],
            "settlements": doc.get("settlements", []),
        }
        manifest.append({"frozen_as": "data/settlement_sample.json", "source": str(path.relative_to(PARENT)),
                         "sha256": sha256(path)})
    dump(OUT / "settlement_sample.json", payload)


def choose_yes_series(series_group: list[dict], yes_price: float) -> dict:
    """Choose the YES token history from a paired YES/NO token group."""
    populated = [row for row in series_group if row.get("history")]
    if not populated:
        return series_group[0]
    return min(populated, key=lambda row: abs(float(row["history"][-1]["p"]) - yes_price))


def freeze_polymarket(manifest: list[dict]) -> None:
    path = PARENT / "data/snapshots/polymarket/2026-08-29.json"
    doc = json.loads(path.read_text())
    events = []
    for event in doc["events"]:
        if event.get("title") not in POLYMARKET_TITLES:
            continue
        groups: dict[str, list[dict]] = {}
        for row in event.get("series", []):
            groups.setdefault(row["market_slug"], []).append(row)
        markets = []
        for slug, rows in groups.items():
            exemplar = rows[0]
            outcomes = json.loads(exemplar["outcomes"])
            prices = [float(x) for x in json.loads(exemplar["outcome_prices"])]
            if outcomes[0].lower() != "yes":
                raise ValueError(f"unexpected outcome order for {slug}: {outcomes}")
            yes_series = choose_yes_series(rows, prices[0])
            markets.append({
                "group_item_title": exemplar["group_item_title"],
                "market_slug": slug,
                "question": exemplar["question"],
                "yes_price": prices[0],
                "no_price": prices[1],
                "yes_history": [
                    {"t": int(point["t"]), "p": float(point["p"])}
                    for point in yes_series.get("history", [])
                ],
            })
        events.append({
            "title": event["title"], "slug": event.get("slug"),
            "start_date": event.get("start_date"), "end_date": event.get("end_date"),
            "closed": event.get("closed"), "liquidity": event.get("liquidity"),
            "volume": event.get("volume"), "markets": markets,
        })
    if {event["title"] for event in events} != POLYMARKET_TITLES:
        missing = sorted(POLYMARKET_TITLES - {event["title"] for event in events})
        raise ValueError(f"missing Polymarket events: {missing}")
    dump(OUT / "market_surface_sample.json", {"fetched_at": doc.get("fetched_at"), "events": events})
    manifest.append({"frozen_as": "data/market_surface_sample.json", "source": str(path.relative_to(PARENT)),
                     "sha256": sha256(path)})


def main() -> None:
    manifest: list[dict] = []
    freeze_ornn(manifest)
    freeze_kalshi(manifest)
    freeze_polymarket(manifest)
    for target in ("index_paths.json", "settlement_sample.json", "market_surface_sample.json"):
        path = OUT / target
        manifest.append({"artifact": f"data/{target}", "sha256": sha256(path)})
    dump(OUT / "source_manifest.json", {
        "frozen_at": "2026-08-30",
        "policy": "Analysis reads frozen artifacts only; live sources are never fetched by make all.",
        "entries": manifest,
    })
    print(f"froze {len(manifest)} source and artifact hashes under {OUT.relative_to(PARENT)}")


if __name__ == "__main__":
    main()
