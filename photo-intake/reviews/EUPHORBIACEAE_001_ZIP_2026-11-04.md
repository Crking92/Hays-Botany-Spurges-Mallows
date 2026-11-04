# Euphorbiaceae_001.zip — 2026-11-04 photo-first audit

**Original ZIP SHA-256:** `d2add8ff36d2d6d144465924e343bcb2fefae86d37677e3124ec1fd91f1b95e2`
**Archive contents:** 34 species folders; 169 actual photograph files; 170 metadata/photo credit entries. All 169 actual files match their recorded SHA-256. Five seven-species contact sheets (last contains six species) visually screened for obvious off-target organisms; no specialist voucher diagnosis or BONAP distribution approval implied. No duplicate file SHA-256 or near-identical within-species pHash distance <= 6 in this batch.

**Site destination:** `Crking92/Hays-Botany-Spurges-Mallows` public family site, **never** the legacy Hays-County-Botany repository.
**Existing release baseline at audit:** 642 gallery images/129 photographed species across the entire family website; these 34 ZIP species already display 130 images; `Euphorbia dentata` had no live images before intake.

## Publication pipeline

The 159 physically present iNaturalist-hosted original JPEGs are indexed in
[`photo-intake/remote-photo-manifests/euphorbiaceae-001-2026-11-04.json`](../remote-photo-manifests/euphorbiaceae-001-2026-11-04.json).
The manifest records the exact original ZIP checksum plus original per-image SHA-256 and iNaturalist observation/photo IDs. Their original user ZIP records further identify credited photographers, recorded source links, licenses, and GBIF IDs.

The GitHub workflow `publish-euphorbiaceae-001-2026-11-04.yml` checks the **live individual-photo iNaturalist API** license, creator, photo membership, and taxon; downloads the source original and compares full SHA-256 with the ZIP before creating a web-sized derivative. It records attribution, original checksum, modification note and noncommercial restriction. Unverified sources remain holds; no claim of live release until site binaries, species cards, gallery indexes and Pages succeed. Workflow run: https://github.com/Crking92/Hays-Botany-Spurges-Mallows/actions/runs/41878506872

The ZIP downloader's license breakdown for all 170 metadata records (not independently approved rights) was CC BY-NC 4.0: 134; CC BY 4.0: 32; CC BY-NC-SA 4.0: 3; CC0 1.0: 1. The public family site explicitly marks itself noncommercial; photo-specific rights still require verification.

## Eleven intake records held, not uploaded to public GitHub

Ten images come from institutional platforms whose exact image/page license must be independently verified. Metadata **claims** are not independent clearance:

- `Argythamnia aphoroides`, `photo_0_ecb1c9405e4bf1ab.jpg`: Washington State University Marion Ownbey Herbarium, intermountainbiota.org, GBIF 6490988647, metadata CC BY-NC 4.0.
- `Croton capitatus`, `photo_3_f6c2481dc8bcf163.jpg` and `photo_4_2db2fa502ae94227.jpg`: University of Texas, was.tacc.utexas.edu, GBIF 3866887358 and 2807600356, metadata CC BY 4.0.
- `Croton lindheimeri`, `photo_1_8f361a43553502fb.jpg`: University of Texas, GBIF 2807286525, metadata CC BY 4.0.
- `Croton lindheimerianus`, `photo_4_9a4184b9e8c49fe8.jpg`: University of Texas, GBIF 3970770311, metadata CC BY 4.0.
- `Croton texensis`, `photo_1_5fda58d865b5d53f.jpg`: University of Texas, GBIF 2807500957, metadata CC BY 4.0.
- `Euphorbia davidii`, `photo_1_82bad4c92b1cfcf4.jpg` and `photo_3_8638b36e33556cad.jpg`: University of Texas, GBIF 3866875475 and 2807596813, metadata CC BY 4.0.
- `Euphorbia serpens`, `photo_3_4155f71bd50f15ab.jpg` and `photo_4_b4829fe7712c3bdd.jpg`: University of Texas, GBIF 2807582150 and 2807364428, metadata CC BY 4.0.

One additional metadata record has **no file inside the uploaded archive**:
- `Euphorbia villifera`, `photo_4_5737dfed1e129bfa.jpg`: Christopher Evans, iNaturalist observation 282446676, metadata CC BY 4.0. Do not count as supplied, installed or approved; do not re-download as a priority while other complete originals are available.

**Next gap:** After actual Pages verification, prioritize the lowest-coverage species and genuine morphology views. Detailed anatomy markup is a separate phase. Never classify held photos as published from an action being queued.
