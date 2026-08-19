from __future__ import annotations
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

def inspection_pdf(record:dict, rows:list[dict])->bytes:
    buf=BytesIO(); doc=SimpleDocTemplate(buf,pagesize=A4,leftMargin=36,rightMargin=36,topMargin=36,bottomMargin=36); styles=getSampleStyleSheet()
    story=[Paragraph('FABRIENT — INSPECTION RECORD',styles['Title']),Spacer(1,12),Paragraph(f"Serial: {record.get('serial','')} &nbsp;&nbsp; Machine: {record.get('machine','')} &nbsp;&nbsp; Operator: {record.get('operator','')}",styles['BodyText']),Spacer(1,14)]
    data=[['Feature','Nominal mm','Actual mm','Tolerance mm','Status']]
    for r in rows:data.append([str(r.get(k,'')) for k in ['feature','nominal_mm','actual_mm','tolerance_mm','status']])
    t=Table(data,repeatRows=1); t.setStyle(TableStyle([('GRID',(0,0),(-1,-1),.5,colors.grey),('BACKGROUND',(0,0),(-1,0),colors.lightgrey),('VALIGN',(0,0),(-1,-1),'TOP'),('FONTSIZE',(0,0),(-1,-1),8)])); story.append(t);story.append(Spacer(1,12));story.append(Paragraph('Ground truth is the recorded physical measurement. Predictions and literature values are not substituted for inspection evidence.',styles['BodyText']));doc.build(story);return buf.getvalue()
