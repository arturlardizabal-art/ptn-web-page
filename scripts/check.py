#!/usr/bin/env python3
"""HTTP audit for the generated PTN site, including pages without JavaScript."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
import json
from pathlib import Path
import urllib.error
import urllib.request
from urllib.parse import urljoin,urlsplit,unquote
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
class Page(HTMLParser):
    def __init__(self):super().__init__();self.h1=0;self.canon=[];self.meta={};self.alts={};self.links=[];self.assets=[];self.jsonld=[];self.script=None;self.buffer='';self.lang='';self.title='';self.in_title=False
    def handle_starttag(self,t,a):
        d=dict(a)
        if t=='html':self.lang=d.get('lang','')
        if t=='h1':self.h1+=1
        if t=='title':self.in_title=True
        if t=='meta':self.meta[d.get('name',d.get('property',''))]=d.get('content','')
        if t=='link':
            if d.get('rel')=='canonical':self.canon.append(d.get('href'))
            if d.get('rel')=='alternate':self.alts[d.get('hreflang')]=d.get('href')
            if d.get('rel') in ('stylesheet','icon','preload'):self.assets.append(d.get('href',''))
        if t=='a':self.links.append(d.get('href',''))
        if t=='img':
            assert 'alt' in d and d.get('width') and d.get('height'),d
            self.assets.append(d.get('src',''))
        if t=='script':
            if d.get('src'):self.assets.append(d['src'])
            self.script=d.get('type');self.buffer=''
    def handle_endtag(self,t):
        if t=='title':self.in_title=False
        if t=='script':
            if self.script=='application/ld+json':self.jsonld.append(json.loads(self.buffer))
            self.script=None
    def handle_data(self,d):
        if self.in_title:self.title+=d
        if self.script=='application/ld+json':self.buffer+=d

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--base',default='http://127.0.0.1:3200');args=parser.parse_args();base=args.base.rstrip('/')
    def fetch(path,method='GET'):
        with urllib.request.urlopen(urllib.request.Request(base+path,method=method,headers={'User-Agent':'PTN-Site-Audit/1.0'}),timeout=20) as r:return r.status,r.geturl(),r.read()
    services=json.loads((ROOT/'content/services.json').read_text());routes=json.loads((ROOT/'content/routes.json').read_text());expected={r['path'] for r in routes}
    _,_,xml=fetch('/sitemap.xml');tree=ET.fromstring(xml)
    locations=[n.text for n in tree.findall('{*}url/{*}loc')]
    assert len(locations)==len(set(locations))==38,locations
    assert set(locations)=={'https://ptntextiles.com'+p for p in expected}
    def audit(r):
        path=r['path'];status,final,body=fetch(path);assert status==200 and final==base+path,(path,status,final)
        p=Page();p.feed(body.decode());canonical='https://ptntextiles.com'+path
        assert p.h1==1,(path,'h1',p.h1)
        assert p.canon==[canonical],(path,'canonical',p.canon)
        assert p.title and p.meta.get('description') and 'noindex' not in p.meta.get('robots',''),path
        assert p.meta.get('og:url')==canonical and p.meta.get('twitter:card')=='summary_large_image',path
        assert p.alts=={'es-MX':'https://ptntextiles.com'+r['alternates']['es'],'en':'https://ptntextiles.com'+r['alternates']['en'],'x-default':'https://ptntextiles.com'+r['alternates']['es']},path
        assert p.lang==('en' if path.startswith('/en/') else 'es-MX'),path
        assert p.jsonld and any(n.get('@type')=='Organization' for g in p.jsonld for n in g['@graph']),path
        assert any('contacto/' in h or '/en/contact/' in h for h in p.links),path
        assert any('https://wa.me/' in h for h in p.links) or path.endswith('contacto/') or path.endswith('contact/'),path
        assert 'Cargando PTN' not in body.decode() and '{{' not in body.decode(),path
        for h in p.links:
            u=urlsplit(h)
            if not u.scheme and not u.netloc and u.path:
                assert u.path in expected or (ROOT/unquote(u.path).lstrip('/')).is_file(),(path,'broken link',h)
        return path,p
    with ThreadPoolExecutor(max_workers=8) as pool:pages=dict(pool.map(audit,routes))
    titles=[p.title for p in pages.values()];descriptions=[p.meta['description'] for p in pages.values()]
    assert len(titles)==len(set(titles)) and len(descriptions)==len(set(descriptions)),'duplicate metadata'
    assets={a for p in pages.values() for a in p.assets if a.startswith('/')}
    with ThreadPoolExecutor(max_workers=8) as pool:
        for result in pool.map(lambda a:(a,fetch(a,'HEAD')[0]),assets):assert result[1]==200,result
    for path in ['/not-a-real-ptn-page/','/.git/config','/servicios/not-a-service/']:
        try:fetch(path)
        except urllib.error.HTTPError as e:assert e.code==404,(path,e.code)
        else:raise AssertionError((path,'expected 404'))
    assert len(services)==13
    print(json.dumps({'pages':len(pages),'service_pages':26,'sitemap_urls':len(locations),'assets':len(assets),'unique_metadata':True,'canonical_and_hreflang':True,'real_404':True,'html_without_js':True},ensure_ascii=False))
if __name__=='__main__':main()
