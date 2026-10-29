#!/usr/bin/env python3
"""QA the real source-filtered visual family website and generate offline preview."""
from pathlib import Path
from collections import Counter
import hashlib,json,shutil,subprocess

ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT/"site"
DIST=ROOT/"dist"
subprocess.run(["python3",str(ROOT/"scripts/validate_collection.py")],check=True,cwd=ROOT)
config=json.loads((ROOT/"config/collection.json").read_text())
idx=json.loads((SITE/"data/collection-index.json").read_text())
m=json.loads((SITE/"data/collection-meta.json").read_text())
g=json.loads((SITE/"data/gallery-index.json").read_text())
report=json.loads((SITE/"photo-source-migration-report.json").read_text())
assert config["planning_status"]=="STAGING_ONLY_NOT_AUTHORITATIVE"
assert config["publication"]["enabled"] is False
assert m["repository_full_name"]==config["repository_full_name"]
assert idx["site_release_stage"]=="PUBLIC_EXISTING_SOURCE_CC_PHOTOS"
assert g["status"]=="ONLY_EXISTING_PUBLIC_RIGHTS_CLEARED_SITE_IMAGES"
assert len(idx["entries"])==g["species"]==report["species"]
total=0; species=0; approved=set()
for row in idx["entries"]:
    sid=row["id"]
    card=json.loads((SITE/"data/species"/(sid+".json")).read_text())
    photos=card["verified_photos"]
    assert len(photos)==row["photo_count"]==g["entries"][sid]["count"],sid
    if photos:species+=1
    for p in photos:
        src=p["src"]
        assert src.startswith("media/"+sid+"/") and ".." not in src
        assert p["creator"] and p["source_page"].startswith("https://") and p["license_url"].startswith("https://creativecommons.org/")
        assert p["noncommercial_only"] is False and p["private_rights_review_only"] is False
        path=SITE/src
        assert path.is_file() and path.stat().st_size>500,src
        content=path.read_bytes()
        assert content.startswith((b"\xff\xd8\xff",b"\x89PNG\r\n\x1a\n",b"RIFF")),src
        assert hashlib.sha1(b"blob "+str(len(content)).encode()+b"\x00"+content).hexdigest()==p["source_blob_sha"],src
        approved.add(path.resolve())
        total+=1
assert total==g["photo_count"]==report["photos_copied_and_eligible"]
assert species==g["photo_species"]==report["species_with_photos"]
assert len(approved)==total
actual={f.resolve() for f in (SITE/"media").rglob("*") if f.is_file()}
assert approved==actual,"Public media folder has images not covered by explicit approved gallery"
html=(SITE/"index.html").read_text(encoding="utf-8")
script=(SITE/"app.js").read_text(encoding="utf-8")
style=(SITE/"styles.css").read_text(encoding="utf-8")
assert 'id="photo-summary"' in html and "gallery-index.json" in script
assert "gallery-strip" in style and "result-thumb" in style
assert "https://crking92.github.io/Hays-County-Botany/" in html
if DIST.exists():shutil.rmtree(DIST)
shutil.copytree(SITE,DIST)
assert len(list((DIST/"data/species").glob("*.json")))==len(idx["entries"])
print("REAL_EXISTING_SOURCE_GALLERY_QA_PASS",json.dumps({
  "repo":m["repository_full_name"],"species":len(idx["entries"]),
  "photographed_species":species,"verified_photos":total,"held_source_records":report["held_records"],
  "site_preview_generated":True,"new_images_downloaded":0,"source_data_modified":False
},sort_keys=True),flush=True)
