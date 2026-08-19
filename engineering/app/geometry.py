from __future__ import annotations
from dataclasses import dataclass
import re

@dataclass(frozen=True)
class GeometrySummary:
    format:str
    vertices:int
    facets:int
    bounds_mm:tuple[float,float,float]|None
    features:list[dict]
    status:str

def parse_stl_ascii(data:bytes)->GeometrySummary:
    text=data.decode('utf-8','ignore')
    verts=[]
    for m in re.finditer(r"vertex\s+([-+\d.eE]+)\s+([-+\d.eE]+)\s+([-+\d.eE]+)",text,re.I):
        verts.append(tuple(float(x) for x in m.groups()))
    if not verts: raise ValueError("not a readable ASCII STL")
    xs,ys,zs=zip(*verts)
    bounds=(max(xs)-min(xs),max(ys)-min(ys),max(zs)-min(zs))
    return GeometrySummary('stl',len(set(verts)),len(verts)//3,bounds,[{"name":"overall_x","value_mm":bounds[0]},{"name":"overall_y","value_mm":bounds[1]},{"name":"overall_z","value_mm":bounds[2]}],'parsed')

def parse_geometry(data:bytes, filename:str)->GeometrySummary:
    ext=filename.lower().rsplit('.',1)[-1] if '.' in filename else ''
    if ext=='stl': return parse_stl_ascii(data)
    if ext in ('step','stp'):
        # STEP topology requires OpenCascade/OCCT; never fake dimensions from text.
        return GeometrySummary(ext,0,0,None,[], 'requires_occt')
    raise ValueError('unsupported geometry format')
