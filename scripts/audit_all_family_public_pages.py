#!/usr/bin/env python3
"""Read-only end-to-end audit of photos actually served by Hays Botany family Pages.

Compares GitHub main gallery with public Pages, reads every public species card,
HEAD-checks every referenced image, and GET-checks one original image per species.
No repository mutations, photo retrieval into source, or license overrides.
"""
from __future__ import annotations
import argparse
import concurrent.futures as cf
import hashlib
import json
import os
from pathlib import PurePosixPath
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

COLLECTIONS = ("Poaceae", "Asteraceae", "Fabaceae", "Monocots-Aquatics",
               "Lamiales", "Asterid-Allies", "Cacti-Buttercups",
               "Spurges-Mallows", "Trees-Shrubs", "Mixed-Families")
AGENT = "HaysBotanyPublishedGalleryAudit/1.0 (read-only live image verification)"
def fetch(url, method="GET", attempts=3):
    last = None
    for n in range(attempts):
        try:
            request = urllib.request.Request(url, method=method, headers={
                "User-Agent": AGENT, "Accept": "application/json,*/*"})
            with urllib.request.urlopen(request, timeout=18) as response:
                if response.status != 200:
                    raise ValueError("HTTP " + str(response.status))
                headers = dict(response.headers)
                return (response.read() if method == "GET" else b""), headers
        except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
            last = exc
            if n+1 < attempts:time.sleep(2 + n*3)
    raise RuntimeError(str(last))
