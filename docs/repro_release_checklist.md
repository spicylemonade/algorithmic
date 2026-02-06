# Reproducibility and Release Checklist (Item 024)

- [x] Environment lockfile present: `requirements.lock`
- [x] Deterministic random seeds documented and fixed at `42`
- [x] Data licensing/source notes captured:
  - DAMIT exports (CUNI DAMIT project)
  - JPL radar shape model pages
  - NASA PDS/SBN archive bundles
- [x] Source citation list included in project docs/results manifests
- [x] One-command rerun available: `./scripts/rerun_all.sh`

Release notes must include commit hash and data snapshot date.
