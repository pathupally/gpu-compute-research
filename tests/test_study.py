from __future__ import annotations

import importlib.util
import math
import re
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "src/study.py"
ROOT = MODULE_PATH.parents[1]
SPEC = importlib.util.spec_from_file_location("study", MODULE_PATH)
study = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(study)


class FunctionalTests(unittest.TestCase):
    def test_touch_dominates_terminal_pathwise(self):
        paths = (
            [("2026-01-01", 1.0), ("2026-01-02", 2.0), ("2026-01-03", 1.5)],
            [("2026-01-01", 2.0), ("2026-01-02", 1.0), ("2026-01-03", 0.5)],
            [("2026-01-01", 1.0), ("2026-01-02", 1.0), ("2026-01-03", 1.0)],
        )
        for rows in paths:
            for strike in (0.75, 1.0, 1.25, 1.75, 2.25):
                terminal = study.binary_outcome(study.functional(rows, "terminal", "2026-01-03"), strike)
                touch = study.binary_outcome(study.functional(rows, "touch", "2026-01-03"), strike)
                self.assertGreaterEqual(touch == "yes", terminal == "yes")

    def test_sparse_radii_have_expected_closed_form(self):
        rows = [("2026-01-01", 100.0), ("2026-01-02", 104.0), ("2026-01-03", 100.0)]
        terminal = study.sparse_radius(rows, "terminal", "2026-01-03", 105.0, +1)
        touch = study.sparse_radius(rows, "touch", "2026-01-03", 105.0, +1)
        self.assertAlmostEqual(terminal, math.log(105.0 / 100.0), places=10)
        self.assertAlmostEqual(touch, math.log(105.0 / 104.0), places=10)

    def test_multiple_crossings_make_touch_robust_to_one_downward_error(self):
        rows = [("2026-01-01", 106.0), ("2026-01-02", 107.0), ("2026-01-03", 100.0)]
        radius = study.sparse_radius(rows, "touch", "2026-01-03", 105.0, -1)
        self.assertTrue(math.isinf(radius))

    def test_mean_attenuates_one_print_error(self):
        rows = [("2026-01-01", 100.0), ("2026-01-02", 100.0)]
        radius = study.sparse_radius(rows, "month_mean", "2026-01-02", 105.0, +1)
        self.assertAlmostEqual(radius, math.log(110.0 / 100.0), places=10)

    def test_bucket_parser(self):
        self.assertEqual(study.parse_bucket("<$3.00"), (-math.inf, 3.0))
        self.assertEqual(study.parse_bucket("$3.00-$3.50"), (3.0, 3.5))
        self.assertEqual(study.parse_bucket("$7.00+"), (7.0, math.inf))

    def test_event_weighting_is_not_strike_weighting(self):
        rows = [
            {"rule": "terminal", "direction": "up", "base_outcome": "no",
             "event": "one-strike", "radius_pct": 1.0},
            {"rule": "terminal", "direction": "up", "base_outcome": "no",
             "event": "three-strikes", "radius_pct": 10.0},
            {"rule": "terminal", "direction": "up", "base_outcome": "no",
             "event": "three-strikes", "radius_pct": 10.0},
            {"rule": "terminal", "direction": "up", "base_outcome": "no",
             "event": "three-strikes", "radius_pct": 10.0},
        ]
        row = next(item for item in study.event_weighted_frontier(rows)
                   if item["rule"] == "terminal"
                   and item["interpretation"] == "false_positive"
                   and item["epsilon_pct"] == 5.0)
        self.assertEqual(row["event_weighted_vulnerable_share"], 0.5)
        self.assertEqual(row["strike_weighted_vulnerable_share"], 0.25)


class FrozenSampleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        study.verify_frozen_manifest()
        path_doc = study.load_json(study.DATA / "index_paths.json")
        cls.paths = {slug: [(row["date"], float(row["value"])) for row in rows]
                     for slug, rows in path_doc["series"].items()}
        cls.kalshi = study.load_json(study.DATA / "settlement_sample.json")
        cls.poly = study.load_json(study.DATA / "market_surface_sample.json")

    def test_frozen_shape(self):
        self.assertEqual(set(self.paths), {"a100-sxm4", "b200", "h100-sxm", "h200", "rtx-5090"})
        self.assertTrue(all(len(rows) == 92 for rows in self.paths.values()))

    def test_settlement_gate(self):
        contracts = study.collect_contracts(self.paths, self.kalshi)
        audit = study.audit_settlements(contracts)
        self.assertEqual(audit["n_strike_contracts"], 208)
        self.assertEqual(audit["n_events"], 56)
        self.assertEqual(audit["numeric_checked"], 187)
        self.assertEqual(audit["outcome_failures"], [])
        self.assertEqual(audit["numeric_failures"], [])

    def test_frozen_records_contain_only_consumed_fields(self):
        for series in self.kalshi["series"].values():
            for market in series["markets"]:
                self.assertEqual(set(market), {"ticker", "event_ticker", "open_time"})
            for settlement in series["settlements"]:
                self.assertEqual(
                    set(settlement),
                    {"ticker", "close_time", "floor_strike", "result", "settled_value"},
                )
        for event in self.poly["events"]:
            self.assertEqual(set(event), {"title", "liquidity", "markets"})
            for market in event["markets"]:
                self.assertEqual(set(market), {"group_item_title", "yes_price", "yes_history"})
                self.assertTrue(all(set(point) == {"t", "p"} for point in market["yes_history"]))

    def test_five_unresolved_high_barrier_bounds(self):
        bounds, histories = study.matched_surface_bounds(self.poly)
        self.assertEqual(len(bounds), 5)
        self.assertTrue(all(row["crossing_reversal_lower_bound_normalized"] > 0 for row in bounds))
        self.assertTrue(all(row["history"]["n_hours"] > 700 for row in bounds))
        self.assertGreater(len(histories), 3500)

    def test_source_manifest_has_public_provenance_boundary(self):
        manifest = study.load_json(study.DATA / "source_manifest.json")
        self.assertEqual(manifest["discovery_sample_cutoff"], "2026-08-30")
        self.assertEqual(len(manifest["artifacts"]), 3)
        self.assertEqual(len(manifest["sources"]), 23)
        for source in manifest["sources"]:
            self.assertFalse(source["raw_artifact_redistributed"])
            self.assertIn("upstream_uri", source)
            self.assertIn("source_record_locator", source)
            self.assertRegex(source["source_fingerprint"], r"^[0-9a-f]{64}$")
            self.assertNotIn("/Users/", str(source))

    def test_manuscript_uses_generated_empirical_tables(self):
        manuscript = (ROOT / "paper/manuscript.tex").read_text()
        lowered = manuscript.lower()
        self.assertIn(r"\input{paper/generated/surface_bounds_table.tex}", manuscript)
        self.assertIn(r"\input{paper/generated/fragility_table.tex}", manuscript)
        self.assertNotIn("apples-to-apples", lowered)
        self.assertNotIn("holds moneyness fixed", lowered)
        self.assertIsNone(re.search(r"(?:49\.4|3\.1)\\%", manuscript))

    def test_generated_fragility_values_match_analysis(self):
        contracts = study.collect_contracts(self.paths, self.kalshi)
        radii = study.compute_radii(contracts, self.paths)
        actual = study.event_weighted_frontier(
            [row for row in radii if row["rule"] == row["actual_rule"]]
        )
        lookup = {(row["rule"], row["interpretation"], row["epsilon_pct"]): row
                  for row in actual}
        expected = {
            f"{100 * lookup[('touch', 'false_negative', 5.0)]['event_weighted_vulnerable_share']:.1f}\\%",
            f"{100 * lookup[('terminal', 'false_negative', 5.0)]['event_weighted_vulnerable_share']:.1f}\\%",
        }
        table = (ROOT / "paper/generated/fragility_table.tex").read_text()
        self.assertEqual(expected, {"54.3\\%", "6.2\\%"})
        self.assertTrue(expected.issubset(set(re.findall(r"[0-9]+\.[0-9]+\\%", table))))


if __name__ == "__main__":
    unittest.main()
