from __future__ import annotations
import csv, io, re
from dataclasses import dataclass

ALIASES={"serial":["serial","serial_number","gauge_serial","id"],"feature":["feature","dimension","critical_dimension","characteristic"],"nominal_mm":["nominal","nominal_mm","target","required"],"actual_mm":["actual","actual_mm","measured","measured_value"],"tolerance_mm":["tolerance","tol","tolerance_mm","plus_minus"]}
@dataclass
class ImportPreview:
    columns:list[str]; mapping:dict[str,str]; rows:list[dict]; warnings:list[str]

def _norm(s:str)->str:return re.sub(r"[^a-z0-9]+","_",s.strip().lower()).strip("_")
def _number(v):
    if v is None or str(v).strip()=="": return None
    m=re.search(r"[-+]?\d+(?:[.,]\d+)?",str(v)); return float(m.group(0).replace(",",".")) if m else None

def preview_csv(text:str)->ImportPreview:
    sample=text[:10000]
    try: dialect=csv.Sniffer().sniff(sample)
    except csv.Error: dialect=csv.excel
    rows=list(csv.DictReader(io.StringIO(text),dialect=dialect))
    columns=list(rows[0].keys()) if rows else []
    mapping={}
    normalized={_norm(c):c for c in columns}
    for target, aliases in ALIASES.items():
        for a in aliases:
            if a in normalized: mapping[target]=normalized[a]; break
    warnings=[]
    for required in ("serial","nominal_mm","actual_mm"):
        if required not in mapping: warnings.append(f"missing required field: {required}")
    return ImportPreview(columns,mapping,rows[:100],warnings)

def confirm_rows(preview:ImportPreview, units:str="mm"):
    if preview.warnings: raise ValueError("mapping incomplete: "+"; ".join(preview.warnings))
    factor={"mm":1.0,"cm":10.0,"in":25.4}.get(units)
    if factor is None: raise ValueError("unsupported units")
    out=[]
    for row in preview.rows:
        nominal=_number(row[preview.mapping["nominal_mm"]]); actual=_number(row[preview.mapping["actual_mm"]])
        if nominal is None or actual is None: continue
        out.append({"serial":str(row[preview.mapping["serial"]]).strip(),"feature":str(row.get(preview.mapping.get("feature",""),"dimension")).strip(),"nominal_mm":nominal*factor,"actual_mm":actual*factor,"tolerance_mm":(_number(row[preview.mapping["tolerance_mm"]])*factor if "tolerance_mm" in preview.mapping and _number(row[preview.mapping["tolerance_mm"]]) is not None else None)})
    return out
