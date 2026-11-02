> **Current photo-first instructions (November 2, 2026):** See [the shared family policy](../workflow/PHOTO_FIRST_PUBLIC_GALLERY_POLICY_2026-11-02.md). Publish useful credited general views of already indexed species as soon as exact-image rights and a basic species sanity check are substantiated. No anatomy arrows or finished lessons are required. Every source image needs its matching metadata sidecar; copies in a ZIP or staging branch do not count until the family Pages gallery serves them. Keep restricted or unresolved photo bytes out of **every** branch of a public repository.

**Two accepted approval paths:** (1) an actual named photo reviewer with real documented evidence; or (2) the owner's documented standing photo-first policy with `approval_mode: OWNER_STANDING_PHOTO_FIRST_POLICY`, `policy_ref: PHOTO_FIRST_PUBLIC_GALLERY_POLICY_2026-11-02`, and truthful `review_operator`, `source_review_evidence`, `taxon_review_evidence` and `approval_note` values. Both still require `rights_approved_for_public: true`, `taxon_reviewed: true`, verified creator, exact-photo HTTPS source, license/version/URL, image bytes and credible source proof. **Never fabricate reviewer evidence, IDs or approvals.**

**Licenses:** verifiable CC0, CC BY and CC BY-SA photos are normally allowed. CC BY-NC 4.0 / CC BY-NC-SA 4.0 are conditionally permitted **only** with an actually noncommercial educational family site, an individually checked license, and `noncommercial_site_use_confirmed: true` for that photo. Preserve explicit NC reuse limits, attribution and adaptation/ShareAlike requirements. Hold ND, ARR and uncertain rights. If the publisher refuses otherwise eligible media, fix its implementation or record the hold; don't bypass guards. New species still need a reviewed index/card installation before automatic general-gallery intake.

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
