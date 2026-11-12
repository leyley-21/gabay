"""Conservative career-specific remote-work guidance, not employer requirements."""
import re

REMOTE_TASKS = [
    (r'software|programmer|web developer', 'Coding, code reviews, testing, and project discussions can be handled online. Check the employer’s development tools, device, and security requirements.'),
    (r'database|data scientist|statistician|operations research', 'Data analysis, reporting, and database work may be performed remotely when secure access is available. Access to sensitive datasets may require an employer-managed device or an on-site environment.'),
    (r'computer|network|information security|cyber|web administrator', 'System monitoring, troubleshooting, and digital support may be handled remotely. Hardware installation, physical repairs, and some security tasks still require site access.'),
    (r'account|audit|bookkeep|payroll|financial|credit|investment', 'Reports, financial records, and client discussions may be handled online using approved accounting or analysis tools. Document checks, audits, and confidential transactions may require on-site access.'),
    (r'graphic|design|animator|art director|multimedia', 'Digital design, revisions, and client reviews may be completed remotely with suitable creative software. Physical production, shoots, or work involving materials may require an on-site visit.'),
    (r'writer|author|editor|journal|reporter|translator|interpreter', 'Writing, editing, translation, and online collaboration may be done remotely. Interviews, field reporting, or assignments with physical source materials may require travel or site access.'),
    (r'customer service|telemarket|telephone|sales', 'Online enquiries, calls, and customer follow-ups may be handled from home. Check for employer-approved calling software, a quiet call space, privacy rules, and any in-person client duties.'),
    (r'marketing|advertis|public relations', 'Campaign planning, digital content, and performance reporting may be handled online. Events, shoots, and in-person stakeholder meetings can still require attendance.'),
    (r'office|administrative|secretar|data entry|clerk', 'Scheduling, document preparation, and digital record updates may be handled online. Paper records, reception work, or duties using office equipment may require attendance.'),
]

def work_arrangement(row):
    if not row['is_wfh_capable']:
        return 'Primarily on-site in this catalog. Check individual job listings for any hybrid or remote duties.'
    for pattern, guidance in REMOTE_TASKS:
        if re.search(pattern,row['title'],re.I):
            return 'Remote or hybrid work may be possible. '+guidance+' Availability depends on the employer and assignment.'
    return ('Some duties may allow remote or hybrid work, depending on the employer. '
            'Check the job listing for site-based tasks, required tools, working hours, and information-security arrangements.')
