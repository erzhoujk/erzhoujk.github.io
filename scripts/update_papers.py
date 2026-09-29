#!/usr/bin/env python3
"""Fetch a small, reproducible three-day multimodal paper digest."""
import json, re, urllib.parse, urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets/data/papers.json"
NS = {"a": "http://www.w3.org/2005/Atom"}

def arxiv():
    q = 'all:"multimodal" OR all:"vision-language" OR all:"video understanding"'
    url = "https://export.arxiv.org/api/query?" + urllib.parse.urlencode({"search_query": q, "start": 0, "max_results": 30, "sortBy": "submittedDate", "sortOrder": "descending"})
    req = urllib.request.Request(url, headers={"User-Agent": "paper-radar/1.0"})
    root = ET.fromstring(urllib.request.urlopen(req, timeout=30).read())
    out=[]
    for e in root.findall("a:entry", NS):
        title=" ".join((e.findtext("a:title", "", NS)).split())
        summary=" ".join((e.findtext("a:summary", "", NS)).split())
        link=next((x.attrib.get("href") for x in e.findall("a:link",NS) if x.attrib.get("rel")=="alternate"), "")
        date=e.findtext("a:published", "", NS)[:10]
        cats={x.attrib.get("term") for x in e.findall("a:category",NS)}
        if not title or "cs.CV" not in cats and "cs.CL" not in cats and "cs.AI" not in cats: continue
        low=(title+summary).lower(); category="视频理解" if "video" in low else "具身智能" if any(x in low for x in ("embodied","robot","vla")) else "训练与评测" if any(x in low for x in ("benchmark","evaluation")) else "视觉语言"
        out.append({"title":title,"authors":", ".join(x.findtext("a:name", "", NS) for x in e.findall("a:author",NS)[:3]),"source":"arXiv","date":date,"category":category,"abstract":summary[:330],"score":90,"url":link,"read_time":max(5,min(15,len(summary)//180+5))})
    return out

def main():
    now=datetime.now(timezone.utc); cutoff=(now-timedelta(days=3)).date().isoformat()
    try: papers=[p for p in arxiv() if p["date"]>=cutoff][:24]
    except Exception as e: print("arXiv fetch failed:",e); papers=[]
    payload={"updated_at":now.isoformat(),"period":f"{cutoff} – {now.date().isoformat()} · 按相关度排序","papers":papers}
    OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n")
    print(f"wrote {len(papers)} papers")

if __name__ == "__main__": main()
