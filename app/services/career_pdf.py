"""Render the exact saved recommendations; never run matching again for an export."""
from datetime import datetime, timedelta, timezone
from io import BytesIO
from pathlib import Path
import re
from xml.sax.saxutils import escape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak

FONT_DIR = Path(__file__).resolve().parents[1] / 'static/fonts'
pdfmetrics.registerFont(TTFont('Gabay', str(FONT_DIR / 'DejaVuSans.ttf')))
pdfmetrics.registerFont(TTFont('Gabay-Bold', str(FONT_DIR / 'DejaVuSans-Bold.ttf')))
pdfmetrics.registerFontFamily('Gabay', normal='Gabay', bold='Gabay-Bold', italic='Gabay', boldItalic='Gabay-Bold')

GREEN = colors.HexColor('#0f766e')
DARK = colors.HexColor('#0f172a')
SLATE = colors.HexColor('#475569')
GOAL_LABELS = {
    'Immediate Workforce Entry': 'Find a job',
    'Continue to College / Higher Ed': 'Continue to college',
    'Vocational Certification (Tech-Voc)': 'Take TESDA training skills',
    'Work From Home / Home Caregiver': 'Explore work from home',
}


def text(value):
    """Escape source text for ReportLab markup, with printable typography."""
    value = str(value or '').translate(str.maketrans({
        '\u2010':'-', '\u2011':'-', '\u2013':'-', '\u2014':'-', '\u2212':'-',
        '\u2018':"'", '\u2019':"'", '\u201c':'"', '\u201d':'"', '\u2026':'...', '\u20b1':'PHP ',
    }))
    return escape(value)


def salary_markup(item):
    ref = item.get('salary_reference') or {}
    url = ref.get('source_url') or ''
    if (ref.get('source_name') != 'Jobstreet PH' or ref.get('measure') != 'advertised_p25_p75'
            or not url.startswith('https://ph.jobstreet.com/career-advice/')):
        return 'No matched Jobstreet salary reference available.'
    amount = re.sub(r'\s*\([^)]*\)\s*$', '', item.get('salary') or '').strip()
    return text(amount) + '  <link href="' + escape(url, {'"':'&quot;'}) + '" color="#0f766e"><u>Jobstreet reference</u></link>'


def build_career_pdf(result):
    output = BytesIO()
    generated = datetime.now(timezone(timedelta(hours=8))).strftime('%d %b %Y')
    doc = SimpleDocTemplate(output, pagesize=A4, rightMargin=48, leftMargin=48,
        topMargin=96, bottomMargin=62, title='ALS-Gabay Career Cards', author='ALS-Gabay',
        pageCompression=1)
    styles = {
        'badge': ParagraphStyle('badge', fontName='Gabay-Bold', fontSize=9, leading=12,
            textColor=colors.HexColor('#92400e'), spaceAfter=8),
        'title': ParagraphStyle('career-title', fontName='Gabay-Bold', fontSize=18, leading=23,
            textColor=DARK, spaceAfter=8, keepWithNext=True),
        'body': ParagraphStyle('body', fontName='Gabay', fontSize=11, leading=15.5,
            textColor=SLATE, spaceAfter=8, splitLongWords=True),
        'metric': ParagraphStyle('metric', fontName='Gabay', fontSize=10.5, leading=15,
            textColor=DARK, spaceAfter=7),
        'section': ParagraphStyle('section', fontName='Gabay-Bold', fontSize=12, leading=17,
            textColor=GREEN, spaceBefore=12, spaceAfter=7, keepWithNext=True),
        'note': ParagraphStyle('note', fontName='Gabay', fontSize=9, leading=12,
            textColor=SLATE, spaceAfter=7),
    }
    goal = result.get('assessment_context', {}).get('goal', '')
    label = GOAL_LABELS.get(goal, goal)
    logo = Path(__file__).resolve().parents[1] / 'static/images/logo.png'
    logo_image = ImageReader(str(logo)) if logo.is_file() else None

    def page_frame(canvas, document):
        width, height = A4
        canvas.saveState()
        if logo_image:
            canvas.drawImage(logo_image, 34, height-57, width=32, height=32, mask='auto', preserveAspectRatio=True)
        canvas.setFillColor(GREEN)
        canvas.setFont('Gabay-Bold', 15)
        canvas.drawString(75, height-37, 'ALS-Gabay')
        canvas.setFillColor(SLATE)
        canvas.setFont('Gabay', 9)
        canvas.drawString(75, height-51, 'Career ideas and next steps')
        canvas.drawRightString(width-34, height-39, generated + ' (PH)')
        canvas.setStrokeColor(colors.HexColor('#cbd5e1'))
        canvas.setLineWidth(.8)
        canvas.roundRect(32, 43, width-64, height-117, 12, stroke=1, fill=0)
        canvas.setFont('Gabay', 8)
        canvas.drawString(34, 26, 'Career guidance | Check current school and employer requirements.')
        canvas.drawRightString(width-34, 26, f'Page {document.page}')
        canvas.restoreState()

    story = []
    for index, item in enumerate(result['recommendations']):
        if index:
            story.append(PageBreak())
        story.append(Paragraph(('Top Career Idea' if index == 0 else 'Career Idea') + f'  |  {index+1}', styles['badge']))
        story.append(Paragraph(text(item.get('title')), styles['title']))
        story.append(Paragraph(text(label) + ' | ' + ('Academic Track' if 'College' in goal else 'Explore This Path'), styles['note']))
        for heading, value, fallback in (
            ('College programs', item.get('college_majors'), 'No college course suggestion available'),
            ('Skills training', item.get('tech_voc'), 'No training suggestion available'),
        ):
            value = (value or '').replace(' | ', '; ') or fallback
            story.append(Paragraph('<b>' + heading + ':</b> ' + text(value), styles['metric']))
        if (('Work From Home' in goal or 'Immediate Workforce' in goal) and item.get('is_wfh_capable')):
            story.append(Paragraph('<b>Work From Home:</b> ' + text(item.get('wfh_info') or 'General remote workspace and stable internet required'), styles['metric']))
        story.append(Paragraph('<b>Estimated salary:</b> ' + salary_markup(item), styles['metric']))
        if item.get('reference_note'):
            story.append(Paragraph(text(item['reference_note']), styles['note']))
        story.append(Paragraph('Career Details &amp; Next Steps', styles['section']))
        story.append(Paragraph(text(item.get('description') or 'Career details are unavailable.'), styles['body']))
        story.append(Paragraph('Why This May Suit You', styles['section']))
        for reason in item.get('fit_reasons') or []:
            story.append(Paragraph(text(reason), styles['body']))
        code = item.get('code') or item.get('onet_code') or ''
        if re.fullmatch(r'\d{2}-\d{4}\.\d{2}', code):
            url = 'https://www.onetonline.org/link/summary/' + code
            story.append(Spacer(1, 6))
            story.append(Paragraph('<link href="'+url+'" color="#0f766e"><u>Read the full career profile (O*NET)</u></link>', styles['note']))
    doc.build(story, onFirstPage=page_frame, onLaterPages=page_frame)
    output.seek(0)
    return output
