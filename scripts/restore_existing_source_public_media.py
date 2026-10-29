#!/usr/bin/env python3
"""Restore only already migrated, strictly reusable photos to public species galleries."""
import hashlib, json, re, shutil, sys
from collections import Counter
from pathlib import Path
SOURCE=Path(sys.argv[1]); ROOT=Path(sys.argv[2]); SITE=ROOT/"site"
ix_path=SITE/"data/collection-index.json"
ix=json.loads(ix_path.read_text())
assert len(ix["entries"])>0
meta_path=SITE/"data/collection-meta.json"
meta=json.loads(meta_path.read_text())
assert len(ix["entries"])==len(list((SITE/"data/species").glob("*.json")))
media=SITE/"media"
assert not media.exists() or not any(media.rglob("*")), "Nonempty site media: inspect before first restore"
media.mkdir(exist_ok=True)
reasons=Counter(); held={}; catalog={}; count=0; records=0; found_species=0; total_bytes=0
def license_info(p):
    name=str(p.get("license") or "").strip()
    if re.search(r"NC|ND|noncommercial|review|unknown|not verified|private|all rights",name,re.I):return None
    if re.fullmatch(r"CC0(?: 1\.0)?",name,re.I):return ("CC0 1.0","https://creativecommons.org/publicdomain/zero/1.0/")
    if re.fullmatch(r"Public [Dd]omain(?: \(U\.S\. federal work\))?",name,re.I):
        return ("Public Domain","https://creativecommons.org/publicdomain/mark/1.0/")
    m=re.fullmatch(r"CC BY(-SA)? (2\.0|2\.5|3\.0|4\.0)(?: US)?",name,re.I)
    if m:
        return ("CC BY"+("-SA" if m.group(1) else "")+" "+m.group(2),
                "https://creativecommons.org/licenses/"+("by-sa" if m.group(1) else "by")+"/"+m.group(2)+"/")
    return None
def approved(p):
    lic=license_info(p)
    if not lic:return None,"unverified_license_or_restricted"
    creator=str(p.get("creator") or "").strip()
    if not creator or re.search(r"unknown|unverified|resolve|source account",creator,re.I):return None,"creator_unverified"
    source=str(p.get("source_page") or "")
    reuse=str(p.get("public_reuse") or "").lower().strip()
    if reuse=="no" or reuse=="false" or "review" in reuse or "private" in reuse or "noncommercial only" in reuse:
        return None,"public_reuse_not_cleared"
    if source.startswith("https://commons.wikimedia.org/wiki/File:"):
        if reuse and not (reuse.startswith("yes") or reuse.startswith("cc_") or reuse in ("public domain","public_domain")):
            return None,"public_reuse_flag_unverified"
        return (creator,source,lic),None
    if source.startswith("https://www.inaturalist.org/photos/") and creator=="Glass Root Garden":
        if "Direct license from photographer" in str(p.get("license_basis") or "") and lic[0]=="CC BY 4.0" and reuse=="yes":
            return (creator,source,lic),None
    return None,"photo_specific_public_source_unverified"
