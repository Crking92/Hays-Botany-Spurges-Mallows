#!/usr/bin/env python3
"""Audit the EXISTING public Spurges-Mallows learner; never collect or install photos."""
import argparse
import concurrent.futures
import hashlib
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
ALLOWED = re.compile(r"(?:CC0(?: 1\.0)?|Public Domain(?: \([^)]*\))?|CC BY(?:-NC)?(?:-SA)? (?:2\.0|2\.5|3\.0|4\.0)(?: [A-Z]{2,8})?)", re.I)

OWNER_DISPLAY_URL = "https://github.com/Crking92/Hays-Botany-Public/blob/main/docs/GLASS_ROOT_GARDEN_PUBLIC_DISPLAY_PERMISSION_20261103.md"
OWNER_DISPLAY_BLOB_SHA1 = {
    "61a9bda053f069204fa18cad9ccc0205dee5b03f",
    "14b0ae32e643656b7741e2eb81bd5598ff6c15ec",
    "49991a852203279be93d8b544fc8d516eaee508a",
    "25f0ba67f2a3cd9a12f571d78dbae41b813a4ab7",
    "6e9054f9d3dcb14f4a4cb679f730a9f3c880d75b",
}

def read(path):
    return json.loads((SITE / path).read_text(encoding="utf-8"))

def require(ok, why):
    if not ok:
        raise RuntimeError("EXISTING_SITE_QA_FAILED: " + why)

def git_blob_sha(raw):
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()

def local_audit():
    meta = read("data/collection-meta.json")
    index = read("data/collection-index.json")
    gallery = read("data/gallery-index.json")
    migration = read("photo-source-migration-report.json")
    rows = index.get("entries", [])
    ids = [row["id"] for row in rows]
    require(len(rows) == len(set(ids)) and len(rows) >= 130, "missing or duplicated species in index")
    require(len(meta["family_assignments"]) == 13, "unexpected family assignments")
    require(set(gallery["entries"]) == set(ids), "gallery/index species IDs differ")
    files = sorted((SITE / "data/species").glob("*.json"))
    require({p.stem for p in files} == set(ids), "published species files do not match index")
    require(gallery.get("status") == "ONLY_EXISTING_PUBLIC_RIGHTS_CLEARED_SITE_IMAGES", "photo release gate changed")
    refs = set()
    count = 0
    featured = 0
    missing_first_looks = []
    for row in rows:
        card = read("data/species/" + row["id"] + ".json")
        sid = row["id"]
        require(all(card.get(k) == row.get(k) for k in ("id", "family", "genus", "scientific_name")),
                sid + ": index/card identity mismatch")
        require(card["family"] in meta["family_assignments"], sid + ": unassigned family")
        if not str(card.get("look_here_first") or "").strip():
            missing_first_looks.append(sid)
        photos = card.get("verified_photos", [])
        require(isinstance(photos, list), sid + ": invalid photos")
        require(row.get("photo_count") == len(photos), sid + ": species index photo count mismatch")
        info = gallery["entries"][sid]
        require(info.get("count") == len(photos), sid + ": gallery count mismatch")
        require(info.get("first_src") == (photos[0]["src"] if photos else None),
                sid + ": gallery thumbnail points to another image")
        if photos:
            featured += 1
        for photo in photos:
            count += 1
            src = photo.get("src", "")
            rel = PurePosixPath(src)
            require(len(rel.parts) >= 3 and rel.parts[0] == "media" and ".." not in rel.parts
                    and not rel.is_absolute(), sid + ": invalid photo path")
            path = SITE.joinpath(*rel.parts)
            require(path.is_file(), sid + ": linked photo bytes missing: " + src)
            require(src not in refs, sid + ": duplicate photo reference: " + src)
            refs.add(src)
            require(git_blob_sha(path.read_bytes()) == photo.get("display_blob_sha",photo.get("source_blob_sha")),
                    sid + ": published photo differs from its archived Git blob")
            for key in ("creator", "source_page", "license", "license_url", "role"):
                require(bool(str(photo.get(key) or "").strip()), sid + ": absent credit field " + key)
            if photo["license"] == "OWNER PUBLIC DISPLAY PERMISSION":
                require(photo.get("source_blob_sha") in OWNER_DISPLAY_BLOB_SHA1
                        and photo.get("creator") == "Glass Root Garden"
                        and photo.get("license_url") == OWNER_DISPLAY_URL
                        and photo.get("site_display_only") is True
                        and photo.get("public_reuse") is False
                        and str(photo.get("source_page") or "").startswith("https://www.inaturalist.org/photos/"),
                        sid + ": owner-specific display permission has no exact-photo proof")
            else:
                require(bool(ALLOWED.fullmatch(photo["license"])),
                        sid + ": unknown/non-public photo license: " + photo["license"])
            require(not photo.get("private_rights_review_only"),
                    sid + ": public gallery points to held/private image")
            if "-NC" in photo["license"]:
                require(photo.get("noncommercial_only") is True and
                        meta["photo_license_policy"]["noncommercial_educational_use"] is True,
                        sid + ": noncommercial image missing site restriction")
            else:
                require(not photo.get("noncommercial_only"),
                        sid + ": unrestricted license incorrectly labeled noncommercial-only")
            require(photo["source_page"].startswith("https://") and photo["license_url"].startswith("https://"),
                    sid + ": missing exact source/license URL")
    actual = {p.relative_to(SITE).as_posix() for p in (SITE / "media").rglob("*") if p.is_file()}
    require(actual == refs, "orphan media files or untracked photo references")
    require(gallery.get("photo_count") == count and gallery.get("photo_species") == featured,
            "photo totals do not agree with actual linked files")
    require(migration.get("photos_copied_and_eligible", 0) <= count
            and migration.get("species_with_photos", 0) <= featured,
            "historic migration snapshot exceeds current live-gallery totals")
    require(migration.get("restricted_media_copied") == 0
            and migration.get("new_external_images") == 0, "photo migration gate unexpectedly changed")
    return ids, sorted(refs), {"species": len(ids), "families": len(meta["family_assignments"]),
                               "photos": count, "photographed_species": featured,
                               "inherited_empty_first_look_count": len(missing_first_looks),
                               "inherited_empty_first_look_species": missing_first_looks}

