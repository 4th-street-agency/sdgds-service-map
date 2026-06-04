#!/usr/bin/env python3
"""
Rebuild the SDGDS service-area map (index.html) from source data.
Inputs (place in this folder):
  Customer_List.csv            ServiceTitan customer export (Customer Name, Full Address)
  reviews.csv                  testimonials export (Author Name, Star rating, Short Review, ...)
  az_zips.json                 AZ ZIP boundaries (one-time download, see README)
Output: ../index.html (self-contained)
Run:    python source/rebuild.py     (from repo root)  OR  python rebuild.py (from source/)
"""
import json, base64, csv, io, re, os
from collections import defaultdict, Counter

HERE=os.path.dirname(os.path.abspath(__file__))
ROOT=os.path.dirname(HERE)
FLOOR=10
AH={"85044","85045","85048"}
SERVICE={"Gilbert","Mesa","Tempe","Chandler","Queen Creek","San Tan Valley",
         "Scottsdale","Phoenix","Fountain Hills","Paradise Valley","Apache Junction","Gold Canyon"}
ADDR=re.compile(r',\s*([^,]+?),\s*AZ\s+(\d{5})',re.I)
def norm(s):
    s=(s or "").lower().strip(); s=re.sub(r'[*].*$','',s); s=re.sub(r'\s+',' ',s); return re.sub(r'[^a-z ]','',s).strip()

def parse_customers(p):
    zc=Counter(); zcity=defaultdict(Counter); name2zip=defaultdict(Counter)
    with open(p,newline="",encoding="latin-1") as f:
        r=csv.reader(f); next(r,None)
        for row in r:
            if len(row)<2: continue
            m=ADDR.search(row[1] or "")
            if not m: continue
            z=m.group(2); zc[z]+=1; zcity[z][m.group(1).strip().title()]+=1; name2zip[norm(row[0])][z]+=1
    return zc,zcity,name2zip

def rdp(pts,eps=0.0004):
    if len(pts)<3: return pts
    def pd(p,a,b):
        (x,y),(x1,y1),(x2,y2)=p,a,b; dx,dy=x2-x1,y2-y1
        if dx==0 and dy==0: return ((x-x1)**2+(y-y1)**2)**.5
        t=max(0,min(1,((x-x1)*dx+(y-y1)*dy)/(dx*dx+dy*dy)))
        return ((x-(x1+t*dx))**2+(y-(y1+t*dy))**2)**.5
    dmax,idx=0,0
    for i in range(1,len(pts)-1):
        d=pd(pts[i],pts[0],pts[-1])
        if d>dmax: dmax,idx=d,i
    if dmax>eps: return rdp(pts[:idx+1],eps)[:-1]+rdp(pts[idx:],eps)
    return [pts[0],pts[-1]]
def ringf(r):
    o=[[round(x,4),round(y,4)] for x,y in rdp([tuple(p) for p in r])]
    if o[0]!=o[-1]: o.append(o[0])
    return o
def simp(g):
    if g["type"]=="Polygon": g["coordinates"]=[ringf(r) for r in g["coordinates"]]
    elif g["type"]=="MultiPolygon": g["coordinates"]=[[ringf(r) for r in p] for p in g["coordinates"]]
    return g
def quantiles(v,n=5):
    v=sorted(v)
    def q(p):
        i=(len(v)-1)*p; lo=int(i); hi=min(lo+1,len(v)-1); return round(v[lo]+(v[hi]-v[lo])*(i-lo))
    return [q(k/n) for k in range(n+1)]

def build_geo(zc,zcity,az):
    served={z:c for z,c in zc.items() if c>=FLOOR}
    feats=[]
    for f in az["features"]:
        z=f["properties"].get("ZCTA5CE10")
        if z not in served: continue
        city="Ahwatukee" if z in AH else zcity[z].most_common(1)[0][0]
        if not(z in AH or city in SERVICE): continue
        feats.append({"type":"Feature","properties":{"zip":z,"count":served[z],"city":city,
            "lat":float(f["properties"]["INTPTLAT10"]),"lng":float(f["properties"]["INTPTLON10"])},
            "geometry":simp(f["geometry"])})
    return feats, quantiles([f["properties"]["count"] for f in feats])

