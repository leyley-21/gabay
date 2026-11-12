"""Expand role-specific pathways using exact names from bundled Philippine sources.

Program existence is evidenced by the registry; occupational relevance is an
editorial association, not evidence of eligibility or a current campus offering.
No fabricated degrees/NC titles, automatic fuzzy matching, or wages are added.
"""
import csv, re, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / 'data/reference'
DATE = '2026-11-12'

def read(name):
    with (REF/name).open(encoding='utf-8-sig', newline='') as f: return list(csv.DictReader(f))

def write(name, rows):
    with (REF/name).open('w', encoding='utf-8', newline='') as f:
        w=csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

BS=lambda name: 'Bachelor of Science in '+name
BA=lambda name: 'Bachelor of Arts in '+name
# More specific occupational titles take priority over broad family names.
RULES = [
(r'video game designer|game developer', [BS('Computer Science'),BS('Information Technology'),BS('Entertainment and Multimedia Computing'),'Bachelor of Multimedia Arts'], ['Game Programming NC III','2D Game Art Development NC III','3D Game Art Development NC III']),
(r'web developer|web and digital interface', [BS('Information Technology'),BS('Computer Science'),BS('Information Systems'),BS('Entertainment and Multimedia Computing'),'Bachelor of Multimedia Arts'], ['Web Development NC III','Programming (JAVA) NC III','Programming (.Net Technology) NC III','Visual Graphic Design NC III']),
(r'software|computer programmer|computer.*research', [BS('Computer Science'),BS('Information Technology'),BS('Information Systems'),BS('Computer Engineering'),BS('Mathematics')], ['Programming (JAVA) NC III','Programming (.Net Technology) NC III','Programming (Python) Level III','Web Development NC III','Programming (Oracle Database) NC III']),
(r'information security|cyber|penetration tester|digital forensics', [BS('Computer Science'),BS('Information Technology'),BS('Information Systems'),BS('Computer Engineering')], ['Cyber Threat Monitoring NC I','Cyber Threat Mitigation NC II','Computer Security Incident Handling Level I','Computer Security Incident Handling Level II']),
(r'data scientist|statistician|mathematician|actuar|operations research', [BS('Statistics'),BS('Mathematics'),BS('Applied Mathematics'),BS('Data Science'),BS('Computer Science')], ['Programming (Python) Level III','Data Analytics Level III']),
(r'database|data warehousing', [BS('Computer Science'),BS('Information Technology'),BS('Information Systems'),BS('Computer Engineering')], ['Programming (Oracle Database) NC III','Programming (Python) Level III']),
(r'computer.*support|network.*(support|administrator|architect)|computer systems analyst|web administrator', [BS('Information Technology'),BS('Computer Engineering'),BS('Computer Science'),BS('Information Systems')], ['Computer Systems Servicing NC II','Cyber Threat Monitoring NC I']),
(r'accountant|auditor|bookkeep|payroll', [BS('Accountancy'),BS('Management Accounting'),BS('Accounting Information Systems'),BS('Business Administration')], ['Bookkeeping NC III','Computerized Bookkeeping and Financial System Level IV']),
(r'financial|finance|credit analyst|loan officer|investment|insurance underwriter', [BS('Business Administration'),BS('Accountancy'),BS('Management Accounting'),BS('Economics'),BS('Mathematics')], ['Bookkeeping NC III','Computerized Bookkeeping and Financial System Level IV']),
(r'human resource|recruit|labor relations', [BS('Psychology'),BA('Psychology'),BS('Business Administration'),'Bachelor of Public Administration'], []),
(r'market research|marketing|advertis|public relations|search marketing', [BS('Business Administration'),BA('Communication'),BS('Entrepreneurship'),BA('Communication Arts')], ['Digital Marketing Level III','Manage Internet Marketing Level III']),
(r'logistic|purchasing|supply chain|cargo|freight|customs', [BS('Customs Administration'),BS('Business Administration'),BS('Industrial Engineering'),BS('Entrepreneurship')], ['Warehousing Services NC II','Logistics Services NC II']),
(r'office.*clerk|administrative assistant|secretar|receptionist|file clerk|data entry', [BS('Office Administration'),BS('Business Administration'),BS('Information Systems')], ['Bookkeeping NC III','Contact Center Services NC II']),
(r'customer service|telemarketer|telephone operator|bill.*collector', [BS('Business Administration'),BA('Communication'),BS('Office Administration')], ['Contact Center Services NC II']),
(r'sales representative|retail sales|cashier', [BS('Business Administration'),BS('Entrepreneurship'),BA('Communication')], ['Customer Services NC II','Contact Center Services NC II']),
(r'chief executive|general and operations manager|chief sustainability|legislator', [BS('Business Administration'),BS('Entrepreneurship'),'Bachelor of Public Administration',BS('Economics')], []),
(r'graphic designer|art director|fine artist|craft artist|industrial designer', ['Bachelor of Fine Arts','Bachelor of Multimedia Arts',BS('Industrial Design'),BS('Entertainment and Multimedia Computing')], ['Visual Graphic Design NC III','Illustration NC II']),
(r'animator|special effects|multimedia', ['Bachelor of Multimedia Arts','Bachelor of Fine Arts',BS('Entertainment and Multimedia Computing'),BS('Computer Science')], ['Animation NC II','2D Animation NC III','3D Animation NC III','2D Game Art Development NC III','3D Game Art Development NC III']),
(r'photograph|camera operator|film.*editor|video editor', ['Bachelor of Multimedia Arts',BA('Communication'),BA('Broadcasting'),'Bachelor of Fine Arts'], ['Photography NC II','Visual Graphic Design NC III']),
(r'writer|author|journalist|reporter|editor|broadcast.*announcer', [BA('Communication'),BA('Journalism'),BA('English'),BA('Broadcasting'),BA('Communication Arts')], []),
(r'civil engineer|construction manager|surveying.*technician', [BS('Civil Engineering'),BS('Construction Engineering and Management'),BS('Geodetic Engineering')], ['Technical Drafting NC II','Construction Site Supervision Level IV']),
(r'mechanical engineer', [BS('Mechanical Engineering'),BS('Manufacturing Engineering'),BS('Mechatronics Engineering')], ['Technical Drafting NC II','Mechanical Drafting NC I','CNC Milling Machine Operation NC II']),
(r'industrial engineer', [BS('Industrial Engineering'),BS('Manufacturing Engineering'),BS('Management Engineering')], ['Technical Drafting NC II']),
(r'electrical engineer', [BS('Electrical Engineering'),BS('Electronics Engineering'),BS('Mechatronics Engineering')], ['Electrical Installation and Maintenance NC II','Electrical Installation and Maintenance NC III','Electrical Installation and Maintenance NC IV']),
(r'electronics engineer|telecommunication', [BS('Electronics Engineering'),BS('Computer Engineering'),BS('Electrical Engineering')], ['Electronic Products Assembly and Servicing NC II','Computer Systems Servicing NC II']),
(r'nursing assistant|personal care aide|home health aide|caregiver', [BS('Nursing'),BS('Midwifery'),BS('Occupational Therapy')], ['Caregiving NC II','Caregiving (Elderly) NC II','Caregiving (Clients with Special Needs) NC II','Caregiving (Newborn to Pre-Schooler) NC II','Health Care Services NC II']),
(r'childcare|nann', ['Bachelor of Early Childhood Education','Bachelor of Elementary Education',BS('Psychology')], ['Early Childhood Care and Development Services NC III','Caregiving (Newborn to Pre-Schooler) NC II','Caregiving (Grade Schooler to Adolescent) NC II']),
(r'chef|cook|baker|food preparation', [BS('Hospitality Management'),BS('Culinary Management'),BS('Food Technology'),BS('Hotel and Restaurant Management')], ['Cookery NC II','Food Production (Professional Cookery) NC III','Food Production (Professional Cookery) NC IV','Food Production (Bread and Patisserie) NC II']),
(r'waiter|waitress|bartender|barista|dining.*attendant|food service manager', [BS('Hospitality Management'),BS('Hotel and Restaurant Management'),BS('Entrepreneurship')], ['Food and Beverage Services NC II','Food and Beverage Services NC III','Bartending NC II','Barista NC II']),
(r'hotel|lodging|housekeep|maid', [BS('Hospitality Management'),BS('Hotel and Restaurant Management'),BS('Tourism Management')], ['Housekeeping NC II','Housekeeping NC III','Housekeeping NC IV','Front Office Services NC II']),
(r'travel|tour guide|flight attendant', [BS('Tourism Management'),BS('Hospitality Management'),BS('Travel Management')], ['Tourism Promotion Services NC II','Tour Guiding Services NC II','Travel Services NC II']),
(r'agricultur|farmer|farmworker|crop|horticultur', [BS('Agriculture'),'Bachelor of Agricultural Technology',BS('Horticulture'),BS('Agribusiness')], ['Agricultural Crops Production NC I','Agricultural Crops Production NC II','Agricultural Crops Production NC III','Organic Agriculture Production NC II','Agricultural Machinery Operation NC II']),
(r'fish|aquacultur', [BS('Fisheries'),BS('Marine Biology'),BS('Aquaculture')], ['Aquaculture (Grow-Out Operation) NC II','Fish Capture NC II','Fish Products Packaging NC II']),
(r'electrician|electrical.*installer|power.*installer', ['Bachelor of Industrial Technology',BS('Electrical Engineering'),BS('Electrical Technology')], ['Electrical Installation and Maintenance NC II','Electrical Installation and Maintenance NC III','Electrical Installation and Maintenance NC IV']),
(r'plumb|pipefit|steamfit', ['Bachelor of Industrial Technology',BS('Industrial Technology'),BS('Civil Engineering')], ['Plumbing NC I','Plumbing NC II','Plumbing NC III']),
(r'carpenter|woodwork|cabinetmaker', ['Bachelor of Industrial Technology',BS('Industrial Technology')], ['Carpentry NC II','Carpentry NC III']),
(r'weld|solder|braze', ['Bachelor of Industrial Technology',BS('Industrial Technology'),BS('Mechanical Engineering')], ['Manual Metal Arc Welding (MMAW) NC II','Manual Metal Arc Welding (MMAW) NC III','Gas Metal Arc Welding (GMAW) NC II','Gas Tungsten Arc Welding (GTAW) NC II','Flux-Cored Arc Welding (FCAW) NC II']),
(r'mason|brickmason|cement mason|concrete finisher', ['Bachelor of Industrial Technology',BS('Civil Engineering')], ['Masonry NC I','Masonry NC II','Masonry NC III']),
(r'automotive|auto.*mechanic|motorcycle|diesel.*mechanic|bus.*mechanic', ['Bachelor of Industrial Technology',BS('Mechanical Engineering'),BS('Automotive Technology')], ['Automotive Servicing (Engine Repair) NC II','Automotive Servicing (Chassis Repair) NC II','Automotive Servicing (Electrical Repair) NC II','Automotive Diagnosis (Engine) NC III','Automotive Diagnosis (Chassis) NC III','Automotive Servicing NC IV']),
(r'machinist|tool and die|cnc|machine tool', ['Bachelor of Industrial Technology',BS('Mechanical Engineering'),BS('Manufacturing Engineering')], ['CNC Lathe Machine Operation NC II','CNC Milling Machine Operation NC II','Machining NC II','Machining NC III']),
(r'tailor|dressmak|sew.*operator', [BS('Clothing Technology'),'Bachelor of Industrial Technology',BS('Entrepreneurship')], ['Dressmaking NC II','Tailoring NC II']),
(r'barber|hairdresser|cosmetolog', ['Bachelor of Industrial Technology',BS('Entrepreneurship')], ['Hairdressing NC II','Hairdressing NC III','Barbering NC II']),
(r'manicur|pedicur', ['Bachelor of Industrial Technology',BS('Entrepreneurship')], ['Beauty Care (Nail Care) Services NC II','Beauty Care (Nail Enhancement Technology) Services NC III']),
]

