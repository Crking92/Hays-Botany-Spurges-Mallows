# Automatic photo intake — Spurges & Mallows

Upload both `photo-intake/approved/<species-id>/photo.jpg` and `photo-intake/approved/<species-id>/photo.jpg.json` to branch `staging/original-source-transfer`. The family workflow validates the species ID, individual source/license metadata, human-attributed approval decision, image decode, 25-MB limit, and collision/duplication protection. After validation the pipeline updates the public site on `main`, recalculates image counts and requests a Pages build.

**Only upload photos with documented public reuse permission.** This repository and staging branch are PUBLIC, including history. Do not upload private or unknown-license photography. Automated checks cannot confer copyright permission or accurately identify an unseen plant.

Sidecar example (replace placeholders only after checking the real image):
```json
{
  "species_id": "actual-existing-slug",
  "photo_file": "my-new-photo.jpg",
  "status": "APPROVED_FOR_PUBLIC_FAMILY_SITE",
  "rights_approved_for_public": true,
  "taxon_reviewed": true,
  "approved_by": "Actual reviewer name",
  "approval_note": "Explain the exact image source and taxon/rights evidence",
  "creator": "Original photographer",
  "source_page": "https://example.org/exact-photo-page",
  "source_page_is_exact": true,
  "license": "CC BY 4.0",
  "license_url": "https://creativecommons.org/licenses/by/4.0/",
  "role": "Only the visible diagnostic structures",
  "modifications": "Unmodified original"
}
```

The importer currently auto-publishes **new pictures of existing indexed species**, not automatically added brand-new species. Missing/unsupported source metadata is held, not falsely marked verified. It does not edit `Hays-County-Botany`.