for row in ix["entries"]:
    sid,family,genus=row["id"],row["family"],row["genus"]
    assert re.fullmatch(r"[a-z0-9-]+",sid)
    origin=SOURCE/"content/taxa"/family/genus/sid/"species.json"
    assert origin.is_file(),str(origin)
    card=json.loads(origin.read_text())
    assert card["id"]==sid and card["family"]==family and card["genus"]==genus
    target=SITE/"data/species"/(sid+".json")
    published=json.loads(target.read_text())
    assert published["id"]==sid
    photos=[]; blocks=[]
    for n,p in enumerate(card.get("images",[]) if isinstance(card.get("images",[]),list) else []):
        records+=1
        file=str(p.get("file") or "")
        if not re.fullmatch(r"images/[A-Za-z0-9._-]+\.(jpg|jpeg|png|webp)",file,re.I):
            blocks.append({"record":n,"reason":"missing_or_remote_original_file"});continue
        ok,reason=approved(p)
        if not ok:
            blocks.append({"record":n,"reason":reason});continue
        candidates=(SOURCE/"content/taxa"/family/genus/sid/file,
                    SOURCE/"migration/private-original-photo-holds"/family/genus/sid/file)
        path=next((x for x in candidates if x.is_file()),None)
        if path is None:
            blocks.append({"record":n,"reason":"archived_photo_bytes_missing"});continue
        content=path.read_bytes()
        suffix=path.suffix.lower()
        valid=(content.startswith(b"\xff\xd8\xff") if suffix in (".jpg",".jpeg") else
               content.startswith(b"\x89PNG\r\n\x1a\n") if suffix==".png" else
               content.startswith(b"RIFF") and content[8:12]==b"WEBP")
        if len(content)<500 or len(content)>25*1024*1024 or not valid:
            blocks.append({"record":n,"reason":"file_signature_or_size_problem"});continue
        src="media/"+sid+"/"+path.name
        dest=SITE/src
        if dest.exists():
            blocks.append({"record":n,"reason":"duplicate_filename"});continue
        dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(path,dest)
        assert dest.read_bytes()==content
        sha=hashlib.sha1(b"blob "+str(len(content)).encode()+b"\x00"+content).hexdigest()
        creator,source,lic=ok
        photos.append({"src":src,"creator":creator,"source_page":source,"license":lic[0],
                       "license_url":lic[1],"source_blob_sha":sha,
                       "role":str(p.get("role") or "Existing field photograph")[:450],
                       "modified":"Exact archived original photograph; no modification",
                       "noncommercial_only":False,"private_rights_review_only":False,
                       "source_page_is_exact":True})
        count+=1;total_bytes+=len(content)
    for block in blocks:reasons[block["reason"]]+=1
    if blocks:held[sid]=blocks
    published["verified_photos"]=photos
    published["photo_status"]="VERIFIED_EXISTING_CC_GALLERY" if photos else "PHOTOS_HELD_FROM_PUBLIC_GALLERY"
    target.write_text(json.dumps(published,ensure_ascii=False,indent=2)+"\n")
    row["photo_count"]=len(photos)
    row["photo_publication_status"]=published["photo_status"]
    catalog[sid]={"count":len(photos),"first_src":photos[0]["src"] if photos else None}
    found_species+=bool(photos)
assert records==count+sum(reasons.values())
ix["site_release_stage"]="PUBLIC_EXISTING_SOURCE_CC_PHOTOS"
ix_path.write_text(json.dumps(ix,ensure_ascii=False,indent=2)+"\n")
meta["site_release_stage"]="PUBLIC_EXISTING_SOURCE_CC_PHOTOS"
meta_path.write_text(json.dumps(meta,ensure_ascii=False,indent=2)+"\n")
(SITE/"data/gallery-index.json").write_text(json.dumps({
    "schema_version":1,"status":"ONLY_EXISTING_PUBLIC_RIGHTS_CLEARED_SITE_IMAGES",
    "species":len(catalog),"photo_species":found_species,"photo_count":count,"entries":catalog
},ensure_ascii=False,indent=2)+"\n")
report={"collection":ix["collection_id"],"status":"PASS_EXISTING_ONLY_STRICT_PUBLIC_PHOTO_TRANSFER",
    "species":len(catalog),"source_photo_records":records,"photos_copied_and_eligible":count,
    "species_with_photos":found_species,"held_records":sum(reasons.values()),
    "held_by_reason":dict(reasons),"held_by_species":held,
    "total_source_image_bytes":total_bytes,"new_external_images":0,
    "restricted_media_copied":0,"source_branch_modified":False}
(SITE/"photo-source-migration-report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
(SITE/"PHOTO_PUBLICATION_SCOPE.md").write_text(
  "# Existing-source photographic publication\n\n"+str(count)+" original photos across "+
  str(found_species)+" species were installed from the existing migration after strict exact-image rights review. "+
  str(sum(reasons.values()))+" image records remain held from public display, with per-species reasons "+
  "in site/photo-source-migration-report.json. Original source files are preserved.\n")
print("SOURCE_ONLY_PHOTO_PASS",json.dumps({k:v for k,v in report.items() if k not in ("held_by_species","held_by_reason")},sort_keys=True),flush=True)
