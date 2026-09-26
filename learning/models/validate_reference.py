"""Independent reference fixtures and artifact integrity checks (no browser)."""
from pathlib import Path
import json, re, sys
import numpy as np
from scipy import signal
from html.parser import HTMLParser

ROOT=Path(__file__).resolve().parents[1]
fixtures=[]
cases=[{}, {'c':20e-6,'rc':.001,'rs':.005,'l':5e-6,'v':42,'startup':True},
       {'c':2200e-6,'rc':.1,'rs':.3,'l':.2e-6,'v':18,'startup':True},
       {'c':100e-6,'rc':.002,'rs':.198,'l':1e-6,'v':36,'startup':False},
       {'c':100e-6,'rc':.002,'rs':.198,'l':1e-6,'v':36,'startup':True},
       {'c':94e-6,'rc':.0015,'rs':.05,'l':1e-6,'v':36,'startup':True}]
for supplied in cases:
    p=dict(c=94e-6,rc=.0015,rs=.05,l=1e-6,v=36,i=20,startup=False);p.update(supplied)
    c,rc,rs,l,v,i=p['c'],p['rc'],p['rs'],p['l'],p['v'],0 if p['startup'] else p['i']
    A=[[-(rs+rc)/l,-1/l],[1/c,0]];B=[[1/l,rc/l],[0,-1/c]];C=[[rc,1],[1,0]];D=[[0,-rc],[0,0]]
    t=np.linspace(0,.002,1501);u=np.column_stack([np.full(len(t),v),np.full(len(t),i)])
    _,y,_=signal.lsim((A,B,C,D),u,t,X0=[0,0 if p['startup'] else v])
    ids=[0,1,2,5,10,20,50,100,200,500,1000,1500]
    fixtures.append({'parameters':p,'samples':[{'index':j,'voltage':float(y[j,0]),'source':float(y[j,1])} for j in ids]})
(ROOT/'qa/transient_reference.json').write_text(json.dumps(fixtures,indent=2)+'\n')

class Inspector(HTMLParser):
    def __init__(self):super().__init__();self.ids=[];self.links=[];self.attrs=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs);self.attrs.append((tag,a))
        if 'id'in a:self.ids.append(a['id'])
        for k in ('src','href'):
            if k in a:self.links.append(a[k])
h=Inspector();h.feed((ROOT/'index.html').read_text());assert len(h.ids)==len(set(h.ids))
(ROOT/'qa/dom_structure.json').write_text(json.dumps(h.attrs,indent=2)+'\n')
missing=[]
for link in h.links:
    if not link.startswith(('https:','http:','#')) and not (ROOT/link).exists():missing.append(link)
assert not missing,missing
script=(ROOT/'lab.js').read_text()
lookups=set(re.findall(r"\$\('([^']+)'\)",script))
assert lookups<=set(h.ids),lookups-set(h.ids)
for tag,a in h.attrs:
    if 'aria-controls'in a:assert a['aria-controls']in h.ids
    if tag=='input':assert a.get('id')+'-o'in h.ids
local_broken=[]
for p in ROOT.rglob('*.md'):
    for target in re.findall(r'\]\(([^)]+)\)',p.read_text()):
        if target.startswith(('http:','https:','#')):continue
        if not (p.parent/target.split('#')[0]).exists():local_broken.append((p.name,target))
assert not local_broken,local_broken
report={'html_unique_ids':len(h.ids),'html_links_checked':len(h.links),'static_element_lookups_checked':len(lookups),
        'local_markdown_links':'passed','transient_reference_cases':len(fixtures),
        'browser_rendering':'Not checked: local-file navigation was blocked by browser security policy.'}
(ROOT/'qa/artifact_checks.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
