# The Benchmark Is Part of the Option

This directory is a self-contained research package for a paper on first-passage
payoffs and benchmark robustness in nascent compute derivatives. It freezes one
data vintage, reproduces every eligible archived settlement, derives model-free
terminal-versus-touch price bounds, and computes deterministic one-print
robustness frontiers.

The headline empirical objects are:

- 208 settled strike decisions representing 56 GPU-events, all reproduced under
  their stated terminal or running-maximum rules;
- five unresolved, matched December 31 terminal/touch surfaces on Polymarket;
- 742-743 common hourly observations per surface;
- a sparse-error experiment that weights each event equally rather than treating
  ladder strikes as independent observations.

The package does **not** estimate an objective probability of benchmark error,
claim that manipulation occurred, or call archived prediction-market prices
arbitrage opportunities. The price histories lack executable bid/ask and depth.

## Reproduce

From the parent repository:

```sh
make -C novelty all
```

`make all` is hermetic: it reads only committed files in `novelty/data/` and
does not fetch live data. To audit the code without compiling the manuscript:

```sh
make -C novelty verify
```

Key outputs:

- `output/pdf/the-benchmark-is-part-of-the-option.pdf` - final manuscript
- `outputs/results.json` - machine-readable results
- `outputs/surface_bounds.csv` - matched price-surface bounds
- `outputs/sparse_error_frontier.csv` - event-weighted sensitivity curves
- `DATA_CARD.md` - provenance, coverage, and limitations
- `literature/RESEARCH_LOG.md` - scoped literature and novelty audit

`make refreeze` is deliberately opt-in. It reads the parent repository's current
snapshots and changes the committed research vintage; it should be used only to
start a declared replication or holdout study.
