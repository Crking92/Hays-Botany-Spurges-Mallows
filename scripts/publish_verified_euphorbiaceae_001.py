#!/usr/bin/env python3
"""Euphorbiaceae photo-first release. Reuse audited Onagraceae source checks,
with a separate expected ZIP manifest and a web-optimized gallery derivative.

Source originals remain untouched in the user's checksum-documented ZIP.
Each live iNaturalist image is independently checked against its observation,
photo-level CC license, credited creator and the exact original ZIP SHA-256
before it can enter public site media. Other provider photos are excluded.
"""
from pathlib import Path
import sys

baseline=Path(__file__).with_name("publish_verified_onagraceae_zip.py")
source=baseline.read_text(encoding="utf-8")

def patch(before,after):
    global source
    if source.count(before)!=1:
        raise SystemExit("Checked photo verifier changed; refuse silent patch: "+before[:70])
    source=source.replace(before,after)

patch('if m["batch_id"]!="onagraceae-2026-11-03":',
      'if m["batch_id"]!="euphorbiaceae-001-2026-11-04":')
patch('current=set(); current_shas=set()',
      'current=set(); current_shas=set(); current_urls=set()')
patch('current.update((x.get("source_page"),x.get("sha256")) for x in card.get("verified_photos",[]))',
      'current.update((x.get("source_page"),x.get("sha256")) for x in card.get("verified_photos",[]))\n        current_urls.update(x.get("source_page") for x in card.get("verified_photos",[]) if x.get("source_page"))')
patch('if (src,sha) in current or sha in current_shas:',
      'if src in current_urls or (src,sha) in current or sha in current_shas:')
patch('records=list(decode(m))',
      'records=sorted(list(decode(m)), key=lambda rec:(len(json.loads((Path("site/data/species")/(rec[0]+".json")).read_text()).get("verified_photos",[])),rec[0]))\n    if len(records)!=159 or m.get("record_count")!=159:raise SystemExit("Euphorbiaceae ZIP manifest count mismatch")')
patch('            filename=f"inat-{pid}.{ext}"',
      '''            # Verify the exact source ORIGINAL before creating a lightweight
            # display copy. The original ZIP and original checksum are preserved.
            with Image.open(io.BytesIO(img)) as original:
                original.thumbnail((1800,1800))
                display=io.BytesIO()
                original.convert("RGB").save(display,format="JPEG",quality=82,optimize=True)
                img=display.getvalue()
            display_sha=hashlib.sha256(img).hexdigest()
            filename=f"inat-{pid}-web.jpg"''')
patch('"review_operator":"Hays Botany Onagraceae photo-first original ZIP verifier"',
      '"review_operator":"Hays Botany Euphorbiaceae original ZIP and live source verifier"')
patch('"taxon_review_evidence":f"3 Onagraceae contact sheets inspected for obvious off-target organisms. Live source name {name} maps to indexed species {sid}; specialist morphology and BONAP range deferred."',
      '"taxon_review_evidence":f"Five Euphorbiaceae ZIP contact sheets reviewed for obvious off-target organisms. Live source determination {name} matches indexed species {sid}; formal plant diagnosis and BONAP county distribution require separate review."')
patch('"modifications":"Original source photo, no edits",',
      '"modifications":"Website-only JPEG derivative resized to fit within 1800 by 1800 pixels and compressed at quality 82. Original ZIP image retained untouched; exact original SHA-256 documented in source evidence.",')
patch('"sha256":sha\n',
      '"original_sha256":sha,"sha256":display_sha\n')
patch('row["status"]="ORIGINAL_AND_RIGHTS_VERIFIED"',
      'row["status"]="ORIGINAL_AND_RIGHTS_VERIFIED"\n            row["original_sha256"]=sha\n            row["published_derivative_sha256"]=display_sha')
patch('raise ValueError("Source observation not found")','raise ValueError("Source observation not found")') if False else None
scope={"__name__":"__main__","__file__":str(baseline)}
exec(compile(source,str(baseline),"exec"),scope)
