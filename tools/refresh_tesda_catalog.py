"""Refresh the complete TESDA training-regulations and competency-standards lists.

Use --download to fetch the official page; otherwise rebuild from the bundled
snapshot. Original list records, including superseded titles, are kept in a
separate auditable CSV. Only current/unmarked titles enter the active catalog.
Requires beautifulsoup4 from requirements-maintenance.txt, not app startup.
"""
import argparse,csv,hashlib,json,re
from datetime import date
from pathlib import Path
from urllib.parse import urljoin,quote,urlsplit,urlunsplit
from urllib.request import Request,urlopen
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
SOURCE='https://www.tesda.gov.ph/download'

def write_csv(path,rows,fields):
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)

def refresh(download=False):
    source=ROOT/'data/source/ph_reference/tesda_all.txt'
    if download:
        with urlopen(Request(SOURCE,headers={'User-Agent':'ALS-Gabay Reference Update/1.1'}),timeout=30) as r:body=r.read(2_000_000)
        if b'Training Regulations' not in body or b'Competency Standards' not in body:raise ValueError('TESDA source layout changed.')
        source.write_bytes(body)
    soup=BeautifulSoup(source.read_text(encoding='utf-8'),'html.parser');records=[];today=date.today().isoformat()
    for table in soup.select('table'):
        h=table.find_previous(['h2','h3','h4','h5']);group=h.get_text(' ',strip=True) if h else ''
        if group not in ('Training Regulations','Competency Standards'):continue
        for tr in table.select('tr'):
            td=tr.find('td');a=tr.select_one('a[href]')
            if not td or not a:continue
            name=' '.join(td.get_text(' ',strip=True).split());url=urljoin(SOURCE,a['href']);parts=urlsplit(url)
            url=urlunsplit((parts.scheme,parts.netloc,quote(parts.path,safe='/%()_-.'),parts.query,''))
            status='superseded' if re.search(r'supersed|repeal|deleted|migrat',name,re.I) else 'listed'
            records.append(dict(program_name=name,list_type=group,list_status=status,source_url=url,official_list_url=SOURCE,reviewed_on=today))
    if len(records)<600:raise ValueError('Unexpectedly short TESDA list; existing catalog not replaced.')
    fields=['program_name','list_type','list_status','source_url','official_list_url','reviewed_on']
    write_csv(ROOT/'data/reference/tesda_official_programs.csv',records,fields)
    catalog=ROOT/'data/reference/program_catalog.csv'
    with catalog.open(encoding='utf-8-sig',newline='') as f:reader=csv.DictReader(f);cols=reader.fieldnames;college=[r for r in reader if r['kind']=='college']
    active={}
    # Training Regulations take precedence where the same title occurs in both lists.
    for row in sorted(records,key=lambda r:r['list_type']=='Training Regulations',reverse=True):
        if row['list_status']!='listed':continue
        name=row['program_name'];key=name.casefold()
        if key not in active:
            active[key]=dict(program_id='tesda-'+hashlib.sha256(key.encode()).hexdigest()[:12],kind='tesda',name=name,aliases='',source_url=row['source_url'],source_status='official_listed',reviewed_on=today)
    write_csv(catalog,sorted(college+list(active.values()),key=lambda r:(r['kind'],r['name'].casefold())),cols)
    manifest=source.parent/'sha256.json'
    entries=json.loads(manifest.read_text()) if manifest.exists() else {}
    entries[source.name]=hashlib.sha256(source.read_bytes()).hexdigest();manifest.write_text(json.dumps(entries,indent=2))
    print(f'TESDA official list records: {len(records)}; active distinct catalog names: {len(active)}')
    return records,active
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--download',action='store_true');a=p.parse_args();refresh(a.download)
