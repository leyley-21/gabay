"""Rebuild reference CSVs from the dated local source snapshot.
Requires optional beautifulsoup4; back up custom mappings before use.
"""
from bs4 import BeautifulSoup
from pathlib import Path
import csv,json,hashlib,re,collections
BASE=Path(__file__).resolve().parents[1]; CACHE=BASE/'data/source/ph_reference'; REF=BASE/'data/reference'
TODAY='2026-10-31'
def write(name,rows,fields=None):
 with (REF/name).open('w',encoding='utf-8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields or list(rows[0]));w.writeheader();w.writerows(rows)
programs={}
def add(kind,name,url,aliases=''):
 name=' '.join(name.split()).replace('Science in in ','Science in ')
 if not name or name in ('Bachelor of Arts','Bachelor of Laws'):return
 key=(kind,name.casefold());id=kind+'-'+hashlib.sha256(name.casefold().encode()).hexdigest()[:12]
 if key not in programs:programs[key]=dict(program_id=id,kind=kind,name=name,aliases=aliases,source_url=url,source_status='official_listed',reviewed_on=TODAY)
for n,url in [('ched','https://ro11.ched.gov.ph/programs-per-hei/'),('curricula','https://legacy.ched.gov.ph/sample-suggested-curricula-undergraduate-programs-different-disciplines-aligned-outcomes-based-education/')]:
 s=BeautifulSoup((CACHE/(n+'.txt')).read_text(),'html.parser')
 for t in s.select('table'):
  for x in t.select('td'):
   name=x.get_text(' ',strip=True)
   if name.startswith(('Bachelor','Doctor of Dental','Doctor of Optometry','Doctor of Veterinary')):add('college',name,url)
s=BeautifulSoup((CACHE/'tesda_all.txt').read_text(),'html.parser');names=[]
for tr in s.select('table tr'):
 td=tr.find('td')
 if td and tr.select_one('a[href*="/TRs/"], a[href*="/CS/"]'):
  name=td.get_text(' ',strip=True)
  if re.search(r'\b(NC [IVX]+|LEVEL [IVX]+)\b',name,re.I) and not re.search(r'supersed|amend|migrat|deleted|repeal',name,re.I):
   names.append(name);add('tesda',name,'https://www.tesda.gov.ph/download')
rows=sorted(programs.values(),key=lambda x:(x['kind'],x['name'].casefold()));write('program_catalog.csv',rows)
print('CATALOG',dict(collections.Counter(x['kind'] for x in rows)))
print('TESDA samples',names[:10],names[-10:])
# preserve original mappings as migration evidence, outside imported references.
archive=BASE/'data/legacy_reference';archive.mkdir(exist_ok=True)
for name in ['college_programs.csv','tesda_programs.csv']:
 if not (archive/name).exists():(archive/name).write_bytes((REF/name).read_bytes())
# Exact-title occupational families, ordered from specific to broad. These are
# advisory pathway mappings, not accreditation, admission or eligibility evidence.
BS=lambda n:'Bachelor of Science in '+n
BA=lambda n:'Bachelor of Arts in '+n
RULES=[
(r'preschool|kindergarten|early childhood',[ 'Bachelor of Early Childhood Education'],['Early Childhood Care and Development Services NC III']),
(r'elementary school teacher',['Bachelor of Elementary Education'],[]),
(r'secondary school teacher|middle school teacher',['Bachelor of Secondary Education'],[]),
(r'special education teacher',['Bachelor of Special Needs Education'],[]),
(r'vocational education|career/technical education',['Bachelor of Technical-Vocational Teacher Education','Bachelor of Technology and Livelihood Education'],[]),
(r'librari|archivist',['Bachelor of Library and Information Science'],[]),
(r'teacher|instructional coordinator|education administrator',['Bachelor of Secondary Education','Bachelor of Elementary Education'],[]),
(r'software|programmer|web developer|web and digital interface|computer.*research',[BS('Computer Science'),BS('Information Technology'),BS('Information Systems')],['Computer Systems Servicing NC II']),
(r'data scientist|statistician|mathematician|actuar',[BS('Data Science'),BS('Statistics'),BS('Mathematics')],[]),
(r'information security|cyber',[BS('Information Technology'),BS('Computer Science')],['Cyber Threat Monitoring NC I','Cyber Threat Mitigation NC II']),
(r'computer|network|database',[BS('Information Technology'),BS('Computer Engineering')],['Computer Systems Servicing NC II']),
(r'accountant|auditor|bookkeep|payroll',[BS('Accountancy'),BS('Management Accounting'),BS('Accounting Information Systems')],['Bookkeeping NC III']),
(r'financial|finance|credit|loan|investment|insurance underwriter',[BS('Finance'),BS('Business Administration')],['Bookkeeping NC III']),
(r'human resource|recruit|labor relations',[BS('Human Resource Management'),BS('Psychology')],[]),
(r'market research|marketing|advertis|public relations',[BS('Business Administration'),BA('Communication')],['Contact Center Services NC II']),
(r'real estate',[BS('Real Estate Management')],[]),
(r'logistic|purchasing|supply chain|cargo|freight|customs',[BS('Customs Administration'),BS('Business Administration')],['Warehousing Services NC II']),
(r'office|administrative assistant|secretar|receptionist|file clerk|data entry',[BS('Office Administration'),BS('Information Systems')],['Contact Center Services NC II','Bookkeeping NC III']),
(r'sales|retail|customer service|cashier|telemark|business|chief executive|general and operations manager',[BS('Business Administration'),BS('Entrepreneurship')],['Contact Center Services NC II','Entrepreneurship NC II']),
(r'registered nurse|nurse practitioner|nurse anesthetist|nurse midwi',[BS('Nursing')],[]),
(r'nursing assistant|personal care aide|home health aide|caregiver',[BS('Nursing')],['Caregiving (Elderly) NC II','Health Care Services NC II','Caregiving (Clients with Special Needs) NC II']),
(r'midwi',[BS('Midwifery'),BS('Nursing')],[]),
(r'medical.*laboratory|clinical.*laboratory|phlebotom',[BS('Medical Laboratory Science'),BS('Medical Technology')],[]),
(r'pharmac',[BS('Pharmacy')],['Pharmacy Services NC III']),
(r'physical therap',[BS('Physical Therapy')],[]),
(r'occupational therap',[BS('Occupational Therapy')],[]),
(r'respiratory therap',[BS('Respiratory Therapy')],[]),
(r'radiologic|radiation therap|nuclear medicine',[BS('Radiologic Technology')],[]),
(r'dietitian|nutrition',[BS('Nutrition and Dietetics')],['Community Nutrition Services NC II']),
(r'dentist|dental',['Doctor of Dental Medicine'],['Dental Laboratory Technology Services NC I']),
(r'optometrist|optician',['Doctor of Optometry'],[]),
(r'veterinar',['Doctor of Veterinary Medicine',BS('Agriculture')],['Animal Health Care and Management NC III']),
(r'psycholog|mental health counselor|marriage and family therapist',[BS('Psychology'),BA('Psychology')],[]),
(r'social worker|social.*service|community health',[BS('Social Work'),BS('Community Development')],['Community Nutrition Services NC II']),
(r'childcare|nann',[ 'Bachelor of Early Childhood Education'],['Early Childhood Care and Development Services NC III','Caregiving (Newborn to Pre-Schooler) NC II']),
(r'physician|surgeon|pediatrician|anesthesiologist|psychiatrist',[BS('Biology'),BS('Medical Laboratory Science')],[]),
(r'civil engineer|construction manager|surveyor|surveying',[BS('Civil Engineering'),BS('Geodetic Engineering')],['Technical Drafting NC II']),
(r'architect|landscape architect',[BS('Architecture'),'Bachelor of Landscape Architecture'],['Technical Drafting NC II']),
(r'interior design',[BS('Interior Design')],['Technical Drafting NC II']),
(r'mechanical engineer|industrial engineer',[BS('Mechanical Engineering'),BS('Industrial Engineering')],['Technical Drafting NC II']),
(r'electrical engineer',[BS('Electrical Engineering')],['Electrical Installation and Maintenance NC II']),
(r'electronic|telecommunication',[BS('Electronics Engineering')],['Electronic Products Assembly and Servicing NC II']),
(r'chemical engineer|chemist|chemical technician',[BS('Chemical Engineering'),BS('Chemistry')],[]),
(r'mining|geolog|petroleum engineer',[BS('Mining Engineering'),BS('Geology')],[]),
(r'environmental|conservation scientist|forester',[BS('Environmental Science'),BS('Forestry')],[]),
(r'biolog|microbiolog|biochem|zoolog',[BS('Biology'),BS('Chemistry')],[]),
(r'food scientist|food.*technolog',[BS('Food Technology')],['Food Processing NC II']),
(r'agricultur|farmer|farmworker|crop|horticultur',[BS('Agriculture'),'Bachelor of Agricultural Technology'],['Agricultural Crops Production NC II','Organic Agriculture Production NC II']),
(r'animal.*(breeder|trainer|caretaker)|ranch|livestock',[BS('Agriculture')],['Animal Production (Ruminants) NC II','Animal Production (Swine) NC II']),
(r'fish|aquacultur',[BS('Fisheries'),BS('Marine Biology')],['Aquaculture (Grow-Out Operation) NC II']),
(r'graphic design|animator|special effects|multimedia',['Bachelor of Multimedia Arts','Bachelor of Fine Arts',BS('Entertainment and Multimedia Computing')],['2D Animation NC III','3D Animation NC III','Animation NC II']),
(r'artist|art director|craft artist|painter.*illustrator',['Bachelor of Fine Arts','Bachelor of Multimedia Arts'],['Visual Graphic Design NC III']),
(r'photograph|camera operator|film|video editor',[BA('Communication'),'Bachelor of Multimedia Arts'],['Photography NC II']),
(r'writer|author|journalist|reporter|editor|broadcast|announcer',[BA('Communication'),BA('Journalism'),BA('English')],[]),
(r'music|singer|composer',['Bachelor of Music'],[]),
(r'interpreter|translator',[BA('English Language'),BA('Filipino')],[]),
(r'lawyer|judge|paralegal|legal assistant',[BA('Political Science'),BS('Legal Management')],[]),
(r'police|detective|criminal investigator|correctional|security guard',[BS('Criminology')],['Security Services NC II']),
(r'firefighter|fire inspector',[BS('Criminology'),BS('Disaster Resiliency and Management')],[]),
(r'political scientist|legislator|government|public administration',['Bachelor of Public Administration',BA('Political Science')],[]),
(r'economist',[BS('Economics'),BA('Economics')],[]),
(r'anthropolog|sociolog|historian|philosoph',[BA('Anthropology'),BA('Sociology'),BA('History')],[]),
(r'clergy|religious',[BA('Theology'),BA('Christian Education')],[]),
(r'chef|cook|baker|food preparation',[BS('Culinary Management'),BS('Hospitality Management')],['Cookery NC II','Bread and Pastry Production NC II']),
(r'food service|waiter|waitress|bartender|barista|dining',[BS('Hospitality Management')],['Food and Beverage Services NC II','Bartending NC II','Barista NC II']),
(r'hotel|lodging|housekeep|maid',[BS('Hospitality Management')],['Housekeeping NC II','Front Office Services NC II']),
(r'travel|tour guide|flight attendant',[BS('Tourism Management')],['Tourism Promotion Services NC II','Tour Guiding Services NC II']),
(r'automotive|auto.*mechanic|motorcycle|diesel.*mechanic|bus.*mechanic',['Bachelor of Industrial Technology',BS('Mechanical Engineering')],['Automotive Servicing NC II','Automotive Servicing (Engine Repair) NC II','Automotive Servicing (Chassis Repair) NC II']),
(r'aircraft|avionics|pilot',[BS('Aircraft Maintenance Technology'),BS('Aeronautical Engineering')],[]),
(r'ship|marine engineer|sailor|boat captain|water transportation',[BS('Marine Engineering'),BS('Marine Transportation')],['Able Seafarer Deck NC II (II-5)','Able Seafarer Engine NC II (III-5)']),
(r'electrician|electrical.*installer|power.*installer',['Bachelor of Industrial Technology',BS('Electrical Engineering')],['Electrical Installation and Maintenance NC II']),
(r'plumb|pipefit|steamfit',['Bachelor of Industrial Technology'],['Plumbing NC II']),
(r'carpenter|woodwork|cabinetmaker',['Bachelor of Industrial Technology'],['Carpentry NC II']),
(r'weld|solder|braze',['Bachelor of Industrial Technology'],['Shielded Metal Arc Welding (SMAW) NC II','Gas Metal Arc Welding (GMAW) NC II']),
(r'mason|brickmason|cement mason|concrete finisher',['Bachelor of Industrial Technology'],['Masonry NC II']),
(r'construction painter|painter.*construction',['Bachelor of Industrial Technology'],['Construction Painting NC II']),
(r'heating|air conditioning|refrigeration',['Bachelor of Industrial Technology',BS('Mechanical Engineering')],['Refrigeration and Air-Conditioning Servicing (DomRAC) NC II']),
(r'machinist|tool and die|cnc|machine tool',['Bachelor of Industrial Technology',BS('Mechanical Engineering')],['CNC Lathe Machine Operation NC II','CNC Milling Machine Operation NC II']),
(r'sew|tailor|dressmak|textile|upholster',['Bachelor of Industrial Technology'],['Dressmaking NC II','Tailoring NC II']),
(r'hairdress|cosmetolog|barber|manicur|skincare',[],['Hairdressing NC II','Beauty Care (Nail Care) Services NC II','Barbering NC II']),
(r'massage',[],['Massage Therapy NC II']),
(r'truck driver|bus driver|chauffeur|taxi driver|delivery.*driver',[],['Driving NC II','Driving (Passenger Bus/Straight Truck) NC III']),
(r'fitness|coach|athlete|recreation',['Bachelor of Physical Education','Bachelor of Sports Science'],[]),
]
# Case-insensitive exact catalog names only; absent qualifications are not invented.
lookup={(p['kind'],p['name'].casefold()):p for p in rows}
occupations=list(csv.DictReader((REF/'occupation_catalog.csv').open()))
links=[];outputs={'college':[],'tesda':[]};coverage=collections.Counter()
for o in occupations:
 college=[];tesda=[];rule='unmapped'
 for pattern,c,t in RULES:
  if re.search(pattern,o['title'],re.I):college,tesda,rule=c,t,pattern;break
 for kind,names0 in [('college',college),('tesda',tesda)]:
  selected=[]
  for name in names0:
   p=lookup.get((kind,name.casefold()))
   if p and p['name'] not in selected:
    selected.append(p['name']);links.append(dict(onet_code=o['onet_code'],program_id=p['program_id'],mapping_status='curated',mapping_note='Advisory occupational-family mapping; local expert review required. Not an admission or licensing decision.'))
  if selected:coverage[kind]+=1
  field='programs' if kind=='college' else 'qualifications'
  outputs[kind].append(dict(onet_code=o['onet_code'],occupation_title=o['title'],**{field:' | '.join(selected)},country='PH',data_status='curated',source_url='',reviewed_on=TODAY))
write('college_programs.csv',outputs['college']);write('tesda_programs.csv',outputs['tesda'])
geo=json.loads((CACHE/'provinces.geojson').read_text())
features=[]
def roundcoords(x):
 if isinstance(x,list):
  if x and isinstance(x[0],(int,float)):return [round(v,5) for v in x]
  return [roundcoords(v) for v in x]
for f in geo['features']:
 coords=roundcoords(f['geometry']['coordinates']);points=[]
 def collect(x):
  if x and isinstance(x[0],(int,float)):points.append(x)
  else:
   for v in x:collect(v)
 collect(coords)
 features.append(dict(type='Feature',properties={'name':f['properties']['shapeName']},bbox=[min(v[0] for v in points),min(v[1] for v in points),max(v[0] for v in points),max(v[1] for v in points)],geometry={'type':f['geometry']['type'],'coordinates':coords}))
folder=BASE/'data/geography';folder.mkdir(exist_ok=True)
(folder/'ph_provinces.geojson').write_text(json.dumps(dict(type='FeatureCollection',features=features),separators=(',',':')))
(folder/'metadata.json').write_bytes((CACHE/'province_metadata.json').read_bytes())
print('COVERAGE',dict(coverage),'LINKS',len(links),'distinct mapped',len(set(x['program_id'] for x in links)))

from refresh_tesda_catalog import refresh
refresh()

# Restore the expanded, source-linked Philippine college catalog and pathways.
import expand_college_paths
