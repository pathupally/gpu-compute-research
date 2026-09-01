#!/usr/bin/env python3
"""Freeze the minimal source vintage used by the paper.

This command is intentionally separate from the analysis. Reproduction reads
only the committed files under ``data``; it never fetches live data or silently
adopts a newer source capture. Refreezing requires an explicit authorized
source-capture directory.
"""

from __future__ import annotations

import hashlib
import json
import argparse
from pathlib import Path


HERE = Path(__file__).resolve()
NOVELTY = HERE.parents[1]
OUT = NOVELTY / "data"
ORNN_SLUGS = ("a100-sxm4", "b200", "h100-sxm", "h200", "rtx-5090")

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

MARKET_FIELDS = ("ticker", "event_ticker", "open_time")
SETTLEMENT_FIELDS = (
    "ticker", "close_time", "floor_strike", "result", "settled_value",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n")


def source_entry(source_id: str, publisher: str, upstream_uri: str,
                 source_record_locator: str, frozen_as: str, fingerprint: str) -> dict:
    return {
        "source_id": source_id,
        "publisher": publisher,
        "upstream_uri": upstream_uri,
        "retrieved_on": "2026-08-29",
        "source_record_locator": source_record_locator,
        "source_fingerprint": fingerprint,
        "frozen_as": frozen_as,
        "raw_artifact_redistributed": False,
        "redistribution_status": "minimal_normalized_research_records_only",
        "upstream_rights": "retained_by_publisher",
    }


def freeze_ornn(manifest: list[dict], source_root: Path) -> None:
    payload = {"as_of": "2026-08-29", "series": {}}
    for slug in ORNN_SLUGS:
        path = source_root / f"ornn/{slug}/2026-08-29.json"
        rows = json.loads(path.read_text())
        payload["series"][slug] = [
            {"date": str(row["timestamp"])[:10], "value": float(row["index_value"])}
            for row in rows
        ]
        title = slug.replace("-", " ").upper()
        manifest.append(source_entry(
            f"ornn-{slug}-2026-08-29",
            "Ornn",
            f"https://api.ornnai.com/api/gpu/{title.replace(' ', '%20')}/index-history",
            "92 daily index observations ending 2026-08-29",
            "data/index_paths.json",
            sha256(path),
        ))
    dump(OUT / "index_paths.json", payload)


def freeze_kalshi(manifest: list[dict], source_root: Path) -> None:
    payload = {"as_of": "2026-08-29", "series": {}}
    for ticker in KALSHI_SERIES:
        path = source_root / f"kalshi/{ticker}/2026-08-29.json"
        doc = json.loads(path.read_text())
        payload["series"][ticker] = {
            "series_ticker": ticker,
            "markets": [
                {key: market.get(key) for key in MARKET_FIELDS if key in market}
                for market in doc.get("markets", [])
            ],
            "settlements": [
                {key: settlement.get(key) for key in SETTLEMENT_FIELDS}
                for settlement in doc.get("settlements", [])
            ],
        }
        manifest.append(source_entry(
            f"kalshi-{ticker}-2026-08-29",
            "Kalshi",
            f"https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker={ticker}",
            f"series_ticker={ticker}",
            "data/settlement_sample.json",
            sha256(path),
        ))
    dump(OUT / "settlement_sample.json", payload)


def choose_yes_series(series_group: list[dict], yes_price: float) -> dict:
    """Choose the YES token history from a paired YES/NO token group."""
    populated = [row for row in series_group if row.get("history")]
    if not populated:
        return series_group[0]
    return min(populated, key=lambda row: abs(float(row["history"][-1]["p"]) - yes_price))


def freeze_polymarket(manifest: list[dict], source_root: Path) -> None:
    path = source_root / "polymarket/2026-08-29.json"
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
                "yes_price": prices[0],
                "yes_history": [
                    {"t": int(point["t"]), "p": float(point["p"])}
                    for point in yes_series.get("history", [])
                ],
            })
        events.append({
            "title": event["title"], "liquidity": event.get("liquidity"),
            "markets": markets,
        })
    if {event["title"] for event in events} != POLYMARKET_TITLES:
        missing = sorted(POLYMARKET_TITLES - {event["title"] for event in events})
        raise ValueError(f"missing Polymarket events: {missing}")
    dump(OUT / "market_surface_sample.json", {"fetched_at": doc.get("fetched_at"), "events": events})
    manifest.append(source_entry(
        "polymarket-compute-surfaces-2026-08-29",
        "Polymarket",
        "https://gamma-api.polymarket.com/events",
        "six B200/H100/H200 terminal and touch events plus hourly YES histories",
        "data/market_surface_sample.json",
        sha256(path),
    ))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source-root", type=Path, required=True,
        help="authorized capture directory containing ornn/, kalshi/, and polymarket/",
    )
    args = parser.parse_args()
    source_root = args.source_root.resolve()
    manifest: list[dict] = []
    freeze_ornn(manifest, source_root)
    freeze_kalshi(manifest, source_root)
    freeze_polymarket(manifest, source_root)
    artifacts = []
    for target in ("index_paths.json", "settlement_sample.json", "market_surface_sample.json"):
        path = OUT / target
        artifacts.append({"artifact": f"data/{target}", "sha256": sha256(path)})
    dump(OUT / "source_manifest.json", {
        "schema_version": "1.0.0",
        "frozen_at": "2026-08-30",
        "discovery_sample_cutoff": "2026-08-30",
        "policy": "Analysis reads frozen artifacts only; live sources are never fetched by make all.",
        "sources": manifest,
        "artifacts": artifacts,
    })
    print(f"froze {len(manifest)} sources and {len(artifacts)} artifacts under {OUT}")


if __name__ == "__main__":
    main()
