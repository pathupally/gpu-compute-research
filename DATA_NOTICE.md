# Data and provenance notice

The MIT license applies to original source code in this repository. It does not
grant rights in third-party benchmark observations, event-contract records,
price histories, names, or source materials.

Public inputs are limited to normalized fields consumed by the analysis.
Upstream publishers retain ownership and any applicable database, contractual,
or access rights. Raw API responses, full market objects, portal captures,
copied rules, and vendor articles are not redistributed.

`data/source_manifest.json` records, for each source, an upstream URI, retrieval
date, record locator, source-capture fingerprint, and redistribution status.
Those source captures are unavailable in this repository. Their fingerprints
support provenance bookkeeping but cannot independently prove the integrity of
an artifact a reader cannot inspect. By contrast, hashes of the three included
normalized artifacts are verified automatically before every analysis run.

Users are responsible for complying with upstream terms when acquiring new
records or constructing a later vintage.
