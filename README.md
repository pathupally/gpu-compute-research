# The Benchmark Is Part of the Option

[![reproducibility](https://github.com/pathupally/gpu-compute-research/actions/workflows/ci.yml/badge.svg)](https://github.com/pathupally/gpu-compute-research/actions/workflows/ci.yml)

**Compute derivatives arrived before their cash benchmark had a public price
history.** That ordering makes the settlement functional — terminal print,
running maximum, or average — a first-order term in the contract rather than a
back-office detail. This repository measures how much it matters, on public
event contracts written against transaction-based GPU rental indices.

Three results, each reproduced from frozen records by `make all`:

### 1. Settlement rules are recoverable from prints alone

A specification-aware program reproduces **208/208 archived binary settlements**
across **56 GPU-events**, and **187/187 numeric settlement values**, with zero
failures. Recovering the rule shows that 29 of the 208 contracts settle on a
**running maximum**, not the terminal print their category name implies.

### 2. A model-free lower bound on the crossing-then-reversing state price

![Matched one-touch and terminal-tail prices across five thresholds; the gap is
the lower bound on the state price of crossing the barrier and later ending
below it.](paper/figures/surface_bounds.svg)

Matched December 31 terminal buckets and one-touch thresholds on the same venue
price the same underlying path. Pathwise payoff dominance means the one-touch
price minus an upper bound on the terminal-tail price lower-bounds the state
price of crossing a barrier and subsequently ending below it. No model, no
volatility parameter, no distributional assumption.

| GPU | Strike | One-touch | Terminal-tail upper | Lower bound |
| --- | ---: | ---: | ---: | ---: |
| H100 | $3.50 | 0.630 | 0.172 | **45.8%** |
| H200 | $6.00 | 0.600 | 0.144 | **45.6%** |
| B200 | $7.50 | 0.510 | 0.085 | **42.4%** |
| B200 | $8.00 | 0.475 | 0.085 | **39.0%** |
| H200 | $7.00 | 0.417 | 0.038 | **37.9%** |

The bound stays strictly positive in **every one of at least 742 aligned hourly
observations** per surface — it is not an artifact of the frozen timestamp.

### 3. One-touch settlement is ~6x more single-print fragile than averaging

A directional sparse-print robustness radius is the smallest perturbation to
**one** published index observation that flips a binary payoff. Event-weighted,
so strike ladders cannot masquerade as independent events:

| Settlement rule | 5% up-print flips | 5% down-print flips |
| --- | ---: | ---: |
| One-touch | **82.4%** | 11.1% |
| Monthly average | **13.2%** | 6.7% |

This is a deterministic susceptibility measure, not an estimate of actual
benchmark error, executable arbitrage, or manipulation. It is the argument for
publication-vintage controls, averaging, and explicit path-functional
disclosure in compute contract design.

## The paper

**[the-benchmark-is-part-of-the-option.pdf](outputs/pdf/the-benchmark-is-part-of-the-option.pdf)**
— 7 pages. Rebuilt from `paper/manuscript.tex` by `make all`. Every percentage
above and both manuscript tables are emitted by `src/study.py` into
`paper/generated/`; none are typed in by hand, and CI fails if a regenerated
number differs by a byte.

JEL: G13, G14, G18, L86.

## Reproduce offline

Requires Python 3.11+ and a LaTeX installation with `pdflatex`. No third-party
packages, no network access at any point.

```sh
make all
```

`make all` reads only the normalized, frozen records in `data/`, verifying
their SHA-256 hashes before analysis begins. To run the settlement, provenance,
weighting, and manuscript tests without compiling the PDF:

```sh
make verify
```

Generated artifacts:

- `outputs/pdf/the-benchmark-is-part-of-the-option.pdf`
- `outputs/results.json`, `outputs/surface_bounds.csv`
- `outputs/sparse_error_frontier.csv` (plus `_actual_rules`, `_core_gpus`)
- `paper/generated/*.tex` — tables, figures, and every reported macro

`make refreeze` is deliberately excluded from the reproducible public path. It
is for an authorized maintainer who supplies separate source captures and wants
to declare a new research vintage.

## What this does not claim

The settlement audit and the pathwise payoff-dominance bound are the primary
findings. The sparse-rule comparison is a deterministic sensitivity analysis:
it does not estimate objective error probabilities, executable arbitrage, or a
causal effect of changing settlement rules. Stated-rule subsets contain
different events, strikes, and denominators, and are reported only as
composition-dependent descriptions.

The discovery vintage ends on **2026-08-30**. No prospective result is
reported; the predeclared holdout begins only with events settling after that
date.

## Scope and data boundary

This repository contains minimal normalized research records, identifiers,
timestamps, locators, and provenance fingerprints. It excludes raw API
responses, full market objects, copied rules, portal captures, and vendor
articles. See [DATA_NOTICE.md](DATA_NOTICE.md) and [DATA_CARD.md](DATA_CARD.md).

Related: [gpu-benchmark-ledger](https://github.com/pathupally/gpu-benchmark-ledger)
— comparability and vintage control across two published GPU price benchmarks
([live dashboard](https://pathupally.github.io/gpu-benchmark-ledger/)).

## Citation and license

Code is MIT licensed. Upstream data and source materials remain the property of
their publishers and are not licensed under MIT. Citation metadata is in
`CITATION.cff`.

Author: Adrian Mathew, Purdue University · `mathe147@purdue.edu`
