# Data card

## Research question

How do terminal and first-passage settlement rules transform the same published
GPU rental index into different contingent claims, and how sensitive are those
claims to a sparse perturbation of one benchmark print?

## Frozen vintage

All empirical inputs were frozen on 2026-08-30 from parent-repository snapshots
labeled or fetched on 2026-08-29. `data/source_manifest.json` records the SHA-256
of every parent source and every frozen artifact. The analysis verifies the
frozen-artifact hashes before doing any calculation.

The root repository had mixed-vintage derived outputs and a failing old
manifest when this study began. None of those derived outputs is used here.
This package recalculates its results from its own frozen inputs.

## Inputs

### Ornn index paths

- Five GPU series: A100 SXM4, B200, H100 SXM, H200, RTX 5090.
- 92 daily levels per GPU from 2026-05-30 through 2026-08-29.
- Used only to reconstruct archived settlements and deterministic
  counterfactual settlement functionals.

### Kalshi compute event contracts

- 17 series families: weekly, monthly, quarterly, and MAX contracts.
- 208 eligible settled strike decisions in the observable index window.
- Those strikes map to 56 unique GPU-event windows; the strike count is not an
  independent sample size.
- Current/final contract metadata, stated rules, results, and settlement values.

### Polymarket matched payoff surfaces

- Six December 31, 2026 events: terminal buckets and one-touch thresholds for
  B200, H100, and H200.
- YES-token price histories and event metadata.
- Five active high barriers have matched terminal-tail bounds and 742-743 common
  hourly observations each.

## Known limitations

- Polymarket histories contain prices and timestamps, not historical executable
  bids, asks, sizes, or depth. No arbitrage or implementable strategy is claimed.
- Terminal buckets and touch markets have different liquidity pools. Equality of
  pricing kernels is an interpretation, not an observed fact.
- A normalized terminal distribution divides bucket prices by their sum. Raw
  bounds are reported alongside normalized bounds.
- The B200 $7.50 and $8.00 thresholds lie within the terminal market's open-ended
  `$7.00+` bin. Its full price is therefore a conservative upper bound on each
  terminal tail, not an exact tail price.
- Sparse-error radii are deterministic robustness measures. Observed daily index
  volatility is never relabeled as measurement-error volatility.
- Later-retrieved history may differ from the exact vintage visible when a
  contract originally settled. Exact reproduction therefore validates the
  archived record pair, not the absence of upstream revision.
- The discovery sample ends on 2026-08-29. Prospective validation must use events
  and observations first published after 2026-08-30.

## Ethical and access notes

The package uses public event-contract metadata and a frozen subset of already
archived index data. It does not increase vendor polling, redistribute the
Silicon Data forward endpoint, identify traders, or infer manipulation by any
named venue or benchmark administrator.
