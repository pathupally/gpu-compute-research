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
- Demirer, Fradkin, Tadelis, and Peng, **The Emerging Market for Intelligence** (2025),
  [NBER 34608](https://www.nber.org/papers/w34608). Documents six facts on the
  LLM API market using OpenRouter and Microsoft Azure. Token-side analog: the
  inference-side complement to a rental index. A joint rental-plus-token study
  is the natural next step and is not in the present paper.
- Li et al., **Spot Pricing in the Cloud Ecosystem** (2017),
  [arXiv:1708.01401](https://arxiv.org/abs/1708.01401). Reviews 61 primary studies
  on provider spot pricing; this literature concerns resource allocation and
  posted cloud prices rather than cash-settled GPU-index options.

## Closest cross-vendor and index-construction methods

- Qi He, **Location-Robust Cost-Preserving Blended Pricing for Multi-Campus AI
  Data Centers** (2026), [arXiv:2512.14197](https://arxiv.org/abs/2512.14197).
  Proposes two-way fixed-effects and common-weight operators that reconcile
  cost-preservation with ranking robustness when a portfolio procures the same
  SKU across heterogeneous campuses. Different problem from cross-vendor
  (location within a portfolio, not vendor across market). The operator
  framework is reusable for cross-vendor reconciliation as future work.
- Bergemann and Deb, **Robust Pricing for Cloud Computing** (2025),
  [Cowles 2423](https://cowles.yale.edu/research/cfdp-2423-robust-pricing-cloud).
  Theoretical mechanism-design result for posted cloud prices under buyer
  private information. Non-empirical but supports the design intuition that
  posted cloud prices do not continuously market-clear.
- "Did You Win the GPU Cloud Lottery? Benchmarking from Tokens-per-Dollar
  Perspective" (2025), [ACM 10.1145/3818671.3818674](https://dl.acm.org/doi/10.1145/3818671.3818674).
  Reports that 8% micro-benchmark variation on identical GPUs can produce a
  1.61× token-per-dollar difference. Empirical basis for the cross-vendor
  basis: a 1–2% level difference between two indices is not small once it
  propagates into per-workload cost.

## Institutional sources

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
- CME Group and Silicon Data, **Compute Futures Launch Announcement** (May 12,
  2026 partnership; August 11, 2026 listing announcement), [official
  release](https://www.cmegroup.com/media-room/press-releases/2026/8/11/cme_group_and_silicondatatolaunchcomputefuturesonoctober5tounloc.html).
  Cash-settled on Silicon Data H100 and B200 rental indices, USD-denominated,
  CFTC review pending.
- ICE and Ornn, **GPU Compute Futures Launch Announcement** (May 19, 2026),
  [press release](https://ir.theice.com/press/news-details/2026/ICE-and-Ornn-to-Launch-GPU-Compute-Futures-Contracts/default.aspx).
  Cash-settled on the Ornn Compute Price Index (OCPI). USD-denominated.
  Contracts may reference H100, H200, B200, RTX 5090, and additional GPU types
  as the market develops. Subject to regulatory approval.
- Architect, **Compute Futures on a New US Exchange** (May 28, 2026). Per
  the joint Ornn–Architect press release, AX perpetuals settle on Ornn's
  indices — i.e. the same family of OCPI
  series Kalshi and ICE reference. Three venues now list or have announced
  cash-settled products referencing Ornn; this strengthens the auditability
  argument but also concentrates the structural conflict-of-interest named in
  the OCPI risk-disclosure.
- NATIVX, energy-normalized compute index, per Silicon Data's published
  SiliconMark-versus-InferenceX methodology note.
  Fourth benchmark under active development.
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