def get_json(url):
    return json.loads(fetch(url)[0])
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--collection", choices=COLLECTIONS, required=True)
    parser.add_argument("--report", required=True)
    args=parser.parse_args()
    short="Hays-Botany-"+args.collection
    base="https://crking92.github.io/"+short+"/site/"
    source="https://raw.githubusercontent.com/Crking92/"+short+"/main/site/"
    report={"collection":args.collection,"site":base,
            "status":"INCOMPLETE","live_gallery_matches_main":False,
            "public_species_checked":0,"unique_photo_urls_checked":0,
            "failed_urls":[]}
    try:
        expected=get_json(source+"data/gallery-index.json")
        report["repo_photo_count"]=expected.get("photo_count",expected.get("photo_files"))
        report["repo_photo_panels"]=expected.get("photo_panels")
        report["repo_photographed_species"]=expected.get("photo_species")
        report["repo_species"]=expected.get("species")
        # Page rollout can lag site writes: retry entire JSON comparison.
        for attempt in range(15):
            try:
                observed=get_json(base+"data/gallery-index.json")
                if observed == expected:
                    report["live_gallery_matches_main"]=True
                    break
                report["live_photo_count"]=observed.get("photo_count",observed.get("photo_files"))
                report["live_photo_panels"]=observed.get("photo_panels")
                report["live_photographed_species"]=observed.get("photo_species")
                print("LIVE_NOT_AT_MAIN",args.collection,"attempt",attempt+1,
                      "live",report["live_photo_count"],"main",report["repo_photo_count"],flush=True)
            except Exception as exc:
                print("LIVE_GALLERY_UNAVAILABLE",args.collection,str(exc)[:150],flush=True)
            if attempt<14: time.sleep(10)
        if not report["live_gallery_matches_main"]:
            raise RuntimeError("Public gallery index has not reached current main repository state")
        page,_=fetch(base+"index.html")
        if b"app.js" not in page:raise RuntimeError("Live HTML missing gallery app.js")
        entries=expected.get("entries")
        if not isinstance(entries,dict) or len(entries)!=expected.get("species"):
            raise RuntimeError("Source gallery index species mismatch")
        def read_species(item):
            sid,info=item
            url=base+"data/species/"+urllib.parse.quote(sid)+".json"
            card=get_json(url)
            if card.get("id")!=sid:raise RuntimeError(sid+": live card ID does not match gallery")
            photos=card.get("panels",[]) if args.collection=="Poaceae" else card.get("verified_photos",[])
            if not isinstance(photos,list) or len(photos)!=info.get("count"):
                raise RuntimeError(sid+": live card photo count does not match main gallery")
            first=photos[0].get("src") if photos else None
            if first!=info.get("first_src"):
                raise RuntimeError(sid+": gallery thumbnail does not match actual live card")
            for p in photos:
                if not p.get("src") or not p.get("creator") or not p.get("license"):
                    raise RuntimeError(sid+": live photo lacks URL, creator, or license")
                if not p.get("source_page"):
                    raise RuntimeError(sid+": live photo lacks source credit link")
            return sid,photos
        with cf.ThreadPoolExecutor(max_workers=7) as pool:
            rows=list(pool.map(read_species, sorted(entries.items())))
        report["public_species_checked"]=len(rows)
        photo_urls={}
        samples=[]
        for sid,photos in rows:
            if photos:samples.append((sid, photos[0]))
            for p in photos:
                src=p["src"]
                full=urllib.parse.urljoin(base,src)
                parsed=urllib.parse.urlparse(full)
                # Allow only this family Pages host/path. Poaceae uses ../content/taxa.
                prefix="https://crking92.github.io/"+short+"/"
                if parsed.scheme!="https" or not full.startswith(prefix) or "../" in parsed.path:
                    raise RuntimeError("Unsafe public photo URL "+str(src))
                photo_urls[full]=(sid,p)
        report["referenced_panels"]=sum(len(x[1]) for x in rows)
        report["unique_photo_urls_expected"]=len(photo_urls)
        def check_one(row):
            url,_info=row
            _body,head=fetch(url,method="HEAD")
            ctype=head.get("Content-Type",head.get("content-type","")).lower()
            n=head.get("Content-Length",head.get("content-length",""))
            if not ctype.startswith("image/"):
                raise RuntimeError("Wrong media Content-Type "+ctype)
            if n and int(n)<200:
                raise RuntimeError("Empty/invalid media length "+n)
            return url
        with cf.ThreadPoolExecutor(max_workers=7) as pool:
            futures={pool.submit(check_one,item):item[0] for item in photo_urls.items()}
            for fut in cf.as_completed(futures):
                try: fut.result();report["unique_photo_urls_checked"]+=1
                except Exception as exc:
                    report["failed_urls"].append({"url":futures[fut],"reason":str(exc)[:180]})
        if report["failed_urls"]:
            raise RuntimeError(str(len(report["failed_urls"]))+" live image URLs fail HEAD check")
        # A real GET, not just HEAD, for at least one rendered image per species.
        def get_sample(sample):
            sid,photo=sample
            url=urllib.parse.urljoin(base,photo["src"])
            payload,head=fetch(url)
            if len(payload)<200:raise RuntimeError("Empty live photo bytes: "+sid)
            sha=photo.get("source_blob_sha")
            if sha:
                got=hashlib.sha1(b"blob "+str(len(payload)).encode()+b"\\0"+payload).hexdigest()
                if got != sha:raise RuntimeError("Live photo bytes differ from credited source Git blob: "+sid)
            return sid
        with cf.ThreadPoolExecutor(max_workers=5) as pool:
            for sid in pool.map(get_sample,samples):
                report["sampled_live_photo_bytes"] = report.get("sampled_live_photo_bytes",0)+1
        report["status"]="LIVE_VERIFIED_ALL_REFERENCED_IMAGE_URLS_AND_SPECIES_CARDS"
    except Exception as exc:
        report["status"]="FAILED_NOT_FULLY_LIVE"
        report["failure"]=str(exc)[:700]
    os.makedirs(os.path.dirname(args.report) or ".",exist_ok=True)
    with open(args.report,"w",encoding="utf-8") as out:
        json.dump(report,out,indent=2,sort_keys=True)
        out.write("\n")
    print("FAMILY_LIVE_PAGES_AUDIT",json.dumps(report,sort_keys=True),flush=True)
    if report["status"]!="LIVE_VERIFIED_ALL_REFERENCED_IMAGE_URLS_AND_SPECIES_CARDS":
        sys.exit(2)
if __name__=="__main__":
    main()
