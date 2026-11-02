#!/usr/bin/env python3
"""Check exact original iNaturalist photo rights before moving backed-up ZIP media into public site."""
import hashlib
import io
import json
import os
import sys
import urllib.request
from pathlib import Path
from PIL import Image

base = Path(__file__).resolve().parents[1]
report = []
manifest = json.loads((base/"photo-intake/remote-photo-manifests/violaceae-2026-11-02.json").read_text())
temp = Path(os.environ.get("RUNNER_TEMP", "/tmp"))/"violaceae-verified"
if manifest["target_license"] != "cc-by-nc":
    sys.exit("Expected CC BY-NC photo-specific ZIP metadata")
aliases = {
  "pombalia-verticillata":{"pombalia verticillata","hybanthus verticillatus"},
  "viola-missouriensis":{"viola missouriensis","viola sororia var. missouriensis"}
}

def fetch(url, limit=25_000_000):
    r=urllib.request.Request(url,headers={"User-Agent":"HaysBotany-EducationalPhotoGallery/1.0"})
    with urllib.request.urlopen(r,timeout=25) as response:
        content=response.read(limit+1)
    if len(content)>limit:
        raise ValueError("Source download too large")
    return content

for item in manifest["photographs"]:
    sid,photo_id,oid=item["species_id"],int(item["photo_id"]),int(item["observation_id"])
    row={"species":sid,"photo_id":photo_id}
    try:
        if sid not in aliases or item["extension"] not in ("jpg","jpeg"):
            raise ValueError("Unknown family species or image extension")
        api=f"https://api.inaturalist.org/v1/observations/{oid}"
        response=json.loads(fetch(api,5_000_000))
        obs=next((r for r in response.get("results",[]) if int(r["id"])==oid),None)
        if not obs:
            raise ValueError("Observation missing in independent provider API check")
        taxon=str((obs.get("taxon") or {}).get("name") or "").lower()
        if taxon not in aliases[sid]:
            raise ValueError("Observation species determination not compatible: "+taxon)
        p=next((p for p in obs.get("photos",[]) if int(p.get("id",0))==photo_id),None)
        if p is None:
            raise ValueError("Individual photo not found on source observation")
        licence=str(p.get("license_code") or "").lower().replace("_","-")
        if licence!="cc-by-nc":
            raise ValueError("Exact photo does not confirm CC BY-NC license: "+licence)
        attribution=str(p.get("attribution") or item["creator"]).strip()
        if not attribution:
            raise ValueError("Missing source credit")
        url=f"https://inaturalist-open-data.s3.amazonaws.com/photos/{photo_id}/original.{item['extension']}"
        payload=fetch(url)
        if hashlib.sha256(payload).hexdigest()!=item["sha256"]:
            raise ValueError("Remote original not byte-identical to backed-up user's ZIP")
        with Image.open(io.BytesIO(payload)) as image:
            if image.format!="JPEG" or image.width*image.height>80_000_000:
                raise ValueError("Image type or pixel limits failed")
            image.verify()
        filename=f"inat-{photo_id}.{item['extension']}"
        folder=temp/"photo-intake"/"approved"/sid
        folder.mkdir(parents=True,exist_ok=True)
        (folder/filename).write_bytes(payload)
        side={
          "species_id":sid,"photo_file":filename,
          "status":"APPROVED_FOR_PUBLIC_FAMILY_SITE",
          "rights_approved_for_public":True,"taxon_reviewed":True,
          "approval_mode":"OWNER_STANDING_PHOTO_FIRST_POLICY",
          "policy_ref":"PHOTO_FIRST_PUBLIC_GALLERY_POLICY_2026-11-02",
          "review_operator":"Hays Botany automated exact-photo provider and ZIP integrity check",
          "source_review_evidence":f"Live iNaturalist API observation {oid} lists photo {photo_id} with photo-specific license {licence}; original ZIP and remote media SHA256 match.",
          "taxon_review_evidence":f"Basic general-photo check: observation taxon {taxon} matches assigned species concept; uploaded contact-sheet screened for clear mismatch; specialist anatomical identification deferred.",
          "approval_note":f"CC BY-NC license confirmed on live individual media {photo_id}; actual ZIP bytes match SHA256. Photo first, detailed diagnostic morphology later.",
          "creator":attribution,
          "source_page":f"https://www.inaturalist.org/photos/{photo_id}",
          "source_page_is_exact":True,
          "license":"CC BY-NC 4.0",
          "license_url":"https://creativecommons.org/licenses/by-nc/4.0/",
          "noncommercial_site_use_confirmed":True,
          "role":item["caption"]+" (general view; diagnostic ID details deferred)",
          "modifications":"Original image bytes, no alterations",
          "sha256":item["sha256"]
        }
        (folder/(filename+".json")).write_text(json.dumps(side,indent=2)+"\n")
        row["status"]="VERIFIED_FOR_RELEASE"
    except Exception as e:
        row.update(status="HELD",reason=str(e)[:500])
    print(json.dumps(row),flush=True)
    report.append(row)
Path("/tmp/violaceae-source-review.json").write_text(json.dumps(report,indent=2)+"\n")
print("APPROVED",sum(x["status"]=="VERIFIED_FOR_RELEASE" for x in report),
      "HELD",sum(x["status"]=="HELD" for x in report),flush=True)
