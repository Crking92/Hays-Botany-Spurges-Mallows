# Hays Botany — Spurges & Mallows

**Historical source transfer COMPLETE; existing public family learner active. New botanical/photo enrichment is deferred.**

[Open the family Visual Learner](https://crking92.github.io/Hays-Botany-Spurges-Mallows/site/) · [Original read-only Hays Botany hub](https://crking92.github.io/Hays-County-Botany/) · [Current botanical write routing](https://github.com/Crking92/Hays-County-Botany/blob/main/workflow/ACTIVE_NEW_PLANT_WRITE_ROUTING_20261028.json)

This collection contains **130 existing species lessons across 13 assigned families**. Its complete original scientific/photo source is preserved on branch [`staging/original-source-transfer`](https://github.com/Crking92/Hays-Botany-Spurges-Mallows/tree/staging/original-source-transfer), whereas its photo-backed public learner lives under `main/site`. New botanical edits go to the approved family branch, not to the legacy hub.

## Migration-only source/file results — October 30, 2026

- **764/764 original files** match their destination's Git blob SHA in the transferred source manifest; **0 missing and 0 changed bytes**.
- Original content: **417 text/source-credit files and 347 original photograph binaries**.
- Existing public learner: **130 species lesson files and 99 hosted public-gallery photographs across 48 species**.
- **261/360 original image metadata references remain excluded from the public gallery** pending individual source, license or permissions review. Those held references do **not** indicate incomplete source-file transfer.
- All `staging/*` and historical photo-hold branches are accessible while the repository is PUBLIC, even if the Pages photo gallery filters held pictures. Do not add any new license-uncertain files, and do not delete or rewrite original source/history as an unapproved workaround.
- Obsolete text-only publish workflows intentionally refuse to overwrite the existing photo-backed family site; do not bypass them.

[Source manifest](https://github.com/Crking92/Hays-Botany-Spurges-Mallows/blob/staging/original-source-transfer/migration/original-source-transfer-manifest.json) · [Existing photo release report](site/photo-source-migration-report.json) · [Migration audit checkpoint](migration/SPURGES_MALLOWS_TRANSFER_QA_20261030.md)

## Verification and next phases

`python3 scripts/verify_existing_site.py` checks all species JSON, exact public media bytes vs recorded Git source SHA, source/license credits and gallery indexes. [Automated public Pages QA](.github/workflows/verify-existing-site-gallery.yml) adds per-file live HTTP checks; count live readiness as passed only if that GitHub Action succeeds. Blank inherited anatomy lesson fields are recorded as deferred content enrichment, not fabricated during migration.

No new imagery, plant additions, photo permissions changes, hub edits, automation restarts, or navigation cutover are authorized by the source migration. Future plant writes follow the hub's active family write registry.
