# Evidence-bearing phrases only. Generic words such as data, assistant,
# support, worker, power, and representative are not skill evidence by themselves.
SKILL_KEYWORD_MAP = {
    'Computers and hardware': ['computer hardware', 'computer repair', 'repair computers', 'computer support specialist', 'computer network support', 'network installation', 'troubleshoot computers'],
    'Programming and coding': ['software developer', 'software engineer', 'computer programmer', 'web developer', 'programming', 'develop software', 'develop computer and network software', 'develop websites', 'write code', 'application developer'],
    'Drawing and design': ['graphic designer', 'industrial designer', 'interior designer', 'fashion designer', 'artist', 'drafter', 'animator', 'illustrator', 'design graphics', 'create graphics', 'draw', 'drawing'],
    'Electrical tools': ['electrician', 'electrical wiring', 'electrical equipment', 'electrical installation', 'electrical repair', 'install electrical', 'repair electrical', 'electrical technician'],
    'Cooking and baking': ['cook', 'chef', 'baker', 'baking', 'prepare food', 'food preparation', 'culinary', 'cooking', 'prepare meals'],
    'Repairs and maintenance': ['mechanic', 'repairer', 'repair equipment', 'equipment maintenance', 'machinery maintenance', 'maintain equipment', 'maintenance worker', 'maintenance technician', 'repair machinery'],
    'Caregiving support': ['caregiver', 'nursing assistant', 'personal care aide', 'home health aide', 'assist patients', 'care for patients', 'provide personal care', 'patient care'],
    'Community health assistance': ['community health', 'health education', 'public health', 'health promotion', 'health outreach', 'health educator', 'community health worker'],
    'Childcare & Elderly support': ['childcare', 'child care', 'preschool', 'elderly', 'older adults', 'nanny', 'nannies', 'care for children', 'care for the aged'],
    'Office paperwork': ['administrative assistant', 'office clerk', 'secretary', 'secretaries', 'receptionist', 'file clerk', 'data entry', 'prepare documents', 'maintain records', 'office administration'],
    'Bookkeeping': ['bookkeeping', 'bookkeeper', 'accountant', 'accounting', 'auditor', 'auditing', 'billing', 'payroll', 'ledger', 'accounts payable', 'accounts receivable'],
    'Selling products': ['sales representative', 'retail sales', 'sell products', 'sell goods', 'sell merchandise', 'salesperson', 'sales worker', 'retail salesperson', 'door-to-door sales'],
}


EDU_ZONE_MAP = {
    'Elementary Level': [1, 2],
    'Junior High School': [1, 2, 3],
    'Senior High School': [1, 2, 3, 4],
    'Not Sure / Exploring': [1, 2, 3, 4, 5]
}


TRAITS = dict(zip('RIASEC', ('Realistic','Investigative','Artistic','Social','Enterprising','Conventional')))
