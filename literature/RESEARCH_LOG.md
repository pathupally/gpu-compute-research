# Literature and novelty audit

## Search procedure

The review combined the repository's stored paper corpus with current primary
sources from publishers, arXiv, regulators, exchanges, benchmark administrators,
and venue rule pages. Four semantic searches were attempted against Firecrawl's
research index on 2026-08-30; the endpoint failed DNS resolution in the execution
environment. The fallback review used direct primary-source search and manual
in-body verification of load-bearing claims.

The novelty claim is intentionally narrow: this is the first documented matched
terminal/one-touch surface and sparse-print robustness audit for public compute
index derivatives that we found. It is not the first work on benchmark design,
cash-settlement manipulation, prediction markets, barrier options, or compute
asset pricing.

## Closest compute research

- Bandi and Su, **(Early) AI Compute Asset Pricing** (2026),
  [arXiv:2607.12156](https://arxiv.org/abs/2607.12156). Establishes compute's
  non-storability, term-rental synthetic forwards, and early risk-premium
  questions. It does not study first-passage event contracts or sparse benchmark
  perturbations.
- Fernandez-Fuertes and Gregoire, **Compute Futures: Who Is Left Exposed?**
  (2026), [SSRN 7224223](https://doi.org/10.2139/ssrn.7224223). Studies basis and
  hedging mismatch across heterogeneous compute exposure.
- Byrne, Corrado, and Sichel, **The Rise of Cloud Computing: Minding Your P's,
  Q's and K's** (2018), [NBER 25188](https://www.nber.org/papers/w25188).
  Constructs quality-adjusted cloud-computing price indexes.
- Li et al., **Spot Pricing in the Cloud Ecosystem** (2017),
  [arXiv:1708.01401](https://arxiv.org/abs/1708.01401). Reviews 61 primary studies
  on provider spot pricing; this literature concerns resource allocation and
  posted cloud prices rather than cash-settled GPU-index options.

## Benchmark and settlement design

- Duffie and Dworczak, **Robust Benchmark Design**, *Journal of Financial
  Economics* 142(2), 775-802 (2021),
  [DOI 10.1016/j.jfineco.2021.06.024](https://doi.org/10.1016/j.jfineco.2021.06.024).
  Designs benchmark fixings when contributors have manipulation incentives.
- Pirrong, **Manipulation of Cash-Settled Futures Contracts**, *Journal of
  Business* 74(2), 221-244 (2001),
  [DOI 10.1086/209671](https://doi.org/10.1086/209671).
- Shiller, **Measuring Asset Values for Cash Settlement in Derivative Markets**,
  *Journal of Finance* 48(3), 911-931 (1993),
  [NBER t0131](https://www.nber.org/papers/t0131).
- IOSCO, **Principles for Financial Benchmarks** (2013),
  [final report](https://www.iosco.org/library/pubdocs/pdf/IOSCOPD415.pdf).
- Zhang, **Competition and Manipulation in Derivative Contract Markets**,
  *Journal of Financial Economics* 144(2), 396-413 (2022).

## Path-dependent derivatives and prediction markets

- Broadie, Glasserman, and Kou, **A Continuity Correction for Discrete Barrier
  Options**, *Mathematical Finance* 7(4), 325-349 (1997),
  [DOI 10.1111/1467-9965.00035](https://doi.org/10.1111/1467-9965.00035).
- Dai, Jia, and Yu, **Settlement Manipulation in Prediction Markets** (2026),
  [arXiv:2606.31675](https://arxiv.org/abs/2606.31675). Shows manipulation around
  short-horizon crypto event-contract settlement. The present paper does not
  test manipulation; it studies payoff dominance and deterministic susceptibility
  in a thin published index.
- Wolfers and Zitzewitz, **Prediction Markets**, *Journal of Economic
  Perspectives* 18(2), 107-126 (2004).

## Institutional sources

- CFTC, **Request for Comment on the Listing of Compute Derivatives Contracts**,
  91 FR 54259 (2026), [Federal Register PDF](https://www.govinfo.gov/content/pkg/FR-2026-08-21/pdf/2026-17163.pdf).
- CME Group and Silicon Data, **Compute Futures Launch Announcement** (August 11,
  2026), [official release](https://www.cmegroup.com/media-room/press-releases/2026/8/11/cme_group_and_silicondatatolaunchcomputefuturesonoctober5tounloc.html).
- Ornn, **Risk Disclosure and Compute Price Index Construction**,
  [official disclosure](https://data.ornnai.com/risk-disclosure).
- Polymarket, [H100 terminal rules](https://polymarket.com/event/gpu-rental-prices-h100-end-of-2026-20260709164334623)
  and [H100 touch rules](https://polymarket.com/event/gpu-rental-prices-h100-hit-in-2026-20260709165909063).

## Novelty decision

Forecasting with 92 daily observations was rejected as underpowered. Estimating
a latent compute price was rejected because benchmark construction and genuine
market dynamics are not separately identified. A risk-premium paper was rejected
because listed compute futures have not produced a mature settlement panel.

The selected contribution survives those constraints:

1. payoff dominance is pathwise and model-free;
2. price bounds use matched underlyings, date, and venue;
3. sparse-error radii are deterministic and do not require a noise distribution;
4. exact settlement reproduction gates all counterfactual analysis;
5. event weighting avoids treating ladder strikes as independent observations.
