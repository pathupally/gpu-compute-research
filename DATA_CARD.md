# Data card

## Research question

How do terminal and first-passage settlement rules transform the same published
GPU rental index into different contingent claims, and how sensitive are those
claims to a sparse perturbation of one benchmark print?

## Discovery vintage and integrity

The discovery sample was frozen on 2026-08-30 from observations retrieved no
later than 2026-08-29. `data/source_manifest.json` records upstream URIs,
retrieval dates, record locators, provenance fingerprints, redistribution
status, and SHA-256 hashes for the three normalized analysis artifacts. The
analysis verifies the artifact hashes before calculation.

Source fingerprints identify source captures retained outside this public
package. Because those captures are not redistributed, the fingerprints are
provenance locators rather than independently verifiable integrity checks.

## Normalized inputs

### Ornn index paths

- Five GPU series: A100 SXM4, B200, H100 SXM, H200, and RTX 5090.
- 92 daily levels per GPU from 2026-05-30 through 2026-08-29.
- Used to reconstruct archived settlements and deterministic counterfactual
  settlement functions.

### Kalshi compute event contracts

- 17 series families: weekly, monthly, quarterly, and MAX contracts.
- Only ticker, event ticker, open/close time, strike, result, and numeric settled
  value fields consumed by the analysis are retained.
- 208 eligible settled strike decisions map to 56 unique GPU-event windows;
  strike count is not treated as an independent sample size.

### Polymarket matched payoff surfaces

- Six December 31, 2026 events: terminal buckets and one-touch thresholds for
  B200, H100, and H200.
- Only event title/liquidity and market label/YES price/YES history are retained.
- Five unresolved high barriers have matched terminal-tail bounds and 742--743
  aligned hourly observations each.

## Known limitations

- Price histories lack executable bids, asks, sizes, and depth. The paper does
  not claim executable arbitrage or an implementable strategy.
- Terminal buckets and touch markets have different liquidity pools. A shared
  pricing kernel is an interpretation, not an observed fact.
- A normalized terminal distribution divides bucket prices by their sum; raw
  bounds are also reported.
- B200 thresholds at $7.50 and $8.00 fall within the terminal market's open-ended
  `$7.00+` bin, so its full price is a conservative upper bound.
- Sparse-error radii are deterministic robustness measures. They are neither
  market state prices nor objective measurement-error probabilities.
- Later-retrieved history may differ from the vintage visible at settlement.
  Exact reproduction validates the archived record pair, not absence of
  upstream revision.
- Actual-rule subsets differ in events, strikes, moneyness, and denominators.
  They are composition-dependent descriptions, not causal comparisons.

## Prospective protocol

No prospective result is reported in this release. The predeclared holdout may
use only events and observations first published after 2026-08-30. It preserves
event weighting, verifies settlement records before inference, freezes each new
vintage before analysis, and labels non-executable price histories as market
state-price diagnostics rather than arbitrage evidence.

## Access and ethics

The package does not redistribute full API responses, copied rules, vendor
articles, or the Silicon Data forward endpoint. It does not identify traders or
infer manipulation by any named venue or benchmark administrator. Upstream
ownership and access terms remain controlling; see `DATA_NOTICE.md`.
