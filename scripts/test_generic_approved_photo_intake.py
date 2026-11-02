#!/usr/bin/env python3
"""Test shared photo intake in a temporary isolated family website; no real release."""
from __future__ import annotations
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
PUBLISHER=ROOT/"scripts/publish_approved_family_photos.py"

def command(source,site,expect=True,check=False):
    args=[sys.executable,str(PUBLISHER),"--source-root",str(source),"--site-root",str(site)]
    if check:args.append("--check")
    p=subprocess.run(args,capture_output=True,text=True)
    if expect and p.returncode:raise AssertionError("Publisher rejected safe fixture: "+p.stdout+p.stderr)
    if not expect and not p.returncode:raise AssertionError("Publisher accepted invalid fixture: "+p.stdout)
    return p

def main():
    site=ROOT/"site"
    gal=json.loads((site/"data/gallery-index.json").read_text())
    rows=json.loads((site/"data/collection-index.json").read_text())["entries"]
    allowed={"CC0 1.0","CC BY 2.0","CC BY 3.0","CC BY 4.0",
             "CC BY-SA 2.0","CC BY-SA 3.0","CC BY-SA 4.0"}
    candidate=None
    for row in rows:
        sid=row["id"]
        card=json.loads((site/"data/species"/(sid+".json")).read_text())
        for photo in card.get("verified_photos",[]):
            path=site/photo.get("src","")
            if photo.get("license") in allowed and path.is_file() and photo.get("creator") and photo.get("source_page","").startswith("https://"):
                candidate=(sid,photo,path)
                break
        if candidate:break
    if candidate is None:raise AssertionError("No publicly hosted exact-license family photo available for isolated QA")
    sid,photo,original=candidate
    with tempfile.TemporaryDirectory(prefix="hays-family-photo-qa-") as tmp:
        root=Path(tmp)
        target=root/"site"
        shutil.copytree(site,target)
        source=root/"source"
        folder=source/"photo-intake/approved"/sid
        folder.mkdir(parents=True)
        file=folder/"qa-isolated-existing-source-crop.jpg"
        with Image.open(original) as img:
            w,h=img.size
            img.crop((0,0,min(w,400),min(h,400))).convert("RGB").save(file,quality=88)
        sidecar=file.with_name(file.name+".json")
        meta={
            "species_id":sid,"photo_file":file.name,
            "status":"APPROVED_FOR_PUBLIC_FAMILY_SITE",
            "rights_approved_for_public":True,"taxon_reviewed":True,
            "approved_by":"ISOLATED AUTOMATED QA ONLY - NOT LIVE APPROVAL",
            "approval_note":"Test-only temporary crop of previously published source; never committed to the real website.",
            "creator":photo["creator"],"source_page":photo["source_page"],
            "source_page_is_exact":True,"license":photo["license"],
            "license_url":photo["license_url"].rstrip("/")+"/",
            "role":"Temporary crop for isolated software integration test only",
            "modifications":"Temporary JPEG crop from already published source image; not released"
        }
        sidecar.write_text(json.dumps(meta))
        assert json.loads(command(source,target,check=True).stdout)["installed"]==1
        assert not (target/"media"/sid/file.name).exists(),"Dry-run changed the website"
        report=json.loads(command(source,target).stdout)
        assert report["installed"]==1 and report["photo_count"]==gal["photo_count"]+1,report
        assert (target/"media"/sid/file.name).is_file()
        assert json.loads(command(source,target).stdout)["installed"]==0
        # Exercise standing-owner-policy + CC BY-NC through the *isolated* test site.
        # This synthetic license switch is a software fixture, NOT a real photo license assertion.
        ncfile=folder/"qa-isolated-photo-first-nc.jpg"
        with Image.open(original) as img:
            w,h=img.size
            img.crop((max(0,min(w//8,45)),max(0,min(h//8,45)),
                      min(w,max(220,w//2)),min(h,max(220,h//2)))).convert("RGB").save(ncfile,quality=89)
        ncmeta=dict(meta)
        ncmeta["photo_file"]=ncfile.name
        ncmeta.pop("approved_by",None)
        ncmeta["approval_mode"]="OWNER_STANDING_PHOTO_FIRST_POLICY"
        ncmeta["policy_ref"]="PHOTO_FIRST_PUBLIC_GALLERY_POLICY_2026-11-02"
        ncmeta["review_operator"]="ISOLATED AUTOMATED SOFTWARE QA"
        ncmeta["source_review_evidence"]="Synthetic source-review note for an isolated published-source software test."
        ncmeta["taxon_review_evidence"]="Synthetic taxon-review note for an isolated published-source software test."
        ncmeta["license"]="CC BY-NC 4.0"
        ncmeta["license_url"]="https://creativecommons.org/licenses/by-nc/4.0/"
        ncmeta["noncommercial_site_use_confirmed"]=True
        ncsidecar=ncfile.with_name(ncfile.name+".json")
        ncsidecar.write_text(json.dumps(ncmeta))
        assert json.loads(command(source,target,check=True).stdout)["installed"]==1
        assert json.loads(command(source,target).stdout)["installed"]==1
        testcard=json.loads((target/"data/species"/(sid+".json")).read_text())
        assert any(p["noncommercial_only"] is True and p["photo_approval_mode"]=="OWNER_STANDING_PHOTO_FIRST_POLICY" for p in testcard["verified_photos"])
        checked=subprocess.run([sys.executable,str(ROOT/"scripts/verify_automatic_gallery.py"),"--site-root",str(target)],capture_output=True,text=True)
        assert checked.returncode==0,checked.stdout+checked.stderr
        ncmeta["noncommercial_site_use_confirmed"]=False
        ncsidecar.write_text(json.dumps(ncmeta))
        command(source,target,expect=False,check=True)
        ncmeta["noncommercial_site_use_confirmed"]=True
        ncmeta.pop("source_review_evidence")
        ncsidecar.write_text(json.dumps(ncmeta))
        command(source,target,expect=False,check=True)
        ncmeta["source_review_evidence"]="Synthetic source-review note for an isolated published-source software test."
        ncsidecar.write_text(json.dumps(ncmeta))
        meta["rights_approved_for_public"]=False
        sidecar.write_text(json.dumps(meta))
        command(source,target,expect=False,check=True)
        meta["rights_approved_for_public"]=True
        meta["license"]="CC BY-NC 4.0"
        sidecar.write_text(json.dumps(meta))
        command(source,target,expect=False,check=True)
        meta["license"]=photo["license"]
        meta["species_id"]="incorrect-species"
        sidecar.write_text(json.dumps(meta))
        command(source,target,expect=False,check=True)
        meta["species_id"]=sid
        sidecar.write_text(json.dumps(meta))
        orphan=folder/"orphan-upload.jpg"
        shutil.copyfile(file,orphan)
        command(source,target,expect=False,check=True)
    assert json.loads((site/"data/gallery-index.json").read_text())["photo_count"]==gal["photo_count"]
    print("PASS: "+sid+" verified from existing "+photo["license"]+" site photo; safe publish and all rejection tests passed")
if __name__=="__main__":main()
