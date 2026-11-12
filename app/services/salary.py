"""Validate sourced PH salary references without inventing missing wages."""
import math
SALARY_COLUMNS=('salary_display','currency','period','min_amount','max_amount','median_amount',
    'source_occupation','source_name','reference_year','measure','match_type','mapping_note','source_count')

def prepare_salary(row):
    status=row.get('data_status','');measure=row.get('measure','legacy_estimate')
    row.setdefault('currency','PHP');row.setdefault('period','month')
    if row['currency']!='PHP' or row.get('country')!='PH' or row['period'] not in ('month','year','hour'):
        raise ValueError('Salary references must identify PH/PHP and a valid pay period.')
    for name in ('source_occupation','source_name','reference_year','mapping_note'):row.setdefault(name,'')
    row.setdefault('match_type','unreviewed');row['measure']=measure
    row['source_count']=int(row.get('source_count') or 0)
    row['median_amount']=row.get('median_amount') or None
    if status=='unavailable':
        if row.get('min_amount') or row.get('max_amount') or row['median_amount']:raise ValueError('Unavailable salary must have blank amounts.')
        row.update(min_amount=None,max_amount=None,salary_display='No matched Philippine salary reference yet.')
        return
    low,high=float(row['min_amount']),float(row['max_amount'])
    if not all(math.isfinite(v) for v in (low,high)) or not 0<low<=high<1e9:raise ValueError('Invalid salary range.')
    row['min_amount'],row['max_amount']=low,high
    if row['median_amount'] is not None:
        row['median_amount']=float(row['median_amount'])
        if not math.isfinite(row['median_amount']) or not low<=row['median_amount']<=high:raise ValueError('Salary median must fall within the stated range.')
    if measure not in ('legacy_estimate','advertised_p25_p75','industry_average_span','survey_average'):raise ValueError('Unknown salary measure.')
    if measure!='legacy_estimate':
        if not (row.get('source_url') and row.get('reviewed_on') and row['source_name'] and row['source_occupation'] and row['reference_year']):
            raise ValueError('Sourced salary needs its role, publisher, year, URL and review date.')
        if row['match_type'] not in ('exact','related'):raise ValueError('State whether the PH role match is exact or related.')
        if not row['reference_year'].isdigit() or not 2000<=int(row['reference_year'])<=2100:raise ValueError('Invalid salary reference year.')
        if row['period']!='month' or row['source_count']<1:raise ValueError('Source must state a monthly basis and observation count.')
    amount=f'PHP {low:,.0f}' if low==high else f'PHP {low:,.0f}–{high:,.0f}'
    if measure=='advertised_p25_p75':
        if row['median_amount'] is None:raise ValueError('Advertised salary distribution needs a median.')
        suffix=f"middle 50% of advertised pay; {row['reference_year']}"
    elif measure=='industry_average_span':suffix=f"range of industry averages; PSA {row['reference_year']}"
    elif measure=='survey_average':suffix=f"survey average; PSA {row['reference_year']}"
    else:suffix='unverified legacy estimate'
    row['salary_display']=f"{amount} / {row['period']} ({suffix})"
