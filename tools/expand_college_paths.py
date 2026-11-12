"""Merge Philippine education classification and official registry program names.

No campus directory is created. Classification examples are explicitly distinguished
from registry-listed offerings. Pathway associations are exploratory, not eligibility.
"""
from pathlib import Path
import csv,json,re,hashlib,collections
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1];REF=ROOT/'data/reference';SRC=ROOT/'data/source/ph_reference'
DATE='2026-11-01'
def read(p):
 with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def write(p,rows,fields=None):
 with p.open('w',encoding='utf-8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields or list(rows[0]));w.writeheader();w.writerows(rows)
def key(name):return re.sub(r'[^a-z0-9]+',' ',name.casefold()).strip()
def clean(name):
 name=' '.join(name.split()).replace('Science in in ','Science in ')
 name=re.sub(r'^Bachelor in Science in ','Bachelor of Science in ',name,flags=re.I)
 if name.isupper():name=name.title().replace(' In ',' in ').replace(' Of ',' of ').replace(' And ',' and ')
 return name
catalog=read(REF/'program_catalog.csv');college={key(r['name']):r for r in catalog if r['kind']=='college'};evidence=[]
fields=list(catalog[0])
def add(name,url,status='official_listed'):
 name=clean(name)
 if not re.match(r'^(Bachelor|Associate|Doctor of (Medicine|Dental|Optometry|Veterinary)|Juris Doctor)',name,re.I):return
 if len(name)>650 or name in ('Bachelor of Arts','Bachelor of Science','Bachelor of Laws'):return
 k=key(name)
 evidence.append(dict(program_name=name,source_url=url,source_status=status,reviewed_on=DATE))
 if k not in college or college[k]['source_status']=='classification_listed' and status=='official_listed':
  college[k]=dict(program_id='college-'+hashlib.sha256(name.casefold().encode()).hexdigest()[:12],kind='college',name=name,aliases='',source_url=url,source_status=status,reviewed_on=DATE)
# PSCED is a national classification, not a claim that a campus offers every example today.
soup=BeautifulSoup((SRC/'psced.html').read_text(),'html.parser')
for tr in soup.select('tr'):
 cells=tr.find_all(['td','th'],recursive=False)
 if len(cells)==2 and not cells[0].find('table'):
  name=cells[0].get_text(' ',strip=True)
  if len(name)<240:add(name,'https://psa.gov.ph/classification/psced/detailedfield','classification_listed')
# Official CAR and Region XI program pages.
for filename,url in [('ched_car.html','https://chedcar.com/program-and-discipline-code/'),('ched_inventory.html','https://ro11.ched.gov.ph/programs-inventory/')]:
 soup=BeautifulSoup((SRC/filename).read_text(),'html.parser')
 for el in soup.select('li, td'):
  if el.find(['li','table']):continue
  text=el.get_text(' ',strip=True)
  if len(text)<240:add(text,url)
# Region III's public registry. Only actual degree records, not inactive programs.
registry=json.loads((SRC/'ched_region3_programs.json').read_text())['data']
for row in registry:
 if row.get('program_status')=='ACTIVE' and row.get('degree_type') in ('Baccalaureate','Pre-Baccalaureate','Post-Baccalaureate'):
  add(row['program_name'],'https://region3.ched.gov.ph/resources/program-registry')
rows=sorted(college.values(),key=lambda r:r['name'].casefold())
write(REF/'college_program_catalog.csv',rows,fields)
write(REF/'college_program_evidence.csv',evidence)
write(REF/'program_catalog.csv',rows+[r for r in catalog if r['kind']=='tesda'],fields)
# Only reasonable-length single-program labels can be mapped into a result card.
usable=[r for r in rows if len(r['name'])<165 and r['name'].count(',')<3 and not re.search(r'formerly|changed to|straight bachelor',r['name'],re.I)]
def find(name):
 k=key(name)
 exact=college.get(k)
 if exact and exact in usable:return exact['name']
 # Prefer current registry names over classification examples; no fabricated names.
 candidates=[r for r in usable if key(r['name'])==k or key(r['name']).startswith(k+' major in') or key(r['name']).startswith(k+' with')]
 if not candidates:return None
 return min(candidates,key=lambda r:(r['source_status']!='official_listed',len(r['name'])))['name']
BS=lambda n:'Bachelor of Science in '+n
BA=lambda n:'Bachelor of Arts in '+n
SPECIFIC=[
(r'landscape architect',['Bachelor of Landscape Architecture',BS('Landscape Architecture')]),
(r'environmental engineer|water/wastewater engineer',[BS('Environmental Engineering'),BS('Civil Engineering')]),
(r'forensic science technician',[BS('Forensic Science'),BS('Biology')]),
(r'embalmer|crematory|mortician|undertaker|funeral attendant',[BS('Biology'),BS('Entrepreneurship')]),
(r'information security|cyber|penetration tester|digital forensics|blockchain|web administrator|data warehousing|document management specialist',[BS('Computer Science'),BS('Information Technology'),BS('Information Systems')]),
(r'coroner|forensic science technician',[BS('Forensic Science'),BS('Biology'),'Doctor of Medicine']),
(r'nurse|nursing|psychiatric aide|orderlies',[BS('Nursing')]),
(r'obstetrician|gynecologist|allergist|immunologist|acupuncturist',[BS('Biology'),'Doctor of Medicine']),
(r'dietetic|nutrition',[BS('Nutrition and Dietetics')]),
(r'medical record|medical transcription|health informatics',[BS('Health Information Management'),BS('Information Technology'),BS('Office Administration')]),
(r'emergency medical|paramedic',[BS('Nursing'),BS('Emergency Medical Services')]),
(r'art therapist',[BS('Psychology'),'Bachelor of Fine Arts']),
(r'materials (engineer|scientist)|metallurg',[BS('Materials Engineering'),BS('Metallurgical Engineering'),BS('Chemistry')]),
(r'water resource|water/wastewater|sustainability|climate change|recycling',[BS('Environmental Science'),BS('Environmental Engineering'),BS('Civil Engineering')]),
(r'survey researcher|social science research',[BS('Statistics'),BA('Sociology')]),
(r'bioinformatics',[BS('Biology'),BS('Computer Science')]),
(r'natural sciences manager|clinical research coordinator',[BS('Biology'),BS('Chemistry')]),
(r'food science technician|quality control analyst',[BS('Food Technology'),BS('Chemistry')]),
(r'operations research',[BS('Mathematics'),BS('Statistics'),BS('Industrial Engineering')]),
(r'occupational health|occupational safety',[BS('Public Health'),BS('Nursing'),BS('Industrial Engineering')]),
(r'producers and directors|talent director|media programming|motion picture|audio and video',[BA('Communication'),'Bachelor of Multimedia Arts']),
(r'interior design',[BS('Interior Design')]),
(r'fashion|costume|sew|textile|tailor|dressmak',[BS('Clothing Technology'),'Bachelor of Industrial Technology']),
(r'aerospace|aircraft|aviation|avionics',[BS('Aeronautical Engineering'),BS('Aircraft Maintenance Technology'),BS('Air Transportation')]),
(r'agricultural engineer',[BS('Agricultural and Biosystems Engineering')]),
(r'bioengineer|biomedical engineer',[BS('Biomedical Engineering'),BS('Biology')]),
(r'computer hardware engineer',[BS('Computer Engineering')]),
(r'nuclear|physicist|astronomer|photonics',[BS('Physics'),BS('Applied Physics')]),
(r'robotics|mechatronic',[BS('Mechatronics Engineering'),BS('Robotics Engineering'),BS('Mechanical Engineering')]),
(r'petroleum|geoscientist|geologist',[BS('Geology'),BS('Petroleum Engineering'),BS('Mining Engineering')]),
(r'geograph|geographic information|cartograph|surveying',[BS('Geography'),BS('Geodetic Engineering')]),
(r'environmental|hydrolog|conservation scientist|industrial ecologist',[BS('Environmental Science'),BS('Forestry'),BS('Biology')]),
(r'forester|forest|logging|logger|^faller',[BS('Forestry'),BS('Agroforestry')]),
(r'animal scientist|zoolog|animal breeder',[BS('Animal Science'),BS('Biology'),BS('Agriculture')]),
(r'molecular|microbiolog|genetic|biochem|biolog|medical scientist|epidemiolog',[BS('Molecular Biology and Biotechnology'),BS('Biology'),BS('Microbiology')]),
(r'soil|plant scientist|agronom|crop',[BS('Agriculture'),BS('Horticulture')]),
(r'atmospheric|space scientist',[BS('Meteorology'),BS('Physics')]),
(r'urban.*planner|regional planner|transportation planner',[BS('Environmental Planning'),BS('Geography'),BS('Architecture')]),
(r'anthropolog|archeolog',[BA('Anthropology'),BA('History')]),
(r'sociolog',[BA('Sociology'),BS('Sociology')]),
(r'historian',[BA('History')]),
(r'political scientist|legislator|public administrator',[BA('Political Science'),'Bachelor of Public Administration']),
(r'counselor|therapist.*family|social.*human service|community health',[BS('Psychology'),BS('Social Work')]),
(r'clergy|religious|theolog',[BA('Theology'),BA('Religious Studies'),BA('Philosophy')]),
(r'judge|judicial|lawyer|arbitrator|legal',[BS('Legal Management'),BA('Political Science'),'Juris Doctor']),
(r'curator|archivist|museum',[BA('History'),BA('Anthropology'),'Bachelor of Library and Information Science']),
(r'library|librarian',['Bachelor of Library and Information Science']),
(r'designer|craft artist|floral|display.*window',['Bachelor of Fine Arts',BS('Industrial Design'),'Bachelor of Multimedia Arts']),
(r'actor|dancer|choreograph|performer',[BA('Theater Arts'),'Bachelor of Performing Arts','Bachelor of Fine Arts']),
(r'musician|singer|composer|music director',['Bachelor of Music']),
(r'sports|athlete|coach|recreation|fitness',['Bachelor of Sports Science',BS('Exercise and Sports Science'),'Bachelor of Physical Education']),
(r'sound|lighting|broadcast|media technical',[BA('Broadcasting'),BA('Communication'),'Bachelor of Multimedia Arts']),
(r'optometrist|orthoptist',['Doctor of Optometry']),
(r'physician|surgeon|cardiologist|dermatologist|neurologist|podiatrist|psychiatrist|anesthesiologist|radiologist|urologist|hospitalist|ophthalmologist',[BS('Biology'),BS('Medical Laboratory Science'),'Doctor of Medicine']),
(r'speech.language|audiologist',[BS('Speech Pathology'),BS('Speech Language Pathology')]),
(r'respiratory',[BS('Respiratory Therapy')]),
(r'radiologic|nuclear medicine|medical dosimetrist|sonograph|cardiovascular technologist',[BS('Radiologic Technology')]),
(r'dental|dentist|orthodontist|prosthodontist',['Doctor of Dental Medicine',BS('Dental Hygiene')]),
(r'occupational therap',[BS('Occupational Therapy')]),
(r'physical therap|rehabilitation|chiropract',[BS('Physical Therapy')]),
(r'cytogenetic|cytotechn|histolog|histotechn|phlebotom|medical equipment preparer|endoscop',[BS('Medical Laboratory Science'),BS('Medical Technology')]),
(r'veterinar|animal care|animal train',['Doctor of Veterinary Medicine',BS('Animal Science')]),
(r'police|correction|detective|security|firefight|fire inspector|bailiff|warden|border protection',[BS('Criminology'),BS('Public Safety Administration')]),
(r'childcare|nann|teaching assistant',['Bachelor of Early Childhood Education','Bachelor of Elementary Education']),
(r'landscap|groundskeep|tree trim',[BS('Horticulture'),BS('Agriculture')]),
(r'fashion|costume|sew|textile|tailor|dressmak',[BS('Clothing Technology'),'Bachelor of Industrial Technology']),
(r'beaut|hair|barber|manicur|skincare|massage',['Bachelor of Industrial Technology',BS('Entrepreneurship')]),
(r'fish|aquaculture',[BS('Fisheries'),BS('Marine Biology')]),
(r'marine|ship|sailor|watercraft|motorboat',[BS('Marine Transportation'),BS('Marine Engineering')]),
(r'truck|bus driver|taxi|chauffeur|locomotive|railroad|subway|traffic|transportation',[BS('Transportation Management'),BS('Business Administration')]),
]
FAMILIES={
 '11':[BS('Business Administration'),BS('Management')],
 '13':[BS('Business Administration'),BS('Entrepreneurship')],
 '15':[BS('Information Technology'),BS('Computer Science'),BS('Information Systems')],
 '17':[BS('Mechanical Engineering'),BS('Industrial Engineering'),'Bachelor of Industrial Technology'],
 '19':[BS('Biology'),BS('Environmental Science')],
 '21':[BS('Social Work'),BS('Psychology')],
 '23':[BS('Legal Management'),BA('Political Science')],
 '25':['Bachelor of Secondary Education','Bachelor of Elementary Education'],
 '27':[BA('Communication'),'Bachelor of Fine Arts'],
 '29':[BS('Health Sciences'),BS('Biology')],
 '31':[BS('Health Sciences'),BS('Nursing')],
 '33':[BS('Criminology'),BS('Public Safety Administration')],
 '35':[BS('Hospitality Management'),BS('Culinary Management')],
 '37':[BS('Environmental Science'),'Bachelor of Industrial Technology'],
 '39':[BS('Hospitality Management'),BS('Entrepreneurship')],
 '41':[BS('Business Administration'),BS('Entrepreneurship')],
 '43':[BS('Office Administration'),BS('Business Administration')],
 '45':[BS('Agriculture'),'Bachelor of Agricultural Technology'],
 '47':['Bachelor of Industrial Technology',BS('Civil Engineering')],
 '49':['Bachelor of Industrial Technology',BS('Mechanical Engineering')],
 '51':['Bachelor of Industrial Technology',BS('Industrial Engineering')],
 '53':[BS('Transportation Management'),BS('Business Administration')],
}
old={r['onet_code']:r for r in read(SRC/'college_base_mappings.csv')};occupations=read(REF/'occupation_catalog.csv');audit=[];mapped=[]
for o in occupations:
 previous=[x.strip() for x in old[o['onet_code']]['programs'].split('|') if x.strip()]
 names=[];rule='existing curated pathway'
 for pattern,paths in SPECIFIC:
  if re.search(pattern,o['title'],re.I):
   names=[n for n in (find(p) for p in paths) if n];rule=pattern
   if names:break
 if not names:names=[n for n in (find(p) for p in previous) if n]
 if not names:
  names=[n for n in (find(p) for p in FAMILIES.get(o['onet_code'][:2],[])) if n];rule='broad occupational-family study exploration'
 names=list(dict.fromkeys(names))
 # Subject teachers need their discipline, rather than a generic education-only pathway.
 if 'Postsecondary' in o['title']:
  subject=o['title'].split(' Teachers')[0].split(',')[0]
  candidates=[r for r in usable if key(subject) in key(r['name']) and r['name'].startswith(('Bachelor','Associate'))]
  if candidates:names=list(dict.fromkeys([r['name'] for r in sorted(candidates,key=lambda r:(r['source_status']!='official_listed',len(r['name'])))[:3]]+names))[:4];rule='postsecondary subject study exploration; advanced study usually required'
 row=dict(old[o['onet_code']]);row['programs']=' | '.join(names);row['data_status']='curated';row['reviewed_on']=DATE;mapped.append(row)
 for n in names:
  p=college[key(n)]
  audit.append(dict(onet_code=o['onet_code'],occupation_title=o['title'],program_name=n,pathway_type='exploratory_study_option',rule=rule,program_source=p['source_url'],source_status=p['source_status'],note='Related study option, not a claim this degree alone qualifies someone for this occupation. Classification examples do not prove a current school offering.'))
write(REF/'college_programs.csv',mapped);write(REF/'college_pathway_audit.csv',audit)
# Refine obvious training specialisms while retaining unmapped careers honestly.
tesda=read(REF/'tesda_programs.csv');active={r['name'] for r in catalog if r['kind']=='tesda'}
training_rules=[
 (r'skincare|skin care',['Beauty Care (Skin Care) Services NC II','Advanced Skin Care Services Level III']),
 (r'manicur|pedicur',['Beauty Care (Nail Care) Services NC II','Beauty Care (Nail Enhancement Technology) Services NC III']),
 (r'dietetic|nutrition',['Community Nutrition Services NC II']),
]
for row in tesda:
 for pattern,names in training_rules:
  if re.search(pattern,row['occupation_title'],re.I):
   selected=[name for name in names if name in active]
   if selected:row['qualifications']=' | '.join(selected);row['reviewed_on']=DATE;row['data_status']='curated'
   break
write(REF/'tesda_programs.csv',tesda)
summary=dict(college_catalog_titles=len(rows),registry_or_official_listed=sum(r['source_status']=='official_listed' for r in rows),classification_examples=sum(r['source_status']=='classification_listed' for r in rows),source_program_evidence_records=len(evidence),region3_registry_records=len(registry),mapped_occupations=sum(bool(r['programs']) for r in mapped),occupation_total=len(occupations),study_associations=len(audit))
(SRC/'college_coverage.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
