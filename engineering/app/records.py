from __future__ import annotations
import csv, io

def inspection_csv(rows:list[dict])->str:
    fields=['serial','feature','nominal_mm','actual_mm','tolerance_mm','status','machine','operator','measured_at']
    out=io.StringIO(); w=csv.DictWriter(out,fieldnames=fields); w.writeheader()
    for r in rows: w.writerow({k:r.get(k,'') for k in fields})
    return out.getvalue()

def inspection_html(record:dict, rows:list[dict])->str:
    esc=lambda x:str(x).replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
    body=''.join('<tr>'+''.join(f'<td>{esc(r.get(k,""))}</td>' for k in ['feature','nominal_mm','actual_mm','tolerance_mm','status'])+'</tr>' for r in rows)
    return f'''<!doctype html><html><head><meta charset="utf-8"><title>Fabrient Inspection Record</title><style>body{{font-family:Arial;margin:40px}}table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #aaa;padding:7px;text-align:left}}.refusal{{padding:12px;border:2px solid #a00}}</style></head><body><h1>Fabrient Inspection Record</h1><p>Serial: {esc(record.get('serial',''))}</p><p>Machine: {esc(record.get('machine',''))} &nbsp; Operator: {esc(record.get('operator',''))}</p><p>Acceptance criteria are reproduced from recorded project data. Predictions are not substituted for measurements.</p><table><thead><tr><th>Feature</th><th>Nominal mm</th><th>Actual mm</th><th>Tolerance mm</th><th>Status</th></tr></thead><tbody>{body}</tbody></table></body></html>'''