def main():
    catalog=read('program_catalog.csv')
    lookup={(r['kind'],r['name'].casefold()):r for r in catalog}
    mappings={kind:read(file) for kind,file in [('college','college_programs.csv'),('tesda','tesda_programs.csv')]}
    audits=[]; changed={'college':0,'tesda':0}; skipped=set()
    for kind, rows in mappings.items():
        field='programs' if kind=='college' else 'qualifications'
        for row in rows:
            selected=None; rule='retained curated mapping'
            for pattern, degrees, qualifications in RULES:
                if re.search(pattern,row['occupation_title'],re.I):
                    selected=[];rule=pattern
                    for name in degrees if kind=='college' else qualifications:
                        entry=lookup.get((kind,name.casefold()))
                        if entry and entry['source_status']=='official_listed': selected.append(entry['name'])
                        elif not entry: skipped.add((kind,name))
                    # Keep older discipline-specific study paths where the new rule
                    # has no registry-supported degree, rather than fabricate one.
                    if kind=='college' and not selected:selected=None
                    break
            if selected is None: selected=[x.strip() for x in row[field].split('|') if x.strip()]
            selected=list(dict.fromkeys(selected))
            value=' | '.join(selected)
            if value!=row[field]: changed[kind]+=1;row['reviewed_on']=DATE
            row[field]=value
            sources=[lookup[(kind,n.casefold())]['source_url'] for n in selected]
            row['source_url']=sources[0] if sources else ''
            for name in selected:
                entry=lookup[(kind,name.casefold())]
                audits.append(dict(onet_code=row['onet_code'],occupation_title=row['occupation_title'],kind=kind,program_name=name,source_url=entry['source_url'],source_status=entry['source_status'],mapping_rule=rule,mapping_status='editorial_related_study_option',note='Program existence source; not a qualification or campus availability guarantee.'))
    write('college_programs.csv',mappings['college']);write('tesda_programs.csv',mappings['tesda'])
    write('career_pathway_audit.csv',audits)
    print(json.dumps(dict(changed=changed,associations=len(audits),unmapped_tesda=sum(not r['qualifications'] for r in mappings['tesda']),unavailable_requested_titles=sorted(skipped)),indent=2))

if __name__=='__main__':main()