BAD=re.compile(r'[a-z][A-Z]')
def build_reviews(rev_csv,name2zip,zip_city):
    rows=list(csv.DictReader(open(rev_csv,newline="",encoding="latin-1")))
    rendered=set(zip_city); zc=Counter(); zs=defaultdict(int); cand=defaultdict(list)
    for rv in rows:
        nm=norm(rv.get("Author Name"))
        if nm not in name2zip: continue
        z=name2zip[nm].most_common(1)[0][0]
        if z not in rendered: continue
        try: st=int(rv.get("Star rating"))
        except: continue
        zc[z]+=1; zs[z]+=st
        cand[z].append({"star":st,"txt":re.sub(r'\s+',' ',(rv.get("Short Review") or "").strip()),
                        "author":(rv.get("Author Name") or "").strip(),"amb":len(name2zip[nm])>1})
    cc=Counter(); cs=defaultdict(int)
    for z in zc: cc[zip_city[z]]+=zc[z]; cs[zip_city[z]]+=zs[z]
    def ok(c,t):
        x=c["txt"]
        if not x or BAD.search(x) or c["amb"]: return False
        if t==1: return c["star"]==5 and 45<=len(x)<=150 and x[-1] in ".!?"
        if t==2: return c["star"]>=4 and 35<=len(x)<=190 and x[-1] in ".!?"
        return c["star"]>=4 and 25<=len(x)<=200
    def sa(a):
        p=a.split(); return (p[0]+(" "+p[1][0]+"." if len(p)>1 and p[1][:1].isalpha() else "")) if p else ""
    used=set(); qbz={}
    for z in sorted(rendered,key=lambda z:len(cand.get(z,[]))):
        for t in (1,2,3):
            pool=[c for c in cand.get(z,[]) if ok(c,t) and norm(c["txt"]) not in used]
            if pool:
                pool.sort(key=lambda c:abs(95-len(c["txt"]))); ch=pool[0]; used.add(norm(ch["txt"]))
                qbz[z]={"quote":ch["txt"],"author":sa(ch["author"])}; break
    REV={}
    for z in rendered:
        c=zip_city[z]; n=cc.get(c,0); e={"ccount":n,"cavg":round(cs[c]/n,2) if n else 0,"city":c}
        if z in qbz: e.update(qbz[z])
        REV[z]=e
    return REV

def main():
    zc,zcity,name2zip=parse_customers(os.path.join(HERE,"Customer_List.csv"))
    az=json.load(open(os.path.join(HERE,"az_zips.json")))
    feats,breaks=build_geo(zc,zcity,az)
    zip_city={f["properties"]["zip"]:f["properties"]["city"] for f in feats}
    REV=build_reviews(os.path.join(HERE,"reviews.csv"),name2zip,zip_city)
    json.dump({"type":"FeatureCollection","features":feats,"breaks":breaks},
              open(os.path.join(HERE,"zip_geo.json"),"w"),separators=(',',':'))
    json.dump(REV,open(os.path.join(HERE,"reviews_by_zip.json"),"w"))
    tpl=open(os.path.join(HERE,"template.html")).read()
    geo=json.dumps({"type":"FeatureCollection","features":feats},separators=(',',':'))
    out=(tpl.replace("__GEO__",geo).replace("__BREAKS__",json.dumps(breaks))
            .replace("__REVIEWS__",json.dumps(REV)))
    open(os.path.join(ROOT,"index.html"),"w").write(out)
    print(f"rebuilt index.html | {len(feats)} ZIPs | breaks {breaks}")
if __name__=="__main__": main()