def get_live(base, rel):
    url = urllib.parse.urljoin(base, rel)
    last = None
    for attempt in range(5):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "HaysBotanyExistingMigrationQA/1.0"})
            with urllib.request.urlopen(req, timeout=20) as response:
                require(response.status == 200, "bad HTTP status for " + url)
                return response.read()
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last = exc
            if attempt != 4:
                time.sleep(min(2 ** attempt, 8))
    raise RuntimeError("LIVE_SITE_FETCH_FAILED: " + url + ": " + str(last))

def live_audit(base, ids, photos):
    base = base.rstrip("/") + "/"
    html = get_live(base, "index.html")
    require(b"collection-title" in html and b"app.js" in html, "missing live learner shell")
    paths = ["data/collection-index.json", "data/gallery-index.json", "data/collection-meta.json"]
    paths += ["data/species/" + sid + ".json" for sid in ids]
    paths += photos
    def verify(rel):
        expected = (SITE / rel).read_bytes()
        received = get_live(base, rel)
        require(hashlib.sha256(received).digest() == hashlib.sha256(expected).digest(),
                "live bytes differ from audited repository: " + rel)
        return rel
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        result = list(pool.map(verify, paths))
    return len(result)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--live", help="Family GitHub Pages site root ending in /site/")
    args = p.parse_args()
    ids, photos, results = local_audit()
    results["local"] = "PASS"
    if args.live:
        results["live_checked_files"] = live_audit(args.live, ids, photos)
        results["live"] = "PASS"
    print(json.dumps(results, indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
